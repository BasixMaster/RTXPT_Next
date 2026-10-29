"""Exact CPU checks for the proposed B8 integrands, not a GPU implementation.

Finite cell measures, proposal probabilities and RGB contributions are distinct.
The short-GI model deliberately retains ineligible/zero draws with probability
mass rather than conditioning its distribution on successful candidate creation.
"""
from dataclasses import dataclass
from fractions import Fraction as Q
from itertools import product


ZERO = (Q(0), Q(0), Q(0))
COMPONENTS = ('native', 'di', 'gi', 'pt')


def scale(rgb, weight):
    return tuple(Q(c) * weight for c in rgb)


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


@dataclass(frozen=True)
class PhysicalPath:
    name: str
    scatter_count: int
    measure: Q
    rgb: tuple
    di_primary: bool
    split_primary: bool
    lambert_secondary: bool
    raw_hit_count: int

    def __post_init__(self):
        if self.scatter_count < 0 or self.raw_hit_count < self.scatter_count:
            raise ValueError('Accepted scattering count cannot exceed raw hits')
        if self.measure <= 0 or len(self.rgb) != 3 or any(c < 0 for c in self.rgb):
            raise ValueError('Positive cell measure and nonnegative RGB required')


def masks(path):
    """Proposed characteristic functions in physical path space.

    Eligibility belongs to the material/geometry contract, never the sampled
    lobe, visibility outcome, chosen light or reservoir success.
    """
    k = path.scatter_count
    d, p, lambert = path.di_primary, path.split_primary, path.lambert_secondary
    return dict(native=int(k == 0 or (k == 1 and not d) or
                           (k >= 2 and not p) or (k == 2 and p and not lambert)),
                di=int(k == 1 and d), gi=int(k == 2 and p and lambert),
                pt=int(k >= 3 and p))


def integral(paths, component=None):
    value = ZERO
    for path in paths:
        weight = 1 if component is None else masks(path)[component]
        value = add(value, scale(path.rgb, path.measure * weight))
    return value


def validate_proposal(probabilities, size):
    if len(probabilities) != size or any(p < 0 for p in probabilities) or sum(probabilities) != 1:
        raise ValueError('Proposal must be a finite probability distribution')


def mis_expectation(paths, proposals, sample_counts, component, mask_fn=masks,
                    mis_transform=None):
    """Enumerate expectations of independently averaged NEE/BSDF techniques.

    Balance weights use sample count times *probability*, not cell density.
    Each technique's sample average has its own 1/n factor, so its expectation
    is q * contribution/q; summing techniques then integrates their MIS weights.
    mis_transform is only a negative-control hook for deliberately broken MIS.
    """
    if component not in COMPONENTS or len(proposals) != len(sample_counts):
        raise ValueError('Unknown component or technique count mismatch')
    for proposal, count in zip(proposals, sample_counts):
        validate_proposal(proposal, len(paths))
        if count <= 0:
            raise ValueError('Technique counts must be positive')
    value = ZERO
    for i, path in enumerate(paths):
        denominator = sum(n * q[i] for n, q in zip(sample_counts, proposals))
        if not denominator:
            if any(path.rgb):
                raise ValueError('Nonzero integrand lies outside proposal support')
            continue
        for technique, (q, count) in enumerate(zip(proposals, sample_counts)):
            if q[i] == 0:
                continue
            alpha = count * q[i] / denominator
            if mis_transform:
                alpha = mis_transform(technique, i, alpha)
            draw = scale(path.rgb, path.measure * mask_fn(path)[component] * alpha / q[i])
            value = add(value, scale(draw, q[i]))
    return value


@dataclass(frozen=True)
class ShortEndpoint:
    measure: Q
    primary_eval: tuple
    light_measures: tuple
    light_proposal: tuple
    direct_rgb: tuple
    eligible: bool


@dataclass(frozen=True)
class ShortDraw:
    endpoint: int
    light: int
    probability: Q
    contribution: tuple


