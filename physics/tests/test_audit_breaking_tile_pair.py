import pytest
from audit_breaking_tile_pair import summarize


def fixture():
    return dict(exact=True, pairs=[dict(pair=i, frame=122+i, exact=True, dense_first=bool(i % 2),
        points=50000, nonzero_heights=700, dense_tiles=200, hash_tiles=120, hash_ms=2., dense_ms=1.) for i in range(64)])


def test_complete_both_order_control_is_not_release_acceptance():
    result = summarize(fixture())
    assert result['exact_height_and_foam'] and result['measured_both_orders_faster']
    assert result['compared_points'] == 3200000
    assert not result['release_accepted']


@pytest.mark.parametrize('key,value', [('pair', True), ('frame', 122), ('dense_first', 1),
    ('dense_ms', float('nan')), ('points', 0), ('nonzero_heights', 50001), ('dense_tiles', 65537)])
def test_malformed_or_repeated_native_evidence_rejects(key, value):
    report = fixture()
    report['pairs'][1][key] = value
    with pytest.raises(ValueError):
        summarize(report)


def test_incomplete_order_sensitive_and_mismatch_results_cannot_promote():
    report = fixture()
    report['pairs'].pop()
    with pytest.raises(ValueError):
        summarize(report)
    report = fixture()
    for row in report['pairs'][1::2]:
        row['dense_ms'] = 3.
    assert not summarize(report)['measured_both_orders_faster']
    report['pairs'][0]['exact'] = False
    assert not summarize(report)['exact_height_and_foam']
