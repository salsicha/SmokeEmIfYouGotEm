import pytest
from audit_compact_crest_source import summarize


def lines():
    return [f'LogTemp: CompactCrestSourcePair frame={i} exact=1 candidate_first={(i//2)%2} source=51000 compact=13000 indices=60000 reference_ms=10.0 candidate_ms=6.0'
            for i in range(120,184)]


def test_complete_ordered_pairs():
    r = summarize('Command line: -RaftSimCompactCrestSourceAudit\n'+'\n'.join(lines()))
    assert r['exact_pairs'] == 64 and r['faster_in_both_orders']
    assert not r['performance_accepted'] and not r['visual_accepted']


@pytest.mark.parametrize('change', ('missing','duplicate','reverse','error','exact','order','count','indices','nan','zero','no_compaction'))
def test_invalid_capture_rejected(change):
    rows = lines()
    if change == 'missing': rows.pop(2)
    elif change == 'duplicate': rows.insert(2, rows[2])
    elif change == 'reverse': rows.reverse()
    elif change == 'error': rows.append('CompactCrestSource mismatch frame=140')
    elif change == 'no_compaction': rows = [r.replace('compact=13000','compact=51000') for r in rows]
    else:
        old,new = dict(exact=('exact=1','exact=0'), order=('candidate_first=0','candidate_first=1'),
                       count=('compact=13000','compact=51001'), indices=('indices=60000','indices=59999'),
                       nan=('candidate_ms=6.0','candidate_ms=nan'), zero=('reference_ms=10.0','reference_ms=0'))[change]
        rows[0] = rows[0].replace(old,new)
    with pytest.raises(ValueError): summarize('\n'.join(rows))


def test_exact_slow_candidate_not_speedup():
    r = summarize('\n'.join(lines()).replace('candidate_ms=6.0','candidate_ms=12.0'))
    assert not r['faster_in_both_orders']
