import pytest
from audit_prepared_crest_range_pair import summarize
from test_audit_crest_range_pair import fixture as range_fixture


def fixture():
    data = range_fixture()
    for row in data['pairs']:
        row['prepared_first'] = row.pop('bounded_first')
        row['prepared_ms'] = row.pop('bounded_ms')
        row['preparation_ms'] = .25
    return data


def test_preparation_is_charged_to_every_build():
    result = summarize(fixture())
    assert result['exact_topology_and_coordinates'] and result['measured_both_orders_faster']
    assert result['groups']['all']['prepared_including_preparation_mean_ms'] == 10.25
    assert not result['release_accepted']
    data = fixture()
    for row in data['pairs']:
        row['preparation_ms'] = 3.
    assert not summarize(data)['measured_both_orders_faster']


def test_single_mismatch_or_losing_order_is_not_qualified():
    data = fixture(); data['pairs'][31]['exact'] = False
    assert not summarize(data)['exact_topology_and_coordinates']
    data = fixture()
    for row in data['pairs'][::2]:
        row['prepared_ms'] = 13.
    assert not summarize(data)['measured_both_orders_faster']


@pytest.mark.parametrize('key,value', [('preparation_ms', -1.), ('preparation_ms', float('nan')),
    ('preparation_ms', True), ('prepared_ms', 0.), ('prepared_ms', float('inf')),
    ('prepared_first', True), ('reference_ms', 0.), ('vertices', 0), ('pair', 2)])
def test_invalid_records_refused(key, value):
    data = fixture(); data['pairs'][0][key] = value
    with pytest.raises(ValueError):
        summarize(data)


def test_incomplete_history_refused():
    data = fixture(); data['pairs'].pop()
    with pytest.raises(ValueError, match='64-pair'):
        summarize(data)
