import pytest
from audit_crest_range_pair import summarize


def fixture():
    return dict(exact=True, pairs=[dict(pair=i, frame=120+i, bounded_first=bool(i%2), exact=True,
        vertices=1000+i, triangles=1400+i, reference_ms=12., bounded_ms=10.) for i in range(64)])


def test_complete_exact_comparison_preserves_names_counts_and_scoped_acceptance():
    report = summarize(fixture())
    assert report['exact_topology_and_coordinates'] and report['measured_both_orders_faster']
    assert report['compared_vertices'] == sum(1000+i for i in range(64))
    assert report['groups']['reference_first']['bounded_mean_ms'] == 10.
    assert report['groups']['bounded_first']['reference_mean_ms'] == 12.
    assert not report['release_accepted']


def test_any_mismatch_or_losing_order_prevents_qualification():
    data = fixture(); data['pairs'][31]['exact'] = False
    assert not summarize(data)['exact_topology_and_coordinates']
    data = fixture()
    for row in data['pairs'][::2]:
        row['bounded_ms'] = 13.
    result = summarize(data)
    assert result['groups']['all']['bounded_mean_ms'] < result['groups']['all']['reference_mean_ms']
    assert not result['measured_both_orders_faster']


@pytest.mark.parametrize('key,value', [('frame', 119), ('vertices', 0), ('triangles', 1.5),
    ('bounded_first', True), ('exact', 1), ('bounded_ms', float('nan')), ('reference_ms', 0.), ('pair', 2)])
def test_invalid_native_records_reject(key, value):
    data = fixture();data['pairs'][0][key] = value
    with pytest.raises(ValueError):
        summarize(data)


def test_missing_pairs_and_repeated_frame_control_reject():
    data = fixture();data['pairs'].pop()
    with pytest.raises(ValueError, match='64-pair'):
        summarize(data)
    data = fixture()
    for row in data['pairs']:
        row['frame'] = 120
    with pytest.raises(ValueError, match='changing-input'):
        summarize(data)


def test_repeated_call_within_frame_is_retained_not_deduplicated():
    data = fixture();data['pairs'][1]['frame'] = 120
    assert summarize(data)['groups']['all']['pairs'] == 64
