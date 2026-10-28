"""Analyze RTXPT's scoped GPU CSV and display-space PNG captures; never infer total FPS."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import random
import statistics

SCHEMA = 1
HEADER = ['frame', 'sceneTime', 'renderWidth', 'renderHeight', 'subSamplingMode',
          'pattern', 'blockSize', 'buildMs', 'compactionMs', 'fillMs']
TIMINGS = ('buildMs', 'compactionMs', 'fillMs')
SCOPE = ('GPU path-trace prepass/build, optional subsampling compaction, and main '
         'path-trace fill only. Excludes subsequent RTXDI DI/GI passes, light/cache '
         'updates, guide generation, reconstruction, postprocessing and presentation. '
         'This is not complete-frame GPU time, RTXDI pass time, throughput or FPS.')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def percentile(values, q):
    """R7 / NumPy-default linear percentile, q in [0,1]."""
    if not values or not 0 <= q <= 1:
        raise ValueError('percentile requires values and q in [0,1]')
    values = sorted(values)
    pos = (len(values) - 1) * q
    lower = math.floor(pos)
    upper = math.ceil(pos)
    return values[lower] + (values[upper] - values[lower]) * (pos - lower)


def stats(values):
    if not values:
        return None
    return dict(count=len(values), min_ms=min(values), max_ms=max(values),
                mean_ms=statistics.mean(values), median_ms=statistics.median(values),
                p95_ms=percentile(values, .95), p99_ms=percentile(values, .99),
                sample_stdev_ms=statistics.stdev(values) if len(values) > 1 else None)


def read_perf(path, start, end):
    if not math.isfinite(start) or not math.isfinite(end) or start < 0 or end <= start:
        raise ValueError('scene window must satisfy 0 <= start < end with finite values')
    rows = []
    previous_frame = -1
    with Path(path).open(newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != HEADER:
            raise ValueError(f'{path}: expected exact upstream perfLog schema {HEADER}')
        for line, raw in enumerate(reader, 2):
            if None in raw or any(v is None for v in raw.values()):
                raise ValueError(f'{path}:{line}: wrong column count')
            try:
                row = {k: int(raw[k]) for k in HEADER[:1] + HEADER[2:7]}
                row['sceneTime'] = float(raw['sceneTime'])
                for k in TIMINGS:
                    row[k] = float(raw[k]) if raw[k].strip() else None
            except (ValueError, TypeError) as exc:
                raise ValueError(f'{path}:{line}: invalid numeric field') from exc
            if row['frame'] <= previous_frame:
                raise ValueError(f'{path}:{line}: non-increasing frame; logs may contain appended process runs')
            previous_frame = row['frame']
            if row['renderWidth'] <= 0 or row['renderHeight'] <= 0:
                raise ValueError(f'{path}:{line}: invalid render dimensions')
            if any(row[k] < 0 for k in ('frame', 'subSamplingMode', 'pattern', 'blockSize')):
                raise ValueError(f'{path}:{line}: negative integer field')
            if not math.isfinite(row['sceneTime']):
                raise ValueError(f'{path}:{line}: non-finite scene time')
            for k in TIMINGS:
                if row[k] is not None and (not math.isfinite(row[k]) or row[k] < 0):
                    raise ValueError(f'{path}:{line}: invalid timing {k}')
            if start <= row['sceneTime'] < end:
                if row['fillMs'] is None:
                    raise ValueError(f'{path}:{line}: selected row has no measured fill pass')
                rows.append(row)
    if not rows:
        raise ValueError(f'{path}: no rows in [{start},{end})')
    scene_times = [r['sceneTime'] for r in rows]
    if len(scene_times) < 2 or max(scene_times) <= min(scene_times):
        raise ValueError(f'{path}: selected sequence sceneTime does not advance; '
                         'static scenes can reset sceneTime to zero and never reach captureSequence record start. '
                         'Use independent wall-clock PresentMon timing and captureSimple for static scenes.')
    if any(b < a for a, b in zip(scene_times, scene_times[1:])):
        raise ValueError(f'{path}: selected sceneTime resets or moves backwards; not one advancing sequence window')
    settings = {tuple(r[k] for k in HEADER[2:7]) for r in rows}
    if len(settings) != 1:
        raise ValueError(f'{path}: selected interval changes dimensions/sampling configuration')
    # Blank optional passes mean not used, not an unknown whole-frame duration.
    settings = dict(zip(HEADER[2:7], next(iter(settings))))
    stages = {k: dict(statistics=stats([r[k] for r in rows if r[k] is not None]),
                     active_frames=sum(r[k] is not None for r in rows),
                     inactive_frames=sum(r[k] is None for r in rows)) for k in TIMINGS}
    summed = [sum(r[k] for k in TIMINGS if r[k] is not None) for r in rows]
    return dict(file=Path(path).name, sha256=digest(path), selected_frames=len(rows),
                first_frame=rows[0]['frame'], last_frame=rows[-1]['frame'],
                first_scene_time=rows[0]['sceneTime'], last_scene_time=rows[-1]['sceneTime'],
                scene_time_advancing=True,
                settings=settings, stages=stages, logged_stage_sum=stats(summed))


def bootstrap_run_median_ci(values, samples=4000, seed=0):
    if len(values) < 3:
        return None
    rng = random.Random(seed)
    samples = [statistics.median(rng.choices(values, k=len(values))) for _ in range(samples)]
    return dict(low_ms=percentile(samples, .025), high_ms=percentile(samples, .975),
                confidence=.95, method='percentile bootstrap over process-run medians',
                bootstrap_samples=len(samples), bootstrap_seed=seed)


def perf_group(paths, label, start, end):
    paths = [Path(p) for p in paths]
    if len({p.resolve() for p in paths}) != len(paths):
        raise ValueError('Each process-run CSV may be supplied once only')
    runs = [read_perf(p, start, end) for p in paths]
    if any(r['settings'] != runs[0]['settings'] for r in runs[1:]):
        raise ValueError('Different render dimensions/sampling settings across runs')
    medians = [r['logged_stage_sum']['median_ms'] for r in runs]
    p95s = [r['logged_stage_sum']['p95_ms'] for r in runs]
    return dict(schema_version=SCHEMA, kind='scoped_perf_group', label=label,
                timing_scope=SCOPE, window=dict(scene_start_inclusive=start, scene_end_exclusive=end),
                settings=runs[0]['settings'], runs=runs,
                summary=dict(process_runs=len(runs), selected_frames=sum(r['selected_frames'] for r in runs),
                             median_of_run_medians_ms=statistics.median(medians),
                             median_of_run_p95s_ms=statistics.median(p95s),
                             min_run_median_ms=min(medians), max_run_median_ms=max(medians),
                             run_median_ci95=bootstrap_run_median_ci(medians),
                             interpretation='exploratory: fewer than five process runs' if len(runs) < 5 else 'five-or-more process runs; independence/configuration still requires run manifests'),
                limitations=['Only CSV fields can be checked here. Scene/camera/exposure, effective feature state, hardware and no-image-write interval must be checked from run manifests.',
                             'Do not treat correlated frames as independent benchmark replications.',
                             'A fixed scene timestep is simulated time, not achieved frame rate.'])


def compare_groups(baseline, candidate):
    for x in (baseline, candidate):
        if x.get('kind') != 'scoped_perf_group' or x.get('schema_version') != SCHEMA:
            raise ValueError('compare expects this tool\'s scoped_perf_group JSON')
    for key in ('settings', 'window', 'timing_scope'):
        if baseline[key] != candidate[key]:
            raise ValueError(f'Cannot compare groups with different {key}')
    b = baseline['summary']['median_of_run_medians_ms']
    c = candidate['summary']['median_of_run_medians_ms']
    return dict(schema_version=SCHEMA, kind='scoped_perf_comparison', baseline=baseline['label'],
                candidate=candidate['label'], timing_scope=SCOPE,
                baseline_median_of_run_medians_ms=b, candidate_median_of_run_medians_ms=c,
                candidate_change_percent=100 * (c / b - 1) if b else None,
                baseline_over_candidate_ratio=b / c if c else None,
                ratio_scope='Logged-stage sum only; not whole-renderer or RTXDI-pass speedup.',
                baseline_process_runs=baseline['summary']['process_runs'],
                candidate_process_runs=candidate['summary']['process_runs'],
                inference='descriptive only; no significance or causal improvement claim',
                limitations=['Pair scene/configuration manifests separately; matching CSV settings do not prove matched workloads.',
                             'Existing logger excludes the subsequent DI/GI passes changed by B1.'])


def image_metrics(reference, test, mask=None):
    import numpy as np
    reference, test = np.asarray(reference), np.asarray(test)
    if reference.shape != test.shape or reference.ndim != 3 or reference.shape[2] != 3:
        raise ValueError('RGB arrays must have identical HxWx3 dimensions; no resizing is performed')
    if reference.dtype != np.uint8 or test.dtype != np.uint8:
        raise ValueError('Display comparison expects decoded 8-bit RGB arrays')
    if mask is None:
        mask = np.ones(reference.shape[:2], dtype=bool)
    else:
        mask = np.asarray(mask, dtype=bool)
    if mask.shape != reference.shape[:2] or not mask.any():
        raise ValueError('ROI mask must match HxW and contain at least one pixel')
    a, b = reference.astype(np.float64) / 255., test.astype(np.float64) / 255.
    diff = b - a
    selected = diff[mask]
    mse = float(np.mean(selected ** 2))
    luma = np.array([.2126, .7152, .0722])
    yref, ytest = a @ luma, b @ luma
    smape = float(100 * np.mean((np.abs(yref - ytest) / (np.abs(yref) + np.abs(ytest) + 1e-4))[mask]))
    changed = np.any(reference != test, axis=2) & mask
    return dict(selected_pixels=int(mask.sum()), total_pixels=int(mask.size),
                decoded_rgb_exactly_equal=bool(not changed.any()), changed_pixels=int(changed.sum()),
                changed_pixel_fraction=float(changed.sum() / mask.sum()),
                max_abs_channel_difference_8bit=int(np.max(np.abs(test.astype(np.int16) - reference.astype(np.int16))[mask])),
                mse_srgb_encoded_rgb=mse,
                psnr_srgb_encoded_rgb_db=None if mse == 0 else 10 * math.log10(1 / mse),
                psnr_identical_infinite=bool(mse == 0), smape_display_luma100=smape)


def ldr_flip_parameter_metadata(parameters):
    """Separate inactive HDR defaults, preserving official sentinels as metadata strings.

    The official1.7 evaluator returns +inf exposure sentinels for LDR. They are
    not metric failures and are not active LDR parameters. Unknown/active
    non-finite values still fail rather than being silently converted.
    """
    inactive_names = {'startExposure', 'stopExposure', 'numExposures', 'tonemapper'}
    active, inactive = {}, {}
    for key, value in parameters.items():
        if key in inactive_names:
            if isinstance(value, float) and not math.isfinite(value):
                value = 'NaN' if math.isnan(value) else ('+inf' if value > 0 else '-inf')
            inactive[key] = value
        else:
            if isinstance(value, float) and not math.isfinite(value):
                raise ValueError(f'Official LDR-FLIP returned non-finite active parameter {key}')
            active[key] = value
    if 'ppd' in active and (not isinstance(active['ppd'], (int, float)) or active['ppd'] <= 0):
        raise ValueError('Official LDR-FLIP returned invalid active ppd parameter')
    return active, dict(status='not_applicable_to_LDR', official_returned_defaults=inactive,
                        sentinel_encoding='Non-finite inactive HDR defaults are preserved as explicit strings, not numbers or metric substitutes.')


def quality_pair(reference_path, test_path, relation='regression', roi_path=None, flip=False, ppd=67.):
    import numpy as np
    from PIL import Image
    def load(path):
        with Image.open(path) as image:
            if image.format != 'PNG' or image.mode not in ('RGB', 'RGBA'):
                raise ValueError(f'{path}: expects an upstream 8-bit RGB/RGBA PNG capture')
            return np.asarray(image.convert('RGB')).copy()
    reference, test = load(reference_path), load(test_path)
    mask = None
    if roi_path:
        with Image.open(roi_path) as image:
            mask = np.asarray(image.convert('L')) > 0
    metrics = image_metrics(reference, test, mask)
    flip_result = dict(status='not_requested', reason='Use --flip with the separately installed official flip-evaluator package for LDR-FLIP.')
    if flip:
        if not math.isfinite(ppd) or ppd <= 0:
            raise ValueError('FLIP pixels-per-degree must be positive and finite')
        try:
            import flip_evaluator as evaluator
        except ImportError as exc:
            raise ValueError('--flip requested but official flip-evaluator is not installed; no substitute metric is emitted') from exc
        error_map, mean_error, parameters = evaluator.evaluate(
            reference.astype(np.float32) / 255., test.astype(np.float32) / 255., 'LDR',
            inputsRGB=True, applyMagma=False, computeMeanError=True, parameters={'ppd': ppd})
        error_map = np.asarray(error_map).squeeze()
        if error_map.shape != reference.shape[:2] or not np.isfinite(error_map).all():
            raise ValueError('Official FLIP returned an unexpected/non-finite scalar map')
        if not math.isfinite(float(mean_error)):
            raise ValueError('Official LDR-FLIP returned a non-finite mean error')
        active_parameters, inactive_hdr_parameters = ldr_flip_parameter_metadata(parameters)
        chosen = error_map if mask is None else error_map[mask]
        try:
            version = importlib.metadata.version('flip-evaluator')
        except importlib.metadata.PackageNotFoundError:
            version = 'unavailable; package supplied outside distribution metadata'
        native = getattr(getattr(evaluator, 'nbflip', None), '__file__', None)
        flip_result = dict(status='measured', metric='LDR-FLIP', evaluator='official NVlabs flip-evaluator',
                           evaluator_version=version, native_sha256=digest(native) if native else None,
                           full_frame_mean=float(mean_error), selected_region_mean=float(np.mean(chosen)),
                           selected_region_p95=float(np.quantile(chosen, .95)),
                           parameters=active_parameters, inactive_hdr_parameters=inactive_hdr_parameters,
                           inputs='normalized sRGB PNG; inputsRGB=True',
                           note='Full-frame evaluator map is computed before ROI reduction; not HDR-FLIP.')
    return dict(schema_version=SCHEMA, kind='display_quality_pair', relation=relation,
                reference=dict(file=Path(reference_path).name, sha256=digest(reference_path)),
                test=dict(file=Path(test_path).name, sha256=digest(test_path)),
                roi=None if not roi_path else dict(file=Path(roi_path).name, sha256=digest(roi_path)),
                dimensions=dict(width=int(reference.shape[1]), height=int(reference.shape[0])),
                metrics=metrics, flip=flip_result,
                definitions=dict(rgb='Decoded 8-bit RGB PNG normalized to [0,1]; alpha excluded.',
                                 mse='Mean squared RGB channel difference in encoded sRGB; peak value 1 for PSNR.',
                                 smape='100*mean(|Yref-Ytest|/(|Yref|+|Ytest|+1e-4)); Y=.2126R+.7152G+.0722B applied to encoded sRGB. This is display luma, not scene luminance.'),
                limitations=['PNG captures are tonemapped display images, not raw linear HDR radiance.',
                             'A regression comparison against B0 measures cross-version difference, not image accuracy against converged truth.',
                             'An accuracy_reference relation is a user declaration; reference convergence and scene/config parity require external evidence.',
                             'These display-space metrics are not paper-exact HDR SMAPE, MAPE, RelMSE or HDR-FLIP and do not establish unbiasedness.'])


def save(path, result):
    text = json.dumps(result, indent=2, allow_nan=False) + '\n'
    if path:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(text, encoding='utf-8')
    else:
        print(text, end='')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('perf', help='Summarize one CSV per process run; partial GPU scope only')
    p.add_argument('csv', nargs='+'); p.add_argument('--label', required=True)
    p.add_argument('--scene-start', type=float, required=True); p.add_argument('--scene-end', type=float, required=True)
    p.add_argument('--output')
    p = sub.add_parser('compare', help='Compare summaries with matching timing window/settings')
    p.add_argument('baseline'); p.add_argument('candidate'); p.add_argument('--output')
    p = sub.add_parser('quality', help='Compare decoded PNGs in display space')
    p.add_argument('reference'); p.add_argument('test'); p.add_argument('--roi')
    p.add_argument('--relation', choices=['regression', 'accuracy_reference'], default='regression')
    p.add_argument('--flip', action='store_true'); p.add_argument('--ppd', type=float, default=67.)
    p.add_argument('--output')
    args = parser.parse_args()
    try:
        if args.command == 'perf':
            result = perf_group(args.csv, args.label, args.scene_start, args.scene_end)
        elif args.command == 'compare':
            result = compare_groups(json.loads(Path(args.baseline).read_text(encoding='utf-8')),
                                    json.loads(Path(args.candidate).read_text(encoding='utf-8')))
        else:
            result = quality_pair(args.reference, args.test, args.relation, args.roi, args.flip, args.ppd)
        save(args.output, result)
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as exc:
        parser.exit(2, f'Analysis failed: {exc}\n')


if __name__ == '__main__':
    main()
