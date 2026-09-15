"""Exact pool-aware NONDISPERSIVE base flux and full-metric work diagnostic.

All source face traces are considered, not just common-wet pressure edges. A
wet trace facing currently unowned dry source support requires activation and
is reported explicitly; incomplete rates are never returned as usable dynamics.
Complete fixed-topology rates still lack rational auxiliary transport/bed work,
wetting events and a time integrator. No gameplay acceptance is implied.
"""
import math
import numpy as np

from subcell_energy_flux import face_flux, face_flux_normal
from subcell_wet_pool_pressure import shared_subsegments
from subcell_wet_pool_primal_energy import evaluate
from triangle_face_section import TriangleFaceSection


def source_traces(partition, parent, axis, sign):
    """Include dry/unowned original triangles; preserve their original IDs."""
    owners = {}
    for index in partition.parent_pools[parent]:
        for source in partition.pools[index]['source_triangle_indices']:
            if source in owners:
                raise ValueError('Original source face belongs to multiple wet pools')
            owners[source] = index
    cell = partition.patch.cells[parent]
    coordinate = sign*partition.patch.spacing[axis]/2
    traces = []
    for source, triangle in zip(cell.source_triangle_indices, cell.triangles):
        for a, b in zip(triangle, np.roll(triangle, -1, axis=0)):
            if a[axis] == coordinate and b[axis] == coordinate and a[1-axis] != b[1-axis]:
                segment = np.array([[a[1-axis], a[2]], [b[1-axis], b[2]]])
                if segment[0, 0] > segment[1, 0]:
                    segment = segment[::-1]
                traces.append(((owners.get(int(source)), int(source)), segment))
    return traces


