"""Exact two-domain oracle for one reciprocal ReSTIR spatial neighbor.

This is a finite-measure derivation, not an HLSL emulator. All source draws and
reservoir-index outcomes are enumerated using rational arithmetic. Pairing and
confidence are fixed independently of the source draws. It neither validates
approximate GPU shift maps nor proves arbitrary sample-dependent history rules.
"""
from dataclasses import dataclass
from fractions import Fraction as Q
from typing import Optional

RGB = tuple[Q, Q, Q]
ZERO: RGB = (Q(0), Q(0), Q(0))


def rgb(*values) -> RGB:
    if len(values) != 3:
        raise ValueError('RGB requires three values')
    return tuple(Q(x) for x in values)


def scale(value: RGB, factor: Q) -> RGB:
    return tuple(x * factor for x in value)


def add(a: RGB, b: RGB) -> RGB:
    return tuple(x + y for x, y in zip(a, b))


def luminance(value: RGB) -> Q:
    # A positive scalar target; exact Rec.709 coefficients sum to one.
    return sum((a * b for a, b in zip(value, (Q(2126, 10000), Q(7152, 10000), Q(722, 10000)))), Q(0))


@dataclass(frozen=True)
class Domain:
    measure: tuple[Q, ...]
    integrand: tuple[RGB, ...]
    pmf: tuple[Q, ...]

    def __post_init__(self):
        if not self.measure or not (len(self.measure) == len(self.integrand) == len(self.pmf)):
            raise ValueError('Domain arrays must have equal nonzero lengths')
        if any(x <= 0 for x in self.measure):
            raise ValueError('Atoms require positive measure')
        if any(x < 0 for x in self.pmf) or sum(self.pmf) != 1:
            raise ValueError('Source PMF must be nonnegative and normalized')
        if any(any(channel < 0 for channel in value) for value in self.integrand):
            raise ValueError('This oracle uses nonnegative RGB transport')
        if any(p == 0 and value != ZERO for p, value in zip(self.pmf, self.integrand)):
            raise ValueError('Canonical source lacks required integrand support')

    @property
    def reference(self) -> RGB:
        result = ZERO
        for value, mass in zip(self.integrand, self.measure):
            result = add(result, scale(value, mass))
        return result

    @property
    def draws(self):
        return tuple((i, p) for i, p in enumerate(self.pmf) if p > 0)

    def target(self, atom: int) -> Q:
        return luminance(self.integrand[atom])

    def weight(self, atom: int) -> Q:
        return self.measure[atom] / self.pmf[atom]


@dataclass(frozen=True)
class PairMap:
    """Pairs are (receiver atom, neighbor atom); a partial bijection is allowed."""
    pairs: tuple[tuple[int, int], ...]

    def __post_init__(self):
        if len({a for a, _ in self.pairs}) != len(self.pairs) or len({b for _, b in self.pairs}) != len(self.pairs):
            raise ValueError('Shift map must be a partial bijection')

    def validate(self, receiver: Domain, neighbor: Domain):
        if any(not 0 <= a < len(receiver.measure) or not 0 <= b < len(neighbor.measure) for a, b in self.pairs):
            raise ValueError('Shift atom outside domain')

    def reverse(self):
        return PairMap(tuple((b, a) for a, b in self.pairs))


@dataclass(frozen=True)
class Outcome:
    source: str
    atom: Optional[int]
    probability: Q
    contribution_weight: Q
    contribution: RGB


@dataclass(frozen=True)
class PairCase:
    outcomes: tuple[Outcome, Outcome]
    vector_shading: RGB
    confidence: Q
    forward_jacobian: Q
    opposite_cached_jacobian: Q

    @property
    def conditional_scalar_mean(self) -> RGB:
        return add(*(scale(out.contribution, out.probability) for out in self.outcomes))


@dataclass(frozen=True)
class ExactExpectation:
    scalar: RGB
    vector: RGB
    reference: RGB
    source_probability_mass: Q
    cases: int


def _divide(numerator: Q, denominator: Q) -> Q:
    return numerator / denominator if denominator > 0 else Q(0)


