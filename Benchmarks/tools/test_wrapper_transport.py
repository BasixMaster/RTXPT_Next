"""Exercise actual wrapper argument construction/manifest parity without a GPU."""
from pathlib import Path
from unittest import mock
import contextlib,io,json,os,shutil,sys,unittest,uuid
import run_capture,run_timed
from capture_identity import transport_settings
class StopBeforeLaunch(RuntimeError):pass
class WrapperTransportTests(unittest.TestCase):
    def setUp(self):
        self.scratch=Path(os.environ.get('BENCHMARK_TEST_TMP',str(Path.cwd()/'work/benchmark-tools-tests'))).resolve();self.root=self.scratch/('fixture-'+uuid.uuid4().hex)
        (self.root/'bin').mkdir(parents=True);(self.root/'Assets').mkdir();(self.root/'Assets/static.scene.json').write_text('{}')
        self.exe=self.root/'bin/renderer.exe';self.exe.write_bytes(b'fake');self.profiler=self.root/'profiler.exe';self.profiler.write_bytes(b'fake-profiler')
    def tearDown(self):
        if not self.root.resolve().is_relative_to(self.scratch):raise RuntimeError('Unsafe cleanup target')
        shutil.rmtree(self.root)
    def command(self,module,mode,out):
        args=['wrapper','--exe',str(self.exe),'--output',str(out),'--label','synthetic','--scene','static.scene.json','--exposure','0','--mode',mode]
        if module is run_timed:args+=['--presentmon',str(self.profiler)]
        else:args+=['--simple']
        return args
    def assert_parity(self,out,launched,expected):
        m=json.loads((out/'manifest.json').read_text());self.assertEqual(transport_settings(launched),expected)
        self.assertEqual({k:m['settings'][k] for k in expected},expected)
    def test_timed_mode_launch_and_metadata_match(self):
        for mode,expected in [('dipt',dict(restir_di=1,restir_gi=0,restir_pt=1)),('digi',dict(restir_di=1,restir_gi=1,restir_pt=0)),('default',dict(restir_di=0,restir_gi=0,restir_pt=0))]:
            out=self.root/('timed-'+mode);launched=[]
            def stop(args,**kwargs):launched.extend(args);raise StopBeforeLaunch('Synthetic test: no process launched')
            with mock.patch.object(sys,'argv',self.command(run_timed,mode,out)),mock.patch.object(run_timed.subprocess,'Popen',side_effect=stop):
                with self.assertRaises(StopBeforeLaunch):run_timed.main()
            self.assert_parity(out,launched,expected)
    def test_capture_mode_launch_and_metadata_match(self):
        for mode,expected in [('dipt',dict(restir_di=1,restir_gi=0,restir_pt=1)),('digi',dict(restir_di=1,restir_gi=1,restir_pt=0)),('default',dict(restir_di=0,restir_gi=0,restir_pt=0))]:
            out=self.root/('capture-'+mode);launched=[]
            def completed(args,**kwargs):
                launched.extend(args);Path(args[args.index('--capturePath')+1]).write_bytes(b'synthetic placeholder; not an image-quality sample')
                process=mock.Mock();process.pid=123;process.returncode=0;process.poll.return_value=0;return process
            with mock.patch.object(sys,'argv',self.command(run_capture,mode,out)),mock.patch.object(run_capture.subprocess,'Popen',side_effect=completed),contextlib.redirect_stdout(io.StringIO()):run_capture.main()
            self.assert_parity(out,launched,expected)
if __name__=='__main__':unittest.main()
