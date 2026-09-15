"""Reference mass/advection/hydrostatic coupling over exact source-cell geometry.

Closed/periodic test patch only. Not the complete dispersive river solver;
no native budget, energy, open-boundary, breaking or gameplay qualification.
"""
import numpy as np
from triangle_cell_storage import cell_triangles, TriangleCellStorage
from triangle_face_section import TriangleFaceSection
from fractions import Fraction as F
from subcell_exact_geometry import cell_fragments, SourceRelativeStorage
from subcell_source_face_section import fragment_section, stage_difference


class SubcellGeometryPatch:
    def __init__(self, sampler, origin, shape, spacing=(1., 1.), periodic=(False, False), relative_stages=False,
                 exact_sources=False):
        origin, spacing = np.asarray(origin, float), np.asarray(spacing, float)
        if (origin.shape != (2,) or spacing.shape != (2,) or not np.isfinite([origin, spacing]).all()
                or (spacing <= 0).any() or len(shape) != 2 or any(int(n) != n or n < 1 for n in shape)
                or len(periodic) != 2):
            raise ValueError('Finite origin, positive spacing and integer (ny,nx) shape required')
        self.shape, self.spacing = tuple(map(int, shape)), spacing
        self.relative_stages = bool(relative_stages)
        self.exact_sources = bool(exact_sources)
        if self.exact_sources and not self.relative_stages:
            raise ValueError('Exact source geometry requires datum-relative storage')
        ny, nx = self.shape
        self.cells, boundaries = [], []
        for row in range(ny):
            for col in range(nx):
                if self.exact_sources:
                    fragments = cell_fragments(sampler, origin+spacing*[col, row], spacing)
                    self.cells.append(SourceRelativeStorage(fragments))
                    boundaries.append([fragment_section(fragments, axis, sign*F(float(spacing[axis]))/2)
                                       for axis in (0, 1) for sign in (-1, 1)])
                    continue
                triangles, source_ids = cell_triangles(sampler, origin+spacing*[col, row], spacing, with_source_ids=True)
                self.cells.append(TriangleCellStorage(triangles, source_ids))
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
        volumes = np.array([cell.relative_volume_and_wet_area(stage_difference(0., cell.source_datum, eta, 0.))[0]
                            if hasattr(cell, 'source_datum') else cell.volume_and_wet_area(eta)[0]
                            for cell, eta in zip(self.cells, stages)])
        velocities = np.zeros((*self.shape, 2)) if velocities is None else np.broadcast_to(velocities, (*self.shape, 2))
        if not np.isfinite(velocities).all():
            raise ValueError('Finite velocity required')
        return volumes.reshape(self.shape), volumes.reshape((*self.shape, 1))*velocities

    def rates(self, volumes, momenta, gravity=9.81, diagnostics=False):
        if self.exact_sources:
            raise ValueError('Exact source evolution requires pool-aware state, not the legacy aggregate-cell rate API')
        volumes, momenta = np.asarray(volumes, float), np.asarray(momenta, float)
        if (volumes.shape != self.shape or momenta.shape != (*self.shape, 2)
                or not np.isfinite(volumes).all() or not np.isfinite(momenta).all() or (volumes < 0).any()
                or np.any(momenta[volumes == 0] != 0)):
            raise ValueError('Finite physical cell state required; dry momentum must be exactly zero')
        volume, momentum = volumes.ravel(), momenta.reshape(-1, 2)
        eta = np.array([cell.relative_stage_for_volume(v) if self.relative_stages else cell.stage_for_volume(v)
                        for cell, v in zip(self.cells, volume)])
        datums = np.array([cell.datum if self.relative_stages else 0. for cell in self.cells])
        velocity = np.divide(momentum, volume[:, None], out=np.zeros_like(momentum), where=volume[:, None] > 0)
        mass_rate = np.zeros(len(volume))
        momentum_rate = np.array([cell.hydrostatic_bed_force(e, gravity, self.relative_stages)
                                  for cell, e in zip(self.cells, eta)])
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
            flux, speed = section.flux(eta[li], ul, eta[ri], ur, axis, gravity, datums[li], datums[ri])
            max_speed = max(max_speed, speed)
            if left != -1:
                mass_rate[left] -= flux[0]
                momentum_rate[left] -= flux[1:]
                outgoing[left] += max(flux[0], 0)
                donor_outgoing[left] += .5*(ul[axis]+speed)*section.moments(eta[li], datums[li])[0]
            if right != -1:
                mass_rate[right] += flux[0]
                momentum_rate[right] += flux[1:]
                outgoing[right] += max(-flux[0], 0)
                donor_outgoing[right] += .5*(speed-ur[axis])*section.moments(eta[ri], datums[ri])[0]
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
            limiting_cell = None
            if active.any():
                candidates = np.flatnonzero(active)
                index = int(candidates[np.argmin(volume[active]/donor_outgoing[active])])
                cell = self.cells[index]
                limiting_cell = dict(row=index//self.shape[1], col=index%self.shape[1],
                    volume_m3=float(volume[index]), stage_m=float(eta[index]+datums[index]),
                    stage_offset_m=float(eta[index]) if self.relative_stages else float(eta[index]-cell.datum),
                    minimum_bed_m=float(cell.levels.min()), maximum_bed_m=float(cell.levels.max()),
                    wet_area_m2=(cell.relative_volume_and_wet_area(eta[index]) if self.relative_stages
                                 else cell.volume_and_wet_area(eta[index]))[1],
                    velocity_mps=velocity[index].tolist(),
                    net_volume_rate_m3s=float(mass_rate[index]),
                    incoming_discharge_m3s=float(outgoing[index]+mass_rate[index]),
                    outgoing_discharge_m3s=float(outgoing[index]),
                    gross_donor_coefficient_m3s=float(donor_outgoing[index]),
                    momentum_rate_m4s2=momentum_rate[index].tolist(),
                    hydrostatic_bed_force_m4s2=cell.hydrostatic_bed_force(eta[index], gravity, self.relative_stages).tolist())
            return (*result, dict(net_drain_limit_seconds=drain_limit, donor_limit_seconds=donor_limit,
                wave_limit_seconds=wave_limit, maximum_face_signal_speed_mps=max_speed,
                maximum_cell_speed_mps=float(np.linalg.norm(velocity, axis=1).max()),
                limiting_donor_cell=limiting_cell))
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
