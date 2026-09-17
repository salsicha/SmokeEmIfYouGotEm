from dataclasses import replace
from fractions import Fraction as F

import pytest

from subcell_exact_geometry import SourceFragment
from subcell_inlet_sweep_geometry import InletSweep
from subcell_front_initial_support import initial_front_support, require_initially_dry_front, initially_dry_front_transfers


def fixture():
    # Front x=2*(1/64-tau), y=0, bed=10-5*x. Both sides lie in this source.
    sweep = InletSweep(((0,0,10),(0,1,11)), (2,0), 1, F(1,4))
    fragment = SourceFragment(7, ((-1,-1,14),(1,-1,4),(1,1,6),(-1,1,16)), (-5,1))
    return sweep, {7:fragment}


def test_exact_shoreline_partitions_same_pool_into_dry_and_wet_traces():
    sweep, fragments = fixture()
    states = {7:dict(pool_id=3, datum=10, stage_offset=-F(5,64))}
    r = initial_front_support(sweep, fragments, states)
    a,b = r['segments']
    assert a['entry_time_interval'] == (0,F(1,128))
    assert b['entry_time_interval'] == (F(1,128),F(1,64))
    assert a['wet_source']['status'] == a['dry_source']['status'] == 'positive-depth'
    assert b['wet_source']['status'] == b['dry_source']['status'] == 'initially-dry'
    assert a['wet_source']['depth_endpoints'] == (F(5,64),0)
    assert r['complete_initial_state'] and r['positive_initial_depth_present']
    with pytest.raises(ValueError,match='known initially dry'):
        require_initially_dry_front(r)
    assert not r['evolving_front_or_flux_or_time_accepted']


def test_missing_is_not_dry_and_pool_membership_is_not_wet_depth():
    sweep,fragments = fixture()
    unknown = initial_front_support(sweep,fragments,{})
    assert not unknown['complete_initial_state']
    with pytest.raises(ValueError): require_initially_dry_front(unknown)
    for state in (None,dict(pool_id=3,datum=0,stage_offset=1)):
        r = initial_front_support(sweep,fragments,{7:state})
        assert r['complete_initial_state'] and not r['positive_initial_depth_present']
        require_initially_dry_front(r)


def test_positive_subfloat_interval_and_large_datum_are_not_rounded_away():
    sweep,fragments = fixture()
    tiny = F(1,10**400)
    # Wet only in tau < tiny. Stage remains exact, despite an unrepresentable width.
    r = initial_front_support(sweep,fragments,{7:dict(pool_id=1,datum=10,
                                                   stage_offset=-F(5,32)+10*tiny)})
    assert r['segments'][0]['entry_time_interval'] == (0,tiny)
    assert r['positive_initial_depth_present']
    dz = F(10**30)
    moved = {k:replace(f,polygon=tuple((x,y,z+dz) for x,y,z in f.polygon)) for k,f in fragments.items()}
    other = replace(sweep,edge=tuple((x,y,z+dz) for x,y,z in sweep.edge))
    r2 = initial_front_support(other,moved,{7:dict(pool_id=1,datum=10+dz,
                                                stage_offset=-F(5,32)+10*tiny)})
    assert [v['entry_time_interval'] for v in r2['segments']] == [v['entry_time_interval'] for v in r['segments']]
    assert r2['segments'][0]['wet_source']['depth_endpoints'] == r['segments'][0]['wet_source']['depth_endpoints']


def test_two_different_source_traces_retain_independent_pool_states():
    sweep,_ = fixture()
    fragments = {
        1:SourceFragment(1,((-1,0,15),(1,0,5),(1,1,6),(-1,1,16)),(-5,1)),
        2:SourceFragment(2,((-1,-1,14),(1,-1,4),(1,0,5),(-1,0,15)),(-5,1))}
    r = initial_front_support(sweep,fragments,{1:None,2:dict(pool_id=9,datum=0,stage_offset=20)})
    a, = r['segments']
    assert a['wet_source']['source'] == 1 and a['wet_source']['status'] == 'initially-dry'
    assert a['dry_source']['source'] == 2 and a['dry_source']['pool_id'] == 9
    assert a['dry_source']['status'] == 'positive-depth'
    with pytest.raises(ValueError): require_initially_dry_front(r)


def test_entire_zero_depth_trace_is_retained_without_epsilon():
    sweep, fragments = fixture()
    sweep=replace(sweep,edge=((0,0,10),(0,1,11)),velocity=(2,0))
    flat=SourceFragment(7,tuple((x,y,10+y) for x,y,z in fragments[7].polygon),(0,1))
    r=initial_front_support(sweep,{7:flat},{7:dict(pool_id=1,datum=10,stage_offset=0)})
    assert r['segments'][0]['wet_source']['status'] == 'zero-depth-trace'
    require_initially_dry_front(r)


@pytest.mark.parametrize('state',[dict(pool_id=1,datum=0,stage_offset=float('nan')),
                                 dict(pool_id=1,datum=float('inf'),stage_offset=0),
                                 dict(pool_id=None,datum=0,stage_offset=0),{}])
def test_invalid_states_reject(state):
    sweep,fragments=fixture()
    with pytest.raises(ValueError): initial_front_support(sweep,fragments,{7:state})


def test_unknown_source_state_is_not_attached_to_another_triangle():
    sweep,fragments=fixture()
    with pytest.raises(ValueError): initial_front_support(sweep,fragments,{9:None})


def test_conditional_flux_entry_requires_known_dry_support_and_preserves_common_rates():
    from subcell_inlet_front_ownership import owned_front_transfers
    sweep,fragments=fixture()
    reference=owned_front_transfers(sweep,fragments)
    candidate=initially_dry_front_transfers(sweep,fragments,{7:None})
    assert candidate['transfers'] == reference['transfers']
    assert candidate['initial_dry_support_verified']
    for states in ({},{7:dict(pool_id=1,datum=0,stage_offset=20)}):
        with pytest.raises(ValueError): initially_dry_front_transfers(sweep,fragments,states)


@pytest.mark.parametrize('shape,col,row', [((0,4),0,0),((4,17),0,0),((4,4),13,0),
                                        ((16,16),1,0),((4.,4),0,0)])
def test_expanded_source_loader_rejects_outside_recorded_patch_before_io(shape,col,row):
    from types import SimpleNamespace
    from audit_south_fork_nonlinear_source_block import load_original_block
    with pytest.raises(ValueError,match='inside the 16x16'):
        load_original_block(SimpleNamespace(block_col=col,block_row=row),shape)
