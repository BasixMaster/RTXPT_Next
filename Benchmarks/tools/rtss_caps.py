"""RTSS SDK cap audit and temporary application-profile scope.

Uses the installed SDK's documented LoadProfile/GetProfileProperty APIs.
Only --action run/restore can mutate the selected executable-name profile.
Global profiles, unrelated profiles and other processes are never modified.
"""
from pathlib import Path
import argparse,configparser,datetime,hashlib,json,os,subprocess,sys
from driver_cap_scope import save,utc

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
CAP_KEYS=['Limit','LimitDenominator','LimitTime','LimitTimeDenominator','SyncScanline0','SyncScanline1','SyncLimiter']

class RTSSBackend:
    def __init__(self,install,exe,helper):
        if sys.platform!='win32':raise RuntimeError('The installed RTSS SDK is Windows-only.')
        self.install=Path(install).resolve();self.exe=Path(exe).resolve();self.name=self.exe.name
        if not self.name.lower().endswith('.exe'):raise ValueError('An executable basename is required.')
        self.name.encode('ascii');self.helper=Path(helper).resolve()
        self.dll_path=self.install/'RTSSHooks.dll'
    def native(self,action):
        p=subprocess.run([str(self.helper),str(self.install),self.name,action],capture_output=True,text=True,timeout=20)
        if p.returncode:raise RuntimeError(f'RTSS SDK helper {action} failed with code{p.returncode}; no success assumed.')
        try:return json.loads(p.stdout)
        except json.JSONDecodeError:raise RuntimeError('RTSS SDK helper returned invalid JSON.')
    def profile_file(self):
        # RTSS SDK ships <application>.exe.cfg templates; verify the selected
        # name only, without reading or exporting unrelated profile names.
        path=self.install/'Profiles'/(self.name+'.cfg')
        virtual=Path(os.environ['LOCALAPPDATA'])/'VirtualStore'/Path(*self.install.parts[1:])/'Profiles'/(self.name+'.cfg')
        found=[p for p in [path,virtual] if p.is_file()]
        if len(found)>1:raise RuntimeError('Multiple physical RTSS target profiles; SDK path ownership is ambiguous.')
        return found[0] if found else None
    def caps_file(self,path):
        if path is None:return {}
        config=configparser.ConfigParser(interpolation=None,strict=False)
        config.read_string(path.read_bytes().decode('utf-8',errors='replace'))
        values={}
        for key in CAP_KEYS:
            try:values[key]=int(config['Framerate'][key],0)
            except (KeyError,ValueError):values[key]=None
        return values
    def audit(self):
        native=self.native('audit');exists=native['application_profile_exists'];file=self.profile_file();global_file=self.install/'Profiles/Global'
        if exists!=(file is not None):raise RuntimeError('SDK/file application profile presence disagrees; no mutation allowed.')
        global_caps=self.caps_file(global_file);app_caps=self.caps_file(file)
        global_property=native['global_property'];app_property=native['property']
        effective={key:app_caps.get(key) if app_caps.get(key) is not None else global_caps.get(key) for key in CAP_KEYS}
        known=app_property['supported'] and all(effective.get(key) is not None for key in ['Limit','LimitTime','SyncScanline0','SyncScanline1'])
        disabled=known and app_property['value']==0 and all(effective[key]==0 for key in ['Limit','LimitTime','SyncScanline0','SyncScanline1'])
        return dict(schema_version=1,collected_utc=utc(),executable_sha256=digest(self.exe),helper_sha256=digest(self.helper),
                    read_only=True,mutation_performed=False,process_elevated=native.get('process_elevated',False),application_profile_exists=exists,scope='executable_basename',
                    property=app_property,global_property=global_property,effective_caps=effective,
                    physical_global_caps=global_caps,physical_application_caps=app_caps,virtual_store_application_profile_exists=file is not None and file.parent!=self.install/'Profiles',
                    limiter_disabled=bool(disabled),coverage='known' if known else 'unknown',
                    private_application_file_sha256=digest(file) if file else None,
                    private_application_file_scope='installed' if file is not None and file.parent==self.install/'Profiles' else ('virtual_store' if file else 'absent'),
                    private_global_file_sha256=digest(global_file),sdk_dll_sha256=digest(self.dll_path))
    def apply_absent(self):
        if self.native('audit')['application_profile_exists'] or self.profile_file() is not None:raise RuntimeError('Existing RTSS application profiles are refused.')
        # SDK documentation: missing app profiles inherit the global profile;
        # explicitly storing FramerateLimit0 creates a disabled per-app override.
        self.native('apply')
    def restore_absent(self,created_sha):
        exists=self.native('audit')['application_profile_exists'];file=self.profile_file()
        if not exists and file is None:return
        if not exists or file is None or digest(file)!=created_sha:raise RuntimeError('Task RTSS profile was changed externally; restoration refused.')
        self.native('delete')
        if self.native('audit')['application_profile_exists'] or self.profile_file() is not None:raise RuntimeError('RTSS profile deletion was not verified.')

