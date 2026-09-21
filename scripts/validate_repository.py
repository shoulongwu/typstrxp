"""Offline validation; never contacts a model API."""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dataset import DATA_PATH, TASKS, prompt_sha256, validate_dataset
from ppl_typst.credentials import resolve_connection


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--require-ready', action='store_true', help='Fail if formal execution is not ready')
    args = parser.parse_args()
    config = json.loads((ROOT / 'configs/pilot.json').read_text())
    errors = validate_dataset()
    blockers = []
    try:
        binary = str(ROOT / config['typst_binary']) if config.get('typst_binary') else 'typst'
        proc = subprocess.run([binary, '--version'], capture_output=True, text=True, timeout=10)
        version = proc.stdout.strip()
        match = re.match(r'^typst (\d+\.\d+\.\d+)(?:\s|$)', version)
        if proc.returncode or not match or match[1] != config['typst_version']:
            blockers.append(f'Typst version mismatch: expected {config["typst_version"]}, found {version!r}')
    except (OSError, subprocess.TimeoutExpired) as exc:
        version = None
        blockers.append(f'Typst unavailable: {exc}')
    for model in config['models']:
        if any(not model.get(key) for key in ('provider', 'base_url', 'model_id')):
            blockers.append(f'Model API configuration incomplete: {model["display_name"]}')
        try:
            resolve_connection(model, ROOT / config.get('credentials_file', 'apikey.config'))
        except (ValueError, OSError):
            blockers.append(f'Model credential missing: {model["model_id"]}')
        if not model.get('api_protocol') or not model.get('model_availability_verified'):
            blockers.append(f'Model availability and generation protocol unverified: {model["model_id"]}')
    if config['status'] != 'frozen':
        blockers.append('Protocol, sampling, rubrics and acceptance thresholds not frozen')
    blockers.append('Full C0-C2 runner and semantic adjudication pipeline not implemented')
    result = {'dataset_valid': not errors, 'task_count': len(TASKS), 'errors': errors,
              'dataset_sha256': hashlib.sha256(DATA_PATH.read_bytes()).hexdigest(),
              'prompt_hashes': {t['id']: prompt_sha256(t['id']) for t in TASKS},
              'installed_typst': version, 'ready_for_experiment': not blockers and not errors,
              'readiness_blockers': blockers}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if errors or (args.require_ready and blockers) else 0


if __name__ == '__main__':
    raise SystemExit(main())
