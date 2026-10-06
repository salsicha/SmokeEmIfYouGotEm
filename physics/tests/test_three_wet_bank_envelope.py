"""Reference geometry proofs; these do not accept native/gameplay behaviour."""
from fractions import Fraction as F
from random import Random
import struct
import pytest
from three_wet_bank_envelope import build,certificate,coefficients,root,value

def binary32(x):return F(struct.unpack('f',struct.pack('f',x))[0])

def captured():
    # v22 same-call contact bff4c53b8ad86c0003b40036862ae8c0e8e6aeb3a2e238e5e70ab0ff4dd2b74f.
    # Reflect x to place original dry corner1 at canonical corner0.
    B=tuple(map(binary32,[8.711944580078125,8.45587158203125,8.534469604492188,8.397781372070312]))
    H=tuple(map(binary32,[0,.061720576137304306,.17600621283054352,.16925844550132751]))
    return B,H

def independent_numerator(B,H,p):
    x,y=p;w=((1-x)*(1-y),x*(1-y),(1-x)*y,x*y)
    wet_weight=sum(w[1:]);bed=sum(a*b for a,b in zip(w,B))
    return sum(w[i]*(B[i]+H[i]) for i in (1,2,3))-wet_weight*bed

def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])

def contains(tri,p):
    c=[cross(a,b,p) for a,b in zip(tri,(*tri[1:],tri[0]))]
    return all(v>=0 for v in c) or all(v<=0 for v in c)

def check(B,H,result):
    assert result['runtime_integrated'] is result['performance_accepted'] is False
    assert result['segments']<=result['initial_segments']
    assert result['points'][0]==(1-H[1]/(B[0]-B[1]),0)
    assert result['points'][-1]==(0,1-H[2]/(B[0]-B[2]))
    for tri in result['wet_triangles']:
        assert cross(*tri)<0
        assert certificate(B,H,tri,1)
    for tri in result['dry_triangles']:assert certificate(B,H,tri,-1)
    for p,q in zip(result['points'],result['inner_points']):
        assert sum(abs(a-b) for a,b in zip(p,q))<=result['width']
    # Polygon partition area: wet + omitted dry + boundary band is one cell.
    wet=sum(-cross(*t)/2 for t in result['wet_triangles'])
    omitted=sum(cross((0,0),p,q)/2 for p,q in zip(result['points'],result['points'][1:]))
    dry=sum(cross(*t)/2 for t in result['dry_triangles'])
    assert wet+omitted==1 and 0<=dry<=omitted

def test_captured_finite_chords_and_anchor_shortcut_really_enter_dry_ground():
    B,H=captured();roots=[root(B,H,F(i,16)) for i in range(17)]
    assert min(independent_numerator(B,H,tuple((a+b)/2 for a,b in zip(p,q)))
               for p,q in zip(roots,roots[1:]))<0
    r=root(B,H,F(3,4));p=tuple(v*(1-F(9,1000))+F(9,1000) for v in r)
    assert independent_numerator(B,H,p)<0
    assert not certificate(B,H,((F(1),F(1)),r,r),1)

def test_complete_captured_wet_and_dry_envelope():
    B,H=captured();result=build(B,H);check(B,H,result)
    # Original (.9013296732491654,.12234552688732947) reflected in x.
    p=(1-F(.9013296732491654),F(.12234552688732947))
    assert independent_numerator(B,H,p)<0
    assert not any(contains(t,p) for t in result['wet_triangles'])
    assert any(contains(t,p) for t in result['dry_triangles'])
    assert result['segments']<69  # Certified simplification, not a runtime budget.

def test_bernstein_polynomial_matches_independent_original_sampler_exactly():
    B,H=captured();rng=Random(2109)
    for _ in range(32):
        tri=tuple(tuple(F(rng.randrange(101),100) for _ in range(2)) for _ in range(3))
        a,b=F(rng.randrange(101),100),F(rng.randrange(101),100)
        bary=(a,(1-a)*b,(1-a)*(1-b))
        p=tuple(sum(bary[i]*tri[i][axis] for i in range(3)) for axis in (0,1))
        got=sum(v*bary[0]**k[0]*bary[1]**k[1]*bary[2]**k[2]
                for k,v in coefficients(B,H,tri).items())
        assert got==independent_numerator(B,H,p)==value(B,H,p)

@pytest.mark.parametrize('case',range(8))
def test_varied_high_banks_have_whole_triangle_certificates(case):
    rng=Random(777+case)
    B=(F(10),*(F(rng.randrange(-20,80),10) for _ in range(3)))
    H=(F(0),*(F(rng.randrange(1,99),100)*(B[0]-b) for b in B[1:]))
    check(B,H,build(B,H))

def test_v18_original_captured_bank():
    # Original dry corner2 -> canonical0; preserve binary32 native input.
    B=tuple(map(binary32,[9.9083251953125,7.7048187255859375,7.243682861328125,7.27630615234375]))
    H=tuple(map(binary32,[0,.2190435528755188,.5688362717628479,.492604672908783]))
    check(B,H,build(B,H))

def test_thin_positive_donors_not_floored():
    B=(F(2),F(0),F(0),F(0));H=(F(0),F(1,10**8),F(1),F(1))
    result=build(B,H);check(B,H,result)
    assert result['points'][0][0]==1-F(1,2*10**8)

def test_invalid_geometry_rejected():
    B,H=captured()
    for width in (0,-1,1):
        with pytest.raises(ValueError):build(B,H,width)
    for bad in ((F(1,10**12),*H[1:]),(0,0,*H[2:]),(0,-1,*H[2:])):
        with pytest.raises(ValueError):build(B,bad)
    with pytest.raises(ValueError):build(B[:3],H)
    with pytest.raises(ValueError):build((0,*B[1:]),H)
    with pytest.raises(ValueError):certificate(B,H,((0,0),(1,0),(1,1)),0)

def test_datum_and_vertical_unit_invariance():
    B,H=captured();reference=build(B,H)
    assert build(tuple(b+F(400000,7) for b in B),H)==reference
    assert build(tuple(b*100 for b in B),tuple(h*100 for h in H))==reference

def test_physical_band_under_rotation_reflection_shear_and_scale():
    B,H=captured();result=build(B,H)
    for x,y in (((60,80),(-80,60)),((100,0),(60,-80)),((0,-100),(-100,0))):
        for p,q in zip(result['points'],result['inner_points']):
            d=tuple(p[i]-q[i] for i in (0,1))
            world=tuple(x[i]*d[0]+y[i]*d[1] for i in (0,1))
            assert sum(v*v for v in world)<=F(1,100)
    # A five-metre source cell uses a stricter local width, not a looser world gate.
    larger=build(B,H,F(1,5000))
    for p,q in zip(larger['points'],larger['inner_points']):
        assert sum((500*(a-b))**2 for a,b in zip(p,q))<=F(1,100)
