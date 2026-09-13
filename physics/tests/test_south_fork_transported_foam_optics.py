"""Optical-response regressions, not physical or visual rapid acceptance."""
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/RaftSimEditorCurrentWaterMaterial.cpp'


def smooth(a, b, x):
    t = max(0, min(1, (x-a)/(b-a)))
    return t*t*(3-2*t)


def response(foam, lace, density=3, footprint=.04):
    amount = max(0, min(1, foam))
    threshold = .80 + (.12-.80)*smooth(.12, .65, amount)
    aa = max(footprint, .04)
    cells = smooth(threshold-aa, threshold+aa, lace)
    return (1-math.exp(-max(density, 0)*amount))*(.1+.9*cells)


def test_zero_foam_cannot_be_whitened_by_lace_or_density():
    for lace in (0, .2, .5, 1):
        for density in (0, 3, 100):
            assert response(0, lace, density) == 0
            assert response(-1, lace, density) == 0
    assert response(.74, 1, 0) == 0


def test_response_is_bounded_monotonic_and_continuous():
    for lace in (0, .1, .2, .5, .9, 1):
        values = [response(i/10000, lace) for i in range(10001)]
        assert all(0 <= value <= 1 for value in values)
        assert all(0 <= b-a < .003 for a, b in zip(values, values[1:]))
    assert response(.7412, .5) > .89
    assert response(.7412, 0) < .1  # open pockets even at the measured peak
    assert response(.2, .9) > .4  # transported sparse foam is not cut off


def test_material_uses_transported_foam_and_shared_optical_consumers_only():
    source = SOURCE.read_text()
    block = source.split('bool ConfigureSouthForkTransportedFoam(', 1)[1].split('// River-specific optical detail', 1)[0]
    assert 'Input(TEXT("VertexFoam"), Vertex)' in block
    assert 'Texture->ParameterName == TEXT("WhitewaterFoamLace")' in block
    assert 'saturate(VertexFoam.r)' in block and 'fwidth(Lace.r)' in block
    assert 'TEXT("FoamRoughness")' in block
    assert 'TEXT("FoamWaterOpacity")' in block
    assert 'TEXT("SpeedAerationFraction")' in block
    assert 'if (!bRoughness || !bOpacity || !bScattering) return false;' in block
    assert 'WorldPositionOffset' not in block and 'OpacityMask' not in block
    assert 'RiverLabel == TEXT("SouthFork") && !ConfigureSouthForkTransportedFoam(Material)' in source
