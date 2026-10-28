"""Validate the user-disabled RTSS cap using read-only SDK/physical-profile evidence."""
import datetime
ZERO_KEYS=['Limit','LimitTime','SyncScanline0','SyncScanline1']
def collect(backend):
    document=backend.audit()
    document['user_confirmed_disabled']=True
    document['authority']='user_confirmed+SDK_readback+physical_profile'
    return document
def validate(document,exe_sha256):
    if document.get('read_only') is not True or document.get('mutation_performed') is not False:
        raise ValueError('RTSS audit must be explicitly read-only.')
    if document.get('user_confirmed_disabled') is not True or document.get('authority')!='user_confirmed+SDK_readback+physical_profile':
        raise ValueError('The user-disabled RTSS setting has not been confirmed.')
    if document.get('executable_sha256')!=exe_sha256:raise ValueError('RTSS audit identifies a different executable.')
    try:age=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(document['collected_utc'])).total_seconds()
    except (KeyError,TypeError,ValueError):raise ValueError('RTSS audit freshness unavailable.')
    if not 0<=age<=60:raise ValueError('RTSS audit must be collected within60seconds of the boundary.')
    if document.get('coverage')!='known' or document.get('virtual_store_application_profile_exists') is not False:
        raise ValueError('RTSS selected physical profile is ambiguous or VirtualStore-only.')
    q=document.get('property',{})
    if q.get('supported') is not True or q.get('value')!=0:raise ValueError('SDK RTSS application cap is not verified zero.')
    global_property=document.get('global_property',{})
    if global_property.get('supported') is not True or not isinstance(global_property.get('value'),int):raise ValueError('RTSS inherited global setting is unavailable.')
    if document.get('application_profile_exists') is True and document.get('private_application_file_scope')=='installed':
        selected='installed_application_profile';physical='physical_application_caps';selected_sha=document.get('private_application_file_sha256')
    elif document.get('application_profile_exists') is False and document.get('private_application_file_scope')=='absent':
        if global_property['value']!=0:raise ValueError('RTSS global fallback cap is enabled.')
        selected='global_fallback_no_application_profile';physical='physical_global_caps';selected_sha=document.get('private_global_file_sha256')
    else:raise ValueError('RTSS SDK/physical application profile selection disagrees.')
    if not isinstance(selected_sha,str) or len(selected_sha)!=64:raise ValueError('Selected physical RTSS profile hash unavailable.')
    for name in ['effective_caps',physical]:
        q=document.get(name,{})
        if any(q.get(key)!=0 for key in ZERO_KEYS):raise ValueError('RTSS physical/effective frame, frametime or scanline limit is not zero.')
    if document.get('limiter_disabled') is not True:raise ValueError('RTSS limiter-disabled state is not verified.')
    for name in ['helper_sha256','sdk_dll_sha256']:
        if not isinstance(document.get(name),str) or len(document[name])!=64:raise ValueError('RTSS helper/SDK identity unavailable.')
    return dict(authority=document['authority'],collected_utc=document['collected_utc'],executable_sha256=exe_sha256,
                read_only=True,mutation_performed=False,restoration_required=False,rtss_known_caps_disabled=True,
                global_limit_observed=global_property['value'],effective_limit=0,selected_physical_profile=selected,
                selected_physical_profile_sha256=selected_sha,physical_selected_caps_zero=True,
                application_profile_absent=document['application_profile_exists'] is False,virtual_store_application_profile_absent=True,
                helper_sha256=document['helper_sha256'],sdk_dll_sha256=document['sdk_dll_sha256'],
                coverage='known RTSS frame/frametime/scanline settings at the observed boundary; other external limiters remain unknown',
                fully_uncapped_system_verified=False)
