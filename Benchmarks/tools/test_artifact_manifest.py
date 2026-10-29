"""Frozen-source/cache boundary tests in a synthetic Git repository; no GPU."""
from pathlib import Path
import json,os,shutil,stat,subprocess,unittest,uuid
from artifact_manifest import snapshot,validate
class ArtifactManifestTests(unittest.TestCase):
    def setUp(self):
        self.scratch=Path(os.environ.get('BENCHMARK_TEST_TMP',str(Path.cwd()/'work/benchmark-tools-tests'))).resolve();self.root=self.scratch/('fixture-'+uuid.uuid4().hex);self.root.mkdir(parents=True)
        (self.root/'Rtxpt').mkdir();(self.root/'Rtxpt/source.hlsl').write_bytes(b'original-source')
        self.bin=self.root/'bin';(self.bin/'ShaderDynamic').mkdir(parents=True);self.exe=self.bin/'renderer.exe';self.exe.write_bytes(b'fake-executable')
        self.shader=self.bin/'ShaderDynamic/variant.bin';self.shader.write_bytes(b'compiled-cache')
        def g(*args):subprocess.run(['git','-C',str(self.root),*args],check=True,capture_output=True)
        g('init');g('add','Rtxpt');g('-c','user.name=Test','-c','user.email=test@example.invalid','commit','-m','synthetic fixture')
        self.manifest=self.root/'frozen.json';self.manifest.write_text(json.dumps(snapshot(self.root,self.exe)),encoding='utf-8')
    def tearDown(self):
        if not self.root.resolve().is_relative_to(self.scratch):raise RuntimeError('Unsafe cleanup target')
        def remove_readonly(func,path,exc):
            if not Path(path).resolve().is_relative_to(self.root):raise RuntimeError('Unsafe fixture cleanup target')
            os.chmod(path,stat.S_IREAD|stat.S_IWRITE);func(path)
        shutil.rmtree(self.root,onerror=remove_readonly)
    def test_unchanged_identity_passes(self):self.assertTrue(validate(self.manifest,self.exe)['validated'])
    def test_source_change_rejected(self):
        (self.root/'Rtxpt/source.hlsl').write_bytes(b'edited')
        with self.assertRaisesRegex(ValueError,'working_diff'):validate(self.manifest,self.exe)
    def test_untracked_renderer_source_rejected(self):
        (self.root/'Rtxpt/new.hlsl').write_bytes(b'new')
        with self.assertRaisesRegex(ValueError,'untracked_source'):validate(self.manifest,self.exe)
    def test_shader_cache_change_rejected(self):
        self.shader.write_bytes(b'different shader')
        with self.assertRaisesRegex(ValueError,'shader_file'):validate(self.manifest,self.exe)
    def test_executable_change_rejected(self):
        self.exe.write_bytes(b'different executable')
        with self.assertRaisesRegex(ValueError,'executable'):validate(self.manifest,self.exe)
    def linked_module(self):
        physical=self.root/'physical';physical.mkdir()
        child=physical/'child';admin=physical/'admin'
        subprocess.run(['git','init','--separate-git-dir',str(admin),str(child)],check=True,capture_output=True)
        (child/'source.txt').write_text('original')
        def g(*args):return subprocess.check_output(['git','-C',str(child),*args],stderr=subprocess.PIPE)
        g('add','source.txt');g('-c','user.name=Test','-c','user.email=test@example.invalid','commit','-m','child fixture')
        # Git marks this file hidden on Windows; r+ preserves that attribute.
        with (child/'.git').open('r+') as stream:
            stream.write('gitdir: ../admin\n');stream.truncate()
        link=self.root/'LinkedModule'
        if os.name=='nt':
            subprocess.run(['cmd','/c','mklink','/J',str(link),str(child)],check=True,capture_output=True)
        else:link.symlink_to(child,target_is_directory=True)
        head=g('rev-parse','HEAD').decode().strip()
        subprocess.run(['git','-C',str(self.root),'update-index','--add','--cacheinfo','160000,'+head+',LinkedModule'],check=True,capture_output=True)
        subprocess.run(['git','-C',str(self.root),'-c','user.name=Test','-c','user.email=test@example.invalid','commit','-m','linked fixture'],check=True,capture_output=True)
        self.manifest.write_text(json.dumps(snapshot(self.root,self.exe)))
        return child,head
    def test_linked_relative_gitfile_records_real_module(self):
        child,head=self.linked_module()
        entry=json.loads(self.manifest.read_text())['submodules']['LinkedModule']
        self.assertEqual(entry['checked_out_sha'],head)
        self.assertTrue(validate(self.manifest,self.exe)['validated'])
    def test_linked_module_edits_remain_rejected(self):
        child,head=self.linked_module();(child/'source.txt').write_text('changed')
        with self.assertRaisesRegex(ValueError,'submodules'):validate(self.manifest,self.exe)
if __name__=='__main__':unittest.main()
