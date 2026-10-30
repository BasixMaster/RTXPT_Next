"""Static environment extension of the explicit unified PSS mode."""
import re

def validate_request(enabled,mis,candidates,stopped):
    if enabled and (not mis or candidates<1 or not stopped):
        raise ValueError('Unified environment requires explicit PSS MIS and stopped animations')

def verify(log,enabled):
    rows=re.findall(r'^PT_UNIFIED_ENV (.+)$',log,re.M)
    lights=re.findall(r'^PT_UNIFIED_ENV_LIGHT frame=(\d+) lightIndex=(\d+) localLights=(\d+)$',log,re.M)
    if not enabled:
        if rows or lights:raise ValueError('Unexpected unified environment activation')
        return dict(active=False)
    expected=dict(enabled='1',proposal='MIP-descent',companion='BSDF-miss',target='single-sample-PSS',standaloneDI='0',standaloneGI='0',fullPTPP='0')
    if not rows or not lights:raise ValueError('Missing environment ownership/light receipt')
    for row in rows:
        if dict(re.findall(r'(\w+)=([^\s]+)',row))!=expected:raise ValueError('Environment receipt differs')
    by_frame={}
    for frame,index,count in lights:
        value=dict(lightIndex=int(index),localLights=int(count))
        if frame in by_frame and by_frame[frame]!=value:raise ValueError('Ambiguous environment light index')
        by_frame[frame]=value
    return dict(active=True,full_ptpp=False,canonical_accepted=False,receipt=expected,lights_by_frame=by_frame)
