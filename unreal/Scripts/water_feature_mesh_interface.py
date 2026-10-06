"""Signed nearest-mesh interface with explicitly undefined crease normals.

Angle-weighted sign follows Baerentzen/Aanaes (2005), not smoothed render
normals: https://www2.imm.dtu.dk/pubdb/edoc/imm3578.pdf.
Requires a closed consistently outward-oriented non-self-intersecting mesh.
Topology/positive total volume checks below do NOT prove non-self-intersection
or the orientation of each disconnected component. No welding/reorientation.
"""
from collections import defaultdict
import numpy as np

from water_feature_surface_mac import SurfaceMacField


def closest_triangle(point, triangle):
    """Independent float64 point/plane and three bounded-segment minimization."""
    p, t = np.asarray(point, float), np.asarray(triangle, float)
    a, b = t[1]-t[0], t[2]-t[0]
    normal = np.cross(a, b)
    area_squared = float(normal @ normal)
    if area_squared <= 0:
        raise ValueError('Zero-area triangle')
    normal /= np.sqrt(area_squared)
    plane = p-((p-t[0]) @ normal)*normal
    # Area-based barycentric coordinates avoid the ill-conditioned Gram
    # determinant subtraction on existing tiny positive-area triangles.
    bary = np.array([np.cross(t[1]-plane, t[2]-plane) @ normal,
                     np.cross(t[2]-plane, t[0]-plane) @ normal,
                     np.cross(t[0]-plane, t[1]-plane) @ normal])/np.sqrt(area_squared)
    candidates = [plane] if np.all(bary >= 0) else []
    for i, j in ((0, 1), (1, 2), (2, 0)):
        edge = t[j]-t[i]
        length_squared = float(edge @ edge)
        if length_squared <= 0:
            raise ValueError('Zero-length triangle edge')
        fraction = np.clip((p-t[i]) @ edge/length_squared, 0., 1.)
        candidates.append(t[i]+fraction*edge)
    return min(candidates, key=lambda q: float(np.sum((p-q)**2)))


def brute_nearest(vertices, triangles, point):
    """Small independent geometric controls only; native cases use a BVH."""
    points = [closest_triangle(point, vertices[t]) for t in triangles]
    index = min(range(len(points)), key=lambda i: float(np.sum((point-points[i])**2)))
    return points[index], index


