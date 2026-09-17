from dataclasses import replace
from fractions import Fraction as F

import pytest

from subcell_exact_geometry import SourceFragment, clip
from subcell_inlet_front_ownership import front_ownership, owned_front_transfers
from subcell_inlet_lateral_flux import lateral_flux
from subcell_inlet_lateral_energy import lateral_energy_flux
from subcell_inlet_sweep_geometry import InletSweep
from test_subcell_inlet_sweep_geometry import fixture


def shared():
    sweep,receiver = fixture()
    sweep = replace(sweep,velocity=(2,F(1,5)))
    corner = (F(20,11),F(2,11),F(12,11))
    wet = replace(receiver,polygon=(receiver.polygon[0],corner,receiver.polygon[2]))
    dry = replace(receiver,source_id=18,polygon=(receiver.polygon[0],receiver.polygon[1],corner))
    return sweep,receiver,{'wet':wet,'dry':dry}


def test_duplicate_closed_queries_become_one_common_transfer():
    sweep,receiver,parts = shared()
    result = owned_front_transfers(sweep,parts)
    assert result['complete_original_source_ownership']
    row, = result['transfers']
    assert row['wet_source']=='wet' and row['dry_source']=='dry'
    whole = (*lateral_flux(sweep,receiver)['outward_volume_momentum_rate_bounds'],
             lateral_energy_flux(sweep,receiver)['outward_energy_rate_per_density_bounds'])
    assert row['common_rate_bounds']==whole
    assert row['debit']['transfer_id']==row['credit']['transfer_id']==row['transfer_id']
    assert row['debit']['sign']==-row['credit']['sign']==-1
    # Both old closed-boundary queries contain that entire flux; do not sum them.
    assert all(lateral_flux(sweep,p)['outward_volume_momentum_rate_bounds']==whole[:3] for p in parts.values())
    assert not result['coupled_time_or_energy_or_native_or_gameplay_accepted']


def test_internal_front_keeps_distinct_domains_inside_same_source():
    sweep,receiver,_ = shared()
    row, = owned_front_transfers(sweep,{17:receiver})['transfers']
    assert row['wet_source']==row['dry_source']==17
    assert row['debit']['domain']!=row['credit']['domain']
    assert row['common_rate_bounds'][0][0]>0


@pytest.mark.parametrize('cut',[F(3,200),F(7,256)])
def test_exact_source_crossings_partition_ray_and_preserve_flux(cut):
    sweep,receiver,parts = shared()
    split = {(key,side):replace(p,polygon=clip(p.polygon,0,cut,side))
             for key,p in parts.items() for side in (False,True)}
    result = owned_front_transfers(sweep,split)
    rows = result['transfers']
    boundary = sweep.time_root**3-cut/sweep.velocity[0]
    assert [r['entry_time_interval'] for r in rows]==[(0,boundary),(boundary,sweep.time_root**3)]
    whole = owned_front_transfers(sweep,parts)['transfers'][0]['common_rate_bounds']
    for j,(a,b) in enumerate(whole):
        low,high = (sum(row['common_rate_bounds'][j][k] for row in rows) for k in (0,1))
        assert low <= b and a <= high
        assert high-low < F(1,10**10)*max(abs(a),abs(b))
    assert result['complete_original_source_ownership']


def test_source_order_winding_rotation_and_large_translation():
    sweep,_,parts = shared()
    before = front_ownership(sweep,parts)
    move = lambda p:(-p[1]+10**12,p[0]-10**12,p[2])
    changed = replace(sweep,edge=tuple(move(p) for p in sweep.edge),velocity=(-sweep.velocity[1],sweep.velocity[0]))
    rotated = {k:replace(p,polygon=tuple(move(q) for q in reversed(p.polygon)),
                        gradient=(-p.gradient[1],p.gradient[0])) for k,p in reversed(list(parts.items()))}
    assert front_ownership(changed,rotated)==before
    mass,x,y,energy = owned_front_transfers(sweep,parts)['transfers'][0]['common_rate_bounds']
    assert owned_front_transfers(changed,rotated)['transfers'][0]['common_rate_bounds']==(mass,(-y[1],-y[0]),x,energy)


def test_missing_owners_are_retained_not_invented_or_accepted():
    sweep,receiver = fixture()
    result = owned_front_transfers(sweep,{17:receiver})
    row, = result['transfers']
    assert row['wet_source']==17 and row['dry_source'] is None
    assert row['status']=='missing-one-original-source'
    assert row['common_rate_bounds'][0][0]>0
    assert not result['complete_original_source_ownership']
    empty = owned_front_transfers(sweep,{})
    row, = empty['transfers']
    assert row['entry_time_interval']==(0,sweep.time_root**3)
    assert row['common_rate_bounds'] is None
    assert row['status']=='missing-both-original-bed-traces'


