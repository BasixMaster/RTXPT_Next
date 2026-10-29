"""Calculated packing-domain oracle (not a GPU shader-execution test)."""
from pathlib import Path
import numpy as np,json
r=Path.cwd();base=r/'work/2026-10-29-gbuffer-precision-v2'
bits=np.arange(0x7c00,dtype=np.uint16);values=bits.view(np.float16).astype(np.float32);clamped=np.minimum(values,np.float32(64512.));halfs=clamped.astype(np.float16).view(np.uint16).astype(np.uint32);rows=[]
for discard in [4,5]:
 codes=np.arange(0x7c00>>discard,dtype=np.uint16);representable=(codes<<discard).view(np.float16).astype(np.float32)
 upper=np.searchsorted(representable,clamped,side='left').clip(0,len(codes)-1);lower=np.maximum(upper-1,0);oracle=np.where(clamped-representable[lower]<representable[upper]-clamped,lower,upper)
 actual=(halfs+(1<<(discard-1)))>>discard;decoded=(actual.astype(np.uint16)<<discard).view(np.float16).astype(np.float32)
 assert np.isfinite(decoded).all() and np.array_equal(actual,oracle)
 old=((bits.astype(np.uint32)>>discard).astype(np.uint16)<<discard).view(np.float16).astype(np.float32)
 assert np.all(np.abs(decoded-clamped)<=np.abs(old-clamped))
 rows.append(dict(discarded_half_bits=discard,finite_half_inputs=len(bits),oracle_mismatches=int(np.count_nonzero(actual!=oracle)),nonfinite_decoded=int(np.count_nonzero(~np.isfinite(decoded))),note='Nearest representable to clamped fp16, ties upward. fp32-to-fp16 double rounding and material/BSDF bias are outside this calculated check.'))
(base/'packing-domain-check.json').write_text(json.dumps(dict(scope='Independent representable-value search oracle compared to a CPU port, not GPU execution or unbiasedness proof',channels=rows),indent=2)+'\n');print(json.dumps(rows))
