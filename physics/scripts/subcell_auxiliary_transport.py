"""Source-face auxiliary transport and geometric commutator, NOT full dynamics.

Use original source slopes and depth moments, not a fitted/mean-depth Gram.
These skew components still need the full cross-mode tensor, including terrain
curvature, and compatible wet/front/pressure work. Never expose them as a river
momentum rate or interpret zero work as nonlinear-model acceptance.
"""
import math
import numpy as np

from subcell_source_frames import face_section
from subcell_wet_pool_pressure import column_intervals, shared_subsegments
from subcell_wet_pool_transport import source_traces


def geometric_commutator(tangent, velocity):
    """Exact source-integrated Eulerian factor-time commutator J u.

    At fixed source points F=h D-1.5 grad(b)., F_t=eta_t D+h D_t.
    Integrating .5*h*(F^T F_t-F_t^T F) uses a=integral h^3,
    c=-1.5 integral h^2 grad(b), c_V=-3 integral h grad(b)/wet_area.
    No quadrature-node motion or arbitrary Gram square-root derivative is used.
    Moving shoreline terms vanish because this integrand contains h.
    """
    s = tangent.system
    u = s._vector(velocity)[:, 0]
    gram = np.array([pool['form']['gram'] for pool in s.partition.pools])
    a, c = gram[:, 0, 0], gram[:, 0, 1:]
    c_rate = tangent.gram_rate[:, 0, 1:]
    d, dt = s.divergence(u), tangent.divergence_rate(u)
    # Keep the two independent transpose paths; this is skew by construction.
    result = .5*(s.divergence_transpose(a*dt)
                  -tangent.transpose_rate(a*d+np.sum(c*u, axis=1))+c*dt[:, None])
    result += .25*(c_rate*d[:, None]-s.divergence_transpose(np.sum(c_rate*u, axis=1)))
    if not np.isfinite(result).all():
        raise ValueError('Source commutator exceeds represented range')
    return result[:, None, :]


def tensor_derivative_part(system, auxiliary, velocity):
    """Symmetric derivative part of N; terrain-curvature term NOT supplied.

    c=integral h^3 div(w)-1.5 integral h^2 grad(b).w uses the original
    integrated moments. Each derivative uses the actual graph coefficients
    and its exact transpose, including oblique source edges and walls.
    """
    w, z = system._vector(auxiliary)[:, 0], system._vector(velocity)[:, 0]
    gram = np.array([pool['form']['gram'] for pool in system.partition.pools])
    c = gram[:, 0, 0]*system.divergence(w)+np.sum(gram[:, 0, 1:]*w, axis=1)
    jac = np.empty((len(w), 2, 2))
    for i in range(2):
        for j in range(2):
            projected = np.zeros_like(z); projected[:, j] = z[:, i]
            jac[:, i, j] = system.divergence(projected)
    trace = jac[:, 0, 0]+jac[:, 1, 1]
    result = np.zeros_like(z)
    for i in range(2):
        for j in range(2):
            stress = c*(jac[:, j, i]+(trace if i == j else 0.))
            result[:, i] -= system.divergence_transpose(stress)[:, j]
    if not np.isfinite(result).all():
        raise ValueError('Source tensor derivative part exceeds represented range')
    return result[:, None, :]


def source_slope(partition, parent, source):
    cell = partition.patch.cells[parent]
    values = cell.bed_gradients[np.asarray(cell.source_triangle_indices) == source]
    if not len(values) or not np.all(values == values[0]):
        raise ValueError('Original source slope missing or inconsistent across fragments')
    return values[0]


def face_coupling(segment, left_form, right_form, left_slope, right_slope, speed):
    """Cubic-exact common-wet face integral of paired two-component factors.

    Integral m(s) [fL(s)^T fR(s)+.75 bL^T bR],
    f=[h,-1.5 grad(b)], b=[0,grad(b)], m=mean(h)*mean(u).n.
    Original depth intervals are used directly, including exact source datums.
    This does not supply transport over an unowned or one-sided wet front.
    """
    if not math.isfinite(speed):
        raise ValueError('Finite face-normal transport speed required')
    ls, rs = np.asarray(left_slope, float), np.asarray(right_slope, float)
    if ls.shape != (2,) or rs.shape != (2,) or not np.isfinite([ls, rs]).all():
        raise ValueError('Two original finite source slopes required')
    from subcell_source_face_section import stage_difference
    delta = stage_difference(left_form['stage_offset'], left_form['datum'],
                             right_form['stage_offset'], right_form['datum'])
    if delta < 0:
        # Integrate the shallower column and add a positive stage difference;
        # subtracting nearly equal depths would erase thin positive support.
        matrix, mass = face_coupling(segment, right_form, left_form, rs, ls, speed)
        return matrix.T, mass
    matrix, mass, active = np.zeros((3, 3)), 0., False
    nodes = (.5-np.sqrt(3)/6, .5+np.sqrt(3)/6)
    for high_end, low_end, span, width in column_intervals(
            segment, left_form['stage_offset'], left_form['datum']):
        # depth grows from a at the high bed endpoint to b at the low endpoint.
        a, b = high_end, low_end
        minimum = max(0., -delta)
        if b <= minimum:
            continue
        if a < minimum:
            width *= (b-minimum)/span
            a = minimum
        active = True
        for node in nodes:
            hl = (1-node)*a+node*b
            hr = hl+delta
            if hl <= 0 or hr <= 0 or width <= 0:
                raise ValueError('Positive shared source column exceeds represented range')
            fl = np.r_[hl, -1.5*ls]
            fr = np.r_[hr, -1.5*rs]
            bl, br = np.r_[0., ls], np.r_[0., rs]
            flux = .5*width*speed*.5*(hl+hr)
            matrix += flux*(np.outer(fl, fr)+.75*np.outer(bl, br))
            mass += flux
    if not np.isfinite(matrix).all() or not math.isfinite(mass):
        raise ValueError('Source-face coupling exceeds represented range')
    if active and speed != 0 and (mass == 0 or matrix[0, 0] == 0):
        raise ValueError('Nonzero source transport coefficient exceeds represented range; no deletion')
    return matrix, mass


