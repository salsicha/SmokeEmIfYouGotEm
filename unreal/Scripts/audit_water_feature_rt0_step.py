"""Save small shared tetrahedral gravity/pressure controls, never source bakes.

Three mesh refinements, exact hydrostatic/ballistic references, and a genuinely
nonhydrostatic tilted free-surface impulse. Fixed geometry only; no animation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from water_feature_rt0_step import LiquidTetrahedra, tank_mesh


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--phase', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    phase = json.loads(args.phase.read_text()); hashes = {str(args.phase.resolve()): digest(args.phase)}
    # Explicit previous work pinning, NOT reuse of its cached phi as this mesh.
    hashes.update(phase['dependency_sha256']); hashes.update(phase['outputs_sha256'])
    for name in (Path(__file__).name, 'water_feature_rt0_step.py'):
        path = Path(__file__).with_name(name); hashes[str(path.resolve())] = digest(path)
    if any(digest(p) != sha for p, sha in hashes.items()):
        raise ValueError('Preserved shared-phase evidence changed')
    args.output.mkdir(); outputs = {}; rows = []; started = time.perf_counter()

    def save(label, name, value):
        path = args.output/(label+'-'+name+'.npy')
        with path.open('xb') as stream:
            np.save(stream, value, allow_pickle=False)
        outputs[str(path.resolve())] = digest(path)
        return str(path.resolve())

    for n in (1, 2, 3):
        for case in ('inclined_hydrostatic', 'ballistic', 'tilted_surface', 'prescribed_inflow'):
            begin = time.perf_counter(); v, t = tank_mesh(n, bed_rise=.2)
            top = v[:, 2] == .5
            if case == 'tilted_surface':
                depth_fraction = (v[:, 2]-.2*v[:, 0])/(.5-.2*v[:, 0])
                v[:, 2] += depth_fraction*.06*(v[:, 0]-.5)
            m = LiquidTetrahedra(v, t); assembled = time.perf_counter()-begin
            surface = m.boundary & np.all(top[m.faces], axis=1)
            fixed = {} if case == 'ballistic' else {int(i): 0. for i in np.flatnonzero(m.boundary & ~surface)}
            u = np.array([.4, -.2, .1]) if case == 'ballistic' else np.zeros(3)
            old = m.uniform_flux(u)
            if case == 'prescribed_inflow':
                for fi in np.flatnonzero(m.boundary & (m.face_centroids[:, 0] == 0)):
                    fixed[int(fi)] = -.02*m.areas[fi]
            # Same smaller PHYSICAL dt on all refinements. The retained v1
            # .01-second run failed its .1 inradius-Courant gate at n=3;
            # no speed clamp or relaxed Courant gate is substituted.
            g = np.array([0., 0., -9.80665]); dt = .004
            before = time.perf_counter(); new, p, proof = m.step(old, dt, g, fixed)
            solve_seconds = time.perf_counter()-before
            label = f'{case}-n{n}'
            arrays = {name: save(label, name, array) for name, array in dict(vertices=m.vertices,
                tetrahedra=m.tetrahedra, faces=m.faces, cell_faces=m.cell_faces, signs=m.signs,
                volumes=m.volumes, mass_matrix=m.M, incidence=m.B, areas=m.areas, normals=m.normals,
                boundary=m.boundary, surface=surface, old_flux=old, new_flux=new, pressure=p).items()}
            prescribed = [[int(i), float(x)] for i, x in fixed.items()]
            row = dict(label=label, case=case, refinement=n, arrays=arrays, prescribed_flux=prescribed,
                gravity_m_s2=g.tolist(), initial_uniform_velocity_m_s=u.tolist(), proof=proof,
                assembly_seconds=assembled, dense_step_seconds=solve_seconds,
                maximum_mass_matrix_bytes=int(m.M.nbytes),
                free_boundary_inward_faces=int(np.count_nonzero(m.boundary & ~np.isin(np.arange(len(new)), list(fixed)) & (new < -1e-12))),
                free_boundary_outward_faces=int(np.count_nonzero(m.boundary & ~np.isin(np.arange(len(new)), list(fixed)) & (new > 1e-12))))
            if case == 'inclined_hydrostatic':
                row['analytic_pressure_error_pa'] = float(np.max(np.abs(p-1000*9.80665*(.5-m.centroids[:, 2]))))
                if row['analytic_pressure_error_pa'] > 1e-8 or proof['maximum_cell_vertex_speed_m_s'] > 1e-10:
                    raise ValueError('Hydrostatic physical reference failed')
            elif case == 'ballistic':
                row['analytic_flux_error_m3_s'] = float(np.max(np.abs(new-m.uniform_flux(u+dt*g))))
                if row['analytic_flux_error_m3_s'] > 1e-11 or np.max(np.abs(p)) > 1e-8:
                    raise ValueError('Free-flight physical reference failed')
            elif case == 'tilted_surface':
                if not row['free_boundary_inward_faces'] or not row['free_boundary_outward_faces']:
                    raise ValueError('Tilted free surface did not exchange local flux in both directions')
            if abs(proof['energy_identity_error_j']) > 1e-9 or proof['maximum_inradius_courant'] > .1:
                raise ValueError('Energy identity or bounded step Courant failed')
            rows.append(row); print('RT0_PHYSICAL_IMPULSE', label, proof, flush=True)
    if any(digest(p) != sha for p, sha in hashes.items()):
        raise ValueError('Control modified preserved evidence')
    result = dict(complete=True, accepted=False, dependency_sha256=hashes, outputs_sha256=outputs,
        runs=rows, total_seconds=time.perf_counter()-started, previous_phase_arrays_reused_as_geometry=False,
        scope='New conforming authored liquid meshes, matched full RT0 kinetic mass / P0 pressure / physical boundary flux / gravity impulse. Fixed geometry, no advection, interface motion, source particle chronology, viscosity, splash, feature animation or river/GameFPS acceptance. Prior native checkpoint preserved.',
        method_reference='https://defelement.org/elements/raviart-thomas.html')
    with (args.output/'report.json').open('x') as stream:
        json.dump(result, stream, indent=2); stream.write('\n')


if __name__ == '__main__':
    main()
