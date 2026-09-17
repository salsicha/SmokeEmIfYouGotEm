import pytest
from audit_crest_sample_order import summarize


def capture():
    return dict(exact=True, pairs=[dict(pair=i, frame=124+i*2, exact=True, candidate_first=bool(i%2),
        vertices=50000, triangles=90000, reference_ms=7., candidate_ms=6.) for i in range(64)])


def test_complete_exact_both_orders():
    result = summarize(capture())
    assert result['exact_topology_and_coordinates'] and result['measured_both_orders_faster']
    assert result['compared_vertices'] == 64*50000
    assert result['compared_triangles'] == 64*90000
    assert result['release_accepted'] is False


@pytest.mark.parametrize('key,value', [('pair', True), ('pair', 3), ('candidate_first', 0),
    ('candidate_first', True), ('exact', 1), ('frame', 119), ('frame', float('nan')),
    ('vertices', 0), ('triangles', 1.2), ('reference_ms', 0), ('candidate_ms', float('inf')),
    ('candidate_ms', float('nan')), ('reference_ms', True)])
def test_invalid_original_values_rejected(key, value):
    report = capture()
    report['pairs'][0][key] = value
    with pytest.raises(ValueError):
        summarize(report)


def test_missing_duplicate_and_repeated_frames_rejected():
    for mode in range(3):
        report = capture()
        if mode == 0:
            report['pairs'].pop()
        elif mode == 1:
            report['pairs'].append(report['pairs'][-1])
        else:
            report['pairs'][1]['frame'] = report['pairs'][0]['frame']
        with pytest.raises(ValueError):
            summarize(report)


def test_mismatch_and_order_sensitive_timings_fail():
    report = capture()
    report['pairs'][7]['exact'] = False
    assert not summarize(report)['exact_topology_and_coordinates']
    report = capture()
    report['exact'] = False
    assert not summarize(report)['exact_topology_and_coordinates']
    report = capture()
    for row in report['pairs'][1::2]:
        row['candidate_ms'] = 7.1
    result = summarize(report)
    assert result['exact_topology_and_coordinates']
    assert not result['measured_both_orders_faster']
