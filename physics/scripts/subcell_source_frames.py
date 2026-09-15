"""Explicit storage/geometry frame helpers shared by both pool representations."""
from fractions import Fraction as F
import math
import numpy as np

from subcell_pressure_kinetic_geometry import local_form
from subcell_source_face_section import SourceFaceSection, stage_difference
from triangle_face_section import TriangleFaceSection


def physical_datum(storage):
    return getattr(storage, 'source_datum', storage.datum)


def pool_form(storage, volume):
    form = local_form(storage, volume)
    return dict(form, datum=physical_datum(storage))


def face_section(trace):
    return trace if isinstance(trace, TriangleFaceSection) else TriangleFaceSection([trace], trace[:, 0])


def trace_start(trace):
    return trace.source_segments[0][0][0] if isinstance(trace, SourceFaceSection) else trace[0, 0]


def absolute_interval(storage, height, datum):
    if hasattr(storage, 'fragments'):
        levels = sorted(set(v[2] for fragment in storage.fragments for v in fragment.polygon))
        surface = F(datum)+F(float(height))
        differences = [surface-level for level in levels]
    else:
        levels = np.unique(storage.levels)
        differences = [stage_difference(0., level, height, datum) for level in levels]
    if any(d == 0 for d in differences):
        raise ValueError('Topology event requires explicit one-sided transition')
    lower = [z for z, d in zip(levels, differences) if d > 0]
    upper = [z for z, d in zip(levels, differences) if d < 0]
    return [max(lower) if lower else -math.inf, min(upper) if upper else math.inf]


def inside_interval(height, datum, low, high):
    if isinstance(datum, F):
        return low < F(datum)+F(float(height)) < high
    return (math.fsum((height, datum, -low)) > 0 and math.fsum((height, datum, -high)) < 0)
