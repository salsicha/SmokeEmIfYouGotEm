"""Direct original-face/bed/wall assembly; never residual-defined bed forces."""
from dataclasses import dataclass
import numpy as np

from subcell_source_frames import face_section
from subcell_wet_pool_pressure import harmonic_area, shared_subsegments
from subcell_wet_pool_pressure_rate import harmonic_area_rate


@dataclass
class Ledger:
    faces: list
    bed: np.ndarray
    wall: np.ndarray

    def __add__(self, other):
        return Ledger(self.faces+other.faces, self.bed+other.bed, self.wall+other.wall)

    def __mul__(self, scale):
        return Ledger([(l, r, scale*f) for l, r, f in self.faces], scale*self.bed, scale*self.wall)

    def action(self):
        result = self.bed+self.wall
        for l, r, force in self.faces:
            result[l] -= force
            result[r] += force
        return result[:, None, :]


def zero(partition):
    n = len(partition.pools)
    return Ledger([], np.zeros((n, 2)), np.zeros((n, 2)))


def divergence_transpose(partition, stress, volume_rate=None):
    """Original D^T or D_t^T on scalar/isotropic or full tensor stresses."""
    result = zero(partition)
    value = np.asarray(stress, float)
    n = len(partition.pools)
    if value.shape == (n,):
        value = value[:, None, None]*np.eye(2)
    if value.shape != (n, 2, 2) or not np.isfinite(value).all():
        raise ValueError('Finite original pool scalar or tensor stress required')
    volume = np.array([p['volume'] for p in partition.pools])
    vd = None if volume_rate is None else np.asarray(volume_rate, float).reshape(n)
    eta_rate = None if vd is None else vd/np.array([p['form']['wet_area'] for p in partition.pools])

    def shared(l, r, section, normal):
        lf, rf = partition.pools[l]['form'], partition.pools[r]['form']
        args = (section, lf['stage_offset'], rf['stage_offset'], lf['datum'], rf['datum'])
        area = harmonic_area(*args)
        if vd is None:
            tensor = .5*area*(value[l]/volume[l]+value[r]/volume[r])
        else:
            area_rate = harmonic_area_rate(*args, eta_rate[l], eta_rate[r])
            tensor = .5*((area_rate-area*vd[l]/volume[l])*value[l]/volume[l]
                         +(area_rate-area*vd[r]/volume[r])*value[r]/volume[r])
        result.faces.append((l, r, tensor@normal))

    for pl, pr, axis, _ in partition.patch.faces:
        if min(pl, pr) >= 0:
            for l, r, section in shared_subsegments(partition.boundary_segments(pl, axis, 1),
                                                   partition.boundary_segments(pr, axis, -1)):
                shared(l, r, section, np.eye(2)[axis])
        else:
            parent, sign = (pr, -1) if pl < 0 else (pl, 1)
            for owner, segment in partition.boundary_segments(parent, axis, sign):
                f = partition.pools[owner]['form']
                area, _, width = face_section(segment).moments(f['stage_offset'], f['datum'])
                weight = area/volume[owner]
                if vd is not None:
                    weight = (width*eta_rate[owner]-area*vd[owner]/volume[owner])/volume[owner]
                result.wall[owner] -= sign*weight*value[owner, :, axis]
    for face in partition.internal_faces:
        if face['left'] is not None and face['right'] is not None:
            shared(face['left'], face['right'], face['segment'], face['normal'])
    return result


def gram(system, velocity):
    u = system._vector(velocity)[:, 0]
    jet = np.column_stack((system.divergence(u), u))
    matrices = np.array([p['form']['gram'] for p in system.partition.pools])
    stress = np.einsum('nij,nj->ni', matrices, jet)
    result = divergence_transpose(system.partition, stress[:, 0])
    result.bed += stress[:, 1:]
    return result


def metric_time(tangent, auxiliary, auxiliary_rate):
    s, part = tangent.system, tangent.system.partition
    w, wt = auxiliary[:, 0], auxiliary_rate[:, 0]
    jet = np.column_stack((s.divergence(w), w))
    jet_t = np.column_stack((tangent.divergence_rate(w)+s.divergence(wt), wt))
    matrices = np.array([p['form']['gram'] for p in part.pools])
    stress = np.einsum('nij,nj->ni', matrices, jet)
    stress_t = np.einsum('nij,nj->ni', tangent.gram_rate, jet)+np.einsum('nij,nj->ni', matrices, jet_t)
    result = (divergence_transpose(part, stress[:, 0], tangent.volume_rate)
              +divergence_transpose(part, stress_t[:, 0]))
    result.bed += stress_t[:, 1:]
    return result


def commutator(tangent, velocity):
    s, part = tangent.system, tangent.system.partition
    u = velocity[:, 0]
    matrices = np.array([p['form']['gram'] for p in part.pools])
    a, c, ct = matrices[:, 0, 0], matrices[:, 0, 1:], tangent.gram_rate[:, 0, 1:]
    d, dt = s.divergence(u), tangent.divergence_rate(u)
    result = (divergence_transpose(part, .5*a*dt-.25*np.sum(ct*u, axis=1))
              +divergence_transpose(part, -.5*(a*d+np.sum(c*u, axis=1)), tangent.volume_rate))
    result.bed += .5*c*dt[:, None]+.25*ct*d[:, None]
    return result


def factor_transport(transport, velocity):
    s = transport.system
    u = velocity[:, 0]
    jet = np.column_stack((s.divergence(u), u))
    stress = np.zeros_like(jet)
    for face in transport.faces:
        l, r, matrix = face['left'], face['right'], face['matrix']
        stress[l] += .5*matrix@jet[r]
        stress[r] -= .5*matrix.T@jet[l]
    result = divergence_transpose(s.partition, stress[:, 0])
    result.bed += stress[:, 1:]
    gram = np.array([pool['form']['gram'] for pool in s.partition.pools])
    k = .25*np.einsum('nij,nj->ni', gram[:, 1:, 1:], transport.transport_velocity)
    result = result+divergence_transpose(s.partition, -np.sum(k*u, axis=1))
    result.bed += k*s.divergence(u)[:, None]
    return result


def tensor(system, curvature, auxiliary, velocity):
    w, z = auxiliary[:, 0], velocity[:, 0]
    matrices = np.array([p['form']['gram'] for p in system.partition.pools])
    c = matrices[:, 0, 0]*system.divergence(w)+np.sum(matrices[:, 0, 1:]*w, axis=1)
    jac = np.empty((len(w), 2, 2))
    for i in range(2):
        for j in range(2):
            projected = np.zeros_like(z); projected[:, j] = z[:, i]
            jac[:, i, j] = system.divergence(projected)
    trace = np.trace(jac, axis1=1, axis2=2)
    stress = -c[:, None, None]*(jac.transpose(0, 2, 1)+trace[:, None, None]*np.eye(2))
    result = divergence_transpose(system.partition, stress)
    result.bed += curvature.action(auxiliary, velocity)[:, 0]
    return result


def base(partition, record):
    result = zero(partition)
    result.bed += record['bed_force']
    for face in record['fluxes']:
        l, r, force = face['left'], face['right'], np.asarray(face['momentum_flux'])
        if l is None:
            result.wall[r] += force
        elif r is None:
            result.wall[l] -= force
        else:
            result.faces.append((l, r, force))
    return result
