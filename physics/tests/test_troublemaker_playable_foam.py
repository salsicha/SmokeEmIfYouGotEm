"""Guard normal-playable optics and actual runtime geographic-frame callsites."""
from pathlib import Path
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'physics/tests'))
from test_south_fork_transported_foam_optics import response


def test_captured_foam_shader_has_no_independent_generation_or_motion():
    code=(ROOT/'unreal/Shaders/Private/RaftSimCapturedFoamOptics.hlsl').read_text()
    body='\n'.join(line.split('//')[0] for line in code.splitlines())
    assert 'saturate(TransportedFoam)' in body
    assert 'fwidth(Lace)' in body
    assert '1.0 - exp(-max(OpticalDensity, 0.0) * amount)' in body
    assert not any(token in body for token in ('Speed','Depth','Time','WorldPosition','sin(','cos('))
    for lace in np.linspace(0,1,101):
        assert response(0,float(lace))==0
        assert response(.8,float(lace),0)==0


def test_captured_foam_optics_are_continuous_and_bounded():
    for footprint in (.04,.2,1):
        for lace in np.linspace(0,1,21):
            values=np.array([response(float(f),float(lace),footprint=footprint) for f in np.linspace(0,1,1001)])
            assert np.all((values>=0)&(values<=1))
            assert np.all(np.diff(values)>=-1e-12)
            assert np.max(np.diff(values))<.03


def test_normal_playable_foam_keeps_physical_outputs_and_scopes_asset():
    script=(ROOT/'unreal/Scripts/configure_playable_troublemaker_foam.py').read_text()
    assert "PATH='/Game/RaftSim/Environment/SouthForkReconstruction/Troublemaker/M_TroublemakerWater'" in script
    assert "('OPACITY','NORMAL','WORLD_POSITION_OFFSET')" in script
    assert "assert before==after" in script
    assert "(vertex,'R','TransportedFoam')" in script
    assert "zero.set_editor_property('r',0.0)" in script
    assert "('BASE_COLOR',water,parameter('WhitewaterFrothColor'))" in script
    assert "('ROUGHNESS',parameter('LiveWaterRoughness')" in script
    assert "('SPECULAR',parameter('LiveWaterSpecular')" in script


def test_actual_foam_and_normal_callsites_use_geographic_frame():
    source=(ROOT/'unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimWaterSurfaceActor.cpp').read_text()
    transport=source.split('// --- Persistent advected foam',1)[1].split('FoamField = MoveTemp',1)[0]
    assert 'RaftSimFoamTransport::ProjectWorldVelocity(' in transport
    assert 'WaterAdapter->GetRiverWorldYSign()' in transport
    assert 'const FVector2D Left2D(-FlowTangent.Y, FlowTangent.X)' not in transport
    assert 'RaftSimFoamTransport::TransformSurfaceNormal(' in source
    assert 'FProcMeshTangent(FlowTangent, WaterAdapter && WaterAdapter->GetRiverWorldYSign() < 0)' in source


def test_reflected_velocity_reverses_neither_station_nor_source_left():
    tangent=np.array([-.93,.36756]);tangent/=np.linalg.norm(tangent)
    left=np.array([-tangent[1],tangent[0]])
    velocity=2.2*tangent+.85*left
    for sign in (1,-1):
        reflection=np.array([1,sign])
        world_tangent=tangent*reflection
        world_velocity=velocity*reflection
        world_left=np.array([-world_tangent[1],world_tangent[0]])*sign
        assert np.allclose([world_velocity@world_tangent,world_velocity@world_left],[2.2,.85])
    # Demonstrate the previous expression is rejected, not just recompute itself.
    world_tangent=tangent*np.array([1,-1]);world_velocity=velocity*np.array([1,-1])
    old_left=np.array([-world_tangent[1],world_tangent[0]])
    assert world_velocity@old_left < 0
