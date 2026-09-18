import copy
import pytest
from audit_atlas_stencil_pair import summarize


def fixture():
    return dict(schema='raftsim.atlas_stencil_pair.v1', map='L_SouthForkAmerican_FullReach',
        samples=50625, world_seconds=10.2, different_samples=0, passed=True,
        paired_parallel_passes_exact=True, identical_masks_probe_requests_feather_and_heights=True,
        atlas_stencil_pairs=[dict(candidate_first=bool(i % 2), reference_ms=5., candidate_ms=4.,
                                 all_samples_and_masks_exact=True) for i in range(64)])


def test_complete_original_evidence_not_mutated_or_overclaimed():
    data = fixture(); before = copy.deepcopy(data); result = summarize(data)
    assert data == before
    assert result['exact'] and result['measured_both_orders_faster']
    assert not result['release_accepted'] and result['groups']['all']['pairs'] == 64


@pytest.mark.parametrize('key,value', [('passed', False), ('different_samples', 1),
    ('paired_parallel_passes_exact', False), ('identical_masks_probe_requests_feather_and_heights', False)])
def test_false_equality_verdicts_remain_false(key, value):
    data = fixture(); data[key] = value
    assert not summarize(data)['exact']


def test_losing_order_not_hidden_by_faster_average():
    data = fixture()
    for row in data['atlas_stencil_pairs'][::2]: row['candidate_ms'] = 5.1
    result = summarize(data)
    assert result['groups']['all']['candidate_mean_ms'] < 5
    assert not result['measured_both_orders_faster']
    data['atlas_stencil_pairs'][40]['all_samples_and_masks_exact'] = False
    assert not summarize(data)['exact']


@pytest.mark.parametrize('key,value', [('schema', 'other'), ('map', 'Troublemaker'), ('samples', 0),
    ('samples', True), ('different_samples', -1), ('different_samples', 50626), ('passed', 1),
    ('world_seconds', 9.99), ('world_seconds', float('nan'))])
def test_bad_capture_rejected(key, value):
    data = fixture(); data[key] = value
    with pytest.raises(ValueError): summarize(data)


@pytest.mark.parametrize('key,value', [('candidate_first', True), ('candidate_first', 0),
    ('all_samples_and_masks_exact', 1), ('reference_ms', 0), ('candidate_ms', float('inf')),
    ('candidate_ms', float('nan')), ('reference_ms', True)])
def test_bad_or_unmeasured_rows_rejected(key, value):
    data = fixture(); data['atlas_stencil_pairs'][0][key] = value
    with pytest.raises(ValueError): summarize(data)


def test_missing_pairs_rejected():
    data = fixture(); data['atlas_stencil_pairs'].pop()
    with pytest.raises(ValueError): summarize(data)
