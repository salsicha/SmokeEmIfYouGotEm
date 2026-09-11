"""Conservative native-face to wet subface source table for the crux FLIP window."""
from pathlib import Path
import json
import hashlib
import numpy as np
from build_south_fork_liquid_window import bilinear, boundary_profiles
from south_fork_registered_mesh import RegisteredMeshSampler
from build_south_fork_liquid_grid_boundary import DRY_FACE_NOISE_M3S
from liquid_domain import layout

ROOT=Path(__file__).resolve().parents[2]


def split_face_discharge(discharge, depths, width):
    depths=np.asarray(depths,dtype=float)
    if not np.isfinite(width) or width<=0:
        raise ValueError('Finite positive subface width required')
    if not np.isfinite(depths).all() or (depths<0).any() or not np.isfinite(discharge):
        raise ValueError('Finite discharge and nonnegative depths required')
    area=float(depths.sum()*width)
    if area<=0:
        if discharge!=0: raise ValueError('Nonzero numerical flux has no actual wet support')
        return np.zeros_like(depths),0.
    velocity=discharge/area
    return velocity*depths*width,velocity


def unresolved_outgoing_dry_noise(discharge,depths):
    """Only tiny OUTGOING dry-face noise; never remove required inflow.

    The existing ghost-boundary model already declares this allowance. Keep
    the signed unresolved target in the report instead of pretending it is a
    resolved wet subface. The strict wet-face conservation gate is unchanged.
    """
    depths=np.asarray(depths,dtype=float)
    return bool(np.isfinite(discharge) and np.isfinite(depths).all() and
        np.all(depths==0) and -DRY_FACE_NOISE_M3S<=discharge<0)


