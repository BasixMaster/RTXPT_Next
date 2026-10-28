"""Independent exact-measure tests; no GPU, renderer binary or native library."""
from fractions import Fraction as Q
import unittest

from paired_reuse_oracle import (
    Domain, PairMap, ZERO, add, conditional_luminance_variance,
    enumerate_expectation, luminance, pair_case, rgb, scale,
)


def nonuniform_fixture():
    a = Domain((Q(1), Q(2), Q(4)),
               (rgb(9, 1, 0), rgb(0, 5, 1), rgb(1, 0, 7)),
               (Q(1, 2), Q(1, 3), Q(1, 6)))
    b = Domain((Q(3), Q(5), Q(2)),
               (rgb(2, 8, 1), rgb(7, 1, 3), rgb(0, 2, 9)),
               (Q(1, 5), Q(3, 10), Q(1, 2)))
    return a, b, PairMap(((0, 2), (1, 0), (2, 1)))


class ExactPairedReuseTests(unittest.TestCase):
    def assert_correct(self, result):
        self.assertEqual(result.source_probability_mass, 1)
        self.assertEqual(result.scalar, result.reference)
        self.assertEqual(result.vector, result.reference)

    def test_identity_map_exact_integral_for_both_receivers(self):
        a = Domain((Q(1), Q(1)), (rgb(1, 0, 2), rgb(0, 5, 1)), (Q(1, 4), Q(3, 4)))
        b = Domain((Q(1), Q(1)), (rgb(4, 2, 0), rgb(1, 1, 7)), (Q(2, 3), Q(1, 3)))
        mapping = PairMap(((0, 0), (1, 1)))
        self.assert_correct(enumerate_expectation(a, b, mapping))
        self.assert_correct(enumerate_expectation(b, a, mapping.reverse()))

    def test_nonunit_path_dependent_jacobians_and_unequal_confidence(self):
        a, b, mapping = nonuniform_fixture()
        for receiver, neighbor, transform, ca, cb in [(a, b, mapping, Q(2), Q(5, 2)),
                                                      (b, a, mapping.reverse(), Q(5, 2), Q(2))]:
            result = enumerate_expectation(receiver, neighbor, transform, ca, cb)
            self.assertEqual(result.cases, 9)
            self.assert_correct(result)

    def test_conditional_rgb_is_exact_average_over_scalar_winners(self):
        a, b, mapping = nonuniform_fixture()
        for ia, _ in a.draws:
            for ib, _ in b.draws:
                case = pair_case(a, b, mapping, ia, ib, Q(2), Q(5, 2))
                self.assertEqual(sum(out.probability for out in case.outcomes), 1)
                self.assertEqual(case.vector_shading, case.conditional_scalar_mean)
                self.assertEqual(case.confidence, Q(9, 2))

    def test_partial_shift_support_is_covered_by_canonical_sample(self):
        a, b, _ = nonuniform_fixture()
        partial = PairMap(((0, 2), (2, 1)))
        self.assert_correct(enumerate_expectation(a, b, partial, Q(3), Q(7)))
        self.assert_correct(enumerate_expectation(b, a, partial.reverse(), Q(7), Q(3)))
        unmapped = pair_case(a, b, partial, 1, 2, Q(3), Q(7))
        self.assertEqual(unmapped.opposite_cached_jacobian, 0)

    def test_missing_neighbor_is_exact_canonical_estimator(self):
        a, b, mapping = nonuniform_fixture()
        result = enumerate_expectation(a, b, mapping, Q(9), Q(4), neighbor_present=False)
        self.assert_correct(result)
        self.assertEqual(result.cases, 3)
        for atom, _ in a.draws:
            case = pair_case(a, b, mapping, atom, None, Q(9), Q(4))
            self.assertEqual(case.outcomes[0].probability, 1)
            self.assertEqual(case.outcomes[0].contribution_weight, a.weight(atom))
            self.assertEqual(case.confidence, 9)

    def test_zero_targets_and_zero_probability_outside_required_support(self):
        a = Domain((Q(1), Q(2), Q(3)), (ZERO, rgb(2, 1, 0), ZERO), (Q(1, 3), Q(2, 3), Q(0)))
        b = Domain((Q(5), Q(2)), (rgb(0, 7, 1), ZERO), (Q(1, 2), Q(1, 2)))
        mapping = PairMap(((0, 0), (1, 1)))
        self.assert_correct(enumerate_expectation(a, b, mapping, Q(2), Q(5)))
        self.assert_correct(enumerate_expectation(b, a, mapping.reverse(), Q(5), Q(2)))
        empty = pair_case(a, b, mapping, 0, 1)
        self.assertEqual(empty.conditional_scalar_mean, ZERO)
        self.assertEqual(empty.vector_shading, ZERO)

    def test_confidence_accounts_for_correlated_technique_multiplicity_once(self):
        a, b, mapping = nonuniform_fixture()
        result = enumerate_expectation(a, b, mapping, Q(2), Q(5), neighbor_multiplicity=3)
        self.assert_correct(result)
        case = pair_case(a, b, mapping, 0, 0, Q(2), Q(5), 3)
        self.assertEqual(case.confidence, 17)
        self.assertEqual(case.vector_shading, case.conditional_scalar_mean)
        bad = enumerate_expectation(a, b, mapping, Q(2), Q(5), 3,
                                    mutation='omit_multiplicity_in_normalization')
        self.assertNotEqual(bad.scalar, bad.reference)

    def test_wrong_jacobian_and_double_normalization_mutations_are_detected(self):
        a, b, mapping = nonuniform_fixture()
        case = pair_case(a, b, mapping, 0, 0)
        self.assertNotEqual(case.opposite_cached_jacobian, 1 / case.forward_jacobian)
        for fault in ['invert_forward_jacobian', 'use_opposite_cached_jacobian',
                      'divide_by_confidence_again']:
            with self.subTest(fault=fault):
                bad = enumerate_expectation(a, b, mapping, Q(2), Q(5, 2), mutation=fault)
                self.assertNotEqual(bad.scalar, bad.reference)

    def test_removing_canonical_support_is_detected(self):
        a, b, _ = nonuniform_fixture()
        bad = enumerate_expectation(a, b, PairMap(((0, 2), (2, 1))),
                                    mutation='drop_unmapped_canonical')
        self.assertNotEqual(bad.scalar, bad.reference)

    def test_vector_shading_does_not_change_scalar_output_law(self):
        a, b, mapping = nonuniform_fixture()
        for ia, _ in a.draws:
            for ib, _ in b.draws:
                normal = pair_case(a, b, mapping, ia, ib, Q(2), Q(5, 2))
                wrong_rgb = pair_case(a, b, mapping, ia, ib, Q(2), Q(5, 2),
                                      mutation='raw_rgb_without_mis')
                self.assertEqual(normal.outcomes, wrong_rgb.outcomes)
                self.assertEqual(normal.confidence, wrong_rgb.confidence)
        bad = enumerate_expectation(a, b, mapping, Q(2), Q(5, 2), mutation='raw_rgb_without_mis')
        self.assertNotEqual(bad.vector, bad.scalar)
        grayscale = enumerate_expectation(a, b, mapping, mutation='replace_rgb_with_luminance')
        self.assertNotEqual(grayscale.vector, grayscale.reference)

    def test_rgb_marginalization_removes_index_choice_variance_conditionally(self):
        a, b, mapping = nonuniform_fixture()
        case = pair_case(a, b, mapping, 0, 0, Q(2), Q(5, 2))
        self.assertGreater(conditional_luminance_variance(case), 0)
        for channel in range(3):
            mean = case.vector_shading[channel]
            variance = sum(out.probability * (out.contribution[channel] - mean) ** 2 for out in case.outcomes)
            self.assertGreaterEqual(variance, 0)
        # The vector is deterministic after fixing source draws and shifts.
        self.assertEqual(case.vector_shading, case.conditional_scalar_mean)

    def test_total_variance_decomposes_into_source_and_index_noise(self):
        a, b, mapping = nonuniform_fixture()
        mean = a.reference
        scalar_variance = [Q(0)] * 4
        vector_variance = [Q(0)] * 4
        index_variance = [Q(0)] * 4
        mean_components = (*mean, luminance(mean))
        for ia, pa in a.draws:
            for ib, pb in b.draws:
                case = pair_case(a, b, mapping, ia, ib, Q(2), Q(5, 2))
                vector_components = (*case.vector_shading, luminance(case.vector_shading))
                for channel in range(4):
                    vector_variance[channel] += pa * pb * (vector_components[channel] - mean_components[channel]) ** 2
                    for out in case.outcomes:
                        components = (*out.contribution, luminance(out.contribution))
                        scalar_variance[channel] += pa * pb * out.probability * (components[channel] - mean_components[channel]) ** 2
                        index_variance[channel] += pa * pb * out.probability * (components[channel] - vector_components[channel]) ** 2
        for scalar, vector, index in zip(scalar_variance, vector_variance, index_variance):
            self.assertEqual(scalar, vector + index)
            self.assertGreaterEqual(scalar, vector)
        self.assertTrue(any(value > 0 for value in index_variance))

    def test_invalid_density_and_nonbijective_mapping_are_rejected(self):
        with self.assertRaises(ValueError):
            Domain((Q(1),), (rgb(1, 0, 0),), (Q(0),))
        with self.assertRaisesRegex(ValueError, 'Canonical source lacks'):
            Domain((Q(1), Q(1)), (ZERO, rgb(1, 0, 0)), (Q(1), Q(0)))
        with self.assertRaises(ValueError):
            Domain((Q(0),), (rgb(1, 0, 0),), (Q(1),))
        with self.assertRaises(ValueError):
            PairMap(((0, 0), (0, 1)))
        a, b, mapping = nonuniform_fixture()
        for bad in [0, -1, Q(1, 2)]:
            with self.assertRaises(ValueError):
                pair_case(a, b, mapping, 0, 0, neighbor_multiplicity=bad)


if __name__ == '__main__':
    unittest.main()
