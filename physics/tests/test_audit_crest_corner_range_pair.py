import copy
import pytest
from audit_crest_corner_range_pair import summarize
from test_audit_crest_interval_pair import fixture as interval_fixture


def fixture():
    return {**interval_fixture(), 'schema': 'raftsim.crest_corner_range_pair.v1'}


def test_shared_contract_does_not_modify_input_or_accept_original_experiment():
    data = fixture()
    before = copy.deepcopy(data)
    result = summarize(data)
    assert data == before
    assert result['exact_topology_and_production'] and result['measured_both_orders_faster']
    assert not result['release_accepted']
    with pytest.raises(ValueError):
        summarize(interval_fixture())


@pytest.mark.parametrize('kind', ('missing', 'order', 'nan', 'single-frame', 'bool-count'))
def test_corrupted_evidence_cannot_be_summarized(kind):
    data = fixture()
    if kind == 'missing': data['pairs'].pop()
    if kind == 'order': data['pairs'][3]['candidate_first'] = False
    if kind == 'nan': data['pairs'][5]['candidate_ms'] = float('nan')
    if kind == 'single-frame':
        for row in data['pairs']: row['frame'] = 130
    if kind == 'bool-count': data['pairs'][3]['triangles'] = True
    with pytest.raises(ValueError):
        summarize(data)


def test_one_losing_order_and_topology_failure_are_retained():
    data = fixture()
    for row in data['pairs'][1::2]: row['candidate_ms'] = 3.01
    result = summarize(data)
    assert result['groups']['all']['candidate_mean_ms'] < 3
    assert not result['measured_both_orders_faster']
    data['pairs'][13]['exact'] = False
    assert not summarize(data)['exact_topology_and_production']
