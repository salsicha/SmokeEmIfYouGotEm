"""Pure placement math matching AddEvidenceCanopy; dimensions are inferred.

The ground argument must come from the native Landscape, not the optical/DSM
placement's advisory terrain_z_cm. Existing mesh bounds and materials are kept.
"""
import math


def transform_row(row, bounds, ground_cm, *, understory=False):
    expected = 5 if understory else 8
    if len(row) != expected or not all(math.isfinite(float(v)) for v in row):
        raise ValueError('Malformed or nonfinite canopy row')
    lower, upper = bounds['min'], bounds['max']
    if len(lower) != 3 or len(upper) != 3:
        raise ValueError('Three-dimensional mesh bounds required')
    if not all(math.isfinite(v) for v in [*lower, *upper, ground_cm]):
        raise ValueError('Nonfinite ground or mesh bounds')
    size = [b-a for a,b in zip(lower, upper)]
    if min(size) <= 0 or size[2] < 100:
        raise ValueError('Expected production mesh bounds in centimetres; no implicit build scale')
    if understory:
        height, width, yaw = row[2:5]
        if height <= 0 or width <= 0:
            raise ValueError('Nonpositive shrub dimensions')
        horizontal = 100*width/max(1, size[0], size[1])
        vertical = 100*height/max(1, size[2])
        root = ground_cm-20
    else:
        radius, height, form, kind, yaw = row[3:8]
        if form not in (0, 1) or kind != 1 or radius <= 0 or height <= 0:
            raise ValueError('Unsupported canopy form/kind or dimensions')
        horizontal = 200*radius/max(1, size[0], size[1])
        vertical = min(1.8*horizontal, max(.8*horizontal, 100*height/max(1, size[2])))
        root = ground_cm-30
    return dict(location_cm=[row[0], row[1], root-lower[2]*vertical],
                scale=[horizontal, horizontal, vertical], yaw_degrees=yaw,
                root_cm=root, ground_cm=ground_cm)
