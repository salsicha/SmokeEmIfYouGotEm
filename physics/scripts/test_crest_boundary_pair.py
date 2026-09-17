from copy import deepcopy
import pytest
from audit_crest_boundary_pair import summarize


def fixture():
    return dict(exact=True, pairs=[dict(pair=i, frame=122+i*2, exact=True, indexed_first=bool(i%2),
        source_vertices=50000, midpoints=1000+i, boundary_midpoints=20+i, triangles=90000,
        reference_ms=1., indexed_ms=.6) for i in range(64)])


def test_exactness_counts_and_both_orders():
    result = summarize(fixture())
    assert result['exact_boundary_flags'] and result['measured_both_orders_faster']
    assert result['compared_midpoints'] == sum(1000+i for i in range(64))
    assert not result['release_accepted']


def test_no_average_only_speed_acceptance():
    report = fixture()
    for row in report['pairs']:
        row['indexed_ms'] = 1.1 if row['indexed_first'] else .1
    assert not summarize(report)['measured_both_orders_faster']


@pytest.mark.parametrize('key,value', [('pair', 9), ('indexed_first', 1), ('exact', 1),
    ('frame', 119), ('reference_ms', 0), ('indexed_ms', float('nan')),
    ('midpoints', -1), ('source_vertices', 0), ('triangles', 1.5),
    ('boundary_midpoints', 100000)])
def test_rejects_invalid_original_rows(key, value):
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


def test_negative_native_exactness_is_not_hidden():
    for kind in ('report', 'row'):
        report = deepcopy(fixture())
        (report if kind == 'report' else report['pairs'][37])['exact'] = False
        assert not summarize(report)['exact_boundary_flags']


def test_other_candidate_evidence_cannot_stand_in_for_boundaries():
    report = fixture()
    for row in report['pairs']:
        del row['boundary_midpoints']
    with pytest.raises(KeyError):
        summarize(report)
