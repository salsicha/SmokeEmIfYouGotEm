import pytest
from audit_foam_flow_pair import summarize


def fixture():
    return dict(schema='raftsim.foam_flow_pair.v1', paired_frame_valid=True,
        game_frame=220, detail_sequence=100, world_seconds=12., simulation_seconds=10.,
        vertices=1, opposed_vertices=1, coverage_above_point_one=1,
        maximum_difference_mps=5., rms_difference_mps=5., samples=[dict(vertex=5,
            x_m=-5439., y_m=3606., mean_u_mps=2., mean_v_mps=0.,
            optical_u_mps=-3., optical_v_mps=0., depth_m=1., coverage=.4, difference_mps=5.)])


def test_actual_opposition_is_reported_without_acceptance_claim():
    result = summarize(fixture())
    assert result['groups']['coverage_above_point_one']['opposed'] == 1
    assert not result['visual_accepted'] and not result['physical_accepted']


@pytest.mark.parametrize('key,value', [('coverage', 1.1), ('depth_m', 0), ('mean_u_mps', float('nan')),
    ('difference_mps', 4.), ('vertex', -1), ('optical_v_mps', True)])
def test_invalid_sample_rejects(key, value):
    data = fixture(); data['samples'][0][key] = value
    with pytest.raises(ValueError):
        summarize(data)


@pytest.mark.parametrize('key,value', [('vertices', 2), ('paired_frame_valid', 1), ('opposed_vertices', 0),
    ('maximum_difference_mps', 4.), ('detail_sequence', 0), ('world_seconds', float('inf'))])
def test_incomplete_or_inconsistent_report_rejects(key, value):
    data = fixture(); data[key] = value
    with pytest.raises(ValueError):
        summarize(data)
