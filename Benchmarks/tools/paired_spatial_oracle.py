"""Independent finite-domain prerequisites for PT++ paired spatial reuse.

This is a CPU oracle, not the renderer's B10 implementation. Source reservoirs
are immutable; two directed shifts per pair serve both destination estimates.
"""
from fractions import Fraction as Q
from itertools import product
from dataclasses import dataclass
import math
import random


def luminance(rgb):
    return sum(Q(c) * w for c, w in zip(rgb, (Q(2126,10000), Q(7152,10000), Q(722,10000))))


def scale(rgb, weight): return tuple(Q(c)*weight for c in rgb)
def add(a,b): return tuple(x+y for x,y in zip(a,b))
ZERO = (Q(0),)*3


def pair_candidates(a, b, mass_a, mass_b, weight_a, weight_b, j_ab, j_ba, count_a=1, count_b=1):
    """Two original samples' RGB and scalar pair-MIS candidates at A and B.

    a=(F_A(X_A), F_B(T_AB(X_A))), b=(F_B(X_B), F_A(T_BA(X_B))).
    Jacobians correspond to those *different* paths; they need not be mutual
    reciprocals. mass values are source targets at their original samples.
    """
    if min(weight_a,weight_b,j_ab,j_ba,count_a,count_b) < 0:
        raise ValueError('Negative weights, Jacobians or sample counts')
    aa,ab=a;bb,ba=b
    denom_a=count_a*mass_a+count_b*luminance(ab)*j_ab
    denom_b=count_b*mass_b+count_a*luminance(ba)*j_ba
    # Empty/zero targets produce zero. Each partition term is evaluated in
    # its source domain; omitting the inverse-domain Jacobian changes it.
    own_a=scale(aa,weight_a*count_a*mass_a/denom_a) if denom_a else ZERO
    cross_b=scale(ab,weight_a*j_ab*count_a*mass_a/denom_a) if denom_a else ZERO
    own_b=scale(bb,weight_b*count_b*mass_b/denom_b) if denom_b else ZERO
    cross_a=scale(ba,weight_b*j_ba*count_b*mass_b/denom_b) if denom_b else ZERO
    return (own_a,cross_a),(own_b,cross_b)


def finite_expectation(values_a,values_b,measure_a,measure_b,proposal_a,proposal_b,permutation,counts=(1,1)):
    """Enumerate all two-source draws; W is the initial inverse-PDF weight.

    Oracle scope: a bijective finite path map with full proposal support,
    arbitrary RGB targets, nonuniform cell measures and unequal sample counts.
    """
    n=len(values_a)
    if sorted(permutation)!=list(range(n)) or any(len(x)!=n for x in (values_b,measure_a,measure_b,proposal_a,proposal_b)):
        raise ValueError('Expected matching finite domains and a bijection')
    if any(x<=0 for seq in (measure_a,measure_b,proposal_a,proposal_b) for x in seq) or sum(proposal_a)!=1 or sum(proposal_b)!=1:
        raise ValueError('Positive measures and normalized full-support proposals required')
    inverse=[permutation.index(i) for i in range(n)];result_a=result_b=ZERO
    for ia,ib in product(range(n),repeat=2):
        jab=measure_b[permutation[ia]]/measure_a[ia]
        jba=measure_a[inverse[ib]]/measure_b[ib]
        ca,cb=pair_candidates((values_a[ia],values_b[permutation[ia]]),
            (values_b[ib],values_a[inverse[ib]]),luminance(values_a[ia]),luminance(values_b[ib]),
            measure_a[ia]/proposal_a[ia],measure_b[ib]/proposal_b[ib],jab,jba,*counts)
        probability=proposal_a[ia]*proposal_b[ib]
        result_a=add(result_a,scale(add(*ca),probability))
        result_b=add(result_b,scale(add(*cb),probability))
    return result_a,result_b


def pairing_texture(size,sigma,seed):
    """Independent race-free CPU construction of PT++ section3's link shuffle.

    Two copies of each link ID are shuffled in alternating offset 2x2 blocks.
    Output is an involution of positions. GPU upload/dispatch is separate work.
    """
    if size<2 or size%2 or sigma<.8: raise ValueError('Even texture size and sigma>=0.8 required')
    rng=random.Random(seed);links=[i//2 for i in range(size*size)]
    iterations=math.floor(sigma*sigma/2+1.46/sigma+1.76/sigma**2+.656/sigma**3+.5)
    for step in range(iterations):
        offset=step%2
        for y in range(0,size,2):
            for x in range(0,size,2):
                cells=[((y+offset+dy)%size)*size+(x+offset+dx)%size for dy,dx in product(range(2),repeat=2)]
                values=[links[i] for i in cells];rng.shuffle(values)
                for i,v in zip(cells,values):links[i]=v
    owners={};partners=[None]*len(links)
    for i,link in enumerate(links):
        if link in owners:
            j=owners.pop(link);partners[i]=j;partners[j]=i
        else:owners[link]=i
    assert not owners
    return partners


@dataclass(frozen=True)
class ShiftRequest:
    source: int
    destination: int
    sample_id: int
    replay_required: bool


def compact_replay(requests,capacity):
    """Preserve every logical request, separating cheap shifts from replay.

    An overflow aborts the oracle schedule; it never truncates the estimator.
    No claim about GPU dispatch/barriers or performance follows from this model.
    """
    cheap=tuple(x for x in requests if not x.replay_required)
    replay=tuple(x for x in requests if x.replay_required)
    if len(replay)>capacity:raise OverflowError('Replay queue must not drop transport work')
    return cheap,replay
