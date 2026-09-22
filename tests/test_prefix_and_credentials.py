import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ppl_typst.credentials import read_local_config, resolve_connection
from ppl_typst.locality import check_locality
from ppl_typst.prompts import ORACLE_REPAIR_INSTRUCTION, REPAIR_INSTRUCTION
from scripts.repair_with_dsh import (compiler_diagnostic_sha256, disable_model_tools,
                                     feedback_prompt, run_rounds,
                                     validate_repair_packet, validate_repair_response)
from scripts.review_with_dsh import validate_packet, validate_review


class PrefixRepairTests(unittest.TestCase):
    def test_upstream_definition_fix_allowed_without_target_edit(self):
        before = '#let n = missing\n#n\n= Next'
        start, end = before.index('#n'), before.index('\n= Next')
        after = '#let n = 2\n#n\n= Next'
        result = check_locality(before, after, start, end)
        self.assertTrue(result.compliant)
        self.assertFalse(result.prefix_unchanged)
        self.assertEqual(result.replacement, '#let n = 2\n#n')
        self.assertEqual(after[result.new_end:], '\n= Next')
        self.assertFalse(check_locality(before, after, start, end, 'block_only').compliant)

    def test_suffix_modification_rejected_even_if_target_fixed(self):
        self.assertFalse(check_locality('PbadQ', 'newPgoodQ ', 1, 4).compliant)

    def test_unicode_and_growing_prefix(self):
        result = check_locality('中文🙂错后文', '新定义\n中文🙂对后文', 3, 4)
        self.assertTrue(result.compliant)
        self.assertEqual(result.replacement, '新定义\n中文🙂对')

    def test_final_target_allows_whole_document_edits(self):
        result = check_locality('Pbad', 'completely rewritten', 1, 4)
        self.assertTrue(result.compliant)
        self.assertEqual(result.new_end, len('completely rewritten'))

    def test_deleting_entire_prefix_only_passes_locality(self):
        result = check_locality('PbadQ', 'Q', 1, 4)
        self.assertTrue(result.compliant)
        self.assertEqual(result.replacement, '')

    def test_repeated_suffix_is_anchored_at_document_end(self):
        result = check_locality('PbadQ', 'QnewQ', 1, 4)
        self.assertEqual(result.replacement, 'Qnew')
        self.assertFalse(check_locality('PbadLONG', 'NG', 1, 4).compliant)

    def test_instruction_matches_document(self):
        guide = Path(__file__).resolve().parents[1] / 'experiments_guide.md'
        text = guide.read_text()
        for line in REPAIR_INSTRUCTION.splitlines():
            self.assertIn('> '+line, text)
        for line in ORACLE_REPAIR_INSTRUCTION.splitlines():
            self.assertIn('> '+line, text)


class CredentialTests(unittest.TestCase):
    def test_per_model_key_and_override_endpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'apikey.config'
            path.write_text('qwen:q.test-with.dots\nglm:g-test\ndeepseek:d-test\n'
                            'qwen baseurl:https://example.com/compatible-mode/v1\n')
            with patch.dict(os.environ, {}, clear=True):
                for label, key in [('qwen','q.test-with.dots'),('glm','g-test'),('deepseek','d-test')]:
                    model={'credential_label':label,'api_key_env':label.upper()+'_API_KEY','base_url':'https://other.test/v1'}
                    base, actual = resolve_connection(model, path)
                    self.assertEqual(actual, key)
                    self.assertEqual(base, 'https://example.com/compatible-mode/v1' if label=='qwen' else 'https://other.test/v1')
                with patch.dict(os.environ, {'GLM_API_KEY':'override'}):
                    self.assertEqual(resolve_connection({'credential_label':'glm','api_key_env':'GLM_API_KEY','base_url':'https://other.test/v1'},path)[1],'override')

    def test_missing_key_does_not_fallback_to_another_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'apikey.config'
            path.write_text('qwen:some-token\n')
            with patch.dict(os.environ, {}, clear=True), self.assertRaises(ValueError):
                resolve_connection({'credential_label':'glm','api_key_env':'GLM_API_KEY','base_url':'https://other.test/v1'},path)


class ReviewerTests(unittest.TestCase):
    def test_disallow_identity_or_credentials_in_packet(self):
        for field in ['model_id','api_key','c1_result']:
            with self.assertRaises(ValueError):
                validate_packet({'review_type':'protocol_review','protocol':'text',field:'value'})

    def test_incomplete_event_cannot_be_submitted(self):
        with self.assertRaises(ValueError):
            validate_packet({'review_type':'event_review','source_before':'bad'})

    def test_unsupported_claims_lack_required_evidence(self):
        with self.assertRaises(ValueError):
            validate_review({'review_status':'ISSUES_FOUND','confidence':0.8,'requires_human_review':True,
                             'findings':[{'severity':'high','explanation':'assertion'}]})

    def test_reviewer_cannot_inject_final_label_fields(self):
        with self.assertRaises(ValueError):
            validate_review({'review_status':'PASS','confidence':0.9,'requires_human_review':False,
                             'findings':[], 'strict_ppl':True})

    def test_advisory_schema(self):
        data={'review_status':'PENDING_REVIEW','confidence':0.2,'requires_human_review':True,'findings':[]}
        self.assertEqual(validate_review(data),data)

    def test_inventory_is_blind_to_oracle_output(self):
        packet = {'review_type':'inventory_review', 'original_task':'task',
                  'source_before':'bad', 'source_after':'fixed', 'target_block':'bad',
                  'diagnostics':'error', 'compile_results':{}}
        with self.assertRaises(ValueError):
            validate_packet(packet)


