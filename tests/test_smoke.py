import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.smoke_qwen import call_model


class FakeResponse:
    status = 200

    def __init__(self, content, finish='stop'):
        self.raw = json.dumps({'model': 'qwen3.8-flash', 'choices': [
            {'message': {'content': content}, 'finish_reason': finish}]}).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def read(self):
        return self.raw


class SmokeTests(unittest.TestCase):
    def test_retains_fences_and_normalizes_only_line_endings(self):
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            response = FakeResponse('```typst\r\nHello\r\n```')
            with patch('scripts.smoke_qwen.urllib.request.urlopen', return_value=response):
                result = call_model(stage, {'model_id': 'qwen3.8-flash'},
                                    'https://example.test/v1', 'test-secret', 'task')
            self.assertEqual(result['status'], 'COMPLETE')
            self.assertEqual(result['assistant_content_chars'], 20)
            self.assertEqual((stage/'source.typ').read_text(), '```typst\nHello\n```')
            self.assertEqual((stage/'response.raw.json').read_bytes(), response.raw)
            self.assertNotIn('test-secret', (stage/'request.json').read_text())

    def test_truncated_source_is_retained_but_not_complete(self):
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            with patch('scripts.smoke_qwen.urllib.request.urlopen', return_value=FakeResponse('$ x', 'length')):
                result = call_model(stage, {'model_id': 'qwen3.8-flash'},
                                    'https://example.test/v1', 'test-secret', 'task')
            self.assertEqual(result['status'], 'TRUNCATED_OR_INCOMPLETE_RESPONSE')
            self.assertTrue((stage/'source.typ').exists())

    def test_failed_call_is_recorded_without_secret(self):
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            with patch('scripts.smoke_qwen.urllib.request.urlopen', side_effect=OSError('test-secret')):
                result = call_model(stage, {'model_id': 'qwen3.8-flash'},
                                    'https://example.test/v1', 'test-secret', 'task')
            self.assertEqual(result['status'], 'API_ERROR')
            self.assertNotIn('test-secret', (stage/'response.metadata.json').read_text())
            self.assertFalse((stage/'source.typ').exists())


if __name__ == '__main__':
    unittest.main()
