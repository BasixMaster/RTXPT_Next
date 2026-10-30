"""Validate the opt-in initial-only roulette with unified finite/environment RIS/PSS MIS; not full PT++ or a timing benchmark."""
from pathlib import Path
import argparse,json,subprocess,sys,hashlib
import numpy as np
from unified_roulette_contract import check_counters
from inspect_pt_reservoirs import inspect
from analyze_hdr import read_pfm

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--exe',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--candidates',type=int,choices=range(1,33),default=4);p.add_argument('--modes',type=int,nargs='+',choices=range(4),default=[0,1,2,3]);a=p.parse_args()
    repo=Path(__file__).resolve().parents[2];base=a.output.resolve();base.mkdir(parents=True,exist_ok=False)
    exe=a.exe.resolve();scene=repo/'Testing/B2/Scenes/opaque-room-unified-env.scene.json'
    # Source identities are separate from shader caches, which may compile on demand.
    source={x.relative_to(repo).as_posix():digest(x) for folder in [repo/'Rtxpt',repo/'Testing/B2/Scenes'] for x in folder.rglob('*') if x.is_file() and x.suffix in ['.h','.cpp','.hlsl','.hlsli','.json','.gltf','.bin']}
    exe_hash=digest(exe);results=[]
    (base/'source-inputs.json').write_text(json.dumps(source,indent=2)+'\n')
    for mode in a.modes:
        label=f'room-unified-rr-m{a.candidates}-mode{mode}';out=base/label
        cmd=[sys.executable,'-X','utf8','-B',str(repo/'Benchmarks/tools/run_capture.py'),'--exe',str(exe),'--output',str(out),'--label',label,'--scene',str(scene),'--width','177','--height','91','--exposure','0','--mode','pt','--pt-mode',str(mode),'--pt-unified-mis-validation','--pt-unified-roulette-validation','--pt-roulette-probability','0.8','--pt-unified-environment-validation','--pt-unified-ris-candidates',str(a.candidates),'--pt-replay-only-validation','--pt-reconnection-mode','0','--pt-fixed-spatial-samples','1','--linear-hdr','--capture-native-radiance','--capture-pt-reservoirs','--simple','--history-frames','8','--max-bounces','4','--max-diffuse-bounces','4','--sampling-seed','47','--environment-diffuse-mip','0','--app-uncapped','--timeout','600']
        subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL)
        m=json.loads((out/'manifest.json').read_text());assert m['measurement_status']=='captured',m['measurement_status']
        assert m['exe_sha256']==exe_hash and m['effective_unified_mis']['active'] and m['effective_unified_ris']['candidates']==a.candidates
        binary=next(out.glob('*.pt.bin'));raw=binary.read_bytes();meta=json.loads(Path(str(binary)+'.json').read_text())
        words=np.frombuffer(raw,'<u4').reshape(-1,16);stats=inspect(words,meta)
        counters=json.loads(Path(str(binary)+'.stats.json').read_text())
        check_counters(counters)
        assert m['effective_unified_roulette']['active']
        assert counters['identity_shift_tests']>0 and counters['identity_shift_failures']==0,counters
        for s in stats.values():assert s['nonfinite_m']==s['nonfinite_weight_valid']==s['nonfinite_target_valid']==0
        initial=stats['initial_preserved_index'];final=stats['final_index']
        y,x=np.indices((meta['height'],meta['width']),dtype=np.int64)
        address=(y//16)*meta['block_row_pitch']+(x//16)*256+(y%16)*16+x%16+meta['initial_preserved_index']*meta['array_pitch']
        selected=words[address];weight=selected[...,3].copy().view('<f4')
        rc=(selected[...,11]>>8)&255;length=(selected[...,11]>>16)&255
        bsdf_pure_replay=int(((weight>0)&(rc>length)).sum())
        nee_terminal=int(((weight>0)&(rc==length)).sum())
        assert bsdf_pure_replay>0 and nee_terminal>0,(bsdf_pure_replay,nee_terminal)
        frame_env=m['effective_unified_environment']['lights_by_frame'][str(meta['frame_index'])]
        light_ids=selected[...,9]&0x7fffffff
        nee_mask=(weight>0)&(rc==length)
        env_nee=int((nee_mask&(light_ids==frame_env['lightIndex'])).sum())
        finite_nee=int((nee_mask&(light_ids!=frame_env['lightIndex'])).sum())
        env_miss=int(((weight>0)&(rc>length)&(selected[...,7].copy().view('<f4')==-1.)).sum())
        assert env_nee>0 and finite_nee>0 and env_miss>0,(env_nee,finite_nee,env_miss)
        ucw=selected[...,7].copy().view('<f4')
        nee_mask=(weight>0)&(rc==length)
        assert np.isfinite(ucw[nee_mask]).all() and (ucw[nee_mask]>0).all()
        if a.candidates==1:assert np.allclose(ucw[nee_mask],1.,rtol=1e-6,atol=1e-6)
        else:assert np.count_nonzero(np.abs(ucw[nee_mask]-1.)>1e-3)>0
        ucw_stats=dict(min=float(ucw[nee_mask].min()),max=float(ucw[nee_mask].max()),mean=float(ucw[nee_mask].mean()),nonunit_count=int(np.count_nonzero(np.abs(ucw[nee_mask]-1.)>1e-3)))
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
        results.append(dict(label=label,mode=mode,passed=True,full_paper_mis=False,continuous_bsdf_mis=True,ris_candidates=a.candidates,pss_ucw_conversion=True,initial_only_roulette=.8,pss_ucw_statistics=ucw_stats,environment_nee_selected=env_nee,finite_nee_selected=finite_nee,environment_miss_selected=env_miss,bsdf_pure_replay_selected=bsdf_pure_replay,nee_terminal_selected=nee_terminal,statistics=stats,counters=counters,raw_hdr_sha256=digest(pfm),image_mean=float(image.mean()),native_nonzero_pixels=int(np.count_nonzero(native.max(2)>0)),native_plus_pt_monotone=True,exe_sha256=exe_hash))
        (base/'results.json').write_text(json.dumps(results,indent=2)+'\n')
        assert digest(exe)==exe_hash
        for name,expected in source.items():assert digest(repo/name)==expected,name
        print('UNIFIED_ROULETTE_GATE_PASSED '+label,flush=True)
    summary=dict(status='scoped_gpu_prerequisite_passed',canonical_accepted=False,full_ptpp=False,full_paper_mis=False,modes=a.modes,ris_candidates=a.candidates,pss_ucw_conversion=True,scene='owned opaque Room;177x91;4/4;seed47;8warmupframes',scope='Finite local lights; uniform multi-candidate RIS with complementary BSDF hits and explicit PSS UCW, full-prefix replay, stopped scene with positive environment; no infinite analytic lights/transmission/binding diffuse cap',cases=len(results),source_files=len(source),exe_sha256=exe_hash,identity_tests=sum(x['counters']['identity_shift_tests'] for x in results),identity_failures=0,performance='not measured; diagnostic captures include readbacks',limits=['Static finite+MIP environment RIS/PSS MIS; initial-only roulette composed; other combinations remain pending.','No original-scene, motion/reset/resize, equal-time, bias or performance acceptance.','Mid-path mode remains excluded; earlier NEE-only exploratory failures retained separately.'])
    (base/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))

if __name__=='__main__':main()
