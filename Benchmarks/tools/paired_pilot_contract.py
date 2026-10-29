"""Validate GPU ownership/finite receipts for the paired/vector pilot."""
import re


def verify(log, enabled=False, gaussian=False):
    if gaussian and not enabled:raise ValueError('Gaussian policy requires paired reuse')
    rows = re.findall(r'^PT_PAIRED_CONTRACT enabled=(\d+) adjacentReciprocal=(\d+) pairOwnedShifts=(\d+) vectorShading=(\d+)\s*$', log, re.MULTILINE)
    if not rows and not enabled:return None
    expected=(str(int(enabled)),str(int(enabled and not gaussian)),str(int(enabled)),str(int(enabled)))
    if not rows or set(rows)!={expected}:raise ValueError('Missing/conflicting paired-vector pilot activation')
    if gaussian:
        policies=re.findall(r'^PT_PAIR_POLICY gaussian=(\d+) residentTables=(\d+) activeTablesPerFrame=(\d+) sigma=(\d+) frameTransforms=(\d+)\s*$',log,re.MULTILINE)
        uploads=re.findall(r'^PT_PAIR_TABLE_UPLOAD tables=(\d+) entries=(\d+) bytes=(\d+) sigma=(\d+) format=(\S+)\s*$',log,re.MULTILINE)
        if not policies or set(policies)!={('1','3','1','16','1')} or not uploads or set(uploads)!={('3','161516','1292128','16','RG32_SINT')}:
            raise ValueError('Missing/conflicting Gaussian policy or table-upload receipt')
    return dict(enabled=enabled,policy='Gaussian reciprocal tables; one per frame' if gaussian else 'adjacent reciprocal pairs',pair_owned_shifts=enabled,
                vector_shading=enabled,canonical_accepted=False)


def check_counters(stats,width,height,gaussian=False):
    pixels=width*height
    pairs=stats['paired_eligible_pairs'];fallback=stats['paired_fallback_pixels']
    shifts=stats['paired_directed_shift_calls'];written=stats['paired_vector_output_pixels']
    if min(width,height)<=0 or min(pairs,fallback,shifts,written)<0:raise ValueError('Invalid paired dispatch counters')
    if written!=pixels or 2*pairs+fallback!=pixels:raise ValueError('Pair ownership skipped or duplicated destination pixels')
    if shifts>2*pairs:raise ValueError('Pair performed more than two directed source shifts')
    if stats['paired_nonfinite_vectors'] or stats['hybrid_returned_nonfinite_target'] or stats['hybrid_returned_nonfinite_weight_product']:
        raise ValueError('Nonfinite paired transport/shading work')
    if gaussian and stats['paired_nonreciprocal_links']!=0:raise ValueError('Nonreciprocal Gaussian frame lookup')
    return dict(pixels=pixels,eligible_pairs=pairs,fallback_pixels=fallback,directed_shifts=shifts,
                scope='GPU ownership and finite-work check; not a transport-mean or timing proof')
