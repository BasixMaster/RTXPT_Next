import unittest
from gbuffer_precision_contract import verify,validate_request

class GBufferPrecisionContractTests(unittest.TestCase):
    def test_legacy_omitted(self):self.assertIsNone(verify(''))
    def test_records_actual_default(self):
        self.assertEqual(verify('GBUFFER_PRECISION_CONTRACT roundedMaterials=0\n'),dict(rounded_materials=0,explicit_override=False,scope='Half-up after fp16 conversion; not exact/unbiased BSDF reconstruction'))
    def test_explicit_modes(self):
        for mode in [0,1]:self.assertEqual(verify(f'GBUFFER_PRECISION_CONTRACT roundedMaterials={mode}\n',mode)['rounded_materials'],mode)
    def test_missing_or_mismatched(self):
        for text in ['', 'GBUFFER_PRECISION_CONTRACT roundedMaterials=0\n']:
            with self.assertRaises(ValueError):verify(text,1)
    def test_invalid_or_conflicting(self):
        for value in ['2','-1','nan','true','0.0']:
            with self.assertRaises(ValueError):verify('GBUFFER_PRECISION_CONTRACT roundedMaterials='+value+'\n')
        with self.assertRaises(ValueError):verify('GBUFFER_PRECISION_CONTRACT roundedMaterials=0\nGBUFFER_PRECISION_CONTRACT roundedMaterials=1\n')
    def test_canonical_identity_cannot_hide_precision_ablation(self):
        for variant in ['B0','B4','B7']:
            with self.assertRaises(ValueError):validate_request(1,variant)
        for mode in [None,0,1]:validate_request(mode,None)
        validate_request(0,'B4')
        with self.assertRaises(ValueError):validate_request(2)
    def test_repeated_identical(self):self.assertEqual(verify('GBUFFER_PRECISION_CONTRACT roundedMaterials=1\n'*2,1)['rounded_materials'],1)

if __name__=='__main__':unittest.main()
