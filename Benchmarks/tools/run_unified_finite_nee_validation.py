"""Validate the opt-in NEE-only unified tree; not full PT++ or a timing benchmark."""
from pathlib import Path
import argparse,json,subprocess,sys,hashlib
import numpy as np
from inspect_pt_reservoirs import inspect
from analyze_hdr import read_pfm

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--exe',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    repo=Path(__file__).resolve().parents[2];base=a.output.resolve();base.mkdir(parents=True,exist_ok=False)
    exe=a.exe.resolve();scene=repo/'Testing/B2/Scenes/opaque-room-registered-env.scene.json'
    # Source identities are separate from shader caches, which may compile on demand.
    source={x.relative_to(repo).as_posix():digest(x) for folder in [repo/'Rtxpt',repo/'Testing/B2/Scenes'] for x in folder.rglob('*') if x.is_file() and x.suffix in ['.h','.cpp','.hlsl','.hlsli','.json','.gltf','.bin']}
    exe_hash=digest(exe);results=[]
    (base/'source-inputs.json').write_text(json.dumps(source,indent=2)+'\n')
    for mode in [0,1,2,3]:
        label=f'room-unified-full-prefix-mode{mode}';out=base/label
        cmd=[sys.executable,'-X','utf8','-B',str(repo/'Benchmarks/tools/run_capture.py'),'--exe',str(exe),'--output',str(out),'--label',label,'--scene',str(scene),'--width','177','--height','91','--exposure','0','--mode','pt','--pt-mode',str(mode),'--pt-unified-finite-nee-validation','--pt-replay-only-validation','--pt-reconnection-mode','0','--pt-fixed-spatial-samples','1','--linear-hdr','--capture-native-radiance','--capture-pt-reservoirs','--simple','--history-frames','8','--max-bounces','4','--max-diffuse-bounces','4','--sampling-seed','47','--environment-diffuse-mip','0','--app-uncapped','--timeout','600']
        subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL)
        m=json.loads((out/'manifest.json').read_text());assert m['measurement_status']=='captured',m['measurement_status']
        assert m['exe_sha256']==exe_hash and m['effective_unified_finite_nee']['active']
        binary=next(out.glob('*.pt.bin'));raw=binary.read_bytes();meta=json.loads(Path(str(binary)+'.json').read_text())
        words=np.frombuffer(raw,'<u4').reshape(-1,16);stats=inspect(words,meta)
        counters=json.loads(Path(str(binary)+'.stats.json').read_text())
        assert counters['identity_shift_tests']>0 and counters['identity_shift_failures']==0,counters
        for s in stats.values():assert s['nonfinite_m']==s['nonfinite_weight_valid']==s['nonfinite_target_valid']==0
        initial=stats['initial_preserved_index'];final=stats['final_index']
        assert initial['positive_weight_path_length_histogram'].get('2',0)>0
        assert any(int(k)>2 and v>0 for k,v in initial['positive_weight_path_length_histogram'].items())
        assert initial['midpath_reconnection_valid']==0
        if mode in [1,3]:assert final['positive_age_valid']>0
        if mode==0:assert final['positive_age_valid']==0
        if mode in [2,3]:assert final['m_greater_than_one']>0
        pfm=next(x for x in out.glob('*.pfm') if not x.name.endswith(('.native.pfm','.native-di.pfm','.native-di-gi.pfm','.native-di-gi-pt.pfm')))
        image=read_pfm(pfm);assert np.isfinite(image).all() and image.min()>=0 and image.max()>0
        native=read_pfm(next(out.glob('*.native.pfm')))
        assert native.shape==image.shape and np.isfinite(native).all()
        assert np.all(image>=native) and image.mean()>native.mean()
        np.savez_compressed(out/'packed-state.npz',words=words)
        results.append(dict(label=label,mode=mode,passed=True,full_paper_mis=False,statistics=stats,counters=counters,raw_hdr_sha256=digest(pfm),image_mean=float(image.mean()),native_nonzero_pixels=int(np.count_nonzero(native.max(2)>0)),native_plus_pt_monotone=True,exe_sha256=exe_hash))
        (base/'results.json').write_text(json.dumps(results,indent=2)+'\n')
        assert digest(exe)==exe_hash
        for name,expected in source.items():assert digest(repo/name)==expected,name
        print('UNIFIED_FINITE_NEE_GATE_PASSED '+label,flush=True)
    summary=dict(status='scoped_gpu_prerequisite_passed',canonical_accepted=False,full_ptpp=False,full_paper_mis=False,modes=[0,1,2,3],scene='owned opaque Room;177x91;4/4;seed47;8warmupframes',scope='Finite local lights; one uniform NEE proposal, full-prefix replay, stopped scene; no environment/infinite lights/transmission/binding diffuse cap',cases=len(results),source_files=len(source),exe_sha256=exe_hash,identity_tests=sum(x['counters']['identity_shift_tests'] for x in results),identity_failures=0,performance='not measured; diagnostic captures include readbacks',limits=['No continuous BSDF-light MIS companion or multi-candidate RIS/PSS integration.','No original-scene, motion/reset/resize, equal-time, bias or performance acceptance.','Mid-path mode rejected after the preserved eight-failure exploratory capture.'])
    (base/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))

if __name__=='__main__':main()
