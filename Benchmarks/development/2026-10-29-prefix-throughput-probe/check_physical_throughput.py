"""Physical repeat after synthetic calibration, including omitted legacy default."""
from pathlib import Path
import subprocess,sys,json,hashlib
import numpy as np
r=Path(__file__).resolve().parents[1];repo=r/'outputs/RTXDI_Next';tools=repo/'Benchmarks/tools';sys.path.insert(0,str(tools));from analyze_throughput import read
base=r/'work/2026-10-29-throughput-clamp';restored=json.loads((base/'physical-producer-restoration.json').read_text());assert restored['restored'];assert hashlib.sha256((repo/'Rtxpt/Shaders/PathTracerSurfaceBridgeDonut.hlsli').read_bytes()).hexdigest()==restored['sha256']
scenes={'convergence':('convergence-test.scene.json',0),'kitchen':('kitchen-with-test-stuff.scene.json',2)}
def capture(scene,variant,preserve,warm=False):
 filename,exposure=scenes[scene];kind='preserve1' if preserve else 'omitted-default';label=f'{scene}-{variant}-{kind}'+('-warm' if warm else '-s0');out=base/'physical'/label
 args=[sys.executable,str(tools/'run_capture.py'),'--exe',str(repo/'bin/Rtxpt.exe'),'--output',str(out),'--label',label,'--scene',filename,'--mode','di' if variant=='B4' else 'dipt','--exposure',str(exposure),'--width','1280','--height','720','--max-bounces','14','--max-diffuse-bounces','2','--simple','--app-uncapped','--linear-hdr','--nee-mis','0','--environment-diffuse-mip','0','--rounded-gbuffer-materials','0','--capture-gbuffer-throughput','--sampling-seed','0','--history-frames','1' if warm else '64','--di-mode','3','--strict-di-validation','--timeout','180']
 if preserve:args+=['--preserve-gbuffer-throughput','1']
 if variant=='B7':args+=['--pt-mode','3','--pt-replay-only-validation','--pt-extended-scene-validation','--pt-disable-age-rejection-validation','--pt-fixed-spatial-samples','1']
 if not warm:args+=['--artifact-manifest',str(base/'physical-artifacts.json')]
 subprocess.run(args,check=True);m=json.loads((out/'manifest.json').read_text());assert m['effective_prefix_throughput']['preserve_above_one']==preserve
 values=read(next(out.glob('*.throughput.bin')));mask=np.any(values>0,axis=-1);assert not np.all(values[mask]==np.array([2,.5,4],dtype=np.float32)),'Synthetic producer output persisted'
 if not preserve:assert m['packed_throughput'][0]['statistics']['pixels_above_one']==0
 return m
for scene in scenes:
 for variant in ['B4','B7']:capture(scene,variant,True,True)
subprocess.run([sys.executable,str(tools/'artifact_manifest.py'),'--repo',str(repo),'--exe',str(repo/'bin/Rtxpt.exe'),'--output',str(base/'physical-artifacts.json')],check=True)
rows=[]
for scene in scenes:
 for variant in ['B4','B7']:
  for preserve in [False,True]:
   m=capture(scene,variant,preserve);rows.append(dict(scene=scene,variant=variant,preserve=preserve,statistics=m['packed_throughput'][0]['statistics'],effective=m['effective_prefix_throughput']))
(base/'physical-summary.json').write_text(json.dumps(dict(scope='Eight final-frame prefix observations after byte-exact physical restoration, including omitted legacy default; no broad unbiasedness or quality-gain proof',rows=rows,any_preserved_values_above_one=any(x['statistics']['pixels_above_one'] for x in rows if x['preserve'])),indent=2)+'\n',encoding='utf-8')
print('Eight strict physical repeat/default captures completed',flush=True)
