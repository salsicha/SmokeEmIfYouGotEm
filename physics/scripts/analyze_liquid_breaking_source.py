"""Measure missing crest sources on an actual captured SDF, not a screenshot.

This diagnostic does not modify the live source or identify a real rapid.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from liquid_breaking_source import crest_activity
from liquid_current_surface_foam import sample
from south_fork_registered_mesh import RegisteredMeshSampler


def hydraulic_context(unit,velocity,window_path=None):
    """Exact candidate-bed clearance; not acceptance of its inferred depths."""
    root=Path(__file__).resolve().parents[2]
    window_path=Path(window_path) if window_path is not None else root/'unreal/SourceArt/RaftSim/SouthForkLiquidWindow20260908/manifest.json'
    window=json.loads(window_path.read_text())
    geometry_path=root/window['source_geometry_manifest']
    geometry=json.loads(geometry_path.read_text());mesh_path=root/geometry['mesh_path']
    mesh_hash=hashlib.sha256(mesh_path.read_bytes()).hexdigest()
    if mesh_hash!=geometry['mesh_sha256'] or mesh_hash!=window['source_geometry_sha256']:
        raise ValueError('Changed candidate geometry')
    registration_path=root/window['source_hydraulic_directory']/Path('../registration.json')
    reg=json.loads(registration_path.read_text())
    rotation=np.column_stack([reg['downstream_unit'],reg['left_unit']])
    if not np.allclose(rotation.T@rotation,np.eye(2),atol=1e-9) or np.linalg.det(rotation)<0:
        raise ValueError('Invalid rigid hydraulic frame')
    xy=((unit[:,:2]-.5)*22.3125)@rotation.T
    with np.load(mesh_path) as mesh:bed=RegisteredMeshSampler(mesh).sample(xy[:,0],xy[:,1])
    depth=unit[:,2]*8+window['local_origin_engine_cm'][2]/100-bed
    speed=np.linalg.norm(sample(velocity,unit)[:,:2],axis=1)/100
    wet=depth>1/3
    if not wet.any():raise ValueError('No resolved-depth columns')
    proxy=speed[wet]/np.sqrt(9.81*depth[wet])
    return dict(columns_deeper_than_one_solver_z_cell=int(wet.sum()),
        quantile_probabilities=[0,.1,.5,.9,1],
        candidate_bed_clearance_m_quantiles=np.quantile(depth[wet],[0,.1,.5,.9,1]).tolist(),
        surface_horizontal_speed_m_s_quantiles=np.quantile(speed[wet],[0,.1,.5,.9,1]).tolist(),
        surface_speed_over_sqrt_g_depth_quantiles=np.quantile(proxy,[0,.1,.5,.9,1]).tolist(),
        ratio_above_one_fraction=float((proxy>1).mean()),depth_averaged_froude_measured=False,
        interpretation='Surface-speed proxy only; 3D unsteady flow and inferred bathymetry, not a hydraulic-jump acceptance test',
        submerged_bed_authority=geometry['submerged_bed_authority'],
        registered_rapid_identity_verified=geometry['registered_rapid_identity_verified'],
        source_sha256={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (window_path,geometry_path,mesh_path,registration_path)})


def analyze(path):
    files=['foam_current.rgba16f','foam_velocity.rgba16f','foam_audit.rgba32f']
    surface=np.fromfile(path/files[0],dtype='<f2').reshape(48,136,136,4).astype(float)
    velocity=np.fromfile(path/files[1],dtype='<f2').reshape(24,68,68,4).astype(float)
    audit=np.fromfile(path/files[2],dtype='<f4').reshape(48,136,136,4).astype(float)
    if not all(np.isfinite(v).all() for v in (surface,velocity,audit)):
        raise ValueError('Nonfinite captured inputs')
    phi=surface[...,0];cross=(phi[:-1]<0)&(phi[1:]>=0)
    height=np.where(cross,np.arange(47)[:,None,None],-1).max(axis=0)
    y,x=np.nonzero(height>=0);z=height[y,x]
    fraction=-phi[z,y,x]/(phi[z+1,y,x]-phi[z,y,x])
    unit=np.stack(((x+.5)/136,(y+.5)/136,(z+.5+fraction)/48),axis=-1)
    # Exclude an additional metre beside the physical 21m square boundary.
    interior=abs((unit[:,:2]-.5)*2231.25).max(axis=1)<950
    unit=unit[interior]
    if not len(unit):raise ValueError('No interior upward surface crossings')
    curvature,alignment,activity=crest_activity(surface,velocity,unit,[2231.25,2231.25,800])
    actual=sample(audit,unit)
    capture=json.loads((path.parent/'capture.json').read_text())
    context=hydraulic_context(unit,velocity,capture.get('window_manifest'))
    return dict(schema='raftsim.liquid_crest_source_diagnostic.v1',interior_columns=len(unit),
        quantile_probabilities=[0,.5,.9,.99,1],
        curvature_per_cm_quantiles=np.quantile(curvature,[0,.5,.9,.99,1]).tolist(),
        outward_alignment_quantiles=np.quantile(alignment,[0,.5,.9,.99,1]).tolist(),
        outward_fraction=float((alignment>.6).mean()),
        convex_outward_fraction=float((activity>0).mean()),
        crest_extension_per_second_quantiles=np.quantile(activity,[0,.5,.9,.99,1]).tolist(),
        mean_crest_extension_per_second=float(activity.mean()),
        current_source_per_second_quantiles=np.quantile(actual[:,0],[0,.5,.9,.99,1]).tolist(),
        zero_current_source_fraction=float((actual[:,0]==0).mean()),
        mean_current_source_per_second=float(actual[:,0].mean()),
        hydraulic_context=context,
        shader_crest_source_enabled=False,entrained_air_or_reference_calibration=False,
        photographed_foam_or_visible_pixel_coverage=False,
        limitations=['One completed instant, no impact history or resolved air fraction',
            'Highest upward zero crossings omit overhangs and camera occlusion',
            'Grid curvature diagnostic differs from the cited SPH neighborhood sum',
            '21m review domain, unverified rapid identity and inferred submerged bed'],
        source_sha256={name:hashlib.sha256((path/name).read_bytes()).hexdigest() for name in files})


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('snapshot',type=Path);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();result=analyze(args.snapshot)
    with args.output.open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    print(json.dumps(result,indent=2))
