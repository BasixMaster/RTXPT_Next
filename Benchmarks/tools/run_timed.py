"""Capture no-image-write, process-filtered PresentMon timing of an owned renderer."""
from pathlib import Path
import argparse,subprocess,time,json,datetime,hashlib,csv

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--exe',type=Path,required=True);ap.add_argument('--presentmon',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--label',required=True);ap.add_argument('--scene',required=True);ap.add_argument('--exposure',type=float,required=True)
    ap.add_argument('--width',type=int,default=1280);ap.add_argument('--height',type=int,default=720)
    ap.add_argument('--warmup-seconds',type=float,default=45);ap.add_argument('--measure-seconds',type=int,default=15)
    ap.add_argument('--mode',choices=['digi','default'],default='digi')
    a=ap.parse_args();exe=a.exe.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    if any(out.iterdir()):raise SystemExit('Run directory must be new/empty.')
    scene_path=exe.parent.parent/'Assets'/a.scene
    scene_data=json.loads(scene_path.read_text(encoding='utf-8-sig'))
    def animates(x):
        if isinstance(x,dict):return x.get('enableAnimations') is True or any(animates(v) for v in x.values())
        if isinstance(x,list):return any(animates(v) for v in x)
        return False
    if animates(scene_data):raise SystemExit('Static-capture guard requires an original scene with animation disabled.')
    args=[str(exe),'--scene',a.scene,'--width',str(a.width),'--height',str(a.height),'--overrideRadianceCacheMode','0','--useNEE','1','--NEEType','2','--useReSTIRDI',str(int(a.mode=='digi')),'--useReSTIRGI',str(int(a.mode=='digi')),'--standaloneDenoiser','0','--overrideAutoexposureOff','--overrideExposureOffset',str(a.exposure),'--disablePostProcessFilters','--overrideToRealtimeMode','--realtimeSamplesPerPixel','1','--realtimeAA','0','--disableFireflyFilters','--overrideSubSamplingMode','0','--nonInteractive','--captureSequence','--sequenceWarmupStart','0','--sequenceRecordStart','20','--sequenceFPS','60','--sequenceFrameCount','1','--capturePath',str(out/'unused.png'),'--perfLog',str(out/'partial-perf.csv')]
    manifest=dict(label=a.label,scene=a.scene,mode=a.mode,started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),command=args,cwd=str(exe.parent),exe_sha256=sha(exe),presentmon_sha256=sha(a.presentmon),settings=dict(width=a.width,height=a.height,exposure=a.exposure,aa=0,denoiser=0,sharc=0,restir_di=int(a.mode=='digi'),restir_gi=int(a.mode=='digi'),animations=False),warmup_wall_s=a.warmup_seconds,measurement_wall_s=a.measure_seconds,no_image_writes=True,selection='Last600 Original/NotSet process/swapchain rows, dropping final16, preregistered.',timing_scope='PresentMon CPU frame cadence and process GPU engine busy/wait intervals; not exclusive DI/GI feature time or display latency.',resource_scope='nvidia-smi whole-device allocation/utilization includes background applications, not exclusive renderer VRAM.',status='running')
    manifest['render_unfocused_guard']='Existing active capture keeps ShouldRenderUnfocused true. Original static sceneTime remains0, so20s capture never writes; owned process is bounded and terminated after timing.'
    manifest['scene_sha256']=sha(scene_path)
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
                    pm_args=[str(a.presentmon.resolve()),'--process_id',str(renderer.pid),'--output_file',str(out/'presentmon.csv'),'--v2_metrics','--no_console_stats','--session_name','BasixPT_'+str(renderer.pid),'--timed',str(a.measure_seconds),'--terminate_after_timed']
                    manifest['presentmon_command']=pm_args;manifest['capture_started_after_wall_s']=elapsed
                    pm=subprocess.Popen(pm_args,stdout=pm_log,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                if pm is not None and pm.poll() is not None:
                    manifest['presentmon_exit_code']=pm.returncode
                    if pm.returncode:raise RuntimeError('PresentMon failed: '+str(pm.returncode))
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
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(label=a.label,status=manifest['status'],wall_s=manifest['wall_s'],presentmon_exit=manifest.get('presentmon_exit_code'))))
    if manifest['status']!='timed_completed':raise SystemExit('Run failed timing/image-write completeness checks; no benchmark sample accepted.')
if __name__=='__main__':main()
