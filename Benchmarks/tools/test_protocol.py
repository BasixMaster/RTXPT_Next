"""Negative acceptance checks for resumed protocol runs; no GPU workload."""
from pathlib import Path
import json,os,shutil,unittest,uuid
from summarize_protocol import validate_run

class ProtocolAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.scratch=Path(os.environ.get('BENCHMARK_TEST_TMP',str(Path.cwd()/'work/benchmark-tools-tests'))).resolve()
        self.root=self.scratch/('fixture-'+uuid.uuid4().hex);self.root.mkdir(parents=True)
    def tearDown(self):
        if not self.root.resolve().is_relative_to(self.scratch):raise RuntimeError('Unsafe cleanup target')
        shutil.rmtree(self.root)
    def rejected_log(self,message):
        d=self.root;(d/'manifest.json').write_text(json.dumps(dict(status='timed_completed',image_write_count=0,no_image_writes=True)),encoding='utf-8')
        (d/'presentmon.log').write_text(message,encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'trace loss'):validate_run(d,{}, {})
    def test_reported_etw_loss_rejected(self):self.rejected_log('WARNING: 42 ETW events were lost during capture.')
    def test_reported_generic_loss_rejected(self):self.rejected_log('Warning: Events were lost during recording.')
    def test_incomplete_run_rejected_before_resume(self):
        d=self.root;(d/'manifest.json').write_text(json.dumps(dict(status='running',image_write_count=0,no_image_writes=True)),encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'Incomplete'):validate_run(d,{}, {})

if __name__=='__main__':unittest.main()
