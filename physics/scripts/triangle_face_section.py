"""Shared exact wet face area and pressure from the original terrain triangles."""
import numpy as np
import math


class TriangleFaceSection:
    def __init__(self, segments, bounds):
        segments, bounds = np.asarray(segments, float), np.asarray(bounds, float)
        if (segments.ndim != 3 or segments.shape[1:] != (2, 2) or not len(segments)
                or bounds.shape != (2,) or not np.isfinite(segments).all()
                or not np.isfinite(bounds).all() or bounds[1] <= bounds[0]):
            raise ValueError('Finite nonempty (tangent,z) segments and face bounds required')
        segments = segments.copy()
        reverse = segments[:, 1, 0] < segments[:, 0, 0]
        segments[reverse] = segments[reverse, ::-1]
        segments = segments[np.argsort(segments[:, 0, 0], kind='stable')]
        self.lengths = segments[:, 1, 0]-segments[:, 0, 0]
        if (self.lengths <= 0).any():
            raise ValueError('Degenerate face segment')
        tolerance = 1e-10*(bounds[1]-bounds[0])
        if (abs(segments[0, 0, 0]-bounds[0]) > tolerance or abs(segments[-1, 1, 0]-bounds[1]) > tolerance
                or np.any(abs(segments[1:, 0, 0]-segments[:-1, 1, 0]) > tolerance)
                or np.any(abs(segments[1:, 0, 1]-segments[:-1, 1, 1]) > 1e-9)):
            raise ValueError('Missing, overlapping, or discontinuous source face coverage')
        self.segments = segments
        self.levels = np.sort(segments[:, :, 1], axis=1)
        self.width = float(bounds[1]-bounds[0])

    @classmethod
    def from_cell(cls, triangles, axis, coordinate, bounds):
        if axis not in (0, 1) or not np.isfinite(coordinate):
            raise ValueError('Finite XY face plane required')
        segments = []
        for triangle in triangles:
            for a, b in zip(triangle, np.roll(triangle, -1, axis=0)):
                if (a[axis] == coordinate and b[axis] == coordinate
                        and a[1-axis] != b[1-axis]):
                    segments.append([[a[1-axis], a[2]], [b[1-axis], b[2]]])
        return cls(segments, bounds)

    def moments(self, stage, datum=0.):
        """Return integral(h ds), integral(h^2 ds), and wet width; exact for each segment."""
        if not all(math.isfinite(v) for v in (stage, datum)):
            raise ValueError('Finite stage required')
        lower_depth, upper_depth = self.depth_intervals(stage, datum).T
        first, second, wet = (np.zeros(len(lower_depth)) for _ in range(3))
        full = (upper_depth >= 0) & (lower_depth > 0)
        a, b = lower_depth[full], upper_depth[full]
        first[full] = (a+b)/2
        second[full] = (a*a+a*b+b*b)/3
        wet[full] = 1
        partial = (lower_depth > 0) & (upper_depth < 0)
        depth = lower_depth[partial]
        fraction = depth/self.bed_spans[partial]
        first[partial] = fraction*depth/2
        second[partial] = fraction*depth*depth/3
        wet[partial] = fraction
        return float(self.lengths@first), float(self.lengths@second), float(self.lengths@wet)

    def depth_intervals(self, stage, datum=0.):
        """Depth at each sorted low/high bed endpoint in the supplied frame."""
        return stage-(self.levels-datum)

    @property
    def bed_spans(self):
        return self.levels[:, 1]-self.levels[:, 0]

    def maximum_depth(self, stage, datum=0.):
        return max(float(self.depth_intervals(stage, datum)[:, 0].max()), 0.)

    def bed_at(self, tangent):
        tangent = np.asarray(tangent, float)
        starts, ends = self.segments[:, 0, 0], self.segments[:, 1, 0]
        if not np.isfinite(tangent).all() or (tangent < starts[0]).any() or (tangent > ends[-1]).any():
            raise ValueError('Outside exact face coverage')
        index = np.minimum(np.searchsorted(ends, tangent, side='left'), len(ends)-1)
        t = (tangent-starts[index])/self.lengths[index]
        return self.segments[index, 0, 1]*(1-t)+self.segments[index, 1, 1]*t

    def verify_shared(self, other):
        """Both cells must expose the same geometric function, not just average bed."""
        if self.width != other.width:
            raise ValueError('Face lengths differ')
        points = np.unique(np.r_[self.segments[:, :, 0].ravel(), other.segments[:, :, 0].ravel()])
        if not np.allclose(self.bed_at(points), other.bed_at(points), atol=1e-9, rtol=0):
            raise ValueError('Neighboring source face geometry differs')

    def flux(self, left_stage, left_velocity, right_stage, right_velocity, axis, gravity=9.81,
             left_datum=0., right_datum=0.):
        """Integrated nondispersive Rusanov base flux on one shared geometric face.

        The bound is constant on this face, so integrals of h and h^2 are exact.
        This is a mass/advection/hydrostatic component, not a replacement for
        the required dispersive pressure/energy coupling or a qualified solver.
        """
        left, right = np.asarray(left_velocity, float), np.asarray(right_velocity, float)
        if (axis not in (0, 1) or left.shape != (2,) or right.shape != (2,)
                or not np.isfinite([left, right]).all() or not np.isfinite(gravity) or gravity <= 0):
            raise ValueError('Finite velocities, positive gravity and XY normal required')
        hl, hhl, _ = self.moments(left_stage, left_datum)
        hr, hhr, _ = self.moments(right_stage, right_datum)
        speed = max(abs(left[axis])+np.sqrt(gravity*self.maximum_depth(left_stage, left_datum)),
                    abs(right[axis])+np.sqrt(gravity*self.maximum_depth(right_stage, right_datum)))
        mass = .5*(left[axis]*hl+right[axis]*hr)-.5*speed*(hr-hl)
        momentum = .5*(left[axis]*hl*left+right[axis]*hr*right)-.5*speed*(hr*right-hl*left)
        momentum[axis] += .25*gravity*(hhl+hhr)
        return np.r_[mass, momentum], float(speed)
