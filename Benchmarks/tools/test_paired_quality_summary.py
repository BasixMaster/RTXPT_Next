import math,unittest
from paired_quality_summary import summarize

class PairedQualityTests(unittest.TestCase):
    def test_seed_alignment_and_independent_golden_uncertainty(self):
        result=summarize([47,1019,4093],[1.,2.,3.],[4093,47,1019],[6.,2.,4.])
        self.assertEqual(result['differences'],[1.,2.,3.]);self.assertEqual(result['mean_difference'],2.)
        self.assertAlmostEqual(result['sample_se'],math.sqrt(1./3.));self.assertEqual(result['change_percent_of_means'],100.)
    def test_mismatched_duplicate_and_nonfinite_inputs(self):
        for args in [([1],[1],[2],[2]),([1,1],[1,2],[1,1],[2,3]),([1],[float('nan')],[1],[2]),([1],[],[1],[2])]:
            with self.assertRaises(ValueError):summarize(*args)
    def test_zero_baseline_and_single_pair(self):
        value=summarize([1],[0],[1],[2]);self.assertIsNone(value['change_percent_of_means']);self.assertIsNone(value['sample_se'])
