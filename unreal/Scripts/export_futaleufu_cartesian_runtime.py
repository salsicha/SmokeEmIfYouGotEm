"""Export full-route native water into the game's existing Cartesian format.

This is a source-exact runtime candidate, not settling or gameplay acceptance.
Hydraulic east/north coordinates stay separate from downstream progress.
Outside solved tiles, dry context is inferred from the reviewed channel/terrain
construction, not falsely presented as measured bathymetry or observed water.
"""
import argparse
import json
import os
from pathlib import Path
import shutil

import numpy as np

from build_futaleufu_continuous_water_domain import ROOT, PREFIX, sha, FutaleufuBed, LandscapeTriangles
from prepare_futaleufu_hydraulic_ports import FACES
from resume_futaleufu_native_checkpoint import require_terminal_audit, exact_state


def intersections(origin, shape, tile_origins, size):
    offsets = np.asarray(tile_origins)-np.asarray(origin)
    if offsets.ndim != 2 or offsets.shape[1] != 2 or not np.isfinite(offsets).all():
        raise ValueError('Finite aligned tile origins required')
    if np.max(np.abs(offsets-np.rint(offsets))) > 1e-7:
        raise ValueError('Source packet and native cell centres do not align')
    offsets = np.rint(offsets).astype(int)
    ny, nx = shape
    result = []
    for i in np.flatnonzero((offsets[:, 0] < nx) & (offsets[:, 1] < ny)
                           & (offsets[:, 0]+size > 0) & (offsets[:, 1]+size > 0)):
        x, y = offsets[i]
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(nx, x+size), min(ny, y+size)
        result.append((int(i), np.s_[y0:y1, x0:x1], np.s_[i*size+y0-y:i*size+y1-y, x0-x:x1-x]))
    return result


def source_centres(reference, origin):
    """Cover both banks of every original arm, not just a single centreline."""
    bins, observations = set(), []
    for name, line in zip(reference.arrays, reference.lines):
        a = reference.arrays[name]
        for station in np.unique(np.r_[0., np.arange(20., line.length, 20.), line.length]):
            centre = np.asarray(line.interpolate(station).coords)[0]
            tangent = (np.asarray(line.interpolate(min(line.length, station+1)).coords)[0]
                       -np.asarray(line.interpolate(max(0., station-1)).coords)[0])
            normal = np.array([-tangent[1], tangent[0]])/np.linalg.norm(tangent)
            left, right = [np.interp(station, a['station_m'], a[k]) for k in ('left_m', 'right_m')]
            points = centre+np.linspace(left, right, max(2, int(np.ceil((right-left)/10))+1))[:, None]*normal
            local = points-origin
            bins.update(map(tuple, np.floor(local/160.).astype(int)))
            observations.extend(local.tolist())
    centres = np.array(sorted(bins), float)*160.+80.5
    return centres, np.asarray(observations)


