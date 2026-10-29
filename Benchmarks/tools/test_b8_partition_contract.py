import unittest
import numpy as np
from b8_partition_contract import verify, check_stages


class PartitionCaptureTests(unittest.TestCase):
    def test_approximation_requires_matching_effective_receipt(self):
        base = 'B8_PARTITION_CONTRACT development=1 version=1 giReuse=1 component=0 minPTLength=4 stage=1\n'
        approx = 'B8_GI_APPROX_CONTRACT enabled=1 mode=3 directional=0 jacobianClamp=1 finalBlend=1\n'
        self.assertTrue(verify(base+approx, True, 0, 1, 3)['gi_reuse'])
        for log, mode in ((base, 3), (base+approx, 2), (base+approx, None)):
            with self.assertRaises(ValueError): verify(log, True, 0, 1, mode)
        initial = base.replace('giReuse=1', 'giReuse=0') + approx.replace('mode=3', 'mode=0')
        self.assertFalse(verify(initial, True, 0, 1, 0)['gi_reuse'])
    def test_receipts_are_effective_not_requested(self):
        row = 'B8_PARTITION_CONTRACT development=1 version=1 giReuse=0 component=0 minPTLength=4\n'
        self.assertFalse(verify(row, True)['canonical_accepted'])
        for bad in ('', row.replace('giReuse=0', 'giReuse=1'), row + row.replace('version=1', 'version=2')):
            with self.assertRaises(ValueError): verify(bad, True)

    def test_cap_support(self):
        z = np.zeros((2, 2, 3)); d = z + 1; g = d + 2; p = g + 3
        self.assertEqual(check_stages(z, d, g, p, p, 3)['components']['pt_long']['nonzero_pixels'], 4)
        with self.assertRaises(ValueError): check_stages(z, d, g, p, p, 2)
        with self.assertRaises(ValueError): check_stages(z, d, g, g, g, 1)
        check_stages(z, d, d, d, d, 1)

    def test_wrong_frame_or_invalid_radiance(self):
        z = np.zeros((1, 1, 3)); o = z + 1
        with self.assertRaises(ValueError): check_stages(z, o, o, o, z, 3)
        with self.assertRaises(ValueError): check_stages(o, z, o, o, o, 3)
        with self.assertRaises(ValueError): check_stages(z, z, z, z + np.nan, z + np.nan, 3)


if __name__ == '__main__': unittest.main()
