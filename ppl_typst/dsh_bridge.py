"""Small, no-tool dsh SDK bridge shared by experiment agents."""
import json
import os
from pathlib import Path
import queue
import signal
import subprocess
import threading
import time


NO_TOOL_ROWS = (
    'user-questions', 'tool-bash', 'tool-pwsh', 'tool-jobs', 'tool-fs',
    'tool-fs-search', 'tool-skill', 'tool-subagent-control',
    'tool-subagent-list-agents', 'tool-subagent', 'tool-subagent-fork',
    'tool-workflow', 'tool-todo', 'tool-goal', 'tool-ralph', 'tool-web',
    'plan-mode',
)


def prepare_home(home, source_home, max_tokens=8192, reasoning_effort=None):
    """Create a minimal isolated dsh home containing only step-5-preview."""
    import yaml  # Optional dependency used only by the dsh bridge.

    settings = yaml.safe_load((source_home/'settings.yaml').read_text())
    provider = settings['llm-pi-ai']['providers']['step']
    if not any(model['id'] == 'step-5-preview' for model in provider['models']):
        raise ValueError('step-5-preview absent from local dsh configuration')
    models = [dict(model, maxTokens=max_tokens)
              for model in provider['models'] if model['id'] == 'step-5-preview']
    if reasoning_effort:
        efforts = ({'off': 'none', 'low': 'low'} if reasoning_effort == 'off'
                   else {reasoning_effort: reasoning_effort})
        models = [dict(model, reasoningEfforts=efforts,
                       compat={'supportsReasoningEffort': True}) for model in models]
    provider['models'] = models
    selected = {
        'llm-pi-ai': {'providers': {'step': provider}},
        'agent-default-model': {
            'provider': 'step', 'model': 'step-5-preview',
            **({'reasoningEffort': reasoning_effort} if reasoning_effort else {}),
        },
    }
    home.mkdir(parents=True, exist_ok=True)
    (home/'settings.yaml').write_text(json.dumps(selected))  # JSON is valid YAML.

    credentials = yaml.safe_load((source_home/'.credentials.yaml').read_text())
    ref = provider['apiKeyEnv']
    selected_credentials = {'version': credentials['version'], 'refs': {}, 'records': {}}
    if ref in credentials.get('refs', {}):
        selected_credentials['refs'][ref] = credentials['refs'][ref]
    elif not os.environ.get(ref):
        raise ValueError('Step credential missing')
    credential_path = home/'.credentials.yaml'
    credential_path.write_text(json.dumps(selected_credentials))
    credential_path.chmod(0o600)


def disable_model_tools(home):
    rows = ''.join(f'- id: {row}\n  disabled: true\n' for row in NO_TOOL_ROWS)
    (home/'cordis.patch.yml').write_text(
        '# Experiment agents use only evidence supplied by the runner.\n' + rows)


def assistant_text(event):
    if event.get('type') != 'assistant/message':
        return None
    blocks = event.get('data', {}).get('message', {}).get('content', [])
    texts = [block.get('text', '') for block in blocks if block.get('type') == 'text']
    return ''.join(texts) if texts else None


class DshSdkClient:
    """Minimal JSON-RPC client for the shipped dsh SDK profile."""

    def __init__(self, cwd, env, raw_path, stderr_path):
        self.raw = raw_path.open('w')
        self.stderr = stderr_path.open('w')
        self.process = subprocess.Popen(
            ['dsh', '--profile', 'sdk'], cwd=cwd, env=env, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=self.stderr, text=True, bufsize=1,
            start_new_session=True)
        self.frames = queue.Queue()
        self.reader = threading.Thread(target=self._reader_loop, daemon=True)
        self.reader.start()
        self.next_id = 1
        self.responses = {}
        self.events = []
        self.statuses = []

    def _reader_loop(self):
        try:
            for line in self.process.stdout:
                self.raw.write(line)
                self.raw.flush()
                self.frames.put(('frame', line))
        finally:
            self.frames.put(('eof', self.process.poll()))

    def _send(self, method, params=None):
        request_id = self.next_id
        self.next_id += 1
        frame = {'jsonrpc': '2.0', 'id': request_id, 'method': method}
        if params is not None:
            frame['params'] = params
        self.process.stdin.write(json.dumps(frame, ensure_ascii=False) + '\n')
        self.process.stdin.flush()
        return request_id

    def _read_one(self, deadline):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('Timed out waiting for dsh SDK response')
        try:
            kind, value = self.frames.get(timeout=remaining)
        except queue.Empty as exc:
            raise TimeoutError('Timed out waiting for dsh SDK response') from exc
        if kind == 'eof':
            raise RuntimeError(f'dsh SDK exited unexpectedly ({value})')
        frame = json.loads(value)
        if 'id' in frame and 'method' not in frame:
            self.responses[frame['id']] = frame
        elif frame.get('method') == 'session.event':
            self.events.append(frame['params'])
        elif frame.get('method') == 'session.status':
            self.statuses.append(frame['params'])

    def _response(self, request_id, deadline):
        while request_id not in self.responses:
            self._read_one(deadline)
        frame = self.responses.pop(request_id)
        if 'error' in frame:
            raise RuntimeError(f"dsh SDK request failed: {frame['error']}")
        return frame.get('result', {})

    def initialize(self, cwd, timeout, provider='step', model='step-5-preview',
                   reasoning_effort='low', max_tokens=8192):
        deadline = time.monotonic() + timeout
        return self._response(self._send('initialize', {
            'cwd': str(cwd), 'provider': provider, 'model': model,
            'reasoningEffort': reasoning_effort, 'maxTokens': max_tokens,
        }), deadline)

    def prompt(self, session_id, prompt, timeout):
        event_start, status_start = len(self.events), len(self.statuses)
        deadline = time.monotonic() + timeout
        receipt = self._response(self._send('session/prompt', {
            'sessionId': session_id,
            'contentBlocks': [{'type': 'text', 'text': prompt}],
        }), deadline)
        saw_running = False
        while True:
            for item in self.statuses[status_start:]:
                if item.get('sessionId') == session_id and item.get('status') == 'running':
                    saw_running = True
                if saw_running and item.get('sessionId') == session_id and item.get('status') == 'idle':
                    new_events = [entry['event'] for entry in self.events[event_start:]
                                  if entry.get('sessionId') == session_id]
                    messages = [text for event in new_events
                                if (text := assistant_text(event)) is not None]
                    usages = [event.get('data', {}).get('usage') for event in new_events
                              if event.get('type') == 'assistant/message'
                              and event.get('data', {}).get('usage') is not None]
                    ends = [event for event in new_events if event.get('type') == 'turn/end']
                    tool_calls = [event.get('data', {}).get('name') for event in new_events
                                  if event.get('type') == 'tool/call']
                    return {
                        'message_id': receipt.get('messageId'),
                        'text': messages[-1] if messages else '',
                        'turn_end': ends[-1].get('data') if ends else None,
                        'tool_calls': tool_calls,
                        'assistant_usages': usages,
                    }
            self._read_one(deadline)

    def close(self):
        try:
            if self.process.poll() is None:
                self._response(self._send('shutdown'), time.monotonic() + 10)
                self.process.wait(timeout=5)
        except Exception:
            if self.process.poll() is None:
                os.killpg(self.process.pid, signal.SIGTERM)
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(self.process.pid, signal.SIGKILL)
                    self.process.wait()
        finally:
            self.reader.join(timeout=1)
            self.raw.close()
            self.stderr.close()
