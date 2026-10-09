"""Bind screened common-grid terrain and water to one continuous native map."""
import argparse
import json
import re
from pathlib import Path

import numpy as np

from build_catalog_map_contract import ROOT, launch
from continuous_collision_probes import sha, write_chunks
from export_colorado_continuous_runtime import registered_queries, _registered_geometry
from build_colorado_continuous_assembly import rebase_chart
from register_colorado_takeout import register as register_takeout


def geographic_takeout(request, mapping, files):
    """Bind mapped geographic points; only the native adapter resolves stations."""
    request = request.resolve(); request.relative_to(ROOT)
    request_digest = sha(request)
    spec = json.loads(request.read_text())
    if spec.get('schema') != 'raftsim.colorado_takeout_request.v1':
        raise ValueError('Unsupported takeout request')
    paths = {key: (ROOT/spec[key]).resolve() for key in ('source_chart', 'evidence', 'osm')}
    for path in paths.values(): path.relative_to(ROOT)
    protected = {request: request_digest, **{path: sha(path) for path in paths.values()}}
    receipt = register_takeout(*(paths[key].read_bytes() for key in ('source_chart', 'evidence', 'osm')))
    origin = np.asarray(mapping['horizontal_origin_epsg6404_m'], dtype=float)
    if origin.shape != (2,) or not np.isfinite(origin).all() or mapping.get('world_y_sign') != -1:
        raise ValueError('Invalid takeout target world frame')
    world = {}
    for key in ('takeout', 'downstream_rapid'):
        xy = np.asarray(receipt[key]['projected_epsg6404_m'], dtype=float)
        if xy.shape != (2,) or not np.isfinite(xy).all():
            raise ValueError('Invalid geographic takeout point')
        world[key+'_world_xy_cm'] = ((xy-origin)*[100., -100.]).tolist()
    if any(sha(path) != digest for path, digest in protected.items()):
        raise ValueError('Takeout source changed during registration')
    for path, digest in protected.items(): files[path.relative_to(ROOT).as_posix()] = digest
    return dict(schema='raftsim.native_geographic_takeout.v1', **world,
        source_registration=receipt,
        acceptance='Native cross-section finish at mapped takeout; ramp geometry and docking not certified')


def rapid_profile_sources(assembly, mapping, files):
    """Bind existing production profiles to verified common-origin source charts.

    Native import performs the actual station/lateral/heading conversion using
    the runtime projection. No interpolated global-station offset is exported.
    """
    assembly = assembly.resolve(); assembly.relative_to(ROOT)
    manifest = json.loads(assembly.read_text())
    if manifest.get('schema') != 'raftsim.colorado_continuous_construction.v1':
        raise ValueError('Unsupported rapid source assembly')
    origin = mapping['horizontal_origin_epsg6404_m']; datum = mapping['vertical_datum_m']
    if (manifest['horizontal_crs'] != 'EPSG:6404' or
            manifest['horizontal_origin_epsg6404_m'] != origin or manifest['vertical_datum_m'] != datum):
        raise ValueError('Rapid assembly uses a different geographic frame')
    names = {'Badger Creek': 'L_Colorado_BadgerCreek', 'House Rock': 'L_Colorado_HouseRock',
             'Soap Creek': 'L_Colorado_SoapCreek', 'Georgie': 'L_Colorado_Georgie',
             'Unkar': 'L_Colorado_Unkar', 'Hance': 'L_Hance'}
    sources = []; seen = set()
    files[assembly.relative_to(ROOT).as_posix()] = sha(assembly)
    for reach in manifest['source_reaches']:
        if reach['name'] not in names: continue
        if reach['name'] in seen: raise ValueError('Duplicate rapid source')
        seen.add(reach['name'])
        original = (ROOT/reach['source_chart']).resolve(); original.relative_to(ROOT)
        if sha(original) != reach['chart_sha256']: raise ValueError('Changed original rapid chart')
        expected, _ = rebase_chart(json.loads(original.read_text()), np.asarray(origin), datum)
        rebased = (assembly.parent/reach['rebased_chart']).resolve(); rebased.relative_to(assembly.parent)
        if json.loads(rebased.read_text()) != expected:
            raise ValueError('Rebased rapid chart disagrees with original geography')
        for path in (original, rebased): files[path.relative_to(ROOT).as_posix()] = sha(path)
        sources.append(dict(map=names[reach['name']], coordinate_map=rebased.relative_to(ROOT).as_posix()))
    if not sources: raise ValueError('No supported production rapid profiles in assembly')
    return sources


