"""Equal-horizon source-front refinement, not full rational-model acceptance.

Compare water and both physical momentum components on original source triangles,
not region indices (which change on splitting/drying). Parent-cell comparisons
are retained separately: agreement after aggregation can hide misplaced water.
"""
import math
import numpy as np

from subcell_source_activation import attempt


def source_state(partition):
    records = {}
    storage_error = 0.
    for pool in partition.pools:
        storage = pool['storage']
        volumes, _ = storage._triangle_volume_and_wet_area(
            pool['form']['stage_offset'], storage.relative_levels)
        velocity = pool['momentum']/pool['volume']
        storage_error = max(storage_error, abs(math.fsum(volumes)-pool['volume']))
        for source, volume in zip(storage.source_triangle_indices, volumes):
            key = (int(pool['parent']), int(source))
            records.setdefault(key, []).append(np.r_[volume, volume*velocity])
    values = {key: np.array([math.fsum(row[j] for row in rows) for j in range(3)])
              for key, rows in records.items()}
    return dict(values=values, maximum_pool_storage_error=storage_error,
                parent_volume=np.asarray(partition.reassembled_volumes).copy(),
                parent_momentum=np.asarray(partition.reassembled_momenta).copy())


def difference(first, second):
    keys = sorted(set(first['values']) | set(second['values']))
    delta = np.array([second['values'].get(key, np.zeros(3))
                      -first['values'].get(key, np.zeros(3)) for key in keys])
    if not len(delta):
        raise ValueError('Source comparison requires represented water')
    return dict(source_volume_l1=float(np.sum(abs(delta[:, 0]))),
        source_momentum_l1=np.sum(abs(delta[:, 1:]), axis=0).tolist(),
        parent_volume_l1=float(np.sum(abs(second['parent_volume']-first['parent_volume']))),
        parent_momentum_l1=np.sum(abs(second['parent_momentum']-first['parent_momentum']), axis=(0, 1)).tolist(),
        maximum_pool_storage_error=max(first['maximum_pool_storage_error'], second['maximum_pool_storage_error']))


def audit_refinement(partition, horizon, base_steps, levels=3, scheme='coupled-events'):
    if not math.isfinite(horizon) or horizon <= 0:
        raise ValueError('Positive finite common horizon required')
    if any(isinstance(n, bool) or not isinstance(n, int) or n <= 0 for n in (base_steps, levels)) or levels < 3:
        raise ValueError('Positive integer base steps and at least three levels required')
    runs, endpoints = [], []
    for level in range(levels):
        steps = base_steps*2**level
        dt = horizon/steps
        current, records = partition, []
        accepted = 0
        for index in range(steps):
            try:
                result = attempt(current, dt, scheme=scheme)
            except ValueError as exc:
                result = dict(state=None, audit=dict(candidate_accepted=False, rejection=str(exc)))
            records.append(dict(result['audit'], step=index+1, start_time=index*dt))
            if not result['audit']['candidate_accepted']:
                break
            if result['state'] is None:
                raise ValueError('Accepted candidate must supply its actual state')
            current = result['state']
            accepted += 1
        runs.append(dict(level=level, steps=steps, duration=dt, accepted_steps=accepted,
                         advanced_seconds=accepted*dt, completed=accepted == steps, attempts=records))
        endpoints.append(source_state(current) if accepted == steps else None)
    comparisons = [dict(coarse_level=i, fine_level=i+1, **difference(a, b))
                   if a is not None and b is not None else None
                   for i, (a, b) in enumerate(zip(endpoints, endpoints[1:]))]
    ratios = []
    for a, b in zip(comparisons, comparisons[1:]):
        if a is None or b is None:
            ratios.append(None)
            continue
        # Zero differences do not establish an observed convergence order.
        ratio = {key: (a[key]/b[key] if b[key] > 0 else None)
                 for key in ('source_volume_l1', 'parent_volume_l1')}
        for key in ('source_momentum_l1', 'parent_momentum_l1'):
            ratio[key] = [x/y if y > 0 else None for x, y in zip(a[key], b[key])]
        ratios.append(ratio)
    return dict(horizon=horizon, scheme=scheme, runs=runs, comparisons=comparisons,
        adjacent_difference_ratios=ratios,
        all_runs_completed=all(r['completed'] for r in runs),
        probe='Same initial state and physical horizon; no retry, timestep selection, source reassignment or state repair',
        full_rational_model_or_time_accuracy_or_native_or_gameplay_accepted=False)
