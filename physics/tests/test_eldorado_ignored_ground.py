"""Class 20 is ignored ground in the Eldorado source; it is not class 10.

Eligibility must still obey geometric/support gates and never relabel a return.
"""
import numpy as np
import pytest
from build_troublemaker_dem_rock_cap import select_lower_returns
from audit_cap_boundary_lower_bins import lower_bin_witnesses
from audit_downstream_cap_returns import neighbour_evidence


@pytest.mark.parametrize('classification,accepted', [(1, True), (2, True),
    (20, True), (10, False), (7, False), (9, False), (17, False), (18, False)])
def test_cap_selection_respects_actual_survey_class(classification, accepted):
    xyz = np.array([[.1, .1, 1.], [.2, .1, 1.1]])
    classes = np.full(2, classification)
    polygon = [[0, 0], [1, 0], [1, 1], [0, 1]]
    ids, support = select_lower_returns(xyz, classes, np.ones(2), polygon)
    assert ids.tolist() == ([0] if accepted else [])
    assert support.tolist() == ([2] if accepted else [])
    np.testing.assert_array_equal(classes, [classification, classification])


def test_ignored_ground_does_not_bypass_clearance_region_or_support():
    xyz = np.array([[.1, .1, 1.], [.2, .1, 1.1], [5., 5., 1.]])
    polygon = [[0, 0], [1, 0], [1, 1], [0, 1]]
    for heights in ([.3, .3, 1.], [1., .1, 1.]):
        ids, _ = select_lower_returns(xyz, np.full(3, 20), heights, polygon)
        assert not len(ids)


def test_lower_witnesses_use_ignored_ground_not_class_ten():
    xyz = np.array([[.1, .1, 0.], [.1, .1, 1.], [.1, .1, 3.]])
    classes = np.array([10, 20, 1])
    rows = lower_bin_witnesses(xyz[2:], xyz, classes, np.ones(3))
    assert len(rows) == 1
    assert rows[0]['source_index'] == 1
    assert rows[0]['classification'] == 20
    rows = neighbour_evidence(xyz[2:], [2], xyz, classes)
    assert rows[0]['lowest_original_id'] == 1
    assert rows[0]['nearby_original_count'] == 2
