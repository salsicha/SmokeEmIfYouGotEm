import pytest
from pathlib import Path
from audit_incremental_crest_history import summarize


def capture():
    return '\n'.join(f'IncrementalCrestHistoryAudit frame={i} exact=1 candidate_first={i%2} dense={int(i%3!=0)} incremental={int(i%3==0)} changed={10 if i%3==0 else 0} vertices=60000 reference_ms=0.7 candidate_ms=0.3' for i in range(120, 184))


def test_complete_exact_moving_history():
    report = summarize(capture())
    assert report['exact'] and report['measured_both_orders_faster']
    assert report['groups']['incremental']['calls'] == 22
    assert report['groups']['reference_first']['calls'] == 32
    assert not report['release_accepted'] and not report['visual_accepted']


@pytest.mark.parametrize('change', [
    lambda s: '\n'.join(s.splitlines()[1:]),
    lambda s: s+'\n'+s.splitlines()[-1],
    lambda s: s.replace('candidate_first=0', 'candidate_first=1', 1),
    lambda s: s.replace('candidate_ms=0.3', 'candidate_ms=nan', 1),
    lambda s: s.replace('candidate_ms=0.3', 'candidate_ms=inf', 1),
    lambda s: s.replace('candidate_ms=0.3', 'candidate_ms=0', 1),
    lambda s: s.replace('dense=0 incremental=1', 'dense=1 incremental=1', 1),
    lambda s: s.replace('changed=10', 'changed=60001', 1),
    lambda s: s.replace('vertices=60000', 'vertices=0', 1),
    lambda s: s.replace('incremental=1', 'incremental=0'),
    lambda s: s+'\nIncrementalCrestHistoryAudit mismatch frame=42',
])
def test_bad_evidence_rejected(change):
    with pytest.raises(ValueError):
        summarize(change(capture()))


def test_exactness_and_both_order_benefit_are_independent():
    assert not summarize(capture().replace('exact=1', 'exact=0', 1))['exact']
    lines = capture().splitlines()
    lines[1::2] = [line.replace('candidate_ms=0.3', 'candidate_ms=0.8') for line in lines[1::2]]
    report = summarize('\n'.join(lines))
    assert report['exact'] and not report['measured_both_orders_faster']


def test_rejected_candidate_cannot_publish_gameplay_vertices():
    source = (Path(__file__).resolve().parents[2] / 'unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimShorelineCrests.cpp').read_text()
    assert 'TEXT("RaftSimIncrementalCrestHistory")' not in source
    assert 'Vertices=MoveTemp(CandidateVertices)' not in source
    assert source.count('IncrementalCorrectionHistory.Apply(') == 1
    diagnostic = source[source.index('if(bIncrementalAudit)'):source.index('else if(bHistoryHashAudit)')]
    assert 'IncrementalCorrectionHistory.Apply(' in diagnostic
    assert 'CorrectionHistory.Apply(Vertices,' in diagnostic
