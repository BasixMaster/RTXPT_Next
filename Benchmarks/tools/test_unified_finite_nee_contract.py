import unittest
from unified_finite_nee_contract import validate_request,verify

GOOD='PT_UNIFIED_FINITE_NEE enabled=1 primaryOwner=PT indirectOwner=PT standaloneDI=0 standaloneGI=0 localProposals=1 transport=NEE-only fullPaperMIS=0\n'
class UnifiedFiniteNEEContract(unittest.TestCase):
    def test_initial_pilot_scope(self):
        validate_request(True,'pt',None,replay_only=True);self.assertFalse(verify(GOOD,True)['full_paper_mis'])
    def test_missing_activation(self):
        with self.assertRaises(ValueError):verify('',True)
    def test_no_silent_control_activation(self):
        with self.assertRaises(ValueError):verify(GOOD,False)
        self.assertFalse(verify('',False)['active'])
    def test_false_full_paper_claim(self):
        with self.assertRaises(ValueError):verify(GOOD.replace('fullPaperMIS=0','fullPaperMIS=1'),True)
    def test_double_counted_owners(self):
        for field in ['standaloneDI','standaloneGI']:
            with self.assertRaises(ValueError):verify(GOOD.replace(field+'=0',field+'=1'),True)
    def test_incompatible_modes(self):
        for kwargs in [dict(mode='dipt'),dict(variant='B10'),dict(b8=True),dict(extended=True),dict(paired=True),dict(roulette=.8),dict(replay_only=False)]:
            args=dict(enabled=True,mode='pt',variant=None,replay_only=True);args.update(kwargs)
            with self.assertRaises(ValueError):validate_request(**args)
    def test_uniform_single_light_inverse_probability(self):
        # Exact uniform discrete selection: p=1/N and W=N. The target's
        # source factor cancels W while the estimate retains all N lights.
        from fractions import Fraction as F
        values=[F(7),F(2),F(11)];n=len(values)
        self.assertEqual(sum(F(1,n)*n*x for x in values),sum(values))
        for x in values:self.assertEqual(F(1,n)*(n*x),x)

if __name__=='__main__':unittest.main()
