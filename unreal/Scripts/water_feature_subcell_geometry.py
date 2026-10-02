"""Closed-triangle mesh sections and geometric MAC-face apertures.

No interpolated distance field, wall inflation or fluid-surface clipping.
Planar polygon operations use float64; geometric inputs remain unchanged.
This is boundary geometry, not yet a complete coupled liquid solver.
"""
from collections import defaultdict
import numpy as np


def signed_area(polygon):
    p = np.asarray(polygon, float)
    if len(p) < 3:
        return 0.
    # Translate before shoelace to avoid large absolute-coordinate cancellation.
    p = p-p[0]
    return float(np.sum(p[:, 0]*np.roll(p[:, 1], -1)-p[:, 1]*np.roll(p[:, 0], -1))/2)


def section_mesh(vertices, triangles, axis, plane):
    """Slice the CLOSED solid, including exactly coplanar surface patches.

    Ring groups use even-odd parity (including holes); coplanar triangle patches
    are separate union groups. Shared edge IDs reuse one calculated endpoint,
    so no epsilon weld or movement of input vertices is needed. Reject branching
    sections instead of inventing a polygon through a degenerate saddle.
    """
    v = np.asarray(vertices, float); t = np.asarray(triangles)
    if (v.ndim != 2 or v.shape[1] != 3 or t.ndim != 2 or t.shape[1] != 3
            or not np.issubdtype(t.dtype, np.integer) or not len(t)
            or t.min() < 0 or t.max() >= len(v) or axis not in (0, 1, 2)
            or not np.isfinite(v).all() or not np.isfinite(plane)):
        raise ValueError('Finite actual triangular mesh and Cartesian slice required')
    if np.any(np.linalg.norm(np.cross(v[t[:, 1]]-v[t[:, 0]],
                                      v[t[:, 2]]-v[t[:, 0]]), axis=1) == 0):
        raise ValueError('Degenerate source triangles do not define a closed solid')
    edges = np.sort(np.concatenate((t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]])), axis=1)
    _, counts = np.unique(edges, axis=0, return_counts=True)
    if np.any(counts != 2):
        raise ValueError('Source mesh must be closed with exactly two triangles per edge')
    other = [a for a in range(3) if a != axis]
    distances = v[:, axis]-plane; nodes = {}; segments = set(); patches = []
    candidates = t[(distances[t].min(1) <= 0) & (distances[t].max(1) >= 0)]
    for tri in candidates:
        values = distances[tri]
        if np.all(values == 0):
            patch = v[tri][:, other]
            if signed_area(patch) != 0:
                patches.append([patch])
            continue
        endpoints = set()
        for a, b in zip(tri, np.roll(tri, -1)):
            a, b = int(a), int(b)
            if distances[a] == 0:
                key = ('v', a); nodes[key] = v[a, other].copy(); endpoints.add(key)
            if distances[a]*distances[b] < 0:
                a, b = sorted((a, b)); key = ('e', a, b)
                if key not in nodes:
                    fraction = distances[a]/(distances[a]-distances[b])
                    nodes[key] = (v[a]+fraction*(v[b]-v[a]))[other]
                endpoints.add(key)
        if len(endpoints) == 2:
            a, b = sorted(endpoints)
            if not np.array_equal(nodes[a], nodes[b]):
                segments.add((a, b))
        elif len(endpoints) > 2:
            raise ValueError('Unresolved nonplanar/branching triangle section')
    adjacency = defaultdict(set)
    for a, b in segments:
        adjacency[a].add(b); adjacency[b].add(a)
    if any(len(neighbors) != 2 for neighbors in adjacency.values()):
        raise ValueError('Nonclosed/branching section; preserve source for review')
    remaining = set(segments); rings = []
    while remaining:
        a, b = min(remaining); start = a; previous = a; current = b; ring = [nodes[a]]
        remaining.remove((a, b))
        for _ in range(len(segments)+1):
            if current == start:
                break
            ring.append(nodes[current])
            following = next(x for x in adjacency[current] if x != previous)
            edge = tuple(sorted((current, following)))
            if edge not in remaining:
                raise ValueError('Self-touching/unresolved section loop')
            remaining.remove(edge); previous, current = current, following
        else:
            raise ValueError('Section traversal failed')
        polygon = np.asarray(ring)
        if signed_area(polygon) != 0:
            rings.append(polygon)
    groups = ([rings] if rings else [])+patches
    return groups, dict(crossing_triangles=len(candidates), intersection_segments=len(segments),
                        closed_rings=len(rings), coplanar_patches=len(patches), moved_vertices=False)


def clip_ring(polygon, lower, upper):
    """Clip a ring to an axis-aligned rectangle; retain zero-width connectors.

    A concave ring can become disconnected. Connectors on clip boundaries have
    zero area and cancel in even-odd sweep; do not replace with its convex hull.
    """
    p = np.asarray(polygon, float)
    for axis, bound, sign in ((0, lower[0], 1), (0, upper[0], -1),
                              (1, lower[1], 1), (1, upper[1], -1)):
        if len(p) == 0:
            break
        out = []
        for a, b in zip(p, np.roll(p, -1, axis=0)):
            da = sign*(a[axis]-bound); db = sign*(b[axis]-bound)
            if da >= 0:
                out.append(a)
            if (da < 0 <= db) or (db < 0 <= da):
                point = a+(da/(da-db))*(b-a); point[axis] = bound
                out.append(point)
        p = np.asarray(out, float).reshape(-1, 2)
    return p


