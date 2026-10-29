"""Independent physical-path catalog and exact counterexamples for B8's plan."""
from fractions import Fraction as Q
from dataclasses import replace
import unittest
from transport_partition_oracle import (
    PhysicalPath, ShortEndpoint, ReconnectionCell, COMPONENTS, ZERO,
    masks, integral, mis_expectation, short_gi_draws, draw_expectation,
    reconnection_reference, reconnection_expectation, exhaustive_partition_cases,
    add, scale,
)


def catalog():
    # Independently labelled physical contributions: emitted x2 is direct(k1),
    # while NEE/scattered emission beyond x2 is k2. Alpha/null hits do not scatter.
    rows = [
        ('visible-emission', 0, (2, 1, 0), False, False, False, 0),
        ('visible-environment', 0, (0, 3, 2), False, False, False, 0),
        ('direct-area', 1, (3, 2, 1), True, True, True, 1),
        ('secondary-emission', 1, (5, 1, 2), True, True, True, 2),
        ('direct-environment', 1, (1, 2, 4), True, True, False, 1),
        ('short-lambert', 2, (4, 3, 2), True, True, True, 2),
        ('short-glossy', 2, (7, 2, 1), True, True, False, 2),
        ('long-lambert', 3, (2, 6, 3), True, True, True, 3),
        ('long-glossy', 4, (3, 1, 7), True, True, False, 4),
        ('delta-primary-fallback', 2, (5, 4, 1), False, False, False, 2),
        ('alpha-null-short', 2, (2, 5, 6), True, True, True, 5),
        ('zero-long', 5, (0, 0, 0), True, True, False, 5),
    ]
    return [PhysicalPath(name, k, Q(i, 78), rgb, d, p, l, raw)
            for i, (name, k, rgb, d, p, l, raw) in enumerate(rows, 1)]


EXPECTED = {'native': tuple(Q(x, 78) for x in (101, 61, 21)),
            'di': tuple(Q(x, 78) for x in (34, 20, 31)),
            'gi': tuple(Q(x, 78) for x in (46, 73, 78)),
            'pt': tuple(Q(x, 78) for x in (43, 57, 87))}


class TransportPartitionTests(unittest.TestCase):
    def test_pointwise_partition_all_56_eligibility_combinations(self):
        cases = list(exhaustive_partition_cases())
        self.assertEqual(len(cases), 56)
        for path in cases:
            weights = masks(path)
            self.assertEqual(set(weights), set(COMPONENTS))
            self.assertEqual(sum(weights.values()), 1)
            self.assertTrue(all(w in [0, 1] for w in weights.values()))

    def test_independent_rgb_integrals_and_component_ownership(self):
        paths = catalog()
        for component, expected in EXPECTED.items():
            self.assertEqual(integral(paths, component), expected)
        self.assertEqual(integral(paths), tuple(Q(x, 78) for x in (224, 211, 217)))
        self.assertEqual(masks(paths[3])['di'], 1)  # emission at x2, not GI
        self.assertEqual(masks(paths[6])['native'], 1)  # glossy short fallback
        self.assertEqual(masks(paths[10])['gi'], 1)  # alpha/null interfaces

    def test_mis_with_unequal_counts_and_nonuniform_proposals(self):
        paths = catalog()
        qn = [Q(i, 78) for i in range(1, 13)]
        qb = list(reversed(qn))
        for component, expected in EXPECTED.items():
            self.assertEqual(mis_expectation(paths, [qn, qb], [4, 2], component), expected)

    def test_single_technique_support_and_zero_integrands(self):
        paths = catalog();qn = [Q(1, 12)] * 12;qb = [Q(1, 11)] * 11 + [Q(0)]
        for component, expected in EXPECTED.items():
            self.assertEqual(mis_expectation(paths, [qn, qb], [1, 3], component), expected)
        with self.assertRaises(ValueError):mis_expectation(paths, [[Q(0)] * 12], [1], 'di')
        unsupported = [Q(0)] + [Q(1, 11)] * 11
        with self.assertRaises(ValueError):mis_expectation(paths, [unsupported], [1], 'native')

    def test_original_gi_suffix_overlap_is_detected(self):
        def broken(path):
            weights = masks(path)
            weights['gi'] = int(path.split_primary and path.scatter_count >= 2)
            return weights
        paths = catalog();q = [Q(1, 12)] * 12
        self.assertNotEqual(mis_expectation(paths, [q], [1], 'gi', broken), EXPECTED['gi'])
        self.assertGreater(sum(broken(paths[7]).values()), 1)

    def test_secondary_emission_and_raw_hit_count_mutants_fail(self):
        def secondary_emission(path):
            out = masks(path)
            if path.name == 'secondary-emission':out['gi'] = 1
            return out
        def raw_hits(path):return masks(replace(path, scatter_count=path.raw_hit_count))
        q = [Q(1, 12)] * 12
        for mutant in [secondary_emission, raw_hits]:
            self.assertNotEqual(mis_expectation(catalog(), [q], [1], 'gi', mutant), EXPECTED['gi'])

    def test_removed_bsdf_counterpart_cannot_keep_old_nee_mis(self):
        paths = catalog();qn = [Q(1, 12)] * 12;qb = [Q(i, 78) for i in range(1, 13)]
        broken = lambda technique, i, alpha: alpha if technique == 0 else Q(0)
        self.assertNotEqual(mis_expectation(paths, [qn, qb], [1, 1], 'gi', mis_transform=broken), EXPECTED['gi'])
        self.assertEqual(mis_expectation(paths, [qn], [1], 'gi'), EXPECTED['gi'])

    def test_ineligible_primary_fallback_is_not_lost(self):
        path = catalog()[9]
        self.assertEqual(masks(path), dict(native=1, di=0, gi=0, pt=0))
        self.assertEqual(masks(replace(path, scatter_count=4, raw_hit_count=4))['native'], 1)


