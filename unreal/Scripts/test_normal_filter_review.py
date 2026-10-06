from pathlib import Path
import pytest
from create_south_fork_normal_filter_review import FOOTPRINT, FLOAT_HASH, INTEGER_HASH, unfiltered_control, control_code


def baseline_code():
    # Preserve the exact pre-install diagnostic input after the scoped fix.
    code = (Path(__file__).parents[1]/'Shaders/Private/RaftSimLocalCurrentNormal.hlsl').read_text()
    assert code.count(INTEGER_HASH) == 1 and FLOAT_HASH not in code
    return code.replace(INTEGER_HASH, FLOAT_HASH)


def test_control_changes_only_filter_expression():
    code = baseline_code()
    result = unfiltered_control(code)
    assert result != code
    assert result.replace('float footprint = 0.0; // diagnostic: no derivative attenuation', FOOTPRINT) == code
    for token in ('Flow.xy * phaseA', 'Flow.xy * phaseB', '* Strength', 'gradient(a)', 'gradient(b)'):
        assert token in result


@pytest.mark.parametrize('code', ['', 'float footprint = 1;', FOOTPRINT + FOOTPRINT])
def test_control_rejects_changed_or_ambiguous_shader(code):
    with pytest.raises(ValueError):
        unfiltered_control(code)


def test_zero_flow_preserves_noise_strength_and_filtering():
    code = baseline_code()
    result = control_code(code, 'zero-flow')
    assert result.replace('float2(0,0) * phase', 'Flow.xy * phase') == code
    assert FOOTPRINT in result and '* Strength' in result


def test_constant_tilt_is_explicit_diagnostic():
    assert control_code('', 'constant') == 'return normalize(float3(0.18,0.09,1.0)); // diagnostic: constant tangent-space tilt'
    with pytest.raises(ValueError):
        control_code('', 'unknown')
    with pytest.raises(ValueError):
        control_code('', 'zero-flow')


def test_integer_hash_preserves_all_other_normal_operations():
    code = baseline_code()
    result = control_code(code, 'integer-hash')
    assert result.replace(INTEGER_HASH, FLOAT_HASH) == code
    assert FOOTPRINT in result and 'Flow.xy * phaseA' in result and '* Strength' in result
    with pytest.raises(ValueError):
        control_code('', 'integer-hash')


def test_shipping_shader_matches_reviewed_candidate_exactly():
    shader = (Path(__file__).parents[1]/'Shaders/Private/RaftSimLocalCurrentNormal.hlsl').read_text()
    assert shader == control_code(baseline_code(), 'integer-hash')
    with pytest.raises(ValueError):
        control_code(shader, 'integer-hash')  # Never silently apply twice.
