"""Pinned PT++ spatial duplication count oracle and activation receipt.

Geometry-independent reservoir IDs are counted in a clipped 17x17 region,
excluding the center and zero IDs. Counts are capped at255 as in RTXDI3.1's
RG8_UNORM map. This validates the map, not bias or quality of history reduction.
"""
import re
import numpy as np

def count_reference(ids):
    ids=np.asarray(ids)
    if ids.ndim!=2 or min(ids.shape)<1:raise ValueError('Expected a nonempty2D sample-ID image')
    h,w=ids.shape;result=np.zeros((h,w),dtype=np.uint32)
    for dy in range(-8,9):
        for dx in range(-8,9):
            if dx==0 and dy==0:continue
            y0,y1=max(0,-dy),min(h,h-dy);x0,x1=max(0,-dx),min(w,w-dx)
            if y1<=y0 or x1<=x0:continue
            own=ids[y0:y1,x0:x1];other=ids[y0+dy:y1+dy,x0+dx:x1+dx]
            result[y0:y1,x0:x1]+=(own!=0)&(own==other)
    return np.minimum(result,255)

def ids_from_packed(words,meta):
    if meta['packed_stride_bytes']!=64 or meta['block_size']!=16:raise ValueError('Unsupported pinned PT reservoir ABI')
    words=np.asarray(words,dtype='<u4')
    if words.ndim!=2 or words.shape[1]!=16:raise ValueError('Expected16words per packed reservoir')
    h,w=meta['height'],meta['width']
    if min(h,w)<1:raise ValueError('Invalid extent')
    y,x=np.indices((h,w),dtype=np.int64)
    pointer=(y//16)*meta['block_row_pitch']+(x//16)*256+(y%16)*16+x%16+meta['final_index']*meta['array_pitch']
    if pointer.min()<0 or pointer.max()>=len(words):raise ValueError('Reservoir addressing exceeds capture')
    selected=words[pointer];weight=selected[...,3].copy().view('<f4')
    return np.where(weight==0,0,selected[...,15]).astype(np.uint32)

def verify(log,enabled):
    rows=re.findall(r'^PT_DUPLICATION_CONTRACT enabled=(\d+) radius=(\d+) maxCount=(\d+) previousFrame=(\d+) strength=([0-9.]+) biased=(\d+)\s*$',log,re.MULTILINE)
    expected=(str(int(enabled)),'8','255','1','0.500000',str(int(enabled)))
    if set(rows)!={expected}:raise ValueError('Missing/conflicting PT duplication activation receipt')
    return dict(enabled=enabled,radius=8,max_count=255,previous_frame=True,strength=0.5,deliberately_biased=enabled,canonical_accepted=False)

def check_gpu(words,meta,counts,stats,require_consumer=False):
    ids=ids_from_packed(words,meta);expected=count_reference(ids);counts=np.asarray(counts)
    if counts.shape!=ids.shape:raise ValueError('Duplication count dimensions differ from captured reservoirs')
    if not np.array_equal(counts,expected):raise ValueError('GPU duplication map differs from independent17x17 count oracle')
    if stats.get('duplication_produced_pixels')!=ids.size:raise ValueError('Duplication producer did not cover every pixel')
    if require_consumer and (stats.get('duplication_map_reads',0)<=0 or stats.get('duplication_nonzero_reads',0)<=0):raise ValueError('Temporal reuse did not consume a nonzero prior duplication count')
    if stats.get('duplication_max_read_count',256)>255:raise ValueError('Temporal map read exceeds pinned count range')
    return dict(pixels=ids.size,nonzero_counts=int(np.count_nonzero(counts)),max_count=int(counts.max()),exact_count_match=True,temporal_reads=stats.get('duplication_map_reads',0),nonzero_temporal_reads=stats.get('duplication_nonzero_reads',0),scope='Exact current-map producer oracle plus previous-map read counters; not a transport-mean or quality claim')
