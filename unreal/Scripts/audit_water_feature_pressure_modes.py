"""Read-only pressure readback / kinetic coupling spectrum on actual saved states.

Different quadrature and direct inverse from constructor. No row filtering,
pressure capping, rerun or field mutation. Spectrum is not an inf-sup proof.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from qualify_water_feature_moving_tetra import reference_data, reference_basis, assemble_B


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('audit', 'qualified', 'output'):
        parser.add_argument('--'+key, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    audit, qualified = (json.loads(p.read_text()) for p in (args.audit, args.qualified))
    pins = {str(args.audit.resolve()): digest(args.audit), str(args.qualified.resolve()): digest(args.qualified),
        str(Path(__file__).resolve()): digest(__file__), **qualified['dependency_sha256']}
    helper = Path(__file__).with_name('qualify_water_feature_moving_tetra.py'); pins[str(helper.resolve())] = digest(helper)
    if any(digest(p) != sha for p, sha in pins.items()):
        raise ValueError('Pressure trajectory inputs changed')
    bary, w = reference_data(); N, grad = reference_basis(bary); rows = []
    for run in audit['runs']:
        if run['pressure_mode'] != 'discontinuous_p1':
            continue
        arrays = {k: np.load(p, allow_pickle=False) for k, p in run['arrays'].items()}
        x, p = arrays['positions'], arrays['pressures']; free = ~arrays['fixed'].ravel()
        M = np.kron(arrays['scalar_material_mass'], np.eye(3)); L = np.linalg.cholesky(M[np.ix_(free, free)])
        indices = sorted(set([0, 1, *range(50, len(x), 50), len(x)-1])); spectra = []
        for i in indices:
            B = assemble_B(x[i], arrays['cells'], arrays['pressure_cells'], bary, grad, w, p.shape[1])[:, free]
            A = np.linalg.solve(L, B.T).T; diagonal = np.linalg.norm(A, axis=1)
            if np.any(diagonal <= 0):
                raise ValueError('Pressure row has no coupling')
            scaled = A/diagonal[:, None]; singular = np.linalg.svd(scaled, compute_uv=False)
            cutoff = 128*np.finfo(float).eps*max(scaled.shape)*singular[0]
            rank = int(np.sum(singular > cutoff)); positive = singular[singular > cutoff]
            spectra.append(dict(step=i, physical_time_s=float(arrays['times'][i]), pressure_rows=len(B),
                numerical_rank=rank, relative_svd_roundoff_cutoff=cutoff/singular[0],
                smallest_retained_row_normalized_singular_value=float(positive[-1]),
                largest_row_normalized_singular_value=float(singular[0]),
                retained_kinetic_coupling_condition=float(singular[0]/positive[-1]),
                pressure_coefficient_min_pa=float(p[i].min()), pressure_coefficient_max_pa=float(p[i].max())))
            print('PRESSURE_MODE_READBACK', run['label'], i, spectra[-1], flush=True)
        actual_p = np.einsum('qi,sti->stq', bary, p[:, arrays['pressure_cells']])
        rows.append(dict(label=run['label'], saved_states_pressure_checked=len(x), spectra=spectra,
            quadrature_pressure_min_pa=float(actual_p.min()), quadrature_pressure_max_pa=float(actual_p.max()),
            maximum_absolute_pressure_coefficient_pa=float(np.max(np.abs(p))),
            hydrostatic_half_meter_scale_pa=1000*9.80665*.5,
            accepted=False, scope='All saved pressure coefficients and independently evaluated linear fields; selected complete kinetic coupling spectra. Not unique physical pressure/inf-sup/feature acceptance.'))
    if any(digest(path) != sha for path, sha in pins.items()):
        raise ValueError('Pressure audit changed preserved fields')
    with args.output.open('x') as stream:
        json.dump(dict(complete=True, accepted=False, dependency_sha256=pins, runs=rows,
            interpretation='Near-null kinetic couplings and very large pressure fields require pressure-space/stability repair; conservation alone does not qualify physical pressure. No modes discarded or solver tolerances changed.'), stream, indent=2)
        stream.write('\n')


if __name__ == '__main__':
    main()
