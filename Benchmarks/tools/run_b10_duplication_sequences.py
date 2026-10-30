from pathlib import Path
import argparse,json,subprocess,sys
from output_space import require_space

def main():
 p=argparse.ArgumentParser(description='B10 duplication: three-seed64-frame static sequences, on/off map history reduction.');p.add_argument('--exe',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 r=Path(__file__).resolve().parents[2];base=a.output.resolve();space=require_space(base,16*1024**3);base.mkdir(parents=True,exist_ok=False)
 (base/'space-preflight.json').write_text(json.dumps(space,indent=2)+'\n')
 room=str(r/'Testing/B2/Scenes/opaque-room-registered-env.scene.json');done=[]
 scenes=[('room',room,640,360,4,4,0),('convergence','convergence-test.scene.json',1280,720,14,2,0),('kitchen','kitchen-with-test-stuff.scene.json',1280,720,14,2,2)]
 for seed_index,seed in enumerate((47,1019,4093)):
  for scene_id,scene,w,h,b,d,e in scenes:
   for version in (('off','on') if seed_index!=1 else ('on','off')):
    label=f'{scene_id}-{version}-s{seed}';stage=2 if scene==room else 3
    cmd=[sys.executable,'-X','utf8','-B',str(r/'Benchmarks/tools/run_capture.py'),'--exe',str(a.exe.resolve()),'--output',str(base/label),'--label',label,'--scene',scene,'--width',str(w),'--height',str(h),'--max-bounces',str(b),'--max-diffuse-bounces',str(d),'--exposure',str(e),'--mode','dipt','--pt-mode','3','--di-mode','3','--nee-mis','0','--strict-di-validation','--b8-initial-gi-validation','--b8-gi-reuse-mode','3','--b8-validation-stage',str(stage),'--pt-reconnection-mode',str(int(stage==2)),'--pt-roulette-probability',str(.8),'--pt-fixed-spatial-samples','1','--linear-hdr','--stop-animations','--frames','64','--record-start','0.1','--sampling-seed',str(seed),'--environment-diffuse-mip','0','--app-uncapped','--timeout','600']
    cmd+=['--pt-paired-spatial-validation','--pt-gaussian-pairing-validation','--pt-replay-compaction-validation']
    if version=='on':cmd+=['--pt-duplication-history-validation']
    if scene!=room:cmd+=['--pt-extended-scene-validation','--pt-replay-only-validation']
    try:
     subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL)
     m=json.loads((base/label/'manifest.json').read_text());assert m['measurement_status']=='captured',m['measurement_status'];assert len(m['images'])==64
     from duplication_contract import verify
     verify((base/label/'renderer.log').read_text(),version=='on')
     done.append(label);(base/'completed.json').write_text(json.dumps(done,indent=2)+'\n')
    except BaseException as ex:
     (base/'failure.json').write_text(json.dumps(dict(case=label,type=type(ex).__name__,message=str(ex)),indent=2)+'\n');raise
    print('B10_DUPLICATION_SEQUENCE_PASSED '+label,flush=True)
if __name__=='__main__':main()
