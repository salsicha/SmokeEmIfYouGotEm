import pytest
from audit_render_values import summarize


def capture():
    return '\n'.join(f'RENDER_VALUES_PAIR frame={i} original_first={int(i%2==0)} reuse=1 vertices=50000 exact=1 original_ms=1.2 candidate_ms=0.4' for i in range(120,184))


def test_complete_exact_both_orders():
    result = summarize(capture())
    assert result['exact'] and result['measured_both_orders_faster']
    assert result['compared_vertices'] == 3200000
    assert result['groups']['candidate_first']['pairs'] == 32
    assert result['release_accepted'] is False


@pytest.mark.parametrize('change', [
    lambda s: '\n'.join(s.splitlines()[1:]),
    lambda s: s+'\n'+s.splitlines()[-1],
    lambda s: s.replace('frame=120', 'frame=119'),
    lambda s: s.replace('original_first=1', 'original_first=0', 1),
    lambda s: s.replace('vertices=50000', 'vertices=0', 1),
    lambda s: s.replace('reuse=1', 'reuse=0'),
    lambda s: s.replace('candidate_ms=0.4', 'candidate_ms=0', 1),
    lambda s: s.replace('candidate_ms=0.4', 'candidate_ms=1e999', 1),
    lambda s: s.replace('candidate_ms=0.4', 'candidate_ms=nan', 1),
    lambda s: s+'\nRENDER_VALUES_PAIR malformed',
])
def test_invalid_evidence_rejected(change):
    with pytest.raises(ValueError):
        summarize(change(capture()))


def test_mismatch_and_order_sensitive_speedup_fail():
    assert not summarize(capture().replace('exact=1', 'exact=0', 1))['exact']
    rows = capture().splitlines()
    rows[1::2] = [r.replace('candidate_ms=0.4', 'candidate_ms=1.3') for r in rows[1::2]]
    assert not summarize('\n'.join(rows))['measured_both_orders_faster']


def test_rebuild_rows_retained():
    result = summarize(capture().replace('frame=120 original_first=1 reuse=1', 'frame=120 original_first=1 reuse=0'))
    assert result['groups']['all']['pairs'] == 64
    assert result['groups']['reuse_original_first']['pairs'] == 31