class MeshInterface:
    def __init__(self, vertices, triangles, nearest, maximum_distance=.001,
                 allowed_faces=None, feature_tolerance=1e-8):
        self.vertices = np.array(vertices, float, copy=True)
        self.triangles = np.array(triangles, np.int64, copy=True)
        if (self.vertices.ndim != 2 or self.vertices.shape[1] != 3
                or not np.isfinite(self.vertices).all() or self.triangles.ndim != 2
                or self.triangles.shape[1] != 3 or len(self.triangles) < 4
                or np.any(self.triangles < 0) or np.any(self.triangles >= len(self.vertices))
                or not np.isfinite(maximum_distance) or maximum_distance <= 0
                or not np.isfinite(feature_tolerance) or not 0 < feature_tolerance < .01):
            raise ValueError('Finite closed triangle geometry and bounded sampling settings required')
        xyz = self.vertices[self.triangles]
        cross = np.cross(xyz[:, 1]-xyz[:, 0], xyz[:, 2]-xyz[:, 0])
        self.double_area = np.linalg.norm(cross, axis=1)
        if np.any(self.double_area <= 0):
            raise ValueError('Zero-area geometry is not repaired')
        self.normals = cross/self.double_area[:, None]
        edges, links = defaultdict(list), defaultdict(lambda: defaultdict(set))
        self.vertex_normals = np.zeros_like(self.vertices)
        self.vertex_faces = defaultdict(list)
        for face, ids in enumerate(self.triangles):
            for i, j in ((0, 1), (1, 2), (2, 0)):
                u, v = int(ids[i]), int(ids[j])
                edges[tuple(sorted((u, v)))].append((face, u < v))
            for corner in range(3):
                u, v, w = (int(ids[(corner+k)%3]) for k in range(3))
                va, vb = self.vertices[v]-self.vertices[u], self.vertices[w]-self.vertices[u]
                angle = np.arctan2(np.linalg.norm(np.cross(va, vb)), va @ vb)
                self.vertex_normals[u] += angle*self.normals[face]
                self.vertex_faces[u].append(face)
                links[u][v].add(w)
                links[u][w].add(v)
        self.edge_normals = {}
        self.edge_faces = {}
        for key, incident in edges.items():
            if len(incident) != 2 or incident[0][1] == incident[1][1]:
                raise ValueError('Closed consistently oriented edges required')
            self.edge_normals[key] = self.normals[incident[0][0]]+self.normals[incident[1][0]]
            self.edge_faces[key] = [item[0] for item in incident]
        for neighbors in links.values():
            if any(len(adjacent) != 2 for adjacent in neighbors.values()):
                raise ValueError('Manifold vertex link required')
            visited, pending = set(), [next(iter(neighbors))]
            while pending:
                vertex = pending.pop()
                if vertex not in visited:
                    visited.add(vertex)
                    pending.extend(neighbors[vertex]-visited)
            if len(visited) != len(neighbors):
                raise ValueError('Disconnected vertex link')
        centered = xyz-self.vertices.mean(axis=0)
        self.volume = float(np.sum(np.einsum('ij,ij->i', centered[:, 0],
                            np.cross(centered[:, 1], centered[:, 2])))/6)
        if self.volume <= 0:
            raise ValueError('Positive outward-oriented total volume required')
        self.allowed = np.ones(len(xyz), bool) if allowed_faces is None else np.asarray(allowed_faces, bool).copy()
        if self.allowed.shape != (len(xyz),):
            raise ValueError('One explicit free-surface allowance per triangle required')
        self.nearest, self.maximum_distance, self.feature_tolerance = nearest, maximum_distance, feature_tolerance
        self.vertices.flags.writeable = self.triangles.flags.writeable = False

    def sample(self, point):
        p = np.asarray(point, float)
        if p.shape != (3,) or not np.isfinite(p).all():
            raise ValueError('Finite 3D query required')
        hit = self.nearest(p)
        if hit is None:
            return None
        q, face = hit
        q = np.asarray(q, float)
        if q.shape != (3,) or not np.isfinite(q).all() or not 0 <= face < len(self.triangles):
            raise ValueError('Invalid nearest-surface result')
        delta, ids = p-q, self.triangles[face]
        distance = float(np.linalg.norm(delta))
        if distance > self.maximum_distance or not self.allowed[face]:
            return None
        xyz, normal = self.vertices[ids], self.normals[face]
        bary = np.array([np.cross(xyz[1]-q, xyz[2]-q) @ normal,
                         np.cross(xyz[2]-q, xyz[0]-q) @ normal,
                         np.cross(xyz[0]-q, xyz[1]-q) @ normal])/self.double_area[face]
        if abs(float(bary.sum())-1) > 1e-6 or np.min(bary) < -self.feature_tolerance:
            raise ValueError('Nearest point is not in the claimed native triangle')
        tolerance = self.feature_tolerance
        if np.max(bary) >= 1-tolerance:
            vertex = int(ids[int(np.argmax(bary))])
            feature, pseudo = 'vertex', self.vertex_normals[vertex]
            incident = self.vertex_faces[vertex]
        elif np.min(bary) <= tolerance:
            zero = int(np.argmin(bary))
            key = tuple(sorted(int(ids[i]) for i in range(3) if i != zero))
            feature, pseudo = 'edge', self.edge_normals[key]
            incident = self.edge_faces[key]
        else:
            feature, pseudo = 'face', normal
            incident = [face]
        direction = float(delta @ pseudo)
        if distance > 1e-12 and abs(direction) <= np.linalg.norm(pseudo)*distance*1e-12:
            return None  # Unresolved sign, no arbitrary air/liquid assignment.
        sign = -1 if direction < 0 else 1
        gradient = sign*delta/distance if distance > 1e-12 else None
        if distance <= 1e-12 and np.all(self.normals[incident] @ self.normals[incident[0]] > 1-1e-12):
            # An internal coplanar triangulation edge is not a physical crease.
            gradient = pseudo/np.linalg.norm(pseudo)
        return dict(phi_m=sign*distance, gradient=gradient, feature=feature,
                    triangle=int(face), closest_m=q, barycentric=bary)

    def surface(self, position):
        sample = self.sample(position)
        if sample is None or sample['gradient'] is None:
            return None  # A crease/vertex has no unique on-surface force normal.
        return sample['phi_m'], sample['gradient']


class RenderMeshMacField(SurfaceMacField):
    """NEW frozen mesh interface plus the still-inferred one-sided MAC fit.

    Strict native interior support and narrow-band/solid checks remain.
    Snapshot geometry/velocity are not given artificial temporal support.
    """
    def __init__(self, *args, interface, **kwargs):
        super().__init__(*args, **kwargs)
        self.interface = interface

    def surface(self, position):
        if super().surface(position) is None:
            return None
        return self.interface.surface(position)

    def sample(self, position, interface_tolerance_cells=1e-6):
        value = super().sample(position, interface_tolerance_cells)
        if value is not None:
            value[1]['constraint_surface'] = 'Actual unchanged rendered mesh, angle-weighted signed nearest distance'
            value[1]['native_base_phi_m'] = SurfaceMacField.surface(self, position)[0]
        return value
