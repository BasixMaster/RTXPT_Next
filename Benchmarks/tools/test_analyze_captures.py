"""Synthetic numerical/parser checks only; these are not renderer measurements."""
import csv
import math
import os
import json
from pathlib import Path
import shutil
import uuid
import unittest
from unittest import mock
from types import SimpleNamespace

import numpy as np
from PIL import Image

import analyze_captures as a


class AnalysisChecks(unittest.TestCase):
    def setUp(self):
        self.scratch = Path(os.environ.get('BENCHMARK_TEST_TMP', str(Path.cwd() / 'work/benchmark-tools-tests'))).resolve()
        self.scratch.mkdir(parents=True, exist_ok=True)
        self.root = self.scratch / ('fixture-' + uuid.uuid4().hex)
        self.root.mkdir()

    def tearDown(self):
        if not self.root.resolve().is_relative_to(self.scratch):
            raise RuntimeError('Refusing cleanup outside the owning test scratch directory')
        shutil.rmtree(self.root)

    def csv(self, name, rows):
        path = self.root / name
        with path.open('w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f); writer.writerow(a.HEADER); writer.writerows(rows)
        return path

    def test_window_optional_passes_and_percentiles(self):
        p = self.csv('r.csv', [
            [0, 0, 100, 50, 0, 3, 8, 90, '', 90],
            [1, 4, 100, 50, 0, 3, 8, 1, '', 2],
            [2, 5, 100, 50, 0, 3, 8, 2, '', 4],
            [3, 6, 100, 50, 0, 3, 8, 99, '', 99]])
        r = a.read_perf(p, 4, 6)
        self.assertEqual(r['selected_frames'], 2)
        self.assertEqual(r['logged_stage_sum']['median_ms'], 4.5)
        self.assertAlmostEqual(r['logged_stage_sum']['p95_ms'], 5.85)
        self.assertEqual(r['stages']['compactionMs']['inactive_frames'], 2)
        self.assertIsNone(r['stages']['compactionMs']['statistics'])

    def test_repeated_process_append_is_rejected(self):
        p = self.csv('r.csv', [[1, 4, 100, 50, 0, 3, 8, 1, '', 2],
                                [0, 5, 100, 50, 0, 3, 8, 1, '', 2]])
        with self.assertRaisesRegex(ValueError, 'non-increasing'):
            a.read_perf(p, 4, 6)

    def test_missing_fill_and_nonfinite_are_rejected(self):
        for value in ['', 'nan', '-1']:
            p = self.csv('r.csv', [[0, 4, 100, 50, 0, 3, 8, 1, '', value]])
            with self.assertRaises(ValueError):
                a.read_perf(p, 4, 6)

    def test_mixed_dimensions_and_empty_window_rejected(self):
        p = self.csv('r.csv', [[0, 4, 100, 50, 0, 3, 8, 1, '', 2],
                                [1, 5, 200, 50, 0, 3, 8, 1, '', 2]])
        with self.assertRaisesRegex(ValueError, 'changes dimensions'):
            a.read_perf(p, 4, 6)
        with self.assertRaisesRegex(ValueError, 'no rows'):
            a.read_perf(p, 7, 8)

    def test_group_uses_run_level_not_pooled_median(self):
        p = self.csv('a.csv', [[i, 4 + i / 10, 100, 50, 0, 3, 8, '', '', 1] for i in range(5)])
        q = self.csv('b.csv', [[0, 4, 100, 50, 0, 3, 8, '', '', 9],
                                [1, 5, 100, 50, 0, 3, 8, '', '', 9]])
        g = a.perf_group([p, q], 'synthetic', 4, 6)
        self.assertEqual(g['summary']['median_of_run_medians_ms'], 5)
        self.assertIsNone(g['summary']['run_median_ci95'])
        with self.assertRaisesRegex(ValueError, 'once only'):
            a.perf_group([p, p], 'synthetic', 4, 6)

    def test_compare_scope_and_configuration(self):
        p = self.csv('a.csv', [[0, 4, 100, 50, 0, 3, 8, '', '', 2],
                                [1, 5, 100, 50, 0, 3, 8, '', '', 2]])
        q = self.csv('b.csv', [[0, 4, 100, 50, 0, 3, 8, '', '', 1],
                                [1, 5, 100, 50, 0, 3, 8, '', '', 1]])
        g, h = a.perf_group([p], 'B0', 4, 6), a.perf_group([q], 'B1', 4, 6)
        r = a.compare_groups(g, h)
        self.assertEqual(r['candidate_change_percent'], -50)
        self.assertEqual(r['baseline_over_candidate_ratio'], 2)
        self.assertIn('not whole-renderer', r['ratio_scope'])
        h['window']['scene_end_exclusive'] = 7
        with self.assertRaisesRegex(ValueError, 'different window'):
            a.compare_groups(g, h)

    def test_static_and_reset_scene_times_are_rejected(self):
        p = self.csv('static.csv', [[i, 0, 100, 50, 0, 3, 8, '', '', 1] for i in range(3)])
        with self.assertRaisesRegex(ValueError, 'sceneTime does not advance'):
            a.read_perf(p, 0, 1)
        q = self.csv('reset.csv', [[0, 4, 100, 50, 0, 3, 8, '', '', 1],
                                    [1, 5, 100, 50, 0, 3, 8, '', '', 1],
                                    [2, 4, 100, 50, 0, 3, 8, '', '', 1]])
        with self.assertRaisesRegex(ValueError, 'resets or moves backwards'):
            a.read_perf(q, 4, 6)

    def test_identical_image_and_known_psnr(self):
        black, white = np.zeros((2, 2, 3), np.uint8), np.full((2, 2, 3), 255, np.uint8)
        r = a.image_metrics(black, black)
        self.assertTrue(r['decoded_rgb_exactly_equal'])
        self.assertIsNone(r['psnr_srgb_encoded_rgb_db'])
        self.assertTrue(r['psnr_identical_infinite'])
        r = a.image_metrics(black, white)
        self.assertEqual(r['mse_srgb_encoded_rgb'], 1)
        self.assertEqual(r['psnr_srgb_encoded_rgb_db'], 0)
        self.assertAlmostEqual(r['smape_display_luma100'], 100 / 1.0001)
        self.assertEqual(r['changed_pixels'], 4)

    def test_roi_and_no_resize(self):
        black = np.zeros((2, 2, 3), np.uint8); changed = black.copy(); changed[0, 0] = 255
        mask = np.array([[False, True], [True, True]])
        r = a.image_metrics(black, changed, mask)
        self.assertTrue(r['decoded_rgb_exactly_equal'])
        self.assertEqual(r['selected_pixels'], 3)
        with self.assertRaisesRegex(ValueError, 'identical HxWx3'):
            a.image_metrics(black, changed[:1])
        with self.assertRaisesRegex(ValueError, 'at least one'):
            a.image_metrics(black, changed, np.zeros((2, 2), bool))

    def test_png_relation_and_channel_difference(self):
        ref = np.zeros((1, 1, 3), np.uint8); test = ref.copy(); test[0, 0, 0] = 1
        rp, tp = self.root / 'ref.png', self.root / 'test.png'
        Image.fromarray(ref).save(rp); Image.fromarray(test).save(tp)
        r = a.quality_pair(rp, tp)
        self.assertEqual(r['relation'], 'regression')
        self.assertAlmostEqual(r['metrics']['mse_srgb_encoded_rgb'], 1 / (3 * 255 ** 2))
        self.assertEqual(r['metrics']['max_abs_channel_difference_8bit'], 1)
        self.assertEqual(r['flip']['status'], 'not_requested')
        self.assertIn('not raw linear HDR', r['limitations'][0])

    def test_official_ldr_inactive_hdr_sentinels_serialize(self):
        # Official1.7 API-shaped synthetic metadata fixture, not a performance result.
        params = dict(ppd=67., startExposure=math.inf, stopExposure=math.inf,
                      numExposures=-1, tonemapper='aces')
        active, inactive = a.ldr_flip_parameter_metadata(params)
        self.assertEqual(active, {'ppd': 67.})
        self.assertEqual(inactive['status'], 'not_applicable_to_LDR')
        self.assertEqual(inactive['official_returned_defaults']['startExposure'], '+inf')
        json.dumps(dict(active=active, inactive=inactive), allow_nan=False)
        with self.assertRaisesRegex(ValueError, 'non-finite active parameter'):
            a.ldr_flip_parameter_metadata(dict(ppd=math.inf))

    def test_adapter_fixture_keeps_metric_nonfinite_failures(self):
        ref = np.zeros((2, 2, 3), np.uint8)
        rp, tp = self.root/'ref.png', self.root/'test.png'
        Image.fromarray(ref).save(rp); Image.fromarray(ref).save(tp)
        params = dict(ppd=67., startExposure=math.inf, stopExposure=math.inf,
                      numExposures=-1, tonemapper='aces')
        result = (np.zeros((2, 2), np.float32), 0., params)
        evaluator = SimpleNamespace(evaluate=lambda *args, **kwargs: result)
        with mock.patch.dict('sys.modules', {'flip_evaluator': evaluator}), \
             mock.patch.object(a.importlib.metadata, 'version', return_value='synthetic-API-fixture'):
            value = a.quality_pair(rp, tp, flip=True)
            a.save(self.root/'quality.json', value)
            self.assertEqual(value['flip']['parameters'], {'ppd': 67.})
            self.assertEqual(value['flip']['full_frame_mean'], 0.)
            result = (np.zeros((2, 2), np.float32), math.inf, params)
            with self.assertRaisesRegex(ValueError, 'non-finite mean error'):
                a.quality_pair(rp, tp, flip=True)
            result = (np.full((2, 2), math.inf, np.float32), 0., params)
            with self.assertRaisesRegex(ValueError, 'non-finite scalar map'):
                a.quality_pair(rp, tp, flip=True)


if __name__ == '__main__':
    unittest.main()