def main(directory=None,audit=None,physical_cells=None):
    directory=Path(directory) if directory is not None else ROOT/'unreal/SourceArt/RaftSim/SouthForkLiquidWindow20260908'
    output=directory/'native_source_profile.json'
    if output.exists(): raise FileExistsError('Retain the earlier source profile')
    solid=json.loads((directory/'manifest.json').read_text())
    geometry=json.loads((ROOT/solid['source_geometry_manifest']).read_text())
    mesh_path=ROOT/geometry['mesh_path']
    if hashlib.sha256(mesh_path.read_bytes()).hexdigest()!=geometry['mesh_sha256']:
        raise ValueError('Captured geometry changed')
    mesh=np.load(mesh_path);sampler=RegisteredMeshSampler(mesh)
    hydraulic=ROOT/solid['source_hydraulic_directory']
    flow=json.loads((hydraulic/'manifest.json').read_text())
    registration=json.loads((hydraulic.parent/'registration.json').read_text())
    audit=Path(audit) if audit is not None else ROOT/'docs/reconstruction-review-2026-09-07/liquid-native-face-flux'
    native=json.loads((audit/'report.json').read_text())
    if not native['passed'] or native['source_geometry_sha256']!=geometry['mesh_sha256']:
        raise ValueError('Native flux audit does not match geometry')
    if hashlib.sha256((hydraulic/'manifest.json').read_bytes()).hexdigest()!=native['source_hydraulic_manifest_sha256']:
        raise ValueError('Hydraulic identity changed')
    if hashlib.sha256((audit/'native_faces.npz').read_bytes()).hexdigest()!=native['faces_sha256']:
        raise ValueError('Native flux bytes changed')
    fields={}
    for name,record in flow['bands'][0]['arrays'].items():
        path=hydraulic/record['file']
        if hashlib.sha256(path.read_bytes()).hexdigest()!=record['sha256']:
            raise ValueError('Changed hydraulic array')
        fields[name]=np.load(path)
    downstream,left=(np.array(registration[k]) for k in ('downstream_unit','left_unit'))
    rotation=np.column_stack((downstream,left))
    domain=layout(solid,native,physical_cells)
    centre=np.asarray(domain['centre_station_lateral_m'])
    extent=np.asarray(domain['physical_extents_m'][:2])
    if flow['grid']['dx_m']!=1 or flow['grid']['dy_m']!=1:
        raise ValueError('Current native subface export requires one-metre source cells')
    profiles=boundary_profiles(fields,flow['grid'],centre,extent,.125,sampler,downstream,left)
    centre_en=centre@rotation.T
    floor=solid['local_origin_engine_cm'][2]/100
    points,velocities,weights,source_ids=[],[],[],[]
    resolved=[];unresolved_outgoing=[];max_error=0.;minimum_clearance=float('inf')
    for name,profile in zip(('west','east','south','north'),profiles):
        inward=-np.array(profile['outward_normal_station_lateral'],dtype=float)
        if len(profile['samples'])!=8*len(native['face_discharge_m3_per_s'][name]):
            raise ValueError('Native face and subface counts disagree')
        for face,q in enumerate(native['face_discharge_m3_per_s'][name]):
            cells=profile['samples'][face*8:(face+1)*8]
            # Place source points 1 cm inside the numerical face and check the
            # ACTUAL bed there; no fallback to a sphere or coarse bed raster.
            sl=np.array([c['station_lateral_m'] for c in cells])+inward*.01
            en=sl@rotation.T
            bed=sampler.sample(en[:,0],en[:,1])
            stage=np.array([c['stage_relative_datum_m'] for c in cells])
            depths=np.maximum(stage-bed,0)
            if unresolved_outgoing_dry_noise(q,depths):
                unresolved_outgoing.append(dict(face=name,cell=face,
                    numerical_inward_discharge_m3s=q,wet_area_m2=0.,
                    status='Unresolved outgoing dry-face noise, not emitted or resolved',
                    boundary_model_allowance_m3s=DRY_FACE_NOISE_M3S))
                continue
            shares,normal_speed=split_face_discharge(q,depths,.125)
            error=abs(float(shares.sum())-q);max_error=max(max_error,error)
            if error>1e-10: raise ValueError('Subface remap lost numerical discharge')
            resolved.append({'face':name,'cell':face,'numerical_inward_discharge_m3s':q,
                             'wet_area_m2':float(depths.sum()*.125),
                             'inward_normal_velocity_mps':normal_speed,
                             'subface_discharge_m3s':shares.tolist()})
            if q<=0: continue  # Export outgoing targets, never emit outgoing water.
            for i,weight in enumerate(shares):
                if weight<=0: continue
                coarse_depth=cells[i]['source_depth_m']
                velocity=np.array(cells[i]['momentum_m2_per_s'])/max(coarse_depth,1e-9)
                velocity+=inward*(normal_speed-float(velocity@inward))
                world_velocity=rotation@velocity
                for layer in range(16):
                    z=bed[i]+depths[i]*(layer+.5)/16
                    minimum_clearance=min(minimum_clearance,z-bed[i])
                    points.append([(en[i,0]-centre_en[0])*100,(en[i,1]-centre_en[1])*100,(z-floor)*100])
                    velocities.append([world_velocity[0]*100,world_velocity[1]*100,0.])
                    weights.append(float(weight/16))
                    source_ids.append([name,face,i,layer])
    intended=sum(max(q,0) for values in native['face_discharge_m3_per_s'].values() for q in values)
    if abs(sum(weights)-intended)>1e-9: raise ValueError('Source distribution lost inflow')
    if not np.isfinite(points).all() or not np.isfinite(velocities).all() or minimum_clearance<=0:
        raise ValueError('Invalid source position/velocity')
    particle_volume=domain['nominal_particle_volume_m3']
    report={'schema':'raftsim.native_face_liquid_source.v1' if domain['legacy_fixture'] else 'raftsim.native_face_liquid_source.v2',
            'source_geometry_sha256':geometry['mesh_sha256'],
            'native_flux_report_sha256':hashlib.sha256((audit/'report.json').read_bytes()).hexdigest(),
            'solid_sha256':solid['solid_sha256'],
            'positions_world_offset_cm':points,'velocities_world_cm_per_s':velocities,
            'weights_m3_per_s':weights,'source_face_subface_layer':source_ids,
            'resolved_faces':resolved,'total_inflow_m3_per_s':intended,
            'unresolved_outgoing_dry_faces':unresolved_outgoing,
            'unresolved_outgoing_dry_flux_m3_per_s':sum(f['numerical_inward_discharge_m3s'] for f in unresolved_outgoing),
            'maximum_subface_flux_error_scope':'Wet supported faces only; unresolved outgoing noise separately reported',
            'maximum_subface_flux_error_m3_per_s':max_error,
            'minimum_source_bed_clearance_m':minimum_clearance,
            'max_source_speed_m_per_s':float(np.linalg.norm(velocities,axis=1).max()/100),
            'grid_extents_cm':(np.asarray(domain['physical_extents_m'])*100).tolist(),
            'num_cells_max_axis':max(domain['physical_cells']),'particles_per_cell':4,
            'domain':domain,
            'nominal_particle_volume_m3':particle_volume,
            'requested_spawn_particles_per_second':intended/particle_volume,
            'source_layer_placement':'16 vertical quadrature centres, 1 cm inside each native boundary face',
            'spawn_volume_calibrated_in_engine':False,'engine_3d_coupled':False,'production_promoted':False}
    output.write_text(json.dumps(report,separators=(',',':'))+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in (
        'positions_world_offset_cm','velocities_world_cm_per_s','weights_m3_per_s',
        'source_face_subface_layer','resolved_faces')},indent=2))


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory',type=Path);parser.add_argument('--audit',type=Path)
    parser.add_argument('--physical-cells',type=int,nargs=2)
    args=parser.parse_args();main(args.directory,args.audit,args.physical_cells)
