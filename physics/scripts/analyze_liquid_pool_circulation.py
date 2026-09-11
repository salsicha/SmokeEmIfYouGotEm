"""Actual 3-D pool velocity, including submerged cells, in the bounded review.

An instantaneous signed-velocity inventory, not a hydraulic-jump acceptance
test. Local x is the registered downstream axis; bends/oblique return flow
require a streamline or time-resolved analysis beyond this fixed box.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from analyze_liquid_grid_readback import load_fields


def analyze(fields, lateral=.37803957956263945):
    velocity=np.asarray(fields['Velocity'])/100
    if velocity.shape!=(24,68,68,3) or not np.isfinite(velocity).all():
        raise ValueError('Finite registered 68x68x24 velocity field required')
    z,y,x=np.meshgrid((np.arange(24)+.5)*8/24+3.5,
                     (np.arange(68)+.5)*21/64-11.15625,
                     (np.arange(68)+.5)*21/64-11.15625,indexing='ij')
    wet=np.rint(fields['SolidVelocity_Boundary'][...,3])==0
    pool=wet&(x>-1)&(x<7)&(abs(y-lateral)<2)
    def summary(mask):
        v=velocity[mask]
        return dict(fluid_cells=len(v),
                    velocity_xyz_quantiles_m_s=np.quantile(v,[0,.1,.5,.9,1],axis=0).tolist() if len(v) else [],
                    upstream_fraction=float(np.mean(v[:,0]<-.05)) if len(v) else None,
                    rising_fraction=float(np.mean(v[:,2]>.05)) if len(v) else None,
                    falling_fraction=float(np.mean(v[:,2]<-.05)) if len(v) else None)
    return dict(schema='raftsim.liquid_pool_circulation.v1',
                bounds=dict(station_m=[-1,7],lateral_m=[lateral-2,lateral+2]),
                signed_speed_threshold_m_s=.05,quantile_probabilities=[0,.1,.5,.9,1],
                pool=summary(pool),
                layers=[dict(datum_z_m=float(z[k,0,0]),**summary(pool&(np.arange(24)[:,None,None]==k))) for k in range(24) if pool[k].any()],
                physical_or_visual_acceptance=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('directory',type=Path)
    args=parser.parse_args();output=args.directory/'pool_circulation.json'
    if output.exists():raise FileExistsError(output)
    capture=json.loads((args.directory/'capture.json').read_text())
    if not capture['complete'] or capture.get('error'):raise ValueError('Completed capture required')
    grids=args.directory/f"terrain_{capture['simulation_steps']:04d}_grids"
    report=analyze(load_fields(grids));report['simulation_seconds']=capture['simulation_steps']/60
    report['source_sha256']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [args.directory/'capture.json',*sorted(grids.iterdir())] if p.is_file()}
    output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('layers','source_sha256')},indent=2))
