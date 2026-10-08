"""Audit the initial bed on every native source centre and route profile point."""
import argparse
import json
from pathlib import Path

import numpy as np
import shapely

from build_futaleufu_corridor_sources import ROOT, sha
from futaleufu_corridor_bed import FutaleufuBed, NAMES


def audit(sources, profile, network, output, depth):
    output = Path(output).resolve(); output.relative_to(ROOT)
    if output.exists():
        raise ValueError('Fresh audit output required')
    model = FutaleufuBed(sources, profile, network, depth_m=depth)
    model.receipt['sources_sha256'][Path(__file__).resolve().relative_to(ROOT).as_posix()] = sha(Path(__file__))
    rows, cols = np.indices(model.grid.shape); t = model.transform
    xy = np.c_[t[2]+(cols.ravel()+.5)*10, t[5]-(rows.ravel()+.5)*10]
    batches = [model.sample(xy[i:i+4096]) for i in range(0, len(xy), 4096)]
    result = {k: np.concatenate([b[k] for b in batches]) for k in batches[0]}
    if (not np.array_equal(result['source_height_m'], model.grid.ravel())
            or np.any(result['height_m'] > result['source_height_m'])
            or np.any(result['inferred_bed'] & ~result['bed_owned'])):
        raise ValueError('Source sampling or ownership invariant failed')
    islands = shapely.intersects(model.islands, shapely.points(xy))
    if np.any(result['inferred_bed'] & islands):
        raise ValueError('Mapped island changed')
    routes = {}
    for j, name in enumerate(NAMES):
        stations = model.arrays[name]['station_m']
        points = shapely.get_coordinates(shapely.line_interpolate_point(model.lines[j], stations))
        r = model.sample(points); margin = r['reference_m']-r['height_m']
        # Open inlet/outlet caps intentionally remain source terrain. The
        # junction endpoints are internal and must still be reported.
        interior = (stations > 0) & (stations < model.lines[j].length)
        blocked = interior & (margin <= 0)
        before = shapely.get_coordinates(shapely.line_interpolate_point(model.lines[j], np.maximum(stations-1, 0)))
        after = shapely.get_coordinates(shapely.line_interpolate_point(model.lines[j], np.minimum(stations+1, model.lines[j].length)))
        tangent = after-before
        normal = np.c_[-tangent[:, 1], tangent[:, 0]]/np.linalg.norm(tangent, axis=1)[:, None]
        midspan = (model.arrays[name]['left_m']+model.arrays[name]['right_m'])/2
        centre = model.sample(points+normal*midspan[:, None])
        centre_depth = centre['reference_m']-centre['height_m']
        routes[name] = dict(samples=len(stations), interior_above_stage=int(blocked.sum()),
            blocked_stations_m=stations[blocked].tolist(), minimum_interior_depth_m=float(margin[interior].min()),
            cut_limit_samples=int(r['cut_limit_reached'].sum()),
            source_route_outside_bank_span=int(np.count_nonzero(interior &
                ((model.arrays[name]['left_m'] >= 0) | (model.arrays[name]['right_m'] <= 0)))),
            inferred_midspan_above_stage=int(np.count_nonzero(interior & (centre_depth <= 0))),
            minimum_interior_midspan_depth_m=float(centre_depth[interior].min()),
            midspan_caveat='Diagnostic cross-section midpoint, not a changed captured route or a verified navigable line')
    record = dict(model.receipt, statistics=dict(native_source_centres=len(xy),
        mapped_island_centres=int(islands.sum()), changed_island_centres=0,
        inferred_bed_centres=int(result['inferred_bed'].sum()),
        inferred_azul_planform_centres=int(result['inferred_planform'].sum()),
        cut_limit_centres=int(result['cut_limit_reached'].sum()),
        maximum_cut_m=float(np.max(result['source_height_m']-result['height_m'])),
        owned_above_stage_centres=int(result['unresolved_above_stage'].sum())), routes=routes,
        limitations=['Native ten-metre audit is not a subpixel ownership or collision proof.',
          'Centreline clearance alone is not raft clearance, solved flow, rapid fidelity or navigation acceptance.',
          'Triangle-support guarding is required when exporting render/collision terrain.'])
    for relative, digest in record['sources_sha256'].items():
        if sha(ROOT/relative) != digest:
            raise ValueError('Input changed during audit')
    output.mkdir(parents=True)
    np.savez_compressed(output/'native_bed_review.npz', **{k: v.reshape(model.grid.shape) for k, v in result.items()})
    record['review_arrays_sha256'] = sha(output/'native_bed_review.npz')
    (output/'audit.json').write_text(json.dumps(record, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    print(json.dumps(dict(statistics=record['statistics'], routes=routes)))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('sources', 'profile', 'network', 'out'):
        p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--depth-m', type=float, required=True)
    a = p.parse_args(); audit(a.sources, a.profile, a.network, a.out, a.depth_m)
