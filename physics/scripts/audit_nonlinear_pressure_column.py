"""Inspect actual FV-coupled pressure columns on captured river states.

Read-only state analysis. No repaired depth, velocity limit, pressure clamp or
scene acceptance. The reconstructed quadratic profile is part of the SGN-type
model, not a measurement of real water. A negative gauge pressure alone is not
a cavitation or flow-separation determination.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import total_depth_bank_replay as bank
from audit_detail_wave_regime import read_snapshot
from total_depth_nonlinear_pressure import pressure_column


def inspect(state, bed, dx, rational=True, breaking_model='none'):
    original = bank.nonlinear_pressure_force
    poles = []
    fractions = []
    def capture(*args, **kwargs):
        value = kwargs.get('dispersion_fraction')
        if value is not None: fractions.append(value.copy())
        return original(*args, **kwargs, on_pressure=lambda values: poles.extend(values))
    diagnostics = {}
    try:
        bank.nonlinear_pressure_force = capture
        total, bound = bank.rate(state, bed, dx, second_order=True, dispersive=True,
            pressure_model='rational_sgn' if rational else 'sgn',
            pressure_interpolation='depth_weighted', pressure_formulation='kinematic',
            pressure_bed_slope='geometry',breaking_model=breaking_model,pressure_diagnostics=diagnostics)
    finally:
        bank.nonlinear_pressure_force = original
    hydro, _ = bank.rate(state, bed, dx, second_order=True)
    h = state[..., 0]
    velocity = np.divide(state[..., 1:], h[..., None], out=np.zeros_like(state[..., 1:]), where=h[..., None] > 0)
    pressure = sum(p['weight']*p['pressure'] for p in poles)
    bottom = sum(p['weight']*p['bottom_pressure'] for p in poles)
    column = pressure_column(h, pressure, bottom)
    fastest = np.unravel_index(np.linalg.norm(velocity, axis=-1).argmax(), h.shape)
    lowest = np.unravel_index(column['minimum'].argmin(), h.shape)
    def cell(yx):
        value = dict(yx=list(map(int, yx)), depth_m=float(h[yx]), bed_m=float(bed[yx]),
            nonbreaking_fraction=float(fractions[0][yx]) if fractions else 1.,
            velocity_mps=velocity[yx].tolist(), total_rate=total[yx].tolist(),
            hydrostatic_rate=hydro[yx].tolist(), pressure_rate=(total-hydro)[yx].tolist(),
            column={name:float(value[yx]) for name,value in column.items()},
            poles=[dict(length=p['length'], weight=p['weight'],
                integrated_nonhydrostatic=float(p['pressure'][yx]), bottom_nonhydrostatic=float(p['bottom_pressure'][yx]),
                quadratic=float(p['quadratic'][yx]), curvature=float(p['curvature'][yx])) for p in poles])
        return value
    return dict(model='rational_sgn' if rational else 'sgn',breaking_model=breaking_model,diagnostics=diagnostics,
        speed_bound_s=float(bound), fastest_cell=cell(fastest), minimum_pressure_cell=cell(lowest),
        negative_bottom_cells=int(np.count_nonzero(column['bottom'] < 0)),
        negative_column_cells=int(np.count_nonzero(column['minimum'] < 0)),
        minimum_gauge_pressure_per_density=float(column['minimum'].min()),
        minimum_gauge_pressure_head_m=float(column['minimum'].min()/9.81),
        integrated_pressure_force=(np.sum(total[...,1:]-hydro[...,1:],axis=(0,1))*dx*dx).tolist())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('snapshot', type=Path)
    parser.add_argument('state', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--breaking-model', choices=('none','hybrid_front'), default='none')
    args = parser.parse_args()
    if args.report.exists(): raise FileExistsError(args.report)
    meta, arrays, hashes = read_snapshot(args.snapshot)
    state = np.load(args.state, allow_pickle=False)
    hashes[str(args.state)] = hashlib.sha256(args.state.read_bytes()).hexdigest()
    bed = arrays['mean_geometry'][..., 0].astype(float)
    report = dict(schema='raftsim.pressure_column_audit.v1', scope=__doc__, scene_accepted=False,
        source_hashes=hashes, implementation_hashes={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in ('audit_nonlinear_pressure_column.py','total_depth_nonlinear_pressure.py','total_depth_bank_replay.py','breaking_front_reference.py')},
        models=[inspect(state, bed, meta['cell_m'], rational,args.breaking_model) for rational in (True, False)])
    with args.report.open('x') as output: json.dump(report, output, indent=2, allow_nan=False)
    print(json.dumps(report, indent=2))


if __name__ == '__main__': main()
