"""RTSS transaction fault tests with fake SDK; no external profile writes."""
from pathlib import Path
import json,os,shutil,unittest,uuid
from rtss_caps import RTSSScope
class FakeRTSS:
    def __init__(self):self.active=False;self.existing=False;self.changed=False;self.fail_restore=False;self.global_hash='global232';self.fail_apply=False
    def audit(self):
        present=self.active or self.existing;limit=0 if self.active else 232
        return dict(process_elevated=True,private_application_file_scope='installed' if present else 'absent',application_profile_exists=present,coverage='known',limiter_disabled=limit==0,
                    effective_caps=dict(Limit=limit,LimitTime=0,SyncScanline0=0,SyncScanline1=0),
                    private_global_file_sha256=self.global_hash,private_application_file_sha256=('changed' if self.changed else 'owned') if present else None)
    def apply_absent(self):
        self.active=True
        if self.fail_apply:raise RuntimeError('Ambiguous SaveProfile failure')
    def restore_absent(self,created_sha):
        if not self.active:return
        if self.fail_restore or self.changed or created_sha!='owned':raise RuntimeError('Restore refused')
        self.active=False
class RTSSScopeTests(unittest.TestCase):
    def setUp(self):
        self.scratch=Path(os.environ.get('BENCHMARK_TEST_TMP',str(Path.cwd()/'work/benchmark-tools-tests'))).resolve();self.root=self.scratch/('fixture-'+uuid.uuid4().hex);self.root.mkdir(parents=True)
        self.exe=self.root/'renderer.exe';self.exe.write_bytes(b'test');self.state=self.root/'private.json';self.backend=FakeRTSS();self.scope=RTSSScope(self.backend,self.state,self.exe)
    def tearDown(self):
        if not self.root.resolve().is_relative_to(self.scratch):raise RuntimeError('Unsafe cleanup target')
        shutil.rmtree(self.root)
    def test_zero_overrides_global232_then_absence_restored(self):
        self.assertTrue(self.scope.begin()['rtss_limit_disabled']);self.assertEqual(self.backend.audit()['effective_caps']['Limit'],0)
        self.assertTrue(self.scope.restore()['restoration_verified']);self.assertFalse(self.backend.active);self.assertEqual(self.backend.audit()['effective_caps']['Limit'],232)
    def test_existing_profile_refused(self):
        self.backend.existing=True
        with self.assertRaises(ValueError):self.scope.begin()
        self.assertFalse(self.state.exists())
    def test_nonelevated_virtualized_write_refused_before_mutation(self):
        original=self.backend.audit
        self.backend.audit=lambda:{**original(),'process_elevated':False}
        with self.assertRaises(ValueError):self.scope.begin()
        self.assertFalse(self.state.exists());self.assertFalse(self.backend.active)
    def test_external_profile_change_preserved(self):
        self.scope.begin();self.backend.changed=True
        with self.assertRaises(RuntimeError):self.scope.restore()
        self.assertTrue(self.backend.active)
    def test_restore_failure_retry(self):
        self.scope.begin();self.backend.fail_restore=True
        with self.assertRaises(RuntimeError):self.scope.restore()
        self.backend.fail_restore=False;self.assertTrue(self.scope.restore()['restoration_verified'])
    def test_ambiguous_apply_is_fail_closed(self):
        self.backend.fail_apply=True
        with self.assertRaises(RuntimeError):self.scope.begin()
        with self.assertRaises(RuntimeError):self.scope.restore()
        self.assertTrue(self.backend.active);self.assertEqual(json.loads(self.state.read_text())['phase'],'apply_attempted')
    def test_global_external_change_is_never_rolled_back(self):
        self.scope.begin();self.backend.global_hash='user_changed_global'
        with self.assertRaises(RuntimeError):self.scope.restore()
        self.assertFalse(self.backend.active);self.assertEqual(self.backend.global_hash,'user_changed_global')
if __name__=='__main__':unittest.main()
