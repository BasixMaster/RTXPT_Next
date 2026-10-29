"""Bounded same-frame direct/queue GPU oracle suite, no benchmark promotion."""
from pathlib import Path
import sys,subprocess,json
import argparse
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--exe',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
repo=Path(__file__).resolve().parents[2];tools=repo/'Benchmarks/tools';sys.path.insert(0,str(tools))
if a.output.resolve().is_relative_to(repo):raise SystemExit('Raw host telemetry requires a private output outside the repository')
if not a.exe.is_file():raise SystemExit('Renderer executable missing')
from replay_queue_contract import check_counters
from paired_pilot_contract import check_counters as pair_counters
base=a.output.resolve();base.mkdir(parents=True,exist_ok=False)
room=str(repo/'Testing/B2/Scenes/opaque-room-registered-env.scene.json')
cases=[('room-first',room,176,90,4,4,0,1,2,1,False),('room-h8',room,176,90,4,4,0,8,2,1,False),('zero-cap1',room,176,90,1,1,0,8,2,1,False),('zero-cap2',room,176,90,2,2,0,8,2,1,False),('odd-edge',room,177,91,4,4,0,8,2,1,False),('tiny-edge',room,177,3,4,4,0,1,2,1,False),('gaussian',room,176,90,4,4,0,8,2,1,True),('temporal',room,176,90,4,4,0,8,3,1,False),('roulette',room,176,90,4,4,0,8,3,2,True),('convergence','convergence-test.scene.json',1280,720,14,2,0,8,2,1,True),('kitchen','kitchen-with-test-stuff.scene.json',1280,720,14,2,2,8,2,1,True)]
(base/'plan.json').write_text(json.dumps(dict(scope='Exact same-frame queue/direct scheduling oracle; not performance, transport correctness or full B10',cases=cases),indent=2)+'\n')
receipts=[]
for label,scene,w,h,b,d,e,history,mode,stage,gaussian in cases:
 cmd=[sys.executable,'-X','utf8','-B',str(tools/'run_capture.py'),'--exe',str(a.exe.resolve()),'--output',str(base/label),'--label',label,'--scene',scene,'--width',str(w),'--height',str(h),'--max-bounces',str(b),'--max-diffuse-bounces',str(d),'--exposure',str(e),'--mode','dipt','--pt-mode',str(mode),'--di-mode','0','--nee-mis','0','--strict-di-validation','--b8-initial-gi-validation','--b8-validation-stage',str(stage),'--pt-paired-spatial-validation','--pt-replay-compaction-validation','--pt-fixed-spatial-samples','1','--capture-pt-reservoirs','--linear-hdr','--simple','--history-frames',str(history),'--sampling-seed','47','--environment-diffuse-mip','0','--app-uncapped','--timeout','300']
 if gaussian:cmd+=['--pt-gaussian-pairing-validation']
 if stage==2:cmd+=['--pt-reconnection-mode','1','--pt-roulette-probability','0.8']
 if scene!=room:cmd+=['--pt-extended-scene-validation','--pt-replay-only-validation']
 try:
  subprocess.run(cmd,check=True)
  folder=base/label;m=json.loads((folder/'manifest.json').read_text());stats=json.loads(next(folder.glob('*.stats.json')).read_text())
  assert m['measurement_status']=='captured' and m['effective_replay_queue']['oracle']
  q=check_counters(stats,w,h);paired=pair_counters(stats,w,h,gaussian)
  if label.startswith('zero-'):assert q['replay_requests']==0 and q['cheap_shifts']==0
  receipts.append(dict(case=label,queue=q,pair=paired));(base/'gpu-checks.json').write_text(json.dumps(receipts,indent=2)+'\n')
 except BaseException as ex:
  (base/'failure.json').write_text(json.dumps(dict(case=label,type=type(ex).__name__,message=str(ex),policy='Preserve first failure and stop; no automatic retries'),indent=2)+'\n');raise
 print('QUEUE_ORACLE_PASSED '+label,flush=True)
print('ALL_QUEUE_ORACLES_COMPLETE',flush=True)
