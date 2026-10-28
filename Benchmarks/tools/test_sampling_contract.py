import argparse
import unittest
from sampling_contract import seed_value, verify, verify_di, verify_pt_replay, verify_pt_history, verify_pt_spatial


class SamplingTests(unittest.TestCase):
    def test_seed_boundaries(self):
        self.assertEqual(seed_value('0'), 0)
        self.assertEqual(seed_value('4294967295'), 0xffffffff)
        for value in ['-1', '4294967296', 'bad']:
            with self.assertRaises(argparse.ArgumentTypeError): seed_value(value)

    def test_effective_contract(self):
        receipt = 'SAMPLING_CONTRACT seed=42 realtime=0 referencePixelCenter=1 pixelJitterScale=0\n'
        self.assertEqual(verify(receipt, 42, True)['seed'], 42)
        with self.assertRaises(ValueError): verify(receipt, 1, True)
        with self.assertRaises(ValueError): verify(receipt.replace('Scale=0', 'Scale=1'), 42, True)
        with self.assertRaises(ValueError): verify(receipt + receipt.replace('seed=42', 'seed=43'), 42, True)

    def test_strict_di_checks_actual_settings(self):
        good='DI_VALIDATION_CONTRACT strict=1 boiling=0 discountNaive=0\nDI_TEMPORAL_CONTRACT permutation=0 maxHistory=20\n'
        self.assertTrue(verify_di(good, True)['strict'])
        for bad in ['',good.replace('boiling=0','boiling=1'),good.replace('discountNaive=0','discountNaive=1')]:
            with self.assertRaises(ValueError):verify_di(bad,True)
        self.assertIn('unavailable',verify_di('')['coverage'])

    def test_replay_diagnostic_receipt(self):
        good='PT_REPLAY_CONTRACT replayOnly=1 roughnessThreshold=1\n'
        self.assertEqual(verify_pt_replay(good,True)['roughness_threshold'],1.)
        for bad in ['',good.replace('Only=1','Only=0'),good.replace('Threshold=1','Threshold=0.3')]:
            with self.assertRaises(ValueError):verify_pt_replay(bad,True)

    def test_age_ablation_retains_mass_cap(self):
        good='PT_HISTORY_CONTRACT ageRejection=0 maxAge=30 maxHistory=8\n'
        self.assertFalse(verify_pt_history(good,True)['age_rejection'])
        for bad in ['',good.replace('Rejection=0','Rejection=1'),good.replace('History=8','History=20')]:
            with self.assertRaises(ValueError):verify_pt_history(bad,True)

    def test_fixed_count_checks_both_paths(self):
        self.assertEqual(verify_pt_spatial('PT_SPATIAL_CONTRACT samples=8 boost=8\n',8)['samples'],8)
        for bad in ['', 'PT_SPATIAL_CONTRACT samples=1 boost=8\n']:
            with self.assertRaises(ValueError):verify_pt_spatial(bad,1)

    def test_legacy_is_not_verified(self):
        self.assertIn('unavailable', verify('')['coverage'])
        with self.assertRaises(ValueError): verify('', 0)
        with self.assertRaises(ValueError): verify('', pixel_center=True)


if __name__ == '__main__': unittest.main()
