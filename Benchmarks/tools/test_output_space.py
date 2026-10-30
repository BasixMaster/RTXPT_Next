import unittest,uuid,shutil
from unittest.mock import patch
from types import SimpleNamespace
from pathlib import Path
from output_space import require_space

class OutputSpaceTests(unittest.TestCase):
    def setUp(self):
        self.parent=(Path.cwd()/'work/benchmark-tools-tests').resolve();self.root=self.parent/('space-'+uuid.uuid4().hex);self.root.mkdir(parents=True)
    def tearDown(self):
        if not self.root.resolve().is_relative_to(self.parent):raise RuntimeError('Unsafe test cleanup target')
        shutil.rmtree(self.root)
    def test_low_space_rejects_before_output_creation(self):
        target=self.root/'new'/'cohort'
        with patch('output_space.shutil.disk_usage',return_value=SimpleNamespace(free=9)):
            with self.assertRaises(OSError):require_space(target,10)
        self.assertFalse(target.exists())
    def test_sufficient_space_receipt(self):
        with patch('output_space.shutil.disk_usage',return_value=SimpleNamespace(free=100)):
            self.assertEqual(require_space(Path.cwd(),10)['available_bytes'],100)
    def test_invalid_requirement(self):
        with self.assertRaises(ValueError):require_space(Path.cwd(),0)
if __name__=='__main__':unittest.main()
