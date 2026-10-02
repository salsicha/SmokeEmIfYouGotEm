"""Read actual implicit wall zero surfaces; never move geometry or alter caches."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import openvdb


def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def crossings(values,positions):
    result=[]
    for i,(a,b) in enumerate(zip(values,values[1:])):
        if a==0:result.append(float(positions[i]))
        elif a*b<0:result.append(float(positions[i]+(-a/(b-a))*(positions[i+1]-positions[i])))
    if values[-1]==0:result.append(float(positions[-1]))
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('standard-root','fractional-root','zero-root','output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():raise FileExistsError(args.output)
    hashes={str(Path(__file__).resolve()):digest(__file__)};controls=[]
    for label,root in (('standard',args.standard_root),('fractional',args.fractional_root),('zero',args.zero_root)):
        proofpath=root/'padding-preflight.json';statepath=root/'domain-settings.json';proof=json.loads(proofpath.read_text());state=json.loads(statepath.read_text())
        for path in (proofpath,statepath):hashes[str(path.resolve())]=digest(path)
        origin=np.array(proof['origin_m']);h=.075;shape=(80,21,42);rows=[]
        for frame in (1,192):
            path=root/'cache'/'data'/f'fluid_data_{frame:04d}.vdb';hashes[str(path.resolve())]=digest(path);fields={}
            for name in ('phi_obstacle','phi'):
                grid=openvdb.read(str(path),name)
                if tuple(grid.metadata['file_base_resolution'])!=shape:raise ValueError('Shape differs')
                a=np.empty(shape,np.float32);grid.copyToArray(a)
                if not np.isfinite(a).all():raise ValueError('Nonfinite native field')
                fields[name]=a
            profiles=[]
            for name,axis,fixed in (('dry_longitudinal_wall',0,(10,26)),('dry_lateral_wall',1,(54,26)),
                ('submerged_lateral_wall',1,(54,7)),('downstream_bed',2,(54,10))):
                sl=[slice(None)]*3;others=[i for i in range(3) if i!=axis]
                for i,v in zip(others,fixed):sl[i]=v
                world=origin[axis]+(np.arange(shape[axis])+.5)*h
                obs=fields['phi_obstacle'][tuple(sl)];liquid=fields['phi'][tuple(sl)]
                point=origin.copy()
                for i,v in zip(others,fixed):point[i]+=(v+.5)*h
                profiles.append(dict(name=name,axis=axis,fixed_native_indices=list(fixed),fixed_world_coordinates_m=point.tolist(),
                    coordinates_m=world.tolist(),obstacle_cells=obs.tolist(),liquid_cells=liquid.tolist(),
                    obstacle_zero_world_m=crossings(obs,world),liquid_zero_world_m=crossings(liquid,world)))
            rows.append(dict(frame=frame,profiles=profiles))
        controls.append(dict(label=label,root=str(root.resolve()),origin_m=origin.tolist(),cell_m=h,shape=list(shape),
            fractions=state['use_fractions'],clearance_cells=state['fractions_distance'],frames=rows))
    if any(c['origin_m']!=controls[0]['origin_m'] for c in controls):raise ValueError('World origins differ')
    if any(digest(p)!=sha for p,sha in hashes.items()):raise ValueError('Pinned source changed')
    report=dict(complete=True,accepted=False,originals_unchanged=True,dependency_sha256=hashes,controls=controls,scope=__doc__,
        caveats='Linear center-profile crossings, not exhaustive 3D collider/pressure or exact-volume attribution. Dry probes are above authored bed/spur. Submerged cross-section is downstream of spur; native liquid phi is also retained. No padding, clipping, clearance/radius fitting or source change applied.')
    with args.output.open('x') as stream:json.dump(report,stream,indent=2)
    print('FRACTIONAL_WALL_PROFILES_COMPLETE',[(c['label'],[(p['name'],p['obstacle_zero_world_m']) for p in c['frames'][0]['profiles']]) for c in controls],flush=True)


if __name__=='__main__':main()
