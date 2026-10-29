"""Verify the guarded original-scene PT contract; this is not scene acceptance."""
import re


def validate_request(enabled, mode, replay_only, variant):
    if enabled and (mode not in ['pt', 'dipt'] or not replay_only or variant is not None):
        raise ValueError('Extended-scene development requires PT, full-prefix replay and no canonical acceptance label')


def verify(log, enabled, diffuse_budget=None, requested_mode=None):
    if not enabled:
        return None
    rows=re.findall(r'^PT_EXTENDED_SCENE_CONTRACT development=(\d+) diffuseBudget=(\d+) fullPrefixReplay=(\d+)\s*$',log,re.MULTILINE)
    if len(set(rows))!=1:
        raise ValueError('Missing or conflicting extended-scene receipt')
    development,budget,replay=map(int,rows[0])
    if development!=1 or replay!=1 or (diffuse_budget is not None and budget!=diffuse_budget):
        raise ValueError('Effective extended-scene diffuse/replay contract differs from request')
    replay_rows=re.findall(r'^PT_REPLAY_CONTRACT replayOnly=(\d+) roughnessThreshold=([^\s]+)\s*$',log,re.MULTILINE)
    if len(set(replay_rows))!=1 or replay_rows[0][0]!='1' or float(replay_rows[0][1])!=1.0:
        raise ValueError('Full-prefix fixed-threshold replay was not activated')
    transport=re.findall(r'^TRANSPORT_CONTRACT di=([01]) gi=([01]) pt=([01]) diMode=\d+ neeMIS=\d+ maxBounces=(\d+) maxDiffuseBounces=(\d+)\s*$',log,re.MULTILINE)
    if len(set(transport))!=1 or transport[0][1:3]!=('0','1') or int(transport[0][4])!=budget:
        raise ValueError('Extended-scene transport receipt is inconsistent')
    if requested_mode is not None and int(transport[0][0])!=int(requested_mode=='dipt'):
        raise ValueError('Actual DI activation differs from the requested extended-scene mode')
    return dict(scope='Verified effective development settings; not scene correctness or canonical acceptance',
                full_prefix_replay=True,diffuse_budget=budget,max_bounces=int(transport[0][3]),canonical_accepted=False)
