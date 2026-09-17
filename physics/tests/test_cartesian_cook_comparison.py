import pytest
import subprocess
import sys
from pathlib import Path
from compare_cartesian_cook_binaries import physical_records


def test_only_wall_time_is_excluded():
    rows = [dict(step=0, time_seconds=600., elapsed_wall_seconds=.2, volume_m3=3., snapshot=True),
            dict(step=20, time_seconds=601., elapsed_wall_seconds=20., volume_m3=4., snapshot=True)]
    changed = [dict(row, elapsed_wall_seconds=row['elapsed_wall_seconds']+12.) for row in rows]
    assert physical_records(rows) == physical_records(changed)
    for key in ('time_seconds', 'volume_m3', 'snapshot', 'step'):
        changed = [dict(row) for row in rows]
        changed[-1][key] = 100
        assert physical_records(rows) != physical_records(changed)
    assert rows[-1]['elapsed_wall_seconds'] == 20.


@pytest.mark.parametrize('seconds', [-1., float('nan'), float('inf')])
def test_invalid_timing_rejected(seconds):
    with pytest.raises(ValueError):
        physical_records([dict(step=0, elapsed_wall_seconds=seconds)])


@pytest.mark.parametrize('rows', [[], [dict(step=1, elapsed_wall_seconds=1.)]])
def test_missing_initial_record_rejected(rows):
    with pytest.raises(ValueError):
        physical_records(rows)


@pytest.mark.parametrize('option', ['--baseline-workers', '--candidate-workers'])
@pytest.mark.parametrize('value', ['0', '65', '-1', 'eight'])
def test_invalid_worker_request_fails_before_creating_output(tmp_path, option, value):
    script=Path(__file__).resolve().parents[1]/'scripts/compare_cartesian_cook_binaries.py'
    output=tmp_path/'comparison'
    result=subprocess.run([sys.executable,str(script),'absent-manifest.json',str(output),
                           '--baseline','absent-baseline.exe','--candidate','absent-candidate.exe',
                           option,value],capture_output=True,text=True)
    assert result.returncode == 2
    assert not output.exists()
    assert 'worker' in result.stderr
    assert 'FileNotFoundError' not in result.stderr
