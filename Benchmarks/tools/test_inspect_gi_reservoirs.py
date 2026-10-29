import unittest
import numpy as np
from inspect_gi_reservoirs import inspect


class GIReservoirTests(unittest.TestCase):
    def setUp(self):
        self.meta = dict(packed_stride_bytes=32, block_size=16, width=17, height=1,
                         mode=3, final_index=1, array_pitch=512, block_row_pitch=512)
        self.words = np.zeros((1024, 8), dtype='<u4')

    def test_tiled_address_and_age(self):
        # Pixel16 lies in the next16x16 block, in final slot1.
        self.words[768, 3] = 7 | (3 << 8)
        self.words[768, 5] = np.array([2.0], '<f4').view('<u4')[0]
        result = inspect(self.words, self.meta)
        self.assertEqual(result['positive_age_valid'], 1)
        self.assertEqual(result['positive_weight'], 1)
        self.assertEqual(result['mean_m_valid'], 7)
        self.words[768, 5] = 0x7f800000
        with self.assertRaises(ValueError): inspect(self.words, self.meta)

    def test_wrong_layout_truncated_and_empty(self):
        self.assertEqual(inspect(self.words, self.meta)['valid'], 0)
        with self.assertRaises(ValueError): inspect(self.words[:700], self.meta)
        with self.assertRaises(ValueError): inspect(self.words[:, :7], self.meta)
        with self.assertRaises(ValueError): inspect(self.words, dict(self.meta, packed_stride_bytes=64))
