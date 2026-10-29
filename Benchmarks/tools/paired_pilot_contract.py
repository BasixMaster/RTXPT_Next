"""Validate GPU ownership/finite receipts for the paired/vector pilot."""
import re


def verify(log, enabled=False):
    rows = re.findall(r'^PT_PAIRED_CONTRACT enabled=(\d+) adjacentReciprocal=(\d+) pairOwnedShifts=(\d+) vectorShading=(\d+)\s*$', log, re.MULTILINE)
    if not rows and not enabled:return None
    expected=(str(int(enabled)),)*4
    if not rows or set(rows)!={expected}:raise ValueError('Missing/conflicting paired-vector pilot activation')
    return dict(enabled=enabled,policy='adjacent reciprocal pairs',pair_owned_shifts=enabled,
                vector_shading=enabled,canonical_accepted=False)


def check_counters(stats,width,height):
    pixels=width*height
    pairs=stats['paired_eligible_pairs'];fallback=stats['paired_fallback_pixels']
    shifts=stats['paired_directed_shift_calls'];written=stats['paired_vector_output_pixels']
    if min(width,height)<=0 or min(pairs,fallback,shifts,written)<0:raise ValueError('Invalid paired dispatch counters')
    if written!=pixels or 2*pairs+fallback!=pixels:raise ValueError('Pair ownership skipped or duplicated destination pixels')
    if shifts>2*pairs:raise ValueError('Pair performed more than two directed source shifts')
    if stats['paired_nonfinite_vectors'] or stats['hybrid_returned_nonfinite_target'] or stats['hybrid_returned_nonfinite_weight_product']:
        raise ValueError('Nonfinite paired transport/shading work')
    return dict(pixels=pixels,eligible_pairs=pairs,fallback_pixels=fallback,directed_shifts=shifts,
                scope='GPU ownership and finite-work check; not a transport-mean or timing proof')
