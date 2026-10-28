"""Run the frozen static B0/B1 protocol serially; resume only fully validated runs."""
from pathlib import Path
import argparse,datetime,json,subprocess,sys
from summarize_protocol import protocol,sha,validate_run,dump

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ['baseline-exe','candidate-exe','presentmon','output','protocol']:ap.add_argument('--'+name,type=Path,required=True)
    a=ap.parse_args();p=protocol(a.protocol.resolve());out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    exes={'B0':a.baseline_exe.resolve(),'B1':a.candidate_exe.resolve()};identities={v:sha(e) for v,e in exes.items()}
    if sha(a.presentmon.resolve())!=p['timing']['tool_sha256']:raise ValueError('PresentMon checksum differs from frozen protocol.')
    t=p['timing'];rs=p['render_settings'];receipt=[]
    for scene in p['scenes']:
        for i,order in enumerate(t['pair_order'],1):
            for version in order:
                name=f"{scene['id']}-{version}-r{i}";directory=out/name
                if directory.exists() and any(directory.iterdir()):
                    m,_=validate_run(directory,p,scene,identities[version]);state='resumed_validated'
                else:
                    cmd=[sys.executable,'-X','utf8','-B',str(Path(__file__).with_name('run_timed.py')),'--exe',str(exes[version]),'--presentmon',str(a.presentmon.resolve()),'--output',str(directory),'--label',name,'--scene',scene['file'],'--exposure',str(scene['exposure']),'--width',str(rs['width']),'--height',str(rs['height']),'--warmup-seconds',str(t['warmup_wall_seconds']),'--measure-seconds',str(t['measurement_wall_seconds'])]
                    print('START '+name,flush=True);subprocess.run(cmd,check=True)
                    m,_=validate_run(directory,p,scene,identities[version]);state='completed_validated'
                scene_path=exes[version].parent.parent/'Assets'/scene['file']
                if sha(scene_path)!=m['scene_sha256']:raise ValueError('Scene content differs from recorded run.')
                receipt.append(dict(run=name,status=state,checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()));dump(out/'completed.json',receipt)
    print('SUITE COMPLETE',flush=True)
if __name__=='__main__':main()
