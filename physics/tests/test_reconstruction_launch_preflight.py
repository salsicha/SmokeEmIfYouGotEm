"""Native launch preflight must keep coverage and wet-state guards strict."""
import importlib.util
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest


@pytest.fixture
def checks(monkeypatch):
    monkeypatch.setitem(sys.modules, 'unreal', SimpleNamespace())
    path = Path(__file__).resolve().parents[2] / 'unreal/Scripts/verify_south_fork_reconstruction_launches.py'
    spec = importlib.util.spec_from_file_location('native_launch_preflight', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def stream(bounds, extent=None):
    return dict(live_window_extent_m=extent or [224., 224.], windows=[dict(
        cooked_fields_manifest='tmp/window/manifest.json', valid_live_center_bounds_m=bounds)])


def test_exact_eight_metre_margin_is_inclusive(checks):
    data = stream([[0., 0., 10., 10.]])
    assert checks.candidates(data, 114., 5.) == [(104.**2, 'tmp/window/manifest.json', 10., 5.)]
    assert not checks.candidates(data, 114.000001, 5.)


def test_inside_crop_is_not_shifted_and_duplicate_rectangles_deduplicate(checks):
    assert checks.candidates(stream([[0., 0., 10., 10.]]*2), 5., 6.) == [
        (0., 'tmp/window/manifest.json', 5., 6.)]


@pytest.mark.parametrize('rectangle', [[2., 0., 1., 3.], [0., 2., 3., 1.],
                                       [float('nan'), 0., 1., 1.], [0., 0., float('inf'), 1.]])
def test_invalid_coverage_rejected(checks, rectangle):
    with pytest.raises(ValueError, match='coverage rectangle'):
        checks.candidates(stream([rectangle]), 0., 0.)


def test_extent_cannot_silently_change_margin(checks):
    with pytest.raises(ValueError, match='live extent'):
        checks.candidates(stream([[0., 0., 1., 1.]], [240., 240.]), 0., 0.)


def sample(**changes):
    return SimpleNamespace(**(dict(wet=True, bed_height_meters=1., depth_meters=2.,
        surface_height_meters=3., velocity_meters_per_second=SimpleNamespace(x=1., y=-1.)) | changes))


@pytest.mark.parametrize('field', ['bed_height_meters', 'depth_meters', 'surface_height_meters'])
def test_nonfinite_sample_rejected(checks, field):
    with pytest.raises(ValueError, match='Invalid native state'):
        checks.sample_values(sample(**{field: float('nan')}))


def test_dry_sample_is_reported_not_relabelled_wet(checks):
    result = checks.sample_values(sample(wet=False, depth_meters=0.))
    assert not result['wet'] and result['depth_m'] == 0.


def test_negative_depth_and_missing_sample_rejected(checks):
    for value in (None, sample(depth_meters=-1e-12)):
        with pytest.raises(ValueError):
            checks.sample_values(value)


def test_native_contract_helpers_import_without_site_packages():
    scripts = Path(__file__).resolve().parents[1] / 'scripts'
    result = subprocess.run([sys.executable, '-S', '-c',
        'import sys; sys.path.insert(0, sys.argv[1]); '
        'from prepare_south_fork_joint_preview import Dependencies, verify_audits', str(scripts)],
        capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
