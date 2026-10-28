import unittest
import numpy as np
from inspect_pt_reservoirs import inspect


class ReservoirTests(unittest.TestCase):
    def test_tiled_address_and_packed_fields(self):
        words = np.zeros((512, 16), dtype='<u4')
        # Pixel (16, 0) resides in block 1, element 256, not linear element 16.
        words[256, 5] = 0x40000000  # half-precision M=2 in the high 16 bits
        words[256, 11] = 7 | (3 << 8) | (5 << 16)
        words[256, 3] = 0x3f800000  # weight=1
        meta = dict(packed_stride_bytes=64, block_size=16, width=17, height=1,
                    block_row_pitch=512, array_pitch=512,
                    initial_preserved_index=0, temporal_output_index=0, final_index=0)
        result = inspect(words, meta)['final_index']
        self.assertEqual(result['valid'], 1)
        self.assertEqual(result['m_greater_than_one'], 1)
        self.assertEqual(result['max_age_valid'], 7)
        self.assertEqual(result['midpath_reconnection_valid'],1)
        self.assertEqual(result['terminal_reconnection_valid'],0)
        self.assertEqual(result['rc_length_histogram_valid'],{'3':1})
        self.assertEqual(result['path_length_histogram_valid'],{'5':1})
        self.assertEqual(result['mean_m_valid'], 2)
        self.assertEqual(result['valid_with_positive_weight'], 1)
        meta['final_index'] = 1
        with self.assertRaises(ValueError): inspect(words, meta)


if __name__ == '__main__': unittest.main()
