import copy
import pytest
from audit_crest_topology_storage_pair import summarize


def fixture():
    return dict(exact=True, pairs=[dict(pair=i, frame=120+i, retained_first=bool(i%2),
        exact=True, vertices=1000+i, triangles=1400+i, legacy_ms=12., retained_ms=10.,
        legacy_assembly_ms=4., retained_assembly_ms=3., root_changed=bool(i%3==0),
        legacy_storage_bytes=10000, retained_storage_bytes=15000) for i in range(64)])


def test_complete_immutable_comparison_reports_memory_not_release_acceptance():
    data = fixture(); before = copy.deepcopy(data)
    result = summarize(data)
    assert data == before and result['exact_topology_and_coordinates']
    assert result['measured_both_orders_faster'] and result['root_changes'] == 22
    assert result['maximum_retained_storage_bytes'] == 15000
    assert not result['release_accepted']


def test_losing_order_cannot_hide_behind_combined_win():
    data = fixture()
    for row in data['pairs'][::2]:
        row['retained_ms'] = 13.
    result = summarize(data)
    assert result['groups']['all']['retained_mean_ms'] < 12.
    assert not result['measured_both_orders_faster']


def test_mismatch_is_not_an_exact_result():
    data = fixture(); data['pairs'][30]['exact'] = False
    assert not summarize(data)['exact_topology_and_coordinates']


@pytest.mark.parametrize('key,value', [('retained_first', True), ('frame', 119),
    ('retained_ms', float('nan')), ('legacy_ms', 0.), ('exact', 1), ('pair', 5),
    ('retained_assembly_ms', 11.), ('root_changed', 1), ('retained_storage_bytes', True),
    ('legacy_storage_bytes', -1), ('retained_storage_bytes', float('inf'))])
def test_invalid_original_record_rejects(key, value):
    data = fixture(); data['pairs'][0][key] = value
    with pytest.raises(ValueError):
        summarize(data)


def test_incomplete_or_unchanged_roots_reject():
    data = fixture(); data['pairs'].pop()
    with pytest.raises(ValueError):
        summarize(data)
    data = fixture()
    for row in data['pairs']:
        row['root_changed'] = False
    with pytest.raises(ValueError, match='root topology'):
        summarize(data)


def test_other_candidate_labels_reject():
    data = fixture(); data['pairs'][0]['indexed_ms'] = 1.
    with pytest.raises(ValueError, match='Mixed'):
        summarize(data)
    data = fixture(); del data['pairs'][0]['retained_ms']
    with pytest.raises(ValueError, match='topology-storage'):
        summarize(data)
