import unittest,struct
import numpy as np
from analyze_throughput import decode,summarize
from throughput_contract import verify,validate_request

class ThroughputTests(unittest.TestCase):
    def test_independent_golden_channel_layout(self):
        word=0x3c0 | (0x380<<11) | (0x200<<22)
        a=decode(b'RTXPTTHP'+struct.pack('<4I',1,2,1,4)+struct.pack('<2I',word,0))
        np.testing.assert_array_equal(a,np.array([[[1,.5,2],[0,0,0]]],dtype=np.float32));s=summarize(a);self.assertEqual(s['pixels_above_one'],1);self.assertEqual(s['positive_pixels'],1);self.assertEqual(s['excess_component_sum'],1)
    def test_subnormal_boundaries(self):
        blob=b'RTXPTTHP'+struct.pack('<4I',1,1,1,4)+struct.pack('<I',1|(1<<11)|(1<<22))
        np.testing.assert_array_equal(decode(blob)[0,0],[2**-20,2**-20,2**-19])
    def test_rejects_truncated_or_unknown_layout(self):
        cases=[b'',b'wronghdr'+b'\0'*16,b'RTXPTTHP'+struct.pack('<4I',2,1,1,4)+b'\0'*4,b'RTXPTTHP'+struct.pack('<4I',1,0,1,4),b'RTXPTTHP'+struct.pack('<4I',1,2,2,4)+b'\0'*4]
        for blob in cases:
            with self.assertRaises(ValueError):decode(blob)
    def test_requested_and_default_receipts(self):
        self.assertIsNone(verify(''))
        for mode in [0,1]:self.assertEqual(verify(f'PREFIX_THROUGHPUT_CONTRACT preserveAboveOne={mode} capturePacked=1\n',mode,True)['preserve_above_one'],bool(mode))
    def test_receipt_mismatch_rejected(self):
        for text in ['', 'PREFIX_THROUGHPUT_CONTRACT preserveAboveOne=0 capturePacked=1\n','PREFIX_THROUGHPUT_CONTRACT preserveAboveOne=1 capturePacked=0\n','PREFIX_THROUGHPUT_CONTRACT preserveAboveOne=2 capturePacked=1\n']:
            with self.assertRaises(ValueError):verify(text,1,True)
    def test_requests_cannot_hide_ablation_or_unsupported_capture(self):
        for args in [(1,False,False,None,'B7'),(0,True,False,'di',None),(0,True,True,'reference',None),(2,False,False,None,None)]:
            with self.assertRaises(ValueError):validate_request(*args)
        validate_request(1,True,True,'dipt',None)

if __name__=='__main__':unittest.main()
