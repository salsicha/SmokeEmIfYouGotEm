import pytest
from audit_crest_publication_cache import audit


def records(candidate='.1'):
    return '\n'.join(f'CrestPublicationCachePair frame={i} exact=1 candidate_first={(i//2)%2} '
                     f'reused={i%2} indices=30 cells=11 reference_ms=.2 candidate_ms={candidate}'
                     for i in range(120, 248))


def test_complete_pair_and_slower_candidate_are_reported_honestly():
    result = audit(records())
    assert len(result['rows']) == 128
    assert result['both_order_mean_improved']
    assert not result['gameplay_performance_or_scene_accepted']
    assert not audit(records('.3'))['both_order_mean_improved']


@pytest.mark.parametrize('change', (
    lambda s: s.split('\n', 1)[1],
    lambda s: s+'\n'+s.split('\n')[0],
    lambda s: '\n'.join(reversed(s.splitlines())),
    lambda s: s.replace('exact=1', 'exact=0', 1),
    lambda s: s.replace('candidate_first=0', 'candidate_first=1', 1),
    lambda s: s.replace('reused=0', 'reused=2', 1),
    lambda s: s.replace('candidate_ms=.1', 'candidate_ms=nan', 1),
    lambda s: s.replace('reference_ms=.2', 'reference_ms=-1', 1),
    lambda s: s.replace('indices=30', 'indices=31', 1),
    lambda s: s.replace('indices=30', 'indices=0'),
    lambda s: s.replace('cells=11', 'cells=0', 1),
    lambda s: s.replace('candidate_ms=.1', 'missing=.1', 1),
    lambda s: s+'\nCrestPublicationCache mismatch',
))
def test_bad_evidence_fails_closed(change):
    with pytest.raises(ValueError):
        audit(change(records()))
