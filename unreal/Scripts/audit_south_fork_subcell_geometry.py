"""Compare exact registered ground and local storage with a normal-game capture.

Read-only evidence, not a new runtime geometry/solver or acceptance report.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
from audit_submitted_carrier_shape import read_table, SOURCE_FIELDS_V2, raw_stage

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'physics/scripts'))
from south_fork_registered_mesh import RegisteredMeshSampler
from triangle_cell_storage import cell_triangles, TriangleCellStorage


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def quantiles(values):
    return np.quantile(values, [0, .5, .95, 1]).tolist()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('ground_audit', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError(args.report)
    base = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach'
    geometry_path = base/'composite_terrain/manifest.json'
    mesh_path = base/'composite_terrain/troublemaker_registered_source.npz'
    map_path = base/'hydraulic_regions_context/coordinate_map.json'
    source_path = Path(str(args.capture)+'.source.csv')
    meta, ground, geometry, coordinates = map(read, (args.capture, args.ground_audit, geometry_path, map_path))
    if meta['schema'] != 'raftsim.submitted_carrier_shape.v2':
        raise ValueError('Expected captured source lattice v2')
    if sha(args.capture) != ground['source_capture_sha256'] or sha(source_path) != ground['source_csv_sha256']:
        raise ValueError('Ground audit refers to a different capture')
    if sha(mesh_path) != geometry['registered_rapid_sha256']:
        raise ValueError('Registered geometry changed')
    # Verify actual saved normal-scene geometry still has the audited identity.
    for path, expected in ground['protected_sha256'].items():
        if sha(Path(path)) != expected:
            raise ValueError('Protected capture/map/mesh/profile changed: '+path)
    for package, expected in ground['protected_actor_packages'].items():
        path = ROOT/'unreal/Content'/(package.removeprefix('/Game/')+'.uasset')
        if sha(path) != expected:
            raise ValueError('Audited actor changed: '+package)
    if ground['configuration']['coordinate_map_path'] != map_path.relative_to(ROOT).as_posix():
        raise ValueError('Different normal coordinate mapping')
    with np.load(mesh_path, allow_pickle=False) as data:
        sampler = RegisteredMeshSampler(data)
    source = read_table(source_path, SOURCE_FIELDS_V2)
    nx, ny, sign = meta['source_nx'], meta['source_ny'], meta['world_y_sign']
    if sign != coordinates['world_y_sign'] or not np.array_equal(source[:, 0], np.arange(nx*ny)):
        raise ValueError('Different or malformed captured grid')
    # Also validates uniformity/order without silently rounding source cells.
    raw_stage(source[:, 1:3]*[1, sign], source, nx, ny, sign)
    offset = np.array(coordinates['world_origin_utm_m'])-geometry['rapid_origin_utm_m']
    z_offset = geometry['rapid_datum_navd88_m']-coordinates['vertical_datum_m']
    results = {}
    for kind in ('source', 'submitted'):
        rows = [row for row in ground['probes'] if row['query_kind'] == kind]
        if not rows or not all(row['hit'] for row in rows):
            raise ValueError('Missing collision query; do not report survivor-only evidence')
        world_xy = np.array([row['world_xy_cm'] for row in rows])*.01
        local_xy = world_xy*[1, sign]+offset
        exact = sampler.sample(local_xy[:, 0], local_xy[:, 1])+z_offset
        collision = np.array([row['ground_z_cm'] for row in rows])*.01
        bilinear = np.array([row['sampled_bed_cm'] for row in rows])*.01
        # Bed-only comparison: dry flags do not erase terrain from this query.
        bed_only = source.copy()
        bed_only[:, 4] -= bed_only[:, 5]
        bed_only[:, 3] = 1
        triangular, valid = raw_stage(world_xy, bed_only, nx, ny, sign)
        if not valid.all():
            raise ValueError('Collision point outside captured bed lattice')
        results[kind] = dict(count=len(rows),
            exact_source_vs_collision_absolute_cm=quantiles(abs(exact-collision)*100),
            bilinear_vs_collision_absolute_cm=quantiles(abs(bilinear-collision)*100),
            coarse_triangular_vs_collision_absolute_cm=quantiles(abs(triangular-collision)*100))

    # Each exact source-grid coordinate is a solver cell center, not a corner.
    # Integrate its full footprint, preserving the original registered topology.
    dx, dy = source[1, 1]-source[0, 1], source[nx, 2]-source[0, 2]
    cells = []
    for row in ground['probes']:
        if row['query_kind'] != 'source':
            continue
        index = row['vertex_id']
        field_xy = source[index, 1:3]
        if not np.allclose(field_xy*[100, sign*100], row['world_xy_cm'], atol=1e-7, rtol=0):
            raise ValueError('Ground probe/source ID differs')
        storage = TriangleCellStorage(cell_triangles(sampler, field_xy+offset, [dx, dy]))
        # Source elevations are world-datum-relative in this game capture.
        eta = source[index, 4]-z_offset
        volume = source[index, 5]*storage.area
        represented, area = storage.volume_and_wet_area(eta)
        conservative_eta = storage.stage_for_volume(volume)
        recovered, recovered_area = storage.volume_and_wet_area(conservative_eta)
        cells.append(dict(source_id=index, source_depth_m=float(source[index, 5]),
            source_stage_m=float(eta), stored_volume_m3=float(volume),
            volume_at_source_stage_m3=represented, wet_area_at_source_stage_m2=area,
            local_conservative_stage_m=conservative_eta, recovered_volume_m3=recovered,
            recovered_wet_area_m2=recovered_area, footprint_area_m2=storage.area))
    wet = [row for row in cells if row['stored_volume_m3'] > 0]
    volume_error = np.array([row['volume_at_source_stage_m3']-row['stored_volume_m3'] for row in cells])
    volume_residual = np.array([row['recovered_volume_m3']-row['stored_volume_m3'] for row in cells])
    shifted = np.array([row['local_conservative_stage_m']-row['source_stage_m'] for row in wet])
    paths = [args.capture, source_path, args.ground_audit, geometry_path, map_path, mesh_path,
             Path(__file__), ROOT/'physics/scripts/triangle_cell_storage.py', ROOT/'physics/scripts/south_fork_registered_mesh.py']
    result = dict(schema='raftsim.south_fork.subcell_geometry.v1', accepted=False,
        captured_world_seconds=meta['world_seconds'], radius_m=ground['radius_m'],
        quantile_probabilities=[0, .5, .95, 1], quantile_method='numpy linear', point_comparison=results,
        storage=dict(cells=len(cells), positive_volume_cells=len(wet),
            source_total_volume_m3=sum(row['stored_volume_m3'] for row in cells),
            exact_geometry_volume_at_source_stage_m3=sum(row['volume_at_source_stage_m3'] for row in cells),
            signed_cell_volume_change_m3=quantiles(volume_error),
            maximum_absolute_cell_volume_change_m3=float(abs(volume_error).max()),
            sum_absolute_cell_volume_changes_m3=float(abs(volume_error).sum()),
            maximum_local_inversion_residual_m3=float(abs(volume_residual).max()),
            positive_volume_stage_shift_m=quantiles(shifted),
            maximum_absolute_positive_volume_stage_shift_m=float(abs(shifted).max())),
        cells=cells, input_sha256={str(path.resolve()): sha(path) for path in paths},
        scope='Exact registered source/collision comparison and hydrostatic per-cell storage only. Footprints use original triangles, with no bed resampling or invented coverage. Inversion preserves each captured cell volume but is not coupled to intercell flux, pressure, momentum, live clipping, or contact. Stage-at-cell-center held constant over each footprint is a diagnostic, not the actual rendered surface or accepted flow reconstruction. No source, map, solver state or render geometry is changed. Geometry provenance remains captured plus explicitly inferred submerged/flank geometry, not measured bathymetry. No settling, visual, physical or 30 FPS acceptance.')
    with args.report.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps({key: value for key, value in result.items() if key not in ('cells', 'input_sha256')}, indent=2))


if __name__ == '__main__':
    main()
