"""Common display-only scores for each declared steady-state activation variant."""
from pathlib import Path
import argparse
import json
import numpy as np
from analyze_captures import quality_pair


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--captures',type=Path,required=True)
    ap.add_argument('--reference',type=Path,required=True);args=ap.parse_args()
    plan=json.loads((args.captures/'plan.json').read_text());groups={}
    for variant in plan['variants']:
        rows=[]
        for seed in plan['seeds']:
            folder=args.captures/f'{variant}-r3-h64-s{seed}'
            manifest=json.loads((folder/'manifest.json').read_text())
            if manifest['measurement_status']!='captured':raise ValueError('Incomplete display capture')
            pngs=list(folder.glob('*.png'))
            if len(pngs)!=1:raise ValueError('Expected one display capture')
            row=quality_pair(args.reference,pngs[0],'accuracy_reference',flip=True,ppd=67.)
            (folder/'display-quality.json').write_text(json.dumps(row,indent=2,allow_nan=False)+'\n')
            rows.append(row)
        groups[variant]=dict(captures=len(rows),unique_image_hashes=len({r['test']['sha256'] for r in rows}),
            median_mse_srgb=float(np.median([r['metrics']['mse_srgb_encoded_rgb'] for r in rows])),
            median_ldr_flip=float(np.median([r['flip']['full_frame_mean'] for r in rows])))
    result=dict(groups=groups,scope='Three explicitly seeded processes per variant;1spp after64historyframes; common encoded-sRGB/LDR-FLIP track, not raw HDR or equal-time quality')
    (args.captures/'display-quality-summary.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(groups))


if __name__=='__main__':main()
