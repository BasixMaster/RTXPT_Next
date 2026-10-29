"""Reject omitted scenes and unlabeled algorithm configurations in version overviews."""
from pathlib import Path
import argparse
import json


def validate(data, repo=None):
    scenes=data['required_scenes'];variants=data['variants']
    if not {'convergence','kitchen','opaque-room'}.issubset(set(scenes)):
        raise ValueError('Original Convergence/Kitchen and controlled opaque room are mandatory')
    if not scenes or len(set(scenes)) != len(scenes) or not variants or len(set(variants)) != len(variants):
        raise ValueError('Required scene and variant IDs must be nonempty and unique')
    expected={(variant,scene) for variant in variants for scene in scenes}
    found=set()
    for row in data['rows']:
        key=(row['variant'],row['scene'])
        if key not in expected or key in found:raise ValueError('Unknown or duplicate comparison row')
        found.add(key)
        if not row.get('algorithm','').strip():raise ValueError('Each row needs an actual/proposed algorithm label')
        development_statuses=['development_not_accepted','low_resolution_development_not_accepted']
        if row['status'] not in ['measured','historical_unverified_caps','unsupported','pending','in_progress']+development_statuses:
            raise ValueError('Unknown comparison coverage status')
        if row['status'] in ['unsupported','pending','in_progress']+development_statuses and not row.get('reason','').strip():
            raise ValueError('Unavailable coverage needs an explicit reason')
        if row['status'] in development_statuses:
            if not row.get('development_evidence','').strip():raise ValueError('Development coverage needs separate evidence')
            if repo is not None and not (Path(repo)/row['development_evidence']).exists():raise ValueError('Development evidence path missing')
        if row['status'] in ['measured','historical_unverified_caps']:
            if not row.get('result','').strip():raise ValueError('Measured coverage needs an evidence path')
            if repo is not None and not (Path(repo)/row['result']).exists():raise ValueError('Comparison evidence path missing')
    if found != expected:raise ValueError('Required comparison scenes were omitted')
    return dict(variants=len(variants),scenes=len(scenes),rows=len(found),status='coverage labels verified; not validation of renderer results')


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('matrix',type=Path);ap.add_argument('--repo',type=Path)
    args=ap.parse_args();print(json.dumps(validate(json.loads(args.matrix.read_text(encoding='utf-8')),args.repo)))