def build(runtime, map_name, start, finish, lateral=0., dressing=None, nanite_terrain=False, profile_assembly=None, takeout_request=None, probe_directory=None):
    if type(nanite_terrain) is not bool:
        raise ValueError('Nanite terrain selection must be boolean')
    runtime = runtime.resolve(); runtime.relative_to(ROOT)
    manifest = json.loads((runtime/'manifest.json').read_text())
    # Generic continuous rivers: (map stem, section id, dressing schema).
    generic_rivers={'chilko_river_bc':('Chilko','chilko_continuous','raftsim.chilko_continuous_dressing.v1'),
                    'pacuare_river_costa_rica':('Pacuare','pacuare_continuous','raftsim.pacuare_continuous_dressing.v1')}
    river_id=manifest.get('river_id')
    chilko=manifest.get('schema')=='raftsim.continuous_runtime_candidate.v1' and river_id in generic_rivers
    stem,section,dressing_schema=generic_rivers[river_id] if chilko else ('Colorado','colorado_continuous','raftsim.colorado_continuous_dressing.v1')
    if not re.fullmatch(r'L_'+stem+r'_[A-Za-z0-9_]+', map_name):
        raise ValueError('Fresh continuous '+stem+' map name required')
    if (ROOT/'unreal/Content/RaftSim/Maps/Continuous'/f'{map_name}.umap').exists():
        raise ValueError('Refusing to overwrite a map')
    if ((not chilko and manifest['schema'] != 'raftsim.colorado_continuous_runtime_candidate.v1') or
            (runtime/'REJECTED.json').exists() or manifest['terrain_solver_bed_max_error_m'] > .01):
        raise ValueError('Unsupported or rejected continuous runtime')
    if chilko and profile_assembly is not None:
        raise ValueError(stem+' geographic rapid profiles require their own reviewed contracts')
    if chilko and takeout_request is not None:
        raise ValueError('Colorado takeout cannot be used for '+stem)
    if not chilko and manifest['full_river_coverage'] and takeout_request is None:
        raise ValueError('Full Colorado run requires source-identified Pearce Ferry takeout')
    files = {}
    for name, digest in manifest['files_sha256'].items():
        path = (runtime/name).resolve(); path.relative_to(runtime)
        if sha(path) != digest:
            raise ValueError('Changed continuous runtime dependency')
        files[path.relative_to(ROOT).as_posix()] = digest
    files[(runtime/'manifest.json').relative_to(ROOT).as_posix()] = sha(runtime/'manifest.json')
    fields = runtime/'cooked_flow_fields'
    flow = json.loads((fields/'manifest.json').read_text())
    terrain = json.loads((runtime/'terrain/manifest.json').read_text())
    mapping = json.loads((runtime/'coordinate_map.json').read_text())
    if chilko and (flow.get('river_id')!=river_id or terrain.get('river_id')!=river_id):
        raise ValueError(stem+' runtime dependencies disagree on river identity')
    band = flow['bands'][0]; g = flow['grid']
    grid = dict(nx=g['nx'], ny=g['ny'], dx=g['dx_m'], dy=g['dy_m'],
                origin_x=g['origin_x_m'], origin_y=g['origin_y_m'])
    station, _, _, _ = _registered_geometry(mapping, terrain, grid)
    if not station[0]+10 < start < finish < station[-1]-10:
        raise ValueError('Descent must stay inside actual cooked coverage, not merely the full coordinate map')
    # launch() indexes local columns. Supply the exact registered subset,
    # preserving global station and world coordinates rather than re-centring.
    points = np.asarray(mapping['points'])
    subset = dict(mapping, points=points[np.searchsorted(points[:, 0], station)].tolist())
    arrays = {k: np.load(fields/band['arrays'][k]['file'], mmap_mode='r') for k in ('bed', 'h', 'wet_mask')}
    initial = launch(subset, arrays['bed'], arrays['h'], arrays['wet_mask'], g, start, lateral)
    if probe_directory is None:
        if arrays['wet_mask'].size > 1000000:
            raise ValueError('Large continuous maps require --probe-directory for bounded collision validation')
        _, queries = registered_queries(mapping, terrain, grid)
        rows, cols = np.nonzero(arrays['wet_mask'])
        xy = queries[rows, cols] - np.asarray(mapping['horizontal_origin_m' if chilko else 'horizontal_origin_epsg6404_m'])
        probes = np.column_stack((xy[:, 0]*100, -xy[:, 1]*100,
                                 (arrays['bed'][rows, cols]-mapping['vertical_datum_m'])*100))
        probe_fields = dict(wet_bed_collision_probes_cm=probes.tolist())
    else:
        probes, dependencies = write_chunks(probe_directory, ROOT, mapping, terrain, grid,
                                             arrays['bed'], arrays['wet_mask'])
        files.update(dependencies)
        probe_fields = dict(wet_bed_collision_probe_chunks=probes)
    relative = runtime.relative_to(ROOT).as_posix()
    environment = None
    if dressing is not None:
        dressing = dressing.resolve(); dressing.relative_to(ROOT)
        environment = json.loads(dressing.read_text())
        if (environment.get('schema') != dressing_schema or
                environment['runtime_sha256'] != sha(runtime/'manifest.json') or
                environment['terrain_sha256'] != sha(runtime/'terrain/manifest.json')):
            raise ValueError('Dressing belongs to different runtime terrain/water')
        if chilko and environment.get('river_id')!=river_id:
            raise ValueError('Dressing river identity disagrees')
        files[dressing.relative_to(ROOT).as_posix()] = sha(dressing)
        for name, digest in environment['mesh_files_sha256'].items():
            path = (ROOT/name).resolve(); path.relative_to(ROOT)
            if sha(path) != digest: raise ValueError('Changed dressing asset')
            files[name] = digest
    result = dict(schema='raftsim.continuous_map_import.v1' if chilko else 'raftsim.colorado_continuous_map_import.v1',
        river_id=river_id if chilko else 'colorado_river_grand_canyon_rowing',
        map_package='/Game/RaftSim/Maps/Continuous/'+map_name,
        display_name=stem+' continuous construction descent', section_id=section,
        files_sha256=files, terrain_manifest=relative+'/terrain/manifest.json',
        coordinate_map=relative+'/coordinate_map.json', cooked_fields=relative+'/cooked_flow_fields',
        streaming=relative+'/moving_water_streaming.json', flow_band=band['band_id'],
        lateral_extent_m=(g['ny']-1)*g['dy_m'], launch=initial,
        finish_station_m=finish, rig='PaddleCrew' if chilko else 'ColoradoOarRig', **probe_fields,
        source_core_interval_m=manifest['source_core_interval_m'],
        full_river_coverage=manifest['full_river_coverage'], nanite_terrain=nanite_terrain,
        acceptance='pending native wet-bed collision, full-hull descent, rendered and packaged tests')
    if environment is not None: result['environment'] = dressing.relative_to(ROOT).as_posix()
    if profile_assembly is not None:
        result['rapid_profile_sources'] = rapid_profile_sources(profile_assembly, mapping, files)
    if takeout_request is not None:
        result['geographic_takeout'] = geographic_takeout(takeout_request, mapping, files)
        result['geographic_takeout']['coordinate_map_sha256'] = sha(runtime/'coordinate_map.json')
        result['geographic_takeout']['cooked_station_interval_m'] = [float(station[0]), float(station[-1])]
        result['finish_station_policy'] = 'Native geographic takeout overrides requested diagnostic finish station'
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--map-name', required=True)
    parser.add_argument('--start', type=float, required=True)
    parser.add_argument('--finish', type=float, required=True)
    parser.add_argument('--lateral', type=float, default=0.)
    parser.add_argument('--dressing', type=Path)
    parser.add_argument('--profile-assembly', type=Path,
                        help='Register authored Badger, Soap Creek, House Rock and Hance profiles through verified rebased charts')
    parser.add_argument('--nanite-terrain', action='store_true',
                        help='Build and verify a native Nanite terrain representation; does not change collision or water')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--probe-directory', type=Path,
                        help='Fresh directory for lossless per-terrain-chunk binary collision probes; required for large maps')
    parser.add_argument('--takeout-request', type=Path,
                        help='Source chart/evidence/OSM request; required for full Colorado coverage. Native projection determines the finish, not --finish.')
    args = parser.parse_args()
    if args.out.exists():
        raise SystemExit('Fresh contract required')
    result = build(args.runtime, args.map_name, args.start, args.finish, args.lateral, args.dressing, args.nanite_terrain, args.profile_assembly, args.takeout_request, args.probe_directory)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result['launch'], indent=2))
