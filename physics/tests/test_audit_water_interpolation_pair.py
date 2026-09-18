import pytest
from audit_water_interpolation_pair import summarize


def fixture():
    return dict(schema='raftsim.water_interpolation_packing_pair.v1', exact=True, pairs=[dict(
        pair=i, frame=122+i, vertices=50625, alpha=.37, fields_and_packing_exact=True,
        production_exact=True, candidate_first=bool(i % 2), reference_ms=2.4, candidate_ms=1.9)
        for i in range(64)])


def test_complete_scoped_evidence():
    result = summarize(fixture())
    assert result['exact_all_fields_and_attributes'] and result['measured_both_orders_faster']
    assert result['compared_vertices'] == 64*50625
    assert result['groups']['candidate_first']['pairs'] == 32
    assert not result['release_accepted']


@pytest.mark.parametrize('key', ['fields_and_packing_exact', 'production_exact'])
def test_either_equality_failure_is_preserved(key):
    data = fixture(); data['pairs'][10][key] = False
    assert not summarize(data)['exact_all_fields_and_attributes']


def test_losing_order_not_hidden_by_aggregate():
    data = fixture()
    for row in data['pairs'][::2]: row['candidate_ms'] = 2.6
    assert not summarize(data)['measured_both_orders_faster']


@pytest.mark.parametrize('key,value', [('pair', False), ('pair', 1), ('frame', 119), ('frame', 122.1),
    ('vertices', 0), ('vertices', True), ('fields_and_packing_exact', 1), ('production_exact', 1),
    ('candidate_first', True), ('reference_ms', 0), ('candidate_ms', float('nan')),
    ('candidate_ms', float('inf')), ('candidate_ms', True), ('alpha', 0), ('alpha', 1.01), ('alpha', True)])
def test_malformed_or_unmeasured_rejected(key, value):
    data = fixture(); data['pairs'][0][key] = value
    with pytest.raises(ValueError): summarize(data)


def test_missing_or_repeated_frames_rejected():
    data = fixture(); data['pairs'].pop()
    with pytest.raises(ValueError): summarize(data)
    data = fixture(); data['pairs'][1]['frame'] = data['pairs'][0]['frame']
    with pytest.raises(ValueError): summarize(data)
    data = fixture(); data['exact'] = 1
    with pytest.raises(ValueError): summarize(data)


def test_top_level_failure_preserved():
    data = fixture(); data['exact'] = False
    assert not summarize(data)['exact_all_fields_and_attributes']
