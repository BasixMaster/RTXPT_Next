"""Validate and summarize the frozen static B0/B1 protocol; never runs a GPU workload."""
from pathlib import Path
import argparse,csv,hashlib,json,math,random,re,statistics
from presentmon_analysis import presentmon_group,compare_presentmon
from analyze_captures import percentile

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def protocol(path):
    p=json.loads(path.read_text(encoding='utf-8'))
    if p.get('protocol_revision')!=2:raise ValueError('Only the static guarded protocol revision2 is supported.')
    if p['timing']['repetitions_per_scene_version']!=5 or len(p['timing']['pair_order'])!=5:raise ValueError('Expected five paired process repetitions.')
    if any(sorted(pair)!=['B0','B1'] for pair in p['timing']['pair_order']):raise ValueError('Each pair must contain B0 and B1 once.')
    if p['render_settings']['spp']!=1 or p['render_settings']['reconstruction']!='none':raise ValueError('Unsupported rendering preset.')
    return p
def validate_run(directory,p,scene,expected_exe_sha=None):
    m=json.loads((directory/'manifest.json').read_text(encoding='utf-8'))
    if m['status']!='timed_completed' or m['image_write_count']!=0 or not m['no_image_writes'] or list(directory.glob('*.png')):raise ValueError(f'Incomplete/no-write validation failed: {directory}')
    log=(directory/'presentmon.log').read_text(encoding='utf-8',errors='replace')
    if re.search(r'(?:ETW\s+)?events?\s+(?:were\s+)?lost|lost\s+(?:ETW\s+)?events?',log,re.I):raise ValueError(f'Reported trace loss (or ambiguous loss counter): {directory}')
    if sha(directory/'presentmon.csv')!=m['presentmon_csv_sha256']:raise ValueError(f'Changed PresentMon CSV: {directory}')
    if m['presentmon_sha256']!=p['timing']['tool_sha256']:raise ValueError('PresentMon executable identity differs from protocol.')
    if expected_exe_sha and m['exe_sha256']!=expected_exe_sha:raise ValueError('Executable differs from resumed run.')
    s=m['settings'];rs=p['render_settings'];t=p['timing']
    if (s['width'],s['height'],s['exposure'],s['aa'],s['denoiser'],s['sharc'],s['restir_di'],s['restir_gi'],s['animations'])!=(rs['width'],rs['height'],scene['exposure'],0,0,0,1,1,False):raise ValueError('Manifest preset mismatch.')
    if m['scene']!=scene['file'] or m['warmup_wall_s']!=t['warmup_wall_seconds'] or m['measurement_wall_s']!=t['measurement_wall_seconds']:raise ValueError('Scene/interval mismatch.')
    with (directory/'partial-perf.csv').open(newline='',encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
    if len(rows)<=1816 or any(int(r['renderWidth'])!=rs['width'] or int(r['renderHeight'])!=rs['height'] or float(r['sceneTime'])!=0 for r in rows):raise ValueError('Static scene, dimensions or rendered-frame coverage invalid.')
    # Run the independent CSV parser too: PID/swapchain/window and finite timings.
    group=presentmon_group([directory/'presentmon.csv'],directory.name,'Rtxpt.exe',600,16)
    if str(group['runs'][0]['identity']['process_id'])!=str(m['process_id']):raise ValueError('Manifest/CSV process identity mismatch.')
    return m,dict(run=directory.name,internal_frames=len(rows),last_app_frame=rows[-1]['frame'],static_scene_time=0,render_size=[rs['width'],rs['height']])
def summary(values):
    return dict(min=min(values),median=statistics.median(values),max=max(values)) if values else None
def summarize(runs,out,p):
    results={}
    for scene in p['scenes']:
        groups={};resource={};validation=[]
        for version in ['B0','B1']:
            paths=[];mem=[];temps=[];clocks=[]
            for i in range(1,6):
                directory=runs/f"{scene['id']}-{version}-r{i}";m,v=validate_run(directory,p,scene);validation.append(v)
                for sample in m.get('resource_samples',[]):
                    if sample['phase']!='measurement' or sample['exit_code']!=0:continue
                    values=[float(x.strip()) for x in sample['device_wide_csv'].split(',')]
                    if len(values)==5 and all(math.isfinite(x) for x in values):mem.append(values[0]);temps.append(values[2]);clocks.append(values[3])
                paths.append(directory/'presentmon.csv')
            group=presentmon_group(paths,version,'Rtxpt.exe',600,16);groups[version]=group;dump(out/scene['id']/(version+'.json'),group)
            resource[version]=dict(scope='Whole-device readings include background applications; not exclusive renderer allocation.',device_memory_used_MiB=summary(mem),temperature_C=summary(temps),graphics_clock_MHz=summary(clocks))
        comparison=compare_presentmon(groups['B0'],groups['B1'])
        for metric in ['GPUBusy','CPUFrameTime','GPUTime']:
            b=[r['metrics'][metric]['statistics']['median_ms'] for r in groups['B0']['runs']]
            c=[r['metrics'][metric]['statistics']['median_ms'] for r in groups['B1']['runs']]
            rng=random.Random(20261028);values=[]
            for _ in range(10000):
                idx=[rng.randrange(5) for _ in range(5)];values.append(100*(statistics.median(c[i] for i in idx)/statistics.median(b[i] for i in idx)-1))
            values.sort();comparison['comparisons'][metric]['paired_run_bootstrap_change_ci95_percent']=[percentile(values,.025),percentile(values,.975)]
            comparison['comparisons'][metric]['inference_limit']='Exploratory5process paired-index bootstrap; temporal frames not independent replicates; clocks not fixed.'
        comparison['resources']=resource;comparison['run_validation']=validation;dump(out/scene['id']/'comparison.json',comparison);results[scene['id']]=comparison
    dump(out/'available-scenes.json',dict(completed_scenes=list(results)))
    return results
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--runs',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--protocol',type=Path,default=Path(__file__).resolve().parents[1]/'first-b1-protocol-v2.json');a=ap.parse_args()
    for scene,c in summarize(a.runs.resolve(),a.output.resolve(),protocol(a.protocol)).items():print(scene,json.dumps(c['comparisons']['GPUBusy']))
if __name__=='__main__':main()
