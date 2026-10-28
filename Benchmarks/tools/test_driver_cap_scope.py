"""Fault/recovery tests with an in-memory driver; no hardware or profile writes."""
from pathlib import Path
import json,os,shutil,unittest,uuid
from driver_cap_scope import CapScope
from cap_preflight import FORCE_OFF

class FakeDriver:
    def __init__(self):self.active=False;self.fail_apply=False;self.fail_restore=False;self.existing=False;self.changed=False
    def call(self,action,exe,profile=None):
        if action=='audit':
            exists=self.active or self.existing
            return dict(application_profile_found=exists,application_lookup_status=0 if exists else -166,settings={n:dict(status=0,value=v,location=0) for n,v in zip(['foreground_fps','background_fps','vsync'],[0,0,FORCE_OFF])})
        if action=='apply':
            self.active=True
            if self.fail_apply:raise RuntimeError('Ambiguous apply failure after save')
            return dict(applied=True)
        if self.fail_restore or self.changed:raise RuntimeError('Restore refused')
        self.active=False;return dict(restored=True)

class DriverCapScopeTests(unittest.TestCase):
    def setUp(self):
        self.scratch=Path(os.environ.get('BENCHMARK_TEST_TMP',str(Path.cwd()/'work/benchmark-tools-tests'))).resolve();self.root=self.scratch/('fixture-'+uuid.uuid4().hex);self.root.mkdir(parents=True)
        self.exe=self.root/'renderer.exe';self.exe.write_bytes(b'test-only');self.state=self.root/'private-state.json';self.driver=FakeDriver();self.scope=CapScope(self.driver,self.state,self.exe)
    def tearDown(self):
        if not self.root.resolve().is_relative_to(self.scratch):raise RuntimeError('Unsafe cleanup target')
        shutil.rmtree(self.root)
    def test_restore_original_absence_and_idempotent_recovery(self):
        q=self.scope.begin();self.assertEqual(q['phase'],'active_verified');self.assertTrue(self.driver.active)
        self.assertTrue(self.scope.restore()['restoration_verified']);self.assertFalse(self.driver.active);self.assertTrue(self.scope.restore()['restoration_verified'])
    def test_shared_or_existing_profile_refused_without_state_or_mutation(self):
        self.driver.existing=True
        with self.assertRaises(ValueError):self.scope.begin()
        self.assertFalse(self.state.exists());self.assertFalse(self.driver.active)
    def test_ambiguous_apply_can_recover(self):
        self.driver.fail_apply=True
        with self.assertRaises(RuntimeError):self.scope.begin()
        self.assertEqual(json.loads(self.state.read_text())['phase'],'apply_attempted');self.assertTrue(self.scope.restore()['restoration_verified'])
    def test_restore_failure_retains_recovery_state(self):
        self.scope.begin();self.driver.fail_restore=True
        with self.assertRaises(RuntimeError):self.scope.restore()
        self.assertEqual(json.loads(self.state.read_text())['phase'],'restore_attempted');self.driver.fail_restore=False;self.assertTrue(self.scope.restore()['restoration_verified'])
    def test_external_profile_edits_are_not_destroyed(self):
        self.scope.begin();self.driver.changed=True
        with self.assertRaises(RuntimeError):self.scope.restore()
        self.assertTrue(self.driver.active)
    def test_wrong_executable_refused_on_recovery(self):
        self.scope.begin()
        with self.assertRaises(ValueError):CapScope(self.driver,self.state,self.root/'other.exe').restore()
        self.assertTrue(self.driver.active)
if __name__=='__main__':unittest.main()
