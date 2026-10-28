"""Create separate control-only source snapshots; never edits the input checkout.

Run this from a workbench with Git and Python3.10+. Builds and GPU workloads
are deliberately outside this tool. Source snapshots retain the exact upstream
root/runtime/assets identities plus the separately hashed adapter patch.
"""
from pathlib import Path
import argparse,difflib,hashlib,io,json,subprocess,tarfile

BASES={'B0':'303b408ab81790a5051abd7573830b7a4112eb8e',
       'B1':'7010bb4cda80788eb13cd9ee6143eb2f52a5b6ee'}
FILES=['Rtxpt/SampleCommon/CommandLine.h','Rtxpt/SampleCommon/CommandLine.cpp',
       'Rtxpt/Sample.cpp','Rtxpt/SampleUI.h','Rtxpt/SampleUI.cpp']


def digest(data):return hashlib.sha256(data).hexdigest()
def git(repo,*args):return subprocess.check_output(['git','-C',str(repo),*args])
def replace(s,old,new):
    if s.count(old)!=1:raise ValueError('Expected one unmodified source anchor: '+old[:90])
    return s.replace(old,new,1)


def adapt(name,s):
    if name=='Rtxpt/SampleCommon/CommandLine.h':
        return replace(s,'    int  UseReSTIRGI                = true;','''    int  UseReSTIRGI                = true;
    bool BenchmarkUncapped         = false;
    int OverrideMaxBounces         = -1;
    int OverrideMaxDiffuseBounces  = -1;''')
    if name=='Rtxpt/SampleCommon/CommandLine.cpp':
        return replace(s,'            ("useReSTIRGI", "Enable/disable ReSTIR GI", value(UseReSTIRGI))','''            ("useReSTIRGI", "Enable/disable ReSTIR GI", value(UseReSTIRGI))
            ("maxBounces", "Benchmark control: override total bounce cap (1..32)", value(OverrideMaxBounces))
            ("maxDiffuseBounces", "Benchmark control: override diffuse bounce cap (0..32)", value(OverrideMaxDiffuseBounces))
            ("benchmarkUncapped", "Benchmark control: app VSync/FPS/Reflex caps and frame generation off; render unfocused; external caps need separate audit", value(BenchmarkUncapped))''')
    if name=='Rtxpt/SampleUI.h':
        s=replace(s,'    bool                                ShowUI                                  = true;',
            '    bool                                BenchmarkUncapped                       = false;\n    bool                                ShowUI                                  = true;')
        s=replace(s,'return (RealtimeMode && IsReflexSupported) ?', 'return (!BenchmarkUncapped && RealtimeMode && IsReflexSupported) ?')
        s=replace(s,'return (RealtimeMode && IsDLSSFGSupported) ?', 'return (!BenchmarkUncapped && RealtimeMode && IsDLSSFGSupported) ?')
        s=replace(s,'? (false) : (EnableVsync);','? (false) : (!BenchmarkUncapped && EnableVsync);')
        s=replace(s,'? (0) : (FPSLimiter);','? (0) : (BenchmarkUncapped ? 0 : FPSLimiter);')
        s=replace(s,'return EnableVsync;','return !BenchmarkUncapped && EnableVsync;')
        return replace(s,'return FPSLimiter;','return BenchmarkUncapped ? 0 : FPSLimiter;')
    if name=='Rtxpt/SampleUI.cpp':
        return replace(s,'    m_ui.UseReSTIRGI                = cmdLine.UseReSTIRGI != 0;','''    m_ui.UseReSTIRGI                = cmdLine.UseReSTIRGI != 0;
    m_ui.BenchmarkUncapped          = cmdLine.BenchmarkUncapped;
    if (m_ui.BenchmarkUncapped)
    {
        m_ui.EnableVsync = false;
        m_ui.FPSLimiter = 0;
        m_ui.RenderWhenOutOfFocus = true;
    }''')
    if name=='Rtxpt/Sample.cpp':
        s=replace(s,'#include "Materials/MaterialsBaker.h"','#include "Materials/MaterialsBaker.h"\n#include <stdexcept>\n#include <cstdio>')
        s=replace(s,'static std::string FindPreferredSceneCaseInsensitive(const std::vector<std::string>& available, const std::string& preferred)\n{','''static std::string FindPreferredSceneCaseInsensitive(const std::vector<std::string>& available, const std::string& preferred)
{
    // Explicit benchmark scenes live outside the unchanged upstream Assets pin.
    const std::filesystem::path explicitScene(preferred);
    if (explicitScene.is_absolute())
    {
        if (!std::filesystem::is_regular_file(explicitScene) || explicitScene.extension() != ".json")
            throw std::runtime_error("Explicit scene file does not exist: " + preferred);
        return explicitScene.lexically_normal().string();
    }''')
        s=replace(s,'    // after the preset, which sets it too','''    // Apply explicit benchmark controls after the scene and quality preset.
    if (m_cmdLine.OverrideMaxBounces >= 0)
        m_ui.BounceCount = dm::clamp(m_cmdLine.OverrideMaxBounces, 1, 32);
    if (m_cmdLine.OverrideMaxDiffuseBounces >= 0)
        m_ui.DiffuseBounceCount = dm::clamp(m_cmdLine.OverrideMaxDiffuseBounces, 0, 32);

    // after the preset, which sets it too''')
        s=replace(s,'    if (m_ui.RenderWhenOutOfFocus)','    if (m_ui.BenchmarkUncapped || m_ui.RenderWhenOutOfFocus)')
        s=replace(s,'reflexConsts.frameLimitUs = m_ui.ReflexCappedFps == 0 ? 0 : int(1000000. / m_ui.ReflexCappedFps);',
            'reflexConsts.frameLimitUs = (m_ui.BenchmarkUncapped || m_ui.ReflexCappedFps == 0) ? 0 : int(1000000. / m_ui.ReflexCappedFps);')
        return replace(s,'    StreamlinePreRender();','''    if (m_ui.BenchmarkUncapped && m_frameIndex == 0)
    {
        int reflexMode = 0, frameGeneration = 0;
#if DONUT_WITH_STREAMLINE
        reflexMode = m_ui.ActualReflexMode();
        frameGeneration = int(m_ui.ActualDLSSFGMode());
#endif
        std::printf("BENCHMARK_CONTROL_ADAPTER vsync=%d fpsLimiter=%d reflexCap=0 reflexMode=%d frameGeneration=%d renderUnfocused=1 maxBounces=%d maxDiffuseBounces=%d\\n",
            int(m_ui.ActualEnableVsync()), m_ui.ActualFPSLimiter(), reflexMode, frameGeneration,
            m_ui.BounceCount, m_ui.DiffuseBounceCount);
        std::fflush(stdout);
    }
    StreamlinePreRender();''')
    raise ValueError(name)


