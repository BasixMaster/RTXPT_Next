"""Finite-domain oracle for native component-dependent diffuse-bounce truncation.

This is transport algebra, not a renderer benchmark or GPU validation. The last
edge into the light is outside the counted prefix: native RTXPT permits the
emission at the first hit after a scatter crosses its diffuse limit, but does
not continue from that hit or perform another NEE there.
"""
from itertools import product
import math


def polynomial(probabilities, degree):
    if degree < 0:
        raise ValueError('negative diffuse budget')
    coefficients = [1.] + [0.] * degree
    for probability in probabilities:
        if not math.isfinite(probability) or not 0 <= probability <= 1:
            raise ValueError('invalid contribution fraction')
        coefficients = [(coefficients[k] * (1-probability) +
                         (coefficients[k-1] * probability if k else 0.))
                        for k in range(degree+1)]
    return coefficients


def convolve(a, b):
    if len(a) != len(b):
        raise ValueError('different retained budgets')
    return [sum(a[j]*b[k-j] for j in range(k+1)) for k in range(len(a))]


def enumerated_survival(probabilities, degree):
    result = 0.
    for labels in product([0, 1], repeat=len(probabilities)):
        if sum(labels) > degree:
            continue
        result += math.prod(p if label else 1-p for p, label in zip(probabilities, labels))
    return result


def enumerated_component_transport(components, degree):
    """Sum native component estimators on a fixed finite path.

    Each component tuple is (RGB BSDF contribution, charged, proposal_mass).
    Proposal masses cancel the matching native component weights. Keeping them
    explicit detects the incorrect substitution of proposal probabilities for
    RGB contribution fractions.
    """
    result = [0., 0., 0.]
    for path in product(*components):
        if sum(component[1] for component in path) > degree:
            continue
        proposal = math.prod(component[2] for component in path)
        if proposal <= 0:
            raise ValueError('test domain requires positive component support')
        for channel in range(3):
            estimator = math.prod(component[0][channel]/component[2] for component in path)
            result[channel] += proposal * estimator
    return result


def collapsed_component_transport(components, degree):
    result = []
    for channel in range(3):
        totals = [sum(component[0][channel] for component in vertex) for vertex in components]
        fractions = [sum(component[0][channel] for component in vertex if component[1])/total
                     if total else 0. for vertex, total in zip(components, totals)]
        result.append(math.prod(totals) * sum(polynomial(fractions, degree)))
    return result


def native_charged(lobe, roughness, source_vertex):
    return bool((lobe & 0x11 or roughness > .25) and not (lobe & 0x10 and source_vertex & 1))
