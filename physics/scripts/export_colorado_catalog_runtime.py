"""Export a screened native Colorado cook without promoting a playable map.

The same registered construction bed supplies the native fields and Landscape.
No initial-state velocities are substituted for solver output, no bank is moved
to improve a score, and a construction pass never means class acceptance.
"""
import argparse
import datetime
import json
import shutil
import struct
from pathlib import Path

import numpy as np
from scipy.ndimage import map_coordinates
from build_colorado_catalog_evidence import ROOT,sha
from review_colorado_catalog_cook import load_frame
from export_hance_evidence_runtime import write_png_u16

BAND='steady_8000cfs_2021'


def checked_cook(inputs,cook,review):
    build=json.loads((inputs/'build_report.json').read_text())
    for name,digest in build['files_sha256'].items():
        if sha(inputs/name)!=digest:raise ValueError('Changed solver input')
    receipt=json.loads(review.read_text())
    if receipt['name']!=build['name'] or not receipt['construction_screen_passed']:
        raise ValueError('Cook did not pass its construction screen')
    if not receipt['construction_screen'] or not all(receipt['construction_screen'].values()):
        raise ValueError('Inconsistent construction screen')
    native=json.loads((cook/'manifest.json').read_text())
    if native!=receipt['native_manifest']:raise ValueError('Different native cook')
    if (native['solver_mode']!='finite_volume' or native['flux_scheme']!='hll' or
        not native['disable_fixture_calibrations'] or native['feature_strength_scale']!=0):
        raise ValueError('Unreviewed solver or forcing')
    validation=json.loads((cook/'validation.json').read_text())
    if not validation['passed'] or not validation['finite_state'] or validation['velocity_limit_reached']:
        raise ValueError('Native validation failed')
    for name,digest in receipt['frame_sha256'].items():
        if sha(cook/'frames'/name)!=digest:raise ValueError('Changed reviewed frame')
    scenario=json.loads((inputs/'scenario/scenario.json').read_text())
    grid=scenario['grid'];shape=(grid['ny'],grid['nx'])
    frame=load_frame(cook/'frames'/receipt['comparison_frames'][-1],shape)
    bed=np.load(inputs/'scenario/bed.npy')
    wet=frame['h']>0
    if not np.allclose((frame['eta']-frame['h'])[wet],bed[wet],atol=1e-6,rtol=0):
        raise ValueError('Cook does not belong to this bed')
    return build,receipt,native,scenario,frame,bed


def landscape_grid(bed,size=2017):
    if bed.ndim!=2 or min(bed.shape)<2 or not np.isfinite(bed).all():
        raise ValueError('Incomplete registered terrain')
    # Source samples are cell centres; the Landscape covers the source edges.
    # Only the half-cell outer margin uses its adjacent source height.
    rr,cc=np.meshgrid(np.linspace(-.5,bed.shape[0]-.5,size),
                       np.linspace(-.5,bed.shape[1]-.5,size),indexing='ij')
    sampled=map_coordinates(bed,[rr,cc],order=1,mode='nearest',prefilter=False)
    lo,hi=float(sampled.min()),float(sampled.max())
    if hi-lo<.01:raise ValueError('Degenerate terrain relief')
    encoded=np.round((sampled-lo)/(hi-lo)*65535).astype('uint16')
    # UE uses 128 height units/cm with scale_z=relief_cm/512: /65536.
    relief=(hi-lo)*65536/65535
    decoded=lo+encoded.astype(float)*relief/65536
    return encoded,decoded,lo,relief


def landscape_sample(decoded,rows,cols):
    """UE Chaos HeightField.cpp GetHeightNormalAt: diagonal (0,0)-(1,1).

    Bilinear interpolation is NOT the collision/render triangle surface at
    nonplanar quads. Leave out-of-source queries missing, never clamp terrain.
    """
    rows,cols=np.broadcast_arrays(np.asarray(rows,dtype=float),np.asarray(cols,dtype=float))
    valid=(np.isfinite(rows)&np.isfinite(cols)&(rows>=0)&(cols>=0)&
           (rows<=decoded.shape[0]-1)&(cols<=decoded.shape[1]-1))
    rr=np.clip(np.where(valid,rows,0),0,decoded.shape[0]-1)
    cc=np.clip(np.where(valid,cols,0),0,decoded.shape[1]-1)
    r=np.minimum(np.floor(rr).astype(int),decoded.shape[0]-2)
    c=np.minimum(np.floor(cc).astype(int),decoded.shape[1]-2)
    y=rr-r;x=cc-c
    z00=decoded[r,c];z10=decoded[r,c+1];z01=decoded[r+1,c];z11=decoded[r+1,c+1]
    height=np.where(x<y,(1-y)*z00+x*z11+(y-x)*z01,
                        (1-x)*z00+(x-y)*z10+y*z11)
    return np.where(valid,height,np.nan)


