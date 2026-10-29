import unittest
from environment_filter_contract import verify


class EnvironmentFilterContractTests(unittest.TestCase):
    def test_preserves_legacy_without_override(self):
        self.assertIsNone(verify(''))

    def test_records_effective_default_without_relabeling_override(self):
        actual=verify('ENVIRONMENT_FILTER_CONTRACT diffuseMip=2\n')
        self.assertEqual(actual['diffuse_mip'],2)
        self.assertFalse(actual['explicit_override'])

    def test_requires_requested_filter_on_both_tracks(self):
        self.assertEqual(verify('ENVIRONMENT_FILTER_CONTRACT diffuseMip=0\n',0)['diffuse_mip'],0)
        for text in ['', 'ENVIRONMENT_FILTER_CONTRACT diffuseMip=2\n']:
            with self.assertRaises(ValueError):verify(text,0)

    def test_rejects_invalid_or_conflicting_effective_settings(self):
        for value in ['nan','inf','-1','17','oops']:
            with self.assertRaises(ValueError):verify('ENVIRONMENT_FILTER_CONTRACT diffuseMip='+value+'\n',0)
        with self.assertRaises(ValueError):
            verify('ENVIRONMENT_FILTER_CONTRACT diffuseMip=0\nENVIRONMENT_FILTER_CONTRACT diffuseMip=2\n',0)

    def test_accepts_repeated_identical_receipts(self):
        self.assertEqual(verify('ENVIRONMENT_FILTER_CONTRACT diffuseMip=0\n'*2,0)['diffuse_mip'],0)


if __name__=='__main__':unittest.main()
