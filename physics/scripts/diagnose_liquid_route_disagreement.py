"""Retain both survey-frame and float-upload-frame routing comparisons.

Diagnostic only: does not approve mismatches or change the routing auditor.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from liquid_dataset import resolve
from audit_liquid_particle_routes import physical_owners
from liquid_native_ownership import prepared_float_frame_owners


def diagnose(directory):
    directory=Path(directory).resolve();report=json.loads((directory/'stages.json').read_text())
    dataset=resolve(report)
    regions=[json.loads((dataset['regions']/f'region-{i:03d}.json').read_text()) for i in range(12)]
    differences=[];native_bad=0;total=0
    for r in report['native_transfer_packet']:
        n=r['particle_count'];total+=n
        p=np.fromfile(directory/r['positions'],dtype='<f4').reshape(n,4)[:,:3]
        routes=np.fromfile(directory/r['route_destinations'],dtype='<u4').reshape(n,4)
        ids=np.fromfile(directory/r['identities'],dtype='<i4').reshape(n,4)
        survey=physical_owners(p,regions)
        uploaded,q,exact,lower,axes=prepared_float_frame_owners(p,regions)
        observed=routes[:,0].astype(np.int64);observed[observed==0xffffffff]=-1
        native_bad+=int(np.count_nonzero(observed!=uploaded))
        for i in np.flatnonzero((observed!=survey)|(observed!=uploaded)):
            differences.append(dict(source_owner=r['region_id'],index=int(i),identity=ids[i].tolist(),
                                    position_cm=p[i].tolist(),survey_owner=int(survey[i]),
                                    reconstructed_upload_owner=int(uploaded[i]),gpu_owner=int(observed[i]),
                                    exact_float_input_local_cm=exact[i].tolist(),rounded_local_cm=q[i].tolist()))
    return dict(source_directory=str(directory),native_step=report['native_transfer_packet_step'],
                particles=total,disagreements=differences,upload_frame_mismatches=native_bad,
                reconstructed_lower_world_xy_cm=lower.tolist(),reconstructed_axes_world_xy=axes.tolist(),
                independent_routing_audit_modified=False,native_full_audit_accepted=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise FileExistsError(args.output)
    result=diagnose(args.directory)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(result,indent=2))
