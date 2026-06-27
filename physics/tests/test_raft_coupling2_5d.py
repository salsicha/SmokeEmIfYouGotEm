import math

import pytest

from raftsim.math3d import Quaternion, Vec3
from raftsim.raft_coupling2_5d import RaftSamplePatch, RaftState6DoF, build_default_raft_mass_properties
from raftsim.scenario2_5d import RaftParameters2_5D


def test_raft_state_advances_linear_and_angular_motion():
    state = RaftState6DoF(
        position=Vec3(1.0, 2.0, 3.0),
        linear_velocity=Vec3(2.0, 0.0, 0.0),
        angular_velocity=Vec3(0.0, 0.0, 1.0),
    )

    advanced = state.advance(0.5, linear_acceleration=Vec3(0.0, 2.0, 0.0))

    assert advanced.position.is_close(Vec3(2.0, 2.5, 3.0))
    assert advanced.linear_velocity.is_close(Vec3(2.0, 1.0, 0.0))
    assert math.isclose(advanced.orientation.norm, 1.0)


def test_raft_state_rejects_negative_timestep():
    with pytest.raises(ValueError):
        RaftState6DoF().advance(-0.1)


def test_world_point_and_point_velocity_include_rotation():
    state = RaftState6DoF(
        position=Vec3(10.0, 0.0, 0.0),
        orientation=Quaternion.from_axis_angle(Vec3(0.0, 0.0, 1.0), math.pi * 0.5),
        linear_velocity=Vec3(1.0, 0.0, 0.0),
        angular_velocity=Vec3(0.0, 0.0, 2.0),
    )

    point = state.world_point(Vec3(1.0, 0.0, 0.0))
    velocity = state.point_velocity(Vec3(1.0, 0.0, 0.0))

    assert point.is_close(Vec3(10.0, 1.0, 0.0), abs_tol=1.0e-9)
    assert velocity.is_close(Vec3(-1.0, 0.0, 0.0), abs_tol=1.0e-9)


def test_default_mass_properties_include_crew_inertia_and_samples():
    params = RaftParameters2_5D(mass_kg=400.0, guide_mass_kg=90.0, passenger_mass_kg=70.0, passenger_count=4)

    properties = build_default_raft_mass_properties(params)

    assert properties.total_mass_kg == 770.0
    assert properties.inverse_mass == pytest.approx(1.0 / 770.0)
    assert properties.inertia_diagonal_kg_m2.x > 0.0
    assert properties.inertia_diagonal_kg_m2.y > properties.inertia_diagonal_kg_m2.x
    assert properties.gravity == Vec3(0.0, 0.0, -9.81)
    assert properties.guide_offset.x < 0.0
    assert len(properties.passenger_offsets) == 4
    assert len(properties.sample_patches) == 14
    assert {patch.kind for patch in properties.sample_patches} == {"left_tube", "right_tube", "floor"}


def test_sample_patch_requires_positive_area_and_normalizes_normal():
    patch = RaftSamplePatch("test", Vec3(), 1.0, Vec3(0.0, 0.0, 2.0))

    assert patch.local_normal == Vec3(0.0, 0.0, 1.0)
    with pytest.raises(ValueError):
        RaftSamplePatch("bad", Vec3(), 0.0)
