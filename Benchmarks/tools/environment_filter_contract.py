"""Verify effective environment filtering without changing legacy defaults."""
import math
import re


def verify(log, requested=None):
    rows=re.findall(r'^ENVIRONMENT_FILTER_CONTRACT diffuseMip=([^\s]+)\s*$',log,re.MULTILINE)
    if not rows and requested is None:
        return None
    if not rows:
        raise ValueError('Missing effective environment filtering receipt')
    try:
        values={float(x) for x in rows}
    except ValueError as exc:
        raise ValueError('Malformed environment filtering receipt') from exc
    if len(values)!=1:
        raise ValueError('Conflicting environment filtering receipts')
    actual=next(iter(values))
    if not math.isfinite(actual) or actual<0 or actual>16:
        raise ValueError('Invalid effective environment diffuse MIP')
    if requested is not None and actual!=requested:
        raise ValueError('Effective environment diffuse MIP differs from request')
    return dict(diffuse_mip=actual,explicit_override=requested is not None,
                scope='Filtering identity only; no renderer correctness or acceptance claim')
