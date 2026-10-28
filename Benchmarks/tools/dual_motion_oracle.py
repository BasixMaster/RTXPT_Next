"""Independent geometry fixtures for PT++ dual-motion reprojection proposals.

This is a small CPU oracle, not renderer integration or history acceptance.
The background's backward projection identifies a previous visible occluder;
tracking that geometry forward supplies the alternate correspondence.
Equation ideas: Zeng et al. (2021), Eq.6 / PT++ section6.4:
https://zheng95z.github.io/publications/trmv21
https://cwyman.org/papers/i3d26_ReSTIRPT++.pdf
No source pseudocode, implementation code or figures were copied.

Fixtures use axis-aligned cameras with explicit pixel-center coordinates.
They cover perspective parallax and orthographic common rigid motion. General
camera rotations/skinning must additionally be checked against GPU exports.
"""
from dataclasses import dataclass
import math
from typing import Optional, Tuple

Vec2 = Tuple[float, float]
Vec3 = Tuple[float, float, float]
Identity = Tuple[int, int, int]  # stable instance, generation/topology, primitive


@dataclass(frozen=True)
class Camera:
    viewport: Tuple[int, int] = (101, 81)
    origin: Vec3 = (0.0, 0.0, 0.0)
    focal: float = 50.0
    orthographic: bool = False

    def validate(self):
        if len(self.viewport) != 2 or any(not isinstance(v, int) or v < 1 for v in self.viewport):
            raise ValueError('Positive integer viewport dimensions required')
        if not math.isfinite(self.focal) or self.focal <= 0 or not finite(self.origin, 3):
            raise ValueError('Finite camera and positive focal scale required')


@dataclass(frozen=True)
class Track:
    previous: Vec3
    current: Vec3
    previous_identity: Identity = (0, 0, 0)
    current_identity: Identity = (0, 0, 0)


@dataclass(frozen=True)
class MotionProposals:
    current: Optional[Vec2]
    ordinary: Optional[Vec2]
    dual: Optional[Vec2]
    occluder_current: Optional[Vec2]
    reason: str

    @property
    def policy(self):
        if self.dual is not None:
            return 'dual_available'
        return 'ordinary_only' if self.ordinary is not None else 'no_history'


def finite(values, dimensions):
    return len(values) == dimensions and all(math.isfinite(value) for value in values)


def valid_identity(identity):
    return len(identity) == 3 and all(type(value) is int and 0 <= value < 0xffffffff for value in identity)


def project(point: Vec3, camera: Camera) -> Optional[Vec2]:
    """Pixel-center convention: viewport center is (width/2,height/2); y down."""
    camera.validate()
    if not finite(point, 3):
        return None
    x, y, z = (point[i] - camera.origin[i] for i in range(3))
    if z <= 0:
        return None
    scale = camera.focal if camera.orthographic else camera.focal / z
    result = (camera.viewport[0] * .5 + scale * x,
              camera.viewport[1] * .5 - scale * y)
    return result if finite(result, 2) else None


def in_view(point: Optional[Vec2], camera: Camera) -> bool:
    # Only points within the sample-center support are accepted by this oracle.
    return point is not None and finite(point, 2) and all(
        .5 <= point[i] <= camera.viewport[i] - .5 for i in range(2))


def dual_coordinate(current: Vec2, ordinary: Vec2, occluder_current: Vec2) -> Vec2:
    """Coordinate proposal only; callers must validate frames, lookup and bounds."""
    if not all(finite(value, 2) for value in [current, ordinary, occluder_current]):
        raise ValueError('Finite two-dimensional correspondences required')
    return tuple(ordinary[i] + current[i] - occluder_current[i] for i in range(2))


def proposals_from_geometry(background: Track, occluder: Optional[Track],
                            previous_camera: Camera, current_camera: Camera,
                            *, history_valid=True, lookup_tolerance=.51) -> MotionProposals:
    """Construct proposals from independent previous/current geometry positions.

    The ordinary coordinate can remain available when an alternate occluder
    reference is invalid. Neither proposal is a claim that a history reservoir
    passes material/normal/depth/shift validation. Resize/cut invalidates all
    history in this deliberately conservative initial integration contract.
    """
    previous_camera.validate();current_camera.validate()
    if not math.isfinite(lookup_tolerance) or lookup_tolerance < 0:
        raise ValueError('Lookup tolerance must be finite and nonnegative')
    x = project(background.current, current_camera)
    if not in_view(x, current_camera):
        return MotionProposals(x, None, None, None, 'invalid_current_pixel')
    if not history_valid:
        return MotionProposals(x, None, None, None, 'history_invalidated')
    if previous_camera.viewport != current_camera.viewport:
        return MotionProposals(x, None, None, None, 'resize_invalidates_history')
    if not valid_identity(background.previous_identity) or not valid_identity(background.current_identity):
        return MotionProposals(x, None, None, None, 'background_identity_invalid')
    if background.previous_identity != background.current_identity:
        return MotionProposals(x, None, None, None, 'background_identity_changed')
    y = project(background.previous, previous_camera)
    if not in_view(y, previous_camera):
        return MotionProposals(x, None, None, None, 'ordinary_offscreen_or_invalid')
    if occluder is None:
        return MotionProposals(x, y, None, None, 'missing_occluder_reference')
    if not valid_identity(occluder.previous_identity) or not valid_identity(occluder.current_identity):
        return MotionProposals(x, y, None, None, 'occluder_identity_invalid')
    if occluder.previous_identity != occluder.current_identity:
        return MotionProposals(x, y, None, None, 'occluder_identity_changed')
    lookup = project(occluder.previous, previous_camera)
    if lookup is None or any(abs(lookup[i] - y[i]) > lookup_tolerance for i in range(2)):
        return MotionProposals(x, y, None, None, 'occluder_lookup_mismatch')
    z = project(occluder.current, current_camera)
    if z is None:
        return MotionProposals(x, y, None, None, 'occluder_projection_invalid')
    u = dual_coordinate(x, y, z)
    if not in_view(u, previous_camera):
        return MotionProposals(x, y, None, z, 'dual_offscreen')
    return MotionProposals(x, y, u, z, 'valid_geometric_dual_proposal')
