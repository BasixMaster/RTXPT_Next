import copy
import unittest
from coverage_matrix import validate


class CoverageMatrixTests(unittest.TestCase):
    def setUp(self):
        self.data=dict(required_scenes=['convergence','kitchen','opaque-room'],variants=['B0','B1','B2','B3'],
            rows=[dict(variant=v,scene=s,status='pending',algorithm='explicit configuration',reason='not measured')
                  for v in ['B0','B1','B2','B3'] for s in ['convergence','kitchen','opaque-room']])

    def test_complete_matrix_is_not_a_rendering_pass_claim(self):
        self.assertEqual(validate(self.data)['rows'],12)

    def test_omitted_or_duplicate_scenes_fail(self):
        for change in ['omit','duplicate']:
            data=copy.deepcopy(self.data)
            if change=='omit':data['rows'].pop()
            else:data['rows'].append(data['rows'][0])
            with self.assertRaises(ValueError):validate(data)

    def test_active_algorithm_and_unsupported_reason_are_required(self):
        for key in ['algorithm','reason']:
            data=copy.deepcopy(self.data);data['rows'][0][key]=''
            with self.assertRaises(ValueError):validate(data)

    def test_measured_without_evidence_fails(self):
        self.data['rows'][0]['status']='measured'
        with self.assertRaises(ValueError):validate(self.data)

    def test_required_scene_cannot_be_removed_from_contract(self):
        self.data['required_scenes'].remove('kitchen')
        self.data['rows']=[row for row in self.data['rows'] if row['scene']!='kitchen']
        with self.assertRaises(ValueError):validate(self.data)
