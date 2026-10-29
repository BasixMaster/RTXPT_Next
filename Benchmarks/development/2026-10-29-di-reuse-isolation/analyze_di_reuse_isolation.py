"""Score completed captures while acquisition runs; fixed cases, fail closed, no timing claims."""
from pathlib import Path
import sys,json,time,statistics,math,hashlib
import numpy as np
r=Path(__file__).resolve().parents[1];repo=r/'outputs/RTXDI_Next';sys.path[:0]=[str(repo/'Benchmarks/tools'),str(r/'work/flip-evaluator')]
from analyze_hdr import read_pfm,compare,hdr_flip
from analyze_captures import quality_pair
base=r/'work/2026-10-29-di-reuse-isolation';refbase=r/'work/2026-10-29-finite-guard-original-resolution';params=json.loads((refbase/'quality-summary.json').read_text())['hdr_flip_parameters'];ys=np.array([.2126,.7152,.0722]);refs={};completed={};deadline=time.monotonic()+3600
for scene in ['convergence','kitchen']:
 d=refbase/scene/'reference4096';pfm=next(d.glob('*.pfm'));a=read_pfm(pfm);refs[scene]=(a,next(d.glob('*.png')),float((a@ys).mean()),hashlib.sha256(pfm.read_bytes()).hexdigest())
cases=[(scene,variant,mode,seed) for seed in [0,11,47,1019,4093] for scene in ['convergence','kitchen'] for variant in ['B4','B7'] for mode in range(4)]
while len(completed)<len(cases):
 progressed=False
 for case in cases:
  if case in completed:continue
  scene,variant,mode,seed=case;label=f'{scene}-{variant}-di{mode}-s{seed}';d=base/label;manifest=d/'manifest.json'
  if not manifest.exists():continue
  try:m=json.loads(manifest.read_text())
  except json.JSONDecodeError:continue
  if m['measurement_status']=='running':continue
  if m['measurement_status']!='captured':
   (base/'analysis-failure.json').write_text(json.dumps(dict(failed_case=label,status=m['measurement_status'],renderer_exit=m.get('renderer_exit_code'),completed=len(completed)),indent=2)+'\n',encoding='utf-8');raise RuntimeError('Acquisition failed; preserved incomplete study: '+label)
  assert m['artifact_identity']['validated'] and m['artifact_identity_after_capture']['validated'] and m['artifact_identity']==m['artifact_identity_after_capture'];assert m['effective_di_reuse']['active'] and m['effective_di_reuse']['mode']==mode;assert m['effective_gbuffer_precision']['rounded_materials']==0 and m['effective_environment_filter']['diffuse_mip']==0
  pfm=next(p for p in d.glob('*.pfm') if not p.name.endswith('.native.pfm'));a=read_pfm(pfm);ref,refpng,ref_y,refsha=refs[scene];assert a.shape==ref.shape and np.isfinite(a).all()
  display=quality_pair(refpng,next(d.glob('*.png')),'accuracy_reference',None,True,67)
  row=dict(scene=scene,variant=variant,di_mode=mode,seed=seed,metrics=compare(ref,a),hdr_flip=hdr_flip(ref,a,params[scene]),ldr_flip=display['flip']['full_frame_mean'],signed_mean_y_percent=100*float(((a-ref)@ys).mean())/ref_y,pfm_sha256=hashlib.sha256(pfm.read_bytes()).hexdigest(),reference_pfm_sha256=refsha)
  if seed==0:
   native=read_pfm(next(d.glob('*.native.pfm')));row['same_frame_components']=dict(native_mean_y=float((native@ys).mean()),post_native_addition_mean_y=float(((a-native)@ys).mean()),total_mean_y=float((a@ys).mean()),scope='Total minus same-frame pre-resampling native radiance; B4 addition is DI, B7 addition includes both DI and PT. Not separate-process component subtraction.')
  (d/'quality.json').write_text(json.dumps(row,indent=2,allow_nan=False)+'\n',encoding='utf-8');completed[case]=row;progressed=True
  print('Scored',label,flush=True)
 if not progressed:
  if time.monotonic()>deadline:raise TimeoutError('Fixed-case analysis deadline reached; no automatic retries')
  time.sleep(2)
rows=[completed[c] for c in cases];groups=[];contrasts=[]
for scene in ['convergence','kitchen']:
 for variant in ['B4','B7']:
  for mode in range(4):
   subset=[x for x in rows if (x['scene'],x['variant'],x['di_mode'])==(scene,variant,mode)];deltas=[x['signed_mean_y_percent'] for x in subset]
   groups.append(dict(scene=scene,variant=variant,di_mode=mode,n=5,mean_signed_y_percent=statistics.mean(deltas),signed_y_sample_se=statistics.stdev(deltas)/math.sqrt(5),median_hdr_flip=statistics.median(x['hdr_flip']['mean'] for x in subset),median_ldr_flip=statistics.median(x['ldr_flip'] for x in subset)))
  for mode in [1,2,3]:
   differences=[completed[scene,variant,mode,seed]['signed_mean_y_percent']-completed[scene,variant,0,seed]['signed_mean_y_percent'] for seed in [0,11,47,1019,4093]]
   contrasts.append(dict(scene=scene,variant=variant,di_mode=mode,reference_mode=0,mean_signed_y_change_percentage_points=statistics.mean(differences),signed_y_change_sample_se=statistics.stdev(differences)/math.sqrt(5),scope='Seed-paired process captures; not identical sampled paths'))
summary=dict(scope='DI reuse-mode isolation, unchanged renderer, fixed1spp history64; no throughput, default promotion or unbiasedness proof',rows=rows,groups=groups,contrasts_vs_initial=contrasts,hdr_flip_parameters=params,reference_source='2026-10-29-finite-guard-original-resolution')
(base/'quality-summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8');print(json.dumps(dict(groups=groups,contrasts=contrasts),indent=2),flush=True)
