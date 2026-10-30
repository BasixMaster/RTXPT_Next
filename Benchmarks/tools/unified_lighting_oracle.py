"""Exact finite-domain oracle for PT++ supplement §5 RIS/NEE PSS conversion.

Independent enumerated model, not a renderer implementation. All probabilities
use the same discrete path measure. Includes both NEE and BSDF strategies.
"""
from fractions import Fraction as F
from itertools import product

def enumerate_ris_mis(contribution,nee_pdf,bsdf_pdf,target,candidates):
    f,p,q,t=([F(x) for x in row] for row in (contribution,nee_pdf,bsdf_pdf,target))
    n=len(f)
    if not n or any(len(row)!=n for row in (p,q,t)):raise ValueError('Inconsistent finite domain')
    if not isinstance(candidates,int) or candidates<1 or candidates>4:raise ValueError('Enumerate one through four candidates')
    if sum(p)!=1 or sum(q)!=1 or any(x<0 for row in (f,p,q,t) for x in row):raise ValueError('Invalid probabilities/contributions')
    if any(f[i]>0 and (p[i]+q[i]==0 or (p[i]>0 and t[i]==0)) for i in range(n)):raise ValueError('Proposal/target support does not cover contribution')
    omega=[candidates*p[i]/(candidates*p[i]+q[i]) if p[i]+q[i]>0 else F(0) for i in range(n)]
    nee=F(0);missing_conversion=F(0);selected_pdf=[F(0)]*n;unit_pss=True
    for stream in product(range(n),repeat=candidates):
        probability=F(1)
        for i in stream:probability*=p[i]
        if not probability:continue
        weights=[t[i]/p[i] for i in stream];total=sum(weights)
        if not total:continue
        for i,w in zip(stream,weights):
            if not w:continue
            event=probability*w/total;selected_pdf[i]+=event
            ucw_path=total/(candidates*t[i]);ucw_pss=ucw_path*p[i]
            integrand=omega[i]*f[i]/p[i]
            nee+=event*integrand*ucw_pss
            missing_conversion+=event*integrand*ucw_path
            unit_pss=unit_pss and ucw_pss==1
    bsdf=sum((1-omega[i])*f[i] for i in range(n) if q[i]>0)
    stale_bsdf=sum(q[i]/(p[i]+q[i])*f[i] for i in range(n) if q[i]>0)
    return dict(reference=sum(f),nee=nee,bsdf=bsdf,combined=nee+bsdf,
                missing_pss_conversion=missing_conversion+bsdf,
                stale_single_sample_bsdf_mis=nee+stale_bsdf,
                selected_nee_pdf=selected_pdf,all_selected_pss_ucw_unit=unit_pss,
                scope='Exact finite-domain RIS/MIS/PSS identity only; no hybrid shift, visibility, temporal reuse or GPU claim')
