"""Cook packages for the discharge-consistent South Fork bed (numpy only).

1. Rebuild every 1 m hydraulic core of the union cook geometry: cells owned
   by the inferred coarse terrain (owners 1 and 4) are resampled from the new
   2 m bed with the exact NW-NE-SW / NE-SE-SW triangle rule of the render and
   collision meshes; registered-rapid, seam and rock-union cells (owners 2, 3,
   5), captured surface, water mask and owners are copied unchanged. With the
   previous bed this rule reproduces the existing cores bit for bit.
2. Initialise water at the captured (hydro-flattened) surface inside the
   captured water mask, with a station-binned conveyance velocity seed along
   the route tangent (as prepare_south_fork_coupled_flow.py).
3. Write raftsim_cartesian_cook packages for the whole river, or for
   overlapping station sections (internal cuts: upstream discharge profile
   carrying the authored Q, downstream outflow at the captured surface).

Args: bed_dir output_dir [--sections a,b,c,...] [--overlap-m 400]
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach'
GEOMETRY = ROOT / 'tmp/south-fork-control-ablation-union-geometry-v1-20260916/manifest.json'
TEMPLATE = ROOT / 'physics/data/validation/milestone17/analytic_fixtures/fixtures/lake_at_rest_balance/scenario/scenario.json'
Q = 45.3069545472
N_MANNING = 0.035
BIN = 10.0
LOWER = -1000.0
INFERRED_OWNERS = (1, 4)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def gauss1d(values, sigma_bins):
    r = int(np.ceil(3 * sigma_bins))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma_bins) ** 2)
    k /= k.sum()
    return np.convolve(np.pad(values, r, mode='edge'), k, mode='valid')


def sample_regular_triangles(z, x0, y0, cell, east, north):
    """Same arithmetic as south_fork_composite_terrain.sample_regular_triangles."""
    cf, rf = (east - x0) / cell, (y0 - north) / cell
    c, r = np.floor(cf).astype(int), np.floor(rf).astype(int)
    if np.any((c < 0) | (c >= z.shape[1] - 1) | (r < 0) | (r >= z.shape[0] - 1)):
        raise ValueError('Outside coarse terrain domain')
    u, v = cf - c, rf - r
    a, b, cc, d = z[r, c], z[r, c + 1], z[r + 1, c], z[r + 1, c + 1]
    if not np.isfinite(np.stack((a, b, cc, d))).all():
        raise ValueError('Coarse terrain has an uncaptured gap')
    return np.where(u + v <= 1, a * (1 - u - v) + b * u + cc * v, b * (1 - v) + cc * (1 - u) + d * (u + v - 1))


def nearest_route(xy, rp):
    """Index of the nearest route point for local metre coordinates xy (N, 2)."""
    out = np.empty(len(xy), int)
    for k0 in range(0, len(xy), 20000):
        q = xy[k0:k0 + 20000]
        lo, hi = q.min(0) - 400, q.max(0) + 400
        cand = np.nonzero((rp[:, 0] > lo[0]) & (rp[:, 0] < hi[0]) & (rp[:, 1] > lo[1]) & (rp[:, 1] < hi[1]))[0]
        if not len(cand):
            cand = np.arange(len(rp))
        best = np.full(len(q), np.inf); bi = np.zeros(len(q), int)
        for j0 in range(0, len(cand), 1000):
            cc = cand[j0:j0 + 1000]
            d = (q[:, None, 0] - rp[None, cc, 0]) ** 2 + (q[:, None, 1] - rp[None, cc, 1]) ** 2
            j = d.argmin(1); dv = d[np.arange(len(q)), j]
            upd = dv < best; best[upd] = dv[upd]; bi[upd] = cc[j[upd]]
        out[k0:k0 + 20000] = bi
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bed_dir', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--sections', default='')
    parser.add_argument('--overlap-m', type=float, default=400.0)
    parser.add_argument('--old-bed', action='store_true', help='control: keep the previous bed (verifies reproduction)')
    args = parser.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT / 'tmp') and not out.exists(), 'Fresh tmp output required'
    bed_manifest = json.loads((args.bed_dir / 'manifest.json').read_text())
    bed_path = ROOT / bed_manifest['outputs']['coarse_bed']['path']
    assert sha(bed_path) == bed_manifest['outputs']['coarse_bed']['sha256']
    with np.load(bed_path) as a:
        coarse = a['coarse_bed_navd88_m']
    x0, y0 = bed_manifest['grid']['first_vertex_utm_m']; cell = bed_manifest['grid']['cell_m']
    geometry = json.loads(GEOMETRY.read_text())
    datum = float(geometry['vertical_datum_navd88_m'])
    origin_utm = np.asarray(geometry['world_origin_utm_m'])
    route = json.loads((BASE / 'playable_route/coordinate_map.json').read_text())
    pts = np.asarray(route['points'])
    tangent = np.column_stack((pts[:, 4], -pts[:, 3]))
    regions = geometry['regions']
    out.mkdir(parents=True)
    core_dir = out / 'cores'; core_dir.mkdir()
    cells = []
    changed_cores = 0
    max_abs_change = 0.0
    offsets = np.arange(80) - 40
    xx, yy = np.meshgrid(offsets, offsets)
    new_regions = []
    for i, rec in enumerate(regions):
        path = ROOT / rec['geometry_file']
        assert sha(path) == rec['geometry_sha256'], rec['name']
        with np.load(path, allow_pickle=False) as a:
            fields = {k: a[k].copy() for k in a.files}
        cx, cy = rec['center_utm_m']
        east = (cx + xx).astype(float); north = (cy + yy).astype(float)
        owner = fields['terrain_owner'].astype(int)
        m = np.isin(owner, INFERRED_OWNERS)
        bed = fields['bed_navd88_m'].copy()
        if not args.old_bed and m.any():
            bed[m] = sample_regular_triangles(coarse, x0, y0, cell, east[m], north[m])
        delta = np.abs(bed - fields['bed_navd88_m'])
        new_rec = copy.deepcopy(rec)
        if delta.max() > 0:
            changed_cores += 1
            max_abs_change = max(max_abs_change, float(delta.max()))
            fields['bed_navd88_m'] = bed
            target = core_dir / (rec['name'] + '.npz')
            np.savez_compressed(target, **fields)
            new_rec.update(geometry_file=target.relative_to(ROOT).as_posix(), geometry_sha256=sha(target),
                           retained_geometry_file=rec['geometry_file'], retained_geometry_sha256=rec['geometry_sha256'],
                           discharge_bed_changed_cells=int((delta > 0).sum()))
        new_regions.append(new_rec)
        water = fields['captured_water_mask'].astype(bool)
        b = bed - datum
        s = fields['captured_surface_navd88_m'] - datum
        depth = np.where(water, np.maximum(s - b, 0.0), 0.0)
        cells.append(dict(bed=b, surface=s, depth=depth, water=water, center=(cx, cy)))
        if (i + 1) % 100 == 0:
            print(f'cores {i + 1}/{len(regions)}', flush=True)
    new_geometry = copy.deepcopy(geometry)
    new_geometry['regions'] = new_regions
    new_geometry['discharge_bed'] = dict(manifest=(args.bed_dir / 'manifest.json').resolve().relative_to(ROOT).as_posix(),
                                         manifest_sha256=sha(args.bed_dir / 'manifest.json'), previous_bed_control=args.old_bed,
                                         changed_core_count=changed_cores, maximum_absolute_bed_change_m=max_abs_change,
                                         retained_geometry_manifest=GEOMETRY.relative_to(ROOT).as_posix(),
                                         retained_geometry_manifest_sha256=sha(GEOMETRY))
    geometry_path = out / 'geometry_manifest.json'
    geometry_path.write_text(json.dumps(new_geometry, indent=2) + '\n')
    print('changed cores', changed_cores, 'max change', max_abs_change, flush=True)

    # Station per wet cell, with endpoint projection (as the original prep).
    rp = pts[:, 1:3]
    all_xy, owners = [], []
    for n, c in enumerate(cells):
        r, cc = np.nonzero(c['water'])
        xy = np.column_stack((c['center'][0] + cc - 40 - origin_utm[0], c['center'][1] + r - 40 - origin_utm[1]))
        all_xy.append(xy); owners.append(np.full(len(r), n))
    all_xy = np.concatenate(all_xy); owners = np.concatenate(owners)
    near = nearest_route(all_xy, rp)
    station = pts[near, 0].copy()
    for endpoint in (0, len(pts) - 1):
        m = near == endpoint
        station[m] += np.sum((all_xy[m] - rp[endpoint]) * tangent[endpoint], axis=1)
    bins = int(np.ceil((pts[-1, 0] + 2000 - LOWER) / BIN))
    idx = np.floor((station - LOWER) / BIN).astype(int)
    assert idx.min() >= 0 and idx.max() < bins
    depth_all = np.concatenate([c['depth'][c['water']] for c in cells])
    conveyance = gauss1d(np.bincount(idx, weights=depth_all ** (5 / 3), minlength=bins) / BIN, 1.0)
    split = np.cumsum([c['water'].sum() for c in cells])[:-1]
    for c, st, nr, ib in zip(cells, np.split(station, split), np.split(near, split), np.split(idx, split)):
        k = conveyance[ib]
        h = c['depth'][c['water']]
        mag = np.divide(Q * h ** (2 / 3), k, out=np.zeros_like(k), where=k > 1e-9)
        mag = np.minimum(mag, 6.0)
        u = np.zeros((80, 80)); v = np.zeros((80, 80)); sta = np.full((80, 80), np.nan)
        u[c['water']] = mag * tangent[nr, 0]; v[c['water']] = mag * tangent[nr, 1]; sta[c['water']] = st
        c['u'], c['v'], c['station'] = u, v, sta

    origins = np.array([r['grid_origin_local_m'] for r in regions])
    by_origin = {(int(round(o[0])), int(round(o[1]))): i for i, o in enumerate(origins)}
    global_edges = {(r['region'], r['edge']): r['endpoint'] for r in geometry['open_geometry_edges']}
    name_to_index = {r['name']: i for i, r in enumerate(regions)}
    global_roles = {(name_to_index[k[0]], k[1]): v for k, v in global_edges.items()}
    template = json.loads(TEMPLATE.read_text())
    edges = dict(west=(np.s_[:, 0], (-1, 0), (1, 0)), east=(np.s_[:, -1], (1, 0), (-1, 0)),
                 south=(np.s_[0, :], (0, -1), (0, 1)), north=(np.s_[-1, :], (0, 1), (0, -1)))

    def tile_station_range(i):
        s = cells[i]['station'][cells[i]['water']]
        return (s.min(), s.max()) if len(s) else (np.nan, np.nan)
    ranges = [tile_station_range(i) for i in range(len(cells))]
    if args.sections:
        cuts = [float(x) for x in args.sections.split(',')]
        cuts = [-1e9] + cuts + [1e9]
        sections = []
        for a, b in zip(cuts[:-1], cuts[1:]):
            members = [i for i, (lo, hi) in enumerate(ranges) if np.isfinite(lo) and hi >= a - args.overlap_m and lo <= b + args.overlap_m]
            sections.append(dict(name=f'section_{len(sections):02d}', core_range_m=[a, b], tiles=members))
    else:
        sections = [dict(name='full', core_range_m=[-1e9, 1e9], tiles=list(range(len(cells))))]

    for sec in sections:
        sdir = out / sec['name']; sdir.mkdir()
        members = set(sec['tiles'])
        local = {i: n for n, i in enumerate(sec['tiles'])}
        mid = 0.5 * (max(sec['core_range_m'][0], -1000) + min(sec['core_range_m'][1], pts[-1, 0] + 1000))
        boundary, upstream = {}, []
        for i in sec['tiles']:
            c = cells[i]
            for edge, (sl, (ddx, ddy), inward) in edges.items():
                key = (int(round(origins[i, 0] + 80 * ddx)), int(round(origins[i, 1] + 80 * ddy)))
                nbr = by_origin.get(key)
                if nbr in members:
                    continue
                ew = c['water'][sl] & (c['depth'][sl] > 0.05)
                if not ew.any():
                    continue  # no flowing water on this face: bank
                if (i, edge) in global_roles:
                    role = global_roles[(i, edge)]
                elif nbr is None:
                    continue  # true bank face of the full geometry
                else:
                    role = 'upstream' if np.median(c['station'][sl][ew]) < mid else 'downstream'
                h = c['depth'][sl]
                if role == 'upstream':
                    t0 = np.array([c['u'][sl][ew].sum(), c['v'][sl][ew].sum()])
                    t0 = t0 / max(np.linalg.norm(t0), 1e-9)
                    proj = inward[0] * t0[0] + inward[1] * t0[1]
                    if proj <= 0.1:
                        print(f'WARNING {sec["name"]} {regions[i]["name"]} {edge}: upstream face does not enter ({proj:.2f}); bank', flush=True)
                        continue
                    upstream.append(dict(i=i, edge=edge, h=h, bed=c['bed'][sl], t=t0, w=h ** (5 / 3) * proj))
                else:
                    boundary[(i, edge)] = dict(kind='outflow', stage=float(np.median(c['surface'][sl][ew])), role='downstream')
        wsum = sum(u['w'].sum() for u in upstream)
        assert upstream and wsum > 0, f'{sec["name"]}: no upstream face'
        imposed = 0.0
        for it in upstream:
            mag = np.where(it['h'] > 1e-6, Q * it['h'] ** (2 / 3) / wsum, 0.0)
            prof = np.column_stack((it['bed'], it['h'], mag * it['t'][0], mag * it['t'][1]))
            imposed += float(Q * it['w'].sum() / wsum)
            boundary[(it['i'], it['edge'])] = dict(kind='discharge_profile', ghost_cells=np.tile(prof, (2, 1)).tolist(), role='upstream')
        assert abs(imposed - Q) < 1e-9
        manifest = dict(schema='raftsim.cartesian_flow_cook.v1', dt_seconds=0.05, packages=[], boundary_probes=[],
                        geometry_manifest=geometry_path.relative_to(ROOT).as_posix(), geometry_manifest_sha256=sha(geometry_path),
                        target_discharge_m3s=Q, authored_combined_inlet_discharge_m3s=imposed, vertical_datum_navd88_m=datum,
                        section=dict(name=sec['name'], core_range_m=sec['core_range_m'], overlap_m=args.overlap_m, tile_count=len(sec['tiles'])),
                        initial_state='captured surface inside captured water mask; conveyance velocity seed along route tangent',
                        measured_velocity=False, measured_bathymetry=False, settled_hydraulics=False, normal_map_integrated=False, inputs=[])
        for i in sec['tiles']:
            rec = new_regions[i]; c = cells[i]
            pkg = sdir / rec['name']; pkg.mkdir()
            np.save(pkg / 'bed.npy', c['bed'])
            h, u, v = c['depth'], c['u'], c['v']
            np.savez_compressed(pkg / 'initial_state.npz', depth=h, eta=c['bed'] + h, u=u, v=v, hu=h * u, hv=h * v, wet=h > 1e-6)
            (pkg / 'features.json').write_text('{"features":[]}\n')
            (pkg / 'probes.json').write_text('{"probes":[]}\n')
            sc = copy.deepcopy(template)
            sc['metadata'] = dict(scenario_id=rec['name'], scenario_type='real_world', fixture_kind=None, river_id='south_fork_american',
                                  flow_band='median_runnable', generator='prepare_south_fork_discharge_bed_cook.py', generator_version='20260926-v1',
                                  description='Discharge-consistent inferred bed; captured-surface initial water; not accepted', confidence_score=.3,
                                  coordinate_reference_system='Unrotated EPSG:32610 east/north metres relative to declared world origin; NAVD88 minus datum',
                                  provenance=dict(source_geometry_file=rec['geometry_file'], source_geometry_sha256=rec['geometry_sha256'],
                                                  submerged_bed_is_uncalibrated_inference=True, discharge_consistent_bed=not args.old_bed,
                                                  initial_velocity_is_inferred=True, target_discharge_m3s=Q, normal_map_integrated=False))
            sc['grid'] = dict(nx=80, ny=80, dx=1., dy=1., origin_x=rec['grid_origin_local_m'][0], origin_y=rec['grid_origin_local_m'][1])
            sc.update(fixed_dt=.05, duration=600., roughness=N_MANNING, feature_count=0, probe_count=0)
            sc['boundaries'] = []
            for edge in ('west', 'east', 'south', 'north'):
                bd = dict(edge=edge, kind='bank')
                spec = boundary.get((i, edge))
                if spec:
                    bd.update({k: v for k, v in spec.items() if k != 'role'})
                    manifest['boundary_probes'].append(dict(tile_index=local[i], edge=edge, role=spec['role']))
                sc['boundaries'].append(bd)
            (pkg / 'scenario.json').write_text(json.dumps(sc, indent=2) + '\n')
            manifest['packages'].append(rec['name'])
            manifest['inputs'].append(dict(name=rec['name'], source_geometry_sha256=rec['geometry_sha256'],
                                           files={n: sha(pkg / n) for n in ('scenario.json', 'bed.npy', 'initial_state.npz', 'features.json', 'probes.json')}))
        (sdir / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        np.savez_compressed(sdir / 'station_map.npz', tiles=np.array(sec['tiles']),
                            station=np.stack([cells[i]['station'] for i in sec['tiles']]),
                            surface=np.stack([cells[i]['surface'] for i in sec['tiles']]),
                            water=np.stack([cells[i]['water'] for i in sec['tiles']]))
        print(sec['name'], 'tiles', len(sec['tiles']), 'boundaries', sorted((regions[k[0]]['name'], k[1], v['role']) for k, v in boundary.items()), flush=True)


if __name__ == '__main__':
    main()
