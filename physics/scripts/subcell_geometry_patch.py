"""Reference mass/advection/hydrostatic coupling over exact source-cell geometry.

Closed/periodic test patch only. Not the complete dispersive river solver;
no native budget, energy, open-boundary, breaking or gameplay qualification.
"""
import numpy as np
from triangle_cell_storage import cell_triangles, TriangleCellStorage
from triangle_face_section import TriangleFaceSection


class SubcellGeometryPatch:
    def __init__(self, sampler, origin, shape, spacing=(1., 1.), periodic=(False, False)):
        origin, spacing = np.asarray(origin, float), np.asarray(spacing, float)
        if (origin.shape != (2,) or spacing.shape != (2,) or not np.isfinite([origin, spacing]).all()
                or (spacing <= 0).any() or len(shape) != 2 or any(int(n) != n or n < 1 for n in shape)
                or len(periodic) != 2):
            raise ValueError('Finite origin, positive spacing and integer (ny,nx) shape required')
        self.shape, self.spacing = tuple(map(int, shape)), spacing
        ny, nx = self.shape
        self.cells, boundaries = [], []
        for row in range(ny):
            for col in range(nx):
                triangles = cell_triangles(sampler, origin+spacing*[col, row], spacing)
                self.cells.append(TriangleCellStorage(triangles))
                boundaries.append([TriangleFaceSection.from_cell(triangles, axis, sign*spacing[axis]/2,
                    [-spacing[1-axis]/2, spacing[1-axis]/2]) for axis in (0, 1) for sign in (-1, 1)])
        self.faces = []
        # Each face has exactly one owner/evaluation, including periodic seams.
        for axis in (0, 1):
            lines, width, stride = (ny, nx, 1) if axis == 0 else (nx, ny, nx)
            for line in range(lines):
                first = line*nx if axis == 0 else line
                for index in range(1, width):
                    left, right = first+(index-1)*stride, first+index*stride
                    a, b = boundaries[left][2*axis+1], boundaries[right][2*axis]
                    a.verify_shared(b)
                    self.faces.append((left, right, axis, a))
                last = first+(width-1)*stride
                if periodic[axis]:
                    a, b = boundaries[last][2*axis+1], boundaries[first][2*axis]
                    a.verify_shared(b)
                    self.faces.append((last, first, axis, a))
                else:
                    self.faces.extend(((-1, first, axis, boundaries[first][2*axis]),
                                       (last, -1, axis, boundaries[last][2*axis+1])))

    def state_from_stages(self, stages, velocities=None):
        stages = np.broadcast_to(np.asarray(stages, float), self.shape).ravel()
        volumes = np.array([cell.volume_and_wet_area(eta)[0] for cell, eta in zip(self.cells, stages)])
        velocities = np.zeros((*self.shape, 2)) if velocities is None else np.broadcast_to(velocities, (*self.shape, 2))
        if not np.isfinite(velocities).all():
            raise ValueError('Finite velocity required')
        return volumes.reshape(self.shape), volumes.reshape((*self.shape, 1))*velocities

    def rates(self, volumes, momenta, gravity=9.81, diagnostics=False):
        volumes, momenta = np.asarray(volumes, float), np.asarray(momenta, float)
        if (volumes.shape != self.shape or momenta.shape != (*self.shape, 2)
                or not np.isfinite(volumes).all() or not np.isfinite(momenta).all() or (volumes < 0).any()
                or np.any(momenta[volumes == 0] != 0)):
            raise ValueError('Finite physical cell state required; dry momentum must be exactly zero')
        volume, momentum = volumes.ravel(), momenta.reshape(-1, 2)
        eta = np.array([cell.stage_for_volume(v) for cell, v in zip(self.cells, volume)])
        velocity = np.divide(momentum, volume[:, None], out=np.zeros_like(momentum), where=volume[:, None] > 0)
        mass_rate = np.zeros(len(volume))
        momentum_rate = np.array([cell.hydrostatic_bed_force(e, gravity) for cell, e in zip(self.cells, eta)])
        outgoing = np.zeros(len(volume))
        donor_outgoing = np.zeros(len(volume))
        max_speed = 0.
        for left, right, axis, section in self.faces:
            li, ri = max(left, right) if left == -1 else left, max(left, right) if right == -1 else right
            ul, ur = velocity[li].copy(), velocity[ri].copy()
            if left == -1:
                ul[axis] *= -1
            if right == -1:
                ur[axis] *= -1
            flux, speed = section.flux(eta[li], ul, eta[ri], ur, axis, gravity)
            max_speed = max(max_speed, speed)
            if left != -1:
                mass_rate[left] -= flux[0]
                momentum_rate[left] -= flux[1:]
                outgoing[left] += max(flux[0], 0)
                donor_outgoing[left] += .5*(ul[axis]+speed)*section.moments(eta[li])[0]
            if right != -1:
                mass_rate[right] += flux[0]
                momentum_rate[right] += flux[1:]
                outgoing[right] += max(-flux[0], 0)
                donor_outgoing[right] += .5*(speed-ur[axis])*section.moments(eta[ri])[0]
        donating = outgoing > 0
        drain_limit = float(np.min(volume[donating]/outgoing[donating])) if donating.any() else np.inf
        wave_limit = .5*float(self.spacing.min())/max_speed if max_speed > 0 else np.inf
        active = donor_outgoing > 0
        donor_limit = float(np.min(volume[active]/donor_outgoing[active])) if active.any() else np.inf
        # Net discharge can vanish while counter-propagating Rusanov donors
        # exchange momentum. Bound their gross coefficient, not only net mass
        # loss: V_new*u_new is then a nonnegative combination of transported
        # momenta before pressure/bed work. A grid-width wave CFL alone misses
        # the arbitrarily small V/face-area ratio of partially wet cells.
        # This does not prove stability of pressure or dispersive coupling.
        result = (mass_rate.reshape(self.shape), momentum_rate.reshape((*self.shape, 2)),
                  min(drain_limit, donor_limit, wave_limit))
        if diagnostics:
            return (*result, dict(net_drain_limit_seconds=drain_limit, donor_limit_seconds=donor_limit,
                wave_limit_seconds=wave_limit, maximum_face_signal_speed_mps=max_speed,
                maximum_cell_speed_mps=float(np.linalg.norm(velocity, axis=1).max())))
        return result

    def advance(self, volumes, momenta, dt, gravity=9.81):
        """One explicit base update. Reject unsafe dt/state; never clip/rescale it."""
        if not np.isfinite(dt) or dt <= 0:
            raise ValueError('Positive finite timestep required')
        dv, dp, limit = self.rates(volumes, momenta, gravity)
        if dt > limit:
            raise ValueError('Timestep exceeds local donor/draining/wave bound')
        new_v, new_p = np.asarray(volumes)+dt*dv, np.asarray(momenta)+dt*dp
        if (new_v < 0).any() or not np.isfinite(new_v).all() or not np.isfinite(new_p).all():
            raise ValueError('Update rejected; no negative-depth repair')
        if np.any(new_p[new_v == 0] != 0):
            raise ValueError('Update produced dry momentum; no silent cleanup')
        return new_v, new_p
