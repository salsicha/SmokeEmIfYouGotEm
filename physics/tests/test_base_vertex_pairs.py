import pytest

from audit_base_vertex_pairs import summarize


def lines(step=2):
    return [f'LogTemp: BaseVertexAudit frame={frame} pair={i+1} exact=1 candidate_first={i%2} vertices=50000 wet=32000 reference_ms=2.9 candidate_ms=1.4'
            for i, frame in enumerate(range(120, 184, step))]


@pytest.mark.parametrize('step', (1, 2))
def test_both_refresh_rates_and_orders(step):
    result = summarize('\n'.join(lines(step)))
    assert result['exact_pairs'] == 64//step
    assert result['faster_in_both_orders']
    assert not result['gameplay_or_performance_accepted']


@pytest.mark.parametrize('change', ('missing', 'duplicate', 'reverse', 'mismatch', 'order', 'wet', 'count', 'zero', 'nan', 'partial', 'error'))
def test_incomplete_or_nonexact_evidence_rejected(change):
    rows = lines()
    if change == 'missing': rows.pop(5)
    elif change == 'duplicate': rows.insert(5, rows[5])
    elif change == 'reverse': rows.reverse()
    elif change == 'partial': rows.pop()
    elif change == 'error': rows.append('BaseVertexAudit state mismatch; candidate not qualified')
    else:
        old, new = dict(mismatch=('exact=1', 'exact=0'), order=('candidate_first=0', 'candidate_first=1'),
                        wet=('wet=32000', 'wet=0'), count=('vertices=50000', 'vertices=100'),
                        zero=('reference_ms=2.9', 'reference_ms=0'), nan=('candidate_ms=1.4', 'candidate_ms=nan'))[change]
        rows[0] = rows[0].replace(old, new)
    with pytest.raises(ValueError):
        summarize('\n'.join(rows))


def test_exact_but_slower_is_not_a_speed_pass():
    result = summarize('\n'.join(lines()).replace('candidate_ms=1.4', 'candidate_ms=3.1'))
    assert result['exact_pairs'] == 32
    assert not result['faster_in_both_orders']


def test_command_line_is_not_a_native_comparison_row():
    result = summarize('Command line: -RaftSimBaseVertexAudit\n'+'\n'.join(lines()))
    assert result['exact_pairs'] == 32
