"""Source-contract checks only; native GPU and SM5 reflection are separate gates."""
from pathlib import Path
import re

import pytest

ROOT = Path(__file__).resolve().parents[2]
SHADER = (ROOT / 'unreal/Plugins/RaftSim/Shaders/Private/RaftSimTotalDepthTransport.usf').read_text()
CPP = (ROOT / 'unreal/Plugins/RaftSim/Source/RaftSimWaterDetail/Private/RaftSimTotalDepthTransportGPU.cpp').read_text()
BINDINGS = [
    ('Velocity', 'float2', 0), ('RawX', 'float4', 1), ('RawY', 'float4', 1),
    ('SlopeX', 'float4', 2), ('SlopeY', 'float4', 2), ('Flattened', 'uint', 2),
    ('ShorelineFactors', 'float2', 2), ('FluxX', 'float4', 3), ('FluxY', 'float4', 3),
    ('FoamFlux', 'float2', 3), ('CorrectionX', 'float2', 3), ('CorrectionY', 'float2', 3),
    ('Partial', 'float2', 4),
]


@pytest.mark.parametrize('name,kind,phase', BINDINGS)
def test_intermediate_is_writable_only_in_its_producer(name, kind, phase):
    assert (f'#if RAFTSIM_TRANSPORT_PHASE == {phase}\n'
            f'RWStructuredBuffer<{kind}> {name}Output;\n'
            f'#define {name} {name}Output\n#else\n'
            f'StructuredBuffer<{kind}> {name};\n#endif') in SHADER
    assert f'SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<{kind}>,{name})' in CPP
    assert f'SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<{kind}>,{name}Output)' in CPP
    assert f'Phase!={phase} ? Graph.CreateSRV({name}):nullptr' in CPP
    assert f'Phase=={phase} ? Graph.CreateUAV({name}):nullptr' in CPP


def test_all_intermediate_outputs_are_covered_and_diagnostics_remain_atomic():
    outputs = set(re.findall(r'RWStructuredBuffer<\w+> (\w+)Output;', SHADER))
    assert outputs == {name for name, _, _ in BINDINGS}
    assert 'RWStructuredBuffer<uint> Diagnostics;' in SHADER
    assert 'InterlockedAdd(Diagnostics[0],1)' in SHADER
    assert 'InterlockedAdd(Diagnostics[1],1)' in SHADER
    assert 'ClearUnusedGraphResources(Shader,P);' in CPP


@pytest.mark.parametrize('name,buffer', [('Direction', 'P'), ('Scratch', 'AP'),
                                       ('Partial', 'Partial'), ('Control', 'Control')])
def test_fused_acceleration_inputs_are_not_writable(name, buffer):
    shader = (ROOT / 'unreal/Plugins/RaftSim/Shaders/Private/RaftSimNonlinearAcceleration.usf').read_text()
    cpp = (ROOT / 'unreal/Plugins/RaftSim/Source/RaftSimWaterDetail/Private/RaftSimNonlinearAccelerationGPU.cpp').read_text()
    assert ('#if !RAFTSIM_ACCELERATION_PREPARE && RAFTSIM_ACCELERATION_PHASE == 13\n'
            f'StructuredBuffer<float4> {name}Input;\n#define {name} {name}Input\n'
            f'#else\nRWStructuredBuffer<float4> {name};\n#endif') in shader
    assert f'SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,{name}Input)' in cpp
    assert f'Params->{name}=!Prepare && Phase==13 ? nullptr:Graph.CreateUAV({buffer});' in cpp
    assert f'Params->{name}Input=!Prepare && Phase==13 ? Graph.CreateSRV({buffer}):nullptr;' in cpp
