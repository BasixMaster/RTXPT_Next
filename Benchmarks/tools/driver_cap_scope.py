"""Temporary exact-executable NVIDIA cap profile with private crash-recovery state.

No global or existing application profile is changed. Existing associations are
refused. Only a newly created, UUID-named, exact-path profile is removed on restore.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,os,subprocess,uuid
from cap_preflight import interpret_driver

def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(path,data):
    path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix(path.suffix+'.tmp')
    with tmp.open('w',encoding='utf-8') as f:
        json.dump(data,f,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
    tmp.replace(path)

class NativeBackend:
    def __init__(self,helper):self.helper=Path(helper).resolve()
    def call(self,action,exe,profile=None):
        args=[str(self.helper)]+([] if action=='audit' else ['--'+action])+[str(exe)]+([] if profile is None else [profile])
        p=subprocess.run(args,capture_output=True,text=True,timeout=30)
        try:data=json.loads(p.stdout)
        except json.JSONDecodeError:data={}
        if p.returncode:raise RuntimeError(f'NVAPI helper {action} failed with code {p.returncode}; private recovery state retained.')
        return data

class CapScope:
    def __init__(self,backend,state,exe):self.backend=backend;self.path=Path(state);self.exe=Path(exe).resolve()
    def begin(self):
        if self.path.exists():raise ValueError('State exists; restore/review it before starting a new transaction.')
        prior=self.backend.call('audit',self.exe)
        if prior.get('application_profile_found') is not False or prior.get('application_lookup_status')!=-166:
            raise ValueError('Only a verified absent application association can be overridden; existing/shared profiles are refused.')
        data=dict(schema_version=1,phase='prepared',created_utc=utc(),exe=str(self.exe),exe_sha256=hashlib.sha256(self.exe.read_bytes()).hexdigest(),profile='BasixPT Benchmark '+str(uuid.uuid4()),original_application_association='absent',prior_private_audit=prior,global_mutation=False)
        save(self.path,data)
        data['phase']='apply_attempted';save(self.path,data)
        self.backend.call('apply',self.exe,data['profile'])
        current=self.backend.call('audit',self.exe);effective=interpret_driver(current)
        if current.get('application_profile_found') is not True or not effective['driver_allows_uncapped_application'] or effective['settings']['vsync']['state']!='forced_off':
            raise RuntimeError('Readback failed; restore the pending transaction before benchmarking.')
        data.update(phase='active_verified',active_utc=utc(),effective=effective);save(self.path,data)
        return self.public(data)
    def restore(self):
        data=json.loads(self.path.read_text(encoding='utf-8'))
        if Path(data['exe']).resolve()!=self.exe or data['original_application_association']!='absent' or data['global_mutation']:
            raise ValueError('Recovery identity mismatch; no driver mutation performed.')
        if data['phase']=='restored':return self.public(data)
        data['phase']='restore_attempted';save(self.path,data)
        restored=self.backend.call('restore',self.exe,data['profile'])
        current=self.backend.call('audit',self.exe)
        if not restored.get('restored') or current.get('application_profile_found') is not False or current.get('application_lookup_status')!=-166:
            raise RuntimeError('Restoration not verified; private recovery state retained.')
        data.update(phase='restored',restored_utc=utc(),restoration_verified=True);save(self.path,data)
        return self.public(data)
    @staticmethod
    def public(data):
        return dict(schema_version=1,executable_sha256=data['exe_sha256'],phase=data['phase'],global_mutation=False,
                    exact_executable_profile=True,restoration_verified=data.get('restoration_verified',False),
                    driver_cap_state=data.get('effective',{}),external_limiters='unknown; operator/runtime evidence required separately')

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=['run','restore'])
    ap.add_argument('--exe',type=Path,required=True);ap.add_argument('--helper',type=Path,required=True);ap.add_argument('--state',type=Path,required=True)
    ap.add_argument('--receipt',type=Path);ap.add_argument('--command',nargs=argparse.REMAINDER,default=[]);a=ap.parse_args()
    state=a.state.resolve();repo=Path(__file__).resolve().parents[2]
    if state.is_relative_to(repo):raise SystemExit('Recovery state must be private/outside the public repository.')
    scope=CapScope(NativeBackend(a.helper),state,a.exe)
    if a.action=='restore':result=scope.restore()
    else:
        if state.exists():raise SystemExit('Recovery state exists; use the explicit restore action before a new run.')
        command=a.command[1:] if a.command[:1]==['--'] else a.command
        if not command:raise SystemExit('run requires --command followed by a bounded benchmark command.')
        try:
            scope.begin();p=subprocess.run(command,check=False)
        finally:
            if state.exists():result=scope.restore()
        if p.returncode:raise SystemExit(p.returncode)
    if a.receipt:save(a.receipt,result)
    print(json.dumps(result))
if __name__=='__main__':main()
