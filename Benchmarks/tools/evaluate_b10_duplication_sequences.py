from pathlib import Path
import json,sys,argparse,hashlib,statistics,numpy as np
from PIL import Image
from analyze_hdr import read_pfm,hdr_flip,compare
from duplication_contract import verify

def main():
 ap=argparse.ArgumentParser(description='Three-seed B10 duplication on/off quality; explicit biased development ablation.')
 ap.add_argument('--sequences-root',type=Path,required=True);ap.add_argument('--policy',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--flip-module-dir',type=Path)
 for name in ('room','convergence','kitchen'):ap.add_argument('--reference-'+name,type=Path,required=True)
 ap.add_argument('--case-index',type=Path,help='Explicit relative paths for preserved captures and separately acquired continuation cases')
 a=ap.parse_args()
 case_paths=json.loads(a.case_index.read_text()) if a.case_index else {}
 if a.output.exists():raise ValueError('Output must be new; preserve earlier evaluations')
 if a.flip_module_dir:sys.path.insert(0,str(a.flip_module_dir.resolve()))
 import flip_evaluator as evaluator
 policy=json.loads(a.policy.read_text());result=dict(schema_version=1,status='development_partial',scope='Three seeds47/1019/4093, one64-frame static sequence per version/scene/seed; distinct no-image-write timing cohort; no brightness fitting. Both policies: paired Gaussian spatial queue, initial roulette0.8 and B8 GI3; Room footprint, originals full-prefix replay. Only duplication temporal history reduction changes.',scenes={})
 for scene in ('room','convergence','kitchen'):
  refdir=getattr(a,'reference_'+scene);rp=next(refdir.glob('*.pfm'));ref=read_pfm(rp);refsha=hashlib.sha256(rp.read_bytes()).hexdigest();prior=next(iter(policy['groups'][scene].values()));assert refsha==prior['reference_sha256'];params=prior['selected_frame_flip'][0]['hdr_flip']['parameters']
  display=np.asarray(Image.open(next(refdir.glob('*.png'))).convert('RGB'),np.float32)/255.;ref_y=float((ref@np.array([.2126,.7152,.0722])).mean());groups={}
  for version in ('off','on'):
   for seed in (47,1019,4093):
    label=f'{scene}-{version}-s{seed}';folder=(a.sequences_root/case_paths.get(label,label)).resolve();assert folder.is_relative_to(a.sequences_root.resolve());m=json.loads((folder/'manifest.json').read_text());assert m['measurement_status']=='captured' and m['effective_sampling']['seed']==seed;contract=verify((folder/'renderer.log').read_text(),version=='on')
    paths=sorted(folder.glob('*.pfm'));assert len(paths)==64;total=np.zeros_like(ref);curves=[];selected=[]
    for i,p in enumerate(paths,1):
     image=read_pfm(p);metrics=compare(ref,image);total+=image;average=total/i
     curves.append(dict(frame=i,pfm=p.name,pfm_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),linear_mse=metrics['linear_rgb_mse'],mean_image_mse=compare(ref,average)['linear_rgb_mse'],mean_y_difference_percent=100*((image@np.array([.2126,.7152,.0722])).mean()/ref_y-1)))
     if i in (1,8,32,64):
      png=p.with_suffix('.png');img=np.asarray(Image.open(png).convert('RGB'),np.float32)/255.;_,ldr,_=evaluator.evaluate(display,img,'LDR',inputsRGB=True,applyMagma=False,computeMeanError=True,parameters=dict(ppd=67.))
      selected.append(dict(frame=i,hdr_flip=hdr_flip(ref,image,params),ldr_flip=float(ldr),png_sha256=hashlib.sha256(png.read_bytes()).hexdigest()))
    groups[label]=dict(version=version,seed=seed,frames=64,source_exe_sha256=m['exe_sha256'],scene_sha256=m['scene_sha256'],reference_sha256=refsha,actual_resolution=[ref.shape[1],ref.shape[0]],contract=contract,curve=curves,selected_frame_flip=selected,mean_frame_linear_mse=float(np.mean([v['linear_mse'] for v in curves])),mean_image_metrics=compare(ref,total/64),mean_image_hdr_flip=hdr_flip(ref,total/64,params),mean_y_difference_percent=float(np.mean([v['mean_y_difference_percent'] for v in curves])),representative=paths[-1].with_suffix('.png').name)
    print('DUPLICATION_QUALITY_EVALUATED '+label,flush=True)
  summaries={}
  for version in ('off','on'):
   values=[v for v in groups.values() if v['version']==version];summary=dict(runs=3,seeds=[v['seed'] for v in values])
   metrics=dict(mean_frame_linear_mse=[v['mean_frame_linear_mse'] for v in values],mean_image_linear_mse=[v['mean_image_metrics']['linear_rgb_mse'] for v in values],mean_y_difference_percent=[v['mean_y_difference_percent'] for v in values],frame64_hdr_flip=[v['selected_frame_flip'][-1]['hdr_flip']['mean'] for v in values],frame64_ldr_flip=[v['selected_frame_flip'][-1]['ldr_flip'] for v in values])
   for metric,numbers in metrics.items():summary[metric]=dict(mean=statistics.mean(numbers),median=statistics.median(numbers),sample_se=statistics.stdev(numbers)/len(numbers)**.5,values=numbers)
   summaries[version]=summary
  result['scenes'][scene]=dict(reference_sha256=refsha,groups=groups,summary=summaries)
  a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
if __name__=='__main__':main()
