"""Reuse the original energy-direction check with the connected scalar binding.

Only the check's explicit forcing context changes. Its actual FV direction,
two pressure poles, three central-difference probes and error gate remain.
"""
import argparse
import hashlib
import json
from pathlib import Path
import audit_rational_energy_direction as original
from periodic_connected_scalar_reference import periodic_connected_gradients
from pressure_cut_endpoint_reference import exact_endpoint_cuts


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True);args=parser.parse_args()
    if args.report.exists():raise FileExistsError(args.report)
    binding=original.difference_scalar_gradients
    results=[]
    try:
        original.difference_scalar_gradients=periodic_connected_gradients
        with exact_endpoint_cuts():
            for seed in (2204,2205):
                result=original.check(seed,64)
                result['scalar']='periodic_connected_depth_weighted'
                results.append(result);print(json.dumps(result),flush=True)
    finally:
        original.difference_scalar_gradients=binding
    report=dict(scope=__doc__,cases=results,original_probes_and_gates_unchanged=True,
        implementation_hashes={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in ('audit_connected_energy_direction.py','audit_rational_energy_direction.py',
                         'periodic_connected_scalar_reference.py','reconstructed_energy_reference.py',
                         'connected_depth_weighted_scalar_gradient.py')})
    with args.report.open('x') as stream:json.dump(report,stream,indent=2,allow_nan=False)


if __name__=='__main__':main()
