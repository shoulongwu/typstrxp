import unittest
from functools import partial

from dataset import TASKS, build_prompt, topic_screen, validate_dataset
from ppl_typst.locality import check_locality

check_block_only = partial(check_locality, repair_scope="block_only")


class DatasetTests(unittest.TestCase):
    def test_all_tasks_have_consistent_c0_identity_and_prompts(self):
        self.assertEqual(validate_dataset(), [])
        self.assertEqual(len(TASKS), 10)
        self.assertEqual(len({task['legacy_id'] for task in TASKS}), 10)
        for task in TASKS:
            self.assertEqual(task['target_page_range'], [2, 5])
            self.assertIn('Typst 0.12.0', build_prompt(task['id']))

    def test_keywords_cannot_prove_semantics(self):
        # Even a comment matching every topic group cannot become semantic evidence.
        result = topic_screen('C0_01', '// eigenvalue diagonalization')
        self.assertTrue(result['topic_keywords_present'])
        self.assertIsNone(result['semantic_verified'])
        self.assertTrue(result['screening_only'])


class LocalityTests(unittest.TestCase):
    def test_changed_length_and_unicode(self):
        result = check_block_only('前🙂OLD后', '前🙂正确修复后', 2, 5)
        self.assertTrue(result.compliant)
        self.assertEqual(result.replacement, '正确修复')
        self.assertEqual('前🙂正确修复后'[:result.new_end], '前🙂正确修复')

    def test_empty_suffix(self):
        result = check_block_only('Pold', 'Pnewer', 1, 4)
        self.assertEqual(result.replacement, 'newer')

    def test_outside_whitespace_is_a_violation(self):
        self.assertFalse(check_block_only('PoldQ', 'Pnew Q ', 1, 4).compliant)

    def test_overlapping_anchors_are_rejected(self):
        result = check_block_only('abXab', 'ab', 2, 3)
        self.assertTrue(result.prefix_unchanged)
        self.assertTrue(result.suffix_unchanged)
        self.assertFalse(result.compliant)

    def test_deletion_is_local_but_not_a_semantic_success(self):
        result = check_block_only('PoldQ', 'PQ', 1, 4)
        self.assertTrue(result.compliant)
        self.assertEqual(result.replacement, '')
        # This helper deliberately has no FIXED or strict_ppl field.

    def test_repeated_block_text_uses_coordinates(self):
        self.assertEqual(check_block_only('aXaX', 'aYaX', 1, 2).replacement, 'Y')
        self.assertFalse(check_block_only('aXaX', 'aXaY', 1, 2).compliant)

    def test_invalid_coordinates_are_not_silently_accepted(self):
        for start, end in [(-1, 1), (1, 1), (0, 99), (2, 1)]:
            with self.assertRaises(ValueError):
                check_block_only('abc', 'abc', start, end)


if __name__ == '__main__':
    unittest.main()
