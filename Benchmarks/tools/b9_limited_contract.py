"""Verify B9 activation and initial-only roulette without claiming full scene support."""
import re
import numpy as np


def verify(log, stage, probability=0.8):
    rows=re.findall(r'^B9_LIMITED_CONTRACT enabled=(\d+) footprint=(\d+) replaySafe=(\d+) giReuse=(\d+) roulette=([^\s]+)\s*$',log,re.MULTILINE)
    if not rows or len(set(rows))!=1:raise ValueError('Missing/conflicting B9 activation receipt')
    enabled,footprint,replay,gi,rr=rows[0]
    expected=(int(stage in (2,3)),int(stage==2),int(stage==3),1)
    if tuple(map(int,(enabled,footprint,replay,gi)))!=expected:
        raise ValueError('Effective B9 algorithm differs from requested stage')
    replay_rows=re.findall(r'^PT_REPLAY_CONTRACT replayOnly=([01]) roughnessThreshold=[^\s]+\s*$',log,re.MULTILINE)
    if len(set(replay_rows))!=1:raise ValueError('Missing/conflicting effective PT replay receipt')
    full_replay=replay_rows[0]=='1'
    if (stage==3 and not full_replay) or (stage==2 and full_replay):
        raise ValueError('Effective replay policy differs from B9 scope')
    requested=probability if stage in (2,3) else 0.0
    if not np.isfinite(float(rr)) or abs(float(rr)-requested)>1e-6:
        raise ValueError('Effective roulette differs from request')
    return dict(stage=stage,gi_reuse=True,footprint=bool(int(footprint)),replay_safe_ablation=bool(int(replay)),full_prefix_replay=full_replay,
                initial_only_roulette_probability=float(rr),scope='B8 matched control with GI reuse; roulette off' if stage==1 else 'Limited PT++; original-scene footprint remains unsupported' if stage==3 else 'Limited PT++ footprint/roulette development; no canonical promotion')


def check_roulette(stats, active, allow_empty=False):
    tested=stats['roulette_tests'];survived=stats['roulette_survived'];killed=stats['roulette_terminated']
    if stats['replay_roulette_tests']!=0:raise ValueError('Roulette ran during replay')
    if tested!=survived+killed:raise ValueError('Roulette counter conservation failed')
    if active and not ((allow_empty and tested==0) or (tested>0 and survived>0 and killed>0)):raise ValueError('No active initial roulette coverage')
    if not active and tested!=0:raise ValueError('Unrequested roulette')
    return dict(tests=tested,survivals=survived,terminations=killed,replay_tests=0)
