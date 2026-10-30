"""Explicit finite RIS/PSS contract, separate from the verified M1 control."""
import re

def validate_request(candidates,mis):
    if type(candidates)!=int or candidates<0 or candidates>32 or (candidates>0 and not mis):
        raise ValueError('PSS RIS requires unified MIS and candidate count1..32;0 preserves control')

def verify(log,candidates):
    rows=re.findall(r'^PT_UNIFIED_RIS (.+)$',log,re.M)
    if candidates==0:
        if rows:raise ValueError('Unexpected PSS RIS activation')
        return dict(active=False,candidates=0)
    if not rows:raise ValueError('Missing PSS RIS receipt')
    expected=dict(enabled='1',candidates=str(candidates),source='uniform-local',target='single-sample-PSS',ucw='RIS-times-source',terminalNEEJacobian='1',fullPTPP='0')
    for row in rows:
        if dict(re.findall(r'(\w+)=([^\s]+)',row))!=expected:raise ValueError('PSS RIS receipt differs')
    return dict(active=True,candidates=candidates,full_ptpp=False,canonical_accepted=False,receipt=expected)
