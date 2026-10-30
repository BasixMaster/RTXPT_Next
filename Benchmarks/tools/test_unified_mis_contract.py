import unittest
from unified_mis_contract import validate_request,verify
class Contract(unittest.TestCase):
    def test_valid(self):validate_request(True,False,'pt',None,replay_only=True,reconnection=0)
    def test_boundaries(self):
        for kw in [dict(nee_only=True),dict(mode='dipt'),dict(variant='B10'),dict(b8=True),dict(extended=True),dict(paired=True),dict(roulette=.8),dict(replay_only=False),dict(reconnection=1),dict(queue=True),dict(duplication=True)]:
            a=dict(enabled=True,nee_only=False,mode='pt',variant=None,replay_only=True,reconnection=0);a.update(kw)
            with self.subTest(kw=kw),self.assertRaises(ValueError):validate_request(**a)
    def test_receipts(self):
        line='PT_UNIFIED_MIS enabled=1 primaryOwner=PT indirectOwner=PT standaloneDI=0 standaloneGI=0 localProposals=1 transport=finite-BSDF-NEE-MIS fullPrefix=1 fullPTPP=0'
        self.assertTrue(verify(line,True)['active'])
        self.assertFalse(verify('',False)['active'])
        for log,enabled in [(line,False),('',True),(line.replace('standaloneDI=0','standaloneDI=1'),True),(line.replace('fullPTPP=0','fullPTPP=1'),True)]:
            with self.subTest(log=log),self.assertRaises(ValueError):verify(log,enabled)
if __name__=='__main__':unittest.main()
