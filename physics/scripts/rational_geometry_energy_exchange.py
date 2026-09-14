"""Local reconstruction-work transfer for the SAME positive two-pole energy.

Each factor row is differentiated on its own local depth stencil. Work is
transferred from that row to the participating depth cells, without a global
flux fit or altering the physical rates. This completes energy bookkeeping,
NOT a conservative hydrodynamic update. No dry/open/gameplay qualification.
"""
from fractions import Fraction as F
import numpy as np
from reverse_rational_depth_gradient import Tape, positive, factor_depth_gradient
from smooth_pressure_reverse import polynomial, smooth_coefficient_reverse
from smooth_pressure_geometry import SmoothPressureGeometry, SmoothPressureGeometryRate
from rational_dual_energy_reference import factor_direction
from patch_pressure_preconditioner import PatchPressureSystem
from rational_primal_energy import evaluate, depth_gradient
from rational_auxiliary_energy_work import local_work


class LocalDepth(dict):
    def __init__(self, tape, g, ht):
        super().__init__()
        self.tape, self.g, self.ht = tape, g, ht

    def __missing__(self, p):
        node = self.tape.node(float(self.g.h[p]), float(self.ht[p]))
        self[p] = node
        return node


def neighbor(p, axis, offset, shape):
    q = list(p)
    q[axis] = (p[axis]+offset) % shape[axis]
    return tuple(q)


def face_nodes(depth, g, axis, p):
    q = neighbor(p, axis, 1, g.h.shape)
    hi, hj = depth[p], depth[q]
    dhi, dei = polynomial(depth, g, axis, p)
    dhj, dej = polynomial(depth, g, axis, q)
    ha, hb = hi+dhi/2, hj-dhj/2
    jump = F(float(g.bed[q]))-F(float(g.bed[p]))-(dei-dhi+dej-dhj)/2
    fa, fb = positive(ha-positive(jump)), positive(hb-positive(-jump))

    def cut(height, retained):
        r = retained/height
        return r*r*(3-2*r), -height*r*r*(1-r)

    aa, ca = cut(ha, fa)
    ab, cb = cut(hb, fb)
    own, other = hi/(hi+hj), hj/(hi+hj)
    nodes = dict(aa=aa, ab=ab, own=own, other=other, shared_b=own*other*(cb-ca))
    # The geometry stores rounded coefficient values, but its prescribed
    # analytic derivative is the exact-polynomial derivative (not round()).
    return {key:depth.tape.node(float(node.value), node.direction, ((node,F(1)),))
            for key, node in nodes.items()}


