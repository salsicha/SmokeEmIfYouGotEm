"""Unit checks for the diagnostic's units and wet-cell filtering."""
from pathlib import Path
import runpy
from types import SimpleNamespace

import numpy as np


def test_game_preview_is_explicit_non_shipping_and_troublemaker_median_only():
    root = Path(__file__).resolve().parents[2]
    source = (root / 'unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimRiverWaterStreamingActor.cpp').read_text()
    block = source.split('#if !UE_BUILD_SHIPPING', 1)[1].split('#endif', 1)[0]
    assert 'WindowId == TEXT("south_fork_troublemaker_live_window")' in block
    assert 'TEXT("RaftSimTroublemakerReviewFields=")' in block
    assert 'RiverConfig->FlowBand != FName(TEXT("median_runnable"))' in block
    assert 'FPaths::FileExists' in block
    assert 'return false;' in block
    assert 'not production promotion' in block


def test_prescribed_discharge_is_explicit_and_rejects_invalid_modes():
    from raftsim.dual_solver import CppSolverRunConfig
    defaults = CppSolverRunConfig(executable=Path('unused'))
    assert defaults.experimental_west_discharge_m3s is None
    valid = dict(executable=Path('unused'), solver_mode='finite_volume',
                 boundary_mode='scenario', disable_fixture_calibrations=True)
    assert CppSolverRunConfig(**valid, experimental_west_discharge_m3s=45.3).experimental_west_discharge_m3s == 45.3
    for value in [-1., float('nan'), float('inf')]:
        try:
            CppSolverRunConfig(**valid, experimental_west_discharge_m3s=value)
        except ValueError:
            pass
        else:
            raise AssertionError('invalid prescribed discharge accepted')
    for changed in [dict(solver_mode='reduced'), dict(boundary_mode='pyclaw'),
                    dict(disable_fixture_calibrations=False)]:
        try:
            CppSolverRunConfig(**{**valid, **changed}, experimental_west_discharge_m3s=45.3)
        except ValueError:
            pass
        else:
            raise AssertionError('unsupported prescribed-discharge mode accepted')


def test_warm_start_preserves_state_and_rejects_mismatched_frames():
    validate = runpy.run_path(str(Path(__file__).resolve().parents[1] /
        'scripts/audit_troublemaker_hydraulic_spinup.py'))['validated_frame_state']
    grid = SimpleNamespace(nx=3, ny=2, dx=.5, dy=.5, origin_x=10., origin_y=-1., shape=(2, 3))
    scenario = SimpleNamespace(grid=grid, bed=np.ones(grid.shape))
    names = ['row', 'col', 'x', 'y', 'h', 'eta', 'u', 'v', 'hu', 'hv', 'wet']
    data = np.zeros(6, dtype=[(name, float) for name in names])
    data['row'], data['col'] = np.indices(grid.shape).reshape(2, -1)
    data['x'] = grid.origin_x + data['col']*grid.dx
    data['y'] = grid.origin_y + data['row']*grid.dy
    data['h'], data['u'], data['v'], data['wet'] = 2., 3., -.5, 1
    data['eta'], data['hu'], data['hv'] = 3., 6., -1.
    original = data.copy()
    # CSV order does not have to be row-major.
    state = validate(scenario, data[::-1])
    assert np.array_equal(state.hu, np.full(grid.shape, 6.))
    assert np.array_equal(state.hv, np.full(grid.shape, -1.))
    assert np.array_equal(state.depth, np.full(grid.shape, 2.))
    assert np.array_equal(data, original)
    assert np.array_equal(scenario.bed, np.ones(grid.shape))
    bad_frames = [data[:-1]]
    for name, value in [('x', 100.), ('row', .5), ('col', 100.),
                        ('eta', 5.), ('h', -1.), ('hu', 99.), ('wet', 0.), ('v', np.nan)]:
        bad = data.copy()
        bad[name][0] = value
        bad_frames.append(bad)
    duplicate = data.copy()
    duplicate[0] = duplicate[1]
    bad_frames.append(duplicate)
    for bad in bad_frames:
        try:
            validate(scenario, bad)
        except ValueError:
            pass
        else:
            raise AssertionError('invalid resume state accepted')


def test_spinup_metrics_use_cross_section_flux_and_exclude_dry_cells():
    measure = runpy.run_path(str(Path(__file__).resolve().parents[1] /
        'scripts/audit_troublemaker_hydraulic_spinup.py'))['measure']
    grid = SimpleNamespace(origin_x=8168., origin_y=-40., nx=801, ny=161, dx=.5, dy=.5)
    shape = (grid.ny, grid.nx)
    depth = np.ones(shape)
    u = np.full(shape, 2.)
    v = np.zeros(shape)
    depth[:10] = 0.
    u[:10] = 1000.  # Must contribute neither flux nor wet-cell statistics.
    result = measure(depth, u, v, depth, grid)
    assert all(abs(section['discharge_m3s'] - 151.) < 1e-9 for section in result['sections'])
    assert all(region['speed_p10_p50_p90_mps'] == [2., 2., 2.] for region in result['regions'])
    assert all(region['supercritical_wet_fraction'] == 0 for region in result['regions'])
    assert result['volume_m3'] == 151 * 801 * .25


