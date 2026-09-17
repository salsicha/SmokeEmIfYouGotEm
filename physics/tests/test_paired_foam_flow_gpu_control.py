"""Execute the real production HLSL helper; configured native runner required."""
import os
from pathlib import Path
import subprocess
import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def runner():
    path = os.environ.get('RAFTSIM_PAIRED_FOAM_GPU_EXE')
    if os.name != 'nt' or not path:
        pytest.skip('Configure the Windows D3D paired-flow runner; a skip is not GPU acceptance')
    assert Path(path).is_file()
    return path


@pytest.mark.parametrize('backend', ['hardware', 'warp'])
def test_exact_production_registered_flow(runner, backend):
    result = subprocess.run([runner, str(ROOT/'unreal/Plugins/RaftSim/Shaders/Private'), backend],
                            capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'variants=10 checked_words=3600 wrong=0 max_error=0' in result.stdout
    assert 'visual_accepted=0' in result.stdout


def test_unknown_backend_is_not_silently_hardware(runner):
    result = subprocess.run([runner, str(ROOT/'unreal/Plugins/RaftSim/Shaders/Private'), 'unknown'],
                            capture_output=True, text=True, timeout=60)
    assert result.returncode == 2
