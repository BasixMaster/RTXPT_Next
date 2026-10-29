"""Analyze matched GBuffer material precision; preserve every seed and paired delta."""
from pathlib import Path
import sys,json,statistics,math,hashlib
import numpy as np
r=Path(__file__).resolve().parents[1];repo=r/'outputs/RTXDI_Next';sys.path[:0]=[str(repo/'Benchmarks/tools'),str(r/'work/flip-evaluator')]
from analyze_hdr import read_pfm,compare,hdr_flip
from analyze_captures import quality_pair
base=r/'work/2026-10-29-gbuffer-precision-v2';refbase=r/'work/2026-10-29-finite-guard-original-resolution';params=json.loads((refbase/'quality-summary.json').read_text())['hdr_flip_parameters'];ys=np.array([.2126,.7152,.0722]);rows=[];groups=[];pairs=[]
for scene in ['convergence','kitchen']:
 refdir=refbase/scene/'reference4096';ref=read_pfm(next(refdir.glob('*.pfm')));refpng=next(refdir.glob('*.png'));ref_y=float((ref@ys).mean())
 for variant in ['B4','B7']:
  samples={}
  for rounded in [0,1]:
   selected=[]
   for seed in [0,11,47,1019,4093]:
    d=base/f'{scene}-{variant}-r{rounded}-s{seed}';m=json.loads((d/'manifest.json').read_text());assert m['measurement_status']=='captured' and m['artifact_identity_after_capture']['validated'];assert m['effective_gbuffer_precision']['rounded_materials']==rounded and m['effective_environment_filter']['diffuse_mip']==0
    pfm=next(p for p in d.glob('*.pfm') if not p.name.endswith('.native.pfm'));a=read_pfm(pfm);assert a.shape==ref.shape and np.isfinite(a).all();display=quality_pair(refpng,next(d.glob('*.png')),'accuracy_reference',None,True,67)
    row=dict(scene=scene,variant=variant,rounded=rounded,seed=seed,metrics=compare(ref,a),hdr_flip=hdr_flip(ref,a,params[scene]),ldr_flip=display['flip']['full_frame_mean'],signed_mean_y_percent=100*float(((a-ref)@ys).mean())/ref_y,pfm_sha256=hashlib.sha256(pfm.read_bytes()).hexdigest())
    if seed==0:
     native=read_pfm(next(d.glob('*.native.pfm')));row['same_frame_native_mean_y']=float((native@ys).mean());row['same_frame_post_native_addition_mean_y']=float(((a-native)@ys).mean())
    (d/'quality.json').write_text(json.dumps(row,indent=2,allow_nan=False)+'\n');rows.append(row);selected.append(row);samples[(rounded,seed)]=row
   delta=[x['signed_mean_y_percent'] for x in selected];groups.append(dict(scene=scene,variant=variant,rounded=rounded,n=5,mean_signed_y_percent=statistics.mean(delta),signed_y_sample_se=statistics.stdev(delta)/math.sqrt(5),median_hdr_flip=statistics.median(x['hdr_flip']['mean'] for x in selected),median_ldr_flip=statistics.median(x['ldr_flip'] for x in selected)))
   print('Completed quality group',scene,variant,rounded,flush=True)
  ds=[samples[1,s]['signed_mean_y_percent']-samples[0,s]['signed_mean_y_percent'] for s in [0,11,47,1019,4093]]
  fs=[samples[1,s]['hdr_flip']['mean']-samples[0,s]['hdr_flip']['mean'] for s in [0,11,47,1019,4093]]
  pairs.append(dict(scene=scene,variant=variant,n=5,mean_signed_y_change_percentage_points=statistics.mean(ds),signed_y_change_sample_se=statistics.stdev(ds)/math.sqrt(5),mean_hdr_flip_change=statistics.mean(fs),hdr_flip_change_sample_se=statistics.stdev(fs)/math.sqrt(5),caveat='Seed-paired process captures; not identical sampled paths or proof of unbiasedness'))
summary=dict(scope='Matched material quantization ablation, raw HDR; no timing or default promotion',groups=groups,paired_changes=pairs,rows=rows,hdr_flip_parameters=params,reference_source='2026-10-29-finite-guard-original-resolution')
(base/'quality-summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n');print(json.dumps(dict(groups=groups,paired_changes=pairs),indent=2),flush=True)