class SourceAuxiliaryTransport:
    def __init__(self, system, transport_velocity):
        self.system = system
        part = system.partition
        velocity = system._vector(transport_velocity)[:, 0]
        self.faces, self.unresolved = [], []
        self.one_sided_owned_faces = 0
        self.partially_shared_owned_faces = 0

        def append(li, ri, ls, rs, pl, pr, segment, normal, source_edge=None):
            if li is None and ri is None:
                return
            if li is None or ri is None:
                owner = ri if li is None else li
                form = part.pools[owner]['form']
                area = face_section(segment).moments(form['stage_offset'], form['datum'])[0]
                if area > 0:
                    self.unresolved.append(dict(left=li, right=ri, wet_area=area,
                                                left_source=ls, right_source=rs))
                return
            lf, rf = part.pools[li]['form'], part.pools[ri]['form']
            section = face_section(segment)
            moments = [section.moments(f['stage_offset'], f['datum']) for f in (lf, rf)]
            areas = [value[0] for value in moments]
            if (areas[0] == 0) != (areas[1] == 0):
                self.one_sided_owned_faces += 1
            if moments[0][2] != moments[1][2]:
                self.partially_shared_owned_faces += 1
            speed = .5*float((velocity[li]+velocity[ri])@normal)
            matrix, mass = face_coupling(segment, lf, rf, source_slope(part, pl, ls),
                                         source_slope(part, pr, rs), speed)
            self.faces.append(dict(left=li, right=ri, matrix=matrix, mass_flux=mass,
                                   left_source=ls, right_source=rs,
                                   internal_source_edge=source_edge))

        for pl, pr, axis, _ in part.patch.faces:
            if min(pl, pr) < 0:
                continue  # Reflecting physical boundary: no advective transfer.
            for (li, ls), (ri, rs), segment in shared_subsegments(
                    source_traces(part, pl, axis, 1), source_traces(part, pr, axis, -1)):
                normal = np.eye(2)[axis]
                append(li, ri, ls, rs, pl, pr, segment, normal)
        for face in part.internal_faces:
            append(face['left'], face['right'], face['left_source'], face['right_source'],
                   face['parent'], face['parent'], face['segment'], face['normal'], face['edge_vertex_ids'])

    def factor_force(self, velocity):
        s = self.system
        u = s._vector(velocity)[:, 0]
        jet = np.column_stack((s.divergence(u), u))
        force = np.zeros_like(jet)
        for face in self.faces:
            l, r, matrix = face['left'], face['right'], face['matrix']
            force[l] += .5*matrix@jet[r]
            force[r] -= .5*matrix.T@jet[l]
        result = s.divergence_transpose(force[:, 0])+force[:, 1:]
        if not np.isfinite(result).all():
            raise ValueError('Source auxiliary factor transport exceeds represented range')
        return result[:, None, :]

    def difference_force(self, velocity):
        u = self.system._vector(velocity)[:, 0]
        result = np.zeros_like(u)
        for face in self.faces:
            l, r, flux = face['left'], face['right'], face['mass_flux']
            result[l] += .5*flux*u[r]
            result[r] -= .5*flux*u[l]
        if not np.isfinite(result).all():
            raise ValueError('Source difference transport exceeds represented range')
        return result[:, None, :]

    def scope(self):
        return dict(shared_source_faces=len(self.faces), unresolved_activation_faces=self.unresolved,
                    one_sided_owned_faces=self.one_sided_owned_faces,
                    partially_shared_owned_faces=self.partially_shared_owned_faces,
                    full_tensor_or_front_or_nonlinear_or_time_or_gameplay_accepted=False)
