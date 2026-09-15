"""Conservative source-front candidate with explicit finite energy rejection.

Uses nondispersive wet fluxes and one-sided dry Riemann fluxes. This is NOT the
full rational auxiliary transport model, a release integrator or native code.
All receiving source IDs are explicit; no common-level pooling or energy reset.
"""
import math
import numpy as np

from subcell_wet_pool_transport import source_traces
from subcell_wet_pool_pressure import shared_subsegments
from subcell_energy_flux import face_flux_normal
from subcell_dry_front_flux import flux as dry_flux
from subcell_wet_pool_primal_energy import evaluate
from subcell_mechanical_energy import squared_depth_integral
from subcell_pressure_kinetic_geometry import local_form
from subcell_wet_connectivity import components
from triangle_cell_storage import TriangleCellStorage
from triangle_face_section import TriangleFaceSection


def faces(partition):
    for pl, pr, axis, _ in partition.patch.faces:
        normal = np.eye(2)[axis]
        if min(pl, pr) < 0:
            parent, sign = (pr, -1) if pl < 0 else (pl, 1)
            pieces = [(tag, tag, segment) for tag, segment in source_traces(partition, parent, axis, sign)]
        else:
            pieces = shared_subsegments(source_traces(partition, pl, axis, 1), source_traces(partition, pr, axis, -1))
        for left, right, segment in pieces:
            yield dict(left=left[0], right=right[0], left_source=left[1], right_source=right[1],
                left_parent=pl, right_parent=pr, normal=normal, segment=segment, internal=False)
    for face in partition.internal_faces:
        yield dict(face, left_parent=face['parent'], right_parent=face['parent'], internal=True)


def assembly(partition, gravity=9.81):
    if not np.isfinite(gravity) or gravity <= 0:
        raise ValueError('Positive finite gravity required')
    pools = partition.pools
    volume = np.array([p['volume'] for p in pools])
    momentum = np.array([p['momentum'] for p in pools])
    velocity = momentum/volume[:, None]
    datum = min(float(c.datum) for c in partition.patch.cells)
    dv = np.zeros_like(volume)
    bed = np.array([p['storage'].hydrostatic_bed_force(p['form']['stage_offset'], gravity, True) for p in pools])
    dp, wall = bed.copy(), np.zeros(2)
    receipts, front_records = {}, []
    for face in faces(partition):
        li, ri = face['left'], face['right']
        if li is None and ri is None:
            continue
        section = TriangleFaceSection([face['segment']], face['segment'][:, 0])
        n = face['normal']
        wall_face = min(face['left_parent'], face['right_parent']) < 0
        if not wall_face and (li is None or ri is None):
            owner = ri if li is None else li
            form = pools[owner]['form']
            outward = -n if li is None else n
            flux, info = dry_flux(section, form['stage_offset'], form['datum'], velocity[owner], outward, gravity, datum)
            if flux[0] == 0:
                continue
            parent = face['left_parent'] if li is None else face['right_parent']
            source = face['left_source'] if li is None else face['right_source']
            key = (parent, source)
            receipt = receipts.setdefault(key, dict(parent=parent, source_triangle_indices=[source],
                volume_rate=0., momentum_rate=np.zeros(2), incoming_energy_flux=0.))
            receipt['volume_rate'] += float(flux[0])
            receipt['momentum_rate'] += flux[1:]
            receipt['incoming_energy_flux'] += info['energy_flux']
            dv[owner] -= flux[0]; dp[owner] -= flux[1:]
            front_records.append(dict(wet_pool=owner, dry_parent=parent, dry_source_face=source,
                internal=face['internal'], normal=outward.tolist(), segment=face['segment'].tolist(),
                volume_flux=float(flux[0]), momentum_flux=flux[1:].tolist(), **info))
            continue
        lf, rf = pools[li]['form'], pools[ri]['form']
        ul, ur = velocity[li].copy(), velocity[ri].copy()
        if face['left_parent'] < 0:
            ul -= 2*float(ul@n)*n
        if face['right_parent'] < 0:
            ur -= 2*float(ur@n)*n
        flux, _ = face_flux_normal(section, lf['stage_offset'], ul, rf['stage_offset'], ur, n,
                                   gravity, lf['datum'], rf['datum'], dissipative=True)
        if face['left_parent'] >= 0:
            dv[li] -= flux[0]; dp[li] -= flux[1:]
        if face['right_parent'] >= 0:
            dv[ri] += flux[0]; dp[ri] += flux[1:]
        if wall_face:
            wall += flux[1:]*(1 if face['left_parent'] < 0 else -1)
    new = list(receipts.values())
    total_mass = float(dv.sum()+sum(r['volume_rate'] for r in new))
    total_momentum = dp.sum(axis=0)+sum((r['momentum_rate'] for r in new), np.zeros(2))
    outgoing = dv < 0
    net_volume_limit = float(np.min(volume[outgoing]/-dv[outgoing])) if outgoing.any() else None
    return dict(partition=partition, gravity=gravity, volume_rate=dv, momentum_rate=dp, new_region_rates=new, fronts=front_records,
        net_mass_rate=total_mass, momentum_boundary_bed_error=float(np.max(abs(total_momentum-bed.sum(axis=0)-wall))),
        bed_force=bed, wall_force=wall, net_volume_limit=net_volume_limit, reference_datum_m=datum)


