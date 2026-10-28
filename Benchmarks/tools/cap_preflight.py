"""Read-only NVIDIA driver cap audit; missing coverage is never interpreted as uncapped."""
from pathlib import Path
import argparse,datetime,hashlib,json,subprocess
import re

FORCE_OFF=0x08416747
PASSIVE=0x60925292
RUNTIME_UNCAPPED='BENCHMARK_UNCAPPED vsync=0 fpsLimiter=0 reflexCap=0 reflexMode=0 frameGeneration=0 renderUnfocused=1'
def validate_audit(document,exe_sha256):
    if document.get('helper_exit')!=0 or document.get('executable_sha256')!=exe_sha256:
        raise ValueError('Driver audit failed or identifies a different executable.')
    try:
        age=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(document['collected_utc'])).total_seconds()
    except (KeyError,ValueError,TypeError):raise ValueError('Driver audit freshness is unavailable.')
    if not 0<=age<=60:raise ValueError('Driver audit is stale or future-dated; collect it within60seconds of launch.')
    state=interpret_driver(document.get('native',{}))
    if not state['driver_allows_uncapped_application'] or state['settings']['vsync']['state']!='forced_off':
        raise ValueError('Explicit foreground/background cap0 and forced-off driver VSync were not verified.')
    return state
def validate_runtime(log):
    adapter = re.search(r'^BENCHMARK_CONTROL_ADAPTER vsync=0 fpsLimiter=0 reflexCap=0 reflexMode=0 frameGeneration=0 renderUnfocused=1 maxBounces=(-?\d+) maxDiffuseBounces=(-?\d+)\s*$', log, re.MULTILINE)
    if RUNTIME_UNCAPPED not in log and adapter is None:
        raise ValueError('Effective renderer uncapped settings were not logged/verified.')
    return dict(vsync=0,fps_limiter=0,reflex_cap=0,reflex_mode=0,frame_generation=0,render_unfocused=True)
def interpret_driver(raw):
    settings=raw.get('settings',{})
    result={};known=True;blocked=False
    for name in ['foreground_fps','background_fps','vsync']:
        item=settings.get(name,{})
        value=item.get('value');ok=item.get('status')==0 and isinstance(value,int)
        known &= ok
        if not ok:state='unknown'
        elif name=='vsync':
            state='forced_off' if value==FORCE_OFF else ('application_controlled' if value==PASSIVE else 'potential_sync_limit')
            blocked |= value not in [FORCE_OFF,PASSIVE]
        else:
            state='disabled' if value==0 else 'enabled'
            blocked |= value!=0
        result[name]=dict(state=state,value=value,location=item.get('location'))
    return dict(settings=result,driver_cap_coverage='known' if known else 'unknown',driver_limit_detected=blocked,
                driver_allows_uncapped_application=bool(known and not blocked),
                external_limiters='unknown; must be checked separately',fully_uncapped_verified=False)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--exe',type=Path,required=True);ap.add_argument('--helper',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();helper=a.helper.resolve();exe=a.exe.resolve()
    p=subprocess.run([str(helper),str(exe)],capture_output=True,text=True,timeout=20)
    try:raw=json.loads(p.stdout)
    except json.JSONDecodeError:raw=dict(coverage='unknown',error='Native helper did not return valid JSON')
    result=dict(schema_version=1,collected_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                executable=exe.name,executable_sha256=hashlib.sha256(exe.read_bytes()).hexdigest(),
                helper_sha256=hashlib.sha256(helper.read_bytes()).hexdigest(),helper_exit=p.returncode,
                native=raw,interpretation=interpret_driver(raw),mutation_performed=False)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(result['interpretation']))
    if p.returncode or result['interpretation']['driver_cap_coverage']!='known':raise SystemExit(2)
    if result['interpretation']['driver_limit_detected']:raise SystemExit(3)
if __name__=='__main__':main()
