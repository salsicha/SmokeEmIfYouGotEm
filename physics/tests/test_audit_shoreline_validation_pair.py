import pytest
from audit_shoreline_validation_pair import summarize


def fixture():
    return dict(exact=True, pairs=[dict(pair=i, frame=122+i, vertices=50625,
        candidate_first=bool(i % 2), exact=True, valid=True, reuse=bool(i % 3),
        reference_ms=2.4, candidate_ms=1.9) for i in range(64)])


def test_complete_exact_evidence_is_not_fps_acceptance():
    report = summarize(fixture())
    assert report['exact_validation_and_reuse'] and report['measured_both_orders_faster']
    assert report['compared_vertices'] == 64*50625
    assert report['groups']['candidate_first']['pairs'] == 32
    assert not report['performance_accepted'] and not report['visual_accepted']


def test_losing_order_and_failure_are_not_hidden_by_mean():
    data = fixture()
    for row in data['pairs'][::2]:
        row['candidate_ms'] = 2.5
    assert not summarize(data)['measured_both_orders_faster']
    data = fixture(); data['pairs'][7]['exact'] = False
    assert not summarize(data)['exact_validation_and_reuse']
    data = fixture(); data['pairs'][7]['valid'] = False
    assert not summarize(data)['all_inputs_valid']


@pytest.mark.parametrize('key,value', [('pair', False), ('pair', 1), ('frame', 119),
    ('frame', 122.5), ('vertices', 0), ('vertices', True), ('exact', 1), ('valid', 1),
    ('reuse', None), ('candidate_first', True), ('reference_ms', 0),
    ('candidate_ms', float('nan')), ('candidate_ms', float('inf'))])
def test_malformed_or_unmeasured_evidence_rejected(key, value):
    data = fixture(); data['pairs'][0][key] = value
    with pytest.raises(ValueError):
        summarize(data)


def test_missing_pairs_or_single_frame_rejected():
    data = fixture(); data['pairs'].pop()
    with pytest.raises(ValueError):
        summarize(data)
    data = fixture()
    for row in data['pairs']:
        row['frame'] = 120
    with pytest.raises(ValueError):
        summarize(data)


def test_versioned_report_requires_explicit_candidate_identity():
    data = fixture(); data['schema'] = 'raftsim.shoreline_validation_pair.v1'
    with pytest.raises(ValueError):
        summarize(data)
    data['candidate_kind'] = 'parallel-fused'
    assert summarize(data)['candidate_kind'] == 'parallel-fused'
    data['schema'] = 'unknown'
    with pytest.raises(ValueError):
        summarize(data)
