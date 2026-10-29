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
    def test_scene_path_cannot_silently_fall_back(self):
        scene=self.root/'Assets/static.scene.json'
        self.assertEqual(run_capture.scene_argument(str(scene)),str(scene.resolve()))
        self.assertEqual(run_capture.scene_argument('static.scene.json'),'static.scene.json')
        with self.assertRaises(ValueError):run_capture.scene_argument('absent.scene.json',self.root/'Assets')
        for missing in [str(self.root/'missing.scene.json'),'missing/path.scene.json']:
            with self.assertRaises(ValueError):run_capture.scene_argument(missing)

    def test_timed_mode_launch_and_metadata_match(self):
        for mode,expected in [('dipt',dict(restir_di=1,restir_gi=0,restir_pt=1)),('digi',dict(restir_di=1,restir_gi=1,restir_pt=0)),('default',dict(restir_di=0,restir_gi=0,restir_pt=0)),('di',dict(restir_di=1,restir_gi=0,restir_pt=0)),('pt',dict(restir_di=0,restir_gi=0,restir_pt=1))]:
            out=self.root/('timed-'+mode);launched=[]
            def stop(args,**kwargs):launched.extend(args);raise StopBeforeLaunch('Synthetic test: no process launched')
            with mock.patch.object(sys,'argv',self.command(run_timed,mode,out)),mock.patch.object(run_timed.subprocess,'Popen',side_effect=stop):
                with self.assertRaises(StopBeforeLaunch):run_timed.main()
            self.assert_parity(out,launched,expected)
    def test_capture_mode_launch_and_metadata_match(self):
        for mode,expected in [('dipt',dict(restir_di=1,restir_gi=0,restir_pt=1)),('digi',dict(restir_di=1,restir_gi=1,restir_pt=0)),('default',dict(restir_di=0,restir_gi=0,restir_pt=0)),('di',dict(restir_di=1,restir_gi=0,restir_pt=0)),('pt',dict(restir_di=0,restir_gi=0,restir_pt=1))]:
            out=self.root/('capture-'+mode);launched=[]
            def completed(args,**kwargs):
                launched.extend(args);Path(args[args.index('--capturePath')+1]).write_bytes(b'synthetic placeholder; not an image-quality sample')
                process=mock.Mock();process.pid=123;process.returncode=0;process.poll.return_value=0;return process
            with mock.patch.object(sys,'argv',self.command(run_capture,mode,out)),mock.patch.object(run_capture.subprocess,'Popen',side_effect=completed),contextlib.redirect_stdout(io.StringIO()):run_capture.main()
            self.assert_parity(out,launched,expected)

    def test_capture_ptpp_and_history_use_effective_receipts(self):
        out=self.root/'ptpp-capture';launched=[]
        args=self.command(run_capture,'dipt',out)+['--pt-reconnection-mode','1','--pt-roulette-probability','0.8','--history-frames','8']
        def completed(command,**kwargs):
            launched.extend(command);Path(command[command.index('--capturePath')+1]).write_bytes(b'fixture')
            kwargs['stdout'].write('PTPP_CONTRACT reconnection=1 rouletteProbability=0.800000012 diagnostics=0\nCAPTURE_HISTORY warmupFrames=8\n');kwargs['stdout'].flush()
            process=mock.Mock();process.pid=123;process.returncode=0;process.poll.return_value=0;return process
        with mock.patch.object(sys,'argv',args),mock.patch.object(run_capture.subprocess,'Popen',side_effect=completed),contextlib.redirect_stdout(io.StringIO()):run_capture.main()
        for flag,value in [('--ptReconnectionMode','1'),('--ptRouletteProbability','0.8'),('--captureWarmupFrames','8')]:
            self.assertEqual(launched[launched.index(flag)+1],value)
        m=json.loads((out/'manifest.json').read_text());self.assertEqual(m['measurement_status'],'captured')
        self.assertEqual(m['effective_capture_history']['warmup_frames'],8)

    def test_timed_ptpp_arguments(self):
        out=self.root/'ptpp-timed';launched=[]
        def stop(command,**kwargs):launched.extend(command);raise StopBeforeLaunch('No GPU launched')
        args=self.command(run_timed,'dipt',out)+['--pt-reconnection-mode','1','--pt-roulette-probability','0.8']
        with mock.patch.object(sys,'argv',args),mock.patch.object(run_timed.subprocess,'Popen',side_effect=stop):
            with self.assertRaises(StopBeforeLaunch):run_timed.main()
        self.assertEqual(launched[launched.index('--ptReconnectionMode')+1],'1')
        self.assertEqual(launched[launched.index('--ptRouletteProbability')+1],'0.8')
if __name__=='__main__':unittest.main()
