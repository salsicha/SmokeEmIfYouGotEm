"""Assemble every registered Colorado source core without truncating the river.

Reuse hash-bound source seam receipts. Export the existing common Landscape
lattice, then require coverage of every classified water cell owned by each
core. This is terrain construction, not hydraulic or playable acceptance.
"""
import argparse
import json
from pathlib import Path
import shutil

import numpy as np

from build_colorado_catalog_evidence import ROOT, sha
from build_colorado_continuous_source_batches import plan_batches
from export_colorado_continuous_terrain import export, LandscapeTriangles
from review_colorado_continuous_bed_seam import screen


def validate_selection(index, rows):
    expected = [i for batch in plan_batches(index, 0) for i in batch]
    if ([r.get('core') for r in rows] != expected or
            any(type(r.get('core')) is not int for r in rows)):
        raise ValueError('Full route requires every ordered core, including its partial final core')
    if len({r['evidence'] for r in rows}) != len(rows):
        raise ValueError('One unique evidence source per core required')


def validate_seam(receipt, before, after, origins, station):
    if (receipt.get('schema') != 'raftsim.colorado_continuous_bed_seam.v1' or
            receipt.get('sources') != [before, after] or
            receipt.get('source_global_origins_m') != origins or
            receipt.get('seam_global_station_m') != station or
            receipt.get('half_width_m') != 100. or
            receipt.get('bed_screen_passed') is not True or
            not screen(receipt['statistics'])):
        raise ValueError('Missing, stale or failed source handoff')


def route_end_caps(route):
    points = np.asarray(route['points'], dtype=float)
    origin = np.asarray(route['horizontal_origin_epsg6404_m'], dtype=float)
    if (points.ndim != 2 or points.shape[1] != 5 or len(points) < 2 or
            origin.shape != (2,) or not np.isfinite(points).all() or not np.isfinite(origin).all()):
        raise ValueError('Invalid geographic route endpoints')
    xy = points[:, 1:3] + origin
    directions = np.array([xy[1]-xy[0], xy[-1]-xy[-2]])
    length = np.linalg.norm(directions, axis=1)
    if np.any(length <= 0): raise ValueError('Duplicate route endpoint vertices')
    return dict(stations=points[[0,-1], 0], positions=xy[[0,-1]], directions=directions/length[:,None])


