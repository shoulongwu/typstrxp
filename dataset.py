"""C0 task loader. Keyword checks are screening signals, never semantic or PPL labels."""
import hashlib
import json
import re
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent / 'data' / 'c0_tasks.json'
DATASET = json.loads(DATA_PATH.read_text(encoding='utf-8'))
TASKS = DATASET['tasks']
TASK_MAP = {task['id']: task for task in TASKS}
LEGACY_ID_MAP = {task['legacy_id']: task['id'] for task in TASKS}


def build_prompt(task_id: str) -> str:
    """Only canonical C0 IDs are accepted; legacy mapping is explicit metadata."""
    return DATASET['common_prompt'] + '\n\n' + TASK_MAP[task_id]['prompt_task']


def prompt_sha256(task_id: str) -> str:
    return hashlib.sha256(build_prompt(task_id).encode('utf-8')).hexdigest()


def topic_screen(task_id: str, text: str) -> dict:
    """Prefer extracted document text; source text can match comments or unused code."""
    patterns = TASK_MAP[task_id]['topic_keyword_patterns']
    missing = [pattern for pattern in patterns if not re.search(pattern, text)]
    return {'topic_keywords_present': not missing, 'missing_patterns': missing,
            'semantic_verified': None, 'screening_only': True}


def validate_dataset() -> list[str]:
    issues = []
    if len(TASK_MAP) != len(TASKS):
        issues.append('Duplicate task IDs')
    for task in TASKS:
        tid = task['id']
        if not re.fullmatch(r'C0_\d{2}', tid) or task['stage'] != 'C0':
            issues.append(f'{tid}: invalid C0 identity')
        low, high = task['target_page_range']
        expected = 'EXACTLY 2 pages' if low == high == 2 else f'between {low} and {high} pages, inclusive'
        if low < 1 or high < low or expected not in task['prompt_task']:
            issues.append(f'{tid}: inconsistent page policy')
        if '#set ' in task['prompt_task'] or 'semantic_checker' in task:
            issues.append(f'{tid}: syntax example or misleading checker remains')
        for pattern in task['topic_keyword_patterns']:
            try:
                re.compile(pattern)
            except re.error as exc:
                issues.append(f'{tid}: invalid keyword pattern: {exc}')
    return issues
