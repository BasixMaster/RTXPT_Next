import unittest
import numpy as np
from duplication_contract import count_reference,ids_from_packed,check_gpu,verify

class DuplicationTests(unittest.TestCase):
    def test_empty_ids_and_single_pixel(self):
        self.assertEqual(int(count_reference([[7]])[0,0]),0)
        self.assertFalse(count_reference(np.zeros((19,21),dtype=np.uint32)).any())
    def test_count_window_and_saturation(self):
        a=count_reference(np.ones((19,21),dtype=np.uint32))
        self.assertEqual(int(a[0,0]),80)
        self.assertEqual(int(a[9,10]),255)
    def test_odd_thin_edges_and_distinct_ids(self):
        np.testing.assert_array_equal(count_reference([[4]*11]),[[8,9,10,10,10,10,10,10,10,9,8]])
        self.assertFalse(count_reference(np.arange(1,24).reshape(1,23)).any())
    def fixture(self):
        meta=dict(packed_stride_bytes=64,block_size=16,width=3,height=2,block_row_pitch=256,array_pitch=256,final_index=1)
        words=np.zeros((512,16),dtype='<u4');idx=[256,257,258,272,273,274]
        words[idx,3]=np.float32(1).view('u4');words[idx,15]=7;words[258,3]=0
        stats=dict(duplication_produced_pixels=6,duplication_map_reads=5,duplication_nonzero_reads=4,duplication_max_read_count=3)
        return words,meta,stats
    def test_final_slot_blocked_addressing_and_empty_weight(self):
        words,meta,_=self.fixture();np.testing.assert_array_equal(ids_from_packed(words,meta),[[7,7,0],[7,7,7]])
    def test_exact_map_and_consumer_gate(self):
        words,meta,stats=self.fixture();counts=np.array([[4,4,0],[4,4,4]])
        self.assertTrue(check_gpu(words,meta,counts,stats,True)['exact_count_match'])
        bad=counts.copy();bad[0,0]+=1
        with self.assertRaises(ValueError):check_gpu(words,meta,bad,stats)
        for key in ['duplication_produced_pixels','duplication_map_reads','duplication_nonzero_reads']:
            s=stats.copy();s[key]=0
            with self.subTest(key=key),self.assertRaises(ValueError):check_gpu(words,meta,counts,s,True)
    def test_activation_mismatch_rejected(self):
        receipt='PT_DUPLICATION_CONTRACT enabled=1 radius=8 maxCount=255 previousFrame=1 strength=0.500000 biased=1'
        self.assertTrue(verify(receipt,True)['deliberately_biased'])
        with self.assertRaises(ValueError):verify(receipt,False)
        with self.assertRaises(ValueError):verify('',True)
if __name__=='__main__':unittest.main()
