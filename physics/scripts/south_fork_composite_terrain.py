"""Cartesian terrain composition; no station-ribbon deformation or raster fallback."""
import numpy as np


def stitch_rectangular_boundaries(inner_edges, outer_edges):
    """Zip corresponding ordered rectangle edges, retaining every XYZ vertex.

    Each edge runs in the same direction on both rectangles; adjoining edges
    share corner vertices. Heights between source anchors are inferred faces.
    """
    if len(inner_edges) != 4 or len(outer_edges) != 4:
        raise ValueError('Four rectangle edges required')
    for edges in (inner_edges, outer_edges):
        for i, edge in enumerate(edges):
            if not np.isfinite(edge).all() or not np.array_equal(edge[-1], edges[(i+1) % 4][0]):
                raise ValueError('Boundary must be a closed finite XYZ loop')
    vertices, triangles, indices = [], [], {}

    def index(point):
        key = tuple(map(float, point))
        if key not in indices:
            indices[key] = len(vertices)
            vertices.append(key)
        return indices[key]

    for inner, outer in zip(inner_edges, outer_edges):
        inner, outer = np.asarray(inner), np.asarray(outer)
        if min(len(inner), len(outer)) < 2:
            raise ValueError('Both boundaries need edge endpoints')
        axis = int(np.argmax(abs(inner[-1, :2]-inner[0, :2])))
        def parameters(points):
            span = points[-1, axis]-points[0, axis]
            if span == 0:
                raise ValueError('Degenerate rectangle edge')
            values = (points[:, axis]-points[0, axis])/span
            if not np.all(np.diff(values) > 0):
                raise ValueError('Boundary order reverses')
            return values
        ti, to = parameters(inner), parameters(outer)
        ii, oo = [index(p) for p in inner], [index(p) for p in outer]
        i = j = 0
        while i+1 < len(ii) or j+1 < len(oo):
            if j+1 == len(oo) or (i+1 < len(ii) and ti[i+1] <= to[j+1]):
                triangles.append([ii[i], ii[i+1], oo[j]])
                i += 1
            else:
                triangles.append([ii[i], oo[j+1], oo[j]])
                j += 1
    xyz = np.asarray(vertices, dtype=np.float64)
    faces = np.asarray(triangles, dtype=np.int64)
    cross = np.cross(xyz[faces[:, 1]]-xyz[faces[:, 0]], xyz[faces[:, 2]]-xyz[faces[:, 0]])
    if np.any(abs(cross[:, 2]) < 1e-10):
        raise ValueError('Degenerate seam triangle')
    reverse = cross[:, 2] < 0
    faces[reverse] = faces[reverse][:, [0, 2, 1]]
    return xyz, faces


def sample_triangles(xyz, faces, east, north):
    """Small seam sampler; exact triangle heights with no extrapolation."""
    east, north = np.broadcast_arrays(np.asarray(east, float), np.asarray(north, float))
    queries = np.column_stack((east.ravel(), north.ravel()))
    out = np.full(len(queries), np.nan)
    for face in faces:
        p, q, r = xyz[face]
        lower, upper = np.minimum(np.minimum(p[:2], q[:2]), r[:2]), np.maximum(np.maximum(p[:2], q[:2]), r[:2])
        ids = np.flatnonzero(np.isnan(out) & np.all(queries >= lower-1e-8, axis=1) & np.all(queries <= upper+1e-8, axis=1))
        if not len(ids):
            continue
        a, b, v = q[:2]-p[:2], r[:2]-p[:2], queries[ids]-p[:2]
        det = a[0]*b[1]-a[1]*b[0]
        u = (v[:, 0]*b[1]-v[:, 1]*b[0])/det
        w = (a[0]*v[:, 1]-a[1]*v[:, 0])/det
        inside = (u >= -1e-8) & (w >= -1e-8) & (u+w <= 1+1e-8)
        out[ids[inside]] = (p[2]+u*(q[2]-p[2])+w*(r[2]-p[2]))[inside]
    if not np.isfinite(out).all():
        raise ValueError('Query outside explicitly joined terrain')
    return out.reshape(east.shape)


