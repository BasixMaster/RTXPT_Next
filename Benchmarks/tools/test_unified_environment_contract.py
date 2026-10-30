import unittest
from unified_environment_contract import validate_request,verify
class EnvironmentContract(unittest.TestCase):
    def test_boundaries(self):
        validate_request(True,True,4,True);validate_request(False,False,0,False)
        for args in [(True,False,4,True),(True,True,0,True),(True,True,4,False)]:
            with self.subTest(args=args),self.assertRaises(ValueError):validate_request(*args)
    def test_effective_receipt(self):
        line='PT_UNIFIED_ENV enabled=1 proposal=MIP-descent companion=BSDF-miss target=single-sample-PSS standaloneDI=0 standaloneGI=0 fullPTPP=0\nPT_UNIFIED_ENV_LIGHT frame=9 lightIndex=8 localLights=8'
        self.assertEqual(verify(line,True)['lights_by_frame']['9']['lightIndex'],8)
        self.assertFalse(verify('',False)['active'])
        for log,on in [('',True),(line,False),(line.replace('standaloneGI=0','standaloneGI=1'),True),(line.replace('fullPTPP=0','fullPTPP=1'),True),(line+'\nPT_UNIFIED_ENV_LIGHT frame=9 lightIndex=9 localLights=8',True)]:
            with self.subTest(log=log),self.assertRaises(ValueError):verify(log,on)
if __name__=='__main__':unittest.main()
