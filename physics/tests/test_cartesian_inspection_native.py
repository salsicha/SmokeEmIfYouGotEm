"""End-to-end read-only checkpoint tests against the compiled native CLI.

Set RAFTSIM_CARTESIAN_INSPECT to the CMake-built executable to run these tests.
No production cook input or checkpoint is modified by these tiny fixtures.
"""
import json
import os
from pathlib import Path
import subprocess

import numpy as np
import pytest

import inspect_cartesian_inundation as inspection


@pytest.fixture
def solver():
    value = os.environ.get('RAFTSIM_CARTESIAN_INSPECT')
    if not value:
        pytest.skip('Set RAFTSIM_CARTESIAN_INSPECT to run native integration tests')
    path = Path(value).resolve()
    assert path.is_file(), 'Configured inspector executable is missing'
    return path


@pytest.fixture
def cook(tmp_path, monkeypatch):
    monkeypatch.setattr(inspection, 'ROOT', tmp_path)
    source = tmp_path / 'source'
    source.mkdir()
    output = tmp_path / 'cook'
    output.mkdir()
    inputs, regions = [], []
    for i in range(2):
        name = f'core_{i:04d}'
        package = source / name
        package.mkdir()
        bed, h, zero = np.zeros((4, 4)), np.full((4, 4), .5), np.zeros((4, 4))
        np.save(package / 'bed.npy', bed)
        np.savez(package / 'initial_state.npz', depth=h, eta=h, u=zero, v=zero,
                 hu=zero, hv=zero, wet=h > 1.e-6)
        (package / 'features.json').write_text('{"features":[]}')
        (package / 'probes.json').write_text('{"probes":[]}')
        scenario = dict(schema_version='raftsim.scenario2_5d.v0',
            metadata=dict(scenario_id=name, scenario_type='fixture'),
            grid=dict(nx=4, ny=4, dx=1., dy=1., origin_x=i*4., origin_y=0.),
            fixed_dt=.05, duration=1., roughness=.035,
            array_files=dict(bed='bed.npy', initial_state='initial_state.npz', features='features.json', probes='probes.json'),
            boundaries=[dict(edge=edge, kind='bank') for edge in ('west','east','south','north')])
        (package / 'scenario.json').write_text(json.dumps(scenario))
        inputs.append(dict(name=name, files={p.name: inspection.sha(p) for p in package.iterdir()}))
        geometry_path = tmp_path / f'{name}.npz'
        np.savez(geometry_path, bed_navd88_m=bed, captured_surface_navd88_m=h,
                 captured_water_mask=np.ones((4,4), dtype=np.uint8))
        regions.append(dict(name=name, geometry_file=geometry_path.name,
            geometry_sha256=inspection.sha(geometry_path), grid_origin_local_m=[i*4.,0.]))
    geometry = tmp_path / 'geometry.json'
    geometry.write_text(json.dumps(dict(regions=regions, grid_spacing_m=1., core_shape=[4,4], vertical_datum_navd88_m=0.)))
    manifest = dict(schema='raftsim.cartesian_flow_cook.v1', dt_seconds=.05,
        packages=[r['name'] for r in inputs], inputs=inputs,
        geometry_manifest=geometry.name, geometry_manifest_sha256=inspection.sha(geometry), vertical_datum_navd88_m=0.)
    source_manifest = source / 'manifest.json'
    source_manifest.write_text(json.dumps(manifest))
    (output / 'input_manifest.json').write_bytes(source_manifest.read_bytes())
    (output / 'input_manifest_path.txt').write_text(str(source_manifest))
    for step in (0, 5):
        frame = output / f'frame_{step:06d}'
        frame.mkdir()
        depth = np.full((8,4), .5) if step == 0 else np.vstack((np.full((4,4),.6), np.full((4,4),.7)))
        for key, array in (('h',depth), ('u',np.zeros((8,4))), ('v',np.zeros((8,4)))):
            np.save(frame / f'{key}.npy', array)
        (frame / 'complete.json').write_text(json.dumps(dict(step=step, snapshot=True, time_seconds=step*.05, volume_m3=float(depth.sum()))))
    return source_manifest, output


def run(solver, cook, *indices):
    source, output = cook
    return subprocess.run([str(solver), str(source), str(output/'frame_000005'), *map(str, indices)],
                          capture_output=True, text=True)