def base_energy(partition, gravity=9.81):
    datum = min(float(c.datum) for c in partition.patch.cells)
    kinetic, potential = 0., 0.
    for p in partition.pools:
        f = p['form']
        q = p['momentum']/math.sqrt(p['volume'])
        kinetic += .5*float(q@q)
        height = math.fsum((f['stage_offset'], f['datum'], -datum))
        potential += gravity*(height*p['volume']-.5*squared_depth_integral(p['storage'], f['stage_offset'], True))
    return dict(kinetic=kinetic, potential=potential, total=kinetic+potential)


def wet_support_transition(partition, states):
    """Split remaining wet source components; release ONLY zero-water support.

    Each input region has a constant stage/velocity representation. Distinct
    input regions are never merged. Split volumes come from original source
    integrals, with their inversion error measured, not globally corrected.
    The full energy budget is checked later on the resulting pressure graph.
    """
    output, records = [], []
    for index, state in enumerate(states):
        parent, ids = state['parent'], state['source_triangle_indices']
        cell = partition.patch.cells[parent]
        if not set(ids).issubset(set(cell.source_triangle_indices)):
            raise ValueError('Transition support must use original parent source IDs')
        mask = np.isin(cell.source_triangle_indices, ids)
        storage = TriangleCellStorage(cell.triangles[mask], cell.source_triangle_indices[mask])
        form = local_form(storage, state['volume'])
        row, col = divmod(parent, partition.patch.shape[1])
        center = partition.origin+partition.patch.spacing*[col, row]
        graph = components(partition.sampler, storage, center, partition.patch.spacing, form['stage_offset'])
        pieces = graph['components']
        if not pieces:
            raise ValueError('Positive stored region has no represented wet source support')
        retained = set(source for piece in pieces for source in piece['source_triangle_indices'])
        dropped = sorted(set(ids)-retained)
        before = len(output)
        if len(pieces) == 1:
            # Removing dry triangles is not a volume adjustment: their exact
            # wet integral is zero, and the same stored V/P are retained.
            output.append(dict(state, source_triangle_indices=pieces[0]['source_triangle_indices']))
        else:
            velocity = np.asarray(state['momentum'])/state['volume']
            for piece in pieces:
                output.append(dict(parent=parent, source_triangle_indices=piece['source_triangle_indices'],
                    volume=piece['volume_m3'], momentum=piece['volume_m3']*velocity))
        if dropped or len(pieces) > 1:
            resulting = output[before:]
            records.append(dict(input_region=index, parent=parent, output_regions=len(pieces),
                released_zero_water_source_ids=dropped,
                volume_error=float(sum(s['volume'] for s in resulting)-state['volume']),
                momentum_error=(sum((s['momentum'] for s in resulting), np.zeros(2))-state['momentum']).tolist()))
    return output, records


