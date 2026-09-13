"""Localize native/survey outer-boundary disagreements without waiving them."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from liquid_dataset import resolve
from audit_liquid_native_handoff import read
from audit_liquid_particle_routes import physical_owners
from liquid_native_ownership import prepared_float_frame_owners


def diagnose(root):
    root=root.resolve();d=json.loads((root/'stages.json').read_text());dataset=resolve(d)
    regions=[json.loads((dataset['regions']/f'region-{i:03d}.json').read_text()) for i in range(12)]
    bounds=np.array([r['bounds_station_lateral_m'] for r in regions]);lo=bounds[:,0].min(0);hi=bounds[:,1].max(0)
    axes=np.array([regions[0]['axis_x_canonical'],regions[0]['axis_y_canonical']])[:,:2]
    details=[];total=0;exact_false_inside=0;exact_false_outside=0;rounded_false_outside=0
    for r in d['native_transfer_packet']:
        n=r['particle_count'];p=read(root,r,'positions',(n,4)).view('<f4')[:,:3].astype(float)
        ids=read(root,r,'identities',(n,4));survey=physical_owners(p,regions)
        uploaded,q,exact,lower,world_axes=prepared_float_frame_owners(p,regions)
        extent=(hi-lo)*100;exact_inside=((exact>=0)&(exact<=extent)).all(axis=1)
        exact_false_inside+=int(((survey<0)&exact_inside).sum())
        exact_false_outside+=int(((survey>=0)&~exact_inside).sum())
        rounded_false_outside+=int(((survey>=0)&(uploaded<0)).sum());total+=n
        for i in np.flatnonzero((survey<0)&(uploaded>=0)):
            station_lateral=(p[i,:2]*[1,-1])@axes.T/100
            details.append(dict(storage_owner=r['region_id'],row=int(i),identity=ids[i].astype(int).tolist(),
                position_world_cm=p[i].tolist(),station_lateral_m=station_lateral.tolist(),
                uploaded_rounded_local_cm=q[i].tolist(),exact_uploaded_frame_local_cm=exact[i].tolist(),
                maximum_survey_exterior_distance_cm=float(np.maximum(lo-station_lateral,station_lateral-hi).max()*100),
                exact_uploaded_frame_also_outside=bool(not exact_inside[i]),
                uploaded_lower_world_cm=lower.tolist(),uploaded_axes_world=world_axes.tolist()))
    return dict(particles=total,survey_lower_station_lateral_m=lo.tolist(),survey_upper_station_lateral_m=hi.tolist(),
        rounded_native_false_inside_particles=len(details),rounded_native_false_outside_particles=rounded_false_outside,
        unrounded_uploaded_frame_false_inside_particles=exact_false_inside,
        unrounded_uploaded_frame_false_outside_particles=exact_false_outside,details=details,
        native_stages_sha256=hashlib.sha256((root/'stages.json').read_bytes()).hexdigest(),
        boundary_tolerance_added=False,physical_domain_expanded=False,particles_modified=False,
        native_boundary_fix_installed=d.get('native_physical_frame_model')=='double-float-residual-outer-v2',
        declared_native_frame_model=d.get('native_physical_frame_model'),
        physical_visual_or_performance_acceptance=False)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('capture',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise FileExistsError(a.output)
    result=diagnose(a.capture);a.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps(result,indent=2))
