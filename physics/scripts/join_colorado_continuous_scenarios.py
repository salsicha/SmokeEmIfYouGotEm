"""Cook adjoining source windows as one domain, without an internal boundary.

Only exact shared-coordinate inputs are eligible. All rendered bed triangles
must exist. Uncovered lateral padding must be classified dry; it never becomes
an invented water connection. The original source inputs remain immutable.
"""
import argparse
import copy
import json
from pathlib import Path

import numpy as np

from build_colorado_catalog_evidence import ROOT, sha
from build_colorado_catalog_scenario import sample_grid
from export_colorado_continuous_terrain import LandscapeTriangles, TerrainMosaic, load_sources


def merge_registered(items, bed, grid, padding_water):
    """Merge actual cell states; disagreement or missing wet coverage is fatal."""
    shape = bed.shape
    fields = {key: np.zeros(shape) for key in ('depth', 'u', 'v')}
    covered = np.zeros(shape, bool)
    classified = np.zeros(shape, bool)
    surface = np.full(shape[1], np.nan)
    for item in items:
        g = item['grid']
        offset = np.array([(g['origin_y']-grid['origin_y'])/grid['dy'],
                           (g['origin_x']-grid['origin_x'])/grid['dx']])
        if not np.allclose(offset, np.rint(offset), atol=1e-9, rtol=0):
            raise ValueError('Inputs do not share an exact cell lattice')
        row, col = np.rint(offset).astype(int)
        if row < 0 or col < 0 or row+g['ny'] > shape[0] or col+g['nx'] > shape[1]:
            raise ValueError('Source outside joined grid')
        sl = (slice(row, row+g['ny']), slice(col, col+g['nx']))
        if not np.array_equal(item['bed'], bed[sl], equal_nan=True):
            raise ValueError('Source bed differs from shared rendered triangles')
        overlap = covered[sl]
        for key in fields:
            values = np.asarray(item[key])
            if values.shape != item['bed'].shape or not np.isfinite(values).all():
                raise ValueError('Incomplete or nonfinite source state')
            if not np.allclose(fields[key][sl][overlap], values[overlap], atol=1e-10, rtol=0):
                raise ValueError('Source states disagree in overlap')
            # Keep the first owner bit-for-bit. No averaging or blend conceals
            # differences at the source boundary.
            fields[key][sl][~overlap] = values[~overlap]
        mask = item['classified_water'].astype(bool)
        if not np.array_equal(classified[sl][overlap], mask[overlap]):
            raise ValueError('Source water classifications disagree')
        classified[sl][~overlap] = mask[~overlap]
        target = surface[col:col+g['nx']]
        valid = np.isfinite(target)
        if not np.allclose(target[valid], item['reference_surface'][valid], atol=1e-9, rtol=0):
            raise ValueError('Source stage references disagree')
        target[~valid] = item['reference_surface'][~valid]
        covered[sl] = True
    if not np.isfinite(surface).all():
        raise ValueError('Source gap in continuous domain')
    if np.any(~covered & padding_water):
        raise ValueError('Uncovered classified water cannot be initialized as dry padding')
    if not np.isfinite(bed).all() or (fields['depth'] < 0).any():
        raise ValueError('Missing bed or negative depth')
    return fields, classified, surface, covered


def write_native_arrays(pkg, bed, h, u, v):
    """Native arrays are row-major, including a transposed terrain sample."""
    np.save(pkg/'bed.npy', np.ascontiguousarray(bed, dtype='<f8'))
    arrays = dict(depth=h, eta=bed+h, u=u, v=v, hu=h*u, hv=h*v, wet=h > 1e-6)
    np.savez_compressed(pkg/'initial_state.npz', **{
        key: np.ascontiguousarray(value, dtype=bool if key == 'wet' else '<f8')
        for key, value in arrays.items()})


