"""Canonical experiment labels, mode eligibility, and effective rendering receipts."""
from pathlib import Path
import hashlib
import json
import re

REGISTRY=Path(__file__).resolve().parents[1]/'versions.json'
SCHEME='2026-10-29-user-confirmed-B0-B10'
MODE_FLAGS={'default':(0,0,0),'di':(1,0,0),'digi':(1,1,0),'pt':(0,0,1),'dipt':(1,0,1),'reference':(0,0,0)}


def prepare(variant, mode, preset='matched-raw', reconnection=None, roulette=None):
    if variant is None:return None
    registry=json.loads(REGISTRY.read_text(encoding='utf-8'))
    if registry['numbering_scheme']!=SCHEME:raise ValueError('Unrecognized experiment numbering scheme')
    record=next((v for v in registry['versions'] if v['id']==variant),None)
    if record is None:raise ValueError('Unknown canonical variant')
    if variant in ['B8','B9','B10']:
        raise ValueError('This combined PT/GI configuration is not implemented; no canonical result may be labelled as active')
    if mode=='reference':raise ValueError('Finite-reference truth captures are separate from the canonical realtime configuration')
    expected=(0,0,0) if variant=='B0' else tuple(record['configuration'][k] for k in ['restir_di','restir_gi','restir_pt'])
    if MODE_FLAGS[mode]!=expected:raise ValueError('Requested rendering mode does not match the canonical experiment')
    if variant=='B0' and preset!='raw-native-control':
        raise ValueError('B0 original defaults are preserved; these raw wrappers require the explicit raw-native-control subpreset')
    if variant!='B0' and preset=='raw-native-control':raise ValueError('raw-native-control qualifies the B0 reference only')
    if variant in ['B0','B1','B2','B3','B4','B5'] and (reconnection is not None or roulette is not None):
        raise ValueError('Native reference controls do not expose PT++ arguments')
    extra=(reconnection==1 or (roulette is not None and 0<roulette<1))
    if extra and (variant not in ['B6','B7'] or preset!='limited-ptpp-ablation'):
        raise ValueError('Additional PT++ settings need an explicit B6/B7 limited-ablation label; GI-off is not B9')
    if preset=='limited-ptpp-ablation' and (variant not in ['B6','B7'] or not extra):
        raise ValueError('Limited-ablation label requires an active PT++ mechanism on B6/B7')
    return dict(numbering_scheme=SCHEME,variant=variant,preset=preset,algorithm=record['algorithm_overview'],
                expected_flags=dict(zip(['di','gi','pt'],expected)),expected_runtime_sha=record['rtxdi_sha'],expected_base_sha=record['source_sha'],expected_assets_sha=record['assets_sha'],
                display_label=variant+' · '+preset+' · '+record['algorithm_overview'],
                limitation='B0 raw control is not original default rendering' if variant=='B0' else 'Actual settings must match the effective renderer receipt')


def verify(log, requested):
    if requested is None:return dict(coverage='not requested; legacy labels retain their original numbering')
    matches=re.findall(r'^TRANSPORT_CONTRACT di=([01]) gi=([01]) pt=([01]) diMode=(\d+) neeMIS=(\d+) maxBounces=(\d+) maxDiffuseBounces=(\d+)\s*$',log,re.MULTILINE)
    if not matches or len(set(matches))!=1:raise ValueError('Canonical experiment lacks a unique effective transport receipt')
    row=matches[0];actual=dict(zip(['di','gi','pt'],map(int,row[:3])))
    if actual!=requested['expected_flags']:raise ValueError('Effective DI/GI/PT configuration differs from canonical label')
    native=re.findall(r'^NATIVE_CONTROLS_CONTRACT revision=2 root=([0-9a-f]{40}) runtime=([0-9a-f]{40}) ',log,re.MULTILINE)
    if requested['variant'] in ['B0','B1','B2','B3','B4','B5'] and not native:
        raise ValueError('Native canonical comparisons require the versioned build provenance receipt')
    if native and (len(set(native))!=1 or native[0][1]!=requested['expected_runtime_sha'] or native[0][0]!=requested['expected_base_sha']):
        raise ValueError('Native build receipt runtime differs from canonical variant')
    return dict(coverage='verified effective first-frame transport receipt',flags=actual,di_mode=int(row[3]),nee_mis=int(row[4]),
                max_bounces=int(row[5]),max_diffuse_bounces=int(row[6]),runtime_scope='Runtime identity requires frozen source/build evidence in addition to this transport receipt')


def verify_snapshot(path,requested):
    if requested is None:return
    if path is None:raise ValueError('Canonical comparisons require a frozen artifact manifest; warm caches first without a canonical result label')
    snapshot=json.loads(Path(path).read_text(encoding='utf-8'))
    runtime=snapshot.get('submodules',{}).get('External/Rtxdi',{})
    if runtime.get('checked_out_sha')!=requested['expected_runtime_sha'] or runtime.get('recorded_gitlink')!=requested['expected_runtime_sha']:
        raise ValueError('Frozen runtime pin does not match canonical experiment')

    if runtime.get('tracked_diff_sha256')!=hashlib.sha256(b'').hexdigest():
        raise ValueError('Canonical runtime must have no tracked modifications')

    assets=snapshot.get('submodules',{}).get('Assets',{})
    if assets.get('checked_out_sha')!=requested['expected_assets_sha'] or assets.get('recorded_gitlink')!=requested['expected_assets_sha'] or assets.get('tracked_diff_sha256')!=hashlib.sha256(b'').hexdigest():
        raise ValueError('Canonical comparisons require matching clean original assets')
