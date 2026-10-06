import copy
import json

import numpy as np
import pytest

from prepare_troublemaker_control_ablation import original_prior_surfaces
from recover_constriction_source_candidate import recover, reconstruct_added_flanks
from south_fork_mesh_sampling import grid_triangles
from south_fork_source_supported_revision import (
    SourceSupportedTerrainRevision, load_source_revision, source_change_bounds, verify_extension,
)
from south_fork_terrain_revision import RegisteredTerrainRevision
from south_fork_registered_mesh import RegisteredMeshSampler


def fixture():
    axis = np.arange(-3.5, 4., .5)
    x, y = np.meshgrid(axis, axis[::-1])
    a = np.full(x.shape, 2, np.uint8)
    a[7, 7] = 3
    original = dict(east_m=x, north_m=y, z_m=np.zeros(x.shape, np.float32),
                    source_surface_m=np.full(x.shape, 3., np.float32), authority=a,
                    nominal_east_axis_m=axis, nominal_north_axis_m=axis[::-1],
                    triangles=grid_triangles(*x.shape), rock_source_return_index=np.array([0], dtype=np.int64))
    baseline, controlled = original_prior_surfaces(original)
    original['z_m'] = controlled
    original['z_m'][7, 7] = 4.
    installed = {k: v.copy() for k, v in original.items()}
    interior = a == 2
    interior[[0, -1], :] = False
    interior[:, [0, -1]] = False
    installed['z_m'][interior] = baseline[interior]
    origin = np.array([100., 200., 220.])
    xyz = np.array([[0., 0., 4.], [.55, 0., 4.1], [.51, .02, 4.2]])+origin
    returns = dict(utm_easting_m=xyz[:, 0], utm_northing_m=xyz[:, 1], navd88_m=xyz[:, 2],
                   classification=np.ones(3, np.uint8), within_survey_water=np.ones(3, bool),
                   height_above_flattened_surface_m=xyz[:, 2]-223.)
    selection = dict(measured_outline=False, measured_flanks=False, source_xyz_may_be_moved=False,
                     source_classifications_may_be_changed=False, origin_utm_and_vertical_datum_m=origin.tolist(),
                     interpreted_selection_polygon_m=[[-.1, -.6], [1.1, -.6], [1.1, .6], [-.1, .6]])
    candidate, added, _, _ = recover(installed, returns, selection)
    candidate, _ = reconstruct_added_flanks(candidate, added, baseline)
    return original, installed, candidate, returns, selection


def test_exact_source_extension_and_composed_sampling():
    original, installed, candidate, returns, selection = fixture()
    proof = verify_extension(installed, candidate, returns, selection, original)
    assert proof['added_captured_vertices'] == 1
    assert proof['minimum_source_bin_count'] == 2
    bed = RegisteredTerrainRevision(original, installed, [100, 200], 220)
    revision = SourceSupportedTerrainRevision(bed, candidate, [100, 200], 220)
    x = np.array([100.2, 100.55, 103.5, 150.])
    y = np.array([200., 200., 203.5, 200.])
    parent = np.r_[bed.original.sample(x[:3]-100, y[:3]-200)+220, 999.]
    out, _ = revision.apply(x, y, parent)
    np.testing.assert_array_equal(out[:3], revision.revised.sample(x[:3]-100, y[:3]-200)+220)
    assert out[-1] == 999.
    # Existing strict bed-only validator STILL refuses these XY/authority edits.
    with pytest.raises(ValueError, match='protected'):
        RegisteredTerrainRevision(installed, candidate, [100, 200], 220)


@pytest.mark.parametrize('key,index', [('east_m', (7, 8)), ('z_m', (7, 7)), ('z_m', (6, 8)), ('authority', (6, 8))])
def test_rehashed_source_or_inference_tamper_is_not_accepted(key, index):
    original, installed, candidate, returns, selection = fixture()
    candidate[key][index] += 1
    with pytest.raises(ValueError, match='source-exact'):
        verify_extension(installed, candidate, returns, selection, original)


def test_changed_source_label_and_claimed_measurement_rejected():
    original, installed, candidate, returns, selection = fixture()
    relabelled = copy.deepcopy(returns)
    relabelled['classification'][1] = 7
    with pytest.raises(ValueError):
        verify_extension(installed, candidate, relabelled, selection, original)
    selection['measured_outline'] = True
    with pytest.raises(ValueError, match='interpreted'):
        verify_extension(installed, candidate, returns, selection, original)


def test_old_evolved_bed_input_and_wrong_frame_rejected():
    original, installed, candidate, _, _ = fixture()
    bed = RegisteredTerrainRevision(original, installed, [100, 200], 220)
    revision = SourceSupportedTerrainRevision(bed, candidate, [100, 200], 220)
    with pytest.raises(ValueError, match='exact retained'):
        revision.apply([100.55], [200.], [224.1])
    with pytest.raises(ValueError, match='frame'):
        SourceSupportedTerrainRevision(bed, candidate, [101, 200], 220)


def test_bounds_include_moved_xy_and_empty_revision_rejected():
    original, _, candidate, _, _ = fixture()
    a, b = RegisteredMeshSampler(original), RegisteredMeshSampler(candidate)
    low, high, count = source_change_bounds(a, b, np.array([100, 200]))
    assert count > 1 and low[0] <= 100.55 <= high[0]
    with pytest.raises(ValueError, match='Empty'):
        source_change_bounds(a, a, np.array([100, 200]))


@pytest.mark.parametrize('key', ['state_transfer_permitted', 'production_promoted'])
def test_manifest_cannot_authorize_evolved_state_or_promotion(tmp_path, key):
    record = dict(schema='raftsim.source_supported_terrain_revision.v1', state_transfer_permitted=False, production_promoted=False)
    record[key] = True
    path = tmp_path/'manifest.json'
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError, match='fresh-state'):
        load_source_revision(path, tmp_path, tmp_path/'old.npz', [100, 200], 220)


def test_dependency_cannot_escape_root(tmp_path):
    record = dict(schema='raftsim.source_supported_terrain_revision.v1', state_transfer_permitted=False, production_promoted=False,
                  bed_revision=dict(path='../outside.json', sha256='not-a-real-hash'))
    path = tmp_path/'manifest.json'
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError, match='escaped project'):
        load_source_revision(path, tmp_path, tmp_path/'old.npz', [100, 200], 220)
