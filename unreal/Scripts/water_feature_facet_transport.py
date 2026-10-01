"""Straightest, constant-speed transport on an unchanged static triangle mesh.

Edge events and dihedral parallel transport replace an undefined crease
normal. This is a kinematic component, not evolving liquid/foam dynamics.
No nearest-surface lifting, averaging of folds, velocity damping or hidden
continuation at an unresolved vertex/contact boundary. Event points must be
kept in native animation keys; skipping them makes off-surface chords.
"""
import numpy as np


class FacetTransport:
    def __init__(self, interface):
        self.interface = interface
        vertices, triangles = interface.vertices, interface.triangles
        xyz = vertices[triangles]
        self.gradients = np.stack([np.cross(interface.normals, xyz[:, (i+2)%3]-xyz[:, (i+1)%3])
                                   /interface.double_area[:, None] for i in range(3)], axis=1)
        edges = {}
        self.adjacent = np.full(triangles.shape, -1, np.int64)
        for face, ids in enumerate(triangles):
            for opposite in range(3):
                key = tuple(sorted(int(ids[i]) for i in range(3) if i != opposite))
                if key in edges:
                    old_face, old_opposite = edges.pop(key)
                    self.adjacent[face, opposite] = old_face
                    self.adjacent[old_face, old_opposite] = face
                else:
                    edges[key] = face, opposite
        if edges or np.any(self.adjacent < 0):
            raise ValueError('Validated closed interface adjacency required')

    def barycentric(self, point, face):
        xyz = self.interface.vertices[self.interface.triangles[face]]
        # Affine barycentrics from the independently defined area gradients.
        bary = self.gradients[face] @ (point-xyz[0])
        bary[0] += 1
        return bary

    def walk(self, position, velocity, face, seconds, maximum_crossings=4096,
             tolerance_m=1e-10):
        p, v = np.array(position, float, copy=True), np.array(velocity, float, copy=True)
        if (p.shape != (3,) or v.shape != (3,) or not np.isfinite(p).all() or not np.isfinite(v).all()
                or not isinstance(face, (int, np.integer)) or not 0 <= face < len(self.adjacent)
                or not np.isfinite(seconds) or seconds < 0 or not isinstance(maximum_crossings, int)
                or maximum_crossings < 1 or not np.isfinite(tolerance_m) or tolerance_m <= 0):
            raise ValueError('Finite matched position/velocity, face and bounded trace settings required')
        speed = float(np.linalg.norm(v))
        xyz = self.interface.vertices[self.interface.triangles[face]]
        plane_error = abs(float((p-xyz[0]) @ self.interface.normals[face]))
        if plane_error > tolerance_m or np.min(self.barycentric(p, face)) < -1e-9:
            raise ValueError('Initial point not on claimed triangle; no hidden projection')
        if abs(float(v @ self.interface.normals[face])) > 1e-10*max(speed, 1.):
            raise ValueError('Initial velocity must already be tangent')
        if not self.interface.allowed[face]:
            raise ValueError('Initial triangle is not an allowed free surface')
        path = [dict(seconds=0., position_m=p.tolist(), face=int(face))]
        events, elapsed, remaining, status = [], 0., float(seconds), 'complete'
        maximum_plane_error, maximum_speed_error = plane_error, 0.
        while speed > 0 and remaining > 0:
            bary = self.barycentric(p, face)
            rates = self.gradients[face] @ v
            # Time to each outgoing edge. Negative barycentrics within the
            # checked roundoff tolerance may yield a zero-time edge event, NOT
            # spatial clamping or a move back onto the surface.
            times = np.full(3, np.inf)
            outgoing = rates < -1e-14*max(speed, 1.)
            times[outgoing] = np.maximum(0., -bary[outgoing]/rates[outgoing])
            crossing_time = float(times.min())
            if crossing_time > remaining:
                p += remaining*v
                # All requested integration time has been consumed. Preserve
                # its exact input timestamp rather than summing edge intervals
                # into a terminal time one ulp short/long. Coordinates are not
                # clamped or advanced beyond the remaining integration time.
                elapsed = float(seconds)
                remaining = 0.
                path.append(dict(seconds=elapsed, position_m=p.tolist(), face=int(face)))
                break
            if not np.isfinite(crossing_time):
                raise ValueError('No outgoing edge for finite nonzero tangent motion')
            p += crossing_time*v
            remaining -= crossing_time
            elapsed = float(seconds)-remaining
            path.append(dict(seconds=elapsed, position_m=p.tolist(), face=int(face)))
            tied = np.flatnonzero(np.abs(times-crossing_time)*speed <= tolerance_m)
            if len(tied) != 1 or np.count_nonzero(np.abs(self.barycentric(p, face)) <= 1e-9) >= 2:
                status = 'unresolved vertex event'
                break
            opposite = int(tied[0])
            next_face = int(self.adjacent[face, opposite])
            if not self.interface.allowed[next_face]:
                status = 'reached contact/non-free-surface triangle'
                break
            if len(events) >= maximum_crossings:
                status = 'crossing limit reached'
                break
            edge_ids = [int(self.interface.triangles[face, i]) for i in range(3) if i != opposite]
            edge = self.interface.vertices[edge_ids[1]]-self.interface.vertices[edge_ids[0]]
            edge /= np.linalg.norm(edge)
            old_normal, next_normal = self.interface.normals[[face, next_face]]
            cosine = float(old_normal @ next_normal)
            sine = float(edge @ np.cross(old_normal, next_normal))
            if abs(cosine*cosine+sine*sine-1) > 1e-8:
                raise ValueError('Unresolved dihedral rotation')
            rotated = v*cosine+np.cross(edge, v)*sine+edge*float(edge @ v)*(1-cosine)
            tangent_error = abs(float(rotated @ next_normal))
            if tangent_error > 1e-8*max(speed, 1.):
                raise ValueError('Edge transport lost tangent direction')
            maximum_speed_error = max(maximum_speed_error, abs(float(np.linalg.norm(rotated))-speed))
            next_xyz = self.interface.vertices[self.interface.triangles[next_face]]
            plane_error = abs(float((p-next_xyz[0]) @ next_normal))
            maximum_plane_error = max(maximum_plane_error, plane_error)
            if plane_error > tolerance_m or np.min(self.barycentric(p, next_face)) < -1e-8:
                raise ValueError('Edge event lost actual shared geometry')
            if np.min(self.barycentric(p, next_face)+min(remaining, 1e-7)*self.gradients[next_face] @ rotated) < -1e-8:
                raise ValueError('Rotated direction does not enter the adjacent facet')
            events.append(dict(seconds=elapsed, from_face=int(face), to_face=next_face,
                               edge_vertices=edge_ids, cosine=cosine, sine=sine,
                               position_m=p.tolist()))
            v, face = rotated, next_face
        if speed == 0 and seconds > 0:
            elapsed, remaining = float(seconds), 0.
            path.append(dict(seconds=elapsed, position_m=p.tolist(), face=int(face)))
        # Validate endpoint without changing its coordinates.
        xyz = self.interface.vertices[self.interface.triangles[face]]
        maximum_plane_error = max(maximum_plane_error, abs(float((p-xyz[0]) @ self.interface.normals[face])))
        if maximum_plane_error > tolerance_m or np.min(self.barycentric(p, face)) < -1e-8:
            raise ValueError('Final path lost actual facet contact')
        return dict(complete=status == 'complete', status=status, position_m=p.tolist(),
            velocity_mps=v.tolist(), face=int(face), consumed_seconds=elapsed,
            remaining_seconds=remaining, requested_seconds=float(seconds), path=path,
            crossings=events, speed_mps=speed, maximum_speed_error_mps=maximum_speed_error,
            maximum_facet_plane_error_m=maximum_plane_error, accepted=False,
            scope='Static-mesh constant-speed straightest-path component. No force/flow integration, water evolution, foam interactions or hydraulic acceptance. Events are required playback keys; stops are explicit, not invented continuation.')