def wet_coverage(grid, profile, terrain, batch_size=100000, end_caps=None):
    """Visit actual core-owned classified cells, not a centreline proxy."""
    if type(batch_size) is not int or batch_size <= 0:
        raise ValueError('Positive coverage batch size required')
    mask = grid['classified_water_mask']
    local_station = grid['station_m']
    halo_start, halo_end = profile['source_halo_interval_m']
    # Promote before adding long-river chainage: float32 addition otherwise
    # rounds a 453 km station by millimetres and defeats endpoint identity.
    station = np.asarray(local_station, dtype=np.float64) + halo_start
    bed = grid['bed_ellipsoid_m']
    if (mask.dtype.kind != 'b' or mask.shape != station.shape or bed.shape != mask.shape or
            mask.ndim != 2 or not np.array_equal(grid['cell_m'], [1., 1.])):
        raise ValueError('Invalid one-metre classified terrain grid')
    lo, hi = profile['source_core_interval_m']
    if not np.isfinite(station[mask]).all():
        raise ValueError('Nonfinite classified-water station')
    if end_caps is not None:
        for endpoint in end_caps['stations']:
            if halo_start <= endpoint <= halo_end:
                # Recover only exact endpoint clamping in the stored dtype.
                # The geographic half-plane check below is still mandatory;
                # neighbouring stations and later bends are never excluded.
                stored_endpoint = np.asarray(endpoint-halo_start, dtype=local_station.dtype)
                station[local_station == stored_endpoint] = endpoint
    # Both neighbouring cores may inspect the exact boundary; none omit it.
    rows, cols = np.nonzero(mask & (station >= lo) & (station <= hi))
    if not len(rows):
        raise ValueError('Source core has no classified water to verify')
    corner = np.asarray(grid['corner_east_north_m'])
    if corner.shape != (2,) or not np.isfinite(corner).all():
        raise ValueError('Invalid source geographic corner')
    missing = 0; examples = []; maximum = 0.; excluded = 0; inspected = 0
    for start in range(0, len(rows), batch_size):
        r, c = rows[start:start+batch_size], cols[start:start+batch_size]
        xy = np.column_stack((corner[0]+c+.5, corner[1]-r-.5))
        if end_caps is not None:
            # Nearest-profile station grids clamp rectangular-crop points
            # beyond the physical route to station zero/the final station.
            # Exclude ONLY those clamped points outside the geographic end
            # cross-sections, not lateral cells or later bends behind a plane.
            s = station[r,c]; outside = np.zeros(len(r), dtype=bool)
            for k, sign in ((0,-1.), (1,1.)):
                delta = (xy-end_caps['positions'][k]) @ end_caps['directions'][k]
                outside |= (np.abs(s-end_caps['stations'][k]) <= 1e-6) & (sign*delta > 1e-6)
            excluded += int(outside.sum()); r, c, xy = r[~outside], c[~outside], xy[~outside]
        inspected += len(r)
        if not len(r): continue
        reference = bed[r, c]
        if not np.isfinite(reference).all():
            raise ValueError('Nonfinite classified source bed')
        actual = terrain.sample(xy); absent = ~np.isfinite(actual)
        missing += int(absent.sum())
        examples.extend(xy[absent][:max(0, 8-len(examples))].tolist())
        if (~absent).any():
            maximum = max(maximum, float(np.abs(actual[~absent]-reference[~absent]).max()))
    if not inspected: raise ValueError('No classified cells inside geographic route endpoints')
    return dict(classified_core_cells=inspected, outside_route_endpoint_cells=excluded,
        missing_terrain_cells=missing,
        missing_examples_epsg6404_m=examples, source_vs_encoded_terrain_max_difference_m=maximum,
        coverage_passed=missing == 0,
        qualification='Every classified core cell checked; coverage_passed reports the result. Height difference is diagnostic, not solver agreement')


