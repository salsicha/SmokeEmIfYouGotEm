"""Execute the actual PowerShell evidence parser; encoding is not FPS acceptance."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[2]
PWSH = shutil.which('pwsh')
pytestmark = pytest.mark.skipif(not PWSH, reason='PowerShell 7 required')


def parse(root, text):
    script = ROOT/'unreal/Scripts/raftsim_startup_motion_evidence.ps1'
    command = ("$ErrorActionPreference='Stop'; . '"+str(script).replace("'", "''")+
               "'; Get-RaftSimStartupMotionEvidence -VideoRoot $env:RAFTSIM_TEST_VIDEO_ROOT "
               "-LogText $env:RAFTSIM_TEST_VIDEO_LOG | ConvertTo-Json -Compress")
    import os
    return subprocess.run([PWSH, '-NoProfile', '-Command', command], capture_output=True, text=True,
        env=dict(os.environ, RAFTSIM_TEST_VIDEO_ROOT=str(root), RAFTSIM_TEST_VIDEO_LOG=text))


def line(path, frames=31, seconds='1.750'):
    return f'RaftSim recording saved: {path} ({frames} source_frames, {seconds} s; encoder may repeat frames to preserve duration)'


def test_finalized_file_is_not_a_decoding_or_fps_claim(tmp_path):
    video = tmp_path/'capture.mp4'; video.write_bytes(b'not a decoded video')
    result = parse(tmp_path, line(video))
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data['source_frames'] == 31 and data['duration_seconds'] == 1.75
    assert data['sha256'] == hashlib.sha256(video.read_bytes()).hexdigest()
    assert data['encoder_may_repeat_frames']
    assert not data['fully_decoded'] and not data['performance_accepted'] and not data['visual_accepted']


@pytest.mark.parametrize('case', ['missing', 'duplicate', 'one_frame', 'zero_time', 'empty', 'absent', 'outside'])
def test_incomplete_or_unscoped_recording_rejected(tmp_path, case):
    root = tmp_path/'videos'; root.mkdir()
    video = root/'capture.mp4'; video.write_bytes(b'evidence')
    text = line(video)
    if case == 'missing': text = 'Game exited 0 without recording'
    elif case == 'duplicate': text += '\n'+text
    elif case == 'one_frame': text = line(video, frames=1)
    elif case == 'zero_time': text = line(video, seconds='0.000')
    elif case == 'empty': video.write_bytes(b'')
    elif case == 'absent': text = line(root/'missing.mp4')
    elif case == 'outside':
        outside = tmp_path/'outside.mp4'; outside.write_bytes(b'evidence'); text = line(outside)
    assert parse(root, text).returncode != 0


def test_recording_cannot_be_used_as_normal_fps_capture():
    result = subprocess.run([PWSH, '-NoProfile', '-File', str(ROOT/'unreal/Scripts/profile_south_fork_current_map.ps1'),
        '-Label', 'south-fork-test-invalid-motion', '-CookProcessId', '1', '-CookStartUtc', 'invalid',
        '-RecordStartupMotion'], capture_output=True, text=True)
    assert result.returncode != 0 and 'Motion recording requires StartupRenderReplay' in result.stderr