def export(inputs,cook,review,out):
    if out.exists():raise ValueError('Fresh runtime export required')
    build,receipt,native,scenario,f,bed=checked_cook(inputs,cook,review)
    evidence=ROOT/build['construction_directory']
    ev=json.loads((evidence/'manifest.json').read_text())
    if sha(evidence/'evidence_grid.npz')!=ev['evidence_grid_sha256']:
        raise ValueError('Construction terrain changed')
    g=dict(np.load(evidence/'evidence_grid.npz'))
    encoded,decoded,tmin,relief=landscape_grid(g['bed_ellipsoid_m'])
    mapping=json.loads((inputs/'coordinate_map.json').read_text())
    pts=np.asarray(mapping['points']);grid=scenario['grid'];ny,nx=bed.shape
    if len(pts)!=nx:raise ValueError('Coordinate map shape mismatch')
    h=f['h'];wet=f['wet']>.5;speed=np.hypot(f['u'],f['v'])
    origin=np.asarray(mapping['horizontal_origin_epsg6404_m'])
    source_xy=pts[:,1:3]+origin
    ll=grid['origin_y']+np.arange(ny)*grid['dy']
    queries=source_xy[None,:,:]+ll[:,None,None]*pts[None,:,3:5]
    corner=g['corner_east_north_m'];sy,sx=g['bed_ellipsoid_m'].shape
    py=(corner[1]-queries[...,1])/sy*2016
    px=(queries[...,0]-corner[0])/sx*2016
    render_bed=landscape_sample(decoded,py,px)
    if not np.isfinite(render_bed[wet]).all():raise ValueError('Wet solver cells outside rendered terrain')
    disagreement=abs(render_bed[wet]-bed[wet])
    if disagreement.max()>.1:
        raise ValueError('Rendered terrain differs from cooked wet bed by over 10 cm; rebuild with --match-landscape and recook')
    out.mkdir(parents=True);fields=out/'cooked_flow_fields';(fields/BAND).mkdir(parents=True)
    arrays={}
    for name,a,dtype in [('bed',bed,'float32'),('h',h,'float32'),
        ('u',np.where(wet,f['u'],0),'float32'),('v',np.where(wet,f['v'],0),'float32'),('wet_mask',wet,'uint8')]:
        path=fields/BAND/(name+'.npy');np.save(path,np.ascontiguousarray(a.astype(dtype)))
        arrays[name]=dict(file=f'{BAND}/{name}.npy',sha256=sha(path),shape=[ny,nx],dtype=dtype)
    froude=np.where(h>.05,speed/np.sqrt(9.81*np.maximum(h,.05)),0)
    energy=np.clip(.6*np.clip((speed-.5)/2.5,0,1)+.4*np.clip((froude-.5)/.5,0,1),0,1)
    bwet=wet&(h>.05);baseline=fields/f'support_band_field_{BAND}.bin'
    with baseline.open('wb') as stream:
        stream.write(struct.pack('<IIiiff',0x52534246,1,ny,nx,grid['origin_y'],grid['dy']))
        for a,dtype in [(pts[:,0],'<f4'),(np.where(bwet,f['eta'],bed).T,'<f4'),(energy.T,'<f4'),(bwet.T,'u1')]:
            a=np.ascontiguousarray(a.astype(dtype));stream.write(struct.pack('<i',a.size));stream.write(a.tobytes())
    runtime_solver=dict(native,binary_sha256=receipt['solver_sha256'],runtime_crop_boundary_mode='cooked_ghost',
                        fixed_dt_s=scenario['fixed_dt'])
    runtime_solver.pop('frames',None)
    # The runtime loader accepts stage/velocity edge boundaries, not the
    # native cook's per-cell discharge_profile. Interior moving crops retain
    # exact cooked ghost cells; these approximations apply only at reach ends.
    inlet=wet[:,0]&(h[:,0]>.05);outlet=wet[:,-1]&(h[:,-1]>.05)
    if not inlet.any() or not outlet.any():raise ValueError('Dry runtime boundary')
    runtime_boundaries=[dict(edge='west',kind='inflow',stage=float(np.median(f['eta'][inlet,0])),
        velocity=[float(np.median(f['u'][inlet,0])),float(np.median(f['v'][inlet,0]))]),
        dict(edge='east',kind='outflow',stage=float(np.median(f['eta'][outlet,-1]))),
        dict(edge='south',kind='bank'),dict(edge='north',kind='bank')]
    manifest=dict(schema='raftsim.cooked_flow_fields.v1',generator=Path(__file__).name,
        generated_on=datetime.date.today().isoformat(),river_id='colorado_river_grand_canyon_rowing',
        rapid_name=build['name'],section_id=mapping['section_id'],source_elevation_datum_m=0.,
        grid=dict(nx=nx,ny=ny,dx_m=grid['dx'],dy_m=grid['dy'],origin_x_m=grid['origin_x'],
            origin_y_m=grid['origin_y'],layout='row_major_c_order',downstream_axis='+x'),
        solver=runtime_solver,bands=[dict(band_id=BAND,directory=BAND,scenario_id=native['scenario_id'],
            effective_manning_n=scenario['roughness'],manning_n=scenario['roughness'],
            discharge_target_m3s=receipt['statistics']['exact_face_discharge_target_m3s'],discharge_target_cfs=8000.,
            runtime_boundaries=runtime_boundaries,arrays=arrays,
            presentation_baseline=dict(file=baseline.name,sha256=sha(baseline)),
            convergence=dict(construction_screen_passed=True,**receipt['statistics']))],
        provenance=ev,runtime_boundary_note='At original reach ends only: median solved stage/velocity. Interior crops use full cooked ghosts.',
        engine_validated=False,class_match='not_established')
    (fields/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    terrain=out/'terrain';terrain.mkdir();write_png_u16(terrain/'heightfield_2017.png',encoded)
    (terrain/'coordinate_map.json').write_text(json.dumps(mapping,indent=1)+'\n')
    surf=np.array([np.median(f['eta'][wet[:,i],i]) if wet[:,i].any() else np.nan for i in range(nx)])
    if not np.isfinite(surf).all():raise ValueError('Dry source section in runtime export')
    bedc=np.array([np.median(bed[wet[:,i],i]) for i in range(nx)])
    cl=dict(schema='raftsim.local_centerline.v1',river_id='colorado_river',section_id=mapping['section_id'],
        points=[dict(station_m=float(s),unreal_local_cm=[float((e-corner[0])*100),float((corner[1]-n)*100)],
            conditioned_visual_surface_elevation_m=float(z),conditioned_visual_bed_elevation_m=float(b),
            conditioned_visual_surface_normalized=float((z-tmin)/relief),
            conditioned_visual_bed_normalized=float((b-tmin)/relief)) for s,(e,n),z,b in zip(pts[:,0],source_xy,surf,bedc)])
    (terrain/'centerline_local.json').write_text(json.dumps(cl,indent=1)+'\n')
    cm=(fields/'manifest.json').relative_to(ROOT).as_posix()
    streaming=dict(schema='raftsim.south_fork.moving_water_streaming.v1',
        full_reach_transit_seed=dict(cooked_fields_manifest=cm,cooked_fields_manifest_sha256=sha(fields/'manifest.json')),
        windows=[dict(window_id=mapping['section_id'],cooked_fields_manifest=cm,station_range_m=[0.,float(pts[-1,0])])],
        moving_window=dict(station_extent_m=480.,lateral_extent_m=(ny-1)*grid['dy'],advance_m=80.),
        settled_hydraulics=True,procedural_reference_field=False)
    (out/'moving_water_streaming.json').write_text(json.dumps(streaming,indent=2)+'\n')
    shutil.copyfile(review,out/'construction_review.json')
    result=dict(schema='raftsim.colorado_catalog_runtime_candidate.v1',name=build['name'],
        source_inputs=str(inputs.relative_to(ROOT)),source_cook=str(cook.relative_to(ROOT)),
        source_review_sha256=sha(review),landscape=dict(size_px=2017,horizontal_span_x_m=sx,horizontal_span_y_m=sy,
            terrain_min_m=tmin,target_relief_cm=relief*100,world_vertical_offset_cm=(tmin-mapping['vertical_datum_m'])*100,
            runtime_vertical_datum_m=mapping['vertical_datum_m'],world_min_x_cm=0.),
        terrain_solver_bed_error_m=dict(p95=float(np.percentile(disagreement,95)),maximum=float(disagreement.max())),
        files_sha256={str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()},
        rapid_point_station_m=build['rapid_point_station_m'],
        limitations=['Regional 10 m dry terrain is not measured boulder geometry.','Rapid bed and low shore are inferred.',
            'Exact rapid entry/exit and named obstacle decisions still need construction and native trials.'],
        playable_map_created=False,engine_validated=False,accepted=False)
    (out/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='files_sha256'},indent=2))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('inputs','cook','review','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();export(a.inputs.resolve(),a.cook.resolve(),a.review.resolve(),a.out.resolve())
