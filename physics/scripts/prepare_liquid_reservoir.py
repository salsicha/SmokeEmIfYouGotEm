"""Prepare explicit exterior water support without changing the rapid's water.

This is input preparation for an open-boundary buffer, NOT an installed solver
or permission to retire backflow. Original core seeds/sources remain immutable.
The buffer's bed comes from original registered triangles; its stage and motion
are uncalibrated hydraulic priors, not additional measurements.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from build_south_fork_liquid_window import bilinear
from build_south_fork_liquid_initial_state import apportion_columns, resolved_wet_depth
from liquid_region_geometry import ownership_table
from south_fork_registered_mesh import RegisteredMeshSampler

ROOT=Path(__file__).resolve().parents[2]


def reservoir_columns(domain, layers):
    counts=np.asarray(domain['physical_cells']);spacing=np.asarray(domain['cell_size_m'],dtype=float)
    bounds=np.asarray(domain['native_face_bounds_m'],dtype=float)
    if (isinstance(layers,bool) or not isinstance(layers,int) or not 2<=layers<=16 or
        counts.shape!=(3,) or not np.issubdtype(counts.dtype,np.integer) or (counts<2).any() or
        spacing.shape!=(3,) or not np.isfinite(spacing).all() or (spacing<=0).any() or
        bounds.shape!=(2,2) or not np.isfinite(bounds).all() or
        not np.allclose(bounds[1]-bounds[0],counts[:2]*spacing[:2],rtol=0,atol=1e-9)):
        raise ValueError('Explicit valid parent grid and 2..16 exterior cell layers required')
    # Same half-cell horizontal quadrature as the core. Enumerate only the ring
    # instead of allocating another full parent grid. Corners are included once.
    nx,ny=2*counts[:2];w=2*layers
    strips=[]
    for xs,ys in ((np.arange(-w,0),np.arange(-w,ny+w)),
                  (np.arange(nx,nx+w),np.arange(-w,ny+w)),
                  (np.arange(nx),np.arange(-w,0)),
                  (np.arange(nx),np.arange(ny,ny+w))):
        x,y=np.meshgrid(xs,ys);strips.append(np.column_stack((x.ravel(),y.ravel())))
    indices=np.concatenate(strips)
    return bounds[0]+(indices+.5)*spacing[:2]/2


def buffer_owners(domain, regions, layers):
    """Expand only genuine outer faces; internal shared cuts do not move."""
    reservoir_columns(domain,layers) # validates domain and layer contract
    ownership_table(domain,regions)
    parent=np.asarray(domain['physical_cells']);result=[]
    for r in regions:
        lo,hi=np.asarray(r['cell_bounds_xy']).copy()
        lo=np.where(lo==0,lo-layers,lo);hi=np.where(hi==parent[:2],hi+layers,hi)
        cells=np.r_[hi-lo,parent[2]];compute=cells+[4,4,0]
        if np.prod(compute,dtype=np.int64)*8>2000000:
            raise ValueError('Buffer expansion exceeds existing regional reconstruction allocation cap')
        result.append(dict(id=r['id'],cell_bounds_xy=[lo.tolist(),hi.tolist()],
            physical_cells=cells.tolist(),computational_cells=compute.tolist(),
            core_cell_bounds_xy=r['cell_bounds_xy']))
    return result


def classify_buffer_columns(sl, domain, regions):
    points=np.asarray(sl,dtype=float);spacing=np.asarray(domain['cell_size_m'][:2])
    bounds=np.asarray(domain['native_face_bounds_m'])
    if points.ndim!=2 or points.shape[1]!=2 or not np.isfinite(points).all():
        raise ValueError('Finite exterior column positions required')
    if np.any(np.all((points>=bounds[0])&(points<=bounds[1]),axis=1)):
        raise ValueError('Exterior preparation must not duplicate core water')
    outer=np.max([r['cell_bounds_xy'][1] for r in regions],axis=0)
    owner=np.full(len(points),-1,dtype=np.int32)
    for r in regions:
        lo,hi=np.asarray(r['cell_bounds_xy']);a,b=bounds[0]+np.array([lo,hi])*spacing
        inside=np.all((points>=a)&((points<b)|((hi==outer)&(points==b))),axis=1)
        if np.any(owner[inside]>=0):raise ValueError('Overlapping exterior ownership')
        owner[inside]=r['id']
    if np.any(owner<0):raise ValueError('Exterior water lacks declared ownership; no clamp fallback')
    return owner


def prepare(parent_directory, region_directory, layers):
    parent_directory,region_directory=Path(parent_directory),Path(region_directory)
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    read=lambda p:json.loads(p.read_text())
    window=read(parent_directory/'manifest.json')
    ownership=read(region_directory/'manifest.json')
    # Verify the original source and every regional state before deriving support.
    for name,digest in ownership['parent_files_sha256'].items():
        if sha(parent_directory/name)!=digest:raise ValueError('Changed parent input: '+name)
    regions=[]
    for record in ownership['region_files']:
        name=record['file']
        if Path(name).name!=name:raise ValueError('Regional path escapes input directory')
        p=region_directory/name
        if sha(p)!=record['sha256']:raise ValueError('Changed regional input: '+name)
        regions.append(read(p))
    domain=ownership['domain'];expanded=buffer_owners(domain,regions,layers)
    original_ids=np.concatenate([r['seed_parent_ids'] for r in regions])
    if not np.array_equal(np.sort(original_ids),np.arange(ownership['particle_count'])):
        raise ValueError('Core seed identities must cover the original namespace exactly once')
    geometry=read(ROOT/window['source_geometry_manifest']);mesh_path=ROOT/geometry['mesh_path']
    if sha(mesh_path)!=window['source_geometry_sha256']:raise ValueError('Changed registered terrain')
    hydraulic=ROOT/window['source_hydraulic_directory'];flow=read(hydraulic/'manifest.json')
    if sha(hydraulic/'manifest.json')!=window['source_hydraulic_manifest_sha256']:
        raise ValueError('Changed hydraulic prior')
    coordinate=read(hydraulic/'coordinate_map.json')
    if coordinate['vertical_datum_m']!=geometry['vertical_origin_navd88_m']:
        raise ValueError('Buffer/core vertical datum mismatch')
    registration=read(hydraulic.parent/'registration.json')
    rotation=np.column_stack((registration['downstream_unit'],registration['left_unit']))
    if not np.allclose(rotation.T@rotation,np.eye(2),atol=1e-9,rtol=0) or np.linalg.det(rotation)<0:
        raise ValueError('Rigid right-handed source frame required')
    arrays={}
    for name,record in flow['bands'][0]['arrays'].items():
        p=hydraulic/record['file']
        if sha(p)!=record['sha256']:raise ValueError('Changed hydraulic array: '+name)
        arrays[name]=np.load(p)
    sl=reservoir_columns(domain,layers)
    en=(sl@rotation.T*100).astype(np.float32).astype(float)/100
    sl=en@rotation # sample the actual encoded GPU positions
    owners=classify_buffer_columns(sl,domain,expanded)
    sampler=RegisteredMeshSampler(np.load(mesh_path));bed=sampler.sample(en[:,0],en[:,1])
    h,u,v,b=(arrays[k] for k in ('h','u','v','bed'))
    stage=bilinear(b+h,sl[:,0],sl[:,1],flow['grid'])
    native_depth=bilinear(h,sl[:,0],sl[:,1],flow['grid'])
    depth=resolved_wet_depth(stage,bed,native_depth)
    momentum=np.column_stack([bilinear(h*k,sl[:,0],sl[:,1],flow['grid']) for k in (u,v)])
    velocity=np.divide(momentum,native_depth[:,None],out=np.zeros_like(momentum),
        where=native_depth[:,None]>1e-9)@rotation.T
    volume=float(domain['nominal_particle_volume_m3'])
    if not np.isclose(volume,np.prod(domain['cell_size_m'])/4,rtol=0,atol=1e-12):
        raise ValueError('Core nominal volume convention changed')
    volumes=depth*np.prod(np.asarray(domain['cell_size_m'][:2])/2)
    counts=apportion_columns(volumes,volume)
    if counts.sum()>5000000:raise ValueError('Exterior seed export capacity exceeded')
    columns=np.repeat(np.arange(len(counts)),counts)
    starts=np.repeat(np.cumsum(counts)-counts,counts)
    fraction=(np.arange(len(columns))-starts+.5)/counts[columns]
    xyz=np.column_stack((en[columns],bed[columns]+depth[columns]*fraction))*100
    xyz=xyz.astype(np.float32).astype(float)
    speeds=np.column_stack((velocity[columns],np.zeros(len(columns))))*100
    floor=window['local_origin_engine_cm'][2];height=domain['physical_extents_m'][2]*100
    if (not len(xyz) or not np.isfinite(xyz).all() or not np.isfinite(speeds).all() or
        np.any(xyz[:,2]<=bed[columns]*100) or np.any(xyz[:,2]>=stage[columns]*100) or
        np.any(xyz[:,2]<=floor) or np.any(xyz[:,2]>=floor+height)):
        raise ValueError('Exterior seed lacks original wet-column/vertical support')
    core_count=ownership['particle_count']
    for r in regions:
        additional=int(np.sum(owners[columns]==r['id']))
        if len(r['seed_parent_ids'])+additional>163840:
            raise ValueError('Core plus reservoir exceeds existing initial-burst capacity')
    return dict(schema='raftsim.liquid_exterior_reservoir_preparation.v1',
        original_core_ownership_sha256=sha(region_directory/'manifest.json'),
        original_core_particle_count=core_count,original_core_sources_unchanged=True,
        source_geometry_sha256=window['source_geometry_sha256'],
        source_hydraulic_manifest_sha256=window['source_hydraulic_manifest_sha256'],
        core_domain=domain,exterior_layers=layers,expanded_owner_bounds=expanded,
        reservoir_seed_parent_ids=np.arange(core_count,core_count+len(xyz)).tolist(),
        reservoir_owner_ids=owners[columns].tolist(),positions_canonical_cm=xyz.tolist(),
        velocities_canonical_cm_per_s=speeds.tolist(),particle_count=len(xyz),
        nominal_particle_volume_m3=volume,column_quadrature_volume_m3=float(volumes.sum()),
        represented_nominal_volume_m3=len(xyz)*volume,
        volume_quantization_error_m3=float(len(xyz)*volume-volumes.sum()),
        minimum_original_bed_clearance_cm=float(np.min(xyz[:,2]-bed[columns]*100)),
        submerged_bed_authority=window['submerged_bed_authority'],
        velocity_authority='Uncalibrated depth-averaged hydraulic prior; vertical velocity is zero',
        runtime_buffer_installed=False,backflow_exchange_verified=False,
        kernel_support_verified=False,production_promoted=False,
        required_before_runtime=['Move external supply to the outer buffer boundary with independently audited flux; do not double-source the old core interface',
            'Couple current pressure/velocity and terrain across the core-buffer interface',
            'Keep identities and signed mass/momentum for both crossing directions and true outer exits',
            'Verify current-state surface, wave reflection, discharge, storage and performance'])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('parent',type=Path);p.add_argument('regions',type=Path)
    p.add_argument('--layers',type=int,default=2);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.output.exists():raise FileExistsError('Retain earlier buffer preparation')
    report=prepare(a.parent,a.regions,a.layers)
    with a.output.open('x') as f:json.dump(report,f,indent=2)
    print(json.dumps({k:v for k,v in report.items() if k not in
        ('core_domain','expanded_owner_bounds','reservoir_seed_parent_ids','reservoir_owner_ids',
         'positions_canonical_cm','velocities_canonical_cm_per_s')},indent=2))
