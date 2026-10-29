"""Inspect full-resolution RTXDI 3.1 GI snapshots; M/age prove participation, not accuracy."""
from pathlib import Path
import json
import numpy as np


def inspect(words, meta):
    if meta['packed_stride_bytes'] != 32 or meta['block_size'] != 16:
        raise ValueError('Unsupported pinned GI ABI')
    if words.ndim != 2 or words.shape[1] != 8:
        raise ValueError('Expected eight uint32 words per GI reservoir')
    w, h = meta['width'], meta['height']
    if w < 1 or h < 1 or meta['mode'] not in range(4):
        raise ValueError('Invalid GI capture dimensions/mode')
    y, x = np.indices((h, w), dtype=np.int64)
    addr = (meta['final_index'] * meta['array_pitch'] + (y//16)*meta['block_row_pitch']
            + (x//16)*256 + (y%16)*16 + x%16)
    if addr.min() < 0 or addr.max() >= len(words):
        raise ValueError('GI reservoir address outside buffer')
    selected = words[addr]
    m = selected[..., 3] & 255
    age = (selected[..., 3] >> 8) & 255
    weight = selected[..., 5].copy().view('<f4')
    position = selected[..., :3].copy().view('<f4')
    valid = m > 0
    if not np.isfinite(weight).all() or (weight < 0).any() or not np.isfinite(position[valid]).all():
        raise ValueError('Nonfinite/negative GI reservoir')
    return dict(pixels=w*h, valid=int(valid.sum()), positive_weight=int((valid & (weight > 0)).sum()),
                m_greater_than_one=int((m > 1).sum()), positive_age_valid=int((valid & (age > 0)).sum()),
                max_age_valid=int(age[valid].max()) if valid.any() else None,
                mean_m_valid=float(m[valid].mean()) if valid.any() else None)


def inspect_file(path):
    path = Path(path)
    raw = path.read_bytes()
    if len(raw) % 32: raise ValueError('Truncated GI reservoir buffer')
    return inspect(np.frombuffer(raw, '<u4').reshape(-1, 8), json.loads(Path(str(path)+'.json').read_text()))
