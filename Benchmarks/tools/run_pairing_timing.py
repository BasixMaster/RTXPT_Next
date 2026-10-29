"""Portable fixed cohort runner; private state and raw telemetry remain in its output directory."""
from pathlib import Path
import sys,subprocess,json
import argparse
ap=argparse.ArgumentParser(description="Collect the fixed three-scene, three-repeat adjacent/Gaussian timing cohort. Windows/NVAPI/RTSS; output is private and must be outside the repository.")
ap.add_argument('--exe',type=Path,required=True);ap.add_argument('--presentmon',type=Path,required=True)
ap.add_argument('--cap-helper',type=Path,required=True);ap.add_argument('--rtss-helper',type=Path,required=True)
ap.add_argument('--rtss-install-dir',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
a=ap.parse_args();repo=Path(__file__).resolve().parents[2];tools=repo/'Benchmarks/tools';sys.path.insert(0,str(tools))
for value in (a.exe,a.presentmon,a.cap_helper,a.rtss_helper):
 if not value.is_file():raise SystemExit('Required executable/helper missing: '+str(value))
base=a.output.resolve()
if base.is_relative_to(repo):raise SystemExit('Private recovery state/device telemetry must stay outside the public repository')
if base.exists():raise SystemExit('Preserve existing cohorts; choose a new output directory')
from driver_cap_scope import CapScope,NativeBackend,save
from artifact_manifest import validate
from presentmon_analysis import presentmon_group,compare_presentmon
base.mkdir(parents=True,exist_ok=False);exe=a.exe.resolve()
scenes={'opaque-room':(str(repo/'Testing/B2/Scenes/opaque-room-registered-env.scene.json'),0,640,360,4,4), 'convergence':('convergence-test.scene.json',0,1280,720,14,2),'kitchen':('kitchen-with-test-stuff.scene.json',2,1280,720,14,2)}
orders=[['adjacent','gaussian'],['gaussian','adjacent'],['adjacent','gaussian']]
plan=dict(scope='Development-only Gaussian versus adjacent one-neighbor pair/vector schedule; GI initial only; no full B10 claim',warmup_seconds=45,measurement_seconds=30,repeats=3,orders=orders,scenes=scenes,selection='Last600 Original/NotSet process/swapchain rows, drop final16',caps='App uncapped; transactional exact-executable NVIDIA profile; read-only RTSS checks; restore every process',quality='Existing Gaussian full-resolution/room cohort plus new adjacent original-resolution snapshots; not replicated original-scene or equal-time quality',desktop='Operator must ensure active desktop and connected display before launch',timing_scope='PresentMon per-process GPU engine busy and CPU cadence, not complete critical-path frame latency/FPS')
save(base/'plan.json',plan)
# Warm/capture the missing matched adjacent original-scene settings before freezing caches.
for scene in ('convergence','kitchen'):
 filename,exposure,w,h,b,d=scenes[scene];label='adjacent-'+scene
 cmd=[sys.executable,'-X','utf8','-B',str(tools/'run_capture.py'),'--exe',str(exe),'--output',str(base/'quality'/label),'--label',label,'--scene',filename,'--exposure',str(exposure),'--width',str(w),'--height',str(h),'--mode','dipt','--pt-mode','2','--di-mode','0','--nee-mis','0','--strict-di-validation','--b8-initial-gi-validation','--b8-validation-stage','1','--pt-paired-spatial-validation','--pt-fixed-spatial-samples','1','--linear-hdr','--simple','--history-frames','8','--sampling-seed','47','--max-bounces',str(b),'--max-diffuse-bounces',str(d),'--environment-diffuse-mip','0','--app-uncapped','--pt-extended-scene-validation','--pt-replay-only-validation','--timeout','300']
 subprocess.run(cmd,check=True)
frozen=base/'frozen-artifacts.json';subprocess.run([sys.executable,'-X','utf8','-B',str(tools/'artifact_manifest.py'),'--repo',str(repo),'--exe',str(exe),'--output',str(frozen)],check=True)
for scene,(filename,exposure,w,h,b,d) in scenes.items():
 for trial,order in enumerate(orders,1):
  for policy in order:
   label=f'{scene}-{policy}-r{trial}';folder=base/'timing'/label;folder.mkdir(parents=True);state=folder/'driver-private-state.json';scope=CapScope(NativeBackend(a.cap_helper.resolve()),state,exe)
   try:
    assert validate(frozen,exe)['validated'];scope.begin();audit=folder/'driver-audit.json'
    with (folder/'cap-preflight.log').open('w') as log:subprocess.run([sys.executable,'-X','utf8','-B',str(tools/'cap_preflight.py'),'--exe',str(exe),'--helper',str(a.cap_helper.resolve()),'--output',str(audit)],check=True,stdout=log)
    args=[sys.executable,'-X','utf8','-B',str(tools/'run_timed.py'),'--exe',str(exe),'--presentmon',str(a.presentmon.resolve()),'--output',str(folder/'run'),'--label',label,'--scene',filename,'--exposure',str(exposure),'--width',str(w),'--height',str(h),'--mode','dipt','--pt-mode','2','--di-mode','0','--nee-mis','0','--strict-di-validation','--b8-initial-gi-validation','--b8-validation-stage','1','--pt-paired-spatial-validation','--pt-fixed-spatial-samples','1','--sampling-seed','47','--max-bounces',str(b),'--max-diffuse-bounces',str(d),'--environment-diffuse-mip','0','--artifact-manifest',str(frozen),'--warmup-seconds','45','--measure-seconds','30','--benchmark-uncapped','--driver-cap-audit',str(audit),'--rtss-install-dir',str(a.rtss_install_dir.resolve()),'--rtss-helper',str(a.rtss_helper.resolve()),'--rtss-user-confirmed-disabled']
    if policy=='gaussian':args+=['--pt-gaussian-pairing-validation']
    if scene!='opaque-room':args+=['--pt-extended-scene-validation','--pt-replay-only-validation']
    subprocess.run(args,check=True)
   except BaseException as exc:
    save(base/'failure.json',dict(label=label,type=type(exc).__name__,message=str(exc),policy='Stop; preserve failed trial, no automatic retries'))
    raise
   finally:
    if state.exists():save(folder/'restoration-receipt.json',scope.restore())
   print('TIMING_ACCEPTED '+label,flush=True)
result={}
for scene in scenes:
 groups={policy:presentmon_group([base/'timing'/f'{scene}-{policy}-r{i}'/'run/presentmon.csv' for i in (1,2,3)],policy+' single-neighbor pair/vector','Rtxpt.exe',600,16) for policy in ('adjacent','gaussian')}
 result[scene]=dict(groups=groups,comparison=compare_presentmon(groups['adjacent'],groups['gaussian']))
save(base/'comparison.json',result);print('ALL_18_TIMINGS_COMPLETE',flush=True)
