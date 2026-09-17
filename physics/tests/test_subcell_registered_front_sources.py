from dataclasses import replace
from fractions import Fraction as F

import numpy as np
import pytest

from subcell_exact_geometry import clip
from subcell_inlet_front_ownership import front_ownership, owned_front_transfers
from subcell_inlet_sweep_geometry import InletSweep
from subcell_registered_front_sources import RegisteredFrontSources
from test_triangle_face_section import sampler


def fixture():
    source = sampler(lambda x,y:10-5*x+y)
    sweep = InletSweep(((0,0,10),(0,1,11)),(2,F(1,5)),1,F(1,4))
    return source,sweep


@pytest.mark.parametrize('velocity',[(2,F(1,5)),(-2,F(1,5)),(F(1,5),2),(F(1,5),-2)])
def test_complete_mesh_search_matches_all_original_faces(velocity):
    source,sweep = fixture()
    edge=((0,0,10),(-1,0,15)) if abs(velocity[0])<1 else sweep.edge
    sweep=replace(sweep,edge=edge,velocity=velocity)
    index=RegisteredFrontSources(source)
    all_faces={i:index._fragment(i) for i in range(len(source.faces))}
    assert front_ownership(sweep,index.fragments(sweep))==front_ownership(sweep,all_faces)
    result=owned_front_transfers(sweep,index.fragments(sweep))
    assert result['complete_original_source_ownership']
    assert not result['coupled_time_or_energy_or_native_or_gameplay_accepted']


def test_source_beyond_audit_block_is_recovered_without_clamping():
    source,_=fixture()
    sweep=InletSweep(((0,0,10),(0,1,11)),(-F(1,10**8),F(1,4)),1,F(1,10**18))
    index=RegisteredFrontSources(source)
    whole=index.fragments(sweep)
    inside={i:replace(f,polygon=clip(f.polygon,0,F(0),True)) for i,f in whole.items()}
    inside={i:f for i,f in inside.items() if f.area>0}
    missing=owned_front_transfers(sweep,inside)
    assert not missing['complete_original_source_ownership']
    assert missing['transfers'][0]['common_rate_bounds'] is None
    recovered=owned_front_transfers(sweep,whole)
    assert recovered['complete_original_source_ownership']
    assert recovered['transfers'][0]['common_rate_bounds'][0][0]>0
    # The front remains outside the block; recovery changes only source scope.
    assert sweep.point(sweep.time_root/2,0)[0][0]<0


def test_subfloat_positive_ray_is_retained_at_shared_source_vertex():
    source,_=fixture()
    sweep=InletSweep(((0,0,10),(0,1,11)),(-F(1,10**126),F(2,10**126)),1,F(1,10**255))
    index=RegisteredFrontSources(source)
    row,=owned_front_transfers(sweep,index.fragments(sweep))['transfers']
    assert row['wet_source'] is not None and row['dry_source'] is not None
    assert row['common_rate_bounds'][0][0]>0
    assert float(row['common_rate_bounds'][0][0])==0


def test_no_terrain_extrapolation_outside_registered_mesh():
    source,sweep=fixture()
    sweep=replace(sweep,edge=tuple((x+10,y,z) for x,y,z in sweep.edge))
    candidates=RegisteredFrontSources(source).fragments(sweep)
    assert candidates=={}
    result=owned_front_transfers(sweep,candidates)
    assert not result['complete_original_source_ownership']
    assert result['transfers'][0]['status']=='missing-both-original-bed-traces'


def test_original_vertices_and_gradient_are_exact_not_sampled_heights():
    source,sweep=fixture()
    original_xyz,original_faces=source.xyz.copy(),source.faces.copy()
    for i,fragment in RegisteredFrontSources(source).fragments(sweep).items():
        assert fragment.source_id==i
        assert fragment.polygon==tuple(tuple(F(float(v)) for v in p) for p in source.xyz[source.faces[i]])
        assert fragment.gradient==(F(-5),F(1))
    np.testing.assert_array_equal(source.xyz,original_xyz)
    np.testing.assert_array_equal(source.faces,original_faces)


def test_index_owns_one_immutable_geometry_epoch():
    source,sweep=fixture()
    index=RegisteredFrontSources(source)
    before=index.fragments(sweep)
    source.xyz[:]=0
    source.faces[:]=0
    assert index.fragments(sweep)==before
    assert all(f.area>0 for f in before.values())


def test_unvalidated_source_and_unrepresentable_search_reject():
    with pytest.raises(ValueError,match='Validated original'):
        RegisteredFrontSources(object())
    source,sweep=fixture()
    huge=F(10**400)
    sweep=replace(sweep,edge=tuple((x+huge,y,z) for x,y,z in sweep.edge))
    with pytest.raises(ValueError,match='represented mesh-search range'):
        RegisteredFrontSources(source).fragments(sweep)


def test_longer_front_retains_every_crossed_source_pair():
    source,_=fixture()
    sweep=InletSweep(((-1,0,15),(-1,1,16)),(20,0),1,F(1,2))
    index=RegisteredFrontSources(source)
    all_faces={i:index._fragment(i) for i in range(len(source.faces))}
    candidates=index.fragments(sweep)
    assert front_ownership(sweep,candidates)==front_ownership(sweep,all_faces)
    result=owned_front_transfers(sweep,candidates)
    assert result['complete_original_source_ownership']
    assert len(result['transfers'])==5
    assert all(row['wet_source']!=row['dry_source'] for row in result['transfers'])
    assert len({row['wet_source'] for row in result['transfers']})==5
    assert result['transfers'][0]['entry_time_interval'][0]==0
    assert result['transfers'][-1]['entry_time_interval'][1]==sweep.time_root**3
