"""Reverse derivative of the smooth rational pressure polynomial.

Independent explicit tangent is in smooth_pressure_geometry. Shared reverse
work assembly, poles and solver checks are unchanged. Research only.
"""
from fractions import Fraction as F
from reverse_rational_depth_gradient import coefficient_reverse


def polynomial(depth,g,axis,p):
    a=list(p);b=list(p);a[axis]=(p[axis]-1)%g.h.shape[axis];b[axis]=(p[axis]+1)%g.h.shape[axis]
    a,b=tuple(a),tuple(b);hi=depth[p]
    c=(depth[b]-depth[a])/2
    e=c+(F(float(g.bed[b]))-F(float(g.bed[a])))/2
    numerator=4*hi*hi;f=numerator/(numerator+c*c)
    return f*c,f*e


def smooth_coefficient_reverse(geometry,mass_direction,adjoints):
    return coefficient_reverse(geometry,mass_direction,adjoints,polynomial_builder=polynomial)
