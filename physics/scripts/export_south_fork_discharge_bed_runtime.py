"""Export the discharge-consistent South Fork cook in the runtime atlas format.

Same layout and checks as export_cartesian_runtime_atlas.py (shared atlas,
799 source packets of 321 x 321 m, streaming manifest), adapted to a new bed:

* Source packets start from the current runtime's packets (including the
  eight Troublemaker rock-union packets). Only cells owned by the inferred
  coarse terrain (owners 1, 4) are resampled from the new 2 m bed with the
  render/collision triangle rule; every other cell is copied unchanged.
* Every packet cell that intersects a cooked tile must equal the atlas bed
  exactly (the original exporter's gate).
* Live-window centre bounds are copied from the current coverage-checked
  streaming manifest: grids, captured masks and hydraulic bounds are
  unchanged and are asserted equal.

Numpy only. Diagnostic metadata never claims settling or acceptance.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
INFERRED_OWNERS = (1, 4)
SOLVER = dict(runtime_cartesian_coupled_config=True, solver_mode='finite_volume', flux_scheme='hll', spatial_order=2,
              fixed_dt_s=.05, cfl=.2, dry_tolerance=1.e-6, roughness_manning=.035, roughness_scale=1.,
              bed_slope_source_scale=1., feature_strength_scale=0., preserve_initial_mass=False)


def sha(path):
    with Path(path).open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def array_meta(path, relative_to, shape, dtype):
    return dict(file=Path(os.path.relpath(path, relative_to)).as_posix(), sha256=sha(path), shape=list(shape), dtype=dtype)


def sample_regular_triangles(z, x0, y0, cell, east, north):
    cf, rf = (east - x0) / cell, (y0 - north) / cell
    c, r = np.floor(cf).astype(int), np.floor(rf).astype(int)
    if np.any((c < 0) | (c >= z.shape[1] - 1) | (r < 0) | (r >= z.shape[0] - 1)):
        raise ValueError('Outside coarse terrain domain')
    u, v = cf - c, rf - r
    a, b, cc, d = z[r, c], z[r, c + 1], z[r + 1, c], z[r + 1, c + 1]
    if not np.isfinite(np.stack((a, b, cc, d))).all():
        raise ValueError('Coarse terrain has an uncaptured gap')
    return np.where(u + v <= 1, a * (1 - u - v) + b * u + cc * v, b * (1 - v) + cc * (1 - u) + d * (u + v - 1))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('cook', type=Path)
    parser.add_argument('step', type=int)
    parser.add_argument('output', type=Path)
    parser.add_argument('--bank-audit', type=Path, required=True)
    parser.add_argument('--bed-dir', type=Path, required=True)
    parser.add_argument('--source-packets', type=Path, default=ROOT / 'tmp/south-fork-control-ablation-source-packets-v1-20260916/manifest.json')
    parser.add_argument('--streaming-template', type=Path, default=ROOT / 'tmp/control-ablation-runtime-4950s-v1-20260917/streaming_manifest_coverage_checked.json')
    args = parser.parse_args()
    output = args.output.resolve()
    assert output.is_relative_to(ROOT / 'tmp') and not output.exists()
    cook = args.cook.resolve()
    flow_path = Path((cook / 'input_manifest_path.txt').read_text().strip())
    assert sha(flow_path) == sha(cook / 'input_manifest.json')
    flow = json.loads(flow_path.read_text())
    geometry_path = ROOT / flow['geometry_manifest']
    assert sha(geometry_path) == flow['geometry_manifest_sha256']
    geometry = json.loads(geometry_path.read_text())
    assert [r['name'] for r in geometry['regions']] == flow['packages'], 'Export needs the full-river cook'
    bed_manifest = json.loads((args.bed_dir / 'manifest.json').read_text())
    assert geometry['discharge_bed']['manifest_sha256'] == sha(args.bed_dir / 'manifest.json'), 'Cook used a different bed'
    bed_path = ROOT / bed_manifest['outputs']['coarse_bed']['path']
    assert sha(bed_path) == bed_manifest['outputs']['coarse_bed']['sha256']
    with np.load(bed_path) as a:
        coarse = a['coarse_bed_navd88_m']
    x0, y0 = bed_manifest['grid']['first_vertex_utm_m']; cell = bed_manifest['grid']['cell_m']
    source = json.loads(args.source_packets.read_text())
    template = json.loads(args.streaming_template.read_text())
    assert [w['window_id'] for w in template['windows']] == [r['name'] for r in source['regions']]
    frame = cook / f'frame_{args.step:06d}'
    complete = json.loads((frame / 'complete.json').read_text())
    audit = json.loads(args.bank_audit.read_text())
    assert complete['step'] == args.step and complete['snapshot']
    assert audit['step'] == args.step and audit['input_manifest_sha256'] == sha(flow_path)
    assert audit['h_sha256'] == sha(frame / 'h.npy') and audit['all_artificial_banks_exactly_dry']
    state = {n: np.load(frame / f'{n}.npy', mmap_mode='r', allow_pickle=False) for n in ('h', 'u', 'v')}
    count = len(flow['packages'])
    assert all(a.dtype == np.dtype('<f8') and a.shape == (count * 80, 80) and np.isfinite(a).all() for a in state.values())
    assert state['h'].min() >= 0 and state['h'].max() <= 10 and np.hypot(state['u'], state['v']).max() <= 20
    datum = flow['vertical_datum_navd88_m']
    output.mkdir(parents=True)
    atlas_dir = output / 'atlas'; atlas_dir.mkdir()
    bed = np.empty_like(state['h'])
    tiles = []
    inputs = {r['name']: r for r in flow['inputs']}
    for i, record in enumerate(geometry['regions']):
        package = flow_path.parent / record['name']
        assert sha(package / 'bed.npy') == inputs[record['name']]['files']['bed.npy']
        scenario = json.loads((package / 'scenario.json').read_text())
        g = scenario['grid']
        assert (g['ny'], g['nx'], g['dx'], g['dy']) == (80, 80, 1., 1.) and [g['origin_x'], g['origin_y']] == record['grid_origin_local_m']
        assert scenario['roughness'] == .035
        bed[i * 80:(i + 1) * 80] = np.load(package / 'bed.npy', allow_pickle=False)
        tiles.append(dict(origin_m=record['grid_origin_local_m'], source_geometry_sha256=record['geometry_sha256']))
    np.save(atlas_dir / 'bed.npy', bed)
    atlas_arrays = dict(bed=array_meta(atlas_dir / 'bed.npy', atlas_dir, bed.shape, '<f8'))
    atlas_arrays.update({n: array_meta(frame / f'{n}.npy', atlas_dir, a.shape, '<f8') for n, a in state.items()})
    atlas = dict(schema='raftsim.cartesian_state_atlas.v1', tile_shape=[80, 80], grid_spacing_m=1., source_elevation_datum_m=datum,
                 dry_tolerance=1.e-6, tiles=tiles, arrays=atlas_arrays, physical_exterior_faces=flow['boundary_probes'],
                 source_frame=str(frame), source_time_seconds=complete['time_seconds'], input_manifest_sha256=sha(flow_path),
                 bank_audit_sha256=sha(args.bank_audit), discharge_bed_manifest_sha256=sha(args.bed_dir / 'manifest.json'),
                 terrain_union=geometry.get('terrain_union'), settled_hydraulics=False, normal_map_integrated=False)
    write_json(atlas_dir / 'manifest.json', atlas)
    atlas_hash = sha(atlas_dir / 'manifest.json')
    origins = np.asarray([t['origin_m'] for t in tiles])
    offsets = np.arange(321) - 160
    dx, dy = np.meshgrid(offsets, offsets)
    streaming = {k: v for k, v in template.items() if k != 'windows'}
    streaming['windows'] = []
    validation, verified, resampled, packets_changed = [], 0, 0, 0
    for i, (record, window) in enumerate(zip(source['regions'], template['windows'])):
        path = ROOT / record['geometry_file']
        assert sha(path) == record['geometry_sha256'], record['name']
        with np.load(path, allow_pickle=False) as packet:
            old_bed = packet['bed_navd88_m'].copy()
            captured = packet['captured_water_mask'].copy()
            owner = packet['terrain_owner'].astype(int)
        cx, cy = record['center_utm_m']
        m = np.isin(owner, INFERRED_OWNERS)
        new_bed = old_bed.copy()
        new_bed[m] = sample_regular_triangles(coarse, x0, y0, cell, (cx + dx[m]).astype(float), (cy + dy[m]).astype(float))
        resampled += int(m.sum()); packets_changed += int(np.any(new_bed != old_bed))
        packet_bed = new_bed - datum
        origin = np.asarray(record['grid_origin_local_m'])
        assert window['hydraulic_bounds_m'] == [*origin.tolist(), *(origin + 320).tolist()]
        relative = origins - origin
        assert np.max(np.abs(relative - np.rint(relative))) < 1.e-7
        relative = np.rint(relative).astype(int)
        modeled = np.zeros((321, 321), dtype=bool)
        gathered = {n: np.zeros((321, 321)) for n in state} if i in (0, 400, 798) else None
        for tile in np.flatnonzero(np.all(relative < 321, axis=1) & np.all(relative + 80 > 0, axis=1)):
            x, y = relative[tile]
            xa, ya = max(0, x), max(0, y); xb, yb = min(321, x + 80), min(321, y + 80)
            dest = np.s_[ya:yb, xa:xb]
            src = np.s_[tile * 80 + ya - y:tile * 80 + yb - y, xa - x:xb - x]
            assert not modeled[dest].any()
            assert np.array_equal(packet_bed[dest], bed[src]), record['name']
            modeled[dest] = True
            verified += int((yb - ya) * (xb - xa))
            if gathered is not None:
                for n in state:
                    gathered[n][dest] = state[n][src]
        directory = output / record['name']; directory.mkdir()
        arrays = {}
        for n, values in (('bed', packet_bed), ('captured_water_mask', captured)):
            np.save(directory / f'{n}.npy', values)
            arrays[n] = array_meta(directory / f'{n}.npy', directory, values.shape, values.dtype.str)
        manifest = dict(schema='raftsim.cooked_flow_fields.v1', coordinate_system='cartesian_east_north_m', source_elevation_datum_m=datum,
                        grid=dict(nx=321, ny=321, dx_m=1., dy_m=1., origin_x_m=float(origin[0]), origin_y_m=float(origin[1])),
                        solver=SOLVER, bands=[dict(band_id='median_runnable', arrays=arrays,
                                                   shared_cartesian_state=dict(manifest='../atlas/manifest.json', sha256=atlas_hash))],
                        source_geometry_sha256=record['geometry_sha256'], discharge_bed_manifest_sha256=sha(args.bed_dir / 'manifest.json'),
                        inferred_cells_resampled=int(m.sum()), settled_hydraulics=False, normal_map_integrated=False)
        if 'terrain_union' in record:
            manifest['terrain_union'] = record['terrain_union']
        write_json(directory / 'manifest.json', manifest)
        streaming['windows'].append(dict(window_id=record['name'], cooked_fields_manifest=(directory / 'manifest.json').relative_to(ROOT).as_posix(),
                                         hydraulic_bounds_m=window['hydraulic_bounds_m'], valid_live_center_bounds_m=window['valid_live_center_bounds_m']))
        if gathered is not None and window['valid_live_center_bounds_m']:
            rect = np.asarray(window['valid_live_center_bounds_m'][0])
            center = (rect[:2] + rect[2:]) * .5
            low = np.floor(center - origin - 112).astype(int) - 2
            high = np.ceil(center - origin + 112).astype(int) + 2
            assert not ((captured != 0) & ~modeled)[low[1]:high[1] + 1, low[0]:high[0] + 1].any()
            dense_dir = output / (record['name'] + '_dense_reference'); dense_dir.mkdir()
            dense = copy.deepcopy(manifest)
            dense['bands'][0].pop('shared_cartesian_state')
            dense_arrays = dict(bed=array_meta(directory / 'bed.npy', dense_dir, packet_bed.shape, '<f8'))
            gathered['wet_mask'] = (gathered['h'] > 1.e-6).astype(np.uint8)
            for n, values in gathered.items():
                np.save(dense_dir / f'{n}.npy', values)
                dense_arrays[n] = array_meta(dense_dir / f'{n}.npy', dense_dir, values.shape, '|u1' if n == 'wet_mask' else '<f8')
            dense['bands'][0]['arrays'] = dense_arrays
            write_json(dense_dir / 'manifest.json', dense)
            validation.append(dict(shared=record['name'], dense=dense_dir.name, center_m=center.tolist()))
        if (i + 1) % 100 == 0:
            print(f'Exported and verified {i + 1}/{len(source["regions"])} packets', flush=True)
    write_json(output / 'streaming_manifest_coverage_checked.json', streaming)
    write_json(output / 'validation_windows.json', dict(windows=validation, extent_m=[224., 224.]))
    report = dict(completed=True, source_packet_count=len(source['regions']), atlas_tile_count=count, exact_bed_intersection_cells=verified,
                  inferred_packet_cells_resampled=resampled, packets_with_changed_bed=packets_changed, atlas_manifest_sha256=atlas_hash,
                  source_packets_manifest=args.source_packets.resolve().relative_to(ROOT).as_posix(), source_packets_manifest_sha256=sha(args.source_packets),
                  streaming_template=args.streaming_template.resolve().relative_to(ROOT).as_posix(), streaming_template_sha256=sha(args.streaming_template),
                  live_center_bounds_copied_unchanged=True,
                  streaming_manifest_sha256=sha(output / 'streaming_manifest_coverage_checked.json'), validation_window_count=len(validation),
                  external_snapshot_dependencies={k: v['file'] for k, v in atlas_arrays.items() if k != 'bed'},
                  discharge_bed_manifest_sha256=sha(args.bed_dir / 'manifest.json'), settled_hydraulics=False, normal_map_integrated=False)
    write_json(output / 'export_audit.json', report)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
