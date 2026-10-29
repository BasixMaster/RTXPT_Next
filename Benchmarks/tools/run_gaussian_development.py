"""Reproduce the bounded Gaussian/adjacent development captures, sequentially.

Requires the built renderer and pinned Assets. This collects quality/diagnostic
data only; it does not run or accept total timing. Output must be new/empty.
"""
from pathlib import Path
import argparse
import subprocess
import sys


def commands(repo,exe,output):
    wrapper=repo/'Benchmarks/tools/run_capture.py'
    common=[sys.executable,'-X','utf8','-B',str(wrapper),'--exe',str(exe),'--linear-hdr',
            '--environment-diffuse-mip','0','--app-uncapped','--timeout','300','--sampling-seed','47']
    room=str(repo/'Testing/B2/Scenes/opaque-room-registered-env.scene.json')
    paired=['--mode','dipt','--pt-mode','2','--di-mode','0','--nee-mis','0','--strict-di-validation',
            '--b8-initial-gi-validation','--b8-validation-stage','1','--pt-paired-spatial-validation','--pt-fixed-spatial-samples','1']
    def case(label,scene,exposure,w,h,bounces,diffuse,extra,transport=paired):
        cmd=common+transport+['--output',str(output/label),'--label',label,'--scene',scene,
                '--exposure',str(exposure),'--width',str(w),'--height',str(h),
                '--max-bounces',str(bounces),'--max-diffuse-bounces',str(diffuse)]+extra
        if label=='gpu-h1':cmd[cmd.index('--sampling-seed')+1]='11'
        if label in ('gpu-h1','gaussian-cap1','gaussian-cap2','gaussian-limited-temporal-h8'):
            cmd[cmd.index('--timeout')+1]='180'
        return label,cmd
    gaussian=['--pt-gaussian-pairing-validation']
    diagnostic=['--capture-native-radiance','--capture-pt-reservoirs','--simple']
    yield case('gpu-h1',room,0,160,91,4,4,gaussian+diagnostic+['--history-frames','1'])
    for name,policy in [('gaussian-room64',gaussian),('adjacent-room64',[])]:
        yield case(name,room,0,640,360,4,4,policy+['--frames','64','--record-start','0.1'])
    yield case('reference-room2048',room,0,640,360,4,4,
               ['--simple','--reference-spp','2048','--reference-pixel-center'],
               ['--mode','reference','--nee-mis','0'])
    for label,scene,exposure in [('gaussian-convergence','convergence-test.scene.json',0),
                                 ('gaussian-kitchen','kitchen-with-test-stuff.scene.json',2)]:
        yield case(label,scene,exposure,1280,720,14,2,gaussian+diagnostic+
                   ['--history-frames','8','--pt-extended-scene-validation','--pt-replay-only-validation'])
    yield case('gaussian-room-h8',room,0,640,360,4,4,gaussian+diagnostic+['--history-frames','8'])
    for cap in (1,2):
        yield case(f'gaussian-cap{cap}',room,0,640,360,cap,cap,gaussian+diagnostic+['--history-frames','1'])
    limited=paired.copy()
    limited[limited.index('--pt-mode')+1]='3';limited[limited.index('--di-mode')+1]='3'
    limited[limited.index('--b8-validation-stage')+1]='2'
    yield case('gaussian-limited-temporal-h8',room,0,640,360,4,4,gaussian+diagnostic+
               ['--history-frames','8','--pt-reconnection-mode','1','--pt-roulette-probability','0.8'],limited)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[2])
    ap.add_argument('--exe',type=Path)
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();repo=a.repo.resolve();exe=(a.exe or repo/'bin/Rtxpt.exe').resolve();out=a.output.resolve()
    if not exe.is_file():raise SystemExit('Built renderer missing')
    if out.exists() and any(out.iterdir()):raise SystemExit('Output must be new/empty; preserve previous experiments')
    out.mkdir(parents=True,exist_ok=True)
    for label,cmd in commands(repo,exe,out):
        print('Capturing '+label,flush=True);subprocess.run(cmd,cwd=repo,check=True)


if __name__=='__main__':main()
