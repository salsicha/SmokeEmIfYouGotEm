"""Opt-in execution tests for the Windows SM5 harness, not a GPU emulator.

Set RAFTSIM_GPU_CONTROL_EXE, RAFTSIM_GPU_CONTROL_ADD_SHADER and
RAFTSIM_GPU_CONTROL_FACE_SHADER to freshly built operation9/4 artifacts.
Unconfigured hosts skip; skips are not evidence of SM5 acceptance.
"""
import os
from pathlib import Path
import struct
import subprocess

import pytest


@pytest.fixture
def artifacts():
    keys = ('RAFTSIM_GPU_CONTROL_EXE', 'RAFTSIM_GPU_CONTROL_ADD_SHADER',
            'RAFTSIM_GPU_CONTROL_FACE_SHADER')
    values = [os.environ.get(key) for key in keys]
    if os.name != 'nt' or not all(values):
        pytest.skip('Actual Windows SM5 artifacts must be explicitly configured')
    paths = [Path(value).resolve() for value in values]
    assert all(path.is_file() for path in paths), 'Configured artifacts must exist'
    return paths


def payload(face=False):
    # 33 records exercise a padded dispatch; all eight face output words count.
    if face:
        record = struct.pack('<16f8I', 1, 1, 1, 0, 0, 0, 0, 1,
                             1, 1, 1, 0, 0, 0, 0, -1,
                             0x3f800000, 0x3f800000, 0x3f800000, 0x3f800000,
                             1, 1, 0, 0)
    else:
        record = struct.pack('<4fI', 1, 2, 0, 0, 0x40400000)
    return struct.pack('<3I', 0x52534650, 5 if face else 10, 33) + record * 33


def run(artifacts, tmp_path, data, face=False, backend='warp'):
    exe, scalar, faces = artifacts
    fixture = tmp_path / 'fixture.bin'
    fixture.write_bytes(data)
    command = [str(exe), str(faces if face else scalar), str(fixture)]
    if backend == 'warp':
        command.append('warp')
    return subprocess.run(command, capture_output=True, text=True, timeout=60)


@pytest.mark.parametrize('face', [False, True])
@pytest.mark.parametrize('backend', ['hardware', 'warp'])
def test_actual_padded_dispatch(artifacts, tmp_path, face, backend):
    result = run(artifacts, tmp_path, payload(face), face, backend)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'cases=33 arithmetic_errors=0' in result.stdout
    assert 'transported_input_errors=0 operation_errors=0' in result.stdout


@pytest.mark.parametrize('face', [False, True])
@pytest.mark.parametrize('damage', ['header', 'count', 'truncated', 'extra'])
def test_malformed_fixture_rejected_before_dispatch(artifacts, tmp_path, face, damage):
    data = bytearray(payload(face))
    if damage == 'header':
        data[0] ^= 1
    elif damage == 'count':
        struct.pack_into('<I', data, 8, 65537)
    elif damage == 'truncated':
        data.pop()
    else:
        data.append(0)
    assert run(artifacts, tmp_path, data, face).returncode == 2


@pytest.mark.parametrize('face', [False, True])
def test_final_expected_word_is_checked(artifacts, tmp_path, face):
    data = bytearray(payload(face))
    data[-4] ^= 1
    result = run(artifacts, tmp_path, data, face)
    assert result.returncode == 1, result.stdout + result.stderr
    assert 'arithmetic_errors=1' in result.stdout


def test_wrong_compiled_operation_cannot_pass_on_matching_values(artifacts, tmp_path):
    data = bytearray(payload())
    # Claim multiplication while retaining this addition shader and matching
    # expected numbers. Value agreement alone must never qualify a wrong CSO.
    struct.pack_into('<I', data, 4, 8)
    result = run(artifacts, tmp_path, data)
    assert result.returncode == 1, result.stdout + result.stderr
    assert 'arithmetic_errors=0' in result.stdout
    assert 'operation_errors=33' in result.stdout