def attempt(partition, duration, gravity=9.81, assembled=None):
    """Return a state ONLY if this candidate's mass/momentum/energy gates pass.

    A passing candidate remains a nondispersive activation control, not proof
    of the full nonlinear model. Never shorten duration or repair a failed state.
    """
    if not np.isfinite([duration, gravity]).all() or duration <= 0 or gravity <= 0:
        raise ValueError('Positive finite duration and gravity required')
    a = assembly(partition, gravity) if assembled is None else assembled
    if a['partition'] is not partition or a['gravity'] != gravity:
        raise ValueError('Matching source state and gravity required for cached assembly')
    volume = np.array([p['volume'] for p in partition.pools])
    momentum = np.array([p['momentum'] for p in partition.pools])
    new_volume = volume+duration*a['volume_rate']
    new_momentum = momentum+duration*a['momentum_rate']
    audit = dict(duration=duration, original_region_count=len(volume),
        requested_new_regions=len(a['new_region_rates']), net_volume_limit=a['net_volume_limit'],
        assembly_net_mass_rate=a['net_mass_rate'], assembly_momentum_balance_error=a['momentum_boundary_bed_error'],
        candidate_accepted=False, full_rational_model_or_time_history_or_gameplay_accepted=False)
    audit['maximum_original_speed_mps'] = float(np.max(np.linalg.norm(momentum/volume[:, None], axis=1)))
    if (new_volume <= 0).any() or not np.isfinite(new_momentum).all() or not np.isfinite(new_volume).all():
        return dict(state=None, audit=dict(audit, rejection='Existing region drains or becomes unrepresentable; no clipping/deletion',
                                         minimum_candidate_volume=float(new_volume.min())))
    states = [dict(old, volume=float(v), momentum=p) for old, v, p in zip(partition.pools, new_volume, new_momentum)]
    for receipt in a['new_region_rates']:
        v, p = duration*receipt['volume_rate'], duration*receipt['momentum_rate']
        if v <= 0 or not np.isfinite(v) or not np.isfinite(p).all():
            return dict(state=None, audit=dict(audit, rejection='Positive receiving flux has unrepresentable stored state'))
        states.append(dict(parent=receipt['parent'], source_triangle_indices=receipt['source_triangle_indices'], volume=v, momentum=p))
    try:
        states, transitions = wet_support_transition(partition, states)
        candidate = partition.with_regions(states)
    except ValueError as exc:
        return dict(state=None, audit=dict(audit, rejection=str(exc)))
    audit['wet_support_transitions'] = transitions
    mass_error = abs(float(candidate.reassembled_volumes.sum()-partition.reassembled_volumes.sum()))
    speeds = np.array([np.linalg.norm(p['momentum']/p['volume']) for p in candidate.pools])
    fastest = int(np.argmax(speeds))
    audit.update(maximum_candidate_speed_mps=float(speeds[fastest]),
        fastest_region=dict(index=fastest, parent=candidate.pools[fastest]['parent'],
            source_triangle_indices=candidate.pools[fastest]['source_triangle_indices'],
            volume=candidate.pools[fastest]['volume']))
    expected_momentum = duration*(a['bed_force'].sum(axis=0)+a['wall_force'])
    actual_momentum = candidate.reassembled_momenta.sum(axis=(0, 1))-partition.reassembled_momenta.sum(axis=(0, 1))
    momentum_error = float(np.max(abs(actual_momentum-expected_momentum)))
    before_base, after_base = base_energy(partition, gravity), base_energy(candidate, gravity)
    try:
        before = evaluate(partition, momentum[:, None, :], gravity)
        after = evaluate(candidate, np.array([p['momentum'] for p in candidate.pools])[:, None, :], gravity)
    except ValueError as exc:
        return dict(state=None, audit=dict(audit, rejection=str(exc), mass_error=mass_error, momentum_error=momentum_error))
    base_delta, full_delta = after_base['total']-before_base['total'], after['total']-before['total']
    contraction_error = max(value['positive_energy_contraction_error'] for value in (before, after))
    passed = (mass_error < 1e-10 and momentum_error < 1e-10 and base_delta <= 1e-10 and full_delta <= 1e-10
              and contraction_error < 1e-10)
    audit.update(candidate_region_count=len(candidate.pools), mass_error=mass_error, momentum_error=momentum_error,
        before_base_energy=before_base['total'], after_base_energy=after_base['total'], base_energy_change=base_delta,
        before_full_energy=before['total'], after_full_energy=after['total'], full_energy_change=full_delta,
        candidate_accepted=passed, rejection=None if passed else 'Conservative finite-state or energy budget failed',
        maximum_positive_energy_contraction_error=contraction_error,
        maximum_pressure_residual=max(p['relative_residual'] for value in (before, after) for p in value['poles']))
    return dict(state=candidate if passed else None, audit=audit)