def short_fixture():
    return [ShortEndpoint(Q(1, 6), (Q(1, 2), Q(1, 3), Q(2, 3)),
                          (Q(2, 3), Q(1, 3)), (Q(1, 4), Q(3, 4)),
                          ((3, 2, 1), (0, 4, 2)), True),
            ShortEndpoint(Q(2, 6), (Q(3, 4), Q(1, 2), Q(1, 4)),
                          (Q(2, 3), Q(1, 3)), (Q(2, 5), Q(3, 5)),
                          ((4, 3, 2), (2, 1, 5)), False),
            ShortEndpoint(Q(3, 6), (Q(2, 5), Q(3, 5), Q(4, 5)),
                          (Q(2, 3), Q(1, 3)), (Q(3, 7), Q(4, 7)),
                          ((1, 0, 2), (2, 3, 0)), True)]


class ShortGiInitialTests(unittest.TestCase):
    def setUp(self):self.endpoints = short_fixture();self.q = (Q(1, 2), Q(1, 3), Q(1, 6))

    def test_exact_nested_draws_match_independent_integral(self):
        # Explicit quadrature, without using proposal probabilities or masks().
        direct0 = (Q(1, 6), Q(4, 27), Q(4, 27))
        direct2 = (Q(4, 15), Q(3, 10), Q(8, 15))
        self.expected = add(direct0, direct2)
        draws = short_gi_draws(self.endpoints, self.q)
        self.assertEqual(sum(d.probability for d in draws), 1)
        self.assertEqual(draw_expectation(draws), self.expected)
        self.assertTrue(all(d.contribution == ZERO for d in draws if d.endpoint == 1))

    def test_fixed_outgoing_initial_only_can_include_nonlambertian_secondary(self):
        # This adds the previously native fallback endpoint at its ORIGINAL
        # outgoing direction. It grants no permission to reuse its RGB unchanged.
        endpoints=[replace(e,eligible=True) for e in self.endpoints]
        expected=(Q(19,15),Q(113,135),Q(503,540))
        self.assertEqual(draw_expectation(short_gi_draws(endpoints,self.q)),expected)

    def test_primary_bsdf_and_pdf_each_occur_once(self):
        draws = short_gi_draws(self.endpoints, self.q);expected = draw_expectation(draws)
        mutants = [lambda d: scale(d.contribution, self.q[d.endpoint]),
                   lambda d: scale(d.contribution, 1 / self.q[d.endpoint]),
                   lambda d: tuple(a * b for a, b in zip(d.contribution, self.endpoints[d.endpoint].primary_eval))]
        for transform in mutants:self.assertNotEqual(draw_expectation(draws, transform), expected)

    def test_conditioning_on_success_changes_the_estimator(self):
        draws = short_gi_draws(self.endpoints, self.q);expected = draw_expectation(draws)
        success = sum(d.probability for d in draws if self.endpoints[d.endpoint].eligible)
        conditioned = [replace(d, probability=d.probability/success) for d in draws
                       if self.endpoints[d.endpoint].eligible]
        self.assertNotEqual(draw_expectation(conditioned), expected)

    def test_zero_visibility_draws_retain_probability(self):
        endpoints = list(self.endpoints)
        endpoints[0] = replace(endpoints[0], direct_rgb=((0, 0, 0), (0, 0, 0)))
        draws = short_gi_draws(endpoints, self.q)
        self.assertEqual(len(draws), 6)
        self.assertEqual(sum(d.probability for d in draws), 1)


class ShortGiReconnectionTests(unittest.TestCase):
    def cells(self, directional=False):
        # Collinear geometry: source z0, target z-1; endpoints z1 and z-2.
        # Corresponding geometric derivatives are1/1^2 and1/2^2.
        return [ReconnectionCell(Q(1, 3), Q(1), Q(1, 4), Q(2, 3),
                                 (2, 1, 4), (4, 3, 1) if directional else (2, 1, 4)),
                ReconnectionCell(Q(2, 3), Q(1, 4), Q(1), Q(3, 4),
                                 (1, 3, 2), (2, 1, 5) if directional else (1, 3, 2))]

    def test_unclamped_jacobian_preserves_lambertian_target(self):
        cells = self.cells();q = (Q(1, 5), Q(4, 5))
        self.assertEqual(reconnection_expectation(cells, q), reconnection_reference(cells))
        for q in [(Q(2, 3), Q(1, 3)), (Q(1, 2), Q(1, 2))]:
            self.assertEqual(reconnection_expectation(cells, q), reconnection_reference(cells))

    def test_runtime_style_jacobian_clamp_and_inverse_are_detected(self):
        cells = self.cells();q = (Q(1, 5), Q(4, 5));reference = reconnection_reference(cells)
        for transform in [lambda j: min(Q(3), max(Q(1, 3), j)), lambda j: 1/j, lambda j: Q(1)]:
            self.assertNotEqual(reconnection_expectation(cells, q, jacobian_transform=transform), reference)

    def test_view_dependent_secondary_requires_reevaluation(self):
        cells = self.cells(directional=True);q = (Q(1, 5), Q(4, 5));reference = reconnection_reference(cells)
        self.assertNotEqual(reconnection_expectation(cells, q), reference)
        self.assertEqual(reconnection_expectation(cells, q, reevaluate=True), reference)

    def test_zero_target_support_and_nonuniform_area(self):
        cells = self.cells();cells[0] = replace(cells[0], target_geometry=Q(0))
        self.assertEqual(reconnection_expectation(cells, (Q(3, 4), Q(1, 4))), reconnection_reference(cells))


if __name__ == '__main__':unittest.main()
