"""Carry an interface through the SAME finite map as a position correction.

Particles use F(x)=x+delta(x), not an RK2 time step. An Eulerian scalar must
therefore use phi_new(y)=phi_old(F^-1(y)); an unrelated RK2 backtrace is not its
inverse. Damped Newton inversion reports failures without clamping, filling or
altering particle volume. Positive sampled Jacobians are necessary evidence,
not a proof that the map is globally one-to-one between the samples.
"""
import numpy as np
from liquid_compatible_advection import sample_compact
from liquid_volume_interface import sample_centred


def supported(points,cells,spacing):
    low=np.floor(points/spacing-.5).astype(int)-1
    return ((low>=0)&(low+3<cells)).all(axis=1)


def inverse_map(destinations,delta_zyx,spacing,*,tolerance=1e-6,max_iterations=24):
    """Invert the forward position map, in the same length units as delta.

    Return candidate departures AND a per-point valid mask. Invalid points
    must never be interpreted as successfully advected interface samples.
    """
    y=np.asarray(destinations,float);d=np.asarray(delta_zyx,float);h=np.asarray(spacing,float)
    if (y.ndim!=2 or y.shape[1]!=3 or d.ndim!=4 or d.shape[-1]!=3 or h.shape!=(3,) or
        not all(np.isfinite(a).all() for a in (y,d,h)) or (h<=0).any() or
        not np.isfinite(tolerance) or tolerance<=0 or not isinstance(max_iterations,int) or max_iterations<1):
        raise ValueError('Finite XYZ destinations, displacement grid, spacing and positive inverse limits required')
    grid=d.transpose(2,1,0,3);cells=np.array(grid.shape[:3]);x=y.copy()
    live=supported(x,cells,h);valid=np.zeros(len(x),bool);folded=np.zeros(len(x),bool)
    errors=np.full(len(x),np.inf);minimum_det=np.inf;iterations=0
    for iteration in range(max_iterations):
        ids=np.flatnonzero(live&~valid)
        if not len(ids):break
        iterations=iteration+1
        movement,jac=sample_compact(x[ids],grid,h,derivatives=True);jac+=np.eye(3)
        determinant=np.linalg.det(jac);minimum_det=min(minimum_det,float(determinant.min()))
        bad=~np.isfinite(determinant)|(determinant<=0)
        folded[ids[bad]]=True;live[ids[bad]]=False
        residual=x[ids]+movement-y[ids];norm=np.linalg.norm(residual,axis=1);errors[ids]=norm
        done=(norm<=tolerance)&~bad;valid[ids[done]]=True
        use=~bad&~done;ids=ids[use]
        if not len(ids):continue
        step=np.linalg.solve(jac[use],residual[use,...,None])[...,0]
        old_norm=norm[use];remaining=np.ones(len(ids),bool)
        # Backtracking changes only the root-search step, NOT the solved field.
        # No weakening of the inverse residual or terrain/contact constraints.
        for power in range(16):
            rows=np.flatnonzero(remaining)
            if not len(rows):break
            trial=x[ids[rows]]-step[rows]*(.5**power)
            inside=supported(trial,cells,h);candidate=np.full(len(rows),np.inf)
            if inside.any():
                v=sample_compact(trial[inside],grid,h)
                candidate[inside]=np.linalg.norm(trial[inside]+v-y[ids[rows[inside]]],axis=1)
            accept=candidate<old_norm[rows]
            accepted=rows[accept];x[ids[accepted]]=trial[accept];remaining[accepted]=False
        live[ids[remaining]]=False
    # Validate the final iterate too (including updates on the last iteration).
    ids=np.flatnonzero(live)
    if len(ids):
        movement,jac=sample_compact(x[ids],grid,h,derivatives=True)
        determinant=np.linalg.det(jac+np.eye(3));minimum_det=min(minimum_det,float(determinant.min()))
        errors[ids]=np.linalg.norm(x[ids]+movement-y[ids],axis=1)
        folded[ids[determinant<=0]]=True
        valid[ids]=(errors[ids]<=tolerance)&(determinant>0)
    report=dict(points=len(x),valid_inverse_points=int(valid.sum()),rejected_inverse_points=int((~valid).sum()),
        nonpositive_sampled_jacobians=int(folded.sum()),iterations=iterations,
        minimum_sampled_determinant=None if not np.isfinite(minimum_det) else minimum_det,
        maximum_valid_inverse_residual=float(errors[valid].max(initial=0)),
        candidate_valid=bool(valid.all()),global_injectivity_proven=False)
    return x,valid,report


def transport_interface(phi,delta,spacing,selected,*,tolerance=1e-6):
    """Transport selected cells, preserving caller-owned solid/exterior data.

    NaN marks rejected selected cells; no old scalar is silently passed off as
    a completed correction. Caller must reject the step before phase rebuild.
    """
    phi=np.asarray(phi,float);selected=np.asarray(selected)
    if (phi.ndim!=3 or selected.shape!=phi.shape or selected.dtype!=bool or
        np.asarray(delta).shape!=(*phi.shape,3) or not np.isfinite(phi).all()):
        raise ValueError('Finite scalar, matching displacement and boolean selection required')
    z,y,x=np.nonzero(selected);points=np.column_stack((x,y,z))
    departures,valid,report=inverse_map((points+.5)*spacing,delta,spacing,tolerance=tolerance)
    scalar,complete=sample_centred(phi,departures,spacing);valid&=complete
    output=phi.copy();output[selected]=np.where(valid,scalar,np.nan)
    report.update(valid_scalar_points=int(valid.sum()),rejected_scalar_points=int((~valid).sum()),
        candidate_valid=bool(valid.all()),forward_map='x + compact(delta,x)',
        interface_reconstructed_from_density=False,particle_mass_modified=False,native_integrated=False)
    return output,report


def reclassify_interface(boundary,phi):
    """Rebuild only existing fluid/air labels from a verified transported phi.

    Never convert solid/exterior cells, move terrain, or reuse a factorization
    after the returned fluid mask changes. This does not fix cut-cell pressure.
    """
    b=np.asarray(boundary,float);phi=np.asarray(phi,float)
    if b.shape!=(*phi.shape,4) or not np.isfinite(b).all() or not np.isfinite(phi).all():
        raise ValueError('Matching finite boundary/interface required')
    types=b[...,3]
    if not np.isin(types,[0,1,2,3]).all():raise ValueError('Integral known phase labels required')
    output=b.copy();mutable=np.isin(types,[0,2]);output[mutable,3]=np.where(phi[mutable]<0,0,2)
    return output,dict(air_to_fluid_cells=int(((types==2)&(output[...,3]==0)).sum()),
        fluid_to_air_cells=int(((types==0)&(output[...,3]==2)).sum()),
        fixed_phase_cells_changed=int((output[~mutable,3]!=types[~mutable]).sum()),
        pressure_factorization_reusable=bool(np.array_equal(types,output[...,3])))
