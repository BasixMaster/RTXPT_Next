"""Bounded B8 NVIDIA-approximation validation; stop and preserve the first failure."""
from pathlib import Path
import argparse,json,subprocess,sys

def main():
 p=argparse.ArgumentParser();p.add_argument('--exe',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--full-scenes',action='store_true');p.add_argument('--verify-existing',action='store_true',help='Recheck retained captures without running the GPU');p.add_argument('--case',action='append',help='Run/recheck only selected case labels');a=p.parse_args()
 r=Path(__file__).resolve().parents[2];base=a.output.resolve();base.mkdir(parents=True,exist_ok=a.verify_existing)
 cases=[];room=str(r/'Testing/B2/Scenes/opaque-room-registered-env.scene.json')
 if not a.full_scenes:
  cases=[(f'room-gi{mode}',room,177,91,4,4,0,8,mode) for mode in (-1,0,1,2,3)]
  cases += [('room-first',room,177,91,4,4,0,1,3),('room-cap1',room,177,91,1,1,0,8,3),('room-cap2',room,177,91,2,2,0,8,3)]
 else:
  for scene,w,h,b,d,e in [(room,640,360,4,4,0),('convergence-test.scene.json',1280,720,14,2,0),('kitchen-with-test-stuff.scene.json',1280,720,14,2,2)]:
   scene_id='room' if scene==room else ('convergence' if 'convergence' in scene else 'kitchen')
   for mode in (-1,3):cases.append((f'{scene_id}-gi{mode}',scene,w,h,b,d,e,32,mode))
 if a.case:cases=[case for case in cases if case[0] in a.case]
 if a.verify_existing:cases=[case for case in cases if (base/case[0]/'manifest.json').is_file()]
 if not cases:raise ValueError('No selected captures')
 results=[]
 for label,scene,w,h,b,d,e,history,mode in cases:
  cmd=[sys.executable,'-X','utf8','-B',str(r/'Benchmarks/tools/run_capture.py'),'--exe',str(a.exe.resolve()),'--output',str(base/label),'--label',label,'--scene',scene,'--width',str(w),'--height',str(h),'--max-bounces',str(b),'--max-diffuse-bounces',str(d),'--exposure',str(e),'--mode','dipt','--pt-mode','3','--di-mode','3','--nee-mis','0','--strict-di-validation','--b8-initial-gi-validation','--b8-validation-stage','1','--pt-fixed-spatial-samples','1','--capture-pt-reservoirs','--capture-native-radiance','--linear-hdr','--simple','--history-frames',str(history),'--sampling-seed','47','--environment-diffuse-mip','0','--app-uncapped','--timeout','300']
  if mode>=0:cmd+=['--b8-gi-reuse-mode',str(mode)]
  if scene!=room:cmd+=['--pt-extended-scene-validation','--pt-replay-only-validation']
  try:
   if not a.verify_existing:subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL)
   m=json.loads((base/label/'manifest.json').read_text());assert m['measurement_status']=='captured',m['measurement_status']
   if mode>=0:
    import re
    dispatches = re.findall(r'B8_GI_DISPATCH frame=(\d+) mode=(\d+) temporal=(\d+) spatial=(\d+) history=(\d+)', (base/label/'renderer.log').read_text())
    assert dispatches and all(int(x[1]) == mode for x in dispatches), dispatches
    assert any(x[4]=='0' and x[2]=='0' for x in dispatches), 'Missing history reset guard'
    assert all(x[2]=='0' for x in dispatches if x[4]=='0'), 'GI read history after reset'
    if mode in (1,3) and history>1:assert any(x[2]=='1' and x[4]=='1' for x in dispatches), 'No temporal dispatch'
    assert all(int(x[3]) == int(mode in (2,3)) for x in dispatches), 'Wrong spatial schedule'
    stats=m['gi_reservoir_snapshots'][0]['statistics']
    if b>=2:assert stats['positive_weight']>0,stats
    if mode in (1,3) and history>1 and b>=2:assert stats['positive_age_valid']>0,stats
    if mode in (2,3) and b>=2:assert stats['m_greater_than_one']>0,stats
    if mode in (0,2):assert stats['positive_age_valid']==0,stats
    if b<2:assert stats['positive_weight']==0,stats
   else:stats=None
   results.append(dict(case=label,gi_mode=mode,gi_snapshot=stats,same_frame=m['b8_same_frame_checks']))
   (base/('revalidated-checks.json' if a.verify_existing else 'checks.json')).write_text(json.dumps(results,indent=2)+'\n')
  except BaseException as ex:
   (base/('revalidation-failure.json' if a.verify_existing else 'failure.json')).write_text(json.dumps(dict(case=label,type=type(ex).__name__,message=str(ex),policy='First failure retained; no automatic retries'),indent=2)+'\n');raise
  print('B8_GI_CHECK_PASSED '+label,flush=True)
if __name__=='__main__':main()
