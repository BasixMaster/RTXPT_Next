"""B8 development receipts and same-frame path-length support checks.

These checks establish dispatch/capture/support, not unbiasedness or GI reuse.
"""
import re
import numpy as np


def verify(log, enabled=False, component=0, stage=0):
    rows = re.findall(r'^B8_PARTITION_CONTRACT development=(\d+) version=(\d+) giReuse=(\d+) component=(\d+) minPTLength=(\d+)(?: stage=(\d+))?\s*$', log, re.MULTILINE)
    rows = [row[:5] + (row[5] or '0',) for row in rows]
    if not rows and not enabled:
        return None
    expected = (str(int(enabled)), '1', '0', str(component), '4', str(stage))
    if not rows or set(rows) != {expected}:
        raise ValueError('Missing, conflicting or incompatible B8 partition receipt')
    return dict(development=enabled, contract_version=1, gi_reuse=False,
                component=component, stage=stage, pt_min_light_inclusive_length=4,
                canonical_accepted=False)


def check_stages(native, native_di, native_di_gi, native_di_gi_pt, final, max_bounces):
    arrays = [np.asarray(x, dtype=np.float64) for x in (native, native_di, native_di_gi, native_di_gi_pt, final)]
    if any(x.shape != arrays[0].shape for x in arrays) or arrays[0].ndim != 3 or arrays[0].shape[-1] != 3:
        raise ValueError('Mismatched same-frame RGB stage dimensions')
    if any(not np.isfinite(x).all() or (x < 0).any() for x in arrays):
        raise ValueError('Nonfinite/negative raw stage radiance')
    # The same output texture was copied after each dispatch. No image-space
    # normalization or fitted brightness correction is permitted here.
    if not np.array_equal(arrays[3], arrays[4]):
        raise ValueError('Final image differs from captured completed sum')
    components = dict(native=arrays[0], di=arrays[1]-arrays[0],
                      gi_short=arrays[2]-arrays[1], pt_long=arrays[3]-arrays[2])
    if any((x < 0).any() for x in components.values()):
        raise ValueError('A cumulative lighting dispatch removed radiance')
    if max_bounces < 2 and np.any(components['gi_short']):
        raise ValueError('GI-short contributed outside k2 support')
    if max_bounces < 3 and np.any(components['pt_long']):
        raise ValueError('PT-long contributed below k3 support')
    return dict(scope='Same-frame support/finite smoke checks only; not a transport-mean oracle',
                max_bounces=max_bounces,
                components={name: dict(mean_rgb=x.mean(axis=(0, 1)).tolist(),
                            nonzero_pixels=int(np.count_nonzero(np.any(x != 0, axis=-1))))
                            for name, x in components.items()})
