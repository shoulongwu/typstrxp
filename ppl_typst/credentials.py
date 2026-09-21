"""Read per-model credentials from environment or the user's local config."""
import os
from pathlib import Path
import re


def read_local_config(path: Path) -> dict:
    result = {}
    if not path.exists():
        return result
    for line in path.read_text(encoding='utf-8').splitlines():
        match = re.fullmatch(r'\s*(deepseek|glm|qwen)\s*:\s*(\S+)\s*', line)
        if match:
            result[match[1]] = match[2]
        match = re.fullmatch(r'\s*(deepseek|glm|qwen)\s+baseurl\s*:\s*(https://\S+)\s*', line, re.I)
        if match:
            result[match[1].lower() + '_base_url'] = match[2].rstrip('/')
    return result


def resolve_connection(model: dict, config_path: Path) -> tuple[str, str]:
    """Return (base URL, key); callers must never log this tuple or HTTP headers."""
    local = read_local_config(config_path)
    label = model['credential_label']
    key = os.environ.get(model['api_key_env']) or local.get(label)
    if not key:
        raise ValueError(f'Missing credential: {model["api_key_env"]} / {label}')
    base_url = local.get(label + '_base_url', model['base_url'])
    return base_url, key
