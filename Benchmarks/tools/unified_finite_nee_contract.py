"""Explicit scope of the finite-NEE unified initial-tree pilot, not full PT++ MIS."""
import re

def validate_request(enabled,mode,variant,b8=False,extended=False,paired=False,roulette=None,replay_only=False):
    if enabled and (mode!='pt' or variant is not None or b8 or extended or paired or (roulette or 0)!=0 or not replay_only):
        raise ValueError('Unified finite-NEE pilot requires unlabelled PT-only, opaque/nonbinding transport, no B8/extended/pair/roulette adaptation')

def verify(log,enabled):
    matches=re.findall(r'^PT_UNIFIED_FINITE_NEE (.+)$',log,re.M)
    if not enabled:
        if matches:raise ValueError('Unexpected unified finite-NEE activation')
        return dict(requested=False,active=False)
    if not matches:raise ValueError('Missing unified finite-NEE activation receipt')
    expected=dict(enabled='1',primaryOwner='PT',indirectOwner='PT',standaloneDI='0',standaloneGI='0',localProposals='1',transport='NEE-only',fullPaperMIS='0')
    for line in matches:
        actual=dict(re.findall(r'(\w+)=([^\s]+)',line))
        if actual!=expected:raise ValueError('Unified ownership/scope receipt differs')
    return dict(requested=True,active=True,canonical_accepted=False,full_paper_mis=False,transport='finite-local-lights, NEE-only continuous paths',receipt=expected)
