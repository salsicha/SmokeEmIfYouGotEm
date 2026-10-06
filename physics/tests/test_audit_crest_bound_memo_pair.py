import pytest
from audit_crest_bound_memo_pair import summarize


def fixture():
    return dict(exact=True, pairs=[dict(pair=i, frame=120+i, bound_first=bool(i%2), exact=True,
        vertices=1000+i, triangles=1400+i, reference_ms=12., bound_ms=10.,
        reference_retained_bytes=1024, bound_retained_bytes=2048) for i in range(64)])


def test_complete_exact_comparison_retains_memory_cost_and_scope():
    result = summarize(fixture())
    assert result['exact_topology_and_coordinates'] and result['measured_both_orders_faster']
    assert result['compared_vertices'] == sum(1000+i for i in range(64))
    assert result['groups']['reference_first']['bound_mean_ms'] == 10.
    assert result['retained_memory']['bound_retained_bytes_maximum'] == 2048
    assert not result['release_accepted']


def test_one_losing_order_or_one_mismatch_prevents_qualification():
    data = fixture(); data['pairs'][31]['exact'] = False
    assert not summarize(data)['exact_topology_and_coordinates']
    data = fixture()
    for row in data['pairs'][::2]:
        row['bound_ms'] = 13.
    assert not summarize(data)['measured_both_orders_faster']


@pytest.mark.parametrize('key,value', [('frame', 119), ('vertices', 0), ('triangles', 1.5),
    ('bound_first', True), ('exact', 1), ('bound_ms', float('nan')), ('reference_ms', 0.), ('pair', 2),
    ('bound_retained_bytes', -1), ('bound_retained_bytes', float('inf')), ('bound_retained_bytes', True),
    ('bound_retained_bytes', .5)])
def test_invalid_native_records_reject(key, value):
    data = fixture(); data['pairs'][0][key] = value
    with pytest.raises(ValueError):
        summarize(data)


def test_missing_pairs_or_single_frame_reject():
    data = fixture(); data['pairs'].pop()
    with pytest.raises(ValueError):
        summarize(data)
    data = fixture()
    for row in data['pairs']:
        row['frame'] = 120
    with pytest.raises(ValueError):
        summarize(data)
