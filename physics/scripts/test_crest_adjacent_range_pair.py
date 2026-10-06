import pytest
from audit_crest_adjacent_range_pair import summarize


def fixture():
    return dict(schema='raftsim.crest_adjacent_range_pairs.v1', exact=True,
        pairs=[dict(pair=i, frame=122+i*2, exact=True, candidate_first=bool(i%2),
                    vertices=1000+i, triangles=1800+i, reference_ms=2., candidate_ms=1.) for i in range(64)])


def test_exactness_and_both_orders():
    result = summarize(fixture())
    assert result['exact_topology_and_coordinates'] and result['measured_both_orders_faster']
    assert result['compared_vertices'] == sum(1000+i for i in range(64))
    assert not result['release_accepted']


def test_average_only_improvement_rejected():
    report = fixture()
    for row in report['pairs']:
        row['candidate_ms'] = 2.1 if row['candidate_first'] else .1
    assert not summarize(report)['measured_both_orders_faster']


@pytest.mark.parametrize('key,value', [('pair', 9), ('candidate_first', 1), ('exact', 1),
    ('frame', 119), ('reference_ms', 0), ('candidate_ms', float('nan')), ('vertices', 0), ('triangles', 1.5)])
def test_invalid_original_rows_rejected(key, value):
    report = fixture()
    report['pairs'][0][key] = value
    with pytest.raises(ValueError):
        summarize(report)


def test_incomplete_reordered_and_repeated_frames_rejected():
    report = fixture()
    for rows in (report['pairs'][:-1], report['pairs'][::-1]):
        with pytest.raises(ValueError):
            summarize(dict(report, pairs=rows))
    for row in report['pairs']:
        row['frame'] = 130
    with pytest.raises(ValueError):
        summarize(report)


def test_failed_native_comparison_stays_failed():
    report = fixture()
    report['pairs'][37]['exact'] = False
    assert not summarize(report)['exact_topology_and_coordinates']
    report = fixture()
    report['exact'] = False
    assert not summarize(report)['exact_topology_and_coordinates']


def test_wrong_schema_is_not_adjacent_range_evidence():
    report = fixture()
    del report['schema']
    with pytest.raises(ValueError):
        summarize(report)
