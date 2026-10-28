"""Requested seed/camera identity and actual first-frame renderer receipt."""
import argparse
import re


def seed_value(value):
    try: seed = int(value)
    except ValueError as exc: raise argparse.ArgumentTypeError('Seed must be uint32') from exc
    if not 0 <= seed <= 0xffffffff:
        raise argparse.ArgumentTypeError('Seed must be in 0..4294967295')
    return seed


def verify(log, requested_seed=None, pixel_center=False):
    matches = re.findall(r'^SAMPLING_CONTRACT seed=(\d+) realtime=([01]) referencePixelCenter=([01]) pixelJitterScale=([^\s]+)\s*$', log, re.MULTILINE)
    if not matches:
        if requested_seed is not None or pixel_center:
            raise ValueError('Requested seed/camera controls lack an effective renderer receipt')
        return dict(coverage='unavailable; legacy renderer receipt absent')
    if len(set(matches)) != 1: raise ValueError('Ambiguous effective sampling receipts')
    seed, realtime, center, jitter = matches[0]
    if requested_seed is not None and int(seed) != requested_seed:
        raise ValueError('Effective seed differs from requested seed')
    if pixel_center and (center != '1' or float(jitter) != 0):
        raise ValueError('Pixel-center reference contract not active')
    return dict(coverage='verified first-frame effective receipt', seed=int(seed), realtime=bool(int(realtime)),
                reference_pixel_center=bool(int(center)), pixel_jitter_scale=float(jitter))


def verify_di(log, strict=False):
    matches = re.findall(r'^DI_VALIDATION_CONTRACT strict=([01]) boiling=([01]) discountNaive=([01])\s*$', log, re.MULTILINE)
    if not matches:
        if strict: raise ValueError('Strict DI validation lacks an effective renderer receipt')
        return dict(coverage='unavailable; legacy renderer receipt absent')
    if len(set(matches)) != 1: raise ValueError('Ambiguous DI validation receipts')
    requested, boiling, discount = matches[0]
    if strict and (requested, boiling, discount) != ('1', '0', '0'):
        raise ValueError('Strict DI validation settings are not active')
    temporal = re.findall(r'^DI_TEMPORAL_CONTRACT permutation=([01]) maxHistory=(\d+)\s*$',log,re.MULTILINE)
    if strict and (not temporal or len(set(temporal)) != 1 or temporal[0][0] != '0'):
        raise ValueError('Strict static DI validation requires permutation off with an effective receipt')
    return dict(coverage='verified first-frame effective receipt', strict=bool(int(requested)),
                boiling=bool(int(boiling)), discount_naive=bool(int(discount)),
                temporal_permutation=bool(int(temporal[0][0])) if temporal else None)


def verify_pt_replay(log, requested=False):
    matches = re.findall(r'^PT_REPLAY_CONTRACT replayOnly=([01]) roughnessThreshold=([^\s]+)\s*$', log, re.MULTILINE)
    if not matches:
        if requested: raise ValueError('PT replay-only diagnostic lacks an effective renderer receipt')
        return dict(coverage='unavailable; legacy renderer receipt absent')
    if len(set(matches)) != 1: raise ValueError('Ambiguous PT replay receipts')
    active, threshold = matches[0]
    if requested and (active != '1' or float(threshold) != 1.):
        raise ValueError('PT replay-only diagnostic is not active')
    return dict(coverage='verified first-frame effective receipt', replay_only=bool(int(active)), roughness_threshold=float(threshold))


def verify_pt_history(log, disable_age=False):
    matches = re.findall(r'^PT_HISTORY_CONTRACT ageRejection=([01]) maxAge=(\d+) maxHistory=(\d+)\s*$', log, re.MULTILINE)
    if not matches:
        if disable_age: raise ValueError('PT age ablation lacks an effective renderer receipt')
        return dict(coverage='unavailable; legacy renderer receipt absent')
    if len(set(matches)) != 1: raise ValueError('Ambiguous PT history receipts')
    age, max_age, mass = map(int,matches[0])
    if disable_age and (age != 0 or mass != 8):
        raise ValueError('PT age ablation must disable age rejection and retain history mass cap8')
    return dict(coverage='verified first-frame effective receipt', age_rejection=bool(age), max_age=max_age,max_history=mass)


def verify_pt_spatial(log, fixed=None):
    matches = re.findall(r'^PT_SPATIAL_CONTRACT samples=(\d+) boost=(\d+)\s*$', log, re.MULTILINE)
    if not matches:
        if fixed is not None: raise ValueError('Fixed PT neighbor count lacks an effective renderer receipt')
        return dict(coverage='unavailable; legacy renderer receipt absent')
    if len(set(matches)) != 1: raise ValueError('Ambiguous PT spatial receipts')
    ordinary, boosted=map(int,matches[0])
    if fixed is not None and (ordinary != fixed or boosted != fixed):
        raise ValueError('PT neighbor count differs from requested fixed count')
    return dict(coverage='verified first-frame effective receipt', samples=ordinary, boost=boosted)
