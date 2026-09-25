import pytest
from audit_mixed_cap_view_targets import triangle_key


def test_reindexing_preserves_direction_but_not_reversal_or_height():
    a=[(0.,0.,0.),(1.,0.,0.),(0.,1.,0.)]
    assert triangle_key(a)==triangle_key(a[1:]+a[:1])
    assert triangle_key(a)!=triangle_key(a[::-1])
    assert triangle_key(a)!=triangle_key([a[0],a[1],(0.,1.,1e-12)])


def test_nonfinite_rejected():
    with pytest.raises(ValueError):triangle_key([(0,0,0),(1,0,0),(0,1,float('nan'))])
