from fractions import Fraction as Q
import unittest
from paired_spatial_oracle import finite_expectation, pairing_texture, compact_replay, ShiftRequest, scale, add, ZERO, pair_candidates, luminance


class PairedSpatialTests(unittest.TestCase):
    def test_exact_mean_two_destinations_unequal_measures_and_counts(self):
        a=[(4,1,0),(0,3,2),(1,0,5)];b=[(0,4,1),(3,0,2),(2,1,0)]
        ma=[Q(1,2),Q(1,3),Q(1,6)];mb=[Q(1,5),Q(3,5),Q(1,5)]
        expected_a=expected_b=ZERO
        for rgb,m in zip(a,ma):expected_a=add(expected_a,scale(rgb,m))
        for rgb,m in zip(b,mb):expected_b=add(expected_b,scale(rgb,m))
        for counts in [(1,1),(3,7),(17,2)]:
            for perm in [(0,1,2),(2,0,1)]:
                self.assertEqual(finite_expectation(a,b,ma,mb,[Q(2,5),Q(1,5),Q(2,5)],
                    [Q(1,4),Q(1,2),Q(1,4)],perm,counts),(expected_a,expected_b))

    def test_vector_shading_is_exact_conditional_selection_mean(self):
        ca,_=pair_candidates(((3,0,0),(1,2,3)),((0,4,0),(0,0,5)),
                            luminance((3,0,0)),luminance((0,4,0)),Q(2),Q(3),Q(1,4),Q(3),2,7)
        weights=[luminance(v) for v in ca];total=sum(weights)
        expectation=ZERO
        for v,w in zip(ca,weights):
            probability=w/total
            expectation=add(expectation,scale(scale(v,1/probability),probability))
        self.assertEqual(expectation,add(*ca))
        # Merely shading the first or the highest-weight RGB is not marginalization.
        self.assertNotEqual(ca[0],expectation)

    def test_pairing_is_reciprocal_without_self_links(self):
        for size in (4,6,16):
            for seed in (0,11,47):
                p=pairing_texture(size,2.5,seed)
                self.assertEqual(sorted(p),list(range(size*size)))
                self.assertTrue(all(j!=i and p[j]==i for i,j in enumerate(p)))
        self.assertEqual(pairing_texture(8,3,11),pairing_texture(8,3,11))
        with self.assertRaises(ValueError):pairing_texture(7,2,0)

    def test_queue_never_discards_nonreplay_work_or_overflow(self):
        requests=[ShiftRequest(0,1,10,True),ShiftRequest(1,0,20,False),ShiftRequest(2,3,30,True)]
        cheap,replay=compact_replay(requests,2)
        self.assertEqual(cheap,(requests[1],));self.assertEqual(replay,(requests[0],requests[2]))
        self.assertEqual(set(cheap+replay),set(requests))
        with self.assertRaises(OverflowError):compact_replay(requests,1)


if __name__=='__main__':unittest.main()
