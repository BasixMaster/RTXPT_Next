"""Independent validation of native/GPU RG32_SINT reciprocal-table payloads."""
import numpy as np
SIZES=(254,230,210)


def validate(data,require_gaussian_scale=True):
    offsets=np.asarray(data,dtype=np.int64)
    if offsets.shape!=(sum(n*n for n in SIZES),2):raise ValueError('Gaussian table extent/stride mismatch')
    reports=[];base=0
    for n in SIZES:
        d=offsets[base:base+n*n];y,x=np.indices((n,n));p=np.stack((x.ravel(),y.ravel()),axis=-1)
        if np.any(np.all(d==0,axis=-1)) or np.any(abs(d)>n//2):raise ValueError('Invalid zero/range Gaussian link')
        partner=(p+d)%n;reverse=d[partner[:,1]*n+partner[:,0]]
        if not np.array_equal(reverse,-d):raise ValueError('Table offsets are not exact reciprocal links')
        # Check conjugation by independent orthogonal matrices, including
        # negative coordinates, tile seams and odd finite-image extents.
        for rotation in (np.eye(2,dtype=np.int64),np.array([[0,-1],[1,0]]),-np.eye(2,dtype=np.int64),np.array([[0,1],[-1,0]])):
            for mirror in (np.eye(2,dtype=np.int64),np.diag([-1,1])):
                matrix=rotation@mirror
                coords=np.array([(a,b) for a in (-511,-n,-1,0,1,n-1,n,513) for b in (-301,-1,0,n-1,n,307)])
                shift=np.array([n-1,17])
                def query(points):
                    transformed=points@matrix.T+shift;cell=transformed%n
                    return (transformed+d[cell[:,1]*n+cell[:,0]]-shift)@matrix
                if not np.array_equal(query(query(coords)),coords):raise ValueError('Frame transform lost reciprocal relation')
        reports.append(dict(size=n,entries=n*n,rms_xy=np.sqrt(np.mean(d*d,axis=0)).tolist(),mean_radius=float(np.mean(np.linalg.norm(d,axis=-1)))))
        if require_gaussian_scale and (not all(14<v<18 for v in reports[-1]['rms_xy']) or not 18<reports[-1]['mean_radius']<22):
            raise ValueError('Pairing offsets do not have the declared Gaussian scale')
        base+=n*n
    return reports


def read(path):
    from pathlib import Path
    raw=Path(path).read_bytes()
    if len(raw)!=sum(n*n for n in SIZES)*8:raise ValueError('Truncated/wrong pairing-table payload')
    return np.frombuffer(raw,dtype='<i4').reshape(-1,2)


if __name__=='__main__':
    import argparse,json,hashlib
    from pathlib import Path
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--binary',type=Path,required=True)
    ap.add_argument('--native-producer',type=Path,help='Optional actual C++ fixture bytes to compare exactly')
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    if args.output.exists():raise SystemExit('Preserve existing evaluation; choose a new output')
    raw=args.binary.read_bytes();reports=validate(read(args.binary))
    if args.native_producer and raw!=args.native_producer.read_bytes():raise SystemExit('GPU/native producer bytes differ')
    args.output.write_text(json.dumps(dict(sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),
        tables=reports,native_identity_verified=bool(args.native_producer)),indent=2)+'\n')