def geometry_exchange(g, mass_direction, poles):
    if not isinstance(g, SmoothPressureGeometry):
        raise ValueError('Positive periodic smooth geometry required')
    ht = np.asarray(mass_direction, dtype=float)
    if ht.shape != g.h.shape or not np.isfinite(ht).all():
        raise ValueError('Finite registered depth direction required')
    systems = [PatchPressureSystem(g, pole['beta']) for pole in poles]
    factors = [(system.w(pole['normalized_auxiliary_velocity']),
                system.v(pole['normalized_auxiliary_velocity']))
               for system, pole in zip(systems, poles)]
    gradient = np.zeros_like(g.h)
    explicit = np.zeros_like(g.h)
    exchange = np.zeros_like(g.h)
    max_value_error = 0.
    maximum_local_depth_nodes = 0
    for p in np.ndindex(g.h.shape):
        tape = Tape()
        depth = LocalDepth(tape, g, ht)
        roots, faces = {}, {}

        def root(q):
            if q not in roots:
                hq = depth[q]
                value = F(float(np.sqrt(g.h[q])))
                partial = value/(2*hq.value)
                roots[q] = tape.node(value, partial*hq.direction, ((hq,partial),))
            return roots[q]

        def face(axis, q):
            key = axis, q
            if key not in faces:
                faces[key] = face_nodes(depth, g, axis, q)
            return faces[key]

        seeds = []
        for pole, (actual_w, actual_v) in zip(poles, factors):
            z = pole['normalized_auxiliary_velocity']
            d, e = tape.node(0), tape.node(0)
            for component, axis in enumerate((1,0)):
                ui = tape.node(float(z[p][component]))/root(p)
                e += F(float(g.edges[component]['physical_b'][p]))*ui
                if g.h.shape[axis] == 1:
                    continue
                left = neighbor(p, axis, -1, g.h.shape)
                right = neighbor(p, axis, 1, g.h.shape)
                ul = tape.node(float(z[left][component]))/root(left)
                ur = tape.node(float(z[right][component]))/root(right)
                a, b = face(axis, p), face(axis, left)
                d += (a['aa']*(a['own']*ui+a['other']*ur)
                      - b['ab']*(b['own']*ul+b['other']*ui))/F(g.dx)
                e += (a['shared_b']*(ur-ui)+b['shared_b']*(ul-ui))/F(g.dx)
            wnode = root(p)*(depth[p]*d-F(3,2)*e)
            vnode = root(p)*e
            max_value_error = max(max_value_error, abs(float(wnode.value)-actual_w[p]),
                                  abs(float(vnode.value)-actual_v[p]))
            seeds.extend(((wnode,pole['alpha']*actual_w[p]),
                          (vnode,.75*pole['alpha']*actual_v[p])))
        adjoints = tape.reverse(seeds)
        maximum_local_depth_nodes = max(maximum_local_depth_nodes, len(depth))
        for q, node in depth.items():
            derivative = adjoints[node.index]
            work = derivative*ht[q]
            gradient[q] += derivative
            explicit[p] += work
            exchange[p] += work
            exchange[q] -= work
    tangent = SmoothPressureGeometryRate(g, g.bed, ht)
    oracle = np.zeros_like(g.h)
    for pole, (w,v) in zip(poles, factors):
        wt, vt = factor_direction(g, tangent, pole['normalized_auxiliary_velocity'])
        oracle += pole['alpha']*(w*wt+.75*v*vt)
    terms = [(p['normalized_auxiliary_velocity'],p['alpha']) for p in poles]
    reverse, _ = factor_depth_gradient(g, ht, terms, np.zeros_like(g.h),
                                       reverse_coefficients=smooth_coefficient_reverse)
    if not all(np.isfinite(a).all() for a in (gradient, explicit, exchange)):
        raise ValueError('Geometry work exceeds storage range')
    return dict(geometry_depth_gradient=gradient, explicit_geometry_work=explicit,
        geometry_exchange=exchange, maximum_factor_value_error=max_value_error,
        maximum_local_depth_nodes=maximum_local_depth_nodes,
        maximum_forward_work_error=float(abs(explicit-oracle).max()),
        maximum_reverse_gradient_error=float(abs(gradient-reverse).max()),
        maximum_graph_balance_error=float(abs(explicit-gradient*ht-exchange).max()))


def complete_local_work(g, p, ht, pt):
    # Supplied rates are observations, not unknowns solved by this identity.
    work = local_work(g, p, ht, pt)
    response = evaluate(g, p)
    geo = geometry_exchange(g, ht, response['poles'])
    eh, _ = depth_gradient(g, p, response, ht)
    coordinate = eh*ht+np.sum(response['canonical_velocity']*pt, axis=-1)
    root = np.sqrt(g.h)[...,None]
    q = p/root
    qt = pt/root-(ht/(2*g.h))[...,None]*q
    residual_qwork = np.zeros_like(g.h)
    for pole in response['poles']:
        system = PatchPressureSystem(g, pole['beta'])
        z = pole['normalized_auxiliary_velocity']
        residual = system.transpose_w(system.w(z))+.75*system.transpose_v(system.v(z))-(q-z)/pole['beta']
        residual_qwork += pole['alpha']*np.sum(residual*qt, axis=-1)
    assembled = (coordinate+geo['geometry_exchange']+work['auxiliary_exchange']
                 +work['stationarity_residual_work']-residual_qwork)
    return dict(**work, **geo, local_coordinate_work=coordinate,
        complete_local_balance_error=float(abs(work['local_energy_rate']-assembled).max()),
        integrated_geometry_exchange=float(geo['geometry_exchange'].sum())*g.dx**2,
        residual_normalization_work=residual_qwork)
