from math import isclose, pi

import pytest

from raftsim.math3d import Quaternion, Vec3


def test_vec3_arithmetic_and_cross_product():
    a = Vec3(1.0, 2.0, 3.0)
    b = Vec3(4.0, -2.0, 0.5)

    assert a + b == Vec3(5.0, 0.0, 3.5)
    assert a - b == Vec3(-3.0, 4.0, 2.5)
    assert 2.0 * a == Vec3(2.0, 4.0, 6.0)
    assert a.dot(b) == pytest.approx(1.5)
    assert a.cross(b) == Vec3(7.0, 11.5, -10.0)


def test_vec3_normalization_rejects_zero_vector():
    with pytest.raises(ValueError):
        Vec3().normalized()


def test_quaternion_rotates_vector():
    rotation = Quaternion.from_axis_angle(Vec3(0.0, 0.0, 1.0), pi / 2.0)
    rotated = rotation.rotate_vector(Vec3(1.0, 0.0, 0.0))

    assert rotated.is_close(Vec3(0.0, 1.0, 0.0), abs_tol=1.0e-12)
    assert isclose(rotation.norm, 1.0, abs_tol=1.0e-12)


def test_quaternion_angular_velocity_integration_stays_normalized():
    orientation = Quaternion.identity()
    for _ in range(100):
        orientation = orientation.integrate_angular_velocity(Vec3(0.0, 0.0, 0.5), 1.0 / 60.0)

    assert isclose(orientation.norm, 1.0, abs_tol=1.0e-12)
