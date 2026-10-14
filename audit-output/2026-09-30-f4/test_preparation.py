"""Preparation-policy checks only: these synthetic values are not genomic inputs."""
import unittest
from derive import quality_reasons


class PreparationPolicy(unittest.TestCase):
    def test_observed_reference(self):
        self.assertEqual(quality_reasons((0, 0), 10, None, (0, 20, 80)), [])

    def test_no_reference_from_missing_likelihood(self):
        self.assertTrue(quality_reasons((0, 0), 30, 99, None))

    def test_weak_reference(self):
        self.assertTrue(quality_reasons((0, 0), 30, None, (0, 19, 80)))

    def test_low_depth(self):
        self.assertTrue(quality_reasons((0, 0), 9, None, (0, 60, 100)))

    def test_complete_variant(self):
        self.assertEqual(quality_reasons((0, 1), 10, 20, None), [])

    def test_missing_variant_quality(self):
        self.assertTrue(quality_reasons((0, 1), 30, None, None))

    def test_partial_call(self):
        self.assertTrue(quality_reasons((0, None), 30, 99, None))

    def test_reference_low_explicit_gq(self):
        self.assertTrue(quality_reasons((0, 0), 30, 10, (0, 60, 100)))


if __name__ == "__main__":
    unittest.main()
