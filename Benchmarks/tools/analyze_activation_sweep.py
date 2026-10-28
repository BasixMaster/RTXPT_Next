"""Score a predeclared PT++ history sweep against one frozen raw-HDR reference."""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np
from analyze_hdr import read_pfm, compare, hdr_flip


def analyze(base, reference_path, parameters):
    plan=json.loads((base/'plan.json').read_text(encoding='utf-8'))
    reference=read_pfm(reference_path);weights=np.array([.2126,.7152,.0722]);mu=float((reference@weights).mean())
    rows=[];identities=set()
    # Enumerate the declared domain; an absent capture is a failure, never silently omitted.
    for mode in plan['reuse_modes']:
        for history in (plan['history_frames'] if mode==3 else [64]):
            for variant in plan['variants']:
                for seed in plan['seeds']:
                    name=f'{variant}-r{mode}-h{history}-s{seed}';folder=base/name
                    manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
                    if manifest['measurement_status']!='captured':raise ValueError('Incomplete capture: '+name)
                    identities.add(manifest['exe_sha256'])
                    files=[p for p in folder.glob('*.pfm') if not p.name.endswith('.native.pfm')]
                    if len(files)!=1:raise ValueError('Expected one raw image: '+name)
                    path=files[0];image=read_pfm(path)
                    result=dict(case=name,variant=variant,seed=seed,reuse_mode=mode,history_frames=history,
                        metrics=compare(reference,image),hdr_flip=hdr_flip(reference,image,parameters),
                        signed_mean_y_percent=100*float(((image-reference)@weights).mean()/mu),
                        image_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                        reference_sha256=hashlib.sha256(reference_path.read_bytes()).hexdigest())
                    (folder/'quality.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
                    rows.append(result);print(name,result['metrics']['linear_rgb_mse'],result['hdr_flip']['mean'],flush=True)
    if len(identities)!=1:raise ValueError('Mixed executable identities in one sweep')
    activation={}
    from inspect_pt_reservoirs import inspect
    for variant,(_,probability) in plan['variants'].items():
        folder=base/f'{variant}-r3-h64-s0';bins=list(folder.glob('*.pt.bin'))
        if len(bins)!=1:raise ValueError('Missing activation reservoir snapshot: '+variant)
        binary=bins[0];meta=json.loads(Path(str(binary)+'.json').read_text())
        counters=json.loads(Path(str(binary)+'.stats.json').read_text())
        if counters['replay_roulette_tests']!=0:raise ValueError('Roulette ran during replay')
        if counters['roulette_tests']!=counters['roulette_terminated']+counters['roulette_survived']:
            raise ValueError('Roulette counter conservation failed')
        if 0 < probability < 1 and (counters['roulette_terminated']==0 or counters['roulette_survived']==0):
            raise ValueError('Requested roulette did not exercise both branches')
        if probability==0 and counters['roulette_tests']!=0:raise ValueError('Roulette active in control')
        raw=binary.read_bytes();statistics=inspect(np.frombuffer(raw,'<u4').reshape(-1,16),meta)
        if any(slot['nonfinite_m'] or slot['nonfinite_weight_valid'] or slot['nonfinite_target_valid'] for slot in statistics.values()):
            raise ValueError('Nonfinite packed reservoir state in '+variant)
        if statistics['final_index']['midpath_reconnection_valid']==0:
            raise ValueError('No active mid-path reconnection in '+variant)
        activation[variant]=dict(counters=counters,metadata=meta,statistics=statistics,binary_sha256=hashlib.sha256(raw).hexdigest())
        (folder/'reservoir-summary.json').write_text(json.dumps(activation[variant],indent=2,allow_nan=False)+'\n',encoding='utf-8')
    groups=[]
    for mode in plan['reuse_modes']:
        for history in (plan['history_frames'] if mode==3 else [64]):
            for variant in plan['variants']:
                sample=[row for row in rows if (row['reuse_mode'],row['history_frames'],row['variant'])==(mode,history,variant)]
                groups.append(dict(variant=variant,reuse_mode=mode,history_frames=history,trials=len(sample),
                    median_linear_rgb_mse=float(np.median([x['metrics']['linear_rgb_mse'] for x in sample])),
                    median_hdr_flip=float(np.median([x['hdr_flip']['mean'] for x in sample])),
                    mean_signed_y_percent=float(np.mean([x['signed_mean_y_percent'] for x in sample])),
                    mse_range=[min(x['metrics']['linear_rgb_mse'] for x in sample),max(x['metrics']['linear_rgb_mse'] for x in sample)]))
    summary=dict(status='exploratory static opaque activation pilot; B3 not promoted',exe_sha256=identities.pop(),groups=groups,
        reference_sha256=hashlib.sha256(reference_path.read_bytes()).hexdigest(),flip_parameters=parameters,
        scope='Separate 1spp captures after declared history warmup, not frame averaging, equal-time convergence or a proof of unbiasedness',
        original_scenes=plan['original_scene_coverage'],activation=activation)
    (base/'quality-summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    return summary


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--captures',type=Path,required=True)
    ap.add_argument('--reference',type=Path,required=True);ap.add_argument('--flip-parameters',type=Path,required=True)
    args=ap.parse_args();analyze(args.captures,args.reference,json.loads(args.flip_parameters.read_text()))
