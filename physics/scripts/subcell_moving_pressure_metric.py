"""Original two-pole physical/canonical metric on evolving source geometry.

M is the actual volume mass matrix and C the unnormalised pressure kinetic
form. With R=sqrt(M), Q=R^-1 C R^-1, the ORIGINAL response is
S=cI+sum(w_j*(I+lambda_j Q)^-1). Thus the physical map is
B=R S R=cM+sum(w_j*M*(M+lambda_j C)^-1*M).

This root-free reference preserves both mass normalizations and original
represented pole constants. Exact dense solves are component oracles, NOT
qualification of the native 40-CG implementation or a nonlinear evolution law.
"""
from fractions import Fraction as F

import numpy as np

from finite_depth_pressure_reference import LENGTHS, WEIGHTS
from subcell_affine_dry_fan import Radical


class PositiveSolve:
    """Exact symmetric LDL^T; reject nonpositive pivots, never regularize."""
    def __init__(self,matrix,zero,*,allow_semidefinite=False):
        self.zero=zero;n=len(matrix)
        if any(len(row)!=n for row in matrix):raise ValueError('Square pressure matrix required')
        if any(matrix[i][j]!=matrix[j][i] for i in range(n) for j in range(n)):
            raise ValueError('Symmetric physical pressure matrix required')
        self.lower=[[zero]*n for _ in range(n)];self.diagonal=[]
        for i in range(n):
            self.lower[i][i]=zero+1
            for j in range(i):
                remainder=matrix[i][j]-sum((self.lower[i][k]*self.diagonal[k]*self.lower[j][k]
                                            for k in range(j)),zero)
                if self.diagonal[j]==0:
                    if remainder!=0:raise ValueError('Indefinite pressure kinetic form')
                    self.lower[i][j]=zero
                else:self.lower[i][j]=remainder/self.diagonal[j]
            pivot=matrix[i][i]-sum((self.lower[i][k]*self.lower[i][k]*self.diagonal[k] for k in range(i)),zero)
            if pivot<0 or (pivot==0 and not allow_semidefinite):
                raise ValueError('Nonpositive physical pressure pivot; no mass floor')
            self.diagonal.append(pivot)

    def solve(self,rhs):
        n=len(self.diagonal)
        if len(rhs)!=n:raise ValueError('Pressure right-hand side shape mismatch')
        if any(d==0 for d in self.diagonal):raise ValueError('Singular pressure matrix cannot be inverted')
        y=[]
        for i in range(n):y.append(rhs[i]-sum((self.lower[i][j]*y[j] for j in range(i)),self.zero))
        x=[a/b for a,b in zip(y,self.diagonal)]
        for i in reversed(range(n)):
            x[i]-=sum((self.lower[j][i]*x[j] for j in range(i+1,n)),self.zero)
        return tuple(x)


