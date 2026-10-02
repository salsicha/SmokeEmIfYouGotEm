"""Owned native explicit-wall preparation before any new scene bake.

Tests analytic planes only, not actual Blender mesh voxelization or hydraulics.
"""
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
from water_feature_field_surface import sample_centers
from water_feature_cell_volume import reconstructed_volume


def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def run(fractional):
    shape=(90,31,42);h=.075;origin=np.array([-.375,-1.1625,-.3375]);scope={};error=None;result=None
    xyz=np.stack(np.meshgrid(*[origin[i]+(np.arange(n)+.5)*h for i,n in enumerate(shape)],indexing='ij'),axis=-1)
    x,y,z=xyz[...,0],xyz[...,1],xyz[...,2]
    analytic=np.minimum.reduce([x,6-x,y+.8,.8-y,z]).astype(np.float32)/h
    stations=np.array([[4.05,0,0],[4.05,-.8,.75],[4.05,.8,.75],[0,0,.9],[6,0,.9]])
    try:
        scope['s99']=manta.Solver(name='owned_explicit_wall_control',gridSize=manta.vec3(*shape),dim=3)
        for name,kind in (('obs',manta.LevelsetGrid),('obj',manta.LevelsetGrid),('flags',manta.FlagGrid)):
            scope[name+'_s99']=scope['s99'].create(kind,name='owned_'+name)
        view=scalar_view(scope['obj_s99'],shape);view[:]=analytic;del view
        scope['obs_s99'].setConst(9999)
        scope['flags_s99'].initDomain(boundaryWidth=1 if fractional else 0,phiWalls=scope['obs_s99'],outflow='Z')
        scope['obj_s99'].floodFill(boundaryWidth=1)
        manta.extrapolateLsSimple(phi=scope['obj_s99'],distance=6,inside=True)
        manta.extrapolateLsSimple(phi=scope['obj_s99'],distance=3,inside=False)
        scope['obs_s99'].join(scope['obj_s99']);scope['obs_s99'].floodFill(boundaryWidth=2 if fractional else 1)
        manta.extrapolateLsSimple(phi=scope['obs_s99'],distance=6,inside=True)
        manta.extrapolateLsSimple(phi=scope['obs_s99'],distance=3)
        final=grid_array(scope['obs_s99'],shape)
        zeros=sample_centers(final,(stations-origin)/h)
        volume=reconstructed_volume((z-.8).astype(np.float32)/h,final,(h,h,h),8)
        result=dict(fractional=fractional,shape=list(shape),origin_m=origin.tolist(),cell_m=h,
            stations_m=stations.tolist(),final_station_phi_cells=zeros.tolist(),
            maximum_station_error_m=float(np.max(np.abs(zeros))*h),
            analytic_box_expected_volume_m3=6*1.6*.8,reconstructed_test_volume=volume,
            analytic_scope='Infinite solid exterior of five planar walls; liquid test top0.8m. Not original sloping bed/spur or host mesh voxelization.')
    except Exception as exc:error=f'{type(exc).__name__}: {exc}';exc.__traceback__=None
    finally:cleanup(scope,'99')
    if error:raise RuntimeError(error)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():raise FileExistsError(args.output)
    source=Path(bpy.data.filepath).resolve();root=source.parent
    if root.name!='eddy-padded-fractional-zero-v1':raise ValueError('Preserved installed-native host required')
    bpy.data.objects['Feature liquid'].modifiers[0].domain_settings.cache_directory=str(root/'cache')
    bpy.context.scene.frame_set(193);space,identifier=actual_space((80,21,42))
    before={n:hashlib.sha256(grid_array(space[f'{n}_s{identifier}'],(80,21,42)).tobytes()).hexdigest() for n in ('phi','phiTmp')}
    rows=[run(mode) for mode in (False,True)]
    if any(hashlib.sha256(grid_array(space[f'{n}_s{identifier}'],(80,21,42)).tobytes()).hexdigest()!=sha for n,sha in before.items()):raise ValueError('Owned probe changed engine fields')
    difference=abs(rows[0]['reconstructed_test_volume']['volume_m3']-rows[1]['reconstructed_test_volume']['volume_m3'])
    passed=all(r['maximum_station_error_m']<4e-6 for r in rows) and difference<1e-8
    hashes={str(p.resolve()):digest(p) for p in (source,Path(__file__))}
    for name in ('probe_water_feature_native_transport.py','probe_water_feature_solver_stages.py','water_feature_field_surface.py','water_feature_cell_volume.py'):
        p=Path(__file__).with_name(name);hashes[str(p.resolve())]=digest(p)
    with args.output.open('x') as stream:json.dump(dict(complete=True,accepted=False,passed=passed,rows=rows,
        paired_volume_difference_m3=difference,actual_phi_unchanged=True,dependency_sha256=hashes,scope=__doc__),stream,indent=2)
    print('EXPLICIT_WALL_KERNEL_PREFLIGHT',passed,[(r['maximum_station_error_m'],r['reconstructed_test_volume']['volume_m3']) for r in rows],difference,flush=True)
    if not passed:raise ValueError('Analytic native wall preparation failed; do not bake')


if __name__=='__main__':main()
