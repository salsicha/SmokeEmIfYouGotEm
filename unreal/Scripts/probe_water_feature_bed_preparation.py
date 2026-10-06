"""Owned native obstacle-preparation controls at unchanged world bed elevations."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import bpy
import manta
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from probe_water_feature_native_transport import actual_space,scalar_view
from probe_water_feature_solver_stages import grid_array,cleanup


def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def run(shape,bed_cells):
    scope={};error=None;result=None
    try:
        scope['s99']=manta.Solver(name='owned_bed_preparation',gridSize=manta.vec3(*shape),dim=3)
        for name,kind in (('obs',manta.LevelsetGrid),('obj',manta.LevelsetGrid),('flags',manta.FlagGrid)):
            scope[name+'_s99']=scope['s99'].create(kind,name='owned_'+name)
        phi=np.broadcast_to(np.arange(shape[2])[None,None,:]+.5-bed_cells,shape).astype(np.float32).copy()
        view=scalar_view(scope['obj_s99'],shape);view[:]=phi;del view
        scope['obs_s99'].setConst(9999)
        scope['flags_s99'].initDomain(boundaryWidth=0,phiWalls=scope['obs_s99'],outflow='Z')
        stages=[('analytic_obj',phi.copy())]
        scope['obj_s99'].floodFill(boundaryWidth=1)
        stages.append(('obj_after_fill',grid_array(scope['obj_s99'],shape)))
        manta.extrapolateLsSimple(phi=scope['obj_s99'],distance=6,inside=True)
        manta.extrapolateLsSimple(phi=scope['obj_s99'],distance=3,inside=False)
        stages.append(('obj_after_extrapolate',grid_array(scope['obj_s99'],shape)))
        scope['obs_s99'].join(scope['obj_s99']);scope['obs_s99'].floodFill(boundaryWidth=1)
        manta.extrapolateLsSimple(phi=scope['obs_s99'],distance=6,inside=True)
        manta.extrapolateLsSimple(phi=scope['obs_s99'],distance=3)
        stages.append(('final_obstacle',grid_array(scope['obs_s99'],shape)))
        x,y=shape[0]//2,shape[1]//2
        result=dict(shape=list(shape),bed_cells=bed_cells,stages=[dict(name=n,center_column=a[x,y,:12].tolist()) for n,a in stages])
    except Exception as exc:error=f'{type(exc).__name__}: {exc}';exc.__traceback__=None
    finally:cleanup(scope,'99')
    if error:raise RuntimeError(error)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():raise FileExistsError(args.output)
    root=Path(bpy.data.filepath).resolve().parent
    if root.name!='eddy-temporal-resume-v6-m2':raise ValueError('Preserved host required')
    bpy.data.objects['Feature liquid'].modifiers[0].domain_settings.cache_directory=str(root/'cache')
    bpy.context.scene.frame_set(193);space,identifier=actual_space((80,21,39))
    before={n:hashlib.sha256(grid_array(space[f'{n}_s{identifier}'],(80,21,39)).tobytes()).hexdigest() for n in ('phi','phiTmp')}
    rows=[run((80,21,39+padding),1.5+padding+phase) for padding in (0,3) for phase in (-1e-6,0.,1e-6)]
    if any(hashlib.sha256(grid_array(space[f'{n}_s{identifier}'],(80,21,39)).tobytes()).hexdigest()!=s for n,s in before.items()):
        raise ValueError('Owned preparation changed actual phi')
    dependencies={str(Path(__file__).resolve()):digest(Path(__file__)),str((root/'feature.blend').resolve()):digest(root/'feature.blend')}
    with args.output.open('x') as stream:json.dump(dict(complete=True,accepted=False,rows=rows,dependency_sha256=dependencies,
        actual_phi_unchanged=True,scope='Native obstacle preparation only; synthetic plane,not host mesh rasterization/full pressure/evolution or acceptance.'),stream,indent=2)
    print('BED_PREPARATION_COMPLETE',flush=True)
    for r in rows:print('PREPARATION',r,flush=True)


if __name__=='__main__':main()
