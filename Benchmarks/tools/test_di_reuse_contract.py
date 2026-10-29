import unittest
from di_reuse_contract import verify

def receipt(mode=3,di=1,gi=0,pt=1):return f'TRANSPORT_CONTRACT di={di} gi={gi} pt={pt} diMode={mode} neeMIS=0 maxBounces=14 maxDiffuseBounces=2\n'

class DIReuseContractTests(unittest.TestCase):
    def test_legacy_without_override(self):self.assertIsNone(verify(''))
    def test_actual_modes(self):
        for mode in range(4):
            actual=verify(receipt(mode),mode,True)
            self.assertEqual(actual['temporal'],mode in [1,3]);self.assertEqual(actual['spatial'],mode in [2,3])
    def test_requested_mode_mismatch(self):
        with self.assertRaises(ValueError):verify(receipt(0),3,True)
    def test_di_off_cannot_be_reported_as_on(self):
        with self.assertRaises(ValueError):verify(receipt(di=0),3,True)
    def test_inactive_mode_is_not_active_reuse(self):
        actual=verify(receipt(di=0,pt=0),3,False)
        self.assertFalse(actual['temporal']);self.assertFalse(actual['spatial'])
    def test_missing_requested_receipt(self):
        with self.assertRaises(ValueError):verify('',3,True)
    def test_invalid(self):
        for value in [-1,4,'oops','3.0']:
            with self.assertRaises(ValueError):verify(receipt(value),3)
        with self.assertRaises(ValueError):verify(receipt(di=2),3)
    def test_conflict(self):
        with self.assertRaises(ValueError):verify(receipt(0)+receipt(3),3)
    def test_identical_repeats(self):self.assertEqual(verify(receipt(2)*2,2)['mode'],2)

if __name__=='__main__':unittest.main()
