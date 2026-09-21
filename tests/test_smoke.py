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


class FakeStreamResponse(FakeResponse):
    def __init__(self, chunks):
        self.lines = [('data: '+json.dumps(chunk)+'\n').encode() for chunk in chunks]
        self.lines.append(b'data: [DONE]\n')

    def __iter__(self):
        return iter(self.lines)


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

    def test_stream_ignores_intermediate_null_and_requires_final_stop(self):
        chunks = [
            {'id':'r1','model':'qwen3.8-flash','choices':[{'delta':{'reasoning_content':'think'},'finish_reason':'null'}]},
            {'id':'r1','model':'qwen3.8-flash','choices':[{'delta':{'content':'Hello'},'finish_reason':None}]},
            {'id':'r1','model':'qwen3.8-flash','choices':[{'delta':{},'finish_reason':'stop'}],
             'usage':{'completion_tokens':2}},
        ]
        model = {'model_id':'qwen3.8-flash','request_parameters':{
            'stream':True,'stream_options':{'include_usage':True},'reasoning_effort':'medium'}}
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            with patch('scripts.smoke_qwen.urllib.request.urlopen', return_value=FakeStreamResponse(chunks)):
                result = call_model(stage, model, 'https://example.test/v1', 'test-secret', 'task')
            self.assertEqual(result['status'], 'COMPLETE')
            self.assertEqual(result['finish_reason'], 'stop')
            self.assertEqual(result['reasoning_mode'], 'medium')
            self.assertEqual((stage/'source.typ').read_text(), 'Hello')
            self.assertTrue((stage/'response.raw.sse').exists())

    def test_stream_reasoning_only_is_invalid(self):
        chunks = [{'choices':[{'delta':{'reasoning_content':'unfinished'},'finish_reason':'null'}]}]
        model = {'model_id':'qwen3.8-flash','request_parameters':{'stream':True}}
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            with patch('scripts.smoke_qwen.urllib.request.urlopen', return_value=FakeStreamResponse(chunks)):
                result = call_model(stage, model, 'https://example.test/v1', 'test-secret', 'task')
            self.assertEqual(result['status'], 'INCOMPLETE_REASONING_ONLY')
            self.assertFalse((stage/'source.typ').exists())

    def test_stream_content_without_final_stop_is_incomplete(self):
        chunks = [{'choices':[{'delta':{'content':'partial'},'finish_reason':None}]}]
        model = {'model_id':'qwen3.8-flash','request_parameters':{'stream':True}}
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            with patch('scripts.smoke_qwen.urllib.request.urlopen',
                       return_value=FakeStreamResponse(chunks)):
                result = call_model(stage, model, 'https://example.test/v1',
                                    'test-secret', 'task')
            self.assertEqual(result['status'], 'TRUNCATED_OR_INCOMPLETE_RESPONSE')
            self.assertEqual((stage/'source.typ').read_text(), 'partial')


if __name__ == '__main__':
    unittest.main()
