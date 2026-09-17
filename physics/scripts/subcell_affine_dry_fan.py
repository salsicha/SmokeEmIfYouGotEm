"""Finite-time homogeneous dry-front solution on ONE original affine bed.

The shallow-water rarefaction is evaluated in an accelerating frame:
X=x+g*grad(b)*t^2/2, u=U-g*grad(b)*t. Original uniform wet depth and velocity
occupy N.(x-origin)<0 initially; the other half-plane is dry. N need not be
normalized. This is NOT the spatially varying inlet, a source-slope junction,
dispersive pressure, or the complete coupled river evolution.

Q(sqrt(g*h*|N|^2)) retains original rational depth/geometry without rounding a
wave speed or deleting positive sub-float fragments. Exact arithmetic does not
increase captured-source precision. Polygon budgets include both donor/fan
states and original bed potential, not a separately prescribed energy update.
"""
from fractions import Fraction as F
from math import factorial, isqrt
from functools import lru_cache

from subcell_exact_geometry import SourceFragment
from subcell_inlet_contact_time import _sqrt_bounds


@lru_cache(maxsize=128)
def _rational_root(d):
    n,q=isqrt(d.numerator),isqrt(d.denominator)
    return F(n,q) if n*n==d.numerator and q*q==d.denominator else None


class Radical:
    """One real quadratic field; rational-square fields reduce immediately."""
    def __init__(self, d, a=0, b=0):
        self.d, self.a, self.b = F(d), F(a), F(b)
        if self.d <= 0:
            raise ValueError('Positive radicand required')
        root=_rational_root(self.d)
        if root is not None:
            self.a += self.b*root
            self.b = F(0)

    def _other(self, value):
        if isinstance(value, Radical):
            if value.d != self.d:
                raise ValueError('Different quadratic fields')
            return value
        return Radical(self.d, value)

    def __add__(self, value):
        v=self._other(value)
        return Radical(self.d,self.a+v.a,self.b+v.b)
    __radd__=__add__
    def __neg__(self): return Radical(self.d,-self.a,-self.b)
    def __sub__(self, value): return self+-self._other(value)
    def __rsub__(self, value): return self._other(value)+-self
    def __mul__(self, value):
        v=self._other(value)
        return Radical(self.d,self.a*v.a+self.b*v.b*self.d,self.a*v.b+self.b*v.a)
    __rmul__=__mul__
    def __truediv__(self, value):
        v=self._other(value)
        denominator=v.a*v.a-v.b*v.b*self.d
        if denominator == 0: raise ZeroDivisionError('Zero algebraic divisor')
        return self*Radical(self.d,v.a/denominator,-v.b/denominator)
    def __rtruediv__(self, value): return self._other(value)/self
    def __eq__(self, value):
        v=self._other(value)
        return self.a==v.a and self.b==v.b
    def sign(self):
        if self.a == 0: return (self.b>0)-(self.b<0)
        if self.b == 0 or (self.a>0)==(self.b>0): return (self.a>0)-(self.a<0)
        v=self.a*self.a-self.b*self.b*self.d
        return ((v>0)-(v<0))*((self.a>0)-(self.a<0))
    def __lt__(self, value): return (self-value).sign()<0
    def __le__(self, value): return (self-value).sign()<=0
    def __gt__(self, value): return (self-value).sign()>0
    def __ge__(self, value): return (self-value).sign()>=0
    def __float__(self):
        # Presentation only; predicates/integrals never use this conversion.
        # Round an enclosure rather than overflowing/underflowing a radicand
        # first or subtracting separately rounded, nearly equal large terms.
        if self.b==0:return float(self.a)
        for bits in (64,128,256,512,1024,2048,4096):
            bounds=[self.a+self.b*r for r in _sqrt_bounds(self.d,bits)]
            a,b=map(float,bounds)
            if a==b:return a
        raise ValueError('Algebraic presentation rounding unresolved')
    def record(self): return dict(rational=self.a,radical_coefficient=self.b,radicand=self.d)


def _clip(polygon, value, positive):
    result=[]
    for a,b in zip(polygon,polygon[1:]+polygon[:1]):
        da,db=value(a),value(b)
        ia,ib=(da>=0,db>=0) if positive else (da<=0,db<=0)
        if ia: result.append(a)
        if ia != ib:
            result.append(tuple(x+(y-x)*da/(da-db) for x,y in zip(a,b)))
    unique=[]
    for p in result:
        if not unique or p!=unique[-1]: unique.append(p)
    if len(unique)>1 and unique[0]==unique[-1]: unique.pop()
    return tuple(unique)


def _integrate(triangle, forms, zero):
    """Integral of products of affine functions via simplex barycentric moments."""
    a,b,c=triangle
    twice_area=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    if twice_area<0: twice_area=-twice_area
    polynomial={(0,0,0):zero+1}
    for form in forms:
        values=[form(p) for p in triangle]
        product={}
        for exponent,coefficient in polynomial.items():
            for i,value in enumerate(values):
                key=tuple(n+int(j==i) for j,n in enumerate(exponent))
                product[key]=product.get(key,zero)+coefficient*value
        polynomial=product
    return twice_area*sum((coefficient*F(factorial(i)*factorial(j)*factorial(k),
                                            factorial(i+j+k+2))
                           for (i,j,k),coefficient in polynomial.items()),zero)


