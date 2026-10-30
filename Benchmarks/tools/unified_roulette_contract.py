"""Explicit initial-only roulette composition, PT++6.2.4/supplement6."""
import re,math

def validate_request(enabled,mis,candidates,replay,probability):
    if enabled and (not mis or candidates<1 or not replay or probability is None or not math.isfinite(probability) or not .1<=probability<1):
        raise ValueError('Unified roulette requires PSS MIS, full-prefix replay and survival in[.1,1)')

def verify(log,enabled,probability):
    rows=re.findall(r'^PT_UNIFIED_ROULETTE (.+)$',log,re.M)
    if not enabled:
        if rows:raise ValueError('Unexpected unified roulette activation')
        return dict(active=False)
    if not rows:raise ValueError('Missing unified roulette receipt')
    for row in rows:
        actual=dict(re.findall(r'(\w+)=([^\s]+)',row));q=float(actual.pop('survival','nan'))
        if actual!=dict(enabled='1',initialOnly='1',replayDraws='0',target='survival-free',fullPTPP='0') or not math.isclose(q,probability,rel_tol=1e-6,abs_tol=1e-7):raise ValueError('Unified roulette receipt differs')
    return dict(active=True,survival=probability,initial_only=True,full_ptpp=False)

def check_counters(c):
    if c['roulette_tests']<=0 or c['roulette_survived']<=0 or c['roulette_terminated']<=0 or c['roulette_tests']!=c['roulette_survived']+c['roulette_terminated'] or c['replay_roulette_tests']!=0:
        raise ValueError('Initial-only roulette counters failed')
