"""Seed-paired process-summary differences; matching seeds does not imply identical paths."""
import math,statistics

def summarize(before_seeds,before_values,after_seeds,after_values):
    if len(before_seeds)!=len(before_values) or len(after_seeds)!=len(after_values):
        raise ValueError('Seed/value dimensions differ')
    if len(set(before_seeds))!=len(before_seeds) or len(set(after_seeds))!=len(after_seeds):
        raise ValueError('Duplicate seeds')
    a=dict(zip(before_seeds,before_values));b=dict(zip(after_seeds,after_values))
    if not a or set(a)!=set(b):raise ValueError('Paired seed sets differ')
    if any(not math.isfinite(v) for v in list(a.values())+list(b.values())):raise ValueError('Nonfinite process summary')
    seeds=sorted(a);delta=[b[s]-a[s] for s in seeds];mean_a=statistics.mean(a.values());mean_b=statistics.mean(b.values())
    return dict(seeds=seeds,baseline_values=[a[s] for s in seeds],candidate_values=[b[s] for s in seeds],differences=delta,
                mean_difference=statistics.mean(delta),sample_se=statistics.stdev(delta)/len(delta)**.5 if len(delta)>1 else None,
                change_percent_of_means=100*(mean_b/mean_a-1) if mean_a!=0 else None,
                scope='Seed-paired separate process captures, not identical sampled paths; small-sample exploratory uncertainty')


def main():
    import argparse,json,hashlib
    from pathlib import Path
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--quality',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    if a.output.exists():raise ValueError('Output must be new')
    q=json.loads(a.quality.read_text());result=dict(schema_version=1,quality_sha256=hashlib.sha256(a.quality.read_bytes()).hexdigest(),scope='Three-seed paired differences across separate processes; no identical-path or universal-significance claim',scenes={})
    for scene,item in q['scenes'].items():
        before,after=item['summary']['B8'],item['summary']['B9'];metrics={}
        for metric in ('mean_frame_linear_mse','mean_image_linear_mse','mean_y_difference_percent','frame64_hdr_flip','frame64_ldr_flip'):
            metrics[metric]=summarize(before['seeds'],before[metric]['values'],after['seeds'],after[metric]['values'])
            if metric=='mean_y_difference_percent':metrics[metric]['unit']='percentage points';metrics[metric].pop('change_percent_of_means')
        result['scenes'][scene]=metrics
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print('Paired quality differences written.')
if __name__=='__main__':main()