def rates(partition, physical_momentum=None, gravity=9.81, dissipative=False, full_metric=True):
    pools = partition.pools
    volumes = np.array([p['volume'] for p in pools])
    momentum = np.array([p['momentum'] for p in pools]) if physical_momentum is None else np.asarray(physical_momentum, float)
    if (momentum.shape != (len(pools), 2) or not np.isfinite(momentum).all()
            or not np.isfinite(gravity) or gravity <= 0):
        raise ValueError('Finite pool physical momenta and positive gravity required')
    velocity = momentum/volumes[:, None]
    bed = np.array([p['storage'].hydrostatic_bed_force(p['form']['stage_offset'], gravity, True) for p in pools])
    dv, dp = np.zeros_like(volumes), bed.copy()
    hydrostatic_closure = bed.copy()
    unresolved, fluxes = [], []
    expected_work, wall_force = 0., np.zeros(2)
    wet_dry_owned_segments = 0
    for parent_l, parent_r, axis, _ in partition.patch.faces:
        exterior = min(parent_l, parent_r) < 0
        if exterior:
            parent, sign = (parent_r, -1) if parent_l < 0 else (parent_l, 1)
            pieces = [(tag, tag, segment) for tag, segment in source_traces(partition, parent, axis, sign)]
        else:
            pieces = shared_subsegments(source_traces(partition, parent_l, axis, 1),
                                        source_traces(partition, parent_r, axis, -1))
        for tag_l, tag_r, segment in pieces:
            li, ri = tag_l[0], tag_r[0]
            if li is None and ri is None:
                continue
            section = TriangleFaceSection([segment], segment[:, 0])
            if li is None or ri is None:
                owner = ri if li is None else li
                form = pools[owner]['form']
                area = section.moments(form['stage_offset'], form['datum'])[0]
                if area > 0:
                    unresolved.append(dict(left_parent=parent_l, right_parent=parent_r, axis=axis,
                        wet_pool=owner, dry_parent=parent_l if li is None else parent_r,
                        wet_source_face=tag_r[1] if li is None else tag_l[1],
                        dry_source_face=tag_l[1] if li is None else tag_r[1],
                        segment=segment.tolist(), wet_column_area=float(area),
                        reason='Wet source trace faces unowned dry support; activation needed, not a reflecting wall'))
                continue
            lf, rf = pools[li]['form'], pools[ri]['form']
            al, i2l, _ = section.moments(lf['stage_offset'], lf['datum'])
            ar, i2r, _ = section.moments(rf['stage_offset'], rf['datum'])
            if al == 0 and ar == 0:
                continue
            if (al == 0) != (ar == 0):
                wet_dry_owned_segments += 1
            ul, ur = velocity[li].copy(), velocity[ri].copy()
            if parent_l < 0:
                ul[axis] *= -1
            if parent_r < 0:
                ur[axis] *= -1
            flux, info = face_flux(section, lf['stage_offset'], ul, rf['stage_offset'], ur, axis,
                                   gravity, lf['datum'], rf['datum'], dissipative)
            if parent_l >= 0:
                dv[li] -= flux[0]
                dp[li] -= flux[1:]
                hydrostatic_closure[li, axis] -= .5*gravity*i2l
            if parent_r >= 0:
                dv[ri] += flux[0]
                dp[ri] += flux[1:]
                hydrostatic_closure[ri, axis] += .5*gravity*i2r
            if exterior:
                wall_force += flux[1:]*(1 if parent_l < 0 else -1)
            expected_work += info['expected_energy_work']*(.5 if exterior else 1.)
            fluxes.append(dict(left=None if parent_l < 0 else li, right=None if parent_r < 0 else ri,
                               axis=axis, mass_flux=float(flux[0]), momentum_flux=flux[1:].tolist()))
    internal_active = 0
    for face in partition.internal_faces:
        li, ri = face['left'], face['right']
        section = TriangleFaceSection([face['segment']], face['segment'][:, 0])
        if li is None or ri is None:
            owner = ri if li is None else li
            form = pools[owner]['form']
            area = section.moments(form['stage_offset'], form['datum'])[0]
            if area > 0:
                unresolved.append(dict(left_parent=face['parent'], right_parent=face['parent'], axis=None,
                    normal=face['normal'].tolist(), edge_vertex_ids=face['edge_vertex_ids'],
                    wet_pool=owner, dry_parent=face['parent'],
                    wet_source_face=face['right_source'] if li is None else face['left_source'],
                    dry_source_face=face['left_source'] if li is None else face['right_source'],
                    segment=face['segment'].tolist(), wet_column_area=float(area),
                    reason='Internal wet source edge faces unowned support; one-sided activation needed'))
            continue
        lf, rf = pools[li]['form'], pools[ri]['form']
        al, i2l, _ = section.moments(lf['stage_offset'], lf['datum'])
        ar, i2r, _ = section.moments(rf['stage_offset'], rf['datum'])
        if al == 0 and ar == 0:
            continue
        internal_active += 1
        wet_dry_owned_segments += int((al == 0) != (ar == 0))
        flux, info = face_flux_normal(section, lf['stage_offset'], velocity[li], rf['stage_offset'], velocity[ri],
                                      face['normal'], gravity, lf['datum'], rf['datum'], dissipative)
        dv[li] -= flux[0]; dv[ri] += flux[0]
        dp[li] -= flux[1:]; dp[ri] += flux[1:]
        hydrostatic_closure[li] -= .5*gravity*i2l*face['normal']
        hydrostatic_closure[ri] += .5*gravity*i2r*face['normal']
        expected_work += info['expected_energy_work']
        fluxes.append(dict(left=li, right=ri, axis=None, normal=face['normal'].tolist(),
                           internal_source_edge=face['edge_vertex_ids'], mass_flux=float(flux[0]),
                           momentum_flux=flux[1:].tolist()))
    common = dict(unresolved_activation_faces=unresolved,
        internal_source_edges=len(partition.internal_faces), internal_active_source_edges=internal_active,
        owned_wet_dry_face_segments=wet_dry_owned_segments,
        complete_fixed_topology_base_rates=not unresolved,
        nonlinear_two_pole_or_wetting_or_time_or_gameplay_accepted=False)
    if unresolved:
        # Do not expose accumulated partial dv/dp as a plausible evolution.
        return dict(**common, volume_rate=None, momentum_rate=None, full_metric_energy_rate=None)
    datum = min(float(c.datum) for c in partition.patch.cells)
    heights = np.array([math.fsum((p['form']['stage_offset'], p['form']['datum'], -datum)) for p in pools])
    base_work = float((gravity*heights-.5*np.sum(velocity*velocity, axis=1))@dv+np.sum(velocity*dp))
    metric = evaluate(partition, momentum[:, None, :], gravity) if full_metric else None
    full_work = None if metric is None else float(metric['volume_gradient']@dv+np.sum(metric['canonical_velocity'][:, 0]*dp))
    return dict(**common, volume_rate=dv, momentum_rate=dp, bed_force=bed, wall_force=wall_force,
        maximum_hydrostatic_geometry_closure_error=float(np.max(abs(hydrostatic_closure))),
        net_mass_rate=float(dv.sum()), total_momentum_rate=dp.sum(axis=0),
        momentum_boundary_bed_error=float(np.max(abs(dp.sum(axis=0)-bed.sum(axis=0)-wall_force))),
        base_energy_rate=base_work, expected_base_energy_rate=float(expected_work),
        base_energy_identity_error=abs(base_work-expected_work), full_metric_energy_rate=full_work,
        full_metric_volume_work=None if metric is None else float(metric['volume_gradient']@dv),
        full_metric_momentum_work=None if metric is None else float(np.sum(metric['canonical_velocity'][:, 0]*dp)),
        fluxes=fluxes)