class RTSSScope:
    def __init__(self,backend,state,exe):self.backend=backend;self.path=Path(state);self.exe=Path(exe).resolve()
    def begin(self):
        if self.path.exists():raise ValueError('Recovery state exists; explicitly restore it before another run.')
        before=self.backend.audit()
        if not before.get('process_elevated'):raise ValueError('The official RTSS SDK sample requires administrator execution; refusing a VirtualStore-only override. No mutation performed.')
        if before['application_profile_exists']:raise ValueError('Existing RTSS application profile is refused; preserve user settings.')
        # Refuse nonzero frametime/scanline sync: the documented SDK mutation
        # below controls the frame-rate limit only, not unsupported properties.
        if before['coverage']!='known' or any(before['effective_caps'].get(k)!=0 for k in ['LimitTime','SyncScanline0','SyncScanline1']):
            raise ValueError('Uncovered frametime/scanline limiter; no RTSS mutation performed.')
        data=dict(schema_version=1,phase='prepared',created_utc=utc(),exe=str(self.exe),exe_sha256=digest(self.exe),original_application_profile='absent',global_mutation=False,prior_private_audit=before)
        save(self.path,data);data['phase']='apply_attempted';save(self.path,data)
        self.backend.apply_absent();after=self.backend.audit()
        data['created_profile_sha256']=after['private_application_file_sha256'];data['active_private_audit']=after;save(self.path,data)
        if not after['application_profile_exists'] or not after['limiter_disabled'] or after.get('private_application_file_scope')!='installed' or before['private_global_file_sha256']!=after['private_global_file_sha256']:
            raise RuntimeError('RTSS cap disable readback/global preservation failed; recovery state retained.')
        data.update(phase='active_verified',active_utc=utc());save(self.path,data);return self.public(data)
    def restore(self):
        data=json.loads(self.path.read_text(encoding='utf-8'))
        if Path(data['exe']).resolve()!=self.exe or data['original_application_profile']!='absent' or data['global_mutation']:raise ValueError('RTSS recovery identity mismatch.')
        if data['phase']=='restored':return self.public(data)
        if not data.get('created_profile_sha256'):
            # A hard failure between SaveProfile and readback is ambiguous.
            # Do not adopt/delete a profile without its owned fingerprint.
            current=self.backend.audit()
            if current['application_profile_exists']:raise RuntimeError('Ambiguous RTSS apply: inspect/reconcile the created profile before recovery.')
        data['phase']='restore_attempted';save(self.path,data)
        self.backend.restore_absent(data.get('created_profile_sha256'));after=self.backend.audit()
        if after['application_profile_exists'] or after['private_global_file_sha256']!=data['prior_private_audit']['private_global_file_sha256']:
            raise RuntimeError('RTSS original absence/global-state restoration not verified.')
        data.update(phase='restored',restored_utc=utc(),restoration_verified=True);save(self.path,data);return self.public(data)
    @staticmethod
    def public(data):
        active=data.get('active_private_audit',{})
        return dict(schema_version=1,phase=data['phase'],executable_sha256=data['exe_sha256'],profile_scope='executable_basename',
                    global_mutation=False,rtss_limit_disabled=active.get('limiter_disabled',False),
                    effective_active_caps=active.get('effective_caps'),restoration_verified=data.get('restoration_verified',False))

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--action',choices=['audit','run','restore'],default='audit')
    ap.add_argument('--install-dir',type=Path,required=True);ap.add_argument('--exe',type=Path,required=True)
    ap.add_argument('--helper',type=Path,required=True,help='Private x86 native helper compiled against the installed RTSS SDK ABI.')
    ap.add_argument('--user-confirmed-disabled',action='store_true',help='Record the operator-provided user confirmation; does not change any RTSS setting.')
    ap.add_argument('--state',type=Path);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--command',nargs=argparse.REMAINDER,default=[]);a=ap.parse_args()
    backend=RTSSBackend(a.install_dir,a.exe,a.helper)
    if a.action=='audit':
        result=backend.audit();result['user_confirmed_disabled']=a.user_confirmed_disabled
        result['authority']='user_confirmed+SDK_readback+physical_profile' if a.user_confirmed_disabled else 'SDK_readback+physical_profile'
    else:
        if a.state is None:raise SystemExit('A private --state path is required.')
        state=a.state.resolve();repo=Path(__file__).resolve().parents[2]
        if state.is_relative_to(repo):raise SystemExit('RTSS recovery state must stay outside the public repository.')
        scope=RTSSScope(backend,state,a.exe)
        if a.action=='restore':result=scope.restore()
        else:
            if state.exists():raise SystemExit('Existing recovery state requires explicit restore.')
            if not a.command:raise SystemExit('run requires a bounded --command.')
            try:scope.begin();p=subprocess.run(a.command,check=False)
            finally:
                if state.exists():result=scope.restore()
            if p.returncode:raise SystemExit(p.returncode)
    save(a.output,result)
    print(json.dumps({k:result[k] for k in ['phase','application_profile_exists','coverage','property','global_property','limiter_disabled','rtss_limit_disabled','restoration_verified'] if k in result}))
if __name__=='__main__':main()
