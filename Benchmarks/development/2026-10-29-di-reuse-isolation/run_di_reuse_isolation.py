"""Original-scene DI reuse isolation, unchanged renderer; no implicit retries/timing claims."""
from pathlib import Path
import subprocess,sys,json,hashlib
r=Path(__file__).resolve().parents[1];repo=r/'outputs/RTXDI_Next';tools=repo/'Benchmarks/tools';base=r/'work/2026-10-29-di-reuse-isolation';base.mkdir(exist_ok=False)
scenes={'convergence':('convergence-test.scene.json',0),'kitchen':('kitchen-with-test-stuff.scene.json',2)}
plan=dict(hypothesis='A persistent DI brightness discrepancy may originate before reuse or in temporal/spatial reuse; compare initial-only, temporal-only, spatial-only, combined within native-DI and PT+DI variants.',decision='If initial-only shares the deficit, reuse is not a complete explanation. If only a reused mode differs, inspect that mode before changing the estimator. Compare signed HDR means/uncertainty and FLIP; do not promote based on brightness alone.',renderer_changes='None; exact cbe38e0 renderer executable and shaders, legacy material packing0',dimensions=[1280,720],bounces=[14,2],history=64,seeds=[0,11,47,1019,4093],di_modes={'0':'initial only','1':'temporal only','2':'spatial only','3':'temporal+spatial'},variants={'B4':'native PT+DI3.1; GI/PT reuse off','B7':'guarded ReSTIR PT+DI3.1; GI off, PT temporal+spatial fixed'},reference='Unchanged native4096spp MIP0 seed101 references from finite-guard-original-resolution; independent2048/4096seed103 checks retained',scope='Fixed1spp terminal-frame quality; not accumulated convergence, unbiasedness or throughput proof',failure_policy='Stop on first failure, preserve it, diagnose before any explicit continuation',source_sha=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip())
(base/'plan.json').write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8')
def capture(scene,variant,mode,seed,warm=False):
 filename,exposure=scenes[scene];label=f'{scene}-{variant}-di{mode}-s{seed}'+('-warm' if warm else '');out=base/label
 args=[sys.executable,str(tools/'run_capture.py'),'--exe',str(repo/'bin/Rtxpt.exe'),'--output',str(out),'--label',label,'--scene',filename,'--mode','di' if variant=='B4' else 'dipt','--exposure',str(exposure),'--width','1280','--height','720','--max-bounces','14','--max-diffuse-bounces','2','--simple','--app-uncapped','--linear-hdr','--nee-mis','0','--environment-diffuse-mip','0','--rounded-gbuffer-materials','0','--sampling-seed',str(seed),'--history-frames','1' if warm else '64','--di-mode',str(mode),'--strict-di-validation','--timeout','180']
 if variant=='B7':args+=['--pt-mode','3','--pt-replay-only-validation','--pt-extended-scene-validation','--pt-disable-age-rejection-validation','--pt-fixed-spatial-samples','1']
 if not warm:args+=['--artifact-manifest',str(base/'frozen-artifacts.json')]
 if seed==0 and not warm:args+=['--capture-native-radiance']
 subprocess.run(args,check=True)
 receipt=json.loads((out/'manifest.json').read_text());assert receipt['effective_di_reuse']['active'] and receipt['effective_di_reuse']['mode']==mode
for scene in scenes:
 for variant in ['B4','B7']:capture(scene,variant,0,0,True)
subprocess.run([sys.executable,str(tools/'artifact_manifest.py'),'--repo',str(repo),'--exe',str(repo/'bin/Rtxpt.exe'),'--output',str(base/'frozen-artifacts.json')],check=True)
identity={name:hashlib.sha256((tools/name).read_bytes()).hexdigest() for name in ['run_capture.py','di_reuse_contract.py','artifact_manifest.py']};(base/'harness-files.json').write_text(json.dumps(identity,indent=2)+'\n',encoding='utf-8')
for i,seed in enumerate(plan['seeds']):
 for scene in (list(scenes) if i%2==0 else list(reversed(scenes))):
  for variant in (['B4','B7'] if i%2==0 else ['B7','B4']):
   order=list(range(4));order=order[i%4:]+order[:i%4]
   for mode in order:capture(scene,variant,mode,seed)
print('80 matched DI reuse-isolation quality captures complete; no throughput claim',flush=True)
