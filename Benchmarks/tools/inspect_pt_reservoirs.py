"""Inspect post-frame RTXDI 3.1 f12037f packed PT reservoirs (64-byte ABI)."""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np


def inspect(words, meta):
    if meta['packed_stride_bytes'] != 64 or meta['block_size'] != 16:
        raise ValueError('Unsupported pinned reservoir ABI')
    if words.ndim != 2 or words.shape[1] != 16:
        raise ValueError('Expected 16 uint32 words per reservoir')
    width, height = meta['width'], meta['height']
    if width < 1 or height < 1: raise ValueError('Invalid dimensions')
    y, x = np.indices((height, width), dtype=np.int64)
    pointer = (y//16)*meta['block_row_pitch'] + (x//16)*256 + (y%16)*16 + x%16
    results = {}
    for semantic in ['initial_preserved_index', 'temporal_output_index', 'final_index']:
        address = pointer + int(meta[semantic])*meta['array_pitch']
        if address.min() < 0 or address.max() >= len(words):
            raise ValueError('Reservoir address outside captured buffer')
        selected = words[address]
        m = (selected[..., 5] >> 16).astype('<u2').view('<f2').astype(np.float64)
        age = selected[..., 11] & 31
        rc = (selected[..., 11] >> 8) & 255
        path_length = (selected[..., 11] >> 16) & 255
        weight = selected[..., 3].astype('<u4').view('<f4')
        target = selected[..., 12:15].copy().astype('<u4').view('<f4')
        valid = m > 0
        results[semantic] = dict(slot=int(meta[semantic]), pixels=int(valid.size), valid=int(valid.sum()),
            m_greater_than_one=int((m > 1).sum()),
            positive_age_valid=int(((age > 0) & valid).sum()),
            midpath_reconnection_valid=int((valid & (rc < path_length)).sum()),
            terminal_reconnection_valid=int((valid & (rc == path_length)).sum()),
            age_histogram_valid={str(int(k)):int(v) for k,v in zip(*np.unique(age[valid],return_counts=True))},
            rc_length_histogram_valid={str(int(k)):int(v) for k,v in zip(*np.unique(rc[valid],return_counts=True))},
            path_length_histogram_valid={str(int(k)):int(v) for k,v in zip(*np.unique(path_length[valid],return_counts=True))},
            max_age_valid=int(age[valid].max()) if valid.any() else None,
            mean_m_valid=float(m[valid].mean()) if valid.any() else None,
            valid_with_positive_weight=int((valid & (weight > 0)).sum()),
            positive_weight_path_length_histogram={str(int(k)):int(v) for k,v in zip(*np.unique(path_length[valid & (weight > 0)],return_counts=True))},
            nonfinite_m=int((~np.isfinite(m)).sum()),
            nonfinite_weight_valid=int((valid & ~np.isfinite(weight)).sum()),
            nonfinite_target_valid=int((valid & ~np.isfinite(target).all(axis=-1)).sum()))
    return results


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--binary', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    raw = args.binary.read_bytes()
    if len(raw) % 64: raise ValueError('Truncated packed reservoir buffer')
    meta = json.loads(Path(str(args.binary)+'.json').read_text())
    result = dict(schema_version=1, binary_sha256=hashlib.sha256(raw).hexdigest(),
                  phase='post-frame snapshot; aliases may share a slot, not an intermediate-pass trace',
                  limitation='Age/M show stored history participation; do not establish unbiased weighting or quality benefit.',
                  metadata=meta, statistics=inspect(np.frombuffer(raw, '<u4').reshape(-1, 16), meta))
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    print(json.dumps(result['statistics']))


if __name__ == '__main__': main()
