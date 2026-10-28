import argparse
import unittest
from sampling_contract import roulette_value, verify_ptpp, verify_capture_history


class PTPlusReceiptTests(unittest.TestCase):
    def test_probability_boundaries(self):
        for value in ['0', '0.1', '0.8', '1']:
            self.assertEqual(roulette_value(value), float(value))
        for value in ['-0.1', '0.01', '1e-40', '1.1', 'nan', 'inf', 'bad']:
            with self.assertRaises(argparse.ArgumentTypeError):
                roulette_value(value)

    def test_history_sweep_requires_actual_receipt(self):
        self.assertEqual(verify_capture_history('CAPTURE_HISTORY warmupFrames=8\n',8)['warmup_frames'],8)
        for bad in ['', 'CAPTURE_HISTORY warmupFrames=64\n', 'CAPTURE_HISTORY warmupFrames=8\nCAPTURE_HISTORY warmupFrames=32\n']:
            with self.assertRaises(ValueError):verify_capture_history(bad,8)

    def test_receipt_matches_actual_mode_and_probability(self):
        good = 'PTPP_CONTRACT reconnection=1 rouletteProbability=0.800000012 diagnostics=0\n'
        self.assertEqual(verify_ptpp(good, 1, .8)['reconnection_mode'], 1)
        for bad in ['', good.replace('reconnection=1', 'reconnection=0'),
                    good.replace('0.800000012', '0'), good.replace('diagnostics=0', 'diagnostics=1'),
                    good.replace('0.800000012', 'nan')]:
            with self.assertRaises(ValueError):
                verify_ptpp(bad, 1, .8)

    def test_legacy_does_not_verify_requested_activation(self):
        self.assertIn('unavailable', verify_ptpp('')['coverage'])
        for mode, probability in [(0, None), (None, 0), (1, .8)]:
            with self.assertRaises(ValueError):
                verify_ptpp('', mode, probability)

    def test_diagnostic_and_conflicting_receipts(self):
        good='PTPP_CONTRACT reconnection=0 rouletteProbability=0 diagnostics=1\n'
        self.assertTrue(verify_ptpp(good, 0, 0, True)['diagnostics'])
        with self.assertRaises(ValueError):
            verify_ptpp(good + good.replace('reconnection=0', 'reconnection=1'), 0, 0, True)


if __name__ == '__main__':
    unittest.main()
