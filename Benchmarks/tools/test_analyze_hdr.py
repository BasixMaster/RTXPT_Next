import os
import uuid
from contextlib import contextmanager
import unittest
from pathlib import Path
import numpy as np
from analyze_hdr import compare, read_pfm


@contextmanager
def fixture_directory():
    scratch = Path(os.environ.get('BENCHMARK_TEST_TMP', str(Path.cwd()/'work/benchmark-tools-tests'))).resolve()
    directory = scratch/('hdr-'+uuid.uuid4().hex)
    directory.mkdir(parents=True)
    try:
        yield directory
    finally:
        if not directory.resolve().is_relative_to(scratch):
            raise RuntimeError('Unsafe fixture cleanup target')
        for child in directory.iterdir(): child.unlink()
        directory.rmdir()


class HDRTests(unittest.TestCase):
    def test_pfm_endian_orientation_scale(self):
        expected = np.arange(12, dtype=np.float64).reshape(2, 2, 3)
        with fixture_directory() as tmp:
            for dtype, scale in [('<f4', -2), ('>f4', 2)]:
                path = Path(tmp)/'sample.pfm'
                path.write_bytes(f'PF\n2 2\n{scale}\n'.encode() + (expected[::-1]/2).astype(dtype).tobytes())
                np.testing.assert_array_equal(read_pfm(path), expected)
                path.write_bytes(path.read_bytes()[:-1])
                with self.assertRaises(ValueError): read_pfm(path)

    def test_known_metric_values(self):
        ref = np.ones((2, 2, 3))
        value = compare(ref, ref*2)
        self.assertAlmostEqual(value['linear_rgb_mse'], 1)
        self.assertAlmostEqual(value['mape_rgb_ydenom'], 1/1.01)
        self.assertAlmostEqual(value['relmse_project'], 1/1.0001)
        self.assertAlmostEqual(value['smape_cgns_y100'], 100/3.0001)
        self.assertEqual(compare(ref, ref)['linear_rgb_mse'], 0)

    def test_black_and_invalid(self):
        black = np.zeros((1, 1, 3))
        self.assertIsNone(compare(black, black)['relmse_project'])
        for bad in [np.full_like(black, np.nan), np.full_like(black, -1)]:
            with self.assertRaises(ValueError): compare(black, bad)
        with self.assertRaises(ValueError): compare(black, np.zeros((2, 1, 3)))


if __name__ == '__main__': unittest.main()
