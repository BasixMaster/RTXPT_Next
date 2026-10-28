"""Run one bounded, manifest-backed RTXPT capture, optionally with process-filtered PresentMon."""
from pathlib import Path
import argparse,subprocess,time,json,hashlib,os,datetime,csv
from capture_identity import transport_settings
from artifact_manifest import validate as validate_artifacts

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--exe',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--label',required=True);ap.add_argument('--scene',required=True)
    ap.add_argument('--exposure',type=float,required=True);ap.add_argument('--width',type=int,default=1280);ap.add_argument('--height',type=int,default=720)
    ap.add_argument('--mode',choices=['digi','dipt','default','reference'],default='digi')
    ap.add_argument('--simple',action='store_true');ap.add_argument('--reference-spp',type=int,default=2048)
    ap.add_argument('--record-start',type=float,default=20);ap.add_argument('--frames',type=int,default=1)
    ap.add_argument('--timeout',type=float,default=300);ap.add_argument('--presentmon',type=Path)
    ap.add_argument('--max-bounces',type=int);ap.add_argument('--max-diffuse-bounces',type=int)
    ap.add_argument('--pt-mode',type=int,choices=[0,1,2,3],default=3)
    ap.add_argument('--linear-hdr',action='store_true',help='Request raw PFM plus metadata; requires a renderer with captureLinearHDR support.')
    ap.add_argument('--artifact-manifest',type=Path,help='Optional strict frozen source/executable/shader identity; compile caches before freezing.')
    a=ap.parse_args();exe=a.exe.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    if any(out.iterdir()):raise SystemExit('Output directory must be new/empty; never append distinct runs.')
    args=[str(exe),'--scene',a.scene,'--width',str(a.width),'--height',str(a.height),'--overrideRadianceCacheMode','0','--useNEE','1','--NEEType','2','--useReSTIRDI',str(int(a.mode=='digi')),'--useReSTIRGI',str(int(a.mode=='digi')),'--standaloneDenoiser','0','--overrideAutoexposureOff','--overrideExposureOffset',str(a.exposure),'--disablePostProcessFilters','--realtimeAA','0','--disableFireflyFilters','--overrideSubSamplingMode','0','--nonInteractive','--capturePath',str(out/'frame.png'),'--captureSuffix',a.label,'--perfLog',str(out/'partial-perf.csv')]
    if a.linear_hdr:args+=['--captureLinearHDR','true']
    if a.mode=='reference':args+=['--overrideToReferenceMode','--referenceSamplesPerPixel',str(a.reference_spp)]
    else:args+=['--overrideToRealtimeMode','--realtimeSamplesPerPixel','1']
    if a.mode=='dipt':
        args[args.index('--useReSTIRDI')+1]='1'
        args+=['--useReSTIRPT','1','--restirPTMode',str(a.pt_mode)]
    if a.max_bounces is not None:args+=['--maxBounces',str(a.max_bounces)]
    if a.max_diffuse_bounces is not None:args+=['--maxDiffuseBounces',str(a.max_diffuse_bounces)]
    if a.simple:args+=['--stopAnimations','--captureSimple']
    else:args+=['--captureSequence','--sequenceFPS','60','--sequenceWarmupStart','0','--sequenceRecordStart',str(a.record_start),'--sequenceFrameCount',str(a.frames)]
    manifest=dict(label=a.label,scene=a.scene,mode=a.mode,output_track='unreconstructed tonemapped sRGB PNG; not linear HDR',exe_sha256=sha(exe),started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),command=args,cwd=str(exe.parent),settings=dict(width=a.width,height=a.height,exposure=a.exposure,aa=0,denoiser=0,radiance_cache=0,restir_di=int(a.mode=='digi'),restir_gi=int(a.mode=='digi'),simple=a.simple,record_start=None if a.simple else a.record_start,frames=1 if a.simple else a.frames,reference_spp=a.reference_spp if a.mode=='reference' else None),timing_scope='External PresentMon plus separate internal partial PT stage attribution. PNG write is outside selected pre-capture window.',measurement_status='running')
    if a.linear_hdr:manifest['output_track']='unreconstructed tonemapped sRGB PNG plus stored linear RGB PFM and source-format metadata'
    manifest['settings']['linear_hdr_requested']=a.linear_hdr
    manifest['settings'].update(transport_settings(args))
    if a.artifact_manifest:manifest['artifact_identity']=validate_artifacts(a.artifact_manifest,exe)
    manifest['settings'].update(max_bounces_override=a.max_bounces,max_diffuse_bounces_override=a.max_diffuse_bounces,pt_mode=a.pt_mode if a.mode=='dipt' else None)
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
            if a.linear_hdr and (len(list(out.glob('*.pfm'))) != len(manifest['images']) or len(list(out.glob('*.pfm.json'))) != len(manifest['images'])):
                manifest['measurement_status']='failed_missing_hdr_capture'
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
