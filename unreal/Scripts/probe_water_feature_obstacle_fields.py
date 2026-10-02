"""Read-only authored-bed/native-obstacle/flag profiles; no solve or cache write."""
import argparse
import dis
import hashlib
import json
from pathlib import Path
import sys
import types
import bpy
import numpy as np
import openvdb

sys.path.insert(0,str(Path(__file__).resolve().parent))
from probe_water_feature_native_transport import actual_space
from probe_water_feature_solver_stages import grid_array
from audit_water_feature_native_mac_extension import native_view
from water_feature_field_surface import sample_centers
from water_feature_solid_clip import EDDY_SOLIDS


def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():raise FileExistsError(args.output)
    prior=json.loads(args.reference.read_text());hashes=dict(prior['dependency_sha256'])
    hashes[str(args.reference.resolve())]=digest(args.reference);hashes[str(Path(__file__).resolve())]=digest(Path(__file__))
    if not prior['complete'] or prior['accepted'] or any(digest(p)!=s for p,s in hashes.items()):
        raise ValueError('Unchanged complete diagnostic reference required')
    root=Path(bpy.data.filepath).resolve().parent
    if root.name!='eddy-temporal-resume-v6-m2':raise ValueError('Matched native scene required')
    scene=bpy.context.scene;domain=bpy.data.objects['Feature liquid'];state=domain.modifiers[0].domain_settings
    state.cache_directory=str(root/'cache');scene.frame_set(193)
    space,identifier=actual_space((80,21,39));h=.075
    origin=np.asarray(domain.matrix_world.translation)-np.array([80,21,39])*h/2
    # Explicit authored surface points, independently selected before sampling.
    stations=[dict(name='downstream_floor',point=[4.05,0,0],normal=[0,0,1]),
        dict(name='approach_plateau',point=[.45,0,.45],normal=[0,0,1]),
        dict(name='spur_front',point=[2.70,.05,.5],normal=[0,-1,0]),
        dict(name='spur_downstream',point=[3.,.30,.5],normal=[1,0,0])]
    offsets=np.array([-.10,-.075,-.05,-.025,-.0125,0,.0125,.025,.05,.075,.1])
    effectors=[]
    for name in EDDY_SOLIDS:
        obj=bpy.data.objects[name];mod=[m for m in obj.modifiers if m.type=='FLUID'][0];eff=mod.effector_settings
        effectors.append(dict(name=name,matrix=[list(r) for r in obj.matrix_world],hide_render=obj.hide_render,
            modifier_show_viewport=mod.show_viewport,modifier_show_render=mod.show_render,
            settings={k:getattr(eff,k) for k in ('effector_type','use_effector','surface_distance','use_plane_init','subframes')
                if hasattr(eff,k)}))
    functions=[]
    for name,value in sorted(space.items()):
        if not isinstance(value,types.FunctionType) or not name.endswith('_'+identifier):continue
        if not any('phiObs' in str(n) or 'flags' in str(n) for n in value.__code__.co_names):continue
        functions.append(dict(name=name,global_names=list(value.__code__.co_names),
            compiled_instructions=[dict(offset=i.offset,opname=i.opname,argrepr=i.argrepr)
                for i in dis.get_instructions(value)]))
    rows=[]
    for frame in (193,217,239):
        scene.frame_set(frame);space,identifier=actual_space((80,21,39));fields={};checks=[]
        path=root/'cache'/'data'/f'fluid_data_{frame:04d}.vdb'
        for cache,key,dtype in (('phi_obstacle','phiObs',np.float32),('phi_obstacle_inflow','phiObsIn',np.float32),
                ('phi','phi',np.float32),('flags','flags',np.int32)):
            grid=openvdb.read(str(path),cache);array=np.empty((80,21,39),dtype);grid.copyToArray(array)
            actual=(native_view(space[f'{key}_s{identifier}'],(80,21,39),integer=True).copy() if key=='flags'
                else grid_array(space[f'{key}_s{identifier}'],(80,21,39)))
            checks.append(dict(field=cache,native_vdb_difference_count=int(np.count_nonzero(actual!=array)),
                maximum_difference=float(np.abs(actual.astype(float)-array).max())))
            fields[cache]=array
        profiles=[]
        for station in stations:
            points=np.array(station['point'])+offsets[:,None]*np.array(station['normal'])
            base=(points-origin)/h
            inside=np.all((base>=.5)&(base<=np.array([80,21,39])-.5),axis=1)
            indices=np.floor(base[inside]).astype(int)
            profiles.append(dict(**station,offset_into_fluid_m=offsets[inside].tolist(),world_points_m=points[inside].tolist(),
                field_values_cells={k:sample_centers(v,base[inside]).tolist() for k,v in fields.items() if k!='flags'},
                native_containing_cell_flags=fields['flags'][indices[:,0],indices[:,1],indices[:,2]].tolist(),
                unsupported_offsets_m=offsets[~inside].tolist()))
        # Raw center-line profile: includes exact flags rather than interpolating
        # categorical values. Distinguish field support from closed-boundary flags.
        columns=[]
        for x,y in ((54,10),(6,10),(36,10)):
            columns.append(dict(column=[x,y],world_z_m=(origin[2]+(np.arange(16)+.5)*h).tolist(),
                fields={k:v[x,y,:16].tolist() for k,v in fields.items()}))
        rows.append(dict(frame=frame,native_vdb_checks=checks,profiles=profiles,columns=columns))
    if any(digest(p)!=s for p,s in hashes.items()):raise ValueError('Preserved evidence changed during read-only probe')
    report=dict(complete=True,accepted=False,originals_unchanged=True,dependency_sha256=hashes,
        actual_origin_m=origin.tolist(),cell_m=h,effectors=effectors,compiled_boundary_functions=functions,frames=rows,
        domain_settings={k:getattr(state,k) for k in ('use_fractions','simulation_method','use_collision_border_bottom',
            'use_collision_border_front','use_collision_border_back','use_collision_border_left','use_collision_border_right')},
        scope='Native cached fields read independently from VDB and actual host; loaded fields can differ from live pre-step generation. No boundary/solver edit, particle projection, new mesh/bake or acceptance.')
    with args.output.open('x') as stream:json.dump(report,stream,indent=2)
    print('OBSTACLE_PROFILE_COMPLETE',args.output,flush=True)
    for row in rows:
        print('FRAME_NATIVE_CHECKS',row['frame'],row['native_vdb_checks'],flush=True)
        for profile in row['profiles']:
            index=profile['offset_into_fluid_m'].index(0.)
            print('AUTHORED_SURFACE',profile['name'],{k:v[index] for k,v in profile['field_values_cells'].items()},
                'FLAG',profile['native_containing_cell_flags'][index],flush=True)


if __name__=='__main__':main()
