"""One subject-model generation, optionally followed by one repair-path probe.

Under protocol 0.4 the optional Qwen repair probes future C2 transport and locality;
C0 trajectory repair belongs to a separately frozen oracle backend. Protocol
v0.6 currently has no active backend. This is not a full C0/C1/C2 run.
Raw responses and source are retained; no semantic claims or PPL labels.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dataset import DATASET, TASK_MAP, build_prompt, topic_screen
from ppl_typst.credentials import resolve_connection
from ppl_typst.locality import check_locality
from ppl_typst.prompts import REPAIR_INSTRUCTION


def save_json(path, data):
    with path.open('x', encoding='utf-8') as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write('\n')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def consume_stream(response, raw_path):
    """Retain the exact SSE body and assemble OpenAI-compatible text deltas."""
    content_parts, reasoning_parts = [], []
    finish_reason = reported_model = response_id = usage = None
    with raw_path.open('xb') as raw_file:
        for line in response:
            raw_file.write(line)
            stripped = line.strip()
            if not stripped or not stripped.startswith(b'data:'):
                continue
            body = stripped[5:].strip()
            if body == b'[DONE]':
                continue
            chunk = json.loads(body)
            reported_model = chunk.get('model', reported_model)
            response_id = chunk.get('id', response_id)
            usage = chunk.get('usage') or usage
            for choice in chunk.get('choices') or []:
                delta = choice.get('delta') or {}
                content = delta.get('content')
                reasoning = delta.get('reasoning_content')
                if isinstance(content, str):
                    content_parts.append(content)
                if isinstance(reasoning, str):
                    reasoning_parts.append(reasoning)
                if choice.get('finish_reason') not in (None, 'null'):
                    finish_reason = choice['finish_reason']
    return {'content': ''.join(content_parts), 'reasoning_content': ''.join(reasoning_parts),
            'finish_reason': finish_reason, 'reported_model': reported_model,
            'response_id': response_id, 'usage': usage, 'raw': raw_path.read_bytes()}


def compile_source(binary, path):
    output = path.with_suffix('.pdf')
    command = [str(binary), 'compile', '--root', str(path.parent), str(path), str(output)]
    started = time.monotonic()
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=30,
                                env={**os.environ, 'NO_COLOR': '1'})
        record = {'status': 'SUCCESS' if result.returncode == 0 else 'COMPILE_FAIL',
                  'exit_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}
    except subprocess.TimeoutExpired:
        record = {'status': 'COMPILE_TIMEOUT', 'exit_code': None}
    record.update(command=command, elapsed_seconds=time.monotonic()-started)
    save_json(path.with_suffix('.compile.json'), record)
    return record


def call_model(stage, model, base_url, key, prompt):
    parameters = {'max_tokens': 32768, 'stream': False}
    parameters.update(model.get('request_parameters') or {})
    payload = {'model': model['model_id'], 'messages': [{'role': 'user', 'content': prompt}],
               **parameters}
    save_json(stage/'request.json', payload)
    (stage/'prompt.txt').write_text(prompt, encoding='utf-8')
    started = time.monotonic()
    request = urllib.request.Request(base_url+'/chat/completions', data=json.dumps(payload).encode(),
              headers={'Authorization': 'Bearer '+key, 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(request, timeout=600) as response:
            http_status = response.status
            if payload['stream']:
                parsed = consume_stream(response, stage/'response.raw.sse')
            else:
                raw = response.read()
                (stage/'response.raw.json').write_bytes(raw)
                data = json.loads(raw)
                choice = data['choices'][0]
                message = choice['message']
                parsed = {'content': message.get('content'),
                          'reasoning_content': message.get('reasoning_content'),
                          'finish_reason': choice.get('finish_reason'),
                          'reported_model': data.get('model'), 'response_id': data.get('id'),
                          'usage': data.get('usage'), 'raw': raw}
        content = parsed['content']
        reasoning_content = parsed['reasoning_content']
        metadata = {'http_status': http_status, 'reported_model': parsed['reported_model'],
                    'response_id': parsed['response_id'], 'usage': parsed['usage'],
                    'finish_reason': parsed['finish_reason'], 'transport': ('sse' if payload['stream'] else 'json'),
                    'elapsed_seconds': time.monotonic()-started,
                    'prompt_sha256': digest(prompt.encode()),
                    'raw_response_sha256': digest(parsed['raw']),
                    'assistant_content_chars': len(content) if isinstance(content, str) else None,
                    'reasoning_content_chars': (len(reasoning_content)
                                                if isinstance(reasoning_content, str) else None),
                    'temperature': parameters.get('temperature', 'provider_default'),
                    'reasoning_mode': parameters.get('reasoning_effort', 'provider_default')}
        if not isinstance(content, str) or not content:
            metadata['status'] = ('INCOMPLETE_REASONING_ONLY' if reasoning_content
                                  else 'NO_USABLE_ASSISTANT_CONTENT')
            content = None
        elif parsed['finish_reason'] != 'stop':
            metadata['status'] = 'TRUNCATED_OR_INCOMPLETE_RESPONSE'
        else:
            metadata['status'] = 'COMPLETE'
        if content is not None:
            (stage/'source.typ').write_text(content.replace('\r\n', '\n').replace('\r', '\n'), encoding='utf-8')
        save_json(stage/'response.metadata.json', metadata)
        return metadata
    except Exception as exc:
        record = {'status': 'API_ERROR', 'error_type': type(exc).__name__,
                  'http_status': getattr(exc, 'code', None), 'elapsed_seconds': time.monotonic()-started}
        save_json(stage/'response.metadata.json', record)
        return record


def inspect_pdf(stage, task_id):
    record = {'semantic_verified': None, 'layout_verified': None}
    for name, command in [('pdfinfo', ['pdfinfo', str(stage/'source.pdf')]),
                          ('text', ['pdftotext', '-layout', str(stage/'source.pdf'), '-'])]:
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=30)
            (stage/(name+'.txt')).write_text(result.stdout, encoding='utf-8')
            if result.returncode != 0:
                record[name+'_error'] = result.stderr
                continue
            if name == 'pdfinfo':
                match = re.search(r'^Pages:\s*(\d+)', result.stdout, re.M)
                record['pages'] = int(match[1]) if match else None
                low, high = TASK_MAP[task_id]['target_page_range']
                record['page_count_in_range'] = low <= record['pages'] <= high if match else None
            else:
                record['topic_screen'] = topic_screen(task_id, result.stdout)
        except (OSError, subprocess.TimeoutExpired) as exc:
            record[name+'_error'] = type(exc).__name__
    save_json(stage/'quality.json', record)
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-dir', required=True, type=Path)
    parser.add_argument('--task-id', default='C0_01', choices=list(TASK_MAP))
    parser.add_argument('--typst', required=True, type=Path)
    parser.add_argument('--repair-boundary', type=Path,
                        help='JSON with start/end and manually reviewed prefix gate evidence')
    args = parser.parse_args()
    binary = args.typst.resolve()
    config = json.loads((ROOT/'configs/pilot.json').read_text())
    model = next(m for m in config['models'] if m['model_id'] == 'qwen3.8-flash')
    version = subprocess.run([str(binary), '--version'], capture_output=True, text=True, check=True).stdout.strip()
    if not re.match(r'^typst 0\.12\.0(?:\s|$)', version):
        parser.error('Smoke uses the specified Typst 0.12.0 compiler')
    base, key = resolve_connection(model, ROOT/config['credentials_file'])
    run = args.run_dir.resolve()
    prompt = build_prompt(args.task_id)
    if not args.repair_boundary:
        run.mkdir(parents=True, exist_ok=False)
        stage = run/'generation'
        stage.mkdir()
        save_json(run/'manifest.json', {
            'run_kind': 'subject_generation_repair_path_smoke', 'formal_experiment': False,
            'task_id': args.task_id,
            'model_id': model['model_id'], 'provider': model['provider'], 'base_url': base,
            'created_at': datetime.now(timezone.utc).isoformat(), 'typst_version': version,
            'typst_binary_sha256': digest(binary.read_bytes()),
            'dataset_version': DATASET['dataset_version'], 'protocol_version': config['protocol_version'],
            'task_prompt_sha256': digest(prompt.encode()), 'repair_scope': config['repair_scope'],
            'generation_calls': 1, 'maximum_repair_calls': 1, 'strict_ppl': None,
            'font_policy': 'current_system_fonts_recorded_not_frozen'})
        fonts = subprocess.run([str(binary), 'fonts'], capture_output=True, text=True, check=True)
        (run/'fonts.txt').write_text(fonts.stdout)
    else:
        manifest = json.loads((run/'manifest.json').read_text())
        if (manifest['task_id'] != args.task_id or manifest['task_prompt_sha256'] != digest(prompt.encode())
                or manifest['typst_binary_sha256'] != digest(binary.read_bytes())):
            parser.error('Original task/compiler snapshot does not match')
        boundary = json.loads(args.repair_boundary.read_text())
        before = (run/'generation/source.typ').read_text()
        start, end = boundary['start'], boundary['end']
        if (not 0 <= start < end <= len(before) or boundary.get('prefix_gate') != 'VERIFIED'
                or not boundary.get('evidence')):
            parser.error('Repair requires a valid, reviewed target boundary and prefix gate')
        prior_compile = json.loads((run/'generation/source.compile.json').read_text())
        if prior_compile['status'] != 'COMPILE_FAIL':
            parser.error('Repair requires an actual compiler failure')
        stage = run/'repair-01'
        stage.mkdir(exist_ok=False)
        save_json(stage/'boundary.json', boundary)
        (stage/'source.before.typ').write_text(before)
        diagnostic = prior_compile['stderr']
        prompt = (REPAIR_INSTRUCTION+'\n\n[Original Task]\n'+prompt+'\n\n[Full Current Source]\n'
                  +before+'\n\n[Target Block]\n'+before[start:end]
                  +f'\nOriginal code-point offsets: [{start}, {end}). Editable prefix: [0, {end}).'
                  +'\n\n[Compiler Diagnostic]\n'+diagnostic)
    print('Calling qwen3.8-flash: '+stage.name, flush=True)
    metadata = call_model(stage, model, base, key, prompt)
    summary = {'stage': stage.name, 'response': metadata, 'strict_ppl': None}
    if metadata['status'] == 'COMPLETE':
        if args.repair_boundary:
            after = (stage/'source.typ').read_text()
            locality = check_locality(before, after, start, end)
            save_json(stage/'locality.json', vars(locality))
            summary['suffix_unchanged'] = locality.suffix_unchanged
            if not locality.compliant:
                summary['status'] = 'PROTOCOL_VIOLATION'
                save_json(stage/'summary.json', summary)
                print(json.dumps(summary, indent=2))
                return 1
            (stage/'prefix.typ').write_text(locality.replacement)
            summary['prefix_compile'] = compile_source(binary, stage/'prefix.typ')
            summary['semantic_preservation'] = 'PENDING_REVIEW'
        summary['full_compile'] = compile_source(binary, stage/'source.typ')
        if summary['full_compile']['status'] == 'SUCCESS':
            summary['quality'] = inspect_pdf(stage, args.task_id)
    save_json(stage/'summary.json', summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    return 0 if summary.get('full_compile', {}).get('status') == 'SUCCESS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