def test_experimental_throat_is_local_and_preserves_initial_section_flux():
    from raftsim.scenario2_5d import read_scenario2_5d_package
    root = Path(__file__).resolve().parents[2]
    module = runpy.run_path(str(root / 'physics/scripts/audit_troublemaker_hydraulic_spinup.py'))
    scenario = read_scenario2_5d_package(root / 'physics/data/real_world/south_fork_american_chili_bar/full_hydraulics/rapids/troublemaker/scenario/median_runnable')
    original_bed = scenario.bed.copy()
    candidate = module['interpreted_throat'](scenario, 12.)
    x, _ = scenario.grid.meshgrid()
    station = scenario.metadata.provenance['station_m']
    outside = (x <= station-34) | (x >= station+12) | (scenario.initial_state.depth == 0)
    assert np.array_equal(candidate.bed[outside], original_bed[outside])
    assert np.array_equal(scenario.bed, original_bed)
    assert np.all(candidate.bed >= original_bed)
    assert np.count_nonzero(candidate.bed != original_bed) > 0
    assert np.allclose(candidate.initial_state.hu.sum(axis=0), scenario.initial_state.hu.sum(axis=0), atol=1e-9)
    assert candidate.metadata.provenance['production_promoted'] is False
    for width in [0, float('nan'), 100]:
        try:
            module['interpreted_throat'](scenario, width)
        except ValueError:
            pass
        else:
            raise AssertionError('invalid throat width accepted')


def test_connected_throat_closes_low_bank_bypasses_without_changing_the_sill():
    from raftsim.scenario2_5d import read_scenario2_5d_package
    root = Path(__file__).resolve().parents[2]
    module = runpy.run_path(str(root / 'physics/scripts/audit_troublemaker_hydraulic_spinup.py'))
    scenario = read_scenario2_5d_package(root / 'physics/data/real_world/south_fork_american_chili_bar/full_hydraulics/rapids/troublemaker/scenario/median_runnable')
    old_bed = scenario.bed.copy()
    old_state = scenario.initial_state.hu.copy()
    candidate = module['bank_connected_throat'](scenario, 12.)
    x, y = scenario.grid.meshgrid()
    station = float(scenario.metadata.provenance['station_m'])
    center = module['_troublemaker_s_bend_centerline_m'](x, station)
    crest = np.ma.median(np.ma.masked_where(scenario.initial_state.depth <= .1,
        scenario.initial_state.eta), axis=0).filled(0.)[None, :] + .8
    full_shoulder = (x >= station-16) & (x <= station-6) & (abs(y-center) >= 7.5)
    assert np.all(candidate.bed[full_shoulder] >= np.broadcast_to(crest, candidate.bed.shape)[full_shoulder]-1e-12)
    untouched = (x <= station-34) | (x >= station+12) | (abs(y-center) <= 4.5) | (old_bed >= crest)
    assert np.array_equal(candidate.bed[untouched], old_bed[untouched])
    assert np.array_equal(candidate.bed[[0, -1], :], old_bed[[0, -1], :])
    assert np.count_nonzero((candidate.bed != old_bed) & (scenario.initial_state.depth == 0)) > 0
    assert np.max(candidate.bed-old_bed) < 4.
    assert np.array_equal(scenario.bed, old_bed)
    assert np.array_equal(scenario.initial_state.hu, old_state)
    assert np.allclose(candidate.initial_state.hu.sum(axis=0), old_state.sum(axis=0), atol=1e-9)
    assert candidate.metadata.provenance['experimental_throat_shoulders'] == 'bank_connected_v1'
    assert candidate.metadata.provenance['production_promoted'] is False
    legacy = module['interpreted_throat'](scenario, 12.)
    assert legacy.metadata.scenario_id != candidate.metadata.scenario_id
    assert not np.array_equal(legacy.bed, candidate.bed)


def test_throat_conveyance_reports_bypass_and_reverse_flow_separately():
    helper = runpy.run_path(str(Path(__file__).resolve().parents[1] /
        'scripts/audit_troublemaker_hydraulic_spinup.py'))['measure_throat_conveyance']
    grid = SimpleNamespace(origin_x=8320., origin_y=-20., nx=120, ny=81, dx=.5, dy=.5)
    depth = np.ones((grid.ny, grid.nx))
    u = np.full_like(depth, 2.)
    # All sampled columns precede the authored bend: centre is zero here.
    result = helper(depth, u, grid, 8368.5888, 12.)
    section = result['sections'][0]
    assert section['net_discharge_m3s'] == 81.
    assert section['core_net_discharge_m3s'] == 25.
    assert section['outside_net_discharge_m3s'] == 44.
    assert section['outside_forward_discharge_fraction'] == 44/81
    u[0] = -2.
    section = helper(depth, u, grid, 8368.5888, 12.)['sections'][0]
    assert section['net_discharge_m3s'] == 79.
    assert section['outside_net_discharge_m3s'] == 42.
    assert section['outside_forward_discharge_fraction'] == 43/80