def test_positive_subfloat_segment_is_not_deleted():
    sweep,receiver = fixture()
    sweep = InletSweep(sweep.edge,(F(1,10**126),0),1,F(1,10**255))
    cut = sweep.velocity[0]*sweep.time_root**3/2
    parts = {side:replace(receiver,polygon=clip(receiver.polygon,0,cut,side)) for side in (False,True)}
    rows = owned_front_transfers(sweep,parts)['transfers']
    assert len(rows)==2
    for row in rows:
        a,b = row['entry_time_interval']
        assert 0 < b-a and float(b-a)==0
        assert row['common_rate_bounds'][0][0]>0
        assert float(row['common_rate_bounds'][0][0])==0


def test_gaps_remain_explicit_in_full_partition():
    sweep,receiver,parts = shared()
    cut = F(1,64)
    selected = {k:replace(p,polygon=clip(p.polygon,0,cut,False)) for k,p in parts.items()}
    rows = owned_front_transfers(sweep,selected)['transfers']
    assert len(rows)==2
    assert rows[0]['status']=='missing-both-original-bed-traces'
    assert rows[1]['status']=='paired-original-sources'
    assert rows[0]['entry_time_interval'][1]==rows[1]['entry_time_interval'][0]


def test_zero_measure_vertex_contact_does_not_claim_a_side():
    sweep,receiver,parts = shared()
    tangent = SourceFragment(90,tuple(tuple(map(F,p)) for p in ((0,0,10),(-1,0,15),(0,-1,9))),receiver.gradient)
    assert front_ownership(sweep,dict(parts,tangent=tangent))==front_ownership(sweep,parts)


def test_collinear_subdivision_and_repeated_vertex_keep_ownership():
    sweep,_,parts = shared()
    wet = parts['wet']
    midpoint = tuple((a+b)/2 for a,b in zip(wet.polygon[0],wet.polygon[1]))
    altered = replace(wet,polygon=(wet.polygon[0],midpoint,midpoint,*wet.polygon[1:]))
    assert front_ownership(sweep,dict(parts,wet=altered))==front_ownership(sweep,parts)


@pytest.mark.parametrize('side',['wet','dry'])
def test_overlapping_sources_rejected_not_resolved_by_key(side):
    sweep,_,parts = shared()
    with pytest.raises(ValueError,match='Overlapping original sources'):
        front_ownership(sweep,dict(parts,duplicate=parts[side]))


def test_shared_bed_jump_and_inconsistent_gradient_rejected():
    sweep,_,parts = shared()
    dry = parts['dry']
    raised = replace(dry,polygon=tuple((x,y,z+1) for x,y,z in dry.polygon))
    with pytest.raises(ValueError,match='bed traces disagree'):
        front_ownership(sweep,dict(parts,dry=raised))
    with pytest.raises(ValueError,match='gradient and vertices disagree'):
        front_ownership(sweep,dict(parts,dry=replace(dry,gradient=(0,0))))
    with pytest.raises(ValueError,match='reserved'):
        front_ownership(sweep,{None:dry})


def test_integration_budget_failure_is_not_hidden_by_ownership():
    sweep,_,parts = shared()
    split = {(key,side):replace(p,polygon=clip(p.polygon,0,F(3,200),side))
             for key,p in parts.items() for side in (False,True)}
    with pytest.raises(ValueError,match='bound unresolved'):
        owned_front_transfers(sweep,split,max_depth=1)


def test_supplied_binary_coordinates_are_converted_before_arithmetic():
    sweep,receiver = fixture()
    exact = front_ownership(sweep,{(3,17):receiver})
    binary = replace(receiver,polygon=tuple(tuple(float(v) for v in p) for p in receiver.polygon),
                     gradient=tuple(float(g) for g in receiver.gradient))
    assert front_ownership(sweep,{(3,17):binary})==exact
    assert all(isinstance(v,F) for row in exact for v in row['entry_time_interval'])


def test_input_sources_remain_unchanged():
    sweep,_,parts = shared()
    before = parts.copy()
    owned_front_transfers(sweep,parts)
    assert parts==before


@pytest.mark.parametrize('polygon',[
    ((0,0,10),(2,0,0),(1,F(1,4),F(21,4)),(2,2,2),(0,2,12)),
    ((-10,-10,50),(-8,-10,40),(-9,F(-39,4),F(181,4)),(-8,-8,42),(-10,-8,52)),
])
def test_concave_sources_reject_even_when_the_ray_is_outside(polygon):
    sweep,receiver = fixture()
    invalid = replace(receiver,polygon=tuple(tuple(map(F,p)) for p in polygon))
    with pytest.raises(ValueError,match='Convex original source'):
        front_ownership(sweep,{17:invalid})
