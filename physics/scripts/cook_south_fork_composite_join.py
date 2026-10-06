"""Cook an enlarged Cartesian window spanning rapid, seam and full-river bed.

This validates integration geometry, not the uncalibrated full-river bed prior.
Never replaces the installed rapid flow or creates a menu scenario.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'physics/src'))
from south_fork_composite_terrain import CompositeTerrainSampler


def main():
    import rasterio
    from scipy.ndimage import map_coordinates
    from raftsim.scenario2_5d import (GridSpec2_5D, Scenario2_5D, ScenarioMetadata2_5D,
        InitialWaterState2_5D, BoundaryCondition2_5D, Probe2_5D)
    from raftsim.dual_solver import run_cpp_solver_scenario, CppSolverRunConfig
    parser = argparse.ArgumentParser()
    parser.add_argument('--steps', type=int, default=6000)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    work = args.output.resolve()
    if not work.is_relative_to(ROOT/'tmp') or work.exists() or args.steps <= 0:
        raise ValueError('Require a fresh in-project scratch run and positive steps')
    base = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09'
    geometry_dir = base/'full_reach/composite_terrain'
    sampler = CompositeTerrainSampler(geometry_dir)
    origin = np.asarray(sampler.manifest['rapid_origin_utm_m'])
    datum = sampler.manifest['rapid_datum_navd88_m']
    direction = np.array([-.93, .36756]); direction /= np.linalg.norm(direction)
    left = np.array([-direction[1], direction[0]])
    # Captured-mask preflight: +/-250 m crosses an upstream river bend at a
    # side wall. +/-230 m, +/-160 m has captured dry side boundaries and real
    # inlet/outlet, and still spans both joins beyond the original rapid crop.
    grid = GridSpec2_5D(nx=461, ny=321, dx=1., dy=1., origin_x=-230., origin_y=-160.)
    x, y = grid.meshgrid()
    east, north = origin[0]+direction[0]*x+left[0]*y, origin[1]+direction[1]*x+left[1]*y
    bed, owners = sampler.sample(east, north, with_owner=True)
    bed -= datum
    def sample_raster(path, order):
        with rasterio.open(path) as ds:
            c, r = (~ds.transform)*(east, north)
            value = map_coordinates(ds.read(1).astype(float), [r-.5, c-.5], order=order,
                                   mode='constant', cval=np.nan)
        if not np.isfinite(value).all():
            raise ValueError('Expanded domain leaves captured source: '+str(path))
        return value
    surface = sample_raster(base/'full_reach/captured_surface_navd88_m.tif', 1)-datum
    wet = sample_raster(base/'full_reach/unknown_submerged_bed_mask.tif', 0) == 1
    if wet[0].any() or wet[-1].any():
        raise ValueError('River crosses side boundary; do not wall off a real channel')
    if not wet[:, 0].any() or not wet[:, -1].any():
        raise ValueError('No captured inlet/outlet')
    depth = np.where(wet, np.maximum(surface-bed, 0), 0)
    area = depth.sum(axis=0)
    if area.min() < .1:
        raise ValueError('Initial wet cross-section disconnected')
    discharge = 45.3069545472
    conveyance = np.sum(depth**(5./3.), axis=0)
    u = np.where(depth > 1e-6, discharge*depth**(2./3.)/conveyance[None, :], 0)
    state = InitialWaterState2_5D.from_depth_velocity(bed, depth, u, np.zeros_like(u))
    inlet, outlet = float(np.median(surface[wet[:, 0], 0])), float(np.median(surface[wet[:, -1], -1]))
    geometry_sha = hashlib.sha256((geometry_dir/'manifest.json').read_bytes()).hexdigest()
    scenario = Scenario2_5D(metadata=ScenarioMetadata2_5D(
        scenario_id='south_fork_composite_join_1m', scenario_type='real_world',
        description='Captured rapid plus exact inferred join and uncalibrated full-river bed; not accepted',
        coordinate_reference_system='Rigid Cartesian metres in EPSG:32610, no curved-grid deformation',
        confidence_score=.3, provenance=dict(geometry_sha256=geometry_sha,
            bed_sampling='composite_render_triangles', bathymetry_authority='explicit uncalibrated inference',
            target_discharge_m3s=discharge, production_promoted=False)),
        grid=grid, fixed_dt=.1, duration=args.steps*.1, bed=bed, initial_state=state,
        boundaries=(BoundaryCondition2_5D('west', 'inflow', stage=inlet, velocity=(discharge/area[0], 0),
            metadata={'target_discharge_m3s': discharge}), BoundaryCondition2_5D('east', 'outflow', stage=outlet),
            BoundaryCondition2_5D('north', 'bank'), BoundaryCondition2_5D('south', 'bank')),
        probes=(Probe2_5D('inlet', (-220, 0)), Probe2_5D('rapid', (8, 0)), Probe2_5D('outlet', (220, 0))), roughness=.035)
    assert scenario.validate().passed, scenario.validate().summary_lines()
    binary = ROOT/'tmp/troublemaker-row-solver-v2-20260912/raftsim_water_solver.exe'
    work.mkdir(parents=True)
    registration = dict(origin_utm_m=origin.tolist(), downstream_unit=direction.tolist(), left_unit=left.tolist(),
        vertical_origin_navd88_m=datum, target_discharge_m3s=discharge, cell_m=1.,
        inlet_stage_navd88_m=inlet+datum, outlet_stage_navd88_m=outlet+datum,
        geometry_sha256=geometry_sha, geometry_manifest=(geometry_dir/'manifest.json').relative_to(ROOT).as_posix(),
        bed_sampling='composite_render_triangles', boundary_mode='mixed_characteristic_discharge',
        solver_binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(), cfl=.2, fixed_dt_seconds=.1,
        owner_cell_counts={str(k): int((owners == k).sum()) for k in (1, 2, 3)},
        production_promoted=False, normal_map_integrated=False)
    (work/'registration.json').write_text(json.dumps(registration, indent=2)+'\n')
    print(json.dumps(registration, indent=2), flush=True)
    result = run_cpp_solver_scenario(scenario, output_dir=work, config=CppSolverRunConfig(
        executable=binary, steps=args.steps, frame_interval=max(1, args.steps//12), solver_mode='finite_volume',
        boundary_mode='scenario', flux_scheme='hll', cfl=.2, feature_strength_scale=0,
        roughness_scale=1, bed_slope_source_scale=1, preserve_initial_mass=False,
        disable_fixture_calibrations=True, experimental_west_discharge_m3s=discharge,
        experimental_west_supercritical_stage=True))
    (work/'run_result.json').write_text(json.dumps(result.to_json_dict(ROOT), indent=2)+'\n')
    print(json.dumps(result.to_json_dict(ROOT)), flush=True)


if __name__ == '__main__':
    main()
