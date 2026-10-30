"""Run scoped spatial queue history oracles, without timing or canonical promotion.

Uses existing scenes and renderer. Output must be a new directory. Application
caps are disabled; driver/external cap controls are required separately for timing.
"""
from pathlib import Path
import subprocess,sys,json,argparse
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--output',type=Path,required=True)
ap.add_argument('--exe',type=Path)
ap.add_argument('--case',choices=['all','room-adjacent64','room-gaussian64','room-thin16','convergence64','kitchen64'],default='all')
a=ap.parse_args()
r=Path(__file__).resolve().parents[2];base=a.output.resolve();base.mkdir(parents=True,exist_ok=False)
exe=(a.exe or r/'bin/Rtxpt.exe').resolve()
sys.path.insert(0,str(r/'Benchmarks/tools'));from replay_queue_contract import check_sequence
common=[sys.executable,'-X','utf8','-B',str(r/'Benchmarks/tools/run_capture.py'),'--exe',str(exe),'--mode','dipt','--pt-mode','3','--di-mode','3','--nee-mis','0','--strict-di-validation','--b8-initial-gi-validation','--b8-gi-reuse-mode','3','--pt-roulette-probability','0.8','--pt-paired-spatial-validation','--pt-replay-compaction-validation','--pt-fixed-spatial-samples','1','--capture-pt-reservoirs','--capture-native-radiance','--linear-hdr','--simple','--sampling-seed','47','--environment-diffuse-mip','0','--app-uncapped','--timeout','600']
room=str(r/'Testing/B2/Scenes/opaque-room-registered-env.scene.json')
cases=[('room-adjacent64',room,177,91,4,4,0,64,2,1,False),('room-gaussian64',room,177,91,4,4,0,64,2,1,True),('room-thin16',room,176,1,1,1,0,16,2,1,False),('convergence64','convergence-test.scene.json',1280,720,14,2,0,64,3,0,True),('kitchen64','kitchen-with-test-stuff.scene.json',1280,720,14,2,2,64,3,0,True)]
receipts=[]
for label,scene,w,h,b,d,e,frames,stage,rc,gaussian in cases:
    if a.case not in ('all',label):continue
    cmd=common+['--output',str(base/label),'--label',label,'--scene',scene,'--width',str(w),'--height',str(h),'--max-bounces',str(b),'--max-diffuse-bounces',str(d),'--exposure',str(e),'--history-frames',str(frames),'--b8-validation-stage',str(stage),'--pt-reconnection-mode',str(rc)]
    if gaussian:cmd+=['--pt-gaussian-pairing-validation']
    if stage==3:cmd+=['--pt-extended-scene-validation','--pt-replay-only-validation']
    subprocess.run(cmd,check=True)
    stats=json.loads(next((base/label).glob('*.stats.json')).read_text());receipt=check_sequence(stats,frames)
    # Raw HDR finite check uses the actual PFM payload, independently of renderer counters.
    import numpy as np
    pfms=list((base/label).glob('*.pfm'));assert pfms,label
    for p in pfms:
        with p.open('rb') as f:
            magic=f.readline();dims=f.readline();scale=float(f.readline());data=np.frombuffer(f.read(),dtype='<f4' if scale<0 else '>f4')
        assert np.isfinite(data).all(),str(p)
    receipts.append(dict(label=label,**receipt,finite_pfm_files=len(pfms)))
    (base/'sequence-checks.json').write_text(json.dumps(receipts,indent=2)+'\n')
print('QUEUE_HISTORY_MATRIX_PASSED',json.dumps(receipts))
