import pytest

from audit_crest_unused_faces import summarize


def capture():
    return '\n'.join(f'CrestUnusedFaceAudit frame={i} exact=1 candidate_first={i%2} vertices=50000 triangles=90000 reference_ms=0.5 candidate_ms=0.2' for i in range(120,184))


def test_complete_exact_both_orders():
    report = summarize(capture())
    assert report['exact'] and report['measured_both_orders_faster']
    assert report['compared_vertices'] == 64*50000
    assert report['groups']['candidate_first']['pairs'] == 32
    assert report['release_accepted'] is False


@pytest.mark.parametrize('change', [
    lambda s: '\n'.join(s.splitlines()[1:]),
    lambda s: s+'\n'+s.splitlines()[-1],
    lambda s: s.replace('frame=120', 'frame=119'),
    lambda s: s.replace('candidate_first=0', 'candidate_first=1', 1),
    lambda s: s.replace('triangles=90000', 'triangles=0', 1),
    lambda s: s.replace('vertices=50000', 'vertices=0', 1),
    lambda s: s.replace('candidate_ms=0.2', 'candidate_ms=0', 1),
    lambda s: s.replace('candidate_ms=0.2', 'candidate_ms=1e999', 1),
    lambda s: s.replace('candidate_ms=0.2', 'candidate_ms=nan', 1),
])
def test_incomplete_or_invalid_evidence_rejected(change):
    with pytest.raises(ValueError):
        summarize(change(capture()))


def test_mismatch_and_order_sensitive_speedup_fail_separately():
    assert not summarize(capture().replace('exact=1', 'exact=0', 1))['exact']
    lines = capture().splitlines()
    lines[1::2] = [line.replace('candidate_ms=0.2', 'candidate_ms=0.6') for line in lines[1::2]]
    report = summarize('\n'.join(lines))
    assert report['exact']
    assert not report['measured_both_orders_faster']
