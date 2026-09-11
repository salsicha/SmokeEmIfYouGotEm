"""Independent captured CPU/GPU particle-to-density parity; not scene acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from liquid_anisotropic_surface import upper_surface


def audit(directory):
    report=json.loads((directory/'report.json').read_text())
    source=Path(report['source_directory'])
    manifest=json.loads((source/'report.json').read_text())
    reference=Path(manifest['reference'])
    identities=(hashlib.sha256(reference.read_bytes()).hexdigest()==manifest['reference_sha256'] and
                hashlib.sha256((directory/'positions.rgba32f').read_bytes()).hexdigest()==manifest['positions_sha256'])
    with np.load(reference) as data:
        expected=data['density']
        matrix=data['matrix']
        weight=data['sample_volumes']*np.linalg.det(matrix)
        minimum,extent=[data[k] for k in ('minimum','extent')]
    count=manifest['count']
    actual=np.fromfile(directory/'density.u32',dtype='<u4').reshape(expected.shape)/report['fixed_point_scale']
    rows=np.fromfile(directory/'kernels.rgba32f',dtype='<f4').reshape(count,3,4).astype(float)
    scalar=np.fromfile(directory/'scalar_readback.r32f',dtype='<f4').reshape(expected.shape).astype(float)
    error=actual-expected
    matrix_error=abs(rows[:,:,:3]-matrix)
    weight_relative=abs(rows[:,0,3]-weight)/np.maximum(abs(weight),1e-12)
    a,b=[upper_surface(rho,minimum,extent) for rho in (expected,actual)]
    common=np.isfinite(a)&np.isfinite(b)
    top_error=a[common]-b[common]
    scalar_error=abs(scalar-(.5-actual))
    finite=bool(np.isfinite(rows).all() and np.isfinite(scalar).all())
    values=dict(identities_verified=identities,diagnostics=report['diagnostics'],finite=finite,
                kernel_matrix_max_error_per_m=float(matrix_error.max()),
                kernel_weight_max_relative_error=float(weight_relative.max()),
                density_max_error=float(abs(error).max()),density_rms_error=float(np.sqrt(np.mean(error**2))),
                r32_readback_scalar_max_error=float(scalar_error.max()),
                top_common_columns=int(common.sum()),top_crossing_presence_matches=bool(np.array_equal(np.isfinite(a),np.isfinite(b))),
                top_height_rms_error_m=float(np.sqrt(np.mean(top_error**2))),top_height_max_error_m=float(abs(top_error).max()),
                gpu_dispatch_and_diagnostic_copy_ms=report['gpu_dispatch_and_diagnostic_copy_ms'],
                live_particle_source_connected=False,physical_or_visual_acceptance=False)
    # Predeclared numerical precision gates. Never loosen them to turn a bad
    # shape or missing particle population into a green check.
    values['numerical_parity_passed']=bool(identities and finite and report['diagnostics']==[0,0,0,0] and
        matrix_error.max()<=5e-4 and weight_relative.max()<=1e-3 and abs(error).max()<=5e-4 and
        scalar_error.max()<=5e-4 and values['top_crossing_presence_matches'] and
        values['top_height_rms_error_m']<=.001 and values['top_height_max_error_m']<=.01)
    return values


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result=audit(args.directory)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['numerical_parity_passed'] else 1)
