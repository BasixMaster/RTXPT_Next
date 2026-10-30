from pathlib import Path
import argparse,json,subprocess,sys,hashlib
from b9_limited_contract import verify,check_roulette
from inspect_pt_reservoirs import inspect
import numpy as np

def main():
 p=argparse.ArgumentParser(description='B9-on-B8 GPU diagnostics and exact B8 host-regression controls.');p.add_argument('--exe',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--previous-b8',type=Path,help='Optional previous B8 workspace work directory for exact control comparison');a=p.parse_args()
 r=Path(__file__).resolve().parents[2];base=a.output.resolve();base.mkdir(parents=True,exist_ok=False);room=str(r/'Testing/B2/Scenes/opaque-room-registered-env.scene.json');results=[]
 cases=[]
 for scene,filename,w,h,b,d,e in [('room',room,640,360,4,4,0),('convergence','convergence-test.scene.json',1280,720,14,2,0),('kitchen','kitchen-with-test-stuff.scene.json',1280,720,14,2,2)]:
  for version in ('B8','B9'):cases.append((scene,filename,w,h,b,d,e,version))
 cases += [('room-cap1',room,177,91,1,1,0,'B9'),('room-cap2',room,177,91,2,2,0,'B9')]
 for scene,filename,w,h,b,d,e,version in cases:
  label=scene+'-'+version;extended=filename!=room;stage=1 if version=='B8' else (3 if extended else 2)
  cmd=[sys.executable,'-X','utf8','-B',str(r/'Benchmarks/tools/run_capture.py'),'--exe',str(a.exe.resolve()),'--output',str(base/label),'--label',label,'--scene',filename,'--width',str(w),'--height',str(h),'--max-bounces',str(b),'--max-diffuse-bounces',str(d),'--exposure',str(e),'--mode','dipt','--pt-mode','3','--di-mode','3','--nee-mis','0','--strict-di-validation','--b8-initial-gi-validation','--b8-gi-reuse-mode','3','--b8-validation-stage',str(stage),'--pt-reconnection-mode',str(int(stage==2)),'--pt-roulette-probability',str(.8 if version=='B9' else 0),'--pt-fixed-spatial-samples','1','--capture-pt-reservoirs','--capture-native-radiance','--linear-hdr','--simple','--history-frames','32','--sampling-seed','47','--environment-diffuse-mip','0','--app-uncapped','--timeout','300']
  if extended:cmd+=['--pt-extended-scene-validation','--pt-replay-only-validation']
  try:
   subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL)
   folder=base/label;m=json.loads((folder/'manifest.json').read_text());assert m['measurement_status']=='captured',m['measurement_status']
   contract=verify((folder/'renderer.log').read_text(),stage);stats=json.loads(next(folder.glob('*.stats.json')).read_text());roulette=check_roulette(stats,version=='B9',allow_empty=b<3)
   assert stats['hybrid_returned_nonfinite_weight_product']==0
   gi=m['gi_reservoir_snapshots'][0]['statistics']
   if b>=2:assert gi['positive_age_valid']>0
   ptfile=next(folder.glob('*.pt.bin'));meta=json.loads(Path(str(ptfile)+'.json').read_text());pt=inspect(np.frombuffer(ptfile.read_bytes(),'<u4').reshape(-1,16),meta)
   final=pt['final_index'];assert final['nonfinite_weight_valid']==0 and final['nonfinite_target_valid']==0
   if b>=3 and version=='B9' and not extended:assert final['midpath_reconnection_valid']>0
   if extended:assert final['midpath_reconnection_valid']==0
   exact=None
   if version=='B8' and a.previous_b8:
    parent='2026-10-29-b8-gi-approx-full' if scene=='room' else '2026-10-29-b8-gi-approx-full-continuation';old=a.previous_b8/parent/(scene+'-gi3');oldpath=next(p for p in old.glob('*.pfm') if '.pfm.' not in p.name);newpath=next(p for p in folder.glob('*.pfm') if '.pfm.' not in p.name)
    exact=hashlib.sha256(oldpath.read_bytes()).hexdigest()==hashlib.sha256(newpath.read_bytes()).hexdigest();assert exact,'B8 raw control changed'
   results.append(dict(case=label,stage=stage,contract=contract,roulette=roulette,gi=gi,pt=pt,exact_previous_b8=exact,same_frame=m['b8_same_frame_checks']))
   (base/'checks.json').write_text(json.dumps(results,indent=2)+'\n')
  except BaseException as ex:
   (base/'failure.json').write_text(json.dumps(dict(case=label,type=type(ex).__name__,message=str(ex),policy='Stop and preserve the first failure'),indent=2)+'\n');raise
  print('B9_GPU_PASSED '+label,flush=True)
if __name__=='__main__':main()
