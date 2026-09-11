"""Math and isolation checks; the actual shader still requires rendered review."""
from pathlib import Path
import numpy as np


def rotate(before, after, detail):
    before = np.array(before, dtype=float)
    after = np.array(after, dtype=float)
    detail = np.array(detail, dtype=float)
    before /= np.linalg.norm(before)
    after /= np.linalg.norm(after)
    detail /= np.linalg.norm(detail)
    c = np.clip(np.dot(before, after), -1., 1.)
    if c < -.999:
        return detail
    axis = np.cross(before, after)
    result = detail + np.cross(axis, detail) + np.cross(axis, np.cross(axis, detail))/(1+c)
    return result/np.linalg.norm(result)


def test_no_displacement_preserves_smooth_and_detail_normals():
    detail = np.array([.2, -.3, .9])
    detail /= np.linalg.norm(detail)
    assert np.allclose(rotate([-.4, .2, 1], [-.4, .2, 1], detail), detail)


def test_face_rotation_tracks_slopes_and_preserves_detail_angle():
    before = np.array([0., 0., 1.])
    detail = np.array([.2, -.1, 1.])
    detail /= np.linalg.norm(detail)
    for slope in [(.4, .2), (-.8, .7), (2., -1.)]:
        after = np.array([-slope[0], -slope[1], 1.])
        after /= np.linalg.norm(after)
        assert np.allclose(rotate(before, after, before), after)
        rotated = rotate(before, after, detail)
        assert np.isclose(np.dot(rotated, after), np.dot(detail, before))
        assert np.allclose(rotate(-before, -after, detail), rotated)


def test_normal_review_is_isolated_and_uses_camera_relative_derivatives():
    root = Path(__file__).resolve().parents[2]
    script = (root/'unreal/Scripts/create_displacement_normal_review.py').read_text()
    assert 'duplicate_asset(SOURCE, destination)' in script
    assert 'save_loaded_asset(material' in script
    assert 'save_loaded_asset(source' not in script
    assert 'WPT_CAMERA_RELATIVE_NO_OFFSETS' in script
    assert 'WPT_CAMERA_RELATIVE)' in script
    assert 'cross(ddx(Before), ddy(Before))' in script
    assert 'cross(ddx(After), ddy(After))' in script
    assert 'get_material_property_input_node_output_name' in script
    assert 'beforeLength < 1e-8 || afterLength < 1e-8' in script
    source = (root/'unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimWaterSurfaceActor.cpp').read_text()
    assert 'bUsesSouthForkFullReachSingleSurface &&\n        (bSmoothDisplacementNormalReview ||' in source
    assert 'MaterialExpressionVertexInterpolator' in script
    assert 'duplicate_material_expression(material, None, fluid)' in script
