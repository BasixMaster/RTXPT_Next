import unittest
from paired_pilot_contract import verify,check_counters


class PairedPilotContractTests(unittest.TestCase):
    def test_activation_requires_all_mechanisms(self):
        row='PT_PAIRED_CONTRACT enabled=1 adjacentReciprocal=1 pairOwnedShifts=1 vectorShading=1\n'
        self.assertFalse(verify(row,True)['canonical_accepted'])
        for invalid in ('',row.replace('pairOwnedShifts=1','pairOwnedShifts=0'),row+row.replace('vectorShading=1','vectorShading=0')):
            with self.assertRaises(ValueError):verify(invalid,True)

    def test_partition_of_destination_pixels_and_shared_work_bound(self):
        stats=dict(paired_eligible_pairs=3,paired_fallback_pixels=3,paired_directed_shift_calls=5,
                   paired_vector_output_pixels=9,paired_nonfinite_vectors=0,
                   hybrid_returned_nonfinite_target=0,hybrid_returned_nonfinite_weight_product=0)
        self.assertEqual(check_counters(stats,3,3)['pixels'],9)
        for key,value in [('paired_fallback_pixels',2),('paired_vector_output_pixels',10),
                          ('paired_directed_shift_calls',7),('paired_nonfinite_vectors',1),
                          ('hybrid_returned_nonfinite_target',1)]:
            with self.assertRaises(ValueError):check_counters(dict(stats,**{key:value}),3,3)


if __name__=='__main__':unittest.main()