def join(inputs, out):
    if out.exists() or len(inputs) < 2:
        raise ValueError('At least two sources and fresh output required')
    reports, scenarios, items = [], [], []
    for folder in inputs:
        folder = folder.resolve()
        report = json.loads((folder/'build_report.json').read_text())
        for name, expected in report['files_sha256'].items():
            if sha(folder/name) != expected:
                raise ValueError('Changed source input')
        if not report.get('shared_hydraulic_frame') or not report.get('continuous_terrain'):
            raise ValueError('Independent source charts cannot be joined')
        if reports and any(report[key] != reports[0][key]
                           for key in ('shared_hydraulic_frame', 'continuous_terrain')):
            raise ValueError('Different shared frame or terrain')
        scenario = json.loads((folder/'scenario/scenario.json').read_text())
        if scenarios and any(scenario[key] != scenarios[0][key] for key in ('roughness', 'fixed_dt')):
            raise ValueError('Different solver parameters')
        state = dict(np.load(folder/'scenario/initial_state.npz', allow_pickle=False))
        reference = dict(np.load(folder/'reference.npz', allow_pickle=False))
        items.append(dict(grid=scenario['grid'], bed=np.load(folder/'scenario/bed.npy'),
                          **{key: state[key] for key in ('depth', 'u', 'v')},
                          **{key: reference[key] for key in ('classified_water', 'reference_surface')}))
        reports.append(report)
        scenarios.append(scenario)
    ordering = np.argsort([item['grid']['origin_x'] for item in items])
    inputs = [inputs[i].resolve() for i in ordering]
    reports = [reports[i] for i in ordering]
    scenarios = [scenarios[i] for i in ordering]
    items = [items[i] for i in ordering]
    frame_path = ROOT/reports[0]['shared_hydraulic_frame']['manifest']
    terrain_path = ROOT/reports[0]['continuous_terrain']['manifest']
    for path, receipt in ((frame_path, reports[0]['shared_hydraulic_frame']),
                          (terrain_path, reports[0]['continuous_terrain'])):
        if sha(path) != receipt['sha256']:
            raise ValueError('Shared dependency changed')
    frame_manifest = json.loads(frame_path.read_text())
    for name, expected in frame_manifest['files_sha256'].items():
        if sha(frame_path.parent/name) != expected:
            raise ValueError('Shared frame file changed')
    arrays = dict(np.load(frame_path.parent/'frame.npz', allow_pickle=False))
    step = frame_manifest['grid_step_m']
    if any(g['grid']['dx'] != step or g['grid']['dy'] != step for g in items):
        raise ValueError('Different source cell resolution')
    lo = items[0]['grid']['origin_x']
    hi = max(i['grid']['origin_x']+(i['grid']['nx']-1)*step for i in items)
    select = (arrays['station_m'] >= lo) & (arrays['station_m'] <= hi)
    station = arrays['station_m'][select]
    ymin = min(i['grid']['origin_y'] for i in items)
    ymax = max(i['grid']['origin_y']+(i['grid']['ny']-1)*step for i in items)
    lateral = np.arange(ymin, ymax+step*.5, step)
    xy = arrays['east_north_m'][select]
    normal = arrays['normal_east_north'][select]
    queries = xy[:, None, :]+normal[:, None, :]*lateral[None, :, None]
    triangles = LandscapeTriangles(terrain_path.parent)
    bed = triangles.sample(queries).T
    # A wider common strip can lack dry fringe coverage at its ends. Crop only
    # exterior halo columns, and refuse any loss from the requested core run.
    complete = np.isfinite(bed).all(axis=0)
    indices = np.flatnonzero(complete)
    if not len(indices) or not complete[indices[0]:indices[-1]+1].all():
        raise ValueError('Missing interior rendered terrain')
    first, last = indices[0], indices[-1]+1
    if first:
        raise ValueError('Upstream terrain gap would invalidate the captured inlet boundary')
    source_station = arrays['source_global_station_m'][select][first:last]
    core_lo = min(r['source_core_interval_m'][0] for r in reports)
    core_hi = max(r['source_core_interval_m'][1] for r in reports)
    if source_station[0] > core_lo or source_station[-1] < core_hi:
        raise ValueError('Terrain does not cover the complete source cores')
    station, queries, bed = station[first:last], queries[first:last], bed[:, first:last]
    sources = load_sources([ROOT/r['construction_directory'] for r in reports],
                           [ROOT/r['source_profile'] for r in reports],bounded=True)
    _, owner = TerrainMosaic(sources).sample(queries[..., 0], queries[..., 1])
    if (owner < 0).any():
        raise ValueError('Missing classified-water source')
    padding_water = np.zeros(owner.shape, bool)
    for index, source in enumerate(sorted(sources, key=lambda s: s['core'][0])):
        grid = source['grid']
        sampled = sample_grid(grid['classified_water_mask'], queries, grid['corner_east_north_m'], True)
        if not np.isfinite(sampled[owner == index]).all():
            raise ValueError('Unclassified terrain padding')
        padding_water[owner == index] = sampled[owner == index] > .5
    grid = dict(nx=len(station), ny=len(lateral), dx=step, dy=step,
                origin_x=float(station[0]), origin_y=float(lateral[0]))
    for item in items:
        g = item['grid']
        start = max(0, int(round((station[0]-g['origin_x'])/step)))
        stop = min(g['nx'], int(round((station[-1]-g['origin_x'])/step))+1)
        for key in ('bed', 'depth', 'u', 'v', 'classified_water'):
            item[key] = item[key][:, start:stop]
        item['reference_surface'] = item['reference_surface'][start:stop]
        item['grid'] = dict(g, origin_x=g['origin_x']+start*step, nx=stop-start)
    state, classified, surface, covered = merge_registered(items, bed, grid, padding_water.T)
    h, u, v = (state[key] for key in ('depth', 'u', 'v'))
    target_q = scenarios[0]['boundaries'][0]['metadata']['target_discharge_m3s']
    if not np.allclose((h*u).sum(axis=0)*step, target_q, atol=1e-8, rtol=0):
        raise ValueError('Joined initial discharge changed')
    scenario = copy.deepcopy(scenarios[0])
    scenario['grid'] = grid
    west = np.array(scenarios[0]['boundaries'][0]['ghost_cells']).reshape(2, items[0]['grid']['ny'], 4)
    # These scenarios currently share a symmetric lateral lattice: embedding
    # the original west ghost in the wider strip retains its exact discharge.
    ghost = np.zeros((2, grid['ny'], 4)); ghost[:, :, 0] = bed[:, 0]
    row = int(round((items[0]['grid']['origin_y']-grid['origin_y'])/step))
    ghost[:, row:row+west.shape[1], :] = west
    scenario['boundaries'][0]['ghost_cells'] = ghost.reshape(-1, 4).tolist()
    scenario['boundaries'][1]['stage'] = float(surface[-1])
    scenario['metadata']['scenario_id'] = 'colorado_continuous_joined'
    scenario['metadata']['generator'] = Path(__file__).name
    scenario['metadata']['provenance']['joined_inputs'] = [p.relative_to(ROOT).as_posix() for p in inputs]
    out.mkdir(parents=True); pkg = out/'scenario'; pkg.mkdir()
    write_native_arrays(pkg, bed, h, u, v)
    for key in ('features', 'probes'):
        (pkg/(key+'.json')).write_text(json.dumps({key: []})+'\n')
    (pkg/'scenario.json').write_text(json.dumps(scenario, indent=2)+'\n')
    (out/'coordinate_map.json').write_bytes((frame_path.parent/'coordinate_map.json').read_bytes())
    np.savez_compressed(out/'reference.npz', station=station, lateral=lateral,
                        source_station=source_station, reference_surface=surface,
                        classified_water=classified)
    receipt = dict(schema='raftsim.colorado_catalog_solver_input.v1', name='Colorado continuous joined',
        grid=grid, source_core_interval_m=[core_lo, core_hi],
        source_station_range_m=[float(source_station[0]), float(source_station[-1])],
        source_inputs=[dict(path=p.relative_to(ROOT).as_posix(), sha256=sha(p/'build_report.json')) for p in inputs],
        continuous_terrain=reports[0]['continuous_terrain'], shared_hydraulic_frame=reports[0]['shared_hydraulic_frame'],
        dry_padding_cells=int((~covered).sum()), roughness_hypothesis=scenario['roughness'],
        cropped_exterior_halo_columns=[int(first), int(len(complete)-last)],
        limitations=['One native domain, not proof of convergence, streaming, boat passage or playable acceptance.',
                     'No curvilinear metric terms added; geographic-space validation remains necessary.'],
        files_sha256={str(p.relative_to(out)): sha(p) for p in out.rglob('*') if p.is_file()},
        solved=False, playable_map_created=False, accepted=False)
    (out/'build_report.json').write_text(json.dumps(receipt, indent=2)+'\n')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, action='append', required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = join(args.input, args.out.resolve())
    print(json.dumps({k: v for k, v in result.items() if k != 'files_sha256'}, indent=2))
