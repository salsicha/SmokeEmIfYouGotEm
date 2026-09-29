"""Independent numerical/limiting checks of the reduced geometry, not foam acceptance."""
import json
import math
import numpy as np
from surface_bubble_shape import shape, meniscus, bessel_k

np.testing.assert_allclose(bessel_k(0, 1.), .4210244382407083, rtol=1e-12)
np.testing.assert_allclose(bessel_k(1, 1.), .6019072301972346, rtol=1e-12)
x = np.geomspace(.0001, 15., 50)
for order in (0, 1):
    np.testing.assert_allclose(bessel_k(order, x, 128), bessel_k(order, x, 256), rtol=1e-11)
rows = []
for radius in (.00002, .0003, .0005, .0007, .001):
    m = shape(radius)
    rr, lc = m['rim_radius_m'], m['capillary_length_m']
    assert abs(m['dimensionless_rim_balance_residual']) < 1e-14
    np.testing.assert_allclose(meniscus(rr, m), m['rim_height_m'], rtol=1e-12)
    # One-sided difference stays in the exterior domain; refine to check slope.
    h = rr*1e-5
    slope = (-3*meniscus(rr,m)+4*meniscus(rr+h,m)-meniscus(rr+2*h,m))/(2*h)
    np.testing.assert_allclose(slope, -m['rim_slope'], rtol=1e-7)
    assert 0 < m['rim_radius_m'] < radius < m['cap_curvature_radius_m']
    assert abs(m['relative_gas_volume_error']) < .005
    assert meniscus(12*lc, m) < 1e-9
    # Pressure equality uses the same zero-rim approximation as equation 3.8.
    pressure_top = 4*m['tension_N_m']/m['cap_curvature_radius_m']
    depth0 = radius+math.sqrt(radius**2-rr**2)
    pressure_bottom = 2*m['tension_N_m']/radius+m['density_kg_m3']*m['gravity_m_s2']*depth0
    np.testing.assert_allclose(pressure_top, pressure_bottom, rtol=1e-14)
    rows.append(m)
small = rows[0]
assert abs(small['cap_curvature_radius_m']/(2*small['gas_radius_m'])-1) < 1e-4
assert abs(small['rim_radius_m']/small['gas_radius_m']/math.sqrt(small['bond']/3)-1) < 1e-4
try:
    shape(.003)
    raise AssertionError('Large bubble should be rejected')
except ValueError:
    pass
print('BUBBLE_SHAPE_CHECKS', json.dumps(rows), flush=True)