def test_native_restores_checkpoint_without_writes_or_steps(solver, cook):
    root = cook[1].parent
    before = {p: inspection.sha(p) for p in root.rglob('*') if p.is_file()}
    result = run(solver, cook, 1, 0)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report['time_seconds'] == .25
    assert report['solver_steps_run'] == 0 and report['state_unchanged']
    assert not report['settling_accepted'] and not report['playable_integrated']
    assert [r['tile_index'] for r in report['tiles']] == [0, 1]
    assert report['selected_volume_m3'] == pytest.approx(20.8)
    assert report['instantaneous_selected_net_inflow_m3s'] == 0.
    assert report['tiles'][0]['inward_flux_m3s'][1] == -report['tiles'][1]['inward_flux_m3s'][0]
    assert report['tiles'][0]['inward_flux_m3s'][1] != 0.
    assert before == {p: inspection.sha(p) for p in root.rglob('*') if p.is_file()}


@pytest.mark.parametrize('indices', [(-1,), (2,), (0,0), ('0garbage',)])
def test_native_rejects_invalid_selection(solver, cook, indices):
    result = run(solver, cook, *indices)
    assert result.returncode != 0
    assert not result.stdout


@pytest.mark.parametrize('field,value', [('h',-1.), ('h',11.), ('u',21.), ('v',float('nan'))])
def test_native_rejects_invalid_checkpoint_state(solver, cook, field, value):
    path = cook[1] / 'frame_000005' / f'{field}.npy'
    data = np.load(path)
    data[0,0] = value
    np.save(path, data)
    result = run(solver, cook, 0)
    assert result.returncode != 0 and 'state gate' in result.stderr


@pytest.mark.parametrize('field,value', [('step',6), ('snapshot',False), ('time_seconds',-1.), ('volume_m3',999.)])
def test_native_rejects_false_completion_record(solver, cook, field, value):
    path = cook[1] / 'frame_000005/complete.json'
    record = json.loads(path.read_text())
    record[field] = value
    path.write_text(json.dumps(record))
    assert run(solver, cook, 0).returncode != 0


def test_wrapper_binds_real_native_results_to_source_geometry(solver, cook):
    report = inspection.inspect(cook[1], [0,5], ['core_0000','core_0001'], solver, [3.5,1.5], 2.)
    assert len(report['history']) == 2
    assert report['history'][1]['internal_face_cancellation_error_m3s'] == 0.
    assert report['history'][1]['interval_selected_volume_rate_m3s'] == pytest.approx(19.2)
    assert report['history'][1]['local_circle']['cells'] == 12
    assert not report['settling_accepted'] and not report['visual_accepted']
    assert str(solver) in report['dependencies']


def test_wrapper_rejects_changed_input(solver, cook):
    (cook[0].parent / 'core_0000/features.json').write_text('{"features": []}')
    with pytest.raises(ValueError, match='Changed dependency'):
        inspection.inspect(cook[1], [0,5], ['core_0000'], solver, [1.,1.], 2.)


def test_wrapper_rejects_changed_frame_zero(solver, cook):
    np.save(cook[1] / 'frame_000000/h.npy', np.full((8,4), .4))
    with pytest.raises(ValueError, match='Frame-zero/input depth mismatch'):
        inspection.inspect(cook[1], [5], ['core_0000'], solver, [1.,1.], 2.)


@pytest.mark.parametrize('field,value,message', [
    ('grid_spacing_m', 2., 'spacing'),
    ('core_shape', [3,4], 'dimensions'),
    ('vertical_datum_navd88_m', 1., 'datum'),
])
def test_wrapper_rejects_hash_valid_but_misregistered_source(solver, cook, field, value, message):
    geometry = cook[1].parent / 'geometry.json'
    data = json.loads(geometry.read_text())
    data[field] = value
    geometry.write_text(json.dumps(data))
    manifest = json.loads(cook[0].read_text())
    manifest['geometry_manifest_sha256'] = inspection.sha(geometry)
    cook[0].write_text(json.dumps(manifest))
    (cook[1] / 'input_manifest.json').write_bytes(cook[0].read_bytes())
    with pytest.raises(ValueError, match=message):
        inspection.inspect(cook[1], [5], ['core_0000'], solver, [1.,1.], 2.)
