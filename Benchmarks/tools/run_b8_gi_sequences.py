from pathlib import Path
import argparse,json,subprocess,sys

def main():
 p=argparse.ArgumentParser(description='Static64-frame B8 initial-GI versus NVIDIA GI reuse sequences; no timed results.');p.add_argument('--exe',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 r=Path(__file__).resolve().parents[2];base=a.output.resolve();base.mkdir(parents=True,exist_ok=False)
 room=str(r/'Testing/B2/Scenes/opaque-room-registered-env.scene.json');done=[]
 for scene_id,scene,w,h,b,d,e in [('room',room,640,360,4,4,0),('convergence','convergence-test.scene.json',1280,720,14,2,0),('kitchen','kitchen-with-test-stuff.scene.json',1280,720,14,2,2)]:
  for mode in (-1,3):
   label=f'{scene_id}-gi{mode}'
   cmd=[sys.executable,'-X','utf8','-B',str(r/'Benchmarks/tools/run_capture.py'),'--exe',str(a.exe.resolve()),'--output',str(base/label),'--label',label,'--scene',scene,'--width',str(w),'--height',str(h),'--max-bounces',str(b),'--max-diffuse-bounces',str(d),'--exposure',str(e),'--mode','dipt','--pt-mode','3','--di-mode','3','--nee-mis','0','--strict-di-validation','--b8-initial-gi-validation','--b8-validation-stage','1','--pt-fixed-spatial-samples','1','--linear-hdr','--stop-animations','--frames','64','--record-start','0.1','--sampling-seed','47','--environment-diffuse-mip','0','--app-uncapped','--timeout','600']
   if mode>=0:cmd+=['--b8-gi-reuse-mode',str(mode)]
   if scene!=room:cmd+=['--pt-extended-scene-validation','--pt-replay-only-validation']
   try:
    subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL)
    m=json.loads((base/label/'manifest.json').read_text());assert m['measurement_status']=='captured',m['measurement_status'];assert len(m['images'])==64
    done.append(label);(base/'completed.json').write_text(json.dumps(done,indent=2)+'\n')
   except BaseException as ex:
    (base/'failure.json').write_text(json.dumps(dict(case=label,type=type(ex).__name__,message=str(ex)),indent=2)+'\n');raise
   print('B8_SEQUENCE_PASSED '+label,flush=True)
if __name__=='__main__':main()
