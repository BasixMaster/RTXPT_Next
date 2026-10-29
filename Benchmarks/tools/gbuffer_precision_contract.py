"""Verify the opt-in material precision ablation; legacy receipts remain readable."""
import re

def verify(log,requested=None):
    rows=re.findall(r'^GBUFFER_PRECISION_CONTRACT roundedMaterials=([^\s]+)\s*$',log,re.MULTILINE)
    if not rows and requested is None:return None
    if not rows:raise ValueError('Missing GBuffer precision receipt')
    if len(set(rows))!=1 or rows[0] not in ['0','1']:raise ValueError('Invalid/conflicting GBuffer precision receipts')
    actual=int(rows[0])
    if requested is not None and actual!=requested:raise ValueError('Effective GBuffer precision differs from request')
    return dict(rounded_materials=actual,explicit_override=requested is not None,scope='Half-up after fp16 conversion; not exact/unbiased BSDF reconstruction')


def validate_request(rounded,variant=None):
    if rounded not in [None,0,1]:raise ValueError('GBuffer precision must be0/1 or omitted')
    if rounded==1 and variant is not None:
        raise ValueError('Rounded materials are a separate ablation; do not label them as a canonical default capture')
