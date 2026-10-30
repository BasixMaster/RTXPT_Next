import unittest
from fractions import Fraction as F
from unified_lighting_oracle import enumerate_ris_mis

class UnifiedLightingOracleTests(unittest.TestCase):
    def fixture(self,m):return enumerate_ris_mis([7,2,11],[F(1,2),F(1,3),F(1,6)],[F(1,5),F(3,10),F(1,2)],[1,9,2],m)
    def test_exact_mean_for_candidate_budgets(self):
        for m in (1,2,3,4):
            with self.subTest(candidates=m):
                result=self.fixture(m);self.assertEqual(result['combined'],F(20));self.assertEqual(sum(result['selected_nee_pdf']),1)
    def test_single_candidate_pss_weight_is_one(self):self.assertTrue(self.fixture(1)['all_selected_pss_ucw_unit'])
    def test_ris_selected_pdf_differs_from_source_pdf(self):self.assertNotEqual(self.fixture(3)['selected_nee_pdf'],[F(1,2),F(1,3),F(1,6)])
    def test_omitting_conversion_is_biased(self):self.assertNotEqual(self.fixture(3)['missing_pss_conversion'],F(20))
    def test_one_sided_mis_update_is_biased(self):self.assertGreater(self.fixture(3)['stale_single_sample_bsdf_mis'],F(20))
    def test_unequal_strategy_support(self):
        result=enumerate_ris_mis([3,5],[1,0],[0,1],[1,0],3);self.assertEqual(result['combined'],8)
    def test_missing_contribution_support_rejected(self):
        with self.assertRaises(ValueError):enumerate_ris_mis([1,2],[1,0],[1,0],[1,0],2)
    def test_missing_ris_target_support_rejected(self):
        with self.assertRaises(ValueError):enumerate_ris_mis([1,2],[F(1,2),F(1,2)],[F(1,2),F(1,2)],[1,0],2)
if __name__=='__main__':unittest.main()
