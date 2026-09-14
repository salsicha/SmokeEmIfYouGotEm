"""Unchanged manufactured pressure-refinement probes with smooth geometry."""
import argparse
import hashlib
import json
from pathlib import Path
import audit_reconstructed_pressure_geometry as original
from smooth_pressure_geometry import SmoothPressureGeometry


def factory(h,b,dx,*,periodic,pressure_trace,bed_quadrature):
    if pressure_trace!='integrated_column' or bed_quadrature!='shared_bottom':
        raise ValueError('Only the registered integrated/shared-bottom candidate is supported')
    return SmoothPressureGeometry(h,b,dx,periodic=periodic)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True);args=parser.parse_args()
    if args.report.exists():raise FileExistsError(args.report)
    original.ReconstructedPressureGeometry=factory
    rows=original.refinement(pressure_trace='integrated_column',bed_quadrature='shared_bottom')
    report=dict(scope=__doc__,rows=rows,full_physical_model_or_gameplay_accepted=False,
        implementation_hashes={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in ('audit_smooth_pressure_refinement.py','audit_reconstructed_pressure_geometry.py','smooth_pressure_geometry.py')})
    with args.report.open('x') as stream:json.dump(report,stream,indent=2,allow_nan=False)
    print(json.dumps(report),flush=True)


if __name__=='__main__':main()
