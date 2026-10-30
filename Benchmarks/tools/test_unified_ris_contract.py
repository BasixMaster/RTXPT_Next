import unittest
from unified_ris_contract import validate_request,verify
from unified_mis_contract import verify as verify_mis
class RISContract(unittest.TestCase):
    def test_bounds(self):
        for m in [0,1,2,4,32]:validate_request(m,True)
        validate_request(0,False)
        for m,enabled in [(-1,True),(33,True),(True,True),(1,False),(4,False)]:
            with self.subTest(m=m),self.assertRaises(ValueError):validate_request(m,enabled)
    def test_receipt(self):
        line='PT_UNIFIED_RIS enabled=1 candidates=4 source=uniform-local target=single-sample-PSS ucw=RIS-times-source terminalNEEJacobian=1 fullPTPP=0'
        self.assertTrue(verify(line,4)['active']);self.assertFalse(verify('',0)['active'])
        for log,m in [('',4),(line,0),(line,1),(line.replace('ucw=RIS-times-source','ucw=RIS-only'),4),(line.replace('fullPTPP=0','fullPTPP=1'),4)]:
            with self.subTest(log=log),self.assertRaises(ValueError):verify(log,m)
    def test_effective_candidate_count(self):
        line='PT_UNIFIED_MIS enabled=1 primaryOwner=PT indirectOwner=PT standaloneDI=0 standaloneGI=0 localProposals=4 transport=finite-BSDF-NEE-MIS fullPrefix=1 fullPTPP=0'
        self.assertTrue(verify_mis(line,True,4)['active'])
        with self.assertRaises(ValueError):verify_mis(line,True)
if __name__=='__main__':unittest.main()