def pair_case(receiver: Domain, neighbor: Domain, mapping: PairMap,
              receiver_atom: int, neighbor_atom: Optional[int],
              receiver_confidence=Q(1), neighbor_confidence=Q(1),
              neighbor_multiplicity=1, mutation: Optional[str] = None) -> PairCase:
    """Enumerate scalar winners and analytically marginalize the same estimator.

    A multiplicity means repeated use of the SAME neighbor sample as distinct
    techniques: their fixed confidences add. It does not assert independent
    sample generation. A missing neighbor returns the canonical estimator.
    Mutations intentionally violate individual contracts for regression tests.
    """
    mapping.validate(receiver, neighbor)
    ca, cb_base = Q(receiver_confidence), Q(neighbor_confidence)
    if ca <= 0 or cb_base <= 0 or not isinstance(neighbor_multiplicity, int) or neighbor_multiplicity < 1:
        raise ValueError('Confidences and technique multiplicity must be positive')
    cb = cb_base * neighbor_multiplicity if neighbor_atom is not None else Q(0)
    source_to_destination = {b: a for a, b in mapping.pairs}
    inverse_at_canonical = dict(mapping.pairs).get(receiver_atom) if neighbor_atom is not None else None
    shifted_neighbor = source_to_destination.get(neighbor_atom) if neighbor_atom is not None else None
    u = receiver.target(receiver_atom)
    v = neighbor.target(neighbor_atom) if neighbor_atom is not None else Q(0)
    f = receiver.target(shifted_neighbor) if shifted_neighbor is not None else Q(0)
    g = neighbor.target(inverse_at_canonical) if inverse_at_canonical is not None else Q(0)
    # Jacobian is the destination/source MEASURE ratio, not a PMF ratio.
    jb = receiver.measure[shifted_neighbor] / neighbor.measure[neighbor_atom] if shifted_neighbor is not None else Q(0)
    ja = neighbor.measure[inverse_at_canonical] / receiver.measure[receiver_atom] if inverse_at_canonical is not None else Q(0)
    if mutation == 'invert_forward_jacobian' and jb:
        jb = 1 / jb
    wa = receiver.weight(receiver_atom)
    wb = neighbor.weight(neighbor_atom) if neighbor_atom is not None else Q(0)
    a0, a1 = ca * wa * u, cb * wb * jb * f
    if mutation == 'drop_unmapped_canonical' and inverse_at_canonical is None:
        a0 = Q(0)
    total = a0 + a1
    p0, p1 = _divide(a0, total), _divide(a1, total)
    denominator_cb = cb_base if mutation == 'omit_multiplicity_in_normalization' and neighbor_atom is not None else cb
    denominator0 = ca * u + denominator_cb * g * ja
    inverse_target = _divide(v, jb)
    if mutation == 'use_opposite_cached_jacobian':
        # WRONG: ja acts on receiver's unrelated original path, not the
        # inverse image of the shifted neighbor path.
        inverse_target = v * ja
    denominator1 = ca * f + denominator_cb * inverse_target
    # Selected-sample normalization: the same preliminary scalar law is used
    # whether RGB marginalization is enabled or disabled.
    w0 = _divide(total * u, u * denominator0)
    w1 = _divide(total * inverse_target, f * denominator1)
    if mutation == 'divide_by_confidence_again':
        w0 /= ca + cb
        w1 /= ca + cb
    value0 = receiver.integrand[receiver_atom]
    value1 = receiver.integrand[shifted_neighbor] if shifted_neighbor is not None else ZERO
    outcomes = (
        Outcome('canonical', receiver_atom, p0, w0, scale(value0, w0)),
        Outcome('neighbor', shifted_neighbor, p1, w1, scale(value1, w1)),
    )
    # Independently expressed balance weights evaluated at EACH candidate's
    # location. They need not sum to one for a realized pair of different paths.
    m0 = _divide(ca * u, denominator0)
    m1 = _divide(cb * inverse_target, denominator1)
    vector = add(scale(value0, wa * m0), scale(value1, wb * jb * m1))
    if mutation == 'drop_unmapped_canonical' and inverse_at_canonical is None:
        vector = scale(value1, wb * jb * m1)
    if mutation == 'divide_by_confidence_again':
        vector = scale(vector, 1 / (ca + cb))
    if mutation == 'raw_rgb_without_mis':
        vector = add(scale(value0, wa * ca), scale(value1, wb * jb * cb))
    if mutation == 'replace_rgb_with_luminance':
        vector = rgb(luminance(vector), luminance(vector), luminance(vector))
    return PairCase(outcomes, vector, ca + cb, jb, ja)


def enumerate_expectation(receiver: Domain, neighbor: Domain, mapping: PairMap,
                          receiver_confidence=Q(1), neighbor_confidence=Q(1),
                          neighbor_multiplicity=1, neighbor_present=True,
                          mutation: Optional[str] = None) -> ExactExpectation:
    scalar, vector, mass = ZERO, ZERO, Q(0)
    count = 0
    neighbor_draws = neighbor.draws if neighbor_present else ((None, Q(1)),)
    for a, pa in receiver.draws:
        for b, pb in neighbor_draws:
            case = pair_case(receiver, neighbor, mapping, a, b,
                             receiver_confidence, neighbor_confidence,
                             neighbor_multiplicity, mutation)
            probability = pa * pb
            scalar = add(scalar, scale(case.conditional_scalar_mean, probability))
            vector = add(vector, scale(case.vector_shading, probability))
            mass += probability
            count += 1
    return ExactExpectation(scalar, vector, receiver.reference, mass, count)


def conditional_luminance_variance(case: PairCase) -> Q:
    mean = luminance(case.conditional_scalar_mean)
    return sum((out.probability * (luminance(out.contribution) - mean) ** 2 for out in case.outcomes), Q(0))
