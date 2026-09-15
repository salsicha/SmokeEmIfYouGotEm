"""Exact source-face geometry with explicit datum-relative numerical kernels.

The float projection is for inspection only. Lengths and wet depths are formed
from retained rational differences, so no positive interval or thin column is
lost by subtracting rounded absolute coordinates.
"""
from fractions import Fraction as F
import math
import numpy as np

from triangle_face_section import TriangleFaceSection


def stage_difference(left_stage, left_datum, right_stage, right_datum):
    """Right minus left surface, retaining exact geometry-datum differences."""
    if isinstance(left_datum, F) or isinstance(right_datum, F):
        return float(F(right_datum)-F(left_datum)+F(float(right_stage))-F(float(left_stage)))
    return math.fsum((right_datum, -left_datum, right_stage, -left_stage))


class SourceFaceSection(TriangleFaceSection):
    def __init__(self, segments):
        ordered = []
        for segment in segments:
            if len(segment) != 2 or any(len(v) != 2 for v in segment):
                raise ValueError('Two original tangent/elevation endpoints required')
            pair = sorted(tuple(F(x) for x in v) for v in segment)
            if pair[0][0] >= pair[1][0]:
                raise ValueError('Positive original face interval required')
            ordered.append(tuple(pair))
        ordered.sort()
        if not ordered:
            raise ValueError('Nonempty original source face required')
        if any(a[1] != b[0] for a, b in zip(ordered, ordered[1:])):
            raise ValueError('Original face has a gap, overlap or discontinuity')
        self.source_segments = tuple(ordered)
        self.source_levels = tuple(tuple(sorted((a[1], b[1]))) for a, b in ordered)
        self.lengths = np.array([float(b[0]-a[0]) for a, b in ordered])
        self.width = float(ordered[-1][1][0]-ordered[0][0][0])
        self.segments = np.asarray(ordered, float)
        self.levels = np.asarray(self.source_levels, float)
        if not np.isfinite(self.lengths).all() or np.any(self.lengths <= 0) or not math.isfinite(self.width):
            raise ValueError('Positive source face length exceeds represented range; no deletion')
        for values in (self.lengths, self.segments, self.levels):
            values.setflags(write=False)

    def depth_intervals(self, stage, datum=0.):
        if not all(math.isfinite(v) for v in (stage, datum)):
            raise ValueError('Finite datum-relative face state required')
        surface = F(datum)+F(float(stage))
        depths = tuple((surface-low, surface-high) for low, high in self.source_levels)
        represented = np.asarray(depths, float)
        if (not np.isfinite(represented).all()
                or any(exact != 0 and value == 0 for row, values in zip(depths, represented)
                       for exact, value in zip(row, values))):
            raise ValueError('Nonzero source face depth exceeds represented range; no dry/wet reclassification')
        return represented

    @property
    def bed_spans(self):
        spans = tuple(high-low for low, high in self.source_levels)
        result = np.asarray(spans, float)
        if not np.isfinite(result).all() or any(exact > 0 and value == 0 for exact, value in zip(spans, result)):
            raise ValueError('Positive source face bed span exceeds represented range')
        return result

    def bed_at(self, tangent):
        values = np.asarray(tangent, dtype=object)
        result = []
        for value in values.ravel():
            t = F(value)
            if not self.source_segments[0][0][0] <= t <= self.source_segments[-1][1][0]:
                raise ValueError('Outside exact source face coverage')
            a, b = next(s for s in self.source_segments if s[0][0] <= t <= s[1][0])
            result.append(float(a[1]+(b[1]-a[1])*(t-a[0])/(b[0]-a[0])))
        return np.asarray(result).reshape(values.shape)

    def restricted(self, low, high):
        low, high = F(low), F(high)
        if low >= high or low < self.source_segments[0][0][0] or high > self.source_segments[-1][1][0]:
            raise ValueError('Positive represented source subinterval required')
        if (low, high) == (self.source_segments[0][0][0], self.source_segments[-1][1][0]):
            # Geometry is already canonical and its arrays are read-only.
            # No water/depth result is retained or reused here.
            return self
        pieces = []
        for a, b in self.source_segments:
            first, last = max(low, a[0]), min(high, b[0])
            if first < last:
                z = lambda t: a[1]+(b[1]-a[1])*(t-a[0])/(b[0]-a[0])
                pieces.append(((first, z(first)), (last, z(last))))
        return type(self)(pieces)

    def tolist(self):
        """Single-trace FLOAT PROJECTION for reports, never geometry recovery."""
        if len(self.source_segments) != 1:
            raise ValueError('Single original trace required for report projection')
        return self.segments[0].tolist()

    def verify_shared(self, other):
        if not isinstance(other, SourceFaceSection):
            raise ValueError('Exact source neighbor required; float projection is not authoritative')
        first, last = self.source_segments[0][0][0], self.source_segments[-1][1][0]
        if (first, last) != (other.source_segments[0][0][0], other.source_segments[-1][1][0]):
            raise ValueError('Original shared face bounds differ')
        if self.source_segments == other.source_segments:
            return  # Exact represented geometry equality, not float tolerance.
        knots = sorted(set(v[0] for s in self.source_segments+other.source_segments for v in s))
        def height(section, t):
            a, b = next(s for s in section.source_segments if s[0][0] <= t <= s[1][0])
            return a[1]+(b[1]-a[1])*(t-a[0])/(b[0]-a[0])
        if any(height(self, t) != height(other, t) for t in knots):
            raise ValueError('Original shared face heights differ')


def fragment_section(fragments, axis, coordinate):
    return SourceFaceSection([segment for fragment in fragments
                              if (segment := fragment.face(axis, coordinate)) is not None])
