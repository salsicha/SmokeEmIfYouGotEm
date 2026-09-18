import numpy as np
import pytest
from audit_cap_change_wet_cells import impact
from compare_last_return_cap import stats


def test_even_subdry_positive_films_are_reported_separately():
    result=impact([1,1,1,1],[0,2,3,1],[0,1e-7,.1,5])
    assert result['changed_cells']==3
    assert result['changed_wet_cells']==1
    assert result['changed_positive_depth_cells']==2
    assert result['bed_delta_min_max_m']==[-1,2]


def test_unchanged_bed_has_no_changed_depth_range():
    assert impact([1],[1],[2])['changed_cell_depth_min_max_m'] is None


@pytest.mark.parametrize('old,new,depth',[([1],[1,2],[0]),([1],[float('nan')],[0]),([1],[1],[-1])])
def test_invalid_impact_inputs(old,new,depth):
    with pytest.raises(ValueError):impact(old,new,depth)


def test_cap_statistics_distinguish_actual_roof_area_and_projection():
    cap=dict(vertices_m=np.array([[0,0,0],[1,0,0],[0,1,2.]]),triangles=np.array([[0,1,2]]))
    result,footprint=stats(cap)
    assert result['projected_area_m2']==.5
    assert result['roof_area_above_60_degrees_m2']==pytest.approx(np.sqrt(5)/2)
    assert result['connected_components']==1 and result['interior_holes']==0
