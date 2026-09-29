"""Map-aligned (Cartesian) cook packages for the Zambezi evidence reach (numpy only).

The Batoka Gorge zigzags through hairpins of 25-40 m radius, which a
curvilinear station/lateral grid cannot follow. The solver has no metric
terms, so an unrotated east/north grid is exact for it; this builds
raftsim_cartesian_cook packages on one:

* grid: --cell-m cells in --tile-cells square tiles on a lattice aligned so
  that one tile edge crosses the river at the inflow cut (a horizontal line
  where the river runs south below the Boiling Pot) and one at the outflow cut
  (a vertical line where it runs west at the reach end);
* tiles: every tile holding evidence river cells with station inside the
  reach, plus the dry 8-neighbours of those tiles (spill room); tiles holding
  only water outside the reach are left out, so the cuts are tile faces;
* bed: the evidence bed (LiDAR-free here: inferred channel bed, harmonic bank
  zone, GLO-30 beyond) averaged over each cell;
* initial water: the evidence reference surface inside the evidence river,
  with a conveyance velocity seed along the midline tangent;
* boundaries: exterior faces carrying reach water at the inflow cut get a
  discharge profile for --discharge-m3s (split by h^5/3 x inward projection),
  faces at the outflow cut an outflow at the face's reference stage, all
  other exterior faces are banks.

Frame: local metres east/north of --world-origin (UTM 35S); heights EGM2008
minus --datum-m. Output: <out>/manifest.json (raftsim.cartesian_flow_cook.v1)
and one scenario package per tile, plus station_map.npz for the comparison.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / 'physics/data/validation/milestone17/analytic_fixtures/fixtures/lake_at_rest_balance/scenario/scenario.json'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('evidence', type=Path)
    ap.add_argument('out', type=Path)
    ap.add_argument('--discharge-m3s', type=float, default=None, help='default: the evidence manifest discharge')
    ap.add_argument('--cell-m', type=float, default=2.0)
    ap.add_argument('--tile-cells', type=int, default=64)
    ap.add_argument('--inflow-north-m', type=float, default=8017440.0, help='UTM northing of the horizontal inflow cut (station ~160 m)')
    ap.add_argument('--outflow-east-m', type=float, default=378460.0, help='UTM easting of the vertical outflow cut')
    ap.add_argument('--world-origin', type=float, nargs=2, default=None, help='UTM of local (0, 0); default west edge, north-south centre')
    ap.add_argument('--datum-m', type=float, default=700.0)
    ap.add_argument('--roughness', type=float, default=0.045)
    ap.add_argument('--dt', type=float, default=0.05)
    ap.add_argument('--seed-cook', type=Path, default=None,
                    help='warm start: take the free surface and velocity of this raftsim_cartesian_cook output (last frame; same tiles) over the new bed')
    ap.add_argument('--seed-velocity', action='store_true',
                    help='seed conveyance velocities along the midline tangent (at hairpins the nearest tangent can point into a wall; '
                         'the default cold start is still water at the reference surface)')
    args = ap.parse_args()
    out = args.out.resolve()
    assert not out.exists(), 'fresh output folder required'
    ev = args.evidence.resolve()
    evm = json.loads((ev / 'manifest.json').read_text())
    X0, Y1, NX, NY = evm['grid']['x0'], evm['grid']['y_top'], evm['grid']['nx'], evm['grid']['ny']
    Q = args.discharge_m3s or evm['parameters']['discharge_m3s']
    g = np.load(ev / 'evidence_grid.npz')
    bed1, river1, st1, ws1 = g['bed'].astype(np.float64), g['river'], g['station'].astype(np.float64), g['ws'].astype(np.float64)
    s_in, s_out = evm['statistics']['reach_station_m']
    cl = np.array(json.loads((ev / 'centreline.json').read_text())['points_xy_station'])
    origin = np.array(args.world_origin if args.world_origin else (X0, Y1 - NY / 2.0))
    D, T = args.cell_m, args.tile_cells
    TM = D * T
    # lattice: lines x = ax + k*TM, y = ay + k*TM through both cuts (in UTM)
    ax = args.outflow_east_m % TM; ay = args.inflow_north_m % TM
    # tiles covering the evidence window (tile index (i, j): east i, north j)
    i0 = int(np.ceil((X0 - ax) / TM)); i1 = int(np.floor((X0 + NX - ax) / TM)) - 1
    j0 = int(np.ceil((Y1 - NY - ay) / TM)); j1 = int(np.floor((Y1 - ay) / TM)) - 1
    # the reach starts at the inflow cut: water north of it (the Boiling Pot) is outside
    north1 = (Y1 - np.arange(NY) - 0.5)[:, None]
    # and it ends at the outflow cut: the reach tail west of it is outside too
    east1 = (X0 + np.arange(NX) + 0.5)[None, :]
    tail = (np.nan_to_num(st1, nan=-1e9) > s_out - 100.0) & (east1 < args.outflow_east_m)
    reach_water = river1 & np.isfinite(st1) & (st1 >= s_in) & (st1 <= s_out) & (north1 < args.inflow_north_m) & ~tail
    other_water = river1 & ~reach_water

    def tile_block(i, j, a):
        """a (1 m, row 0 north) over tile (i, j) as (T*D rows from south, T*D cols from west)."""
        e0 = ax + i * TM; n0 = ay + j * TM
        c0 = int(round(e0 - X0)); r1 = int(round(Y1 - n0)); r0 = r1 - int(TM)
        return a[r0:r1, c0:c0 + int(TM)][::-1]   # flip so row 0 is south

    has_reach, has_other = {}, {}
    for i in range(i0, i1 + 1):
        for j in range(j0, j1 + 1):
            has_reach[(i, j)] = bool(tile_block(i, j, reach_water).any())
            has_other[(i, j)] = bool(tile_block(i, j, other_water).any())
    members = {k for k, v in has_reach.items() if v}
    assert not any(has_other[k] for k in members if k[1] * TM + ay >= args.inflow_north_m), 'water above the inflow cut inside the tile set'
    spill = set()
    for (i, j) in members:
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                k = (i + di, j + dj)
                if k in has_reach and k not in members and not has_other[k]:
                    spill.add(k)
    tiles = sorted(members | spill)
    print(f'lattice offset ({ax:.1f}, {ay:.1f}) m; {len(members)} reach tiles + {len(spill)} spill tiles of {TM:.0f} m', flush=True)

    # per-station reference surface and conveyance velocity seed (evidence 1 m -> cell means)
    ctx, cty = np.gradient(cl[:, 0]), np.gradient(cl[:, 1]); cn = np.hypot(ctx, cty); ctx, cty = ctx / cn, cty / cn
    k = int(round(D))
    cells = {}
    for (i, j) in tiles:
        b = tile_block(i, j, bed1).reshape(T, k, T, k).mean((1, 3))
        rw = tile_block(i, j, reach_water).reshape(T, k, T, k).mean((1, 3)) >= 0.5
        stb = np.nanmedian(np.where(tile_block(i, j, reach_water), tile_block(i, j, st1), np.nan).reshape(T, k, T, k).transpose(0, 2, 1, 3).reshape(T, T, -1), axis=2) if rw.any() else np.full((T, T), np.nan)
        wsb = np.nanmedian(np.where(tile_block(i, j, reach_water), tile_block(i, j, ws1), np.nan).reshape(T, k, T, k).transpose(0, 2, 1, 3).reshape(T, T, -1), axis=2) if rw.any() else np.full((T, T), np.nan)
        wet = rw & np.isfinite(wsb) & (wsb - b > 0.02)
        h = np.where(wet, wsb - b, 0.0)
        cells[(i, j)] = dict(bed=b, h=h, wet=wet, station=np.where(wet, stb, np.nan), surface=np.where(wet, wsb, np.nan))
    # conveyance seed: per 10 m station bin, Q split by h^5/3 over the bin's cross-section cells
    allst = np.concatenate([c['station'][c['wet']] for c in cells.values()])
    allh = np.concatenate([c['h'][c['wet']] for c in cells.values()])
    nb = int(np.ceil((allst.max() + 1) / 10.0)) + 1
    conv = np.bincount((allst // 10).astype(int), weights=allh ** (5 / 3), minlength=nb) * D / (10.0 / D)
    for c in cells.values():
        u = np.zeros((T, T)); v = np.zeros((T, T))
        if c['wet'].any():
            s = c['station'][c['wet']]; hh = c['h'][c['wet']]
            idx = np.clip(np.searchsorted(cl[:, 2], s), 0, len(cl) - 1)
            mag = np.minimum(Q * hh ** (2 / 3) / np.maximum(conv[(s // 10).astype(int)], 1e-9), 6.0)
            u[c['wet']] = mag * ctx[idx]; v[c['wet']] = mag * cty[idx]
        c['tu'], c['tv'] = u.copy(), v.copy()   # directions for the inflow profile
        if not args.seed_velocity:
            u[:] = 0.0; v[:] = 0.0
        c['u'], c['v'] = u, v

    # exterior faces
    faces = dict(west=(np.s_[:, 0], (-1, 0), (1, 0)), east=(np.s_[:, -1], (1, 0), (-1, 0)),
                 south=(np.s_[0, :], (0, -1), (0, 1)), north=(np.s_[-1, :], (0, 1), (0, -1)))
    tile_set = set(tiles)
    boundary, upstream = {}, []
    for (i, j) in tiles:
        c = cells[(i, j)]
        for edge, (sl, (di, dj), inward) in faces.items():
            if (i + di, j + dj) in tile_set:
                continue
            ew = c['wet'][sl] & (c['h'][sl] > 0.05)
            if not ew.any():
                continue
            e_face = ax + (i + (1 if edge == 'east' else 0)) * TM if edge in ('west', 'east') else None
            n_face = ay + (j + (1 if edge == 'north' else 0)) * TM if edge in ('south', 'north') else None
            if edge == 'north' and abs(n_face - args.inflow_north_m) < 1e-6:
                t0 = np.array([c['tu'][sl][ew].sum(), c['tv'][sl][ew].sum()]); t0 /= max(np.linalg.norm(t0), 1e-9)
                proj = inward[0] * t0[0] + inward[1] * t0[1]
                assert proj > 0.3, f'inflow face {(i, j)} does not enter ({proj:.2f})'
                upstream.append(dict(k=(i, j), edge=edge, h=c['h'][sl], bed=c['bed'][sl] - args.datum_m, t=t0, w=c['h'][sl] ** (5 / 3) * proj))
            elif edge == 'west' and abs(e_face - args.outflow_east_m) < 1e-6:
                boundary[((i, j), edge)] = dict(kind='outflow', stage=float(np.median(c['surface'][sl][ew])) - args.datum_m, role='downstream')
            else:
                raise AssertionError(f'reach water meets an uncut exterior face: tile {(i, j)} {edge}')
    wsum = sum(u_['w'].sum() for u_ in upstream)
    assert upstream and wsum > 0 and any(v['role'] == 'downstream' for v in boundary.values())
    imposed = 0.0
    for it in upstream:
        mag = np.where(it['h'] > 1e-6, Q * it['h'] ** (2 / 3) / (wsum * D), 0.0)
        prof = np.column_stack((it['bed'], it['h'], mag * it['t'][0], mag * it['t'][1]))
        imposed += float(Q * it['w'].sum() / wsum)
        boundary[(it['k'], it['edge'])] = dict(kind='discharge_profile', ghost_cells=np.tile(prof, (2, 1)).tolist(), role='upstream')
    assert abs(imposed - Q) < 1e-6
    # the face discharge the profile carries: sum(h * |u.n|) * D
    carried = sum(float((np.where(it['h'] > 1e-6, Q * it['h'] ** (2 / 3) / (wsum * D), 0) * it['h']).sum() * D *
                        (np.array([0, -1]) @ it['t'])) for it in upstream)

    seed = None
    if args.seed_cook:
        sk = args.seed_cook.resolve()
        smf = json.loads((sk / 'input_manifest.json').read_text())
        assert [list(t) for t in tiles] == smf['tile_indices'], 'warm start needs the same tiles'
        sroot = Path((sk / 'input_manifest_path.txt').read_text().strip()).parent
        sframe = sorted(q for q in sk.glob('frame_*') if (q / 'complete.json').exists())[-1]
        seed = dict(h=np.load(sframe / 'h.npy'), u=np.load(sframe / 'u.npy'), v=np.load(sframe / 'v.npy'), root=sroot, frame=sframe.name,
                    names=smf['packages'])
    out.mkdir(parents=True)
    template = json.loads(TEMPLATE.read_text())
    names = [f'tile_e{i:+04d}_n{j:+04d}' for (i, j) in tiles]
    manifest = dict(schema='raftsim.cartesian_flow_cook.v1', dt_seconds=args.dt, packages=names, boundary_probes=[],
                    evidence_manifest_sha256=sha(ev / 'manifest.json'), evidence_grid_sha256=sha(ev / 'evidence_grid.npz'),
                    target_discharge_m3s=Q, authored_combined_inlet_discharge_m3s=imposed, inflow_face_normal_discharge_m3s=carried,
                    vertical_datum_m=args.datum_m, world_origin_utm35s_m=origin.tolist(),
                    grid=dict(cell_m=D, tile_cells=T, lattice_offset_utm_m=[ax, ay], inflow_north_m=args.inflow_north_m,
                              outflow_east_m=args.outflow_east_m, reach_station_m=[s_in, s_out]),
                    tile_indices=[list(k) for k in tiles], reach_tiles=[list(k) for k in sorted(members)],
                    initial_state='evidence reference surface inside the evidence river; ' + ('conveyance velocity seed along the midline tangent'
                                  if args.seed_velocity else 'still water (cold start)') if not args.seed_cook else
                                  f'warm start: free surface and velocity of {args.seed_cook.name}/{seed["frame"]} over the revised bed',
                    measured_velocity=False, measured_bathymetry=False, settled_hydraulics=False, inputs=[])
    local = {k: n for n, k in enumerate(tiles)}
    for (i, j), name in zip(tiles, names):
        c = cells[(i, j)]
        pkg = out / name; pkg.mkdir()
        np.save(pkg / 'bed.npy', c['bed'] - args.datum_m)
        h, u, v = c['h'], c['u'], c['v']
        if seed:
            k_ = local[(i, j)]; rows_ = slice(k_ * T, (k_ + 1) * T)
            eta_old = np.load(seed['root'] / seed['names'][k_] / 'bed.npy') + seed['h'][rows_]
            wet_old = seed['h'][rows_] > 1e-6
            h = np.where(wet_old, np.maximum(eta_old - (c['bed'] - args.datum_m), 0.0), 0.0)
            u = np.where(h > 1e-6, seed['u'][rows_], 0.0); v = np.where(h > 1e-6, seed['v'][rows_], 0.0)
        np.savez_compressed(pkg / 'initial_state.npz', depth=h, eta=c['bed'] - args.datum_m + h, u=u, v=v, hu=h * u, hv=h * v, wet=h > 1e-6)
        (pkg / 'features.json').write_text('{"features":[]}\n'); (pkg / 'probes.json').write_text('{"probes":[]}\n')
        sc = copy.deepcopy(template)
        sc['metadata'] = dict(scenario_id=name, scenario_type='real_world', fixture_kind=None, river_id='zambezi_batoka_gorge',
                              flow_band=f'low_water_{Q:.0f}cms', generator='prepare_zambezi_cartesian_cook.py', generator_version='20260928-v1',
                              description='Zambezi upper gorge evidence reach; inferred bed; not accepted', confidence_score=.3,
                              coordinate_reference_system=f'Unrotated EPSG:32735 east/north metres relative to {origin.tolist()}; EGM2008 minus {args.datum_m} m',
                              provenance=dict(evidence_manifest_sha256=sha(ev / 'manifest.json'), submerged_bed_is_uncalibrated_inference=True,
                                              initial_velocity_is_inferred=True, target_discharge_m3s=Q))
        e0 = ax + i * TM - origin[0]; n0 = ay + j * TM - origin[1]
        sc['grid'] = dict(nx=T, ny=T, dx=D, dy=D, origin_x=e0 + D / 2, origin_y=n0 + D / 2)
        sc.update(fixed_dt=args.dt, duration=600., roughness=args.roughness, feature_count=0, probe_count=0)
        sc['boundaries'] = []
        for edge in ('west', 'east', 'south', 'north'):
            bd = dict(edge=edge, kind='bank')
            spec = boundary.get(((i, j), edge))
            if spec:
                bd.update({k_: v_ for k_, v_ in spec.items() if k_ != 'role'})
                manifest['boundary_probes'].append(dict(tile_index=local[(i, j)], edge=edge, role=spec['role']))
            sc['boundaries'].append(bd)
        (pkg / 'scenario.json').write_text(json.dumps(sc, indent=2) + '\n')
        manifest['inputs'].append(dict(name=name, files={n: sha(pkg / n) for n in ('scenario.json', 'bed.npy', 'initial_state.npz', 'features.json', 'probes.json')}))
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    np.savez_compressed(out / 'station_map.npz', station=np.stack([cells[k]['station'] for k in tiles]),
                        surface=np.stack([cells[k]['surface'] for k in tiles]), wet=np.stack([cells[k]['wet'] for k in tiles]),
                        tiles=np.array(tiles))
    print(json.dumps(dict(tiles=len(tiles), reach_tiles=len(members), inflow_faces=len(upstream),
                          outflow_faces=sum(v['role'] == 'downstream' for v in boundary.values()),
                          imposed_m3s=imposed, inflow_face_normal_m3s=carried, wet_cells=int(sum(c['wet'].sum() for c in cells.values())),
                          origin=origin.tolist()), indent=1))


if __name__ == '__main__':
    main()
