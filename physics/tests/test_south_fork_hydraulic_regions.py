import importlib.util
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('regions', ROOT/'physics/scripts/prepare_south_fork_hydraulic_regions.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_region_centers_follow_original_corner_and_shared_lattice():
    points = np.array([[0, 0, 0], [70, 70, 0], [170, 70, 100]], dtype=float)
    station, centers = MODULE.region_centers(points, np.array([1000., 2000.]), 40)
    assert np.array_equal(station, [0, 40, 80, 120, 160, 170])
    assert np.array_equal(centers, [[1000,2000], [1040,2000], [1070,2010], [1070,2050], [1070,2090], [1070,2100]])
    assert centers.dtype == np.int64


def test_coverage_requires_whole_live_window_in_two_axes():
    margin, index = MODULE.coverage_margin(np.array([[40, 0], [0, 90], [80, 80]]), np.array([[0, 0], [80, 0]]))
    assert np.array_equal(margin, [120, 70, 80])
    assert margin[0] >= MODULE.HALF_LIVE_M
    assert np.all(margin[1:] < MODULE.HALF_LIVE_M)