def export(audit_path, output):
    audit_path, output = Path(audit_path).resolve(), Path(output).resolve()
    output.relative_to(ROOT)
    if output.exists(): raise ValueError('Fresh runtime candidate required')
    audit = json.loads(audit_path.read_text())
    last = require_terminal_audit(audit)
    native = ROOT/audit['native_run']/'native'
    source = Path((native/'input_manifest_path.txt').read_text().strip()).resolve()
    if sha(source) != sha(native/'input_manifest.json'): raise ValueError('Native input manifest changed')
    m = json.loads(source.read_text())
    size = m['grid']['tile_cells']
    if m['grid']['cell_m'] != 1. or m['vertical_datum_m'] != 150.:
        raise ValueError('Reviewed one-metre Futaleufu native frame required')
    frame = native/('frame_%06d'%last['step'])
    pins = {ROOT/p: h for p, h in audit['sources_sha256'].items()}
    for p in (audit_path, Path(__file__).resolve()): pins[p] = sha(p)

    def verify():
        for p, h in pins.items():
            if sha(p) != h: raise ValueError('Runtime candidate source changed: '+str(p))

    verify()
    state = {k: np.load(frame/(k+'.npy'), mmap_mode='r', allow_pickle=False) for k in ('h', 'u', 'v')}
    exact_state(*[state[k] for k in ('h', 'u', 'v')], (len(m['packages'])*size, size))
    keys = [tuple(k) for k in m['tile_indices']]
    tile_origins = np.array(keys, float)*size+.5
    opened = {(r['tile_index'], r['edge']) for r in m['boundary_probes']}
    keyset = set(keys)
    for i, key in enumerate(keys):
        for edge, (sl, delta, _, _) in FACES.items():
            if (key[0]+delta[0], key[1]+delta[1]) in keyset or (i, edge) in opened: continue
            if np.any(state['h'][i*size:(i+1)*size][sl] != 0.):
                raise ValueError('Native loader requires exactly dry artificial exterior; do not clip small depths')
    terrain = LandscapeTriangles(ROOT/'tmp/futaleufu-hydraulic-buffer-terrain-v1')
    ref = FutaleufuBed(ROOT/'tmp/futaleufu-continuous-source-window-v2',
        PREFIX/'hydrology/channel_profile_2026_10_v2', PREFIX/'hydrography/confluence_network_2026_10_v1/network.json', depth_m=1.8)
    context = FutaleufuBed(ROOT/'tmp/futaleufu-continuous-source-window-v2', ROOT/'tmp/futaleufu-hydraulic-buffer-profile-v1',
        ROOT/'tmp/futaleufu-hydraulic-buffer-network-v1/network.json', depth_m=1.8)
    origin = np.asarray(m['horizontal_origin_utm18s_m'])
    centres, probes = source_centres(ref, origin)
    if shutil.disk_usage(ROOT).free < 40*1024**3+len(centres)*321*321*10+512*1024**2:
        raise ValueError('Runtime candidate must preserve the 40 GiB disk reserve')
    output.mkdir(parents=True)
    atlas_dir = output/'atlas'; atlas_dir.mkdir()
    bed = np.empty_like(state['h'])
    for i, name in enumerate(m['packages']):
        bed[i*size:(i+1)*size] = np.load(source.parent/name/'bed.npy', allow_pickle=False)
    np.save(atlas_dir/'bed.npy', bed)

    def save(path, value): path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')

    def meta(path, folder, array):
        return dict(file=Path(os.path.relpath(path, folder)).as_posix(), sha256=sha(path),
                    shape=list(array.shape), dtype=array.dtype.str)

    arrays = dict(bed=meta(atlas_dir/'bed.npy', atlas_dir, bed))
    arrays.update({k: meta(frame/(k+'.npy'), atlas_dir, a) for k, a in state.items()})
    atlas = dict(schema='raftsim.cartesian_state_atlas.v1', tile_shape=[size, size], grid_spacing_m=1.,
        source_elevation_datum_m=150., dry_tolerance=1e-6, tiles=[dict(origin_m=p.tolist()) for p in tile_origins],
        arrays=arrays, physical_exterior_faces=m['boundary_probes'], source_time_seconds=last['time_seconds'],
        input_manifest_sha256=sha(source), source_audit_sha256=sha(audit_path),
        settled_hydraulics=False, normal_map_integrated=False)
    save(atlas_dir/'manifest.json', atlas)
    streaming = dict(schema='raftsim.cartesian_water_streaming.v1', grid_spacing_m=1., advance_m=80.,
        roughness_manning=.045, source_context_cells=3, minimum_raft_interior_margin_m=8.,
        live_window_extent_m=[224., 224.], windows=[], settled_hydraulics=False, normal_map_integrated=False)
    qualified_centres, cell_count = [], 0
    for n, centre in enumerate(centres):
        low = centre-160.
        x, y = np.meshgrid(low[0]+np.arange(321), low[1]+np.arange(321))
        xy = np.stack((x, y), axis=-1)+origin
        absolute_bed = terrain.sample(xy)
        packet_bed = absolute_bed-150.
        channel = context.sample(xy.reshape(-1, 2))
        # This runtime field name is legacy. Its source is explicitly inferred
        # channel eligibility, not an optical classification or a measurement.
        mask = (channel['bed_owned'] & (channel['reference_m'] > absolute_bed.ravel())).reshape((321, 321)).astype('uint8')
        modeled = np.zeros((321, 321), bool)
        for i, dest, src in intersections(low, (321, 321), tile_origins, size):
            if modeled[dest].any() or not np.array_equal(packet_bed[dest], bed[src]):
                raise ValueError('Packet and native encoded-terrain bed differ')
            modeled[dest] = True
            cell_count += int(bed[src].size)
        if np.any(mask & ~modeled):
            raise ValueError('Packet includes unsolved inferred wet context; missing source cannot become invented dry water')
        # The full packet must also avoid unmodeled physical inlet/outlet ghosts.
        for p in m['boundary_probes']:
            i = p['tile_index']; sl, delta, _, _ = FACES[p['edge']]
            rows, cols = np.indices((size, size))
            points = tile_origins[i]+np.c_[cols[sl], rows[sl]]+delta
            wet = state['h'][i*size:(i+1)*size][sl] != 0
            if np.any(wet & ((points >= low) & (points <= low+320)).all(axis=1)):
                raise ValueError('Runtime packet touches a physical boundary; keep numerical buffer outside gameplay')
        name = 'source_%04d'%n; folder = output/name; folder.mkdir()
        np.save(folder/'bed.npy', packet_bed); np.save(folder/'captured_water_mask.npy', mask)
        fields = dict(schema='raftsim.cooked_flow_fields.v1', coordinate_system='cartesian_east_north_m',
            source_elevation_datum_m=150., grid=dict(nx=321, ny=321, dx_m=1., dy_m=1., origin_x_m=float(low[0]), origin_y_m=float(low[1])),
            solver=dict(runtime_cartesian_coupled_config=True, solver_mode='finite_volume', flux_scheme='hll', spatial_order=2,
                fixed_dt_s=.01, cfl=.2, dry_tolerance=1e-6, roughness_manning=.045, roughness_scale=1.,
                bed_slope_source_scale=1., feature_strength_scale=0., preserve_initial_mass=False),
            bands=[dict(band_id='median_runnable', arrays={k: meta(folder/(k+'.npy'), folder, a)
                for k, a in (('bed', packet_bed), ('captured_water_mask', mask))},
                shared_cartesian_state=dict(manifest='../atlas/manifest.json', sha256=sha(atlas_dir/'manifest.json')))],
            mask_basis='Inferred source-bound channel eligibility and encoded terrain; not measured or classified imagery',
            measured_bathymetry=False, settled_hydraulics=False, normal_map_integrated=False)
        save(folder/'manifest.json', fields)
        bounds = np.r_[centre-45., centre+45.].tolist()
        streaming['windows'].append(dict(window_id=name, cooked_fields_manifest=(folder/'manifest.json').relative_to(ROOT).as_posix(),
            hydraulic_bounds_m=np.r_[low, low+320.].tolist(), valid_live_center_bounds_m=[bounds]))
        qualified_centres.append(centre)
        if (n+1)%20 == 0: print('Verified full-river runtime source %d/%d'%(n+1, len(centres)), flush=True)
    # A probe needs a selected centre with >=8 m raft margin in the 224 m crop.
    covered = np.zeros(len(probes), bool)
    for c in qualified_centres: covered |= (np.abs(probes-c) <= 45.+112.-8.).all(axis=1)
    if not covered.all(): raise ValueError('Original route/bank probes lack continuous selectable windows')
    save(output/'streaming_manifest.json', streaming)
    bounds = np.r_[tile_origins.min(axis=0), (tile_origins+size-1).max(axis=0)].tolist()
    save(output/'coordinate_map.json', dict(schema='raftsim.cartesian_water_coordinate_map.v1', river_id='futaleufu_river_chile',
        hydraulic_bounds_m=bounds, horizontal_crs='EPSG:32718', horizontal_origin_m=origin.tolist(), vertical_datum_m=150.,
        vertical_reference='EGM2008', world_y_sign=-1, scope='Hydraulic east/north only; use captured continuous chart for progress'))
    terrain.verify_unchanged(); verify()
    report = dict(schema='raftsim.futaleufu_cartesian_runtime_candidate.v1', source_audit_sha256=sha(audit_path),
        source_time_seconds=last['time_seconds'], source_packet_count=len(centres), atlas_tile_count=len(keys),
        exact_bed_intersection_cells=cell_count, original_route_and_bank_probes=len(probes), covered_probes=int(covered.sum()),
        atlas_manifest_sha256=sha(atlas_dir/'manifest.json'), streaming_manifest_sha256=sha(output/'streaming_manifest.json'),
        exactly_dry_artificial_exterior=True, physical_ports_outside_packets=True,
        progress_chart=(PREFIX/'hydrography/continuous_route_2026_10_v2/coordinate_map.json').relative_to(ROOT).as_posix(),
        native_engine_loaded=False, settled_hydraulics=False, normal_map_integrated=False, packaged_fps_verified=False)
    save(output/'export_audit.json', report)
    print(json.dumps(report), flush=True)
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--audit', type=Path, required=True); p.add_argument('--out', type=Path, required=True)
    a = p.parse_args(); export(a.audit, a.out)
