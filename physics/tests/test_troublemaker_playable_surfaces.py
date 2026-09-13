"""Normal-game crest, transported froth and registered terrain color contracts."""
import json
from pathlib import Path
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]

def test_refinement_is_normal_playable_and_not_a_solver_experiment():
    code=(ROOT/'unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimWaterSurfaceActor.cpp').read_text()
    assert 'bPlayableCrestRefinement = bPlayableCapturedSouthFork;' in code
    assert 'if (!bStatefulDetailGeometryReview && !bPlayableCrestRefinement)' in code
    assert 'RaftSimPlayableCrestMesh::Reconstruct(' in code
    assert 'T=(T-N*FVector::DotProduct(T,N)).GetSafeNormal();' in code
    helper=(ROOT/'unreal/Plugins/RaftSim/Source/RaftSimRaft/Public/RaftSimPlayableCrestMesh.h').read_text()
    assert 'const float Correction=Crest-InterpolatedCrest[I]' in helper
    assert 'Positions[I].Z += Correction' in helper
    assert 'I = Refinement.SourceVertexCount' in helper
    assert 'SampleWater' not in helper

def test_froth_normal_has_no_new_source_geometry_or_animation():
    code=(ROOT/'unreal/Shaders/Private/RaftSimCapturedFrothNormal.hlsl').read_text()
    body='\n'.join(line.split('//')[0] for line in code.splitlines())
    assert 'saturate(Foam) * saturate(Lace)' in body
    assert '*saturate(Foam)' in body
    assert 'ddx(height)' in body and 'ddy(height)' in body
    assert '0.65/max(length(gradient),1.e-5)' in body
    assert not any(s in body for s in ('Time','Speed','Depth','sin(','cos(','WorldPositionOffset'))

def test_froth_normal_zero_and_slope_bound():
    for foam in (0,.1,.5,1):
        for gradient in (np.zeros(3),np.array([1,2,0]),np.array([1e6,0,0])):
            bounded=gradient*min(1,.65/max(np.linalg.norm(gradient),1e-5))*foam
            assert np.linalg.norm(bounded)<=.650000001
            if foam==0:assert np.array_equal(bounded,np.zeros(3))

def test_authority_texture_does_not_drape_inferred_bed():
    folder=ROOT/'unreal/SourceArt/RaftSim/TroublemakerSurfaceAuthority'
    mask=np.asarray(Image.open(folder/'T_TroublemakerSurfaceAuthority.png'))
    with np.load(ROOT/'tmp/south-fork-rock-return-xy-candidate-v2-20260907/registered_mesh_source.npz') as d:
        authority=d['authority']
        assert not np.any(mask[:,:,0][authority!=1])
        assert np.array_equal(mask[:,:,1]>0,authority==3)
    assert not np.any(mask[[0,-1],:,0])
    assert not np.any(mask[:,[0,-1],0])

def test_registered_texture_frame_matches_reflected_world():
    data=json.loads((ROOT/'unreal/SourceArt/RaftSim/TroublemakerSurfaceAuthority/manifest.json').read_text())
    left,bottom,right,top=data['local_bounds_m']
    for east,north,expected in ((left,top,[0,0]),(right,bottom,[1,1]),((left+right)/2,(top+bottom)/2,[.5,.5])):
        world=np.array([east,-north])*100
        actual=[(world[0]*.01-left)/(right-left),(world[1]*.01+top)/(top-bottom)]
        assert np.allclose(actual,expected,atol=1e-12)

def test_ground_integration_preserves_geometry_and_original_pbr():
    code=(ROOT/'unreal/Scripts/integrate_troublemaker_surface_color.py').read_text()
    assert "('NORMAL','ROUGHNESS','WORLD_POSITION_OFFSET')" in code
    assert 'assert sha(ROOT/name)==digest' in code
    assert "'instance_backup':str(backup)" in code
    assert "assert {k:graph_signature(ground,p) for k,p in props.items()}==before" in code
