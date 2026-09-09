import unittest
from model import calculate_hmaf, classify_hmos
class TestHMAF(unittest.TestCase):
    def test_balanced_midpoint(self):
        r=calculate_hmaf(3,3,3,3,3,3,3,3,3)
        self.assertAlmostEqual(r.digital_reliability,3.0); self.assertAlmostEqual(r.digital_suitability,3.0); self.assertAlmostEqual(r.physical_presence_need,3.0); self.assertAlmostEqual(r.hmos,3.0); self.assertEqual(r.orientation,'Balanced hybrid')
    def test_digital_extreme(self):
        r=calculate_hmaf(5,5,5,5,5,5,1,1,1); self.assertAlmostEqual(r.hmos,5.0); self.assertEqual(r.orientation,'Mostly digital tools')
    def test_physical_extreme(self):
        r=calculate_hmaf(1,1,1,1,1,1,5,5,5); self.assertAlmostEqual(r.hmos,1.0); self.assertEqual(r.orientation,'Mostly physical presence')
    def test_thresholds(self):
        self.assertEqual(classify_hmos(1.49)[0],'Mostly physical presence'); self.assertEqual(classify_hmos(1.50)[0],'Hybrid leaning physical'); self.assertEqual(classify_hmos(2.49)[0],'Hybrid leaning physical'); self.assertEqual(classify_hmos(2.50)[0],'Balanced hybrid'); self.assertEqual(classify_hmos(3.50)[0],'Hybrid leaning digital'); self.assertEqual(classify_hmos(4.50)[0],'Mostly digital tools')
if __name__=='__main__': unittest.main()
