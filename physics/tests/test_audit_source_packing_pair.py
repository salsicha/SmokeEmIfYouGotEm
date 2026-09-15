import pytest
from audit_source_packing_pair import summarize


def fixture():
    return dict(schema='raftsim.source_packing_pair.v1', exact=True, pairs=[dict(
        pair=i, frame=122+i, vertices=50625, exact=True, vector_first=bool(i % 2),
        reference_ms=2.4, vector_ms=1.9) for i in range(64)])


def test_complete_scoped_evidence_and_both_orders():
    result = summarize(fixture())
    assert result['exact_all_attributes'] and result['measured_both_orders_faster']
    assert result['compared_vertices'] == 64*50625
    assert result['groups']['reference_first']['pairs'] == 32
    assert not result['release_accepted']


def test_failures_and_losing_order_are_not_hidden_in_mean():
    data = fixture(); data['pairs'][10]['exact'] = False
    assert not summarize(data)['exact_all_attributes']
    data = fixture()
    for row in data['pairs'][::2]: row['vector_ms'] = 2.6
    assert not summarize(data)['measured_both_orders_faster']


@pytest.mark.parametrize('key,value', [('pair', False), ('pair', 1), ('frame', 119), ('frame', 122.1),
    ('vertices', 0), ('vertices', True), ('exact', 1), ('vector_first', True), ('reference_ms', 0),
    ('vector_ms', float('nan')), ('vector_ms', float('inf'))])
def test_malformed_or_unmeasured_data_rejected(key, value):
    data = fixture(); data['pairs'][0][key] = value
    with pytest.raises(ValueError): summarize(data)


def test_missing_pairs_or_single_frame_rejected():
    data = fixture(); data['pairs'].pop()
    with pytest.raises(ValueError): summarize(data)
    data = fixture()
    for row in data['pairs']: row['frame'] = 120
    with pytest.raises(ValueError): summarize(data)


def test_retained_output_is_not_reported_as_vector_color_optimization():
    data = fixture(); data['schema'] = 'raftsim.source_packing_pair.v2'
    data['candidate_kind'] = 'retained-output'
    for row in data['pairs']:
        row['candidate_first'] = row.pop('vector_first')
        row['candidate_ms'] = row.pop('vector_ms')
    result = summarize(data)
    assert result['candidate_kind'] == 'retained-output'
    assert result['measured_both_orders_faster']
    data['candidate_kind'] = 'unknown'
    with pytest.raises(ValueError): summarize(data)
