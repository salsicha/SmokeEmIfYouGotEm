import pytest
from audit_sm5_shader_resources import audit


def assembly(count):
    return ('// Resource Bindings:\n' + ''.join(
        f'// Output{i} UAV struct r/w u{i} 1\n' for i in range(count)) +
        'cs_5_0\n' + ''.join(f'dcl_uav_structured u{i}, 16\n' for i in range(count)))


@pytest.mark.parametrize('count', [0, 1, 6, 8])
def test_supported_resource_count(count):
    result = audit(assembly(count))
    assert result['passed'] and result['uav_count'] == count
    assert not result['gpu_execution_accepted'] and not result['full_cook_accepted']


@pytest.mark.parametrize('count', [9, 10, 11, 12, 13])
def test_successful_compilation_can_still_exceed_sm5(count):
    assert not audit(assembly(count))['passed']


def test_extended_feature_flag_and_sparse_high_slot_rejected():
    assert not audit('// 64 UAV slots\n'+assembly(8))['passed']
    assert not audit(assembly(1).replace('u0', 'u9'))['passed']


def test_fxc_indented_listing_matches_unindented_engine_dump():
    source = assembly(6)
    indented = source.replace('cs_5_0', '      cs_5_0').replace('dcl_uav', '      dcl_uav')
    assert audit(indented.replace('\n', '\r\n')) == audit(source)


@pytest.mark.parametrize('text', ['', 'cs_5_0\n', assembly(1).replace('cs_5_0', 'cs_6_0'),
                                assembly(1).replace('dcl_uav_structured u0, 16\n', ''),
                                assembly(2).replace('u1', 'u0')])
def test_missing_or_inconsistent_reflection_fails(text):
    with pytest.raises(ValueError):
        audit(text)
