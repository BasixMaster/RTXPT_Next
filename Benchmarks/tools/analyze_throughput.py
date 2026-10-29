"""Read the packed prefix diagnostic. Values are weights, not radiance."""
from pathlib import Path
import struct,json,argparse
import numpy as np

def decode(blob):
    if len(blob)<24 or blob[:8]!=b'RTXPTTHP':raise ValueError('Missing packed throughput header')
    version,width,height,pixel_bytes=struct.unpack_from('<4I',blob,8)
    if version!=1 or not width or not height or pixel_bytes!=4 or len(blob)!=24+width*height*4:raise ValueError('Unsupported/truncated packed throughput layout')
    packed=np.frombuffer(blob,dtype='<u4',offset=24).reshape(height,width)
    half=np.stack(((packed<<4)&0x7ff0,(packed>>7)&0x7ff0,(packed>>17)&0x7fe0),axis=-1).astype('<u2')
    return half.view('<f2').astype(np.float32)

def read(path):
    return decode(Path(path).read_bytes())

def summarize(values):
    finite=np.isfinite(values);above=np.any(values>1,axis=-1);positive=np.any(values>0,axis=-1)
    return dict(dimensions=[values.shape[1],values.shape[0]],pixels=int(above.size),nonfinite_components=int(np.count_nonzero(~finite)),pixels_above_one=int(np.count_nonzero(above)),positive_pixels=int(np.count_nonzero(positive)),max_component=float(values.max()),excess_component_sum=float(np.maximum(values-1,0).sum(dtype=np.float64)),scope='Decoded packed dominant-prefix weights at captured frame; not prepack float32 values or radiance loss')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('path',type=Path);p.add_argument('--output',type=Path);a=p.parse_args();result=summarize(read(a.path));text=json.dumps(result,indent=2,allow_nan=False)+'\n'
    if a.output:a.output.write_text(text,encoding='utf-8')
    else:print(text)
if __name__=='__main__':main()
