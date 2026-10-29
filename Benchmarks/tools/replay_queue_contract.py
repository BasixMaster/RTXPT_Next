"""Effective queue activation and exact same-frame scheduling oracle."""
import re

def verify(log,enabled=False,oracle=False):
    rows=re.findall(r'^PT_QUEUE_CONTRACT enabled=(\d+) shiftStride=(\d+) requestCapacityPerPixel=(\d+) oracle=(\d+) indirect=(\d+)\s*$',log,re.MULTILINE)
    if not rows and not enabled:return None
    expected=(str(int(enabled)),'104','1',str(int(enabled and oracle)),'1')
    if set(rows)!={expected}:raise ValueError('Missing/conflicting replay queue activation or oracle receipt')
    return dict(enabled=enabled,oracle=enabled and oracle,shift_stride_bytes=104,indirect_dispatch=enabled,canonical_accepted=False)

def check_counters(stats,width,height):
    pixels=width*height
    if min(width,height)<=0 or stats['queue_oracle_pixels']!=pixels:raise ValueError('Queue oracle did not compare every destination pixel')
    if stats['queue_overflow']:raise ValueError('Replay queue overflow; fallback preserved work but capacity gate failed')
    if stats['queue_reservoir_mismatches'] or stats['queue_vector_mismatches']:raise ValueError('Queue schedule changed packed reservoir state or vector-radiance bits')
    if stats['queue_shift_stride_bytes']!=104 or stats['queue_cache_elements']!=pixels:raise ValueError('Queue GPU cache layout/capacity mismatch')
    if stats['queue_replay_requests']<0 or stats['queue_cheap_shifts']<0 or stats['queue_replay_requests']+stats['queue_cheap_shifts']>pixels:raise ValueError('Queue request ownership exceeds one source per pixel')
    return dict(compared_pixels=pixels,reservoir_mismatches=0,vector_mismatches=0,overflow=0,replay_requests=stats['queue_replay_requests'],cheap_shifts=stats['queue_cheap_shifts'],scope='Exact packed output/vector comparison under identical frame/input/RNG; not a transport correctness or performance claim')