def snapshot(repo,sha,directory):
    if directory.exists():raise ValueError('Refuse to overwrite snapshot: '+str(directory))
    directory.mkdir(parents=True)
    # Archive must ignore the author's checkout newline preference; the patch
    # and source hashes are defined against exact Git blob bytes.
    data=git(repo,'-c','core.autocrlf=false','archive','--format=tar',sha)
    with tarfile.open(fileobj=io.BytesIO(data),mode='r:') as archive:
        for member in archive.getmembers():
            target=(directory/member.name).resolve()
            if not target.is_relative_to(directory.resolve()) or not (member.isfile() or member.isdir()):
                raise ValueError('Unexpected archive member: '+member.name)
        archive.extractall(directory)
    # A private Git repository makes git-apply resolve against this exact
    # snapshot rather than any ancestor repository. Read source objects through
    # an alternate; never reset/edit the input checkout or copy its submodules.
    git(directory,'init','-q');git(directory,'config','core.autocrlf','false')
    common=Path(git(repo,'rev-parse','--git-common-dir').decode().strip())
    common=(common if common.is_absolute() else repo/common).resolve()
    alternates=directory/'.git/objects/info/alternates'
    alternates.write_bytes(((common/'objects').as_posix()+'\n').encode())
    git(directory,'update-ref','HEAD',sha);git(directory,'read-tree',sha)


