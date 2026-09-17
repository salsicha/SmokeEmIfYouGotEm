"""Actual Windows SM5 transport harness checks; unconfigured hosts skip.

Required: RAFTSIM_TRANSPORT_CONTROL_EXE, RAFTSIM_TRANSPORT_CONTROL_SHADERS,
RAFTSIM_TRANSPORT_CONTROL_FIXTURE. Use a complete compiled phase set and the
unchanged matching original fixture. These tests do not qualify pressure/RK2.
"""
import os
from pathlib import Path
import struct
import subprocess

import pytest


@pytest.fixture
def artifacts():
    keys = ('RAFTSIM_TRANSPORT_CONTROL_EXE', 'RAFTSIM_TRANSPORT_CONTROL_SHADERS',
            'RAFTSIM_TRANSPORT_CONTROL_FIXTURE')
    values = [os.environ.get(key) for key in keys]
    if os.name != 'nt' or not all(values):
        pytest.skip('Explicit actual Windows SM5 transport artifacts required')
    exe, shaders, fixture = [Path(value).resolve() for value in values]
    assert exe.is_file() and fixture.is_file()
    assert all((shaders / f'{phase}.cso').is_file() for phase in range(6))
    return exe, shaders, fixture


def run(artifacts, path, backend='warp'):
    exe, shaders, _ = artifacts
    return subprocess.run([str(exe), 'run', str(shaders), str(path), backend],
                          capture_output=True, text=True, timeout=60)


@pytest.mark.parametrize('backend', ['hardware', 'warp'])
def test_original_transport_fixture(artifacts, backend):
    result = run(artifacts, artifacts[2], backend)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'transport_pass=1 pressure_or_step_accepted=0' in result.stdout


@pytest.mark.parametrize('damage', ['magic', 'version', 'count', 'dimensions', 'truncate', 'tail'])
def test_malformed_fixture_is_not_a_pass(artifacts, tmp_path, damage):
    data = bytearray(artifacts[2].read_bytes())
    if damage == 'magic':
        data[0] ^= 1
    elif damage == 'version':
        struct.pack_into('<I', data, 4, 4)
    elif damage == 'count':
        struct.pack_into('<I', data, 8, 33)
    elif damage == 'dimensions':
        struct.pack_into('<I', data, 12, 513)
    elif damage == 'truncate':
        del data[36:]
    else:
        data.append(0)
    path = tmp_path / 'malformed.bin'
    path.write_bytes(data)
    assert run(artifacts, path).returncode == 2


@pytest.mark.parametrize('damage', ['negative_depth', 'dry_momentum', 'infinite_bed', 'negative_foam'])
def test_original_invalid_state_cases_rejected(artifacts, tmp_path, damage):
    data = bytearray(artifacts[2].read_bytes())
    x, y = struct.unpack_from('<2I', data, 12)
    assert x*y > 3
    bed, state = 36, 36+4*x*y
    if damage == 'negative_depth':
        struct.pack_into('<f', data, state+3*16, -1)
    elif damage == 'dry_momentum':
        struct.pack_into('<2f', data, state+3*16, 0, 1)
    elif damage == 'infinite_bed':
        struct.pack_into('<f', data, bed+3*4, float('inf'))
    else:
        struct.pack_into('<f', data, state+3*16+12, -1)
    path = tmp_path / 'invalid-state.bin'
    path.write_bytes(data)
    result = run(artifacts, path)
    assert result.returncode == 1, result.stdout + result.stderr
    assert 'case=0 pairs_mismatched=' in result.stdout
    first = next(line for line in result.stdout.splitlines() if line.startswith('case=0 pairs_mismatched='))
    assert 'diagnostics=0/' not in first
    assert 'cfl=0 ' in first


def test_compiled_model_tag_must_match_fixture(artifacts, tmp_path):
    data = bytearray(artifacts[2].read_bytes())
    version, = struct.unpack_from('<I', data, 4)
    struct.pack_into('<I', data, 4, 1 if version != 1 else 3)
    path = tmp_path / 'wrong-model.bin'
    path.write_bytes(data)
    result = run(artifacts, path)
    assert result.returncode == 1, result.stdout + result.stderr
    assert 'transport_pass=0' in result.stdout