class AffineDryFan:
    def __init__(self, origin, normal, depth, velocity, bed_at_origin, gradient, gravity=F(981,100)):
        try:
            self.origin=tuple(map(F,origin)); self.normal=tuple(map(F,normal))
            self.velocity=tuple(map(F,velocity)); self.gradient=tuple(map(F,gradient))
            self.depth,self.bed,self.gravity=map(F,(depth,bed_at_origin,gravity))
        except (ValueError,TypeError,OverflowError) as exc:
            raise ValueError('Finite original rational state required') from exc
        if any(len(x)!=2 for x in (self.origin,self.normal,self.velocity,self.gradient)):
            raise ValueError('Two-dimensional vectors required')
        self.norm2=sum(n*n for n in self.normal)
        if self.norm2<=0 or self.depth<=0 or self.gravity<=0:
            raise ValueError('Positive wet depth, gravity and nonzero normal required')
        self.d=self.gravity*self.depth*self.norm2
        self.c=Radical(self.d,0,1); self.zero=Radical(self.d)
        self.un=sum(n*u for n,u in zip(self.normal,self.velocity))

    def _coordinate(self,p):
        return sum((n*(x-o) for n,x,o in zip(self.normal,p,self.origin)),self.zero)

    def _profile(self,time):
        t=F(time)
        if t<=0: raise ValueError('Positive finite fan time required')
        shift=self.gravity*sum(n*s for n,s in zip(self.normal,self.gradient))*t*t/2
        head=(self.un-self.c)*t-shift
        front=(self.un+2*self.c)*t-shift
        # L=un+2c-xi; h=L^2/(9*g*|N|^2).
        linear=lambda p:self.un+2*self.c-(self._coordinate(p)+shift)/t
        velocities=tuple((lambda p,j=j:self.velocity[j]-self.un*self.normal[j]/self.norm2
            +self.normal[j]*(self.un+2*self.c+2*(self._coordinate(p)+shift)/t)/(3*self.norm2)
            -self.gravity*self.gradient[j]*t) for j in range(2))
        wet_velocity=tuple(u-self.gravity*s*t for u,s in zip(self.velocity,self.gradient))
        return head,front,linear,velocities,wet_velocity

    def state(self,point,time):
        p=tuple(map(F,point)); t=F(time)
        if len(p)!=2 or t<0: raise ValueError('Two-dimensional point and nonnegative time required')
        q=self._coordinate(p)
        if t==0:
            return (self.zero+self.depth,tuple(self.zero+u for u in self.velocity)) if q<0 else (self.zero,(self.zero,self.zero))
        head,front,linear,velocity,wet=self._profile(t)
        if q<=head: return self.zero+self.depth,tuple(self.zero+u for u in wet)
        if q>=front: return self.zero,(self.zero,self.zero)
        return linear(p)*linear(p)/(9*self.gravity*self.norm2),tuple(u(p) for u in velocity)

    def integrate(self,fragment,time,*,energy_datum=0):
        """Conserved budgets on a fixed ORIGINAL polygon, at a physical time.

        Dry polygons remain zero. Positive algebraic slivers are not rounded
        through exported vertices. Crossing a different bed slope is rejected;
        adjacent source triangles on the SAME plane may be integrated separately.
        """
        t,datum=F(time),F(energy_datum)
        if t<0 or not isinstance(fragment,SourceFragment) or fragment.area<=0:
            raise ValueError('Original positive source polygon and nonnegative time required')
        if tuple(map(F,fragment.gradient))!=self.gradient or any(
            F(z)!=self.bed+sum(s*(F(x)-o) for s,x,o in zip(self.gradient,(x,y),self.origin))
            for x,y,z in fragment.polygon):
            raise ValueError('Fan cannot cross a different original affine bed')
        original=fragment.polygon
        cross=lambda a,b:a[0]*b[1]-a[1]*b[0]
        orientation=sum(cross(a,b) for a,b in zip(original,original[1:]+original[:1]))
        sign=1 if orientation>0 else -1
        if orientation==0 or any(sign*cross((b[0]-a[0],b[1]-a[1]),(p[0]-a[0],p[1]-a[1]))<0
                for a,b in zip(original,original[1:]+original[:1]) for p in original):
            raise ValueError('Convex original affine polygon required')
        polygon=tuple(tuple(self.zero+F(x) for x in p) for p in fragment.polygon)
        if t==0:
            parts=[(_clip(polygon,self._coordinate,False),'wet')]
            wet=self.velocity
        else:
            head,front,linear,velocity,wet=self._profile(t)
            parts=[(_clip(polygon,lambda p:self._coordinate(p)-head,False),'wet'),
                   (_clip(_clip(polygon,lambda p:self._coordinate(p)-head,True),
                          lambda p:self._coordinate(p)-front,False),'fan')]
        mass=self.zero; momentum=[self.zero,self.zero]; energy=self.zero
        for poly,branch in parts:
            for i in range(1,len(poly)-1):
                tri=(poly[0],poly[i],poly[i+1])
                if branch=='wet':
                    coefficient=self.depth; forms=[]
                    speed=tuple((lambda p,u=u:self.zero+u) for u in wet)
                else:
                    coefficient=F(1,9)/(self.gravity*self.norm2); forms=[linear,linear]; speed=velocity
                m=coefficient*_integrate(tri,forms,self.zero)
                mass+=m
                for j in range(2):
                    momentum[j]+=coefficient*_integrate(tri,forms+[speed[j]],self.zero)
                    energy+=coefficient/2*_integrate(tri,forms+[speed[j],speed[j]],self.zero)
                energy+=self.gravity*coefficient*coefficient/2*_integrate(tri,forms+forms,self.zero)
                energy+=self.gravity*coefficient*_integrate(tri,forms+[lambda p:p[2]-datum],self.zero)
        if mass<0: raise ValueError('Negative exact fan mass')
        return dict(volume=mass,momentum=tuple(momentum),energy_per_density=energy,
                    bed_force=tuple(-self.gravity*s*mass for s in self.gradient),
                    source_id=fragment.source_id,time=t,
                    spatially_varying_or_dispersive_or_gameplay_accepted=False)
