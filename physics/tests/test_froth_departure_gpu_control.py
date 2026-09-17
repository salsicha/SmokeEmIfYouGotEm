import os
from pathlib import Path
import subprocess
import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize('backend', ['hardware', 'warp'])
def test_actual_departure_shader(backend):
    runner = os.environ.get('RAFTSIM_FROTH_DEPARTURE_GPU_EXE')
    if os.name != 'nt' or not runner:
        pytest.skip('Configure the Windows GPU runner; a skip is not acceptance')
    assert Path(runner).is_file()
    result = subprocess.run([runner, str(ROOT/'unreal/Plugins/RaftSim/Shaders/Private'), backend],
                            text=True, capture_output=True, timeout=60)
    assert result.returncode == 0, result.stdout+result.stderr
    assert 'variants=17 checked_words=2448 wrong=0' in result.stdout
    assert 'rotation_second_order=1 visual_accepted=0' in result.stdout
