"""Geometry-derived expected coordinates, rather than a second U-formula copy."""
import unittest
from dual_motion_oracle import Camera, Track, project, proposals_from_geometry, dual_coordinate


class DualMotionGeometryTests(unittest.TestCase):
    def setUp(self):
        self.camera = Camera()

    def check_geometry(self, background, occluder, expected_history_world,
                       expected_pixel, previous=None, current=None):
        previous = previous or self.camera;current = current or self.camera
        # Expected world points are explicitly constructed on the previous
        # background plane; their expected projected pixels are fixed literals.
        self.assertEqual(project(expected_history_world, previous), expected_pixel)
        result = proposals_from_geometry(background, occluder, previous, current)
        self.assertEqual(result.policy, 'dual_available')
        for a, b in zip(result.dual, expected_pixel):self.assertAlmostEqual(a, b, places=10)
        return result

    def test_projection_pixel_centers_and_depth_parallax(self):
        self.assertEqual(project((0, 0, 10), self.camera), (50.5, 40.5))
        self.assertEqual(project((2, 0, 10), self.camera), (60.5, 40.5))
        self.assertEqual(project((2, 0, 5), self.camera), (70.5, 40.5))
        self.assertEqual(project((0, 2, 10), self.camera), (50.5, 30.5))

    def test_moving_foreground_static_background(self):
        # Foreground moves two world units at depth5: twenty pixels.
        # The old visible background point four units left at depth10 is30.5.
        self.check_geometry(Track((0,0,10),(0,0,10)), Track((0,0,5),(2,0,5)),
                            (-4,0,10), (30.5,40.5))

    def test_uniform_rigid_motion_reduces_to_ordinary_in_orthographic_view(self):
        # Orthographic projection gives both depths the same screen velocity.
        camera=Camera(focal=10, orthographic=True)
        result=self.check_geometry(Track((0,0,10),(2,0,10)), Track((0,0,5),(2,0,5)),
                                   (0,0,10), (50.5,40.5), camera, camera)
        self.assertEqual(result.dual,result.ordinary)

    def test_uniform_world_translation_does_not_erase_perspective_parallax(self):
        # Same rigid world displacement is NOT generally equal projected motion.
        result=self.check_geometry(Track((0,0,10),(2,0,10)), Track((0,0,5),(2,0,5)),
                                   (-2,0,10), (40.5,40.5))
        self.assertNotEqual(result.dual,result.ordinary)

    def test_static_occluder_independently_moving_background(self):
        result=self.check_geometry(Track((-2,0,10),(0,0,10)), Track((-1,0,5),(-1,0,5)),
                                   (0,0,10), (50.5,40.5))
        self.assertEqual(result.dual,result.current)
        self.assertNotEqual(result.dual,result.ordinary)

    def test_independent_foreground_and_background_velocities(self):
        self.check_geometry(Track((-2,0,10),(0,0,10)), Track((-1,0,5),(1,0,5)),
                            (-4,0,10), (30.5,40.5))

    def test_camera_only_translation_has_depth_dependent_flow(self):
        self.check_geometry(Track((0,0,10),(0,0,10)), Track((0,0,5),(0,0,5)),
                            (2,0,10), (60.5,40.5), self.camera, Camera(origin=(2,0,0)))

    def test_vertical_foreground_motion_obeys_y_down_convention(self):
        self.check_geometry(Track((0,0,10),(0,0,10)), Track((0,0,5),(0,2,5)),
                            (0,-4,10), (50.5,60.5))

    def test_wrong_negative_current_motion_and_zero_motion_are_falsified(self):
        fixtures=[(Track((0,0,10),(0,0,10)),Track((0,0,5),(2,0,5)),self.camera,(30.5,40.5)),
                  (Track((0,0,10),(0,0,10)),Track((0,0,5),(0,0,5)),Camera(origin=(2,0,0)),(60.5,40.5)),
                  (Track((-2,0,10),(0,0,10)),Track((-1,0,5),(1,0,5)),self.camera,(30.5,40.5))]
        for background,occluder,current,expected in fixtures:
            result=proposals_from_geometry(background,occluder,self.camera,current)
            self.assertEqual(result.dual,expected)
            zero_motion=result.current
            # Wrong model: negate the background's ordinary backward motion.
            negative_current=tuple(2*result.current[i]-result.ordinary[i] for i in range(2))
            self.assertNotEqual(zero_motion,expected)
            self.assertNotEqual(negative_current,expected)

    def test_finite_domain_625_independent_motion_configurations(self):
        # Two independently translating planes, foreground depth5/background10.
        # A one-unit foreground shift spans two background-plane world units.
        # These literal projection tables come from that ray/plane geometry;
        # they do not use the alternate-correspondence formula under test.
        expected_x={-2:70.5,-1:60.5,0:50.5,1:40.5,2:30.5}
        expected_y={-2:20.5,-1:30.5,0:40.5,1:50.5,2:60.5}
        rejected_zero=rejected_negative_current=cases=0
        for bx in range(-2,3):
            for by in range(-2,3):
                background=Track((-bx,-by,10),(0,0,10))
                for ox in range(-2,3):
                    for oy in range(-2,3):
                        occluder=Track((-bx*.5,-by*.5,5),(-bx*.5+ox,-by*.5+oy,5))
                        result=proposals_from_geometry(background,occluder,self.camera,self.camera)
                        expected=(expected_x[ox],expected_y[oy])
                        self.assertEqual(project((-2*ox,-2*oy,10),self.camera),expected)
                        self.assertEqual(result.policy,'dual_available')
                        self.assertEqual(result.dual,expected)
                        rejected_zero+=result.current!=expected
                        wrong=tuple(2*result.current[i]-result.ordinary[i] for i in range(2))
                        rejected_negative_current+=wrong!=expected
                        cases+=1
        self.assertEqual(cases,625)
        self.assertEqual(rejected_zero,600)
        self.assertEqual(rejected_negative_current,616)

    def test_changed_occluder_identity_keeps_only_ordinary_proposal(self):
        background=Track((0,0,10),(0,0,10))
        for previous,current in [((1,1,0),(1,2,0)),((1,1,0),(2,1,0)),((1,1,0),(1,1,3))]:
            result=proposals_from_geometry(background,Track((0,0,5),(2,0,5),previous,current),self.camera,self.camera)
            self.assertEqual(result.policy,'ordinary_only')
            self.assertEqual(result.reason,'occluder_identity_changed')

    def test_invalid_identity_sentinels_are_not_valid_even_when_unchanged(self):
        background=Track((0,0,10),(0,0,10))
        for invalid in [(-1,0,0),(0xffffffff,0,0),(0,0xffffffff,0),(0,0,0xffffffff)]:
            result=proposals_from_geometry(background,Track((0,0,5),(2,0,5),invalid,invalid),self.camera,self.camera)
            self.assertEqual(result.policy,'ordinary_only')
            self.assertEqual(result.reason,'occluder_identity_invalid')
        invalid_background=Track((0,0,10),(0,0,10),(-1,0,0),(-1,0,0))
        self.assertEqual(proposals_from_geometry(invalid_background,None,self.camera,self.camera).policy,'no_history')

    def test_missing_and_mismatched_occluder_lookup_are_not_motion(self):
        background=Track((0,0,10),(0,0,10))
        for occluder,reason in [(None,'missing_occluder_reference'),
                               (Track((1,0,5),(2,0,5)),'occluder_lookup_mismatch')]:
            result=proposals_from_geometry(background,occluder,self.camera,self.camera)
            self.assertEqual(result.policy,'ordinary_only');self.assertEqual(result.reason,reason)

    def test_offscreen_alternate_falls_back_without_clamping(self):
        result=proposals_from_geometry(Track((0,0,10),(0,0,10)),Track((0,0,5),(20,0,5)),self.camera,self.camera)
        self.assertEqual(result.policy,'ordinary_only');self.assertEqual(result.reason,'dual_offscreen')
        self.assertEqual(result.ordinary,(50.5,40.5))

    def test_occluder_can_leave_view_while_alternate_history_stays_visible(self):
        result=proposals_from_geometry(Track((10,0,10),(8.9,0,10)),Track((5,0,5),(6,0,5)),self.camera,self.camera)
        self.assertEqual(result.policy,'dual_available')
        self.assertGreater(result.occluder_current[0],self.camera.viewport[0])
        self.assertAlmostEqual(result.dual[0],85.0)

    def test_offscreen_ordinary_projection_cannot_supply_lookup(self):
        result=proposals_from_geometry(Track((-20,0,10),(0,0,10)),None,self.camera,self.camera)
        self.assertEqual(result.policy,'no_history');self.assertIsNone(result.ordinary)

    def test_resize_cut_and_background_identity_invalidate_history(self):
        background=Track((0,0,10),(0,0,10));occluder=Track((0,0,5),(2,0,5))
        cases=[(background,self.camera,False,'history_invalidated'),
               (background,Camera(viewport=(102,81)),True,'resize_invalidates_history'),
               (Track(background.previous,background.current,(1,1,0),(1,2,0)),self.camera,True,'background_identity_changed')]
        for point,camera,valid,reason in cases:
            result=proposals_from_geometry(point,occluder,self.camera,camera,history_valid=valid)
            self.assertEqual(result.policy,'no_history');self.assertEqual(result.reason,reason)

    def test_nonfinite_behind_camera_and_invalid_configuration(self):
        self.assertIsNone(project((float('nan'),0,10),self.camera))
        self.assertIsNone(project((0,0,-1),self.camera))
        result=proposals_from_geometry(Track((0,0,10),(0,0,10)),Track((0,0,5),(0,0,-1)),self.camera,self.camera)
        self.assertEqual(result.policy,'ordinary_only');self.assertEqual(result.reason,'occluder_projection_invalid')
        with self.assertRaises(ValueError):project((0,0,10),Camera(viewport=(0,81)))
        with self.assertRaises(ValueError):dual_coordinate((float('nan'),0),(0,0),(0,0))


if __name__=='__main__':unittest.main()
