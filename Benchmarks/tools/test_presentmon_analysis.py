"""Synthetic schema/selection/unit checks; not PresentMon or renderer measurements."""
import csv
import os
from pathlib import Path
import shutil
import unittest
import uuid

import presentmon_analysis as p


class PresentMonChecks(unittest.TestCase):
    def setUp(self):
        self.scratch=Path(os.environ.get('BENCHMARK_TEST_TMP',str(Path.cwd()/'work/benchmark-tools-tests'))).resolve()
        self.scratch.mkdir(parents=True,exist_ok=True)
        self.root=self.scratch/('fixture-'+uuid.uuid4().hex);self.root.mkdir()
    def tearDown(self):
        if not self.root.resolve().is_relative_to(self.scratch):raise RuntimeError('Unsafe cleanup target')
        shutil.rmtree(self.root)
    def write(self,name,rows,extra=('FrameType',)):
        file=self.root/name
        fields=['Application','ProcessID','SwapChainAddress','CPUStartTime','CPUFrameTime','GPUBusy','GPUTime','CPUWait','DisplayedTime']+list(extra)
        with file.open('w',newline='',encoding='utf-8')as f:
            w=csv.DictWriter(f,fields);w.writeheader();w.writerows(rows)
        return file
    def rows(self,n=8,frame_type=True):
        return [dict(Application='Rtxpt.exe',ProcessID='50',SwapChainAddress='0xabc',CPUStartTime=str(i*10),CPUFrameTime=str(i+1),GPUBusy='2',GPUTime='5',CPUWait='1',DisplayedTime='NA',**({'FrameType':'NotSet'} if frame_type else {}))for i in range(n)]
    def test_window_and_metric_scopes(self):
        file=self.write('p.csv',self.rows())
        r=p.read_presentmon(file,'rtxpt.exe',3,2)
        self.assertEqual(r['selection']['selected_first_cpu_start'],'30')
        self.assertEqual(r['selection']['selected_last_cpu_start'],'50')
        self.assertEqual(r['metrics']['CPUFrameTime']['statistics']['median_ms'],5)
        self.assertEqual(r['metrics']['GPUBusy']['statistics']['median_ms'],2)
        self.assertEqual(r['metrics']['GPUTime']['statistics']['median_ms'],5)
        self.assertEqual(r['metrics']['DisplayedTime']['status'],'unavailable')
    def test_generated_frame_filter_and_missing_field(self):
        rows=self.rows();rows[-1]['FrameType']='Generated'
        r=p.read_presentmon(self.write('p.csv',rows),'rtxpt.exe',2,1)
        self.assertEqual(r['selection']['excluded_frame_type_frames'],1)
        self.assertEqual(r['selection']['selected_last_cpu_start'],'50')
        r=p.read_presentmon(self.write('q.csv',self.rows(frame_type=False),extra=()),'rtxpt.exe',2,1)
        self.assertFalse(r['selection']['frame_type_column_present'])
    def test_multiple_process_or_swapchain_requires_filter(self):
        rows=self.rows();rows[-1]['ProcessID']='51'
        f=self.write('p.csv',rows)
        with self.assertRaisesRegex(ValueError,'multiple matching process'):p.read_presentmon(f,'rtxpt.exe',2,1)
        self.assertEqual(p.read_presentmon(f,'rtxpt.exe',2,1,process_id=50)['identity']['process_id'],'50')
        rows=self.rows();rows[-1]['SwapChainAddress']='0xdef'
        f=self.write('q.csv',rows)
        with self.assertRaisesRegex(ValueError,'multiple matching swapchains'):p.read_presentmon(f,'rtxpt.exe',2,1)
    def test_insufficient_rows_and_invalid_timing(self):
        f=self.write('p.csv',self.rows())
        with self.assertRaisesRegex(ValueError,'need 9'):p.read_presentmon(f,'rtxpt.exe',8,1)
        rows=self.rows();rows[4]['GPUBusy']='nan'
        f=self.write('q.csv',rows)
        with self.assertRaisesRegex(ValueError,'non-finite'):p.read_presentmon(f,'rtxpt.exe',3,2)
    def test_group_comparison_is_metric_specific(self):
        b=p.presentmon_group([self.write('b.csv',self.rows())],'B0','rtxpt.exe',3,2)
        rows=self.rows()
        for r in rows:r['GPUBusy']='1'
        c=p.presentmon_group([self.write('c.csv',rows)],'B1','rtxpt.exe',3,2)
        result=p.compare_presentmon(b,c)
        self.assertEqual(result['comparisons']['GPUBusy']['candidate_change_percent'],-50)
        self.assertEqual(result['comparisons']['GPUTime']['candidate_change_percent'],0)
        self.assertEqual(result['comparisons']['DisplayedTime']['status'],'unavailable')
        c['present_configuration']['SyncInterval']=['1']
        with self.assertRaisesRegex(ValueError,'presentation configuration differs'):
            p.compare_presentmon(b,c)
    def test_frame_time_alias(self):
        f=self.write('p.csv',self.rows())
        f.write_text(f.read_text(encoding='utf-8').replace('CPUFrameTime','FrameTime'),encoding='utf-8')
        self.assertEqual(p.read_presentmon(f,'rtxpt.exe',3,2)['metrics']['CPUFrameTime']['source_column'],'FrameTime')


if __name__=='__main__':unittest.main()
