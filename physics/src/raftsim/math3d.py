"""Small dependency-free 3D math primitives for the physics core."""

from __future__ import annotations

from dataclasses import dataclass
from math import asin, atan2, cos, isclose, sin, sqrt

EPSILON = 1.0e-12


@dataclass(frozen=True, slots=True)
class Vec3:
    """Immutable 3D vector with the operations needed by the simulation core."""

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def __iter__(self):
        yield self.x
        yield self.y
        yield self.z

    def __add__(self, other: Vec3) -> Vec3:
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: Vec3) -> Vec3:
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __neg__(self) -> Vec3:
        return Vec3(-self.x, -self.y, -self.z)

    def __mul__(self, scalar: float) -> Vec3:
        return Vec3(self.x * scalar, self.y * scalar, self.z * scalar)

    def __rmul__(self, scalar: float) -> Vec3:
        return self * scalar

    def __truediv__(self, scalar: float) -> Vec3:
        if abs(scalar) <= EPSILON:
            raise ZeroDivisionError("Cannot divide Vec3 by zero.")
        return Vec3(self.x / scalar, self.y / scalar, self.z / scalar)

    def dot(self, other: Vec3) -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other: Vec3) -> Vec3:
        return Vec3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
        )

    @property
    def magnitude_squared(self) -> float:
        return self.dot(self)

    @property
    def magnitude(self) -> float:
        return sqrt(self.magnitude_squared)

    def normalized(self) -> Vec3:
        length = self.magnitude
        if length <= EPSILON:
            raise ValueError("Cannot normalize a near-zero Vec3.")
        return self / length

    def is_close(self, other: Vec3, *, rel_tol: float = 1.0e-9, abs_tol: float = 1.0e-12) -> bool:
        return (
            isclose(self.x, other.x, rel_tol=rel_tol, abs_tol=abs_tol)
            and isclose(self.y, other.y, rel_tol=rel_tol, abs_tol=abs_tol)
            and isclose(self.z, other.z, rel_tol=rel_tol, abs_tol=abs_tol)
        )

    def as_tuple(self) -> tuple[float, float, float]:
        return (self.x, self.y, self.z)


@dataclass(frozen=True, slots=True)
class Quaternion:
    """Unit quaternion used for raft orientation."""

    w: float = 1.0
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    @staticmethod
    def identity() -> Quaternion:
        return Quaternion()

    @staticmethod
    def from_axis_angle(axis: Vec3, angle_radians: float) -> Quaternion:
        unit_axis = axis.normalized()
        half_angle = angle_radians * 0.5
        scale = sin(half_angle)
        return Quaternion(
            cos(half_angle),
            unit_axis.x * scale,
            unit_axis.y * scale,
            unit_axis.z * scale,
        ).normalized()

    def __mul__(self, other: Quaternion) -> Quaternion:
        return Quaternion(
            self.w * other.w - self.x * other.x - self.y * other.y - self.z * other.z,
            self.w * other.x + self.x * other.w + self.y * other.z - self.z * other.y,
            self.w * other.y - self.x * other.z + self.y * other.w + self.z * other.x,
            self.w * other.z + self.x * other.y - self.y * other.x + self.z * other.w,
        )

    @property
    def norm_squared(self) -> float:
        return self.w * self.w + self.x * self.x + self.y * self.y + self.z * self.z

    @property
    def norm(self) -> float:
        return sqrt(self.norm_squared)

    def normalized(self) -> Quaternion:
        length = self.norm
        if length <= EPSILON:
            raise ValueError("Cannot normalize a near-zero Quaternion.")
        return Quaternion(self.w / length, self.x / length, self.y / length, self.z / length)

    def conjugate(self) -> Quaternion:
        return Quaternion(self.w, -self.x, -self.y, -self.z)

    def rotate_vector(self, vector: Vec3) -> Vec3:
        rotated = self * Quaternion(0.0, vector.x, vector.y, vector.z) * self.conjugate()
        return Vec3(rotated.x, rotated.y, rotated.z)

    def integrate_angular_velocity(self, angular_velocity: Vec3, dt: float) -> Quaternion:
        """Return orientation advanced by a fixed-step angular velocity update."""

        angular_speed = angular_velocity.magnitude
        if angular_speed <= EPSILON:
            return self.normalized()
        delta = Quaternion.from_axis_angle(angular_velocity / angular_speed, angular_speed * dt)
        return (delta * self).normalized()

    def to_euler_radians(self) -> tuple[float, float, float]:
        """Return roll, pitch, yaw in radians for diagnostics and plots."""

        sinr_cosp = 2.0 * (self.w * self.x + self.y * self.z)
        cosr_cosp = 1.0 - 2.0 * (self.x * self.x + self.y * self.y)
        roll = atan2(sinr_cosp, cosr_cosp)

        sinp = 2.0 * (self.w * self.y - self.z * self.x)
        if abs(sinp) >= 1.0:
            pitch = 1.5707963267948966 if sinp > 0.0 else -1.5707963267948966
        else:
            pitch = asin(sinp)

        siny_cosp = 2.0 * (self.w * self.z + self.x * self.y)
        cosy_cosp = 1.0 - 2.0 * (self.y * self.y + self.z * self.z)
        yaw = atan2(siny_cosp, cosy_cosp)
        return (roll, pitch, yaw)

    def is_close(
        self,
        other: Quaternion,
        *,
        rel_tol: float = 1.0e-9,
        abs_tol: float = 1.0e-12,
    ) -> bool:
        return (
            isclose(self.w, other.w, rel_tol=rel_tol, abs_tol=abs_tol)
            and isclose(self.x, other.x, rel_tol=rel_tol, abs_tol=abs_tol)
            and isclose(self.y, other.y, rel_tol=rel_tol, abs_tol=abs_tol)
            and isclose(self.z, other.z, rel_tol=rel_tol, abs_tol=abs_tol)
        )

    def as_tuple(self) -> tuple[float, float, float, float]:
        return (self.w, self.x, self.y, self.z)
