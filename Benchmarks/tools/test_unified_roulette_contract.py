import unittest
from unified_roulette_contract import validate_request,verify,check_counters
from unified_mis_contract import validate_request as validate_mis
class UnifiedRoulette(unittest.TestCase):
    def test_request(self):
        validate_request(True,True,4,True,.8)
        validate_mis(True,False,'pt',None,roulette=.8,replay_only=True,reconnection=0,unified_roulette=True,candidates=4)
        for args in [(True,False,4,True,.8),(True,True,0,True,.8),(True,True,4,False,.8),(True,True,4,True,0),(True,True,4,True,1),(True,True,4,True,float('nan'))]:
            with self.subTest(args=args),self.assertRaises(ValueError):validate_request(*args)
    def test_receipt(self):
        line='PT_UNIFIED_ROULETTE enabled=1 survival=0.800000012 initialOnly=1 replayDraws=0 target=survival-free fullPTPP=0'
        self.assertTrue(verify(line,True,.8)['active']);self.assertFalse(verify('',False,0)['active'])
        for log,on in [(line,False),('',True),(line.replace('replayDraws=0','replayDraws=1'),True)]:
            with self.subTest(log=log),self.assertRaises(ValueError):verify(log,on,.8)
    def test_counters(self):
        good=dict(roulette_tests=100,roulette_survived=80,roulette_terminated=20,replay_roulette_tests=0);check_counters(good)
        for key,value in [('replay_roulette_tests',1),('roulette_terminated',0),('roulette_tests',99)]:
            bad=dict(good);bad[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):check_counters(bad)
if __name__=='__main__':unittest.main()