def source_hashes(directory):
    return {p.relative_to(directory).as_posix():digest(p.read_bytes())
            for p in directory.rglob('*') if p.is_file() and '.git' not in p.relative_to(directory).parts}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source-repo',type=Path,required=True)
    ap.add_argument('--output-root',type=Path,required=True)
    ap.add_argument('--package-root',type=Path,default=Path(__file__).resolve().parent)
    a=ap.parse_args();repo=a.source_repo.resolve();out=a.output_root.resolve();package=a.package_root.resolve();package.mkdir(parents=True,exist_ok=True)
    before={name:git(repo,'show',BASES['B0']+':'+name).decode('utf-8') for name in FILES}
    after={name:adapt(name,s) for name,s in before.items()}
    patch=''.join('diff --git a/'+name+' b/'+name+'\n'+''.join(difflib.unified_diff(
        before[name].splitlines(keepends=True),after[name].splitlines(keepends=True),fromfile='a/'+name,tofile='b/'+name)) for name in FILES)
    patch_path=package/'benchmark-controls.patch';patch_path.write_bytes(patch.encode('utf-8'))
    records=[]
    for label,sha in BASES.items():
        directory=out/('controls-'+label);snapshot(repo,sha,directory);original=source_hashes(directory)
        git(directory,'apply','--check',str(patch_path));git(directory,'apply',str(patch_path));modified=source_hashes(directory)
        changed=sorted(n for n in original if original[n]!=modified[n])
        if changed!=sorted(FILES):raise ValueError('Unexpected adapter changes: '+str(changed))
        if set(original)!=set(modified):raise ValueError('Adapter added or removed source files')
        shaders={n:h for n,h in original.items() if n.endswith(('.hlsl','.hlsli'))}
        if any(modified[n]!=h for n,h in shaders.items()):raise ValueError('Shader source changed')
        links=git(repo,'ls-tree','-r',sha).decode().splitlines();links=[s for s in links if s.startswith('160000')]
        records.append(dict(label=('RTXPT1.9' if label=='B0' else 'B1')+'+benchmark-controls-v1',base_source_sha=sha,snapshot_directory='controls-'+label,
            patch_applies=True,changed_paths=changed,shader_files_verified_unchanged=len(shaders),source_file_count=len(original),
            root_gitlinks=links,changed_source_hashes={n:dict(before=original[n],after=modified[n]) for n in changed},
            shader_source_manifest_sha256=digest(json.dumps(shaders,sort_keys=True).encode()),
            shader_sources=shaders,build_status='not_built',gpu_status='not_run'))
    manifest=dict(schema_version=1,adapter='benchmark-controls-v1',patch_sha256=digest(patch.encode()),
        scope='Five host/CLI/UI files only. No shader, estimator, runtime, dependency or Assets changes.',
        default_behavior='All overrides inactive by default. New executable identities are required even when the patch is control-only.',
        controls=['absolute scene JSON path','maxBounces1..32','maxDiffuseBounces0..32','benchmarkUncapped'],
        uncapped_scope='Application VSync/FPS limiter/Reflex cap/Reflex mode/frame generation disabled; unfocused rendering enabled. Driver, compositor and external overlays are separate.',
        records=records)
    (package/'manifest.json').write_bytes((json.dumps(manifest,indent=2)+'\n').encode())
    print(json.dumps(dict(patch_applies_to_both=True,changed_paths=FILES,shader_files_verified=[r['shader_files_verified_unchanged'] for r in records],build='not_run',gpu='not_run')))


if __name__=='__main__':main()
