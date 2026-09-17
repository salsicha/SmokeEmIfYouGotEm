import copy

import pytest

from audit_crest_empty_tile_pair import summarize


def fixture():
    return dict(exact=True, pairs=[dict(pair=i, frame=120+i, skip_first=bool(i % 2),
        exact=True, vertices=1000+i, triangles=1400+i, legacy_ms=12., skip_ms=10.,
        legacy_assembly_ms=4., skip_assembly_ms=3.) for i in range(64)])


def test_complete_comparison_preserves_evidence_and_has_no_release_claim():
    data = fixture()
    before = copy.deepcopy(data)
    result = summarize(data)
    assert data == before
    assert result['exact_topology_and_coordinates'] and result['measured_both_orders_faster']
    assert result['groups']['skip_first']['skip_mean_ms'] == 10.
    assert not result['release_accepted']


def test_mismatch_and_losing_order_reject():
    data = fixture()
    data['pairs'][31]['exact'] = False
    assert not summarize(data)['exact_topology_and_coordinates']
    data = fixture()
    for row in data['pairs'][::2]:
        row['skip_ms'] = 13.
    result = summarize(data)
    assert result['groups']['all']['skip_mean_ms'] < 12.
    assert not result['measured_both_orders_faster']


@pytest.mark.parametrize('key,value', [('frame', 119), ('vertices', 0), ('triangles', 1.5),
    ('skip_first', True), ('exact', 1), ('skip_ms', float('nan')), ('legacy_ms', 0.),
    ('pair', 2), ('skip_assembly_ms', float('nan')), ('legacy_assembly_ms', 13.)])
def test_invalid_native_record_rejects(key, value):
    data = fixture()
    data['pairs'][0][key] = value
    with pytest.raises(ValueError):
        summarize(data)


def test_missing_pairs_reject():
    data = fixture()
    data['pairs'].pop()
    with pytest.raises(ValueError):
        summarize(data)


def test_different_candidate_report_cannot_be_relabelled_as_skip():
    data = fixture()
    data['pairs'] = [{key.replace('skip', 'strong'): value for key, value in row.items()}
                     for row in data['pairs']]
    with pytest.raises(ValueError, match='empty-tile fields'):
        summarize(data)


def test_mixed_candidate_fields_cannot_override_skip_evidence():
    data = fixture()
    data['pairs'][0]['strong_ms'] = 1.
    with pytest.raises(ValueError, match='Mixed'):
        summarize(data)