def sample_regular_triangles(z, x0, y0, cell, east, north):
    """Same NW-NE-SW / NE-SE-SW triangles used by the coarse render mesh."""
    east, north = np.broadcast_arrays(np.asarray(east, float), np.asarray(north, float))
    cf, rf = (east-x0)/cell, (y0-north)/cell
    c, r = np.floor(cf).astype(int), np.floor(rf).astype(int)
    if np.any((c < 0) | (c >= z.shape[1]-1) | (r < 0) | (r >= z.shape[0]-1)):
        raise ValueError('Outside coarse terrain domain')
    u, v = cf-c, rf-r
    a, b, cc, d = z[r, c], z[r, c+1], z[r+1, c], z[r+1, c+1]
    if not np.isfinite(np.stack((a, b, cc, d))).all():
        raise ValueError('Coarse terrain has an uncaptured gap')
    return np.where(u+v <= 1, a*(1-u-v)+b*u+cc*v, b*(1-v)+cc*(1-u)+d*(u+v-1))


def coarse_quad_mask(z, x0, y0, cell, exclusion):
    """Keep valid source quads outside the grid-aligned replacement rectangle."""
    valid = np.isfinite(z[:-1, :-1]) & np.isfinite(z[:-1, 1:]) & np.isfinite(z[1:, :-1]) & np.isfinite(z[1:, 1:])
    xmin, ymin, xmax, ymax = exclusion
    c0, c1 = (xmin-x0)/cell, (xmax-x0)/cell
    r0, r1 = (y0-ymax)/cell, (y0-ymin)/cell
    values = np.array([c0, c1, r0, r1])
    if not np.allclose(values, np.round(values), atol=1e-8, rtol=0):
        raise ValueError('Replacement boundary must follow coarse grid vertices')
    c0, c1, r0, r1 = np.round(values).astype(int)
    if not (0 <= c0 < c1 < z.shape[1] and 0 <= r0 < r1 < z.shape[0]):
        raise ValueError('Replacement rectangle outside coarse grid')
    if not np.isfinite(z[r0:r1+1, c0:c1+1]).all():
        raise ValueError('Replacement contains missing captured source')
    valid[r0:r1, c0:c1] = False
    return valid


