import unittest
from replay_queue_contract import verify,check_counters,check_sequence

class ReplayQueueContractTests(unittest.TestCase):
    def fixture(self):return dict(queue_oracle_pixels=15,queue_overflow=0,queue_reservoir_mismatches=0,queue_vector_mismatches=0,queue_shift_stride_bytes=104,queue_cache_elements=15,queue_replay_requests=4,queue_cheap_shifts=2)
    def test_legacy_absence(self):self.assertIsNone(verify(''))
    def sequence_fixture(self):return dict(queue_sequence_frames=64,queue_sequence_reservoir_failure=0,queue_sequence_vector_failure=0,queue_sequence_overflow_failure=0)
    def test_history_coverage(self):self.assertEqual(check_sequence(self.sequence_fixture(),64)['frames_compared'],64)
    def test_earlier_failure_survives_clean_final_frame(self):
        for field in ('queue_sequence_reservoir_failure','queue_sequence_vector_failure','queue_sequence_overflow_failure'):
            s=self.sequence_fixture();s.update(self.fixture());s[field]=1
            with self.subTest(field=field),self.assertRaises(ValueError):check_sequence(s,64)
    def test_missing_history_receipt_rejected(self):
        for field in self.sequence_fixture():
            s=self.sequence_fixture();del s[field]
            with self.subTest(field=field),self.assertRaises(ValueError):check_sequence(s,64)
    def test_short_history_rejected(self):
        with self.assertRaises(ValueError):check_sequence(self.sequence_fixture(),65)
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