def short_gi_draws(endpoints, primary_proposal):
    """Enumerate the proposed GI-short initial estimator, including empty draws.

    Any secondary BSDF is allowed for initial-only sampling at its fixed
    outgoing direction, provided direct_rgb/proposals cover its declared domain.
    Later unchanged-radiance reuse needs a separate Lambertian/reevaluation gate.
    primary_eval is f1*cos1 once; direct_rgb is f2*cos2*Le*visibility, excluding
    secondary emission and deeper transport. NEE-only direct_rgb has MIS1.
    """
    validate_proposal(primary_proposal, len(endpoints))
    draws = []
    for i, (endpoint, q1) in enumerate(zip(endpoints, primary_proposal)):
        validate_proposal(endpoint.light_proposal, len(endpoint.direct_rgb))
        if endpoint.measure <= 0 or len(endpoint.light_measures) != len(endpoint.direct_rgb):
            raise ValueError('Invalid primary/light quadrature cells')
        if q1 <= 0 or any(q <= 0 for q in endpoint.light_proposal):
            raise ValueError('Initial oracle requires full proposal support')
        for j, (mu2, q2, radiance) in enumerate(zip(endpoint.light_measures,
                                                  endpoint.light_proposal,
                                                  endpoint.direct_rgb)):
            if mu2 <= 0:
                raise ValueError('Light cell measures must be positive')
            rgb = tuple(Q(f) * Q(light) for f, light in zip(endpoint.primary_eval, radiance))
            weight = endpoint.measure * mu2 / (q1 * q2) if endpoint.eligible else Q(0)
            draws.append(ShortDraw(i, j, q1 * q2, scale(rgb, weight)))
    return draws


def draw_expectation(draws, transform=None):
    value = ZERO
    for draw in draws:
        contribution = draw.contribution if transform is None else transform(draw)
        value = add(value, scale(contribution, draw.probability))
    return value


@dataclass(frozen=True)
class ReconnectionCell:
    area_measure: Q
    source_geometry: Q  # dOmega_source / dArea, strictly positive support
    target_geometry: Q  # dOmega_target / dArea, possibly zero target support
    target_primary_eval: Q
    source_radiance: tuple
    target_radiance: tuple


def reconnection_reference(cells):
    """Independent target-area integral, using target outgoing radiance."""
    value = ZERO
    for cell in cells:
        value = add(value, scale(cell.target_radiance,
                                cell.area_measure * cell.target_geometry * cell.target_primary_eval))
    return value


def reconnection_expectation(cells, source_probabilities, *, reevaluate=False,
                            jacobian_transform=None):
    """Transfer source solid-angle inverse weights to target solid angle.

    J=dOmega_target/dOmega_source=Gtarget/Gsource. The density pushforward is
    q_target=q_source/J, so its inverse weight is J/q_source. Unchanged outgoing
    radiance is valid only when secondary radiance is direction independent.
    """
    validate_proposal(source_probabilities, len(cells))
    value = ZERO
    for cell, probability in zip(cells, source_probabilities):
        if probability <= 0 or cell.area_measure <= 0 or cell.source_geometry <= 0 or cell.target_geometry < 0:
            raise ValueError('Invalid source support or geometric measure')
        source_omega_density = probability / (cell.area_measure * cell.source_geometry)
        jacobian = cell.target_geometry / cell.source_geometry
        if jacobian_transform:
            jacobian = jacobian_transform(jacobian)
        radiance = cell.target_radiance if reevaluate else cell.source_radiance
        contribution = scale(radiance, cell.target_primary_eval * jacobian / source_omega_density)
        value = add(value, scale(contribution, probability))
    return value


def exhaustive_partition_cases():
    for k, d, p, lambert in product(range(7), [False, True], [False, True], [False, True]):
        yield PhysicalPath('enumerated', k, Q(1), (1, 2, 3), d, p, lambert, k + 3)
