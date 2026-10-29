"""Fresh preserved RTXPT1.9 PT-only override; never redefine B0 defaults."""
from pathlib import Path
import sys,subprocess,json,hashlib
import argparse
ap=argparse.ArgumentParser(description=__doc__)
for name in ('native-repo','presentmon','cap-helper','rtss-helper','rtss-install-dir','output'):ap.add_argument('--'+name,type=Path,required=True)
a=ap.parse_args();repo=Path(__file__).resolve().parents[2];tools=repo/'Benchmarks/tools'
if a.output.resolve().is_relative_to(repo):raise SystemExit('Private raw telemetry and recovery state require an output outside the repository')
for value in (a.native_repo/'bin/Rtxpt.exe',a.presentmon,a.cap_helper,a.rtss_helper):
 if not value.is_file():raise SystemExit('Required executable/helper missing: '+str(value))
sys.path.insert(0,str(tools))
from driver_cap_scope import CapScope,NativeBackend,save
from artifact_manifest import validate
from presentmon_analysis import presentmon_group
base=a.output.resolve();base.mkdir(parents=True,exist_ok=False)
build=a.native_repo.resolve();exe=build/'bin/Rtxpt.exe'
scenes={'opaque-room':(str(repo/'Testing/B2/Scenes/opaque-room-registered-env.scene.json'),0,640,360,4,4),'convergence':('convergence-test.scene.json',0,1280,720,14,2),'kitchen':('kitchen-with-test-stuff.scene.json',2,1280,720,14,2)}
save(base/'plan.json',dict(variant='B0',preset='raw-native-control',algorithm='Preserved RTXPT1.9 native PT; ReSTIR DI/GI/PT off; native NEE retained',source='303b408ab81790a5051abd7573830b7a4112eb8e',adapter_scope='Actual source identity recorded by frozen-artifacts.json; effective original-source/runtime receipts mandatory',runtime='a14e079c727ed8c4fd3173bd2aea8244c9d9f6d6',assets='a56be4ed65029d2733fd02f00f4027ffd541eda8',scenes=scenes,repetitions=3,warmup_seconds=45,measure_seconds=30,selection='Last600 Original/NotSet rows,drop final16',quality='Three process restarts; native simple-capture warmup; no independent-seed claim; display PNG only; preserved binary has no raw HDR exporter',scope='Fresh cohort, B0 PT-only override, not unchanged original defaults. Native shaders/MIS retained. Room4/4 differs from older3/3 room cohort.',caps='Application uncapped; owned exact-exe NVIDIA profile; readonly RTSS checks; restore every process',timing_scope='Per-process GPU engine busy and CPU cadence; not complete critical-path GPU latency or FPS'))
def common(scene):
 f,e,w,h,b,d=scenes[scene]
 return ['--exe',str(exe),'--scene',f,'--exposure',str(e),'--width',str(w),'--height',str(h),'--mode','default','--max-bounces',str(b),'--max-diffuse-bounces',str(d)]
for scene in scenes:
 subprocess.run([sys.executable,'-X','utf8','-B',str(tools/'run_capture.py'),*common(scene),'--output',str(base/'preflight'/scene),'--label','B0-PT-only-preflight','--simple','--app-uncapped','--timeout','300'],check=True)
frozen=base/'frozen-artifacts.json'
subprocess.run([sys.executable,'-X','utf8','-B',str(tools/'artifact_manifest.py'),'--repo',str(build),'--exe',str(exe),'--output',str(frozen)],check=True)
for scene in scenes:
 for trial in (1,2,3):
  label=f'{scene}-B0-PT-only-r{trial}'
  subprocess.run([sys.executable,'-X','utf8','-B',str(tools/'run_capture.py'),*common(scene),'--variant','B0','--variant-preset','raw-native-control','--artifact-manifest',str(frozen),'--output',str(base/'quality'/label),'--label',label,'--simple','--app-uncapped','--timeout','300'],check=True)
 print('B0_QUALITY_COMPLETE '+scene,flush=True)
for scene in scenes:
 for trial in (1,2,3):
  label=f'{scene}-B0-PT-only-r{trial}';folder=base/'timing'/label;folder.mkdir(parents=True)
  state=folder/'driver-private-state.json';scope=CapScope(NativeBackend(a.cap_helper),state,exe)
  try:
   assert validate(frozen,exe)['validated'];scope.begin();audit=folder/'driver-audit.json'
   with (folder/'cap-preflight.log').open('w') as log:subprocess.run([sys.executable,'-X','utf8','-B',str(tools/'cap_preflight.py'),'--exe',str(exe),'--helper',str(a.cap_helper),'--output',str(audit)],check=True,stdout=log)
   subprocess.run([sys.executable,'-X','utf8','-B',str(tools/'run_timed.py'),*common(scene),'--variant','B0','--variant-preset','raw-native-control','--artifact-manifest',str(frozen),'--output',str(folder/'run'),'--label',label,'--presentmon',str(a.presentmon),'--warmup-seconds','45','--measure-seconds','30','--benchmark-uncapped','--driver-cap-audit',str(audit),'--rtss-install-dir',str(a.rtss_install_dir),'--rtss-helper',str(a.rtss_helper),'--rtss-user-confirmed-disabled'],check=True)
  except BaseException as exc:
   save(base/'failure.json',dict(label=label,type=type(exc).__name__,message=str(exc),policy='Stop and preserve first failure; no automatic retries'));raise
  finally:
   if state.exists():save(folder/'restoration-receipt.json',scope.restore())
  print('B0_TIMING_ACCEPTED '+label,flush=True)
save(base/'comparison.json',{s:presentmon_group([base/'timing'/f'{s}-B0-PT-only-r{i}'/'run/presentmon.csv' for i in (1,2,3)],'B0/PT-only raw override','Rtxpt.exe',600,16) for s in scenes})
print('ALL_B0_PT_ONLY_COMPLETE',flush=True)
