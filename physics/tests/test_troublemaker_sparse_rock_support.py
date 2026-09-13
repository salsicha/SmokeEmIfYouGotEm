import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from recover_troublemaker_sparse_rock_support import corroborated_cells


def fixture():
    authority = np.full((5, 5), 2)
    authority[1, 2] = authority[2, 1] = 3
    height = np.full((5, 5), 2.)
    height[authority == 3] = 5.
    candidate = np.full((5, 5), np.nan)
    candidate[2, 2] = 5.1
    return authority, height, candidate, np.isfinite(candidate)


def test_two_original_neighbours_corroborate_measured_return():
    assert corroborated_cells(*fixture())[2, 2]


def test_one_neighbour_is_insufficient():
    a, h, c, mask = fixture()
    a[1, 2] = 2
    assert not corroborated_cells(a, h, c, mask).any()


def test_cannot_overwrite_measured_ground_or_rock():
    for authority in (1, 3, 4):
        a, h, c, mask = fixture()
        a[2, 2] = authority
        assert not corroborated_cells(a, h, c, mask).any()


def test_high_canopy_and_low_water_returns_rejected():
    for height in (6.01, 3.99, np.nan, np.inf):
        a, h, c, mask = fixture()
        c[2, 2] = height
        assert not corroborated_cells(a, h, c, mask).any()


def test_new_support_does_not_propagate():
    a, h, c, mask = fixture()
    c[3, 3] = 5.1
    result = corroborated_cells(a, h, c, np.isfinite(c))
    assert result[2, 2] and not result[3, 3]


def test_recovered_mesh_preserves_existing_measurements_and_mask():
    from PIL import Image
    from audit_troublemaker_sparse_rock_returns import ROOT, SOURCE
    with np.load(SOURCE/'registered_mesh_source.npz') as old, np.load(ROOT/'tmp/troublemaker-sparse-rock-support-20260912/registered_mesh_source.npz') as new:
        changed = old['authority'] != new['authority']
        assert changed.sum() == 420
        for key in ('east_m', 'north_m', 'z_m', 'authority'):
            assert np.array_equal(old[key][~changed], new[key][~changed])
        assert np.all(old['authority'][changed] == 2)
        mask = np.asarray(Image.open(ROOT/'unreal/SourceArt/RaftSim/TroublemakerSparseRockAuthority20260912/T_TroublemakerSurfaceAuthority.png'))
        assert np.array_equal(mask[:,:,1] > 0, new['authority'] == 3)
        assert not mask[:,:,0][new['authority'] != 1].any()


def test_added_vertices_are_original_captured_returns_not_synthetic_heights():
    import json
    from audit_troublemaker_sparse_rock_returns import ROOT, BASE
    directory = ROOT/'tmp/troublemaker-sparse-rock-support-20260912'
    manifest = json.loads((directory/'manifest.json').read_text())
    with np.load(directory/'registered_mesh_source.npz') as mesh, np.load(BASE/'classified_lidar_returns.npz') as points:
        selected = mesh['rock_source_return_index']
        rock = mesh['authority'] == 3
        assert np.array_equal(mesh['east_m'][rock], points['utm_easting_m'][selected]-manifest['origin_utm_m'][0])
        assert np.array_equal(mesh['north_m'][rock], points['utm_northing_m'][selected]-manifest['origin_utm_m'][1])
        assert np.max(abs(mesh['z_m'][rock]+manifest['vertical_origin_navd88_m']-points['navd88_m'][selected])) < 3e-5
        assert np.all(points['height_above_flattened_surface_m'][selected] > .3)
