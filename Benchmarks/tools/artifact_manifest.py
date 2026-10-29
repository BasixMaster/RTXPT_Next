"""Freeze/check source, executable and compiled shader-cache identity outside timing.

Compile/warm the intended shader variants before freezing. New/changed cache files
during a strict measured run invalidate the manifest; diagnostic runs may omit it.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,subprocess

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def git(repo,*args):
    # Relative submodule gitfiles must resolve from the physical worktree.
    # A junction in a frozen control can otherwise point Git at the parent
    # control's nonexistent .git/modules directory instead of the real owner.
    return subprocess.check_output(['git','-C',str(Path(repo).resolve()),*args],stderr=subprocess.PIPE)
def snapshot(repo,exe):
    repo=Path(repo).resolve();exe=Path(exe).resolve()
    source_paths=['Rtxpt','CMakeLists.txt']
    untracked=git(repo,'ls-files','--others','--exclude-standard','--',*source_paths).decode('utf-8').splitlines()
    shaders={}
    for dirname in ['ShaderDynamic','ShaderPrecompiled']:
        root=exe.parent/dirname
        if not root.exists():continue
        for path in sorted(root.rglob('*')):
            if path.is_file() and path.suffix.lower() in ['.bin','.signature','.h','.hlsl','.hlsli']:
                shaders[path.relative_to(exe.parent).as_posix()]=sha(path)
    submodules={}
    for line in git(repo,'ls-tree','-r','HEAD').decode('utf-8').splitlines():
        if not line.startswith('160000 '):continue
        meta,name=line.split('\t',1);entry=dict(recorded_gitlink=meta.split()[2])
        try:
            entry['checked_out_sha']=git(repo/name,'rev-parse','HEAD').decode().strip()
            entry['tracked_diff_sha256']=hashlib.sha256(git(repo/name,'diff','--binary','HEAD')).hexdigest()
        except subprocess.CalledProcessError:entry['checked_out_sha']=None;entry['tracked_diff_sha256']=None
        submodules[name]=entry
    return dict(schema_version=1,root_source_sha=git(repo,'rev-parse','HEAD').decode().strip(),
                source_scope=source_paths,working_diff_sha256=hashlib.sha256(git(repo,'diff','--binary','HEAD','--',*source_paths)).hexdigest(),
                untracked_source_hashes={name:sha(repo/name) for name in sorted(untracked)},submodules=submodules,
                executable_sha256=sha(exe),shader_file_hashes=shaders,
                note='Hashes identify on-disk compiled shader caches and copied compiler inputs; they do not prove which individual cache entry executed. Freeze after intended shader compilation; no per-frame hashing.')
def validate(path,exe):
    path=Path(path);expected=json.loads(path.read_text(encoding='utf-8'))
    repo=Path(git(Path(exe).resolve().parent,'rev-parse','--show-toplevel').decode().strip())
    actual=snapshot(repo,exe)
    changed=[key for key in actual if expected.get(key)!=actual[key]]
    if changed:raise ValueError('Frozen artifact identity changed: '+', '.join(changed))
    return dict(manifest_sha256=sha(path),root_source_sha=actual['root_source_sha'],working_diff_sha256=actual['working_diff_sha256'],
                executable_sha256=actual['executable_sha256'],shader_files=len(actual['shader_file_hashes']),validated=True)
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--repo',type=Path,required=True);ap.add_argument('--exe',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();data=snapshot(a.repo,a.exe)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(dict(root_source_sha=data['root_source_sha'],untracked_source_files=len(data['untracked_source_hashes']),shader_files=len(data['shader_file_hashes']),executable_sha256=data['executable_sha256'])))
if __name__=='__main__':main()
