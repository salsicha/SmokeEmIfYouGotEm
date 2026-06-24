"""Dependency-free 2D math primitives for top-down river simulation."""

from __future__ import annotations

from dataclasses import dataclass
from math import cos, hypot, isclose, sin

EPSILON = 1.0e-12


@dataclass(frozen=True, slots=True)
class Vec2:
    """Immutable 2D vector."""

    x: float = 0.0
    y: float = 0.0

    def __iter__(self):
        yield self.x
        yield self.y

    def __add__(self, other: Vec2) -> Vec2:
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vec2) -> Vec2:
        return Vec2(self.x - other.x, self.y - other.y)

    def __neg__(self) -> Vec2:
        return Vec2(-self.x, -self.y)

    def __mul__(self, scalar: float) -> Vec2:
        return Vec2(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar: float) -> Vec2:
        return self * scalar

    def __truediv__(self, scalar: float) -> Vec2:
        if abs(scalar) <= EPSILON:
            raise ZeroDivisionError("Cannot divide Vec2 by zero.")
        return Vec2(self.x / scalar, self.y / scalar)

    def dot(self, other: Vec2) -> float:
        return self.x * other.x + self.y * other.y

    def cross(self, other: Vec2) -> float:
        """Return the scalar z component of the 2D cross product."""

        return self.x * other.y - self.y * other.x

    @property
    def magnitude_squared(self) -> float:
        return self.dot(self)

    @property
    def magnitude(self) -> float:
        return hypot(self.x, self.y)

    def normalized(self) -> Vec2:
        length = self.magnitude
        if length <= EPSILON:
            raise ValueError("Cannot normalize a near-zero Vec2.")
        return self / length

    def safe_normalized(self, fallback: Vec2 | None = None) -> Vec2:
        if self.magnitude <= EPSILON:
            return fallback if fallback is not None else Vec2(1.0, 0.0)
        return self.normalized()

    def perpendicular_left(self) -> Vec2:
        return Vec2(-self.y, self.x)

    def perpendicular_right(self) -> Vec2:
        return Vec2(self.y, -self.x)

    def rotated(self, angle_radians: float) -> Vec2:
        c = cos(angle_radians)
        s = sin(angle_radians)
        return Vec2(self.x * c - self.y * s, self.x * s + self.y * c)

    def distance_to(self, other: Vec2) -> float:
        return (self - other).magnitude

    def is_close(self, other: Vec2, *, rel_tol: float = 1.0e-9, abs_tol: float = 1.0e-12) -> bool:
        return isclose(self.x, other.x, rel_tol=rel_tol, abs_tol=abs_tol) and isclose(
            self.y,
            other.y,
            rel_tol=rel_tol,
            abs_tol=abs_tol,
        )

    def as_tuple(self) -> tuple[float, float]:
        return (self.x, self.y)


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def smoothstep(edge0: float, edge1: float, value: float) -> float:
    if edge0 == edge1:
        return 0.0 if value < edge0 else 1.0
    t = clamp((value - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)
