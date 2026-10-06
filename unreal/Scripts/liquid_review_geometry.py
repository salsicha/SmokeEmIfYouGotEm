"""Closed, terrain-following volumes used by the offline liquid diagnostic."""
import math


def height_volume_geometry(upper, lower, dx, dy):
    """Return outward-wound faces; include BOTH complete heightfield surfaces.

    A flat bottom on a water fill would seed liquid inside the riverbed. Lower
    must therefore be the bed for water and a below-bed grid for the collider.
    """
    ny = len(upper)
    nx = len(upper[0]) if ny else 0
    if (min(nx, ny) < 2 or len(lower) != ny or
            any(len(row) != nx for row in (*upper, *lower)) or
            not all(math.isfinite(x) and x > 0 for x in (dx, dy))):
        raise ValueError('Expected matching rectangular grids and positive spacing')
    if any(not math.isfinite(a) or not math.isfinite(b) or a <= b
           for top, bottom in zip(upper, lower) for a,b in zip(top,bottom)):
        raise ValueError('Upper surface must be finite and strictly above lower')
    count = nx*ny
    vertices = [(i*dx, j*dy, grid[j][i]) for grid in (upper, lower)
                for j in range(ny) for i in range(nx)]
    faces = []
    for j in range(ny-1):
        for i in range(nx-1):
            a = j*nx+i
            # A warped quad is ambiguous. Use the same diagonal on both
            # surfaces, so water thickness/volume do not depend on tessellation.
            for top in ((a, a+1, a+nx+1), (a, a+nx+1, a+nx)):
                faces.extend((top, tuple(count+k for k in reversed(top))))
    perimeter = (list(range(nx)) + [j*nx+nx-1 for j in range(1,ny)]
        + [(ny-1)*nx+i for i in range(nx-2,-1,-1)]
        + [j*nx for j in range(ny-2,0,-1)])
    for k, a in enumerate(perimeter):
        b = perimeter[(k+1)%len(perimeter)]
        faces.append((a, a+count, b+count, b))
    return vertices, faces
