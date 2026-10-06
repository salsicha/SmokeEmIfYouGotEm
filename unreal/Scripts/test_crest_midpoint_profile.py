import pytest
from audit_crest_midpoint_profile import audit


def row(frame,serial=2.,parallel=.8):
    return f'CrestMidpointAudit exact frame={frame} vertices=200 midpoints=100 bands=3 serial_ms={serial} parallel_ms={parallel} parallel_first={frame%2}'


def test_all_requested_frames_and_repeated_calls_retained():
    result=audit('\n'.join([row(120),row(121),row(121,3.,1.)]),120,121)
    assert result['calls']==3 and result['frames']==2
    assert result['exact_vertex_attribute_sets']==600
    assert result['per_frame']['serial_ms']['maximum']==5.
    assert result['call_order_benefit_ms']['0']['count']==1
    assert result['call_order_benefit_ms']['1']['count']==2
    assert not result['ordinary_game_fps_accepted']


@pytest.mark.parametrize('log',[
    row(120),row(120)+'\n'+row(121)+'\nCrestMidpointAudit mismatch frame=130',
    row(120)+'\n'+row(121).replace('parallel_first=1','parallel_first=0'),
    row(120)+'\n'+row(121).replace('parallel_ms=0.8','parallel_ms=nan'),
    row(120)+'\n'+row(121).replace('bands=3','bands=0'),
    row(120)+'\n'+row(121).replace('vertices=200','vertices=10'),
    row(120)+'\nCrestMidpointAudit exact incomplete',
])
def test_incomplete_mismatched_or_invalid_actual_evidence_rejected(log):
    with pytest.raises(ValueError):audit(log,120,121)


def test_no_work_cannot_be_called_a_speed_win():
    log='\n'.join(row(f).replace('midpoints=100 bands=3','midpoints=0 bands=0') for f in (120,121))
    with pytest.raises(ValueError):audit(log,120,121)
