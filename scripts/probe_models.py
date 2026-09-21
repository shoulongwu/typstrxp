"""Small connectivity checks, explicitly excluded from experimental trials."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import urllib.request
import urllib.error

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ppl_typst.credentials import resolve_connection


def probe(model):
    result = {'model_id': model['model_id'], 'credential_label': model['credential_label'], 'is_experiment_trial': False}
    try:
        base, key = resolve_connection(model, ROOT / 'apikey.config')
        base = model.get('_base_url_override', base)
        result['base_url'] = base
        payload = {'model': model['model_id'], 'messages': [{'role': 'user', 'content': 'Reply with OK.'}],
                   'max_tokens': 64, 'stream': False}
        request = urllib.request.Request(base + '/chat/completions',
                  data=json.dumps(payload).encode(),
                  headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key})
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.load(response)
            result['http_status'] = response.status
        result['chat_completions_response'] = bool(isinstance(data.get('choices'), list) and data['choices'])
        result['reported_model'] = data.get('model')
        result['usage'] = data.get('usage')
        result['finish_reason'] = data.get('choices', [{}])[0].get('finish_reason')
    except urllib.error.HTTPError as exc:
        result.update(http_status=exc.code, error='HTTP_ERROR')
    except Exception as exc:
        result['error'] = type(exc).__name__
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    parser.add_argument('--model-id')
    parser.add_argument('--credential-label', choices=['qwen','glm','deepseek'])
    parser.add_argument('--base-url')
    args = parser.parse_args()
    config = json.loads((ROOT/'configs/pilot.json').read_text())
    models = [m.copy() for m in config['models'] if not args.model_id or m['model_id'] == args.model_id]
    if not models or ((args.credential_label or args.base_url) and len(models) != 1):
        parser.error('Connection overrides require exactly one selected model')
    for model in models:
        if args.credential_label:
            model['credential_label'] = args.credential_label
            model['api_key_env'] = args.credential_label.upper() + '_API_KEY'
        if args.base_url:
            model['_base_url_override'] = args.base_url.rstrip('/')
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    # Reserve the artifact before paid calls; do not repeat calls on an overwrite error.
    with output.open('x', encoding='utf-8') as artifact:
        with ThreadPoolExecutor(max_workers=3) as pool:
            results = list(pool.map(probe, models))
        record = {'created_at': datetime.now(timezone.utc).isoformat(), 'results': results}
        artifact.write(json.dumps(record, indent=2)+'\n')
    print(json.dumps(record, indent=2))
    return 0 if all(r.get('chat_completions_response') for r in results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
