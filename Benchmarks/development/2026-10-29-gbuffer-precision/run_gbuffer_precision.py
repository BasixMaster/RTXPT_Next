"""Matched, bounded material-packing ablation. No timing claims or implicit retries."""
from pathlib import Path
import subprocess,sys,json,hashlib
r=Path(__file__).resolve().parents[1];repo=r/'outputs/RTXDI_Next';tools=repo/'Benchmarks/tools';base=r/'work/2026-10-29-gbuffer-precision-v2';base.mkdir(exist_ok=False)
scenes={'convergence':('convergence-test.scene.json',0),'kitchen':('kitchen-with-test-stuff.scene.json',2)}
plan=dict(hypothesis='Legacy material packing truncation contributes to native DI/PT+DI brightness deficit. Half-up after fp16 conversion changes material reconstruction, not PDFs/lighting scaling.',decision='Compare signed raw-linear mean luminance and HDR-FLIP to unchanged independent native reference; reject universal-fix claims if scene/variant residuals persist.',control='explicit roundedMaterials=0, legacy packing',candidate='explicit roundedMaterials=1, half-up packing at identical layout',dimensions=[1280,720],bounce_limits=[14,2],history_frames=64,seeds=[0,11,47,1019,4093],scope='Separate B4/B7 precision ablation, not promoted canonical defaults; no throughput',reference='2026-10-29-finite-guard-original-resolution native4096 seed101',failure_policy='Stop on first failed launch, preserve all evidence, no automatic retries',source_sha=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip())
(base/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
(base/'renderer-working.patch').write_bytes(subprocess.check_output(['git','-C',str(repo),'diff','--binary','HEAD','--','Rtxpt','CMakeLists.txt']))
def capture(scene,variant,seed,rounded,warm=False):
 filename,exposure=scenes[scene];mode={'B4':'di','B7':'dipt'}[variant];label=f'{scene}-{variant}-r{rounded}-s{seed}'+('-warm' if warm else '');out=base/label
 args=[sys.executable,str(tools/'run_capture.py'),'--exe',str(repo/'bin/Rtxpt.exe'),'--output',str(out),'--label',label,'--scene',filename,'--mode',mode,'--exposure',str(exposure),'--width','1280','--height','720','--max-bounces','14','--max-diffuse-bounces','2','--simple','--app-uncapped','--linear-hdr','--nee-mis','0','--environment-diffuse-mip','0','--rounded-gbuffer-materials',str(rounded),'--sampling-seed',str(seed),'--history-frames','1' if warm else '64','--di-mode','3','--strict-di-validation','--timeout','180']
 if variant=='B7':args+=['--pt-mode','3','--pt-replay-only-validation','--pt-extended-scene-validation','--pt-disable-age-rejection-validation','--pt-fixed-spatial-samples','1']
 if not warm:args+=['--artifact-manifest',str(base/'frozen-artifacts.json')]
 if seed==0 and not warm:args+=['--capture-native-radiance']
 subprocess.run(args,check=True)
for scene in scenes:
 for variant in ['B4','B7']:capture(scene,variant,0,0,True)
subprocess.run([sys.executable,str(tools/'artifact_manifest.py'),'--repo',str(repo),'--exe',str(repo/'bin/Rtxpt.exe'),'--output',str(base/'frozen-artifacts.json')],check=True)
for i,seed in enumerate(plan['seeds']):
 for scene in (list(scenes) if i%2==0 else list(reversed(scenes))):
  for variant in ['B4','B7']:
   for rounded in ([0,1] if i%2==0 else [1,0]):capture(scene,variant,seed,rounded)
print('40 matched material-packing quality captures completed; no throughput measurement',flush=True)
