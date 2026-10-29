"""Validate actual DI activation/reuse, rather than trusting requested command flags."""
import re

def verify(log,requested_mode=None,expected_di=None):
    rows=re.findall(r'^TRANSPORT_CONTRACT di=(\S+) gi=(\S+) pt=(\S+) diMode=(\S+)(?: |$)',log,re.MULTILINE)
    if not rows and requested_mode is None:return None
    if not rows:raise ValueError('Missing effective DI reuse/transport receipt')
    if len(set(rows))!=1:raise ValueError('Conflicting DI reuse/transport receipts')
    try:di,gi,pt,mode=map(int,rows[0])
    except ValueError as exc:raise ValueError('Malformed DI reuse/transport receipt') from exc
    if di not in [0,1] or gi not in [0,1] or pt not in [0,1] or mode not in range(4):raise ValueError('Invalid DI reuse/transport receipt')
    if requested_mode is not None and mode!=requested_mode:raise ValueError('Actual DI reuse mode differs from request')
    if expected_di is not None and di!=int(expected_di):raise ValueError('Actual DI activation differs from requested lighting mode')
    return dict(active=bool(di),mode=mode,temporal=bool(di and mode in [1,3]),spatial=bool(di and mode in [2,3]),gi=bool(gi),pt=bool(pt),scope='Effective first-frame settings; not estimator correctness or timing proof')
