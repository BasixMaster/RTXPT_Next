"""Cap-state interpretation tests; these do not query or modify the GPU driver."""
import unittest,datetime
from cap_preflight import interpret_driver,FORCE_OFF,PASSIVE,validate_audit,validate_runtime,RUNTIME_UNCAPPED
class CapPreflightTests(unittest.TestCase):
    def raw(self,fg=0,bg=0,vs=PASSIVE):
        return dict(settings={n:dict(status=0,value=v,location=0) for n,v in zip(['foreground_fps','background_fps','vsync'],[fg,bg,vs])})
    def test_application_controlled_is_not_full_verification(self):
        q=interpret_driver(self.raw());self.assertTrue(q['driver_allows_uncapped_application']);self.assertFalse(q['fully_uncapped_verified'])
    def test_background_limit_rejected(self):self.assertTrue(interpret_driver(self.raw(bg=30))['driver_limit_detected'])
    def test_foreground_limit_rejected(self):self.assertTrue(interpret_driver(self.raw(fg=60))['driver_limit_detected'])
    def test_forced_off_allowed(self):self.assertTrue(interpret_driver(self.raw(vs=FORCE_OFF))['driver_allows_uncapped_application'])
    def test_missing_never_means_disabled(self):
        q=interpret_driver({});self.assertEqual(q['driver_cap_coverage'],'unknown');self.assertFalse(q['driver_allows_uncapped_application'])
    def document(self):return dict(helper_exit=0,executable_sha256='test',collected_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),native=self.raw(vs=FORCE_OFF))
    def test_wrong_executable_audit_rejected(self):
        with self.assertRaises(ValueError):validate_audit(self.document(),'other')
    def test_stale_driver_audit_rejected(self):
        d=self.document();d['collected_utc']='2020-01-01T00:00:00+00:00'
        with self.assertRaises(ValueError):validate_audit(d,'test')
    def test_effective_renderer_log_required(self):
        with self.assertRaises(ValueError):validate_runtime('BENCHMARK_UNCAPPED requested=true')
        self.assertEqual(validate_runtime(RUNTIME_UNCAPPED)['fps_limiter'],0)
    def test_fresh_explicit_override_audit_accepted(self):self.assertTrue(validate_audit(self.document(),'test')['driver_allows_uncapped_application'])
if __name__=='__main__':unittest.main()


class AdapterRuntimeTests(unittest.TestCase):
    def test_control_adapter_receipt(self):
        receipt='BENCHMARK_CONTROL_ADAPTER vsync=0 fpsLimiter=0 reflexCap=0 reflexMode=0 frameGeneration=0 renderUnfocused=1 maxBounces=3 maxDiffuseBounces=3'
        self.assertEqual(validate_runtime(receipt)['fps_limiter'],0)
        with self.assertRaises(ValueError):validate_runtime(receipt.replace('vsync=0','vsync=1'))
        with self.assertRaises(ValueError):validate_runtime(receipt.replace(' maxBounces=3 maxDiffuseBounces=3',''))
