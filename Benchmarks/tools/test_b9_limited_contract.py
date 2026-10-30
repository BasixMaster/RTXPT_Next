import unittest
from b9_limited_contract import verify, check_roulette


class B9ContractTests(unittest.TestCase):
    def test_actual_algorithm_and_gi_activation(self):
        row='B9_LIMITED_CONTRACT enabled=1 footprint=1 replaySafe=0 giReuse=1 roulette=0.8\nPT_REPLAY_CONTRACT replayOnly=0 roughnessThreshold=0.1\n'
        self.assertTrue(verify(row,2)['footprint'])
        for bad in ('',row.replace('giReuse=1','giReuse=0'),row.replace('footprint=1','footprint=0'),row.replace('roulette=0.8','roulette=nan')):
            with self.assertRaises(ValueError):verify(bad,2)
        replay=row.replace('footprint=1 replaySafe=0','footprint=0 replaySafe=1').replace('replayOnly=0','replayOnly=1')
        self.assertTrue(verify(replay,3)['full_prefix_replay'])
        with self.assertRaises(ValueError):verify(replay,2)

    def test_b8_original_scene_replay_is_reported_independently_of_b9_stage(self):
        log='B9_LIMITED_CONTRACT enabled=0 footprint=0 replaySafe=0 giReuse=1 roulette=0\nPT_REPLAY_CONTRACT replayOnly=1 roughnessThreshold=1\n'
        result=verify(log,1)
        self.assertTrue(result['full_prefix_replay'])
        self.assertFalse(result['replay_safe_ablation'])

    def test_roulette_only_initial_and_conserves_trials(self):
        stats=dict(roulette_tests=100,roulette_survived=80,roulette_terminated=20,replay_roulette_tests=0)
        self.assertEqual(check_roulette(stats,True)['survivals'],80)
        for field,value in [('replay_roulette_tests',1),('roulette_terminated',21),('roulette_survived',0)]:
            with self.assertRaises(ValueError):check_roulette(dict(stats,**{field:value}),True)
        with self.assertRaises(ValueError):check_roulette(stats,False)
        empty=dict(roulette_tests=0,roulette_survived=0,roulette_terminated=0,replay_roulette_tests=0)
        with self.assertRaises(ValueError):check_roulette(empty,True)
        self.assertEqual(check_roulette(empty,True,allow_empty=True)['tests'],0)
