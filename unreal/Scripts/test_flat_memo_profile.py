import pytest
from audit_flat_memo_profile import audit


def row(f, a=3., b=2.):
    return (f'FlatMemoAudit exact frame={f} vertices=300 triangles=500 map_ms={a} '
            f'flat_ms={b} flat_first={f%2} map_bytes=1024 flat_bytes=900')


def test_duplicate_and_unchanged_calls_are_retained():
    r = audit('\n'.join([row(120), row(121), row(121, 4, 2), 'FlatMemoAudit unchanged frame=122']), 120, 122)
    assert r['build_calls'] == 3 and r['unchanged_calls'] == 1
    assert r['exact_vertices'] == 900 and r['exact_triangles'] == 1500
    assert not r['ordinary_fps_accepted'] and not r['visual_or_physics_accepted']


@pytest.mark.parametrize('log', [
    row(120), row(120)+'\n'+row(121)+'\nFlatMemoAudit mismatch frame=500',
    row(120)+'\n'+row(121).replace('flat_ms=2.0', 'flat_ms=nan'),
    row(120)+'\n'+row(121).replace('flat_first=1', 'flat_first=0'),
    row(120)+'\nFlatMemoAudit exact broken', row(120)+'\nFlatMemoAudit unchanged broken',
    'FlatMemoAudit unchanged frame=120\nFlatMemoAudit unchanged frame=121',
    (row(120)+'\n'+row(121)).replace('flat_bytes=900', 'flat_bytes=0'),
])
def test_invalid_or_incomplete_evidence_rejected(log):
    with pytest.raises(ValueError):
        audit(log, 120, 121)
