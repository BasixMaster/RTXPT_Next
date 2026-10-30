import unittest
from experiment_contract import prepare,verify,verify_snapshot
import hashlib,json,uuid,shutil,contextlib
from pathlib import Path


@contextlib.contextmanager
def owned_scratch():
    parent=(Path.cwd()/'work/benchmark-tools-tests').resolve();folder=parent/('canonical-'+uuid.uuid4().hex)
    folder.mkdir(parents=True)
    try:yield folder
    finally:
        if not folder.resolve().is_relative_to(parent):raise RuntimeError('Unsafe fixture cleanup')
        shutil.rmtree(folder)


class CanonicalExperimentTests(unittest.TestCase):
    def test_roadmap_and_sampling_ids_cannot_be_recorded_as_active(self):
        from experiment_contract import VARIANT_IDS
        for version in ['B10.75','B10.50','B10.25']+['B'+str(i) for i in range(11,17)]:
            self.assertIn(version,VARIANT_IDS)
            with self.assertRaises(ValueError):prepare(version,'dipt')
    def test_all_supported_mode_assignments(self):
        for v,mode in [('B1','di'),('B2','digi'),('B3','default'),('B4','di'),('B5','digi'),('B6','pt'),('B7','dipt')]:
            self.assertEqual(prepare(v,mode)['variant'],v)

    def test_b0_defaults_cannot_be_relabelled_as_raw_control(self):
        with self.assertRaises(ValueError):prepare('B0','default')
        self.assertEqual(prepare('B0','default','raw-native-control')['expected_flags'],dict(di=0,gi=0,pt=0))

    def test_wrong_algorithm_and_combined_ptgi_are_rejected(self):
        for v,mode in [('B1','default'),('B2','di'),('B4','digi'),('B6','dipt'),('B7','pt'),('B8','dipt'),('B9','dipt'),('B10','dipt')]:
            with self.assertRaises(ValueError):prepare(v,mode)

    def test_limited_gi_off_pilot_is_not_b9(self):
        with self.assertRaises(ValueError):prepare('B7','dipt',reconnection=1,roulette=.8)
        self.assertEqual(prepare('B7','dipt','limited-ptpp-ablation',1,.8)['variant'],'B7')
        with self.assertRaises(ValueError):prepare('B9','dipt','limited-ptpp-ablation',1,.8)

    def test_effective_mode_receipt_is_required(self):
        req=prepare('B7','dipt');good='TRANSPORT_CONTRACT di=1 gi=0 pt=1 diMode=3 neeMIS=1 maxBounces=3 maxDiffuseBounces=3\n'
        self.assertEqual(verify(good,req)['flags']['di'],1)
        for bad in ['',good.replace('di=1','di=0'),good+good.replace('gi=0','gi=1')]:
            with self.assertRaises(ValueError):verify(bad,req)

    def test_native_build_provenance_must_match_baseline_and_runtime(self):
        req=prepare('B1','di')
        log='TRANSPORT_CONTRACT di=1 gi=0 pt=0 diMode=3 neeMIS=1 maxBounces=14 maxDiffuseBounces=2\n'
        native=f"NATIVE_CONTROLS_CONTRACT revision=2 root={req['expected_base_sha']} runtime={req['expected_runtime_sha']} nee=1\n"
        self.assertEqual(verify(log+native,req)['flags'],dict(di=1,gi=0,pt=0))
        for bad in [log,log+native.replace(req['expected_base_sha'],'f'*40),log+native.replace(req['expected_runtime_sha'],'0'*40)]:
            with self.assertRaises(ValueError):verify(bad,req)

    def test_native_ptpp_arguments_are_rejected_even_if_noop(self):
        for q in [0,1]:
            with self.assertRaises(ValueError):prepare('B4','di',roulette=q)
        with self.assertRaises(ValueError):prepare('B1','di',reconnection=0)

    def test_snapshot_requires_matching_clean_runtime(self):
        req=prepare('B4','di')
        with self.assertRaises(ValueError):verify_snapshot(None,req)
        runtime=dict(checked_out_sha=req['expected_runtime_sha'],recorded_gitlink=req['expected_runtime_sha'],tracked_diff_sha256=hashlib.sha256(b'').hexdigest())
        with owned_scratch() as d:
            p=Path(d)/'snapshot.json'
            def write():p.write_text(json.dumps(dict(submodules={'External/Rtxdi':runtime,'Assets':dict(checked_out_sha=req['expected_assets_sha'],recorded_gitlink=req['expected_assets_sha'],tracked_diff_sha256=hashlib.sha256(b'').hexdigest())})))
            write();verify_snapshot(p,req)
            runtime['tracked_diff_sha256']='changed';write()
            with self.assertRaises(ValueError):verify_snapshot(p,req)
            runtime['tracked_diff_sha256']=hashlib.sha256(b'').hexdigest();runtime['checked_out_sha']='f'*40;write()
            with self.assertRaises(ValueError):verify_snapshot(p,req)


if __name__=='__main__':unittest.main()
