from pathlib import Path
import sys,json,hashlib,argparse,numpy as np
from PIL import Image
ap=argparse.ArgumentParser(description='Evaluate retained B8 static sequences against frozen native references; no brightness fitting.')
ap.add_argument('--sequences-root',type=Path,required=True);ap.add_argument('--policy',type=Path,required=True,help='Frozen quality.json containing reference hashes and reference-derived HDR-FLIP parameters')
for name in ('room','convergence','kitchen'):ap.add_argument('--reference-'+name,type=Path)
ap.add_argument('--scenes',nargs='+',choices=['room','convergence','kitchen'],default=['room','convergence','kitchen']);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--flip-module-dir',type=Path)
a=ap.parse_args()
if a.output.exists():raise SystemExit('Output must be new; preserve prior evaluations')
if a.flip_module_dir:sys.path.insert(0,str(a.flip_module_dir.resolve()))
import flip_evaluator as evaluator
from analyze_hdr import read_pfm,hdr_flip,compare
base=a.sequences_root;out=a.output;out.parent.mkdir(parents=True,exist_ok=True)
policy=json.loads(a.policy.read_text());params={}
for scene in a.scenes:
 group=next(iter(policy['groups'][scene].values()));params[scene]=dict(reference_sha256=group['reference_sha256'],hdr_parameters=group['selected_frame_flip'][0]['hdr_flip']['parameters'])
results={}
for scene in a.scenes:
 refdir=getattr(a,'reference_'+scene)
 if refdir is None:raise ValueError('Selected scene requires its native reference directory')
 rp=next(refdir.glob('*.pfm'));ref=read_pfm(rp);refsha=hashlib.sha256(rp.read_bytes()).hexdigest();assert refsha==params[scene]['reference_sha256']
 display=np.asarray(Image.open(next(refdir.glob('*.png'))).convert('RGB'),np.float32)/255.;refy=float((ref@np.array([.2126,.7152,.0722])).mean());groups={}
 for mode in (-1,3):
  label=f'{scene}-gi{mode}';folder=base/label;m=json.loads((folder/'manifest.json').read_text());assert m['measurement_status']=='captured'
  paths=sorted(folder.glob('*.pfm'));assert len(paths)==64
  total=np.zeros_like(ref);curves=[];selected=[]
  for i,p in enumerate(paths,1):
   image=read_pfm(p);metrics=compare(ref,image);total+=image;average=total/i
   curves.append(dict(frame=i,pfm=p.name,pfm_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),linear_mse=metrics['linear_rgb_mse'],mean_image_mse=compare(ref,average)['linear_rgb_mse'],mean_y_difference_percent=100*((image@np.array([.2126,.7152,.0722])).mean()/refy-1)))
   if i in (1,8,32,64):
    png=p.with_suffix('.png');img=np.asarray(Image.open(png).convert('RGB'),np.float32)/255.
    _,ldr,_=evaluator.evaluate(display,img,'LDR',inputsRGB=True,applyMagma=False,computeMeanError=True,parameters=dict(ppd=67.))
    selected.append(dict(frame=i,hdr_flip=hdr_flip(ref,image,params[scene]['hdr_parameters']),ldr_flip=float(ldr),png_sha256=hashlib.sha256(png.read_bytes()).hexdigest()))
  mean_metrics=compare(ref,total/64)
  groups[label]=dict(frames=64,source_exe_sha256=m['exe_sha256'],scene_sha256=m['scene_sha256'],reference_sha256=refsha,actual_resolution=[ref.shape[1],ref.shape[0]],gi_mode=mode,curve=curves,selected_frame_flip=selected,mean_frame_linear_mse=float(np.mean([v['linear_mse'] for v in curves])),mean_image_metrics=mean_metrics,mean_image_hdr_flip=hdr_flip(ref,total/64,params[scene]['hdr_parameters']),mean_y_difference_percent=float(np.mean([v['mean_y_difference_percent'] for v in curves])),representative=paths[-1].with_suffix('.png').name)
  print('QUALITY_COMPLETE '+label,flush=True)
 results[scene]=groups
 out.write_text(json.dumps(dict(status='development_not_promoted',scope='One static64-frame sequence per scene/mode, seed47; frame averaging curves, not equal-time convergence or independent replication; GI approximations retained; no brightness fitting',groups=results),indent=2,allow_nan=False)+'\n')
