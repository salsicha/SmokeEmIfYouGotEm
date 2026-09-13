"""Stage the settled join fields in the full-river world for runtime integration.

Requires source-exact geometry, all saved-frame sanity, settling and numerical
conservation. These gates do not certify inferred bathymetry or visual fidelity.
"""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'physics/src'))
from raftsim.scenario2_5d import read_scenario2_5d_package
from south_fork_composite_terrain import CompositeTerrainSampler
from south_fork_survey_sanity import require_sane_frames
from audit_troublemaker_hydraulic_spinup import validated_frame_state
from export_troublemaker_review_fields import validate_solver_manifest

BASE = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach'
WORK = ROOT/'tmp/south-fork-composite-join-cook-20260912'
OUT = BASE/'rapid_join_flow'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert not OUT.exists(), 'Use a new delivery revision; do not overwrite runtime fields'
    registration = json.loads((WORK/'registration.json').read_text())
    flow = json.loads((WORK/'flow_review.json').read_text())
    conservation = json.loads((WORK/'conservation_review.json').read_text())
    geometry_path = BASE/'composite_terrain/manifest.json'
    assert sha(geometry_path) == registration['geometry_sha256'] == flow['geometry_sha256'] == conservation['source_geometry_sha256']
    assert flow['mean_flow_screen_passed'] and all(flow['checks'].values())
    assert conservation['passed'] and all(conservation['checks'].values())
    assert conservation['instantaneous_outflow_within_2_percent_of_target']
    run = json.loads((WORK/'run_result.json').read_text())
    assert run['returncode'] == 0
    assert sha(Path(run['command'][0])) == registration['solver_binary_sha256']
    folder = ROOT/run['output_dir']
    raw_manifest = json.loads((folder/'manifest.json').read_text())
    sanity = require_sane_frames(folder, raw_manifest)
    frame = folder/raw_manifest['frames'][-1]
    assert sha(frame) == conservation['source_frame_sha256']
    solver = validate_solver_manifest(frame, folder/'manifest.json')
    scenario = read_scenario2_5d_package(next((WORK/'scenario').glob('*/scenario.json')))
    state = validated_frame_state(scenario, np.genfromtxt(frame, delimiter=',', names=True))
    terrain = CompositeTerrainSampler(BASE/'composite_terrain')
    x, y = scenario.grid.meshgrid()
    direction, left, origin = (np.array(registration[k]) for k in ['downstream_unit', 'left_unit', 'origin_utm_m'])
    sample_bed = terrain.sample(origin[0]+direction[0]*x+left[0]*y, origin[1]+direction[1]*x+left[1]*y)
    assert np.array_equal(sample_bed-registration['vertical_origin_navd88_m'], scenario.bed)
    river_map_path = BASE/'playable_route/coordinate_map.json'
    river_map = json.loads(river_map_path.read_text())
    offset = origin-np.array(river_map['origin_utm_m'])
    first = int(np.floor(x.min()/10))*10-10
    last = int(np.ceil(x.max()/10))*10+10
    coordinate = dict(schema='raftsim.curved_river_coordinate_map.v1',
        points=[[float(s), *(offset+direction*s).tolist(), *left.tolist()] for s in range(first, last+1, 10)],
        origin_utm_m=river_map['origin_utm_m'], world_y_sign=-1,
        vertical_datum_m=registration['vertical_origin_navd88_m'],
        interpretation='Rigid hydraulic coordinates in full-river world; not full-river progress chainage',
        full_river_progress_coordinate_map=river_map_path.relative_to(ROOT).as_posix(),
        full_river_progress_coordinate_map_sha256=sha(river_map_path))
    (OUT/'median_runnable').mkdir(parents=True)
    records = {}
    for name, values in dict(h=state.depth, u=state.u, v=state.v, bed=scenario.bed, wet_mask=state.wet).items():
        packed = np.ascontiguousarray(values, dtype=np.uint8 if name == 'wet_mask' else np.float32)
        if name != 'wet_mask':
            assert np.max(abs(packed.astype(np.float64)-values)) < 1e-5
        path = OUT/'median_runnable'/(name+'.npy')
        np.save(path, packed)
        records[name] = dict(file=path.relative_to(OUT).as_posix(), dtype=str(packed.dtype), shape=list(packed.shape), sha256=sha(path))
    grid = scenario.grid
    manifest = dict(schema='raftsim.cooked_flow_fields.v1', river_id='south_fork_american_chili_bar',
        rapid_name='Troublemaker full-river terrain join', source_elevation_datum_m=registration['vertical_origin_navd88_m'],
        all_bands_passed=False, production_promoted=False,
        grid=dict(nx=grid.nx, ny=grid.ny, dx_m=grid.dx, dy_m=grid.dy, origin_x_m=grid.origin_x, origin_y_m=grid.origin_y,
            layout='row_major_c_order', crs='Rigid Cartesian metres from EPSG:32610'),
        bands=[dict(band_id='median_runnable', arrays=records, runtime_boundaries=[b.to_json_dict() for b in scenario.boundaries],
            validation=dict(passed=False, reason='Matched integration candidate; inferred bed and visual/runtime handoff not accepted'))],
        solver={key: solver[key] for key in ['solver_mode', 'flux_scheme', 'cfl', 'dry_tolerance', 'roughness_scale',
            'bed_slope_source_scale', 'feature_strength_scale', 'spatial_order', 'preserve_initial_mass', 'disable_fixture_calibrations']},
        review=dict(source_geometry_sha256=registration['geometry_sha256'], source_geometry_manifest=geometry_path.relative_to(ROOT).as_posix(),
            source_solver_binary_sha256=registration['solver_binary_sha256'], source_bed_sampling='composite_render_triangles',
            source_run=WORK.relative_to(ROOT).as_posix(), frame_sha256=sha(frame), saved_frame_sanity=sanity,
            no_surface_limiter_applied=True, runtime_replays_offline_boundary=True, photorealism_accepted=False,
            mean_flow_screen_sha256=sha(WORK/'flow_review.json'), conservation_review_sha256=sha(WORK/'conservation_review.json')))
    manifest['solver'].update(fixed_dt_s=scenario.fixed_dt, roughness_manning=scenario.roughness,
        runtime_replay_offline_config=True, experimental_west_discharge_m3s=registration['target_discharge_m3s'],
        experimental_west_supercritical_stage=True)
    (OUT/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    (OUT/'coordinate_map.json').write_text(json.dumps(coordinate, indent=2)+'\n')
    delivery = dict(source_geometry_sha256=registration['geometry_sha256'], source_bed_sample_bit_identical=True,
        source_frame_sha256=sha(frame), normal_map_integrated=False, full_reconstruction_accepted=False,
        required_next_step='Native full-river terrain placement, progress-axis separation and hydraulic-region handoff',
        files={p.relative_to(OUT).as_posix(): sha(p) for p in sorted(OUT.rglob('*')) if p.is_file()})
    (OUT/'delivery.json').write_text(json.dumps(delivery, indent=2)+'\n')
    print(json.dumps(delivery, indent=2))


if __name__ == '__main__':
    main()
