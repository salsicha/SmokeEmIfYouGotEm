"""Actual standalone SM5 transport-to-pressure tests; no RK2/scene acceptance."""
import os
from pathlib import Path
import shutil
import struct
import subprocess

import pytest


@pytest.fixture
def artifacts():
    keys = ('RAFTSIM_TRANSPORT_CONTROL_EXE', 'RAFTSIM_TRANSPORT_CONTROL_SHADERS',
            'RAFTSIM_TRANSPORT_CONTROL_FIXTURE', 'RAFTSIM_PRESSURE_CONTROL_SHADERS')
    values = [os.environ.get(key) for key in keys]
    if os.name != 'nt' or not all(values):
        pytest.skip('Explicit actual Windows SM5 coupled artifacts required')
    exe, transport, fixture, pressure = map(lambda v: Path(v).resolve(), values)
    assert exe.is_file() and fixture.is_file()
    assert all((transport / f'{p}.cso').is_file() for p in range(6))
    names = [f'pressure-{p}' for p in range(7)] + ['acceleration-prepare']
    names += [f'acceleration-{p}' for p in (1,2,3,4,5,6,11,12,13,14)]
    assert all((pressure / f'{name}.cso').is_file() for name in names)
    return exe, transport, fixture, pressure


def run(artifacts, fixture=None, backend='hardware', pressure=None):
    exe, transport, original, compiled = artifacts
    return subprocess.run([str(exe), 'run-coupled', str(transport), str(fixture or original),
                           backend, str(pressure or compiled)], capture_output=True, text=True, timeout=900)


@pytest.mark.parametrize('backend', ['hardware', 'warp'])
def test_original_full_coupled_fixture(artifacts, backend):
    result = run(artifacts, backend=backend)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'transport_pass=1 coupled_pressure_fixture_pass=1 step_accepted=0' in result.stdout
    count, = struct.unpack_from('<I', artifacts[2].read_bytes(), 8)
    rows = [line for line in result.stdout.splitlines() if ' pressure_tags=' in line]
    assert len(rows) == count
    assert all('pressure_tags=1' in row and 'coupled_pressure_pass=1' in row for row in rows)


@pytest.mark.parametrize('backend', ['hardware', 'warp'])
def test_actual_activity_guard_preserves_inactive_outputs(artifacts, backend):
    result = subprocess.run([str(artifacts[0]), 'test-pressure-guard',
                             str(artifacts[3] / 'acceleration-6.cso'), backend],
                            capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'activity_guard_cases=20 activity_guard_pass=1 step_accepted=0' in result.stdout


def resting_fixture(artifacts, tmp_path, damage=None):
    data = artifacts[2].read_bytes()
    x,y = struct.unpack_from('<2I', data, 12)
    n = x*y
    record = bytearray(data[12:12+24+60*n])
    assert len(record) == 24+60*n
    # Eight copies retain the original minimum-count gate; fast rejection tests
    # do not stand in for either full original fixture/backend pass above.
    if damage == 'force':
        struct.pack_into('<f', record, 24+48*n, 1.)
    elif damage == 'fraction':
        struct.pack_into('<f', record, 24+56*n, -0.25)
    path = tmp_path / 'resting.bin'
    path.write_bytes(data[:8]+struct.pack('<I',8)+record*8)
    return path


@pytest.mark.parametrize('damage', ['force', 'fraction'])
def test_changed_expected_force_or_invalid_fraction_cannot_pass(artifacts, tmp_path, damage):
    result = run(artifacts, fixture=resting_fixture(artifacts,tmp_path,damage))
    assert result.returncode == 1, result.stdout + result.stderr
    assert 'coupled_pressure_fixture_pass=0' in result.stdout
    if damage == 'fraction':
        first = next(row for row in result.stdout.splitlines() if 'case=0 pressure_tags=' in row)
        assert 'pressure_diagnostics=0/' not in first


def test_wrong_phase_order_cannot_pass_even_for_rest(artifacts, tmp_path):
    compiled = tmp_path / 'wrong-order'
    shutil.copytree(artifacts[3], compiled)
    a,b = (compiled / f'pressure-{p}.cso' for p in (0,1))
    first,second = a.read_bytes(), b.read_bytes()
    a.write_bytes(second)
    b.write_bytes(first)
    result = run(artifacts, fixture=resting_fixture(artifacts,tmp_path), pressure=compiled)
    assert result.returncode == 1, result.stdout + result.stderr
    assert 'pressure_tags=0' in result.stdout
    assert 'coupled_pressure_fixture_pass=0' in result.stdout


def test_missing_pressure_phase_cannot_pass(artifacts, tmp_path):
    result = run(artifacts, pressure=tmp_path)
    assert result.returncode == 2
    assert 'Missing input:' in result.stderr
