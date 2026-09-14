import pytest
from audit_crest_region_profile import audit


def row(f,a=3.,b=2.):
    return f'CrestRegionAudit exact frame={f} regions=10 vertices=300 triangles=500 linear_ms={a} indexed_ms={b} indexed_first={f%2}'


def test_complete_duplicate_and_unchanged_calls_retained():
    r=audit('\n'.join([row(120),row(121),row(121,4,2),'CrestRegionAudit unchanged frame=122']),120,122)
    assert r['frames']==3 and r['build_calls']==3 and r['unchanged_calls']==1
    assert r['exact_expanded_vertices']==900 and r['exact_triangles']==1500
    assert r['per_frame']['linear_ms']['maximum']==7
    assert not r['ordinary_fps_accepted']


@pytest.mark.parametrize('log',[
    row(120),row(120)+'\n'+row(121)+'\nCrestRegionAudit mismatch frame=500',
    row(120)+'\n'+row(121).replace('indexed_ms=2.0','indexed_ms=nan'),
    row(120)+'\n'+row(121).replace('indexed_first=1','indexed_first=0'),
    row(120)+'\nCrestRegionAudit exact broken',
    row(120)+'\nCrestRegionAudit unchanged broken',
    'CrestRegionAudit unchanged frame=120\nCrestRegionAudit unchanged frame=121',
    (row(120)+'\n'+row(121)).replace('regions=10','regions=0'),
])
def test_incomplete_or_invalid_evidence_rejected(log):
    with pytest.raises(ValueError):audit(log,120,121)
