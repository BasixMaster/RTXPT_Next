import unittest
from replay_queue_contract import verify,check_counters

class ReplayQueueContractTests(unittest.TestCase):
    def fixture(self):return dict(queue_oracle_pixels=15,queue_overflow=0,queue_reservoir_mismatches=0,queue_vector_mismatches=0,queue_shift_stride_bytes=104,queue_cache_elements=15,queue_replay_requests=4,queue_cheap_shifts=2)
    def test_legacy_absence(self):self.assertIsNone(verify(''))
    def test_enabled_needs_receipt(self):
        with self.assertRaises(ValueError):verify('',True,True)
    def test_effective_oracle(self):self.assertTrue(verify('PT_QUEUE_CONTRACT enabled=1 shiftStride=104 requestCapacityPerPixel=1 oracle=1 indirect=1',True,True)['oracle'])
    def test_missing_oracle_rejected(self):
        with self.assertRaises(ValueError):verify('PT_QUEUE_CONTRACT enabled=1 shiftStride=104 requestCapacityPerPixel=1 oracle=0 indirect=1',True,True)
    def test_exact_output_gate(self):self.assertEqual(check_counters(self.fixture(),5,3)['compared_pixels'],15)
    def test_each_failure_rejected(self):
        for name,value in dict(queue_oracle_pixels=14,queue_overflow=1,queue_reservoir_mismatches=1,queue_vector_mismatches=1,queue_shift_stride_bytes=64,queue_cache_elements=16,queue_replay_requests=16).items():
            s=self.fixture();s[name]=value
            with self.subTest(field=name),self.assertRaises(ValueError):check_counters(s,5,3)
    def test_empty_queue_still_compares_all_outputs(self):
        s=self.fixture();s['queue_replay_requests']=0;s['queue_cheap_shifts']=0;self.assertEqual(check_counters(s,5,3)['replay_requests'],0)
if __name__=='__main__':unittest.main()