def union_area(groups, lower, upper):
    """Area of a union of even-odd ring groups within one physical MAC face.

    Vertical sweep events include all endpoints and crossing edges. Between
    consecutive events union interval lengths are linear; two interior samples
    integrate that length exactly (up to float64), not midpoint occupancy.
    """
    lo = np.asarray(lower, float); hi = np.asarray(upper, float)
    if lo.shape != (2,) or hi.shape != (2,) or not np.isfinite([lo, hi]).all() or np.any(hi <= lo):
        raise ValueError('Positive finite 2D rectangle required')
    edges_by_group = []; all_edges = []; events = [lo[0], hi[0]]
    for rings in groups:
        edges = []
        for ring in rings:
            p = np.asarray(ring, float)
            if p.ndim != 2 or p.shape[1] != 2 or len(p) < 3 or not np.isfinite(p).all():
                raise ValueError('Finite polygon rings required')
            if np.any(p.max(0) < lo) or np.any(p.min(0) > hi):
                continue
            p = clip_ring(p, lo, hi)
            if len(p) < 3:
                continue
            events.extend(p[:, 0].tolist())
            for a, b in zip(p, np.roll(p, -1, axis=0)):
                if a[0] == b[0]:
                    continue
                if b[0] < a[0]:
                    a, b = b, a
                edge = (float(a[0]), float(b[0]), float((b[1]-a[1])/(b[0]-a[0])), a.copy())
                edges.append(edge); all_edges.append(edge)
        if edges:
            edges_by_group.append(edges)
    if not all_edges:
        return 0.
    for i, a in enumerate(all_edges):
        for b in all_edges[i+1:]:
            left = max(a[0], b[0]); right = min(a[1], b[1])
            slope = a[2]-b[2]
            if right <= left or slope == 0:
                continue
            difference = (a[3][1]+a[2]*(left-a[3][0]))-(b[3][1]+b[2]*(left-b[3][0]))
            crossing = left-difference/slope
            if left < crossing < right:
                events.append(crossing)
    events = np.unique(events)

    def length_at(x, left, right):
        intervals = []
        for edges in edges_by_group:
            # Adjacent float64 events need not have a representable midpoint.
            # Select edges by the whole open slab, not by a rounded sample x.
            hits = sorted(e[3][1]+e[2]*(x-e[3][0]) for e in edges
                          if e[0] <= left and e[1] >= right)
            if len(hits) % 2:
                raise ValueError('Odd polygon crossing count; do not fill missing geometry')
            intervals.extend((hits[j], hits[j+1]) for j in range(0, len(hits), 2))
        if not intervals:
            return 0.
        intervals.sort(); a, b = intervals[0]; length = 0.
        for c, d in intervals[1:]:
            if c <= b:
                b = max(b, d)
            else:
                length += b-a; a, b = c, d
        return length+b-a

    area = 0.
    for a, b in zip(events, events[1:]):
        if b > a:
            area += (b-a)*(length_at(a+.25*(b-a), a, b)+length_at(a+.75*(b-a), a, b))/2
    total = float(np.prod(hi-lo)); tolerance = 1e-10*total*max(1, len(all_edges))
    if area < -tolerance or area > total+tolerance:
        raise ValueError('Union area outside physical rectangle')
    return min(total, max(0., float(area)))


def face_apertures(meshes, shape, origin, cell_m, progress=None):
    """All N+1 plane faces per axis; not the shortened native MAC storage.

    Geometric solid closures block coplanar faces. No guessed exterior half-cell
    distance values, volume fit, prescribed fluid state or native flag stomping.
    """
    origin = np.asarray(origin, float)
    if (len(shape) != 3 or any(n < 2 for n in shape) or origin.shape != (3,)
            or not np.isfinite(origin).all() or not np.isfinite(cell_m) or cell_m <= 0):
        raise ValueError('Positive 3D lattice required')
    arrays = []; rows = []
    for axis in range(3):
        other = [i for i in range(3) if i != axis]
        dims = list(shape); dims[axis] += 1; area = np.empty(dims, float)
        for index in range(shape[axis]+1):
            plane = origin[axis]+index*cell_m; groups = []; sources = []
            for name, (v, t) in meshes.items():
                section, proof = section_mesh(v, t, axis, plane)
                groups.extend(section); sources.append(dict(name=name, **proof))
            bounds = [(np.vstack(rings).min(0), np.vstack(rings).max(0), rings) for rings in groups]
            for j in range(shape[other[0]]):
                for k in range(shape[other[1]]):
                    lo = origin[other]+np.array([j, k])*cell_m; hi = lo+cell_m
                    relevant = [rings for a, b, rings in bounds if not (np.any(b < lo) or np.any(a > hi))]
                    coordinate = [0, 0, 0]; coordinate[axis] = index
                    coordinate[other[0]] = j; coordinate[other[1]] = k
                    # Floating world-coordinate subtraction can differ from h
                    # by ulps. Normalize the polygon measure by that SAME
                    # represented rectangle before expressing it in h^2 units.
                    # This is roundoff normalization, not a wall/volume fit.
                    blocked = union_area(relevant, lo, hi) if relevant else 0.
                    area[tuple(coordinate)] = cell_m**2*(1.-blocked/float(np.prod(hi-lo)))
            rows.append(dict(axis=axis, index=index, plane_m=float(plane), sources=sources))
            if progress is not None:
                progress(axis, index)
        arrays.append(area)
    return arrays, rows
