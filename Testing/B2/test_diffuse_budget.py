"""Independent finite-domain checks; no renderer/GPU result is inferred."""
import itertools
import unittest
from diffuse_budget_reference import (polynomial, convolve, enumerated_survival,
    enumerated_component_transport, collapsed_component_transport, native_charged)


class DiffuseBudgetTests(unittest.TestCase):
    def test_dynamic_program_matches_enumeration(self):
        for n in range(7):
            probabilities = [.0, .2, .47, 1., .91, .31][:n]
            for degree in range(n+1):
                self.assertAlmostEqual(sum(polynomial(probabilities, degree)),
                                       enumerated_survival(probabilities, degree), places=13)

    def test_cached_suffix_and_changed_prefix_equal_whole_path(self):
        original = [.1, .8, .3, .95, .6, .2]
        for cut in range(len(original)+1):
            for degree in range(7):
                suffix = polynomial(original[cut:], degree)
                changed_prefix = [1-p for p in original[:cut]]
                composed = convolve(polynomial(changed_prefix, degree), suffix)
                direct = polynomial(changed_prefix+original[cut:], degree)
                for got, expected in zip(composed, direct):
                    self.assertAlmostEqual(got, expected, places=13)

    def test_component_transport_marginalization_is_rgb_not_proposal(self):
        vertices = [
            [((.9,.1,.4), True, .2), ((.1,.9,.6), False, .8)],
            [((.2,.7,.8), True, .75), ((.8,.3,.2), False, .25)],
            [((.6,.5,.1), True, .1), ((.4,.5,.9), False, .9)]]
        for degree in range(4):
            full = enumerated_component_transport(vertices, degree)
            collapsed = collapsed_component_transport(vertices, degree)
            for a,b in zip(full, collapsed):
                self.assertAlmostEqual(a,b,places=13)
        for actual,expected in zip(collapsed_component_transport(vertices[:1],0),[.1,.9,.6]):
            self.assertAlmostEqual(actual,expected,places=13)
        self.assertNotEqual(collapsed_component_transport(vertices[:1],0),[.8,.8,.8])

    def test_native_classification_boundaries(self):
        self.assertTrue(native_charged(0x01,.01,1))
        self.assertFalse(native_charged(0x02,.25,1))
        self.assertTrue(native_charged(0x02,.25001,1))
        self.assertFalse(native_charged(0x10,.8,1))
        self.assertTrue(native_charged(0x10,.8,2))
        self.assertFalse(native_charged(0x04,0.,1))

    def test_final_edge_excluded_from_budget_prefix(self):
        # A final emissive hit is allowed after the crossing scatter. Charging
        # the final edge would incorrectly turn this contribution into zero.
        self.assertEqual(enumerated_survival([0.],0),1.)
        self.assertEqual(enumerated_survival([0.,1.],0),0.)

    def test_truncation_cannot_restore_lost_probability(self):
        for degree in range(4):
            self.assertEqual(sum(polynomial([1.]*5,degree)),0.)
        with self.assertRaises(ValueError):polynomial([float('nan')],2)
        with self.assertRaises(ValueError):convolve([1.],[1.,0.])


if __name__=='__main__':unittest.main()
