"""Restart audits must reject altered physics even with internally valid hashes."""
import copy

import pytest

from audit_cartesian_snapshot_restart import verify_retained_inputs
from prepare_cartesian_snapshot_restart import make_restart_manifest


def manifest():
    return dict(schema='cook', dt_seconds=.05, boundary_probes=[{'edge': 'west'}],
                vertical_datum_navd88_m=220., target_discharge_m3s=45.,
                terrain_union={'source': 'captured'}, measured_bathymetry=False,
                future_solver_setting={'order': 2}, packages=['core'], inputs=[],
                geometry_manifest='geometry', geometry_manifest_sha256='abc')


def scenario():
    return dict(schema_version='scenario', fixed_dt=.05, duration=600.,
                grid={'nx': 80}, boundaries=[{'edge': 'west', 'kind': 'outflow'}],
                roughness=.035, raft={'drag_coefficient': 1.25},
                array_files={'bed': 'bed.npy'}, feature_count=0, probe_count=0,
                metadata=dict(river_id='south_fork', scenario_id='core',
                              generator='old', description='old', provenance={'old': True}))


def test_only_restart_bookkeeping_changes_and_inputs_stay_untouched():
    old = manifest()
    saved = copy.deepcopy(old)
    new = make_restart_manifest(old, 7200.)
    new.update(geometry_manifest='extended', geometry_manifest_sha256='def', restart={})
    verify_retained_inputs(old, new)
    assert old == saved
    old = scenario()
    new = copy.deepcopy(old)
    new['metadata'].update(generator='restart', description='continued', provenance={'new': True})
    verify_retained_inputs(old, new, scenario=True)


@pytest.mark.parametrize('field', [k for k in manifest()
    if k not in {'packages', 'inputs', 'geometry_manifest', 'geometry_manifest_sha256'}])
def test_every_retained_manifest_setting_rejects_change(field):
    old = manifest()
    new = make_restart_manifest(old, 7200.)
    new[field] = .1 if field == 'dt_seconds' else 'changed'
    with pytest.raises(AssertionError):
        verify_retained_inputs(old, new)


@pytest.mark.parametrize('field', [k for k in scenario() if k != 'metadata'])
def test_every_retained_scenario_setting_rejects_change(field):
    old = scenario()
    new = copy.deepcopy(old)
    new[field] = 'changed'
    with pytest.raises(AssertionError):
        verify_retained_inputs(old, new, scenario=True)


@pytest.mark.parametrize('field', ['initialization_is_fresh_not_restart', 'settled_hydraulics', 'normal_map_integrated'])
def test_restart_cannot_claim_cold_start_or_acceptance(field):
    old = manifest()
    new = make_restart_manifest(old, 7200.)
    new[field] = True
    with pytest.raises(AssertionError):
        verify_retained_inputs(old, new)


@pytest.mark.parametrize('scenario_mode', [False, True])
@pytest.mark.parametrize('mutation', ['missing', 'extra', 'identity'])
def test_missing_extra_or_identity_fields_do_not_escape(scenario_mode, mutation):
    old = scenario() if scenario_mode else manifest()
    new = copy.deepcopy(old) if scenario_mode else make_restart_manifest(old, 7200.)
    if mutation == 'missing':
        del new['roughness' if scenario_mode else 'target_discharge_m3s']
    elif mutation == 'extra':
        new['new_solver_setting'] = 17
    elif scenario_mode:
        new['metadata']['river_id'] = 'different_river'
    else:
        new['terrain_union']['source'] = 'different_source'
    with pytest.raises(AssertionError):
        verify_retained_inputs(old, new, scenario=scenario_mode)
