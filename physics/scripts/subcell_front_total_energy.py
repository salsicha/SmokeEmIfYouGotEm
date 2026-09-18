"""Total physical-energy variation on the SAME moving-front source geometry.

Adds g*integral(h**2/2+(bed-datum)*h) to the original two-pole kinetic
functional in both momentum coordinates. Coordinates and the energy datum
are fixed; original bed height/slope and all depth moments are independent
primitive arguments. This supplies an energy derivative, NOT the missing
conservative transport bracket, wetting/front force or open-boundary law.
"""
from fractions import Fraction as F

from subcell_front_pressure_variation import FrontPressureVariation


class FrontTotalEnergyVariation:
    def __init__(self, geometry, metric, physical_momentum, *, energy_datum=0, solved_state=None):
        self.pressure=FrontPressureVariation(geometry,metric,physical_momentum,solved_state=solved_state)
        self.geometry=geometry;self.number=metric.number;self.zero=metric.zero
        self.energy_datum=F(energy_datum)
        self.potential_energy=self.zero
        moments=[];spatial=[];slopes=[];heights=[]
        for owner in geometry.active:
            form=geometry.forms[owner];fragment=geometry.fragments[owner]
            gravity=F(form['gravity']);bed=F(form['bed_at_origin'])
            origin=tuple(map(F,form['spatial_origin']));gradient=fragment.gradient
            if gravity<=0 or len(origin)!=2 or any(
                    p[2]!=bed+sum(s*(x-o) for s,x,o in zip(gradient,p,origin)) for p in fragment.polygon):
                raise ValueError('Positive gravity and matching original affine bed required')
            m1,m2,_=form['depth_moments'][1:];xh=form['depth_spatial_moments']
            moments.append((gravity*(bed-self.energy_datum),gravity/2,self.zero))
            spatial.append(tuple(gravity*s for s in gradient))
            slopes.append(tuple(gravity*x for x in xh))
            heights.append(gravity*m1)
            self.potential_energy+=gravity*((bed-self.energy_datum)*m1+m2/2
                                           +sum((s*x for s,x in zip(gradient,xh)),self.zero))
        self.potential_depth_moment_gradients=tuple(moments)
        self.spatial_moment_gradients=tuple(spatial)
        self.potential_bed_gradient_gradients=tuple(slopes)
        self.bed_height_gradients=tuple(heights)
        p=metric.vector(physical_momentum)
        v=metric.vector(self.pressure.momentum_gradient)
        self.kinetic_energy=sum((a*b for a,b in zip(p,v)),self.zero)/2
        self.total_energy=self.kinetic_energy+self.potential_energy
        for prefix in ('','canonical_'):
            setattr(self,prefix+'momentum_gradient',getattr(self.pressure,prefix+'momentum_gradient'))
            setattr(self,prefix+'face_column_gradients',getattr(self.pressure,prefix+'face_column_gradients'))
            for name,addition in (('depth_moment_gradients',moments),('bed_gradient_gradients',slopes)):
                original=getattr(self.pressure,prefix+name)
                setattr(self,prefix+name,tuple(tuple(a+b for a,b in zip(row,extra))
                                             for row,extra in zip(original,addition)))

    def work(self, momentum_direction, moment_direction, face_column_direction, bed_gradient_direction,
             spatial_moment_direction, bed_height_direction, *, momentum_coordinate='physical'):
        """Full primitive work at fixed source XY, gravity and energy datum.

        Geometry directions are supplied, never manufactured from an energy
        residual. A dry owner's creation remains unsupported by the pressure
        derivative. Potential energy is the SAME sign in both coordinates.
        """
        moments=tuple(tuple(self.number(x) for x in row) for row in moment_direction)
        slopes=tuple(tuple(self.number(x) for x in row) for row in bed_gradient_direction)
        spatial=tuple(tuple(self.number(x) for x in row) for row in spatial_moment_direction)
        heights=tuple(self.number(x) for x in bed_height_direction)
        n=len(self.geometry.active)
        if len(spatial)!=n or any(len(row)!=2 for row in spatial) or len(heights)!=n:
            raise ValueError('Spatial moments and bed-height direction per active original source required')
        kinetic=self.pressure.work(momentum_direction,moments,face_column_direction,slopes,
                                   momentum_coordinate=momentum_coordinate)
        dot=lambda a,b:sum((x*y for row,delta in zip(a,b) for x,y in zip(row,delta)),self.zero)
        potential_moment=dot(self.potential_depth_moment_gradients,moments)
        potential_slope=dot(self.potential_bed_gradient_gradients,slopes)
        spatial_work=dot(self.spatial_moment_gradients,spatial)
        height_work=sum((a*b for a,b in zip(self.bed_height_gradients,heights)),self.zero)
        potential=potential_moment+potential_slope+spatial_work+height_work
        return dict(kinetic_energy_direction=kinetic['energy_direction'],potential_energy_direction=potential,
                    energy_direction=kinetic['energy_direction']+potential,
                    momentum_work=kinetic['momentum_work'],face_column_work=kinetic['face_column_work'],
                    depth_moment_work=kinetic['depth_moment_work']+potential_moment,
                    bed_gradient_work=kinetic['bed_gradient_work']+potential_slope,
                    spatial_moment_work=spatial_work,bed_height_work=height_work,
                    momentum_coordinate=momentum_coordinate,
                    conservative_force_or_wetting_or_open_or_native_or_gameplay_accepted=False)

    def time_work(self, momentum_rate, *, momentum_coordinate='physical'):
        g=self.geometry
        return self.work(momentum_rate,[g.forms[i]['depth_moment_rates'] for i in g.active],
                         [f['column_normal_rate'] for f in g.faces],[(0,0) for _ in g.active],
                         [g.forms[i]['depth_spatial_moment_rates'] for i in g.active],[0 for _ in g.active],
                         momentum_coordinate=momentum_coordinate)
