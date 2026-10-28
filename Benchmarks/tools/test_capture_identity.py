"""Launch/manifest parity guards, including the previously incorrect DI+PT case."""
import unittest
from capture_identity import transport_settings
class CaptureIdentityTests(unittest.TestCase):
    def test_dipt_launch_is_di1_gi0_pt1(self):
        self.assertEqual(transport_settings(['app','--useReSTIRDI','1','--useReSTIRGI','0','--useReSTIRPT','1']),dict(restir_di=1,restir_gi=0,restir_pt=1))
    def test_original_digi_without_pt_flag(self):
        self.assertEqual(transport_settings(['app','--useReSTIRDI','1','--useReSTIRGI','1']),dict(restir_di=1,restir_gi=1,restir_pt=0))
    def test_reference_without_reuse(self):
        self.assertEqual(transport_settings(['app','--useReSTIRDI','0','--useReSTIRGI','0']),dict(restir_di=0,restir_gi=0,restir_pt=0))
    def test_duplicate_flag_rejected(self):
        with self.assertRaises(ValueError):transport_settings(['app','--useReSTIRDI','1','--useReSTIRDI','0','--useReSTIRGI','0'])
    def test_missing_or_invalid_flags_rejected(self):
        for args in [['app'],['--useReSTIRDI','1','--useReSTIRGI','no']]:
            with self.assertRaises(ValueError):transport_settings(args)
if __name__=='__main__':unittest.main()
