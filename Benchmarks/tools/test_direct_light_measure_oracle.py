import math
import unittest

from direct_light_measure_oracle import (AreaCell, Receiver, area_target, compare_area_receivers,
    enumerate_initial_states, initial_expectation, reference_integral, reuse_expectation, validate_domain)


class DirectLightMeasureOracleTests(unittest.TestCase):
    def setUp(self):
        self.A = Receiver((0., 0., 0.), (0., 0., 1.))
        self.B = Receiver((0., 0., -1.), (0., 0., 1.))
        self.one_light = [AreaCell('light', p, (0., 0., -1.), 1., 1., .5)
                          for p in [(-.2, -.3, 2.), (.5, .5, 2.)]]

    def assertRelative(self, actual, expected):
        self.assertLess(abs(actual / expected - 1), 2e-12)

    def test_area_to_solid_angle_and_bsdf_cosine(self):
        record = area_target(AreaCell('unit', (0., 0., 2.), (0., 0., -1.), 2., 3., 1.), self.A)
        self.assertEqual(record['q_area'], .5)
        self.assertEqual(record['q_omega'], 2.)
        self.assertRelative(record['F'], 3. / math.pi)
        self.assertRelative(record['target'], 1.5 / math.pi)

    def test_exact_one_light_reference_forward_inverse_and_counterexample(self):
        for dst, src, expected in [(self.A, self.B, .06876131207823032),
                                    (self.B, self.A, .03305528132162140)]:
            result = compare_area_receivers(self.one_light, dst, src, [.5, .5], [.5, .5])
            self.assertRelative(result['reference'], expected)
            self.assertRelative(result['identity_uv'], expected)
            self.assertGreater(abs(result['literal_relative_difference']), .01)

    def test_mixed_lights_unequal_areas_proposals_and_tree_counts(self):
        cells = self.one_light + [AreaCell('large-bright', (.3, -.4, 3.), (0., 0., -1.), 5., 2., 1.)]
        for dst, src, dp, sp, dm, sm in [
            (self.A, self.B, [.15, .15, .7], [.4, .4, .2], 1, 2),
            (self.B, self.A, [.4, .4, .2], [.15, .15, .7], 2, 1),
            (self.A, self.B, [.1, .2, .7], [.3, .6, .1], 2, 3)]:
            result = compare_area_receivers(cells, dst, src, dp, sp, dm, sm)
            self.assertRelative(result['destination_initial'], result['reference'])
            self.assertRelative(result['source_initial'], result['source_reference'])
            self.assertRelative(result['identity_uv'], result['reference'])
            self.assertEqual(result['destination_M'], dm)
            self.assertEqual(result['source_M'], sm)

    def test_same_receiver_is_identity_even_for_literal_ratio(self):
        result = compare_area_receivers(self.one_light, self.A, self.A, [.2, .8], [.7, .3], 2, 1)
        self.assertRelative(result['identity_uv'], result['reference'])
        self.assertRelative(result['literal_light_pdf_ratio'], result['reference'])

    def test_nonuniform_cell_masses_are_not_ordinary_proposal_probabilities(self):
        targets, mass, proposal = [1., 3.], [.25, .75], [.8, .2]
        states = enumerate_initial_states(targets, mass, proposal, 2)
        self.assertRelative(initial_expectation(states, targets), 2.5)
        self.assertRelative(reference_integral(targets, mass), 2.5)

    def test_environment_proposal_change_fixed_or_versioned_measure(self):
        # Two directional cells with fixed solid-angle masses. Radiance and the
        # importance proposal both change between frames; all proposals retain support.
        omega_mass, fd, fs = [.4, .6], [2., 5.], [1., 3.]
        pd, ps = [.8, .2], [.3, .7]
        reference = reference_integral(fd, omega_mass)
        ad = enumerate_initial_states(fd, omega_mass, pd, 1)
        bs = enumerate_initial_states(fs, omega_mass, ps, 2)
        self.assertRelative(reuse_expectation(fd, fs, ad, bs), reference)

        # If the target absorbs the environment proposal, its base measure is
        # versioned p_frame*dOmega, so the identity-direction derivative is pD/pS.
        td = [f * m / p for f, m, p in zip(fd, omega_mass, pd)]
        ts = [f * m / p for f, m, p in zip(fs, omega_mass, ps)]
        ad = enumerate_initial_states(td, pd, pd, 1)
        bs = enumerate_initial_states(ts, ps, ps, 2)
        correct = reuse_expectation(td, ts, ad, bs, [d / s for d, s in zip(pd, ps)])
        reversed_ratio = reuse_expectation(td, ts, ad, bs, [s / d for d, s in zip(pd, ps)])
        self.assertRelative(correct, reference)
        self.assertGreater(abs(reversed_ratio / reference - 1), .01)

    def test_domain_support_shape_and_bounded_enumeration_rejected(self):
        for args in [([1.], [1.], [0.], 1), ([1.], [1.], [.5], 1),
                     ([1.], [], [1.], 1), ([0.], [1.], [1.], 1),
                     ([1., 2.], [.5, .5], [.5, .5], 13)]:
            with self.assertRaises(ValueError):
                enumerate_initial_states(*args)
        with self.assertRaises(ValueError):
            validate_domain([AreaCell('bad', (0., 0., 1.), (0., 0., -1.), 1., 1., .5)])
        with self.assertRaises(ValueError):
            reuse_expectation([1.], [1.], [], [], [0.])


if __name__ == '__main__':
    unittest.main()
