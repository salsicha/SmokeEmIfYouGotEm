import math

import pytest

from raftsim.math3d import Quaternion, Vec3
from raftsim.raft_coupling2_5d import RaftState6DoF


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
