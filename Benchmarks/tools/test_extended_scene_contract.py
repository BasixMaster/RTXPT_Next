import unittest
from extended_scene_contract import validate_request,verify

LOG='''PT_EXTENDED_SCENE_CONTRACT development=1 diffuseBudget=2 fullPrefixReplay=1
PT_REPLAY_CONTRACT replayOnly=1 roughnessThreshold=1
TRANSPORT_CONTRACT di=1 gi=0 pt=1 diMode=3 neeMIS=0 maxBounces=14 maxDiffuseBounces=2
'''


class ExtendedSceneContractTests(unittest.TestCase):
    def test_combined_approximate_gi_requires_explicit_requested_mode(self):
        log=LOG.replace('gi=0','gi=1')+'B8_PARTITION_CONTRACT development=1 version=1 giReuse=1 component=0 minPTLength=4 stage=1\n'
        log+='B8_GI_APPROX_CONTRACT enabled=1 mode=3 directional=0 jacobianClamp=1 finalBlend=1\n'
        self.assertTrue(verify(log,True,2,'dipt',True,1,3)['combined_partition'])
        for mode in (None,0,1,2):
            with self.assertRaises(ValueError):verify(log,True,2,'dipt',True,1,mode)
    def test_records_actual_settings_without_promoting(self):
        receipt=verify(LOG,True,2)
        self.assertEqual(receipt['max_bounces'],14)
        self.assertFalse(receipt['canonical_accepted'])

    def test_legacy_runs_do_not_require_new_receipts(self):
        self.assertIsNone(verify('',False,2))

    def test_rejects_wrong_diffuse_budget(self):
        with self.assertRaises(ValueError):verify(LOG,True,3)

    def test_rejects_missing_and_conflicting_contracts(self):
        for log in ['',LOG+LOG.replace('diffuseBudget=2','diffuseBudget=3')]:
            with self.assertRaises(ValueError):verify(log,True,2)

    def test_rejects_midpath_threshold_and_missing_replay(self):
        for log in [LOG.replace('roughnessThreshold=1','roughnessThreshold=0.1'),LOG.replace('replayOnly=1','replayOnly=0')]:
            with self.assertRaises(ValueError):verify(log,True,2)

    def test_rejects_overlapping_gi_or_wrong_transport_budget(self):
        for log in [LOG.replace('gi=0','gi=1'),LOG.replace('maxDiffuseBounces=2','maxDiffuseBounces=3')]:
            with self.assertRaises(ValueError):verify(log,True,2)

    def test_rejects_development_off_receipt(self):
        with self.assertRaises(ValueError):verify(LOG.replace('development=1','development=0'),True,2)

    def test_rejects_actual_di_activation_mismatch(self):
        with self.assertRaises(ValueError):verify(LOG,True,2,'pt')
        self.assertIsNotNone(verify(LOG,True,2,'dipt'))

    def test_request_requires_explicit_replay_and_no_canonical_label(self):
        for args in [(True,'pt',False,None),(True,'default',True,None),(True,'dipt',True,'B7')]:
            with self.assertRaises(ValueError):validate_request(*args)
        validate_request(True,'dipt',True,None)

    def test_combined_development_requires_verified_partition(self):
        combined=LOG.replace('gi=0','gi=1')
        with self.assertRaises(ValueError):verify(combined,True,2,'dipt',True)
        receipt='B8_PARTITION_CONTRACT development=1 version=1 giReuse=0 component=0 minPTLength=4 stage=0\n'
        self.assertTrue(verify(combined+receipt,True,2,'dipt',True)['combined_partition'])
        with self.assertRaises(ValueError):verify(combined+receipt.replace('giReuse=0','giReuse=1'),True,2,'dipt',True)


if __name__=='__main__':unittest.main()
