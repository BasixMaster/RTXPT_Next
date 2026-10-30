"""Independent finite-domain GRIS expectation under receiver changes.

The terminal UV coordinates are unchanged; conditional solid-angle density
changes with the receiver. It is already in the PSS integrand, so a second
solid-angle Jacobian is incorrect for this explicit PSS mode.
"""
import unittest
from fractions import Fraction as F
from itertools import product

def enumerate_receiver_shift(m,pss_conversion=True,extra_geometry=False):
    source=[F(7),F(2),F(11)];destination=[F(3),F(13),F(5)]
    p=[F(1,3)]*3;q_source=[F(2),F(3),F(7)];q_destination=[F(4),F(1),F(5)]
    result=F(0)
    for stream in product(range(3),repeat=m):
        probability=F(1)
        for x in stream:probability*=p[x]
        weights=[source[x]/p[x] for x in stream];total=sum(weights)
        for x,w in zip(stream,weights):
            event=probability*w/total
            ucw_path=total/(m*source[x]);ucw_pss=ucw_path*p[x] if pss_conversion else ucw_path
            integrand_pss=destination[x]/p[x]
            jacobian=q_source[x]/q_destination[x] if extra_geometry else F(1)
            result+=event*integrand_pss*ucw_pss*jacobian
    return result

class ReceiverShift(unittest.TestCase):
    def test_ris_pss_shift(self):
        for m in [1,2,3,4]:
            with self.subTest(m=m):self.assertEqual(enumerate_receiver_shift(m),F(21))
    def test_wrong_measures_are_detected(self):
        self.assertEqual(enumerate_receiver_shift(4,pss_conversion=False),F(63))
        self.assertEqual(enumerate_receiver_shift(4,extra_geometry=True),F(95,2))
if __name__=='__main__':unittest.main()