class OracleRepairTests(unittest.TestCase):
    class FakeClient:
        def __init__(self, responses):
            self.responses = iter(responses)
            self.prompts = []

        def prompt(self, session_id, prompt, timeout):
            self.prompts.append(prompt)
            return {'message_id': str(len(self.prompts)), 'text': next(self.responses),
                    'turn_end': {'reason': 'completed'}, 'tool_calls': []}

    @staticmethod
    def packet():
        return {'event_id':'e1', 'original_task':'task', 'source_before':'PbadSECRET_SUFFIX',
                'target_start':1, 'target_end':4, 'target_block':'bad',
                'selected_diagnostic':'original error',
                'target_diagnostics':['original error']}

    def test_frozen_target_coordinates_must_match(self):
        packet = {'event_id':'e1', 'original_task':'task', 'source_before':'PbadQ',
                  'target_start':1, 'target_end':4, 'target_block':'bad',
                  'selected_diagnostic':'error', 'target_diagnostics':['error']}
        self.assertEqual(validate_repair_packet(packet), packet)
        with self.assertRaises(ValueError):
            validate_repair_packet({**packet, 'target_block':'other'})
        with self.assertRaises(ValueError):
            validate_repair_packet({**packet, 'target_diagnostics':['different error']})

    def test_oracle_response_has_one_source_field(self):
        self.assertEqual(validate_repair_response({'prefix_after':'fixed'}), 'fixed')
        with self.assertRaises(ValueError):
            validate_repair_response({'prefix_after':'fixed', 'strict_ppl':False})

    def test_failed_prefix_is_repaired_in_same_session(self):
        client = self.FakeClient([
            '{"prefix_after":"Pstillbad"}', '{"prefix_after":"Pfixed"}'
        ])
        compile_results = [
            {'status':'COMPILE_FAIL', 'exit_code':1, 'stdout':'',
             'stderr':'prefix line 1: error', 'command':[]},
            {'status':'SUCCESS', 'exit_code':0, 'stdout':'', 'stderr':'', 'command':[]},
        ]
        with tempfile.TemporaryDirectory() as tmp, \
                patch('scripts.repair_with_dsh.compile_source', side_effect=compile_results):
            records, after, status = run_rounds(self.packet(), Path(tmp), Path('typst'),
                                                client, 'one-session', 4, 10)
        self.assertEqual(status, 'PREFIX_COMPILE_SUCCESS')
        self.assertEqual(after, 'PfixedSECRET_SUFFIX')
        self.assertEqual(len(records), 2)
        self.assertIn('prefix line 1: error', client.prompts[1])
        self.assertNotIn('SECRET_SUFFIX', client.prompts[1])

    def test_identical_failed_candidate_stops_as_no_progress(self):
        response = '{"prefix_after":"Pstillbad"}'
        client = self.FakeClient([response, response, response])
        failed = {'status':'COMPILE_FAIL', 'exit_code':1, 'stdout':'',
                  'stderr':'same diagnostic', 'command':[]}
        with tempfile.TemporaryDirectory() as tmp, \
                patch('scripts.repair_with_dsh.compile_source', return_value=failed):
            records, after, status = run_rounds(self.packet(), Path(tmp), Path('typst'),
                                                client, 'one-session', 4, 10)
        self.assertEqual(status, 'NO_PROGRESS')
        self.assertIsNone(after)
        self.assertEqual(len(records), 2)

    def test_transport_failure_does_not_consume_repair_rounds(self):
        class FailedClient:
            def prompt(self, session_id, prompt, timeout):
                return {'message_id':'1', 'text':'',
                        'turn_end':{'reason':{'kind':'error', 'error':{'code':'TRANSPORT'}}},
                        'tool_calls':[]}
        with tempfile.TemporaryDirectory() as tmp:
            records, after, status = run_rounds(self.packet(), Path(tmp), Path('typst'),
                                                FailedClient(), 'one-session', 4, 10)
        self.assertEqual(status, 'ORACLE_RUNTIME_FAILURE')
        self.assertIsNone(after)
        self.assertEqual(len(records), 1)

    def test_any_oracle_tool_call_is_a_protocol_violation(self):
        class ToolClient:
            def prompt(self, session_id, prompt, timeout):
                return {'message_id':'1', 'text':'{"prefix_after":"Pfixed"}',
                        'turn_end':{'reason':'completed'}, 'tool_calls':['bash']}
        with tempfile.TemporaryDirectory() as tmp:
            records, after, status = run_rounds(self.packet(), Path(tmp), Path('typst'),
                                                ToolClient(), 'one-session', 4, 10)
        self.assertEqual(status, 'PROTOCOL_VIOLATION')
        self.assertEqual(records[0]['tool_calls'], ['bash'])
        self.assertIsNone(after)

    def test_dsh_tool_producers_are_disabled_by_home_patch(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            disable_model_tools(home)
            patch_text = (home/'cordis.patch.yml').read_text()
        self.assertIn('- id: tool-bash\n  disabled: true', patch_text)
        self.assertIn('- id: tool-web\n  disabled: true', patch_text)

    def test_feedback_excludes_unrelated_document_context(self):
        text = feedback_prompt(1, 'COMPILE_FAIL', 'only this diagnostic')
        self.assertIn('only this diagnostic', text)
        self.assertIn('immutable suffix', text)
        self.assertNotIn('SECRET_SUFFIX', text)

    def test_diagnostic_progress_hash_ignores_round_path(self):
        first = 'error: bad\n  ┌─ runs/x/round-01/prefix.after.typ:7:2\n  │\n7 │ #bad\n'
        second = 'error: bad\n  ┌─ runs/x/round-02/prefix.after.typ:7:2\n  │\n7 │ #bad\n'
        self.assertEqual(compiler_diagnostic_sha256(first),
                         compiler_diagnostic_sha256(second))


if __name__ == '__main__':
    unittest.main()
