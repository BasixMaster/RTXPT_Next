"""Capture no-image-write, process-filtered PresentMon timing of an owned renderer."""
from pathlib import Path
from experiment_contract import prepare as prepare_experiment, verify as verify_experiment, verify_snapshot
import argparse,subprocess,time,json,datetime,hashlib,csv
from cap_preflight import validate_audit,validate_runtime
from capture_identity import transport_settings
from sampling_contract import roulette_value, seed_value, verify as verify_sampling, verify_di, verify_pt_history, verify_pt_spatial, verify_ptpp
from run_capture import scene_argument
from artifact_manifest import validate as validate_artifacts
from extended_scene_contract import validate_request as validate_extended_request, verify as verify_extended
from environment_filter_contract import verify as verify_environment_filter
from rtss_caps import RTSSBackend
from rtss_readonly import collect as collect_rtss,validate as validate_rtss

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--exe',type=Path,required=True);ap.add_argument('--presentmon',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--variant',choices=['B'+str(i) for i in range(11)])
    ap.add_argument('--variant-preset',choices=['matched-raw','raw-native-control','limited-ptpp-ablation'],default='matched-raw')
    ap.add_argument('--label',required=True);ap.add_argument('--scene',required=True);ap.add_argument('--exposure',type=float,required=True)
    ap.add_argument('--width',type=int,default=1280);ap.add_argument('--height',type=int,default=720)
    ap.add_argument('--warmup-seconds',type=float,default=45);ap.add_argument('--measure-seconds',type=int,default=15)
    ap.add_argument('--mode',choices=['digi','dipt','di','pt','default'],default='digi')
    ap.add_argument('--benchmark-uncapped',action='store_true',help='New builds only: require effective renderer log and matching active driver cap audit.')
    ap.add_argument('--driver-cap-audit',type=Path)
    ap.add_argument('--max-bounces',type=int);ap.add_argument('--max-diffuse-bounces',type=int)
    ap.add_argument('--pt-mode',type=int,choices=[0,1,2,3],default=3)
    ap.add_argument('--pt-replay-only-validation',action='store_true')
    ap.add_argument('--pt-extended-scene-validation',action='store_true',help='Guarded development only; no canonical result label')
    ap.add_argument('--nee-mis',type=int,choices=[0,1,2])
    ap.add_argument('--environment-diffuse-mip',type=int,choices=range(17),metavar='0..16')
    ap.add_argument('--sampling-seed',type=seed_value)
    ap.add_argument('--strict-di-validation',action='store_true')
    ap.add_argument('--pt-disable-age-rejection-validation',action='store_true')
    ap.add_argument('--pt-reconnection-mode',type=int,choices=[0,1])
    ap.add_argument('--pt-roulette-probability',type=roulette_value)
    ap.add_argument('--pt-fixed-spatial-samples',type=int,choices=range(1,33))
    ap.add_argument('--artifact-manifest',type=Path,help='Optional strict frozen source/executable/shader identity; warm/compile caches before freezing.')
    ap.add_argument('--rtss-install-dir',type=Path);ap.add_argument('--rtss-helper',type=Path)
    ap.add_argument('--rtss-user-confirmed-disabled',action='store_true',help='User has disabled RTSS cap; collect only read-only SDK/profile boundary audits.')
    a=ap.parse_args();validate_extended_request(a.pt_extended_scene_validation,a.mode,a.pt_replay_only_validation,a.variant);canonical=prepare_experiment(a.variant,a.mode,a.variant_preset,a.pt_reconnection_mode,a.pt_roulette_probability);verify_snapshot(a.artifact_manifest,canonical)
    exe=a.exe.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    if any(out.iterdir()):raise SystemExit('Run directory must be new/empty.')
    rtss=None
    if a.rtss_install_dir or a.rtss_helper or a.rtss_user_confirmed_disabled:
        if not (a.rtss_install_dir and a.rtss_helper and a.rtss_user_confirmed_disabled):raise SystemExit('RTSS read-only verification requires install-dir, helper and user-confirmed-disabled together.')
        rtss=RTSSBackend(a.rtss_install_dir,exe,a.rtss_helper)
    a.scene=scene_argument(a.scene,exe.parent.parent/'Assets')
    scene_path=exe.parent.parent/'Assets'/a.scene
    scene_data=json.loads(scene_path.read_text(encoding='utf-8-sig'))
    def animates(x):
        if isinstance(x,dict):return x.get('enableAnimations') is True or any(animates(v) for v in x.values())
        if isinstance(x,list):return any(animates(v) for v in x)
        return False
    if animates(scene_data):raise SystemExit('Static-capture guard requires an original scene with animation disabled.')
    args=[str(exe),'--scene',a.scene,'--width',str(a.width),'--height',str(a.height),'--overrideRadianceCacheMode','0','--useNEE','1','--NEEType','2','--useReSTIRDI',str(int(a.mode in ['digi','dipt','di'])),'--useReSTIRGI',str(int(a.mode=='digi')),'--standaloneDenoiser','0','--overrideAutoexposureOff','--overrideExposureOffset',str(a.exposure),'--disablePostProcessFilters','--overrideToRealtimeMode','--realtimeSamplesPerPixel','1','--realtimeAA','0','--disableFireflyFilters','--overrideSubSamplingMode','0','--nonInteractive','--captureSequence','--sequenceWarmupStart','0','--sequenceRecordStart','20','--sequenceFPS','60','--sequenceFrameCount','1','--capturePath',str(out/'unused.png'),'--perfLog',str(out/'partial-perf.csv')]
    if a.nee_mis is not None:args+=['--neeMIS',str(a.nee_mis)]
    if a.environment_diffuse_mip is not None:args+=['--environmentDiffuseMip',str(a.environment_diffuse_mip)]
    if a.sampling_seed is not None:args+=['--samplingSeed',str(a.sampling_seed)]
    if a.strict_di_validation:args+=['--strictDIValidation','true']
    if a.pt_replay_only_validation:args+=['--ptReplayOnlyValidation','true']
    if a.pt_extended_scene_validation:args+=['--ptExtendedSceneValidation','true']
    if a.pt_disable_age_rejection_validation:args+=['--ptDisableAgeRejectionValidation','true']
    if a.pt_reconnection_mode is not None:args+=['--ptReconnectionMode',str(a.pt_reconnection_mode)]
    if a.pt_roulette_probability is not None:args+=['--ptRouletteProbability',str(a.pt_roulette_probability)]
    if a.pt_fixed_spatial_samples is not None:args+=['--ptFixedSpatialSamples',str(a.pt_fixed_spatial_samples)]
    if a.mode in ['dipt','pt']:args+=['--useReSTIRPT','1','--restirPTMode',str(a.pt_mode)]
    if a.max_bounces is not None:args+=['--maxBounces',str(a.max_bounces)]
    if a.max_diffuse_bounces is not None:args+=['--maxDiffuseBounces',str(a.max_diffuse_bounces)]
    driver_state=None
    if a.benchmark_uncapped:
        if a.driver_cap_audit is None:raise SystemExit('Uncapped mode requires a matching active --driver-cap-audit; unknown caps are not disabled.')
        driver_state=validate_audit(json.loads(a.driver_cap_audit.read_text(encoding='utf-8')),sha(exe))
        args+=['--benchmarkUncapped=true']
    manifest=dict(label=a.label,scene=a.scene,mode=a.mode,started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),command=args,cwd=str(exe.parent),exe_sha256=sha(exe),presentmon_sha256=sha(a.presentmon),settings=dict(width=a.width,height=a.height,exposure=a.exposure,aa=0,denoiser=0,sharc=0,restir_di=int(a.mode=='digi'),restir_gi=int(a.mode=='digi'),animations=False),warmup_wall_s=a.warmup_seconds,measurement_wall_s=a.measure_seconds,no_image_writes=True,selection='Last600 Original/NotSet process/swapchain rows, dropping final16, preregistered.',timing_scope='PresentMon CPU frame cadence and process GPU engine busy/wait intervals; not exclusive DI/GI feature time or display latency.',resource_scope='nvidia-smi whole-device allocation/utilization includes background applications, not exclusive renderer VRAM.',status='running')
    manifest['canonical_experiment']=canonical
    manifest['render_unfocused_guard']='Existing active capture keeps ShouldRenderUnfocused true. Original static sceneTime remains0, so20s capture never writes; owned process is bounded and terminated after timing.'
    manifest['scene_sha256']=sha(scene_path)
    if a.artifact_manifest:manifest['artifact_identity']=validate_artifacts(a.artifact_manifest,exe)
    manifest['settings'].update(transport_settings(args))
    manifest['settings'].update(max_bounces_override=a.max_bounces,max_diffuse_bounces_override=a.max_diffuse_bounces,pt_mode=a.pt_mode if a.mode in ['dipt','pt'] else None)
    manifest['cap_control']=dict(renderer_override_requested=a.benchmark_uncapped,driver=driver_state,external_limiters='unknown; not covered by renderer/NVAPI',fully_uncapped_verified=False)
    if rtss:
        manifest['cap_control']['rtss_before_launch']=validate_rtss(collect_rtss(rtss),sha(exe))
        manifest['cap_control']['external_limiters']='Known RTSS settings read-only verified; other external limiters remain unknown.'
    if a.driver_cap_audit:manifest['cap_control']['audit_sha256']=sha(a.driver_cap_audit)
    samples=[];pm=None;start=time.monotonic();renderer=None
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    with (out/'renderer.log').open('w',encoding='utf-8') as log,(out/'presentmon.log').open('w',encoding='utf-8') as pm_log:
        try:
            renderer=subprocess.Popen(args,cwd=exe.parent,stdout=log,stderr=subprocess.STDOUT);manifest['process_id']=renderer.pid
            warm_end=start+a.warmup_seconds;next_sample=0
            while True:
                now=time.monotonic();elapsed=now-start
                if renderer.poll() is not None:raise RuntimeError('Renderer exited before timed capture completed: '+str(renderer.returncode))
                if now>=warm_end and pm is None:
                    if rtss:manifest['cap_control']['rtss_before_measurement']=validate_rtss(collect_rtss(rtss),manifest['exe_sha256'])
                    pm_args=[str(a.presentmon.resolve()),'--process_id',str(renderer.pid),'--output_file',str(out/'presentmon.csv'),'--v2_metrics','--no_console_stats','--session_name','BasixPT_'+str(renderer.pid),'--timed',str(a.measure_seconds),'--terminate_after_timed']
                    manifest['presentmon_command']=pm_args;manifest['capture_started_after_wall_s']=elapsed
                    pm=subprocess.Popen(pm_args,stdout=pm_log,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                if pm is not None and pm.poll() is not None:
                    manifest['presentmon_exit_code']=pm.returncode
                    if pm.returncode:raise RuntimeError('PresentMon failed: '+str(pm.returncode))
                    if rtss:manifest['cap_control']['rtss_after_measurement']=validate_rtss(collect_rtss(rtss),manifest['exe_sha256'])
                    break
                if elapsed>a.warmup_seconds+a.measure_seconds+20:raise TimeoutError('Owned timed run exceeded its bound.')
                if elapsed>=next_sample:
                    gpu=subprocess.run(['nvidia-smi','--query-gpu=memory.used,utilization.gpu,temperature.gpu,clocks.current.graphics,power.draw','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=8,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                    samples.append(dict(elapsed_s=elapsed,phase='warmup' if pm is None else 'measurement',device_wide_csv=gpu.stdout.strip(),exit_code=gpu.returncode));next_sample=elapsed+1
                time.sleep(.1)
            manifest['status']='profiler_stopped_pending_validation'
        finally:
            if renderer and renderer.poll() is None:
                renderer.terminate();renderer.wait(timeout=10);manifest['renderer_intentionally_terminated']=True
            if pm and pm.poll() is None:pm.terminate();pm.wait(timeout=5)
            manifest['renderer_exit_code']=renderer.returncode if renderer else None
            manifest['wall_s']=time.monotonic()-start;manifest['resource_samples']=samples
            completed=manifest['status']=='profiler_stopped_pending_validation'
            manifest['status']='failed'
            csv_path=out/'presentmon.csv'
            if csv_path.exists():
                manifest['presentmon_csv_sha256']=sha(csv_path)
                with csv_path.open(newline='',encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
                selected=[r for r in rows if r.get('ProcessID')==str(renderer.pid)]
                manifest['observed_present_rows']=len(selected)
                if completed and len(selected)>=616 and not list(out.glob('*.png')):manifest['status']='timed_completed'
            manifest['image_write_count']=len(list(out.glob('*.png')))
            (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    trace_log=(out/'presentmon.log').read_text(encoding='utf-8',errors='replace')
    manifest['reported_trace_loss']='ETW events were lost' in trace_log
    if manifest['reported_trace_loss']:manifest['status']='failed_trace_loss'
    if a.benchmark_uncapped:
        try:
            manifest['cap_control']['effective_renderer']=validate_runtime((out/'renderer.log').read_text(encoding='utf-8',errors='replace'))
            with (out/'presentmon.csv').open(newline='',encoding='utf-8-sig') as f:sync={r.get('SyncInterval') for r in csv.DictReader(f) if r.get('ProcessID')==str(renderer.pid)}
            if sync!={'0'}:raise ValueError('Observed application presentation was not consistently SyncInterval0.')
            manifest['cap_control']['observed_sync_interval']=0
        except (ValueError,OSError) as exc:
            manifest['status']='failed_cap_verification';manifest['cap_control']['failure']=str(exc)
    try:
        receipt_log=(out/'renderer.log').read_text(encoding='utf-8',errors='replace')
        if a.nee_mis is not None:
            import re
            mis=re.findall(r'^TRANSPORT_CONTRACT .* neeMIS=(\d+) ',receipt_log,re.MULTILINE)
            if len(set(mis))!=1 or int(mis[0])!=a.nee_mis:raise ValueError('Native MIS override lacks matching effective receipt')
            manifest['effective_native_nee_mis']=int(mis[0])
        manifest['effective_canonical_experiment']=verify_experiment(receipt_log,canonical)
        manifest['effective_extended_scene_contract']=verify_extended(receipt_log,a.pt_extended_scene_validation,a.max_diffuse_bounces,a.mode)
        manifest['effective_environment_filter']=verify_environment_filter(receipt_log,a.environment_diffuse_mip)
        manifest['effective_sampling']=verify_sampling(receipt_log,a.sampling_seed)
        manifest['effective_di_validation']=verify_di(receipt_log,a.strict_di_validation)
        manifest['effective_pt_history']=verify_pt_history(receipt_log,a.pt_disable_age_rejection_validation)
        manifest['effective_pt_spatial']=verify_pt_spatial(receipt_log,a.pt_fixed_spatial_samples)
        manifest['effective_ptpp']=verify_ptpp(receipt_log,a.pt_reconnection_mode,a.pt_roulette_probability,False)
    except ValueError as exc:
        manifest['status']='failed_transport_receipt';manifest['transport_receipt_failure']=str(exc)
    if a.artifact_manifest:
        try:manifest['artifact_identity_after_capture']=validate_artifacts(a.artifact_manifest,exe)
        except (ValueError,OSError) as exc:
            manifest['status']='failed_artifact_identity';manifest['artifact_failure']=str(exc)
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(label=a.label,status=manifest['status'],wall_s=manifest['wall_s'],presentmon_exit=manifest.get('presentmon_exit_code'))))
    if manifest['status']!='timed_completed':raise SystemExit('Run failed timing/image-write completeness checks; no benchmark sample accepted.')
if __name__=='__main__':main()