class MovingPressureMetric:
    def __init__(self,volumes,volume_rates,kinetic,kinetic_rate):
        volumes,volume_rates=tuple(volumes),tuple(volume_rates)
        kinetic,kinetic_rate=tuple(map(tuple,kinetic)),tuple(map(tuple,kinetic_rate))
        n=2*len(volumes)
        if len(volume_rates)!=len(volumes) or any(len(a)!=n or any(len(row)!=n for row in a) for a in (kinetic,kinetic_rate)):
            raise ValueError('Matching volume and two-component pressure geometry required')
        values=(*volumes,*volume_rates,*(v for a in (kinetic,kinetic_rate) for row in a for v in row))
        radical=next((v for v in values if isinstance(v,Radical)),None)
        self.zero=Radical(radical.d) if radical is not None else F(0)
        self.mass=tuple(self.number(v) for v in volumes for _ in range(2))
        self.mass_rate=tuple(self.number(v) for v in volume_rates for _ in range(2))
        self.kinetic=tuple(tuple(self.number(v) for v in row) for row in kinetic)
        self.kinetic_rate=tuple(tuple(self.number(v) for v in row) for row in kinetic_rate)
        if any(v<=0 for v in self.mass):raise ValueError('Only positive active source volumes; no dry inverse mass')
        if any(a[i][j]!=a[j][i] for a in (self.kinetic,self.kinetic_rate) for i in range(n) for j in range(n)):
            raise ValueError('Symmetric pressure geometry and time derivative required')
        PositiveSolve(self.kinetic,self.zero,allow_semidefinite=True)
        # Match the original implemented constants, including its represented
        # zero-mode sum, rather than rounding c to 1/15 or fitting inverse poles.
        self.constant=F(1-float(np.sum(WEIGHTS)))
        self.poles=[]
        self.physical=[[self.zero]*n for _ in range(n)]
        self.physical_rate=[[self.zero]*n for _ in range(n)]
        for i in range(n):
            self.physical[i][i]=self.constant*self.mass[i]
            self.physical_rate[i][i]=self.constant*self.mass_rate[i]
        for length,weight in zip(LENGTHS,WEIGHTS):
            length,weight=F(float(length)),F(float(weight))
            h=[[length*self.kinetic[i][j]+(self.mass[i] if i==j else 0) for j in range(n)] for i in range(n)]
            hd=[[length*self.kinetic_rate[i][j]+(self.mass_rate[i] if i==j else 0) for j in range(n)] for i in range(n)]
            solver=PositiveSolve(h,self.zero)
            columns=[solver.solve(tuple(self.mass[i] if i==j else self.zero for i in range(n))) for j in range(n)]
            a=tuple(tuple(columns[j][i] for j in range(n)) for i in range(n))
            # A=H^-1 M; B_j=M A. Differentiate both exterior M factors,
            # and H^-1 itself: B_j,t=M_t A+A^T M_t-A^T H_t A.
            ha=[[sum((hd[i][k]*a[k][j] for k in range(n)),self.zero) for j in range(n)] for i in range(n)]
            for i in range(n):
                for j in range(n):
                    self.physical[i][j]+=weight*self.mass[i]*a[i][j]
                    self.physical_rate[i][j]+=weight*(self.mass_rate[i]*a[i][j]+a[j][i]*self.mass_rate[j]
                        -sum((a[k][i]*ha[k][j] for k in range(n)),self.zero))
            self.poles.append(dict(length=length,weight=weight,matrix=h,matrix_rate=hd,auxiliary_map=a,solver=solver))
        self.solve_physical=PositiveSolve(self.physical,self.zero)
        if any(self.physical_rate[i][j]!=self.physical_rate[j][i] for i in range(n) for j in range(n)):
            raise ValueError('Physical metric time derivative lost symmetry')

    def number(self,value):
        return self.zero+(value if isinstance(value,Radical) else F(value))

    def vector(self,pairs):
        pairs=tuple(tuple(p) for p in pairs)
        if len(pairs)*2!=len(self.mass) or any(len(p)!=2 for p in pairs):
            raise ValueError('Two components per active original source required')
        return tuple(self.number(v) for pair in pairs for v in pair)

    def action(self,matrix,vector):
        return tuple(sum((a*b for a,b in zip(row,vector)),self.zero) for row in matrix)

    def pairs(self,vector):return tuple(tuple(vector[i:i+2]) for i in range(0,len(vector),2))

    def physical_momentum(self,canonical_velocity):
        return self.pairs(self.action(self.physical,self.vector(canonical_velocity)))

    def evaluate(self,physical_momentum,physical_momentum_rate):
        p,pd=self.vector(physical_momentum),self.vector(physical_momentum_rate)
        v=self.solve_physical.solve(p)
        change=self.action(self.physical_rate,v)
        vd=self.solve_physical.solve(tuple(a-b for a,b in zip(pd,change)))
        layer=tuple(a/b for a,b in zip(p,self.mass))
        layer_rate=tuple((a-b*c)/m for a,b,c,m in zip(pd,layer,self.mass_rate,self.mass))
        canonical_momentum=tuple(m*u for m,u in zip(self.mass,v))
        canonical_momentum_rate=tuple(md*u+m*ud for md,u,m,ud in zip(self.mass_rate,v,self.mass,vd))
        energy=sum((a*b for a,b in zip(p,v)),self.zero)/2
        input_work=sum((a*b for a,b in zip(pd,v)),self.zero)
        geometry_work=-sum((a*b for a,b in zip(v,change)),self.zero)/2
        direct_rate=sum((a*b+c*d for a,b,c,d in zip(pd,v,p,vd)),self.zero)/2
        if energy<0 or direct_rate!=input_work+geometry_work:
            raise ValueError('Original physical energy positivity or complete chain rule failed')
        poles=[]
        mv=tuple(m*u for m,u in zip(self.mass,v))
        mvd=tuple(md*u+m*ud for md,u,m,ud in zip(self.mass_rate,v,self.mass,vd))
        reconstructed=[self.constant*x for x in mv]
        reconstructed_rate=[self.constant*x for x in mvd]
        positive_terms=[self.constant*sum((m*u*u for m,u in zip(self.mass,v)),self.zero)/2]
        positive_rate=self.constant*sum((md*u*u+2*m*u*ud for md,u,m,ud in zip(self.mass_rate,v,self.mass,vd)),self.zero)/2
        for pole in self.poles:
            a=self.action(pole['auxiliary_map'],v)
            ha=self.action(pole['matrix_rate'],a)
            ad=pole['solver'].solve(tuple(x-y for x,y in zip(mvd,ha)))
            if self.action(pole['matrix'],a)!=mv:
                raise ValueError('Exact original pressure pole residual is nonzero')
            derivative=self.action(pole['matrix'],ad)
            if tuple(x+y for x,y in zip(derivative,ha))!=mvd:
                raise ValueError('Differentiated original pole equation failed')
            for i in range(len(p)):
                reconstructed[i]+=pole['weight']*self.mass[i]*a[i]
                reconstructed_rate[i]+=pole['weight']*(self.mass_rate[i]*a[i]+self.mass[i]*ad[i])
            ca=self.action(self.kinetic,a);cta=self.action(self.kinetic_rate,a)
            positive_terms.append(pole['weight']*sum((mass*x*x+pole['length']*x*y
                                  for mass,x,y in zip(self.mass,a,ca)),self.zero)/2)
            positive_rate+=pole['weight']*sum((md*x*x+2*mass*x*xd+pole['length']*(x*z+2*xd*y)
                            for md,mass,x,xd,y,z in zip(self.mass_rate,self.mass,a,ad,ca,cta)),self.zero)/2
            poles.append(dict(length=pole['length'],weight=pole['weight'],auxiliary_velocity=self.pairs(a),
                              auxiliary_velocity_rate=self.pairs(ad),exact_residual_zero=True,exact_rate_residual_zero=True))
        if tuple(reconstructed)!=p or tuple(reconstructed_rate)!=pd:
            raise ValueError('Original two-pole momentum or time-work reconstruction failed')
        if any(e<0 for e in positive_terms) or sum(positive_terms,self.zero)!=energy or positive_rate!=direct_rate:
            raise ValueError('Independent positive auxiliary energy or time-work identity failed')
        return dict(kinetic_energy=energy,kinetic_energy_rate=direct_rate,momentum_work=input_work,
                    geometry_time_work=geometry_work,canonical_velocity=self.pairs(v),canonical_velocity_rate=self.pairs(vd),
                    layer_velocity=self.pairs(layer),layer_velocity_rate=self.pairs(layer_rate),
                    canonical_momentum=self.pairs(canonical_momentum),canonical_momentum_rate=self.pairs(canonical_momentum_rate),
                    poles=poles,positive_energy_terms=tuple(positive_terms),positive_auxiliary_energy_rate=positive_rate,
                    exact_original_momentum_and_rate_reconstruction=True,
                    native_40cg_or_nonlinear_force_or_open_boundary_or_gameplay_accepted=False)