class CompositeTerrainSampler:
    """One surface for future render/collision exports and hydraulic cooking.

    Owner codes: 1 original coarse triangles, 2 original rapid triangles,
    3 inferred join triangles, 4 additive source-context coarse triangles,
    5 optional original-return rock solid with explicitly inferred flanks.
    These codes identify meshes, NOT measurement authority.
    """
    def __init__(self, directory, extension_directory=None, rock_cap_manifest=None):
        import hashlib
        import json
        from pathlib import Path
        import rasterio
        from south_fork_registered_mesh import RegisteredMeshSampler
        directory = Path(directory)
        self.manifest = json.loads((directory/'manifest.json').read_text())
        for name, expected in self.manifest['artifacts'].items():
            if hashlib.sha256((directory/name).read_bytes()).hexdigest() != expected:
                raise ValueError('Composite geometry artifact changed: '+name)
        with rasterio.open(directory/'coarse_bed_navd88_m.tif') as ds:
            self.coarse = ds.read(1)
        with np.load(directory/'coarse_topology.npz') as data:
            self.valid_quads = data['valid_quads']
        with np.load(directory/'troublemaker_registered_source.npz') as data:
            self.rapid = RegisteredMeshSampler({k: data[k] for k in data.files})
        with np.load(directory/'troublemaker_seam.npz') as data:
            self.seam_xyz, self.seam_faces = data['xyz_navd88_utm_m'], data['triangles']
        self.x0, self.y0 = self.manifest['grid']['first_vertex_utm_m']
        self.cell = self.manifest['grid']['cell_m']
        self.rock_union=None
        if rock_cap_manifest is not None:
            from south_fork_rock_union import SourceRockUnion
            self.rock_union=SourceRockUnion(rock_cap_manifest,Path(__file__).resolve().parents[2],
                directory/'troublemaker_registered_source.npz',self.manifest['rapid_origin_utm_m'],
                self.manifest['rapid_datum_navd88_m'])
            a,b,c,d=self.manifest['inner_boundary_utm_m']
            if (np.any(self.rock_union.lower<[a,b]) or np.any(self.rock_union.upper>[c,d])):
                raise ValueError('Rock candidate extends beyond its retained rapid terrain')
        self.supplemental_quads = None
        if extension_directory is not None:
            extension_directory = Path(extension_directory)
            extension = json.loads((extension_directory/'manifest.json').read_text())
            assert extension['completed'] and extension['base_geometry_manifest_sha256'] == hashlib.sha256((directory/'manifest.json').read_bytes()).hexdigest()
            for name, expected in extension['artifacts'].items():
                assert hashlib.sha256((extension_directory/name).read_bytes()).hexdigest() == expected
            with rasterio.open(extension_directory/'coarse_bed_navd88_m.tif') as ds:
                extended_bed = ds.read(1)
            row, col = extension['original_grid_offset_row_col']
            original = extended_bed[row:row+self.coarse.shape[0],col:col+self.coarse.shape[1]]
            finite = np.isfinite(self.coarse)
            assert np.array_equal(original[finite], self.coarse[finite])
            with np.load(extension_directory/'topology.npz') as data:
                extended_quads = data['valid_quads']
                self.supplemental_quads = data['supplemental_quads']
            assert np.all(extended_quads[row:row+self.valid_quads.shape[0],col:col+self.valid_quads.shape[1]][self.valid_quads])
            self.coarse, self.valid_quads = extended_bed, extended_quads
            self.x0, self.y0 = extension['grid']['first_vertex_utm_m']
            assert extension['grid']['cell_m'] == self.cell

    def sample(self, east, north, with_owner=False):
        east, north = np.broadcast_arrays(np.asarray(east, float), np.asarray(north, float))
        shape = east.shape
        x, y = east.ravel(), north.ravel()
        if not np.isfinite(x).all() or not np.isfinite(y).all():
            raise ValueError('Finite Cartesian queries required')
        def inside(bounds):
            a, b, c, d = bounds
            return (x >= a) & (x <= c) & (y >= b) & (y <= d)
        rapid = inside(self.manifest['inner_boundary_utm_m'])
        seam = inside(self.manifest['coarse_exclusion_boundary_utm_m']) & ~rapid
        coarse = ~rapid & ~seam
        out = np.empty(len(x))
        owner = np.empty(len(x), dtype=np.uint8)
        origin = self.manifest['rapid_origin_utm_m']
        if rapid.any():
            out[rapid] = self.rapid.sample(x[rapid]-origin[0], y[rapid]-origin[1])+self.manifest['rapid_datum_navd88_m']
            owner[rapid] = 2
        if seam.any():
            out[seam] = sample_triangles(self.seam_xyz, self.seam_faces, x[seam], y[seam])
            owner[seam] = 3
        if coarse.any():
            c, r = np.floor((x[coarse]-self.x0)/self.cell).astype(int), np.floor((self.y0-y[coarse])/self.cell).astype(int)
            if np.any((r < 0) | (r >= self.valid_quads.shape[0]) | (c < 0) | (c >= self.valid_quads.shape[1])):
                raise ValueError('Outside composite source coverage')
            if not self.valid_quads[r, c].all():
                raise ValueError('No authoritative coarse triangle at query')
            out[coarse] = sample_regular_triangles(self.coarse, self.x0, self.y0, self.cell, x[coarse], y[coarse])
            owner[coarse] = 1
            if self.supplemental_quads is not None:
                owner[coarse] += 3*self.supplemental_quads[r, c].astype(np.uint8)
        if self.rock_union is not None:
            out,changed=self.rock_union.apply(x,y,out)
            if np.any(changed&~rapid):raise ValueError('Rock union changed another terrain owner')
            owner[changed]=5
        return (out.reshape(shape), owner.reshape(shape)) if with_owner else out.reshape(shape)


def coarse_mesh_tiles(z, valid_quads, x0, y0, cell, datum, tile_quads=128):
    """Streamable source-exact mesh packets; adjacent tiles share identical edges.

    Local metre vertices avoid large-coordinate FBX float quantization. Actor
    placement supplies UTM translation separately. No simplification is applied.
    """
    if tile_quads < 1 or valid_quads.shape != (z.shape[0]-1, z.shape[1]-1):
        raise ValueError('Invalid coarse topology/tile size')
    for row in range(0, z.shape[0]-1, tile_quads):
        for col in range(0, z.shape[1]-1, tile_quads):
            mask = valid_quads[row:row+tile_quads, col:col+tile_quads]
            if not mask.any():
                continue
            nr, nc = mask.shape
            r, c = np.nonzero(mask)
            a = r*(nc+1)+c
            faces = np.vstack((np.column_stack((a, a+1, a+nc+1)),
                               np.column_stack((a+1, a+nc+2, a+nc+1))))
            ids, inverse = np.unique(faces, return_inverse=True)
            vr, vc = np.divmod(ids, nc+1)
            vertices = np.column_stack((vc*cell, -vr*cell, z[row+vr, col+vc].astype(np.float64)-datum))
            if not np.isfinite(vertices).all():
                raise ValueError('Export would invent a missing terrain vertex')
            yield dict(row=row, col=col, origin_utm_m=[x0+col*cell, y0-row*cell],
                xyz_local_m=vertices, triangles=inverse.reshape(-1, 3),
                source_grid_vertex_index=(row+vr)*z.shape[1]+col+vc)
