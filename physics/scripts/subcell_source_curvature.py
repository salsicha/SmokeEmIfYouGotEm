"""Weak original-triangle slope-jump curvature for the nonlinear tensor.

Piecewise affine terrain has zero within-triangle Hessian, but a nonzero
Hessian measure on original shared edges. Same-water-region edges therefore
must be retained. This operator is research, not full wet/front/scene acceptance.
"""
from fractions import Fraction as F
import math
import numpy as np

from subcell_source_face_section import SourceFaceSection, stage_difference
from subcell_source_region_faces import clipped_edge
from subcell_wet_pool_pressure import column_intervals, shared_subsegments
from subcell_wet_pool_transport import source_traces


def original_gradient(partition, parent, source):
    cell = partition.patch.cells[parent]
    if not hasattr(cell, 'fragments'):
        raise ValueError('Curvature requires original exact-source gradients')
    gradients = {fragment.gradient for fragment in cell.fragments if fragment.source_id == source}
    if len(gradients) != 1:
        raise ValueError('Original source gradient missing or inconsistent')
    return next(iter(gradients))


def common_depth_moments(segment, left, right):
    """Cubic-safe two-node integration of mean-depth powers on common wet support."""
    delta = stage_difference(left['stage_offset'], left['datum'], right['stage_offset'], right['datum'])
    if delta < 0:
        return common_depth_moments(segment, right, left)
    moments = np.zeros(2)
    for a, b, span, width in column_intervals(segment, left['stage_offset'], left['datum']):
        if b <= 0:
            continue
        if a < 0:
            width *= b/span
            a = 0.
        for point in (.5-np.sqrt(3)/6, .5+np.sqrt(3)/6):
            h = (1-point)*a+point*b+.5*delta
            first, second = .5*width*h, .5*width*h*h
            if min(first, second) <= 0 or not np.isfinite([first, second]).all():
                raise ValueError('Positive curvature weight exceeds represented range; no deletion')
            moments += [first, second]
    return moments


class SourceCurvatureTensor:
    def __init__(self, system):
        self.system = system
        part = system.partition
        if not all(hasattr(cell, 'fragments') for cell in part.patch.cells):
            raise ValueError('Curvature requires original exact-source geometry')
        self.edges, self.unresolved = [], []
        self.same_region_edges = 0

        def append(pl, pr, li, ri, left_source, right_source, section, tangent, normal, kind, ids=None):
            gl = original_gradient(part, pl, left_source)
            gr = original_gradient(part, pr, right_source)
            jump = tuple(b-a for a, b in zip(gl, gr))
            if jump == (0, 0):
                return
            # C0 affine source triangles have identical tangential slope.
            # Check with the original exact rationals before using the normal
            # rank-one form; no projection of inconsistent source geometry.
            if sum(a*b for a, b in zip(jump, tangent)) != 0:
                raise ValueError('Original source slopes disagree along their shared edge')
            if li is None and ri is None:
                return
            if li is None or ri is None:
                owner = ri if li is None else li
                form = part.pools[owner]['form']
                if section.moments(form['stage_offset'], form['datum'])[0] > 0:
                    self.unresolved.append(dict(left=li, right=ri, left_source=left_source,
                                                right_source=right_source, kind=kind))
                return
            lf, rf = part.pools[li]['form'], part.pools[ri]['form']
            m1, m2 = common_depth_moments(section, lf, rf)
            if m1 == 0:
                return
            jump_normal = float(np.asarray(tuple(map(float, jump)))@normal)
            if jump_normal == 0 or not math.isfinite(jump_normal):
                raise ValueError('Nonzero original curvature exceeds represented range')
            hessian = jump_normal*np.outer(normal, normal)
            self.edges.append(dict(left=li, right=ri, left_source=left_source,
                right_source=right_source, depth_integral=m1, squared_depth_integral=m2,
                mean_slope=np.array([float((a+b)/2) for a, b in zip(gl, gr)]),
                hessian=hessian, normal=normal.copy(), section=section,
                parent_left=pl, parent_right=pr, kind=kind, source_edge=ids))
            self.same_region_edges += int(li == ri)

        # Slopes may change across a grid face only when that face lies on an
        # actual source edge. Equal-source pairs have an exactly zero jump.
        for pl, pr, axis, _ in part.patch.faces:
            if min(pl, pr) < 0:
                continue
            for (li, ls), (ri, rs), segment in shared_subsegments(
                    source_traces(part, pl, axis, 1), source_traces(part, pr, axis, -1)):
                append(pl, pr, li, ri, ls, rs, segment, tuple(F(int(j != axis)) for j in range(2)),
                       np.eye(2)[axis], 'cartesian-source-jump')

        source = part.sampler
        for parent, cell in enumerate(part.patch.cells):
            owners = {int(s): i for i in part.parent_pools[parent] for s in part.pools[i]['source_triangle_indices']}
            adjacency = {}
            for face in sorted(set(map(int, cell.source_triangle_indices))):
                vertices = source.faces[face]
                for j in range(3):
                    edge = tuple(sorted((int(vertices[j]), int(vertices[(j+1)%3]))))
                    adjacency.setdefault(edge, []).append(face)
            row, col = divmod(parent, part.patch.shape[1])
            center = part.origin+part.patch.spacing*[col, row]
            for edge, faces in adjacency.items():
                if len(faces) > 2:
                    raise ValueError('Nonmanifold original curvature edge')
                if len(faces) != 2:
                    continue
                ls, rs = faces
                clipped = clipped_edge(source, edge, center, part.patch.spacing, with_exact=True)
                if clipped is None:
                    continue
                _, length, exact = clipped
                section = SourceFaceSection([[(F(0), exact[0][2]), (F(length), exact[1][2])]])
                a, b = source.xyz[list(edge)]
                dx, dy = F(float(b[0]))-F(float(a[0])), F(float(b[1]))-F(float(a[1]))
                third = source.xyz[next(int(v) for v in source.faces[ls] if int(v) not in edge)]
                cross = dx*(F(float(third[1]))-F(float(a[1])))-dy*(F(float(third[0]))-F(float(a[0])))
                if cross == 0:
                    raise ValueError('Degenerate original curvature triangle')
                normal = np.array([float(dy), -float(dx)])
                normal /= math.hypot(*normal)
                if cross < 0:
                    normal *= -1
                append(parent, parent, owners.get(ls), owners.get(rs), ls, rs, section,
                       (dx, dy), normal, 'internal-source-jump', list(edge))

    def action(self, auxiliary, velocity):
        s = self.system
        w, z = s._vector(auxiliary)[:, 0], s._vector(velocity)[:, 0]
        d = s.divergence(w)
        result = np.zeros_like(z)
        for edge in self.edges:
            l, r = edge['left'], edge['right']
            w_trace, z_trace = .5*(w[l]+w[r]), .5*(z[l]+z[r])
            d_trace = .5*(d[l]+d[r])
            coefficient = (-1.5*edge['squared_depth_integral']*d_trace
                           +3*edge['depth_integral']*float(edge['mean_slope']@w_trace))
            force = coefficient*(edge['hessian']@z_trace)
            result[l] += .5*force
            result[r] += .5*force
        if not np.isfinite(result).all():
            raise ValueError('Original source curvature force exceeds represented range')
        return result[:, None, :]

    def scope(self):
        return dict(wet_curvature_edges=len(self.edges), same_region_curvature_edges=self.same_region_edges,
                    unresolved_curvature_fronts=self.unresolved,
                    full_force_or_front_or_time_or_gameplay_accepted=False)
