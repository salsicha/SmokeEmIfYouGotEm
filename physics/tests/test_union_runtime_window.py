import numpy as np
import pytest
from prepare_south_fork_union_runtime import choose_window


def windows():
    return {'windows':[{'cooked_fields_manifest':'b','valid_live_center_bounds_m':[[-100,-100,100,100]]},
                       {'cooked_fields_manifest':'a','valid_live_center_bounds_m':[[-100,-100,100,100]]}]}


def test_default_midpoint_and_deterministic_packet():
    manifest,center=choose_window(windows(),[[-80,0],[80,80]])
    assert manifest=='a'
    np.testing.assert_array_equal(center,[0,40])


def test_same_center_keeps_all_queries_and_four_cell_margin():
    manifest,center=choose_window(windows(),[[-80,0],[80,80]],[0,0])
    assert manifest=='a'
    np.testing.assert_array_equal(center,[0,0])


@pytest.mark.parametrize('center',[[29,0],[0,-29],[101,0],[np.nan,0],[0],[0,0,0]])
def test_requested_center_is_never_clamped_or_relaxed(center):
    with pytest.raises(ValueError):choose_window(windows(),[[-80,0],[80,80]],center)


def test_disjoint_window_is_not_bridged():
    stream={'windows':[{'cooked_fields_manifest':'a','valid_live_center_bounds_m':[[-100,-100,-10,100],[10,-100,100,100]]}]}
    with pytest.raises(ValueError):choose_window(stream,[[-80,0],[80,80]],[0,0])


@pytest.mark.parametrize('points',[[],[[0,float('inf')]],[[0,0,0]],[[-200,0],[200,0]]])
def test_invalid_or_too_wide_query_sets_rejected(points):
    with pytest.raises(ValueError):choose_window(windows(),points)
