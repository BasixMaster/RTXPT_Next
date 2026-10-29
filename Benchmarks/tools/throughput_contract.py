"""Effective opt-in prefix-throughput diagnostic identity."""
import re

def validate_request(preserve,capture=False,linear_hdr=False,mode=None,variant=None):
    if preserve not in [None,0,1]:raise ValueError('Prefix throughput must be0/1 or omitted')
    if preserve==1 and variant is not None:raise ValueError('Unclamped throughput is a separate ablation, not a canonical default')
    if capture and (not linear_hdr or mode not in ['di','dipt']):raise ValueError('Packed throughput diagnostic requires realtime DI/DI+PT raw HDR')

def verify(log,preserve=None,capture=False):
    rows=re.findall(r'^PREFIX_THROUGHPUT_CONTRACT preserveAboveOne=(\S+) capturePacked=(\S+)\s*$',log,re.MULTILINE)
    if not rows and preserve is None and not capture:return None
    if not rows:raise ValueError('Missing prefix throughput receipt')
    if len(set(rows))!=1 or any(x not in ['0','1'] for x in rows[0]):raise ValueError('Invalid/conflicting prefix throughput receipt')
    actual,packed=map(int,rows[0])
    if preserve is not None and actual!=preserve:raise ValueError('Actual prefix clamp differs from request')
    if bool(packed)!=bool(capture):raise ValueError('Packed throughput capture differs from request')
    return dict(preserve_above_one=bool(actual),capture_packed=bool(packed),scope='Upper clamp identity; R11G11B10 quantization/finite upper clamp remain')
