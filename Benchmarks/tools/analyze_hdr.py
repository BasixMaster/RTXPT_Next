"""Compare stored linear RGB PFM images under QUALITY_METRICS.md conventions."""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np


def hdr_flip(reference, test, parameters):
    import importlib.metadata
    import flip_evaluator as evaluator
    error_map, mean, used = evaluator.evaluate(
        reference.astype(np.float32), test.astype(np.float32), 'HDR',
        inputsRGB=False, applyMagma=False, computeMeanError=True, parameters=dict(parameters))
    values = np.asarray(error_map).squeeze()
    if values.shape != reference.shape[:2] or not np.isfinite(values).all() or not np.isfinite(mean):
        raise ValueError('Official HDR-FLIP returned an invalid error map/mean')
    native = Path(evaluator.nbflip.__file__)
    return dict(status='measured', metric='HDR-FLIP', evaluator='official NVlabs flip-evaluator',
                evaluator_version=importlib.metadata.version('flip-evaluator'),
                native_sha256=hashlib.sha256(native.read_bytes()).hexdigest(),
                mean=float(mean), p95=float(np.quantile(values, .95)), parameters=used,
                inputs='Stored nonnegative linear RGB; inputsRGB=False; no external exposure or tonemap transform')


def read_pfm(path):
    with Path(path).open('rb') as stream:
        if stream.readline().strip() != b'PF':
            raise ValueError('Expected RGB PFM')
        width, height = map(int, stream.readline().split())
        scale = float(stream.readline())
        if width <= 0 or height <= 0 or not np.isfinite(scale) or scale == 0:
            raise ValueError('Invalid PFM dimensions/scale')
        raw = stream.read()
    if len(raw) != width * height * 12:
        raise ValueError('PFM payload length mismatch')
    pixels = np.frombuffer(raw, dtype='<f4' if scale < 0 else '>f4')
    return pixels.reshape(height, width, 3)[::-1].astype(np.float64) * abs(scale)


def compare(reference, test):
    if reference.shape != test.shape or reference.ndim != 3 or reference.shape[-1] != 3:
        raise ValueError('Expected matching RGB images')
    if not np.isfinite(reference).all() or not np.isfinite(test).all():
        raise ValueError('Nonfinite radiance: metrics rejected, not silently masked')
    if (reference < 0).any() or (test < 0).any():
        raise ValueError('These radiance metrics require nonnegative inputs')
    weights = np.array([0.2126, 0.7152, 0.0722])
    ref_y, test_y = reference @ weights, test @ weights
    mu = float(ref_y.mean())
    error = test - reference
    relative = mu > 0
    return dict(linear_rgb_mse=float(np.mean(error ** 2)),
                smape_cgns_y100=float(100 * np.mean(abs(test_y-ref_y)/(abs(test_y)+abs(ref_y)+1e-4))),
                full_frame_reference_mean_luminance=mu,
                mape_rgb_ydenom=float(np.mean(abs(error)/(ref_y[..., None]+0.01*mu))) if relative else None,
                relmse_project=float(np.mean(error**2/(ref_y[..., None]**2+(0.01*mu)**2))) if relative else None,
                relative_metrics_available=relative)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--reference', type=Path, required=True)
    ap.add_argument('--test', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--hdr-flip', action='store_true', help='Requires the separately installed official flip-evaluator')
    ap.add_argument('--flip-parameters', type=Path, help='Fixed ppd/tonemapper/exposure JSON derived once from the reference')
    args = ap.parse_args()
    reference, test = read_pfm(args.reference), read_pfm(args.test)
    result = dict(schema_version=1, metric_convention='QUALITY_METRICS.md linear RGB v1; Rec.709 luminance; full frame',
                  scope='single image versus finite-sample reference; not bias or independent-trial evidence',
                  hdr_flip='not measured', value_transform='none',
                  inputs={key: dict(file=path.name, sha256=hashlib.sha256(path.read_bytes()).hexdigest())
                          for key, path in [('reference', args.reference), ('test', args.test)]},
                  metrics=compare(reference, test))
    if args.hdr_flip:
        parameters = json.loads(args.flip_parameters.read_text()) if args.flip_parameters else dict(ppd=67., tonemapper='ACES')
        result['hdr_flip'] = hdr_flip(reference, test, parameters)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    print(json.dumps(result['metrics']))


if __name__ == '__main__':
    main()
