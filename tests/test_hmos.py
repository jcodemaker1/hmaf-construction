import unittest
from model import calculate_hmaf, classify_hmos
from evidence import PROJECT_COUNT_SCORE, task_presence_cap

class TestHMAFv006(unittest.TestCase):
    def test_balanced_midpoint_no_context(self):
        r = calculate_hmaf(3,3,3,3,3,3,3,3,3)
        self.assertAlmostEqual(r.base_hmos, 3.0)
        self.assertAlmostEqual(r.hmos, 3.0)
        self.assertEqual(r.orientation, "Balanced hybrid")

    def test_narrow_balanced_thresholds(self):
        self.assertEqual(classify_hmos(2.84)[0], "Hybrid leaning physical")
        self.assertEqual(classify_hmos(2.85)[0], "Balanced hybrid")
        self.assertEqual(classify_hmos(3.15)[0], "Balanced hybrid")
        self.assertEqual(classify_hmos(3.16)[0], "Hybrid leaning digital")

    def test_project_count_changes_outcome(self):
        low = calculate_hmaf(3, PROJECT_COUNT_SCORE["1"], 3,3,3,3, 3,3,3)
        high = calculate_hmaf(3, PROJECT_COUNT_SCORE["9+"], 3,3,3,3, 3,3,3)
        self.assertLess(low.hmos, high.hmos)

    def test_routine_context_moves_digital(self):
        r = calculate_hmaf(3,3,3,3,3,3,3,3,3, context_means=[3.70])
        self.assertGreater(r.hmos, 3.15)
        self.assertEqual(r.orientation, "Hybrid leaning digital")

    def test_highrisk_context_moves_physical(self):
        r = calculate_hmaf(3,3,3,3,3,3,3,3,3, context_means=[2.40])
        self.assertLess(r.hmos, 2.85)
        self.assertEqual(r.orientation, "Hybrid leaning physical")

    def test_small_project_context_moves_physical(self):
        r = calculate_hmaf(3,3,3,3,3,3,3,3,3, context_means=[2.33])
        self.assertLess(r.hmos, 2.85)

    def test_critical_inspection_cap(self):
        cap = task_presence_cap("Critical inspection / hold point")
        r = calculate_hmaf(5,5,5,5,5,5,1,1,1, task_cap=cap)
        self.assertLessEqual(r.hmos, 2.84)
        self.assertEqual(r.orientation, "Hybrid leaning physical")

    def test_midscale_context_stays_balanced_at_midpoint(self):
        r = calculate_hmaf(3,3,3,3,3,3,3,3,3, context_means=[2.89])
        self.assertGreaterEqual(r.hmos, 2.85)
        self.assertLessEqual(r.hmos, 3.15)

if __name__ == "__main__":
    unittest.main()
