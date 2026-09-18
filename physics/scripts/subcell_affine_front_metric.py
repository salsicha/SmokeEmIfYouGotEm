"""Original vertical kinetic form on the finite-time affine dry-fan profile.

Retains the existing completed-square form h*(h*D-1.5*b.u)^2+.75*h*(b.u)^2.
The fan depth is quadratic, not a horizontal hydrostatic stage or mean depth.
Exact moving-profile moments supply the metric and its actual time derivative;
neither is a volume-only derivative. This does not close the varying inlet,
intercell pressure derivative, slope junctions or full dispersive evolution.
"""
from fractions import Fraction as F

from subcell_affine_dry_fan import _clip, _integrate


def front_metric(fan, fragment, time):
    """Integrate h**0..3 and d/dt of h**1..3 on the original fixed polygon.

    At the moving dry edge all h**k integrands for k>=1 vanish. At the moving
    fan head they agree on both sides. Thus the interface terms cancel, leaving
    exact branch integrals of k*h**(k-1)*h_t. Wet-area rate is deliberately not
    inferred by that argument. No finite differences generate metric rates.
    """
    t=F(time)
    if t<=0:
        raise ValueError('Positive finite moving-front time required')
    # Reuse the original affine-plane/convex-polygon validation, not a projected
    # or resampled polygon. The mass comparison below is independently assembled.
    budget=fan.integrate(fragment,t)
    head,front,linear,_,_=fan._profile(t)
    normal_acceleration=fan.gravity*sum(n*s for n,s in zip(fan.normal,fan.gradient))
    linear_rate=lambda p:fan._coordinate(p)/(t*t)-normal_acceleration/2
    wet=_clip(fragment.polygon,lambda p:fan._coordinate(p)-head,False)
    varying=_clip(_clip(fragment.polygon,lambda p:fan._coordinate(p)-head,True),
                  lambda p:fan._coordinate(p)-front,False)
    moments=[fan.zero]*4;rates=[fan.zero]*3;rate_scales=[fan.zero]*3
    spatial=[fan.zero]*2;spatial_rates=[fan.zero]*2
    for polygon,variable in ((wet,False),(varying,True)):
        # Algebraic vertices must not pass through the rational-only geometry
        # helper or a float projection. Zero-area triangles integrate to zero.
        for index in range(1,len(polygon)-1):
            triangle=(polygon[0],polygon[index],polygon[index+1])
            coefficient=F(1,9)/(fan.gravity*fan.norm2) if variable else fan.depth
            for k in range(4):
                forms=[linear]*(2*k) if variable else []
                moments[k]+=coefficient**k*_integrate(triangle,forms,fan.zero)
                if variable and k:
                    rates[k-1]+=2*k*coefficient**k*_integrate(
                        triangle,[linear]*(2*k-1)+[linear_rate],fan.zero)
            # Bed potential needs integral((x-origin)*h), not the centroid of
            # the footprint times volume. Preserve the curved depth profile.
            for axis in range(2):
                coordinate=lambda p,axis=axis:p[axis]-fan.origin[axis]
                spatial[axis]+=coefficient*_integrate(
                    triangle,([linear,linear] if variable else [])+[coordinate],fan.zero)
                if variable:
                    spatial_rates[axis]+=2*coefficient*_integrate(
                        triangle,[linear,linear_rate,coordinate],fan.zero)
    # Gross actual work is a meaningful derivative-audit scale even when
    # opposite changes cancel. Never divide pre-existing mass by a tiny time
    # to obtain an arbitrarily permissive normalization.
    coefficient=F(1,9)/(fan.gravity*fan.norm2)
    for positive in (False,True):
        polygon=_clip(varying,linear_rate,positive)
        for index in range(1,len(polygon)-1):
            triangle=(polygon[0],polygon[index],polygon[index+1])
            for k in range(1,4):
                term=2*k*coefficient**k*_integrate(
                    triangle,[linear]*(2*k-1)+[linear_rate],fan.zero)
                rate_scales[k-1]+=term if positive else -term
    if moments[1]!=budget['volume'] or any(m<0 for m in moments):
        raise ValueError('Moving-profile moments do not preserve the original fan volume')
    if any(scale<(rate if rate>=0 else -rate) for scale,rate in zip(rate_scales,rates)):
        raise ValueError('Gross metric work cannot be less than net work')

    def gram(m1,m2,m3):
        x,y=fan.gradient
        return ((m3,-F(3,2)*x*m2,-F(3,2)*y*m2),
                (-F(3,2)*x*m2,3*x*x*m1,3*x*y*m1),
                (-F(3,2)*y*m2,3*x*y*m1,3*y*y*m1))

    return dict(source_id=fragment.source_id,time=t,depth_moments=tuple(moments),
                depth_moment_rates=tuple(rates),depth_moment_rate_scales=tuple(rate_scales),
                depth_spatial_moments=tuple(spatial),depth_spatial_moment_rates=tuple(spatial_rates),
                spatial_origin=fan.origin,bed_at_origin=fan.bed,gravity=fan.gravity,
                gram=gram(*moments[1:]),
                gram_rate=gram(*rates),
                rate_coordinate='physical time on a fixed original source polygon',
                varying_inlet_or_intercell_or_dispersive_evolution_or_gameplay_accepted=False)


def metric_work(form, jet, jet_rate=(0,0,0)):
    """Energy and complete time work for the supplied (D,u_x,u_y) jet.

    Includes BOTH metric-time work and velocity-jet work, with no sign repair,
    inferred dry velocity, pressure solve or energy-residual redistribution.
    """
    jet,jet_rate=tuple(map(F,jet)),tuple(map(F,jet_rate))
    if len(jet)!=3 or len(jet_rate)!=3:
        raise ValueError('Divergence and two velocity components required')
    contract=lambda a,m,b:sum(a[i]*m[i][j]*b[j] for i in range(3) for j in range(3))
    energy=contract(jet,form['gram'],jet)/2
    metric_rate=contract(jet,form['gram_rate'],jet)/2
    velocity_rate=contract(jet_rate,form['gram'],jet)
    if energy<0:
        raise ValueError('Negative original moving-profile kinetic energy')
    return dict(energy=energy,metric_time_work=metric_rate,jet_time_work=velocity_rate,
                energy_rate=metric_rate+velocity_rate)
