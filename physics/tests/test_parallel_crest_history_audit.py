import pytest

from audit_parallel_crest_history import summarize


def rows():
    return [f'ParallelCrestHistoryPair frame={i} exact=1 candidate_first={(i//2)%2} dense={i%2} vertices=65536 reference_ms=2.0 candidate_ms=1.0'
            for i in range(120, 184)]


def test_both_orders_for_each_state_and_complete_rows():
    result = summarize('\n'.join(rows()))
    assert result['exact_pairs'] == 64 and result['faster_in_both_states_and_orders']
    assert all(g['pairs'] == 16 for g in result['groups'])
    assert not result['gameplay_or_performance_accepted']


@pytest.mark.parametrize('kind', ('missing', 'duplicate', 'reversed', 'mismatch', 'zero', 'infinite', 'negative', 'order', 'state', 'malformed', 'hidden_error'))
def test_invalid_pairs_fail_closed(kind):
    data = rows()
    if kind == 'missing': data.pop()
    elif kind == 'duplicate': data.append(data[-1])
    elif kind == 'reversed': data.reverse()
    elif kind == 'mismatch': data[0] = data[0].replace('exact=1', 'exact=0')
    elif kind == 'zero': data[0] = data[0].replace('reference_ms=2.0', 'reference_ms=0')
    elif kind == 'infinite': data[0] = data[0].replace('candidate_ms=1.0', 'candidate_ms=inf')
    elif kind == 'negative': data[0] = data[0].replace('candidate_ms=1.0', 'candidate_ms=-1')
    elif kind == 'order': data[0] = data[0].replace('candidate_first=0', 'candidate_first=1')
    elif kind == 'state': data = [r.replace('dense=1', 'dense=0') for r in data]
    elif kind == 'malformed': data[0] += ' unexpected=1'
    else: data.append('ParallelCrestHistory mismatch frame=77')
    with pytest.raises(ValueError): summarize('\n'.join(data))


def test_one_regressing_state_order_cannot_be_hidden_by_overall_mean():
    data = rows()
    data = [r.replace('candidate_ms=1.0', 'candidate_ms=2.1') if 'dense=1' in r and 'candidate_first=1' in r else r for r in data]
    result = summarize('\n'.join(data))
    assert not result['faster_in_both_states_and_orders']


def test_mapped_only_dispatch_preserves_dense_serial_and_keeps_all_timings():
    data = [r+f' parallel_used={1-i%2}' for i, r in zip(range(120, 184), rows())]
    result = summarize('\n'.join(data))
    assert result['mapped_only_dispatch_verified'] and result['changed_path_faster_in_both_orders']
    assert len(result['groups']) == 4 and len(result['rows']) == 64
    bad = list(data)
    bad[1] = bad[1].replace('parallel_used=0', 'parallel_used=1')
    with pytest.raises(ValueError, match='serial dense'): summarize('\n'.join(bad))
    with pytest.raises(ValueError, match='policy'): summarize('\n'.join(data[:-1]+rows()[-1:]))
