"""Run one bounded, manifest-backed RTXPT capture, optionally with process-filtered PresentMon."""
from pathlib import Path
from experiment_contract import VARIANT_IDS, prepare as prepare_experiment, verify as verify_experiment, verify_snapshot
import argparse,subprocess,time,json,hashlib,os,datetime,csv
from capture_identity import transport_settings
from sampling_contract import roulette_value, seed_value, verify as verify_sampling, verify_di, verify_pt_replay, verify_pt_history, verify_pt_spatial, verify_ptpp, verify_capture_history
from artifact_manifest import validate as validate_artifacts
from extended_scene_contract import validate_request as validate_extended_request, verify as verify_extended
from environment_filter_contract import verify as verify_environment_filter
from di_reuse_contract import verify as verify_di_reuse
from throughput_contract import verify as verify_throughput, validate_request as validate_throughput
from b8_partition_contract import validate_replay_roulette, verify as verify_b8, check_stages as check_b8_stages
from paired_pilot_contract import verify as verify_paired
from replay_queue_contract import verify as verify_queue, check_counters as check_queue_counters
from gbuffer_precision_contract import verify as verify_gbuffer_precision, validate_request as validate_gbuffer_request

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def scene_argument(value, assets_dir=None):
    path = Path(value)
    if path.is_file(): return str(path.resolve())
    if path.is_absolute() or '/' in value or '\\' in value:
        raise ValueError('Scene path does not exist; refusing renderer fallback to a different scene')
    if assets_dir is not None and not (Path(assets_dir)/value).is_file():
        raise ValueError('Named scene is absent from the pinned Assets directory; refusing fallback')
    return value  # Renderer-owned asset name, resolved by its asset search path.

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--exe',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--variant',choices=VARIANT_IDS)
    ap.add_argument('--b8-initial-gi-validation',action='store_true',help='Development only: initial DI/GI-short/PT-long partition; not a canonical B8 result')
    ap.add_argument('--b8-component',type=int,choices=range(5),default=0,help='Development output:0sum,1native,2DI,3GI-short,4PT-long')
    ap.add_argument('--b8-gi-reuse-mode',type=int,choices=range(4),help='Opt into NVIDIA GI approximation:0 initial,1 temporal,2 spatial,3 both; omission preserves legacy initial-only control')
    ap.add_argument('--b8-validation-stage',type=int,choices=range(4),default=0,help='GI-short development:0 initial,1 DI/PT reuse,2 limited PT++ ablation; not canonical B9')
    ap.add_argument('--pt-paired-spatial-validation',action='store_true',help='Development only: adjacent reciprocal-pair shifts and vector shading; not full B10')
    ap.add_argument('--pt-replay-compaction-validation',action='store_true',help='Opt-in replay queue; reservoir capture enables the same-frame exact direct oracle')
    ap.add_argument('--pt-duplication-history-validation',action='store_true',help='Opt-in deliberately biased temporal history reduction using the prior duplication map')
    ap.add_argument('--pt-gaussian-pairing-validation',action='store_true',help='Paired development: three resident Gaussian tables, one transformed table per frame')
    ap.add_argument('--variant-preset',choices=['matched-raw','raw-native-control','limited-ptpp-ablation'],default='matched-raw')
    ap.add_argument('--label',required=True);ap.add_argument('--scene',required=True)
    ap.add_argument('--exposure',type=float,required=True);ap.add_argument('--width',type=int,default=1280);ap.add_argument('--height',type=int,default=720)
    ap.add_argument('--mode',choices=['digi','dipt','di','pt','default','reference'],default='digi')
    ap.add_argument('--stop-animations',action='store_true',help='Freeze scene animations for static sequence comparisons')
    ap.add_argument('--simple',action='store_true');ap.add_argument('--reference-spp',type=int,default=2048)
    ap.add_argument('--record-start',type=float,default=20);ap.add_argument('--frames',type=int,default=1)
    ap.add_argument('--timeout',type=float,default=300);ap.add_argument('--presentmon',type=Path)
    ap.add_argument('--max-bounces',type=int);ap.add_argument('--max-diffuse-bounces',type=int)
    ap.add_argument('--pt-mode',type=int,choices=[0,1,2,3],default=3)
    ap.add_argument('--pt-extended-scene-validation',action='store_true',help='Development replay-first original-scene transport; no canonical acceptance claim')
    ap.add_argument('--app-uncapped',action='store_true',help='Quality captures: disable app caps only; external cap audit belongs to timed runs.')
    ap.add_argument('--capture-native-radiance',action='store_true')
    ap.add_argument('--history-frames',type=int,choices=range(1,4097),metavar='1..4096',help='Explicit simple-capture history warmup, not accumulated spp')
    ap.add_argument('--di-light-mode',type=int,choices=[0,1,2])
    ap.add_argument('--di-brdf-samples',type=int,choices=range(33))
    ap.add_argument('--pt-reconnection-mode',type=int,choices=[0,1])
    ap.add_argument('--pt-roulette-probability',type=roulette_value)
    ap.add_argument('--pt-fixed-spatial-samples',type=int,choices=range(1,33))
    ap.add_argument('--capture-pt-reservoirs',action='store_true')
    ap.add_argument('--pt-disable-age-rejection-validation',action='store_true')
    ap.add_argument('--pt-replay-only-validation',action='store_true')
    ap.add_argument('--strict-di-validation',action='store_true')
    ap.add_argument('--di-mode',type=int,choices=[0,1,2,3])
    ap.add_argument('--nee-mis',type=int,choices=[0,1,2])
    ap.add_argument('--preserve-gbuffer-throughput',type=int,choices=[0,1])
    ap.add_argument('--capture-gbuffer-throughput',action='store_true')
    ap.add_argument('--rounded-gbuffer-materials',type=int,choices=[0,1],help='Explicit diagnostic material packing; omitted preserves legacy truncation')
    ap.add_argument('--environment-diffuse-mip',type=int,choices=range(17),metavar='0..16')
    ap.add_argument('--nee-type',type=int,choices=[0,1,2],default=2)
    ap.add_argument('--sampling-seed',type=seed_value)
    ap.add_argument('--reference-pixel-center',action='store_true')
    ap.add_argument('--linear-hdr',action='store_true',help='Request raw PFM plus metadata; requires a renderer with captureLinearHDR support.')
    ap.add_argument('--artifact-manifest',type=Path,help='Optional strict frozen source/executable/shader identity; compile caches before freezing.')
    a=ap.parse_args();validate_throughput(a.preserve_gbuffer_throughput,a.capture_gbuffer_throughput,a.linear_hdr,a.mode,a.variant);validate_gbuffer_request(a.rounded_gbuffer_materials,a.variant);validate_extended_request(a.pt_extended_scene_validation,a.mode,a.pt_replay_only_validation,a.variant);canonical=prepare_experiment(a.variant,a.mode,a.variant_preset,a.pt_reconnection_mode,a.pt_roulette_probability);verify_snapshot(a.artifact_manifest,canonical)
    exe=a.exe.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    if any(out.iterdir()):raise SystemExit('Output directory must be new/empty; never append distinct runs.')
    a.scene=scene_argument(a.scene,exe.parent.parent/'Assets')
    if a.history_frames is not None and not a.simple:raise SystemExit('--history-frames requires --simple')
    args=[str(exe),'--scene',a.scene,'--width',str(a.width),'--height',str(a.height),'--overrideRadianceCacheMode','0','--useNEE','1','--NEEType',str(a.nee_type),'--useReSTIRDI',str(int(a.mode in ['digi','dipt','di'])),'--useReSTIRGI',str(int(a.mode=='digi')),'--standaloneDenoiser','0','--overrideAutoexposureOff','--overrideExposureOffset',str(a.exposure),'--disablePostProcessFilters','--realtimeAA','0','--disableFireflyFilters','--overrideSubSamplingMode','0','--nonInteractive','--capturePath',str(out/'frame.png'),'--captureSuffix',a.label,'--perfLog',str(out/'partial-perf.csv')]
    if (a.b8_component or a.b8_validation_stage) and not a.b8_initial_gi_validation:
        raise SystemExit('B8 component selection requires the explicit development partition')
    if a.b8_gi_reuse_mode is not None and not a.b8_initial_gi_validation:
        raise SystemExit('GI approximation requires explicit B8 development partition')
    validate_replay_roulette(a.b8_validation_stage,a.b8_initial_gi_validation,a.pt_extended_scene_validation,a.pt_replay_only_validation,a.b8_gi_reuse_mode,a.pt_reconnection_mode,a.pt_roulette_probability)
    if a.b8_initial_gi_validation:
        if a.variant is not None or a.mode!='dipt' or a.di_mode is None or a.nee_mis!=0 or not a.strict_di_validation:
            raise SystemExit('B8 development requires no canonical label, mode dipt, explicit DI mode, exact NEE MIS and strict DI')
        if a.b8_validation_stage==0 and (a.pt_mode!=0 or a.di_mode!=0):raise SystemExit('B8 stage0 requires DI/PT reuse off')
        if a.b8_validation_stage<2 and (a.pt_roulette_probability or 0)!=0:raise SystemExit('B8 stage0/1 requires roulette off')
        if a.b8_validation_stage==2 and (a.pt_reconnection_mode!=1 or not 0<(a.pt_roulette_probability or 0)<1):raise SystemExit('Limited PT++ ablation requires explicit footprint and roulette in(0,1)')
        args[args.index('--useReSTIRGI')+1]='1'
        args+=['--b8InitialGIValidation','true','--b8Component',str(a.b8_component),'--b8ValidationStage',str(a.b8_validation_stage)]
    if a.b8_gi_reuse_mode is not None: args+=['--b8GIReuseMode',str(a.b8_gi_reuse_mode)]
    if a.pt_paired_spatial_validation:
        if not a.b8_initial_gi_validation or a.b8_validation_stage==0 or a.pt_mode not in (2,3) or a.pt_fixed_spatial_samples!=1:
            raise SystemExit('Paired pilot requires B8 stage1/2, spatial PT and one fixed neighbor')
        args+=['--ptPairedSpatialValidation','true']
    if a.pt_gaussian_pairing_validation:
        if not a.pt_paired_spatial_validation:raise SystemExit('Gaussian policy requires the paired spatial development path')
        args+=['--ptGaussianPairingValidation','true']
    if a.pt_replay_compaction_validation:
        if not a.pt_paired_spatial_validation:raise SystemExit('Replay compaction requires paired B8 development')
        args+=['--ptReplayCompactionValidation','true']
    if a.pt_duplication_history_validation:
        if not a.b8_initial_gi_validation or a.pt_mode not in (1,3):
            raise SystemExit('Duplication history validation requires explicit B8 and temporal PT')
        args+=['--ptDuplicationHistoryValidation','true']
    if a.capture_native_radiance:
        if not a.linear_hdr:raise SystemExit('Native radiance diagnostics require --linear-hdr')
        args+=['--captureNativeRadiance','true']
    if a.pt_reconnection_mode is not None:args+=['--ptReconnectionMode',str(a.pt_reconnection_mode)]
    if a.history_frames is not None:args+=['--captureWarmupFrames',str(a.history_frames)]
    if a.pt_roulette_probability is not None:args+=['--ptRouletteProbability',str(a.pt_roulette_probability)]
    if a.pt_fixed_spatial_samples is not None:args+=['--ptFixedSpatialSamples',str(a.pt_fixed_spatial_samples)]
    if a.capture_pt_reservoirs:args+=['--capturePTReservoirs','true']
    if a.pt_disable_age_rejection_validation:args+=['--ptDisableAgeRejectionValidation','true']
    if a.pt_replay_only_validation:args+=['--ptReplayOnlyValidation','true']
    if a.pt_extended_scene_validation:
        if a.variant is not None or a.mode not in ['pt','dipt'] or not a.pt_replay_only_validation:
            raise SystemExit('Extended-scene development requires PT mode, explicit full-prefix replay and no canonical result label')
        args+=['--ptExtendedSceneValidation','true']
    if a.strict_di_validation:args+=['--strictDIValidation','true']
    if a.di_light_mode is not None:args+=['--diLightMode',str(a.di_light_mode)]
    if a.di_brdf_samples is not None:args+=['--diBrdfSamples',str(a.di_brdf_samples)]
    if a.di_mode is not None:args+=['--restirDIMode',str(a.di_mode)]
    if a.nee_mis is not None:args+=['--neeMIS',str(a.nee_mis)]
    if a.environment_diffuse_mip is not None:args+=['--environmentDiffuseMip',str(a.environment_diffuse_mip)]
    if a.preserve_gbuffer_throughput is not None:args+=['--preserveGBufferThroughput',str(a.preserve_gbuffer_throughput)]
    if a.capture_gbuffer_throughput:args+=['--captureGBufferThroughput','true']
    if a.rounded_gbuffer_materials is not None:args+=['--roundedGBufferMaterials',str(a.rounded_gbuffer_materials)]
    if a.app_uncapped:args+=['--benchmarkUncapped','true']
    if a.sampling_seed is not None:args+=['--samplingSeed',str(a.sampling_seed)]
    if a.reference_pixel_center:args+=['--referencePixelCenter','true']
    if a.linear_hdr:args+=['--captureLinearHDR','true']
    if a.mode=='reference':args+=['--overrideToReferenceMode','--referenceSamplesPerPixel',str(a.reference_spp)]
    else:args+=['--overrideToRealtimeMode','--realtimeSamplesPerPixel','1']
    if a.mode in ['dipt','pt']:
        args[args.index('--useReSTIRDI')+1]=str(int(a.mode=='dipt'))
        args+=['--useReSTIRPT','1','--restirPTMode',str(a.pt_mode)]
    if a.max_bounces is not None:args+=['--maxBounces',str(a.max_bounces)]
    if a.max_diffuse_bounces is not None:args+=['--maxDiffuseBounces',str(a.max_diffuse_bounces)]
    if a.stop_animations and not a.simple:args+=['--stopAnimations']
    if a.simple:args+=['--stopAnimations','--captureSimple']
    else:args+=['--captureSequence','--sequenceFPS','60','--sequenceWarmupStart','0','--sequenceRecordStart',str(a.record_start),'--sequenceFrameCount',str(a.frames)]
    manifest=dict(label=a.label,scene=a.scene,mode=a.mode,output_track='unreconstructed tonemapped sRGB PNG; not linear HDR',exe_sha256=sha(exe),started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),command=args,cwd=str(exe.parent),settings=dict(width=a.width,height=a.height,exposure=a.exposure,aa=0,denoiser=0,radiance_cache=0,restir_di=int(a.mode=='digi'),restir_gi=int(a.mode=='digi'),simple=a.simple,record_start=None if a.simple else a.record_start,frames=1 if a.simple else a.frames,reference_spp=a.reference_spp if a.mode=='reference' else None),timing_scope='External PresentMon plus separate internal partial PT stage attribution. PNG write is outside selected pre-capture window.',measurement_status='running')
    manifest['scene_sha256']=sha(exe.parent.parent/'Assets'/a.scene)
    manifest['canonical_experiment']=canonical
    manifest['paired_spatial_pilot_requested']=a.pt_paired_spatial_validation
    manifest['gaussian_pairing_requested']=a.pt_gaussian_pairing_validation
    if a.b8_initial_gi_validation:
        manifest['development_partition']=dict(contract_version=1,canonical_accepted=False,gi_reuse=bool(a.b8_gi_reuse_mode),gi_approximation_mode=a.b8_gi_reuse_mode,component=a.b8_component,stage=a.b8_validation_stage,pt_min_light_inclusive_length=4)
    if a.pt_extended_scene_validation:manifest['development_extended_scene_transport']=dict(full_prefix_replay=True,canonical_accepted=False,diffuse_budget='Native sampled-lobe accounting with terminal-emission truncation')
    if a.linear_hdr:manifest['output_track']='unreconstructed tonemapped sRGB PNG plus stored linear RGB PFM and source-format metadata'
    manifest['settings']['linear_hdr_requested']=a.linear_hdr
    manifest['settings'].update(sampling_seed_requested=a.sampling_seed,reference_pixel_center_requested=a.reference_pixel_center,di_mode_requested=a.di_mode,nee_mis_requested=a.nee_mis,nee_type=a.nee_type)
    manifest['settings'].update(transport_settings(args))
    if a.artifact_manifest:manifest['artifact_identity']=validate_artifacts(a.artifact_manifest,exe)
    manifest['settings'].update(max_bounces_override=a.max_bounces,max_diffuse_bounces_override=a.max_diffuse_bounces,pt_mode=a.pt_mode if a.mode in ['dipt','pt'] else None)
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    started=time.monotonic();samples=[];pm=None;next_sample=0
    with (out/'renderer.log').open('w',encoding='utf-8') as log,(out/'presentmon.log').open('w',encoding='utf-8') as pm_log:
        renderer=subprocess.Popen(args,cwd=exe.parent,stdout=log,stderr=subprocess.STDOUT)
        manifest['process_id']=renderer.pid
        if a.presentmon:
            pm_args=[str(a.presentmon.resolve()),'--process_id',str(renderer.pid),'--output_file',str(out/'presentmon.csv'),'--v2_metrics','--no_console_stats','--session_name','BasixPT_'+str(renderer.pid),'--terminate_on_proc_exit','--timed',str(int(a.timeout)),'--terminate_after_timed']
            manifest['presentmon_command']=pm_args;manifest['presentmon_sha256']=sha(a.presentmon)
            pm=subprocess.Popen(pm_args,stdout=pm_log,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        try:
            while renderer.poll() is None:
                elapsed=time.monotonic()-started
                if elapsed>a.timeout:raise TimeoutError('Renderer exceeded bounded run timeout')
                if elapsed>=next_sample:
                    gpu=subprocess.run(['nvidia-smi','--query-gpu=memory.used,utilization.gpu,temperature.gpu,clocks.current.graphics,power.draw','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=8,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                    samples.append(dict(elapsed_s=elapsed,device_wide_csv=gpu.stdout.strip(),exit_code=gpu.returncode));next_sample=elapsed+1
                time.sleep(.1)
        except BaseException:
            renderer.kill();renderer.wait();manifest['measurement_status']='failed_or_timeout';raise
        finally:
            if pm:
                try:pm.wait(timeout=8)
                except subprocess.TimeoutExpired:pm.terminate();pm.wait(timeout=5);manifest['presentmon_forced_stop']=True
            manifest['renderer_exit_code']=renderer.returncode;manifest['elapsed_wall_s']=time.monotonic()-started
            manifest['images']=[dict(name=p.name,sha256=sha(p),bytes=p.stat().st_size) for p in out.glob('*.png')]
            manifest['measurement_status']='captured' if renderer.returncode==0 and manifest['images'] else 'failed'
            manifest['linear_hdr_files']=[dict(name=p.name,sha256=sha(p),bytes=p.stat().st_size) for p in sorted(out.glob('*.pfm*'))]
            diagnostic_suffixes=('.native.pfm','.native-di.pfm','.native-di-gi.pfm','.native-di-gi-pt.pfm')
            main_pfms=[p for p in out.glob('*.pfm') if not p.name.endswith(diagnostic_suffixes)]
            if a.linear_hdr and (len(main_pfms) != len(manifest['images']) or any(not Path(str(p)+'.json').is_file() for p in main_pfms)):
                manifest['measurement_status']='failed_missing_hdr_capture'
            try:
                manifest['effective_b8_partition']=verify_b8((out/'renderer.log').read_text(encoding='utf-8',errors='replace'),a.b8_initial_gi_validation,a.b8_component,a.b8_validation_stage,a.b8_gi_reuse_mode)
                manifest['effective_paired_spatial_pilot']=verify_paired((out/'renderer.log').read_text(encoding='utf-8',errors='replace'),a.pt_paired_spatial_validation,a.pt_gaussian_pairing_validation)
                manifest['effective_replay_queue']=verify_queue((out/'renderer.log').read_text(encoding='utf-8',errors='replace'),a.pt_replay_compaction_validation,a.capture_pt_reservoirs)
                if a.b8_gi_reuse_mode is not None and a.capture_pt_reservoirs:
                    from inspect_gi_reservoirs import inspect_file
                    gi_files = list(out.glob('*.gi.bin'))
                    if len(gi_files) != len(manifest['images']):raise ValueError('Missing GI reservoir snapshot')
                    manifest['gi_reservoir_snapshots'] = [dict(name=p.name,statistics=inspect_file(p)) for p in gi_files]
                if a.pt_replay_compaction_validation and a.capture_pt_reservoirs:
                    queue_stats=list(out.glob('*.stats.json'))
                    if len(queue_stats)!=len(manifest['images']):raise ValueError('Queue oracle statistics missing for a captured image')
                    manifest['queue_same_frame_oracles']=[check_queue_counters(json.loads(p.read_text()),a.width,a.height) for p in queue_stats]
                if a.pt_duplication_history_validation:
                    from duplication_contract import verify as verify_duplication, check_gpu as check_duplication
                    import numpy as np
                    manifest['effective_duplication_history']=verify_duplication((out/'renderer.log').read_text(encoding='utf-8',errors='replace'),True)
                    if a.capture_pt_reservoirs:
                        maps=list(out.glob('*.pt.bin.duplication.bin'))
                        if len(maps)!=len(manifest['images']):raise ValueError('Missing duplication map snapshot')
                        manifest['duplication_map_checks']=[]
                        for map_path in maps:
                            reservoir_path=Path(str(map_path).removesuffix('.duplication.bin'))
                            meta=json.loads(Path(str(reservoir_path)+'.json').read_text())
                            stats=json.loads(Path(str(reservoir_path)+'.stats.json').read_text())
                            manifest['duplication_map_checks'].append(check_duplication(
                                np.frombuffer(reservoir_path.read_bytes(),'<u4').reshape(-1,16),meta,
                                np.frombuffer(map_path.read_bytes(),'<u4').reshape(meta['height'],meta['width']),stats))
                if a.b8_initial_gi_validation and a.capture_native_radiance and a.b8_component==0:
                    from analyze_hdr import read_pfm
                    manifest['b8_same_frame_checks']=[check_b8_stages(
                        *(read_pfm(str(p)+suffix) for suffix in ('.native.pfm','.native-di.pfm','.native-di-gi.pfm','.native-di-gi-pt.pfm')),
                        read_pfm(p),a.max_bounces) for p in main_pfms]
            except (ValueError,OSError,TypeError) as exc:
                manifest['measurement_status']='failed_b8_partition_contract';manifest['b8_partition_failure']=str(exc)
            if a.capture_native_radiance and len(list(out.glob('*.native.pfm'))) != len(manifest['images']):manifest['measurement_status']='failed_missing_native_component'
            try:manifest['effective_environment_filter']=verify_environment_filter((out/'renderer.log').read_text(encoding='utf-8',errors='replace'),a.environment_diffuse_mip)
            except ValueError as exc:manifest['measurement_status']='failed_environment_filter_contract';manifest['environment_filter_failure']=str(exc)
            try:manifest['effective_sampling']=verify_sampling((out/'renderer.log').read_text(encoding='utf-8',errors='replace'),a.sampling_seed,a.reference_pixel_center)
            except ValueError as exc:manifest['measurement_status']='failed_sampling_contract';manifest['sampling_failure']=str(exc)
            try:manifest['effective_di_validation']=verify_di((out/'renderer.log').read_text(encoding='utf-8',errors='replace'),a.strict_di_validation)
            except ValueError as exc:manifest['measurement_status']='failed_di_validation_contract';manifest['di_validation_failure']=str(exc)
            try:manifest['effective_extended_scene_contract']=verify_extended((out/'renderer.log').read_text(encoding='utf-8',errors='replace'),a.pt_extended_scene_validation,a.max_diffuse_bounces,a.mode,a.b8_initial_gi_validation,a.b8_validation_stage,a.b8_gi_reuse_mode)
            except ValueError as exc:manifest['measurement_status']='failed_extended_scene_contract';manifest['extended_scene_failure']=str(exc)
            try:manifest['effective_pt_replay']=verify_pt_replay((out/'renderer.log').read_text(encoding='utf-8',errors='replace'),a.pt_replay_only_validation)
            except ValueError as exc:manifest['measurement_status']='failed_pt_replay_contract';manifest['pt_replay_failure']=str(exc)
            try:manifest['effective_pt_history']=verify_pt_history((out/'renderer.log').read_text(encoding='utf-8',errors='replace'),a.pt_disable_age_rejection_validation)
            except ValueError as exc:manifest['measurement_status']='failed_pt_history_contract';manifest['pt_history_failure']=str(exc)
            try:manifest['effective_pt_spatial']=verify_pt_spatial((out/'renderer.log').read_text(encoding='utf-8',errors='replace'),a.pt_fixed_spatial_samples)
            except ValueError as exc:manifest['measurement_status']='failed_pt_spatial_contract';manifest['pt_spatial_failure']=str(exc)
            try:manifest['effective_ptpp']=verify_ptpp((out/'renderer.log').read_text(encoding='utf-8',errors='replace'),a.pt_reconnection_mode,a.pt_roulette_probability,a.capture_pt_reservoirs)
            except ValueError as exc:manifest['measurement_status']='failed_ptpp_contract';manifest['ptpp_failure']=str(exc)
            try:manifest['effective_capture_history']=verify_capture_history((out/'renderer.log').read_text(encoding='utf-8',errors='replace'),a.history_frames)
            except ValueError as exc:manifest['measurement_status']='failed_capture_history';manifest['capture_history_failure']=str(exc)
            try:manifest['effective_canonical_experiment']=verify_experiment((out/'renderer.log').read_text(encoding='utf-8',errors='replace'),canonical)
            except ValueError as exc:manifest['measurement_status']='failed_canonical_experiment';manifest['canonical_failure']=str(exc)
            try:manifest['effective_gbuffer_precision']=verify_gbuffer_precision((out/'renderer.log').read_text(encoding='utf-8',errors='replace'),a.rounded_gbuffer_materials)
            except ValueError as exc:manifest['measurement_status']='failed_gbuffer_precision_contract';manifest['gbuffer_precision_failure']=str(exc)
            try:manifest['effective_di_reuse']=verify_di_reuse((out/'renderer.log').read_text(encoding='utf-8',errors='replace'),a.di_mode,a.mode in ['di','dipt','digi'])
            except ValueError as exc:manifest['measurement_status']='failed_di_reuse_contract';manifest['di_reuse_failure']=str(exc)
            try:
                manifest['effective_prefix_throughput']=verify_throughput((out/'renderer.log').read_text(encoding='utf-8',errors='replace'),a.preserve_gbuffer_throughput,a.capture_gbuffer_throughput)
                if a.capture_gbuffer_throughput:
                    from analyze_throughput import read as read_throughput, summarize as summarize_throughput
                    files=list(out.glob('*.throughput.bin'))
                    if len(files)!=len(manifest['images']):raise ValueError('Missing packed throughput capture')
                    manifest['packed_throughput']=[dict(name=p.name,sha256=sha(p),statistics=summarize_throughput(read_throughput(p))) for p in files]
                    if any(x['statistics']['nonfinite_components'] for x in manifest['packed_throughput']):raise ValueError('Nonfinite packed prefix weights')
            except (ValueError,OSError) as exc:manifest['measurement_status']='failed_prefix_throughput_contract';manifest['prefix_throughput_failure']=str(exc)
            manifest['resource_scope']='nvidia-smi values cover the whole device including other applications; not renderer-exclusive allocation.'
            manifest['resource_samples']=samples
            if a.artifact_manifest:
                try:manifest['artifact_identity_after_capture']=validate_artifacts(a.artifact_manifest,exe)
                except (ValueError,OSError) as exc:
                    manifest['measurement_status']='failed_artifact_identity';manifest['artifact_failure']=str(exc)
            (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(label=a.label,status=manifest['measurement_status'],exit=renderer.returncode,images=len(manifest['images']),wall_s=manifest['elapsed_wall_s'])))
    if manifest['measurement_status']!='captured':raise SystemExit(1)
if __name__=='__main__':main()
