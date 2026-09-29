"""Measure actual cached bank-spur flow; do not infer an eddy from foam alone."""
import argparse
import json
from pathlib import Path
import sys

import bpy
import numpy as np


def region(pos, vel, lo, hi):
    mask=np.all((pos>=lo)&(pos<hi),axis=1)
    values=vel[mask]
    return dict(bounds_m=[lo,hi], count=len(values),
                mean_velocity_mps=values.mean(axis=0).tolist() if len(values) else None,
                reverse_x_fraction=float(np.mean(values[:,0]<0)) if len(values) else None)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--calibration',type=Path,required=True)
    parser.add_argument('--frames',type=int,nargs='+',default=[192,216,240,264,288])
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():
        raise FileExistsError(args.output)
    setup=json.loads((Path(bpy.data.filepath).parent/'setup.json').read_text())
    cal=json.loads(args.calibration.read_text())
    if setup['case']!='eddy' or not cal['passed'] or cal['resolution']!=setup['resolution'] or cal['fps']!=setup['fps'] or cal['domain_dimensions_m']!=setup['dimensions_m'] or cal['blender']!=bpy.app.version_string:
        raise ValueError('Wrong case or calibration')
    bounds=np.array(setup['obstacle_bounds_m'])
    rows=[]
    for frame in args.frames:
        if not 1<=frame<=setup['frames']:
            raise ValueError('Frame outside bake')
        bpy.context.scene.frame_set(frame)
        obj=bpy.data.objects['Feature liquid'].evaluated_get(bpy.context.evaluated_depsgraph_get())
        ps=next(p for p in obj.particle_systems if p.name=='Liquid')
        pos,vel=np.empty(len(ps.particles)*3,np.float32),np.empty(len(ps.particles)*3,np.float32)
        ps.particles.foreach_get('location',pos)
        ps.particles.foreach_get('velocity',vel)
        pos,vel=pos.reshape(-1,3),vel.reshape(-1,3)*cal['inferred_raw_velocity_to_mps']
        if not len(pos) or not np.isfinite(pos).all() or not np.isfinite(vel).all():
            raise ValueError('Missing/nonfinite liquid particles')
        deep=np.all((pos>bounds[0]+.075)&(pos<bounds[1]-.075),axis=1)
        # Fixed regions declared from geometry, not selected after seeing signs.
        rows.append(dict(frame=frame,particles=len(pos),deep_inside_spur=int(deep.sum()),
            main_current=region(pos,vel,[3.15,-.65,.1],[4.5,-.15,.7]),
            bank_return=region(pos,vel,[3.2,.4,.1],[4.5,.7,.7]),
            behind_spur=region(pos,vel,[3.075,.1,.1],[3.45,.6,.7]),
            downstream_turn=region(pos,vel,[4.35,.05,.1],[4.85,.6,.7])))
    report=dict(source_blend=bpy.data.filepath,frames=rows,accepted=False,
                limitations='Narrow-band primary-particle means, not volume averages or tracked trajectories. Counterflow alone is not proof of a closed circulation path. Requires animation, shear-seam exchange and boundary sensitivity checks.')
    args.output.write_text(json.dumps(report,indent=2))
    print('EDDY_AUDIT',json.dumps(report),flush=True)


if __name__=='__main__':
    main()
