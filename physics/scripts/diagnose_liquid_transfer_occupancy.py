"""Measure native P2G interpolation support, not an inferred liquid surface.

All quantities use the same captured transfer step. The final boundary readback
can be from a later step and is deliberately excluded. Nonzero interpolation
support is not a liquid-volume fraction or a pressure-surface measurement.
"""
import argparse
import json
from pathlib import Path
import numpy as np


def measure(total, cell_volume_m3, halo=2):
    total = np.asarray(total)
    if (total.ndim != 4 or total.shape[-1] != 4 or
            not np.isfinite(total).all() or np.any(total[..., 3] < 0) or
            not np.isfinite(cell_volume_m3) or cell_volume_m3 <= 0 or
            halo < 0 or min(total.shape[1:3]) <= 2*halo):
        raise ValueError('Finite nonnegative transfer mass and valid cell metric required')
    mass = total[:, halo:-halo, halo:-halo, 3] if halo else total[..., 3]
    rho = mass.astype(float)/cell_volume_m3
    # These fixed bins describe the field; none is used to classify fluid.
    edges = [0., .01, .1, .5, 1., 2., float('inf')]
    supported = rho > 0
    bins = []
    for low, high in zip(edges[:-1], edges[1:]):
        selected = (rho > low) & (rho <= high)
        bins.append(dict(lower_exclusive=low, upper_inclusive=high if np.isfinite(high) else None,
                         cells=int(selected.sum()),
                         deposited_volume_m3=float(mass[selected].sum(dtype=float))))
    return dict(physical_cells=int(mass.size), supported_cells=int(supported.sum()),
                nonzero_support_cell_volume_m3=float(supported.sum()*cell_volume_m3),
                deposited_volume_m3=float(mass.sum(dtype=float)), density_bins=bins,
                maximum_deposited_volume_over_cell_volume=float(rho.max()))


def diagnose(directory):
    directory = Path(directory).resolve()
    report = json.loads((directory/'stages.json').read_text())
    capture = json.loads((directory/'capture.json').read_text())
    if (not capture['complete'] or report['exchange_error'] or report['zero_water'] or
            not report['native_transfer_packet_saved'] or not report['scheduler_alignment_observed']):
        raise ValueError('Complete aligned native transfer capture required')
    records = report['native_transfer_packet']
    if sorted(r['region_id'] for r in records) != list(range(12)):
        raise ValueError('All twelve physical owners required')
    results = []
    for record in records:
        path = (directory/record['total']).resolve()
        if path.parent != directory:
            raise ValueError('Transfer file leaves capture directory')
        cells = np.asarray(record['cells'], dtype=int)
        spacing = np.asarray(record['extent_cm'], dtype=float)/cells
        values = np.fromfile(path, dtype='<f4')
        if values.size != int(np.prod(cells))*4:
            raise ValueError('Incomplete transfer file')
        result = measure(values.reshape((*cells[::-1], 4)), float(np.prod(spacing/100)))
        result.update(region_id=record['region_id'], source_file=record['total'],
                      particle_count=record['particle_count'],
                      nominal_particle_volume_m3=record['particle_count']*float(np.float32(record['particle_volume_m3'])))
        results.append(result)
    deposited = sum(r['deposited_volume_m3'] for r in results)
    support = sum(r['nonzero_support_cell_volume_m3'] for r in results)
    bins = [{**results[0]['density_bins'][i],
             'cells':sum(r['density_bins'][i]['cells'] for r in results),
             'deposited_volume_m3':sum(r['density_bins'][i]['deposited_volume_m3'] for r in results)}
            for i in range(len(results[0]['density_bins']))]
    return dict(source_directory=str(directory), native_p2g_step=report['native_transfer_packet_step'],
                native_dataset=report['native_dataset'], regions=results, density_bins=bins,
                particle_count=sum(r['particle_count'] for r in results),
                deposited_volume_m3=deposited, nonzero_support_cell_volume_m3=support,
                support_cell_volume_over_deposited_volume=support/deposited if deposited else None,
                excludes_xy_halo_duplicates=True, final_boundary_readback_used=False,
                support_is_not_measured_fluid_volume=True, signed_interface_reconstructed=False,
                physical_visual_or_performance_acceptance=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = diagnose(args.directory)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('regions','native_dataset')}, indent=2))
