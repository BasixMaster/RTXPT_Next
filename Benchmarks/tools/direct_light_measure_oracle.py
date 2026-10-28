"""Exact finite-domain oracle for a proposed unified direct-light reservoir.

This is CPU mathematical evidence, not a renderer test. The finite cells define
their own quadrature integral; no Monte Carlo sampling or GPU work is performed.
"""
from dataclasses import dataclass
from itertools import product
import math


@dataclass(frozen=True)
class AreaCell:
    light_id: str
    point: tuple
    normal: tuple
    area: float
    radiance: float
    base_mass: float


@dataclass(frozen=True)
class Receiver:
    point: tuple
    normal: tuple
    albedo: float = 1.0


@dataclass(frozen=True)
class InitialState:
    cell: int
    inverse_weight: float
    M: int
    probability: float


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def area_target(cell, receiver):
    """Return F/qOmega in a light-ID + uniform-UV cell measure.

    The area of a light belongs in qOmega, while base_mass partitions the
    unit UV square of that particular light. Different light IDs each have
    unit base mass; discrete light-selection probabilities belong in proposals.
    """
    if cell.area <= 0 or cell.base_mass <= 0 or cell.radiance < 0 or receiver.albedo < 0:
        raise ValueError('Areas/masses must be positive; radiance/albedo nonnegative')
    d = tuple(b - a for a, b in zip(receiver.point, cell.point))
    distance2 = _dot(d, d)
    if distance2 <= 0:
        raise ValueError('Receiver must differ from light position')
    direction = tuple(x / math.sqrt(distance2) for x in d)
    light_cosine = max(0.0, -_dot(cell.normal, direction))
    receiver_cosine = max(0.0, _dot(receiver.normal, direction))
    if light_cosine == 0:
        return dict(F=0.0, q_area=1.0 / cell.area, q_omega=math.inf, target=0.0)
    q_omega = distance2 / (cell.area * light_cosine)
    F = receiver.albedo * receiver_cosine * cell.radiance / math.pi
    return dict(F=F, q_area=1.0 / cell.area, q_omega=q_omega, target=F / q_omega)


def validate_domain(cells):
    if not cells:
        raise ValueError('At least one quadrature cell is required')
    by_light = {}
    for cell in cells:
        if cell.base_mass <= 0 or not math.isfinite(cell.base_mass):
            raise ValueError('Cell base mass must be finite and positive')
        by_light[cell.light_id] = by_light.get(cell.light_id, 0.0) + cell.base_mass
    if any(not math.isclose(mass, 1.0, abs_tol=1e-12) for mass in by_light.values()):
        raise ValueError('Each light must partition its unit UV domain')


def reference_integral(targets, base_masses):
    if len(targets) != len(base_masses):
        raise ValueError('Target and base-mass shapes differ')
    return math.fsum(t * m for t, m in zip(targets, base_masses))


def enumerate_initial_states(targets, base_masses, proposal_masses, M):
    """Enumerate M-tree RIS reservoirs with their exact selection probabilities.

    proposal_masses are ordinary finite probabilities. Their densities in the
    declared base measure are proposal_mass/base_mass. This distinction catches
    area/light-selection factors being counted twice. Full support is required.
    """
    n = len(targets)
    if n == 0 or len(base_masses) != n or len(proposal_masses) != n:
        raise ValueError('Targets, base masses and proposals must have the same nonzero shape')
    if not isinstance(M, int) or isinstance(M, bool) or M < 1 or n ** M > 4096:
        raise ValueError('M must be a positive integer within the bounded exact domain')
    if any(not math.isfinite(t) or t <= 0 for t in targets):
        raise ValueError('This positive-domain oracle requires finite positive targets')
    if any(not math.isfinite(m) or m <= 0 for m in base_masses):
        raise ValueError('Base masses must be finite and positive')
    if any(not math.isfinite(p) or p <= 0 for p in proposal_masses):
        raise ValueError('Proposal must have full positive support')
    if not math.isclose(math.fsum(proposal_masses), 1.0, abs_tol=1e-12):
        raise ValueError('Proposal probabilities must sum to one')
    states = []
    for draws in product(range(n), repeat=M):
        draw_probability = math.prod(proposal_masses[z] for z in draws)
        weights = [targets[z] * base_masses[z] / proposal_masses[z] for z in draws]
        running_sum = math.fsum(weights)
        for z, weight in zip(draws, weights):
            states.append(InitialState(z, running_sum / (M * targets[z]), M,
                                       draw_probability * weight / running_sum))
    return states


def initial_expectation(states, targets):
    return math.fsum(s.probability * targets[s.cell] * s.inverse_weight for s in states)


def reuse_expectation(destination_targets, source_targets, destination_states, source_states,
                      forward_jacobians=None):
    """Enumerate one runtime-style forward/inverse normalization step.

    forward_jacobians map source->destination. Their reciprocal is used in the
    inverse normalization. Unit Jacobians correspond to fixed light-ID/UV reuse.
    Target/source M remain distinct and enter both combine and MIS normalization.
    """
    n = len(destination_targets)
    if n == 0 or len(source_targets) != n:
        raise ValueError('Source and destination target domains differ')
    jacobians = [1.0] * n if forward_jacobians is None else list(forward_jacobians)
    if len(jacobians) != n or any(not math.isfinite(j) or j <= 0 for j in jacobians):
        raise ValueError('Jacobian must be finite and positive for every domain cell')
    terms = []
    for a in destination_states:
        for b in source_states:
            weights = [destination_targets[a.cell] * a.inverse_weight * a.M,
                       destination_targets[b.cell] * b.inverse_weight * jacobians[b.cell] * b.M]
            weight_sum = math.fsum(weights)
            pair_probability = a.probability * b.probability
            for selected_source, z in enumerate((a.cell, b.cell)):
                target = destination_targets[z]
                inverse_target = source_targets[z] / jacobians[z]
                pi = target if selected_source == 0 else inverse_target
                pi_sum = target * a.M + inverse_target * b.M
                final_inverse_weight = weight_sum * pi / (target * pi_sum)
                terms.append(pair_probability * (weights[selected_source] / weight_sum)
                             * target * final_inverse_weight)
    return math.fsum(terms)


def compare_area_receivers(cells, destination, source, destination_proposal, source_proposal,
                           destination_M=1, source_M=1):
    """Compare declared identity-UV mapping against the literal light-PDF ratio.

    The latter is a deliberate negative control for this proposed *direct* sample
    contract. It is not a finding about existing longer-path GPU measurements.
    """
    validate_domain(cells)
    dst_records = [area_target(cell, destination) for cell in cells]
    src_records = [area_target(cell, source) for cell in cells]
    dst = [r['target'] for r in dst_records]
    src = [r['target'] for r in src_records]
    mass = [cell.base_mass for cell in cells]
    a = enumerate_initial_states(dst, mass, destination_proposal, destination_M)
    b = enumerate_initial_states(src, mass, source_proposal, source_M)
    reference = reference_integral(dst, mass)
    identity = reuse_expectation(dst, src, a, b)
    literal = reuse_expectation(dst, src, a, b,
        [s['q_omega'] / d['q_omega'] for s, d in zip(src_records, dst_records)])
    return dict(reference=reference, destination_initial=initial_expectation(a, dst),
                source_initial=initial_expectation(b, src), source_reference=reference_integral(src, mass),
                identity_uv=identity, literal_light_pdf_ratio=literal,
                destination_M=destination_M, source_M=source_M,
                identity_relative_difference=identity / reference - 1,
                literal_relative_difference=literal / reference - 1,
                destination_records=dst_records, source_records=src_records)
