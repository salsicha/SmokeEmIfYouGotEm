"""Keep historical-mask diagnostics distinct from present-flow acceptance."""
import numpy as np
import pytest

from inspect_cartesian_inundation import inundation, internal_flux_error


def fields():
    return dict(bed=np.zeros(4), surface=np.ones(4),
                source_water=np.array([1, 0, 1, 0]),
                initial_depth=np.array([1., 0., 1., 0.]),
                depth=np.array([2., .5, 0., 9.]),
                selected=np.array([True, True, True, False]), area=2.)


def test_selected_volume_new_wet_and_historical_mask_are_separate():
    result = inundation(**fields())
    assert result['cells'] == 3
    assert result['area_m2'] == 6.
    assert result['volume_m3'] == 5.
    assert result['wet_area_m2'] == 4.
    assert result['initially_zero_depth_now_wet_area_m2'] == 2.
    assert result['initially_zero_depth_now_wet_volume_m3'] == 1.
    assert result['outside_source_water_mask_wet_area_m2'] == 2.
    assert result['outside_source_water_mask_wet_volume_m3'] == 1.
    assert result['maximum_outside_source_water_mask_depth_m'] == .5
    assert result['common_source_water_wet_cells'] == 1
    assert result['common_source_water_stage_minus_captured_p10_p50_p90_m'] == [1., 1., 1.]


def test_dry_selection_has_no_stage_percentiles():
    args = fields()
    args['depth'] = np.zeros(4)
    result = inundation(**args)
    assert result['wet_area_m2'] == 0.
    assert result['maximum_outside_source_water_mask_depth_m'] == 0.
    assert result['common_source_water_stage_minus_captured_p10_p50_p90_m'] == []


@pytest.mark.parametrize('key,value,message', [
    ('bed', [0., 0.], 'Mismatched'),
    ('surface', [0., np.nan, 0., 0.], 'Nonfinite'),
    ('depth', [-1., 0., 0., 0.], 'Negative'),
    ('initial_depth', [0., -1., 0., 0.], 'Negative'),
    ('source_water', [0, 2, 0, 0], 'Nonbinary'),
    ('selected', [False] * 4, 'nonempty'),
    ('area', 0., 'Positive'),
    ('area', float('nan'), 'Positive'),
])
def test_invalid_cell_inputs_fail_closed(key, value, message):
    args = fields()
    args[key] = value
    with pytest.raises(ValueError, match=message):
        inundation(**args)


def grid(x, y):
    return dict(nx=4, ny=4, dx=1., dy=1., origin_x=x, origin_y=y)


@pytest.mark.parametrize('offset,faces', [
    ((4., 0.), (1, 0)), ((-4., 0.), (0, 1)),
    ((0., 4.), (3, 2)), ((0., -4.), (2, 3)),
])
def test_adjacent_inward_fluxes_cancel_in_all_directions(offset, faces):
    a, b = [0.] * 4, [0.] * 4
    a[faces[0]], b[faces[1]] = 7., -7.
    rows = [dict(tile_index=0, inward_flux_m3s=a), dict(tile_index=1, inward_flux_m3s=b)]
    grids = {0: grid(0., 0.), 1: grid(*offset)}
    assert internal_flux_error(rows, grids) == 0.
    b[faces[1]] += .25
    assert internal_flux_error(rows, grids) == .25


def test_nonadjacent_faces_are_not_paired():
    rows = [dict(tile_index=i, inward_flux_m3s=[1.] * 4) for i in range(2)]
    assert internal_flux_error(rows, {0: grid(0., 0.), 1: grid(8., 0.)}) == 0.


def test_repeated_or_nonfinite_native_flux_is_rejected():
    row = dict(tile_index=0, inward_flux_m3s=[0.] * 4)
    with pytest.raises(ValueError, match='Repeated'):
        internal_flux_error([row, row], {0: grid(0., 0.)})
    row['inward_flux_m3s'][0] = float('nan')
    with pytest.raises(ValueError, match='Invalid native flux'):
        internal_flux_error([row], {0: grid(0., 0.)})
