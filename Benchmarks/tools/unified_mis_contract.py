"""Restricted finite M1 MIS integration; never a full-PT++ acceptance receipt."""
import re

def validate_request(enabled,nee_only,mode,variant,b8=False,extended=False,paired=False,roulette=None,replay_only=False,reconnection=None,queue=False,duplication=False):
    if enabled and (nee_only or mode!='pt' or variant is not None or b8 or extended or paired or (roulette or 0)!=0 or not replay_only or reconnection!=0 or queue or duplication):
        raise ValueError('Finite unified MIS requires exclusive unlabelled PT, fixed-threshold full-prefix replay, no B8/extended/pair/roulette/queue/duplication')

def verify(log,enabled,candidates=0):
    matches=re.findall(r'^PT_UNIFIED_MIS (.+)$',log,re.M)
    if not enabled:
        if matches:raise ValueError('Unexpected unified MIS activation')
        return dict(requested=False,active=False)
    if not matches:raise ValueError('Missing unified MIS receipt')
    expected=dict(enabled='1',primaryOwner='PT',indirectOwner='PT',standaloneDI='0',standaloneGI='0',localProposals=str(max(1,candidates)),transport='finite-BSDF-NEE-MIS',fullPrefix='1',fullPTPP='0')
    for line in matches:
        if dict(re.findall(r'(\w+)=([^\s]+)',line))!=expected:raise ValueError('Unified MIS receipt differs')
    return dict(requested=True,active=True,canonical_accepted=False,full_ptpp=False,receipt=expected)
