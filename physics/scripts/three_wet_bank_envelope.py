"""Exact-rational reference for a conservative three-wet bank envelope.

This produces proof geometry, not engine delivery or a physical water solver.
No depth tolerance is used. Inconclusive certificates fail closed. The positive
width is a local-coordinate L1 boundary error bound, not a wet-depth floor.
For a world mapping P + x*X + y*Y, choose width <= .1/max(|X|,|Y|)
with X,Y in centimetres to bound the physical boundary band to one millimetre.
"""
from fractions import Fraction as F

def add(a,b):
    c=dict(a)
    for k,v in b.items():c[k]=c.get(k,F(0))+v
    return c
def scale(a,s):return {k:v*s for k,v in a.items()}
def mul(a,b):
    c={}
    for i,u in a.items():
        for j,v in b.items():
            k=tuple(x+y for x,y in zip(i,j));c[k]=c.get(k,F(0))+u*v
    return c
def linear(values):return {tuple(int(i==j) for i in range(3)):v for j,v in enumerate(values)}
ONE=linear((F(1),)*3)
ONE2=mul(ONE,ONE)

def coefficients(B,H,tri):
    # Canonical dry corner is (0,0), the other corners are (1,0),(0,1),(1,1).
    x=linear(tuple(p[0] for p in tri));y=linear(tuple(p[1] for p in tri))
    nx=add(ONE,scale(x,-1));ny=add(ONE,scale(y,-1))
    weights=(mul(nx,ny),mul(x,ny),mul(nx,y),mul(x,y))
    wet,drop={},{}
    for i in (1,2,3):
        wet=add(wet,scale(weights[i],H[i]))
        drop=add(drop,scale(weights[i],B[0]-B[i]))
    return add(mul(wet,ONE2),scale(mul(weights[0],drop),-1))

def certificate(B,H,tri,sign,remaining=9):
    # Homogeneous power coefficients / positive multinomial factors are
    # Bernstein coefficients. Their signs certify the ENTIRE triangle.
    if sign not in (-1,1):raise ValueError('Certificate sign must be wet or dry')
    cs=coefficients(B,H,tri)
    if all(sign*v>=0 for v in cs.values()):return True
    if remaining==0:return False
    a,b,c=tri
    ab=tuple((x+y)/2 for x,y in zip(a,b));bc=tuple((x+y)/2 for x,y in zip(b,c));ca=tuple((x+y)/2 for x,y in zip(c,a))
    return all(certificate(B,H,t,sign,remaining-1) for t in ((a,ab,ca),(ab,b,bc),(ca,bc,c),(ab,bc,ca)))

def value(B,H,p):
    x,y=p;w=((1-x)*(1-y),x*(1-y),(1-x)*y,x*y)
    return sum(w[i]*(H[i]-w[0]*(B[0]-B[i])) for i in (1,2,3))

def root(B,H,t):
    if t==0:return 1-H[1]/(B[0]-B[1]),F(0)
    if t==1:return F(0),1-H[2]/(B[0]-B[2])
    x,y=1-t,t
    largest=max(x,y);x/=largest;y/=largest
    lo,hi=F(0),F(1)
    for _ in range(64):
        mid=(lo+hi)/2
        if value(B,H,(x*mid,y*mid))>=0:hi=mid
        else:lo=mid
    return x*hi,y*hi

def build(B,H,width=F(1,1000)):
    # L1 displacement bounds Euclidean displacement on a one-metre square.
    if len(B)!=4 or len(H)!=4:raise ValueError('Four original bed/depth corners required')
    B,H=tuple(map(F,B)),tuple(map(F,H));width=F(width)
    if not 0<width<1:raise ValueError('Positive geometric width below one cell required')
    if H[0]!=0 or any(H[i]<=0 or B[0]<=B[i]+H[i] for i in (1,2,3)):
        raise ValueError('Exactly one high dry corner and three positive donors required')
    origin=(F(0),F(0));anchor=(F(1),F(1))
    def point(t):
        r=root(B,H,t)
        direction=(1-t,t)
        advance=min([width/2]+[(1-v)/(2*d) for v,d in zip(r,direction) if d])
        return r if t in (0,1) else tuple(v+advance*d for v,d in zip(r,direction))
    def inner(p):return tuple(v*max(F(0),1-width/sum(p)) for v in p)
    def interval(p,q):
        return certificate(B,H,(p,q,q),1) and certificate(B,H,(origin,inner(p),inner(q)),-1)
    points=[point(F(0))];stack=[(F(0),F(1),0)]
    while stack:
        a,b,level=stack.pop();p,q=point(a),point(b)
        if interval(p,q):
            points.append(q);continue
        if level>=16:raise ValueError(f'No certified envelope at {a},{b}')
        mid=(a+b)/2;stack.extend(((mid,b,level+1),(a,mid,level+1)))
    if not all(0<=v<=1 for p in points for v in p):raise ValueError('Envelope left original cell')
    initial_segments=len(points)-1
    # Dyadic construction is an initial bracket, not a mandate to keep surplus
    # nodes. Only remove a node when the SAME full wet/dry proofs hold.
    i=1
    while i<len(points)-1:
        if interval(points[i-1],points[i+1]):del points[i];i=max(1,i-1)
        else:i+=1
    polygon=[anchor,(F(1),F(0)),*points,(F(0),F(1))]
    def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    triangles=[]
    while len(polygon)>3:
        found=False
        for i,b in enumerate(polygon):
            a=polygon[i-1];c=polygon[(i+1)%len(polygon)]
            if cross(a,b,c)>=0:continue
            if any(all(cross(p,q,r)<=0 for p,q in ((a,b),(b,c),(c,a)))
                   for j,r in enumerate(polygon) if j not in ((i-1)%len(polygon),i,(i+1)%len(polygon))):continue
            if not certificate(B,H,(a,b,c),1):continue
            triangles.append((a,b,c));del polygon[i];found=True;break
        if not found:raise ValueError(f'No wet-certified ear; {len(polygon)} remain')
    if not certificate(B,H,tuple(polygon),1):raise ValueError('Final wet triangle unproved')
    triangles.append(tuple(polygon))
    dry=tuple((origin,inner(p),inner(q)) for p,q in zip(points,points[1:]))
    # Every band vertex lies at L1 distance <= width from its corresponding
    # outer segment endpoint. By convexity the complete intervening strip is
    # within that distance of the outer segment. Dry triangles cover the rest
    # of the omitted corner; certified ears cover the retained wet polygon.
    if not all(sum(abs(a-b) for a,b in zip(p,inner(p)))<=width for p in points):
        raise ValueError('Geometric band bound unproved')
    return dict(points=tuple(points),wet_triangles=tuple(triangles),dry_triangles=dry,
                inner_points=tuple(inner(p) for p in points),width=width,
                initial_segments=initial_segments,segments=len(points)-1,
                runtime_integrated=False,performance_accepted=False)
