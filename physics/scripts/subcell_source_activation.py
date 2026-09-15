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
from subcell_coupled_front_update import coupled_update
from subcell_donor_face_flux import flux as donor_flux


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


def assembly(partition, gravity=9.81, face_scheme='paired'):
    if not np.isfinite(gravity) or gravity <= 0:
        raise ValueError('Positive finite gravity required')
    if face_scheme not in ('paired', 'donor'):
        raise ValueError('Unknown source face flux')
    pools = partition.pools
    volume = np.array([p['volume'] for p in pools])
    momentum = np.array([p['momentum'] for p in pools])
    velocity = momentum/volume[:, None]
    datum = min(float(c.datum) for c in partition.patch.cells)
    dv = np.zeros_like(volume)
    incoming, outgoing = np.zeros_like(volume), np.zeros_like(volume)
    face_minima = np.full_like(volume, np.inf)
    bed = np.array([p['storage'].hydrostatic_bed_force(p['form']['stage_offset'], gravity, True) for p in pools])
    dp, wall = bed.copy(), np.zeros(2)
    force_parts = {key: np.zeros_like(momentum) for key in ('wall', 'pressure', 'negative_exchange', 'dry_front')}
    receipts, front_records, transfers, exchanges = {}, [], [], []
    for face in faces(partition):
        li, ri = face['left'], face['right']
        for owner in (li, ri):
            if owner is not None:
                face_minima[owner] = min(face_minima[owner], float(face['segment'][:, 1].min()))
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
                volume_rate=0., momentum_rate=np.zeros(2), explicit_force_rate=np.zeros(2), incoming_energy_flux=0.))
            receipt['volume_rate'] += float(flux[0])
            receipt['momentum_rate'] += flux[1:]
            receipt['explicit_force_rate'] += np.asarray(info['nonadvective_momentum_flux'])
            receipt['incoming_energy_flux'] += info['energy_flux']
            dv[owner] -= flux[0]; dp[owner] -= flux[1:]
            outgoing[owner] += flux[0]
            force_parts['dry_front'][owner] -= np.asarray(info['nonadvective_momentum_flux'])
            transfers.append((owner, key, float(flux[0])))
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
        if face_scheme == 'donor':
            flux, info = donor_flux(section, lf['stage_offset'], ul, rf['stage_offset'], ur, n,
                                   gravity, lf['datum'], rf['datum'])
        else:
            flux, info = face_flux_normal(section, lf['stage_offset'], ul, rf['stage_offset'], ur, n,
                                       gravity, lf['datum'], rf['datum'], dissipative=True)
        if not wall_face and li != ri:
            # Fp = Fmass*u_upwind + D*(ul-ur) + pressure*n. Only the
            # nonnegative exchange D is implicit; any negative remainder is
            # still present in the exact assembled rate, never discarded.
            al = section.moments(lf['stage_offset'], lf['datum'])[0]
            ar = section.moments(rf['stage_offset'], rf['datum'])[0]
            if face_scheme == 'donor':
                d = info['velocity_exchange']
            else:
                central = float(.5*(ul+ur)@n)*info['pressure_secant_area']
                d = .5*(info['dissipation_speed']*ar-central) if flux[0] >= 0 else .5*(info['dissipation_speed']*al+central)
            if d > 0:
                exchanges.append((li, ri, float(d)))
            else:
                force_parts['negative_exchange'][li] -= d*(ul-ur)
                force_parts['negative_exchange'][ri] += d*(ul-ur)
            pressure = .5*(info['left_pressure']+info['right_pressure'])*n
            force_parts['pressure'][li] -= pressure
            force_parts['pressure'][ri] += pressure
        if face['left_parent'] >= 0:
            dv[li] -= flux[0]; dp[li] -= flux[1:]
            outgoing[li] += max(0., flux[0]); incoming[li] += max(0., -flux[0])
        if face['right_parent'] >= 0:
            dv[ri] += flux[0]; dp[ri] += flux[1:]
            outgoing[ri] += max(0., -flux[0]); incoming[ri] += max(0., flux[0])
        if wall_face:
            wall += flux[1:]*(1 if face['left_parent'] < 0 else -1)
            force_parts['wall'][li] += flux[1:]*(1 if face['left_parent'] < 0 else -1)
        elif flux[0] > 0 and li != ri:
            transfers.append((li, ri, float(flux[0])))
        elif flux[0] < 0 and li != ri:
            transfers.append((ri, li, float(-flux[0])))
    new = list(receipts.values())
    receiving_indices = {key: len(pools)+i for i, key in enumerate(receipts)}
    transfers = [(owner, receiving_indices[other] if isinstance(other, tuple) else other, rate)
                 for owner, other, rate in transfers]
    total_mass = float(dv.sum()+sum(r['volume_rate'] for r in new))
    total_momentum = dp.sum(axis=0)+sum((r['momentum_rate'] for r in new), np.zeros(2))
    draining = dv < 0
    net_volume_limit = float(np.min(volume[draining]/-dv[draining])) if draining.any() else None
    below = [dict(index=i, parent=p['parent'], source_triangle_indices=p['source_triangle_indices'],
        volume=p['volume'], stage_offset=p['form']['stage_offset'], datum=p['form']['datum'],
        face_minimum=float(face_minima[i]), gap=float(face_minima[i]-p['form']['datum']),
        gap_to_stage_ratio=float((p['form']['datum']-face_minima[i])/p['form']['stage_offset']))
        for i, p in enumerate(pools) if face_minima[i] < p['form']['datum']]
    below.sort(key=lambda r: r['gap_to_stage_ratio'], reverse=True)
    return dict(partition=partition, gravity=gravity, face_scheme=face_scheme, volume_rate=dv, momentum_rate=dp, new_region_rates=new, fronts=front_records,
        incoming_volume_rate=incoming, outgoing_volume_rate=outgoing,
        transfers=transfers,
        velocity_exchanges=exchanges,
        source_face_below_storage_minimum=dict(count=len(below), largest_relative_discrepancies=below[:8]),
        explicit_force_parts=dict(bed=bed, **force_parts),
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


def attempt(partition, duration, gravity=9.81, assembled=None, scheme='explicit'):
    """Return a state ONLY if this candidate's mass/momentum/energy gates pass.

    A passing candidate remains a nondispersive activation control, not proof
    of the full nonlinear model. Never shorten duration or repair a failed state.
    """
    if not np.isfinite([duration, gravity]).all() or duration <= 0 or gravity <= 0:
        raise ValueError('Positive finite duration and gravity required')
    if scheme not in ('explicit', 'coupled-frozen', 'coupled-donor'):
        raise ValueError('Unknown source-front update scheme')
    face_scheme = 'donor' if scheme == 'coupled-donor' else 'paired'
    a = assembly(partition, gravity, face_scheme) if assembled is None else assembled
    if a['partition'] is not partition or a['gravity'] != gravity or a['face_scheme'] != face_scheme:
        raise ValueError('Matching source state and gravity required for cached assembly')
    volume = np.array([p['volume'] for p in partition.pools])
    momentum = np.array([p['momentum'] for p in partition.pools])
    new_volume = volume+duration*a['volume_rate']
    new_momentum = momentum+duration*a['momentum_rate']
    audit = dict(duration=duration, scheme=scheme, original_region_count=len(volume),
        requested_new_regions=len(a['new_region_rates']), net_volume_limit=a['net_volume_limit'],
        assembly_net_mass_rate=a['net_mass_rate'], assembly_momentum_balance_error=a['momentum_boundary_bed_error'],
        candidate_accepted=False, full_rational_model_or_time_history_or_gameplay_accepted=False)
    audit['source_face_below_storage_minimum'] = a['source_face_below_storage_minimum']
    audit['maximum_original_speed_mps'] = float(np.max(np.linalg.norm(momentum/volume[:, None], axis=1)))
    coupled = None
    if scheme in ('coupled-frozen', 'coupled-donor'):
        try:
            coupled = coupled_update(a, duration)
        except ValueError as exc:
            return dict(state=None, audit=dict(audit, rejection=str(exc)))
        new_volume, new_momentum = coupled['volume'][:len(volume)], coupled['momentum'][:len(volume)]
        audit['coupled_update'] = coupled['audit']
    if (new_volume <= 0).any() or not np.isfinite(new_momentum).all() or not np.isfinite(new_volume).all():
        rejected = np.flatnonzero((new_volume <= 0) | ~np.isfinite(new_volume) | ~np.isfinite(new_momentum).all(axis=1))
        failures = [dict(index=int(i), parent=partition.pools[i]['parent'],
            source_triangle_indices=partition.pools[i]['source_triangle_indices'],
            volume=float(volume[i]), candidate_volume=float(new_volume[i]),
            incoming_volume_rate=float(a['incoming_volume_rate'][i]),
            outgoing_volume_rate=float(a['outgoing_volume_rate'][i]),
            stage_offset=partition.pools[i]['form']['stage_offset'], datum=partition.pools[i]['form']['datum'],
            velocity=(momentum[i]/volume[i]).tolist(), momentum_rate=a['momentum_rate'][i].tolist()) for i in rejected]
        return dict(state=None, audit=dict(audit, rejection='Existing region drains or becomes unrepresentable; no clipping/deletion',
                                         rejected_regions=failures,
                                         minimum_candidate_volume=float(new_volume.min())))
    states = [dict(old, volume=float(v), momentum=p) for old, v, p in zip(partition.pools, new_volume, new_momentum)]
    for index, receipt in enumerate(a['new_region_rates'], len(volume)):
        v, p = duration*receipt['volume_rate'], duration*receipt['momentum_rate']
        if coupled is not None:
            v, p = coupled['volume'][index], coupled['momentum'][index]
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
