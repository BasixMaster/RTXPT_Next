"""User-disabled RTSS audit acceptance tests; no SDK or profile mutation."""
import copy,datetime,unittest
from rtss_readonly import validate
class RTSSReadOnlyTests(unittest.TestCase):
    def document(self):
        zero=dict(Limit=0,LimitTime=0,SyncScanline0=0,SyncScanline1=0)
        return dict(read_only=True,mutation_performed=False,user_confirmed_disabled=True,authority='user_confirmed+SDK_readback+physical_profile',
                    collected_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),executable_sha256='exe',
                    coverage='known',application_profile_exists=False,private_application_file_scope='absent',virtual_store_application_profile_exists=False,
                    property=dict(supported=True,value=0),global_property=dict(supported=True,value=0),
                    effective_caps=zero.copy(),physical_global_caps=zero.copy(),private_global_file_sha256='c'*64,limiter_disabled=True,helper_sha256='a'*64,sdk_dll_sha256='b'*64)
    def test_user_confirmed_read_only_zero_accepted_without_admin(self):
        d=self.document();d['process_elevated']=False;d['private_global_file_sha256']='c'*64;q=validate(d,'exe')
        self.assertTrue(q['rtss_known_caps_disabled']);self.assertFalse(q['fully_uncapped_system_verified']);self.assertFalse(q['mutation_performed'])
    def test_user_application_zero_overrides_global232_without_mutation(self):
        d=self.document();d.update(application_profile_exists=True,private_application_file_scope='installed',private_application_file_sha256='d'*64,physical_application_caps=d['effective_caps'].copy())
        d['global_property']['value']=232;d['physical_global_caps']['Limit']=232;q=validate(d,'exe')
        self.assertEqual(q['effective_limit'],0);self.assertEqual(q['global_limit_observed'],232);self.assertFalse(q['application_profile_absent']);self.assertFalse(q['restoration_required'])
    def test_stale_audit_rejected(self):
        d=self.document();d['collected_utc']='2020-01-01T00:00:00+00:00'
        with self.assertRaises(ValueError):validate(d,'exe')
    def test_wrong_executable_rejected(self):
        with self.assertRaises(ValueError):validate(self.document(),'other')
    def test_virtual_store_or_app_override_rejected(self):
        for key,value in [('virtual_store_application_profile_exists',True),('application_profile_exists',True),('private_application_file_scope','virtual_store')]:
            d=self.document();d[key]=value
            with self.assertRaises(ValueError):validate(d,'exe')
    def test_sdk_and_physical_zero_must_agree(self):
        for which in ['property','global_property']:
            d=self.document();d[which]['value']=232
            with self.assertRaises(ValueError):validate(d,'exe')
        d=self.document();d['physical_global_caps']['Limit']=232
        with self.assertRaises(ValueError):validate(d,'exe')
    def test_scanline_and_frametime_limits_rejected(self):
        for key in ['LimitTime','SyncScanline0','SyncScanline1']:
            d=self.document();d['effective_caps'][key]=1
            with self.assertRaises(ValueError):validate(d,'exe')
    def test_missing_confirmation_or_mutating_receipt_rejected(self):
        for key,value in [('user_confirmed_disabled',False),('mutation_performed',True),('read_only',False)]:
            d=self.document();d[key]=value
            with self.assertRaises(ValueError):validate(d,'exe')
if __name__=='__main__':unittest.main()