def run(selection_path, out):
    selection_path = Path(selection_path).resolve(); out = Path(out).resolve()
    selection_path.relative_to(ROOT); out.relative_to(ROOT)
    if out.exists():
        raise ValueError('Fresh full-route assembly required; preserve existing outputs')
    selection = json.loads(selection_path.read_text())
    if selection.get('schema') != 'raftsim.colorado_full_terrain_selection.v1':
        raise ValueError('Explicit full-route selection required')
    def resolve(name):
        path = (ROOT/name).resolve(); path.relative_to(ROOT); return path
    protected = {selection_path: sha(selection_path)}
    def bind(path, digest):
        if sha(path) != digest: raise ValueError('Changed assembly input: '+str(path))
        if path in protected and protected[path] != digest: raise ValueError('Conflicting input identity')
        protected[path] = digest
    index_path = resolve(selection['windows'])/'index.json'
    bind(index_path, selection['index_sha256']); index = json.loads(index_path.read_text())
    route_path = resolve(selection['route']); bind(route_path, selection['route_sha256'])
    route = json.loads(route_path.read_text()); points = np.asarray(route['points'])
    end_caps = route_end_caps(route)
    if (points.ndim != 2 or points.shape[1] != 5 or len(points) < 2 or not np.isfinite(points).all() or
            np.any(np.diff(points[:, 0]) <= 0) or points[0, 0] != 0. or
            points[-1, 0] != index['route_length_m']):
        raise ValueError('Coordinate chart does not cover the complete source route')
    rows = selection['sources']; validate_selection(index, rows)
    evidence = []; profiles = []; identities = []
    for i, row in enumerate(rows):
        folder = resolve(row['evidence']); manifest_path = folder/'manifest.json'
        bind(manifest_path, row['manifest_sha256']); manifest = json.loads(manifest_path.read_text())
        window = index['windows'][i]; profile = index_path.parent/(window['tile_id']+'.json')
        p = json.loads(profile.read_text())
        if (any(p.get(k) != window.get(k) for k in
                ('name', 'tile_id', 'source_core_interval_m', 'source_halo_interval_m')) or
                manifest['name'] != window['name'] or
                manifest['parameters']['inferred_dry_shore_clearance_m'] != 1.):
            raise ValueError('Core identity or shared shore construction policy disagrees')
        captures = {resolve(name): h for name, h in manifest['source_files_sha256'].items()}
        if profile not in captures: raise ValueError('Source profile absent from capture lineage')
        for path, digest in captures.items():
            if path not in protected: bind(path, digest)
            elif protected[path] != digest: raise ValueError('Conflicting captured source identity')
        bind(folder/'evidence_grid.npz', manifest['evidence_grid_sha256'])
        identity = dict(directory=str(folder), manifest_sha256=row['manifest_sha256'],
                        grid_sha256=manifest['evidence_grid_sha256'])
        if i:
            seam_path = resolve(row['seam']); bind(seam_path, row['seam_sha256'])
            validate_seam(json.loads(seam_path.read_text()), identities[-1], identity,
                [index['windows'][j]['source_halo_interval_m'][0] for j in (i-1, i)],
                window['source_core_interval_m'][0])
        identities.append(identity); evidence.append(folder); profiles.append(profile)
    def disk_check():
        if shutil.disk_usage(ROOT).free < 40*1024**3:
            raise ValueError('Preserve 40 GiB disk headroom; no source deletion')
    disk_check(); out.mkdir(parents=True)
    (out/'launch.json').write_text(json.dumps(dict(selection_sha256=sha(selection_path),
        core_count=len(rows), source_interval_m=[0., index['route_length_m']],
        reused_seam_receipts=len(rows)-1, hydraulic_accepted=False, engine_accepted=False), indent=2))
    stage = 'common_landscape'
    try:
        result = export(evidence, profiles, route_path, out/'terrain')
        print('EXPORTED', len(result['chunks']), 'common-lattice chunks', flush=True)
        disk_check(); stage = 'full_classified_water_coverage'
        terrain = LandscapeTriangles(out/'terrain'); coverage = []
        (out/'coverage').mkdir()
        for i, (folder, profile) in enumerate(zip(evidence, profiles)):
            disk_check()
            with np.load(folder/'evidence_grid.npz', allow_pickle=False) as grid:
                item = wet_coverage(grid, json.loads(profile.read_text()), terrain, end_caps=end_caps)
            item['core'] = i; coverage.append(item)
            (out/'coverage'/f'core{i:04d}.json').write_text(json.dumps(item, indent=2))
            print(f'COVERAGE {i:04d}: {item["missing_terrain_cells"]} missing of {item["classified_core_cells"]}', flush=True)
        stage = 'terminal_identity'
        if any(sha(path) != digest for path, digest in protected.items()):
            raise ValueError('Source changed during full-route assembly')
        receipt = dict(core_count=len(rows), source_interval_m=[0., index['route_length_m']],
            terrain_chunks=len(result['chunks']),
            shared_edge_max_encoded_difference=result['shared_edge_max_encoded_difference'],
            incomplete_perimeter_chunks=len(result['incomplete_source_chunks']),
            classified_core_cells=sum(c['classified_core_cells'] for c in coverage),
            outside_route_endpoint_cells=sum(c['outside_route_endpoint_cells'] for c in coverage),
            missing_terrain_cells=sum(c['missing_terrain_cells'] for c in coverage),
            all_classified_water_covered=all(c['coverage_passed'] for c in coverage),
            source_files_unchanged=True, reused_seam_receipts=len(rows)-1,
            hydraulic_accepted=False, engine_accepted=False, vegetation_complete=False,
            full_river_playable=False)
        filename = 'completed.json' if receipt['all_classified_water_covered'] else 'rejected.json'
        (out/filename).write_text(json.dumps(receipt, indent=2))
        return receipt
    except Exception as error:
        (out/'failure.json').write_text(json.dumps(dict(stage=stage, error=str(error),
            partial_sources_preserved=True), indent=2))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selection', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = run(args.selection, args.out)
    print(json.dumps(result, indent=2))
    if not result['all_classified_water_covered']: raise SystemExit(1)
