"""Independent metric/quadrature and coupled readback of every RT0 control.

Does not import the pressure/geometry constructor or execute its solver.
Four-point degree-two tetrahedral cubature constructs kinetic mass independently.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def check(actual, expected, tolerance, name):
    error = float(np.max(np.abs(np.asarray(actual)-np.asarray(expected))))
    if not np.isfinite(error) or error > tolerance:
        raise ValueError(f'{name} independent readback failed: {error}')
    return error


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    audit = json.loads(args.audit.read_text()); hashes = {str(args.audit.resolve()): digest(args.audit),
        str(Path(__file__).resolve()): digest(__file__), **audit['dependency_sha256'], **audit['outputs_sha256']}
    if any(digest(p) != sha for p, sha in hashes.items()):
        raise ValueError('Constructor or pinned readback changed')
    started = time.perf_counter(); rows = []
    a = (5+3*np.sqrt(5))/20; b = (5-np.sqrt(5))/20
    bary = np.full((4, 4), b); np.fill_diagonal(bary, a)
    for row in audit['runs']:
        data = {k: np.load(p, allow_pickle=False) for k, p in row['arrays'].items()}
        v, t, faces = data['vertices'], data['tetrahedra'], data['faces']
        q, old, pressure = data['new_flux'], data['old_flux'], data['pressure']; dt = row['proof']['dt_seconds']
        nf = len(faces); B = np.zeros((len(t), nf)); M = np.zeros((nf, nf)); force = np.zeros(nf)
        vols = []; centers = []; all_speeds = []; all_ids = []; all_signs = []
        face_map = {tuple(f): i for i, f in enumerate(faces)}
        incidences = np.zeros(nf, int); area = np.zeros(nf); normal = np.zeros((nf, 3))
        for ci, tet in enumerate(t):
            xyz = v[tet]; vol = np.dot(xyz[1]-xyz[0], np.cross(xyz[2]-xyz[0], xyz[3]-xyz[0]))/6
            if vol <= 0:
                raise ValueError('Nonpositive actual tetra volume')
            center = xyz.sum(axis=0)/4; samples = bary@xyz; vols.append(vol); centers.append(center)
            indices = []; signs = []
            for opposite in range(4):
                key = tuple(sorted(int(x) for j, x in enumerate(tet) if j != opposite)); fi = face_map[key]
                tri = v[list(key)]; av = np.cross(tri[1]-tri[0], tri[2]-tri[0])/2
                if np.dot(av, xyz[opposite]-tri[0]) > 0:
                    av = -av
                magnitude = np.linalg.norm(av)
                if incidences[fi] == 0:
                    normal[fi] = av/magnitude; area[fi] = magnitude; sign = 1
                else:
                    if incidences[fi] != 1 or np.dot(av/magnitude, normal[fi]) > -1+1e-12:
                        raise ValueError('Readback is nonconforming/overlapping')
                    sign = -1
                incidences[fi] += 1; B[ci, fi] = sign; indices.append(fi); signs.append(sign)
                force[fi] += sign*1000*np.dot(center-xyz[opposite], row['gravity_m_s2'])/3
            basis = (samples[:, None, :]-xyz[None, :, :])/(3*vol)
            local = 1000*vol/4*np.einsum('kic,kjc->ij', basis, basis)
            s = np.array(signs); M[np.ix_(indices, indices)] += local*s[:, None]*s[None, :]
            coeff = q[indices]*s
            all_ids.append(indices); all_signs.append(signs)
            # RT0 normal trace is constant on each triangle, unlike its
            # tangential trace. Verify every local flux and wall contact.
            for opposite, fi in enumerate(indices):
                pos = v[faces[fi]].mean(axis=0)
                trace = sum((pos-xyz[j])*coeff[j] for j in range(4))/(3*vol)
                check(np.dot(trace, normal[fi])*area[fi], q[fi], 1e-12, 'normal trace')
            velocities = np.array([sum((pos-xyz[j])*coeff[j] for j in range(4))/(3*vol) for pos in xyz])
            all_speeds.append(np.linalg.norm(velocities, axis=1))
        vols = np.array(vols); centers = np.array(centers); boundary = incidences == 1
        if np.any(incidences < 1) or np.any(incidences > 2):
            raise ValueError('Incomplete boundary topology')
        errors = dict(volume_m3=check(data['volumes'], vols, 2e-16, 'volume'),
            cell_faces=check(data['cell_faces'], all_ids, 0., 'cell faces'),
            signs=check(data['signs'], all_signs, 0., 'local orientations'),
            incidence=check(data['incidence'], B, 0., 'incidence'),
            boundary=check(data['boundary'].astype(int), boundary.astype(int), 0., 'boundary'),
            face_area_m2=check(data['areas'], area, 2e-16, 'area'),
            normal=check(data['normals'], normal, 1e-13, 'normal'),
            mass_relative=check(data['mass_matrix']/M.diagonal().max(), M/M.diagonal().max(), 1e-13, 'quadrature mass'))
        fixed = np.zeros(nf, bool); fixed_values = np.zeros(nf)
        for fi, value in row['prescribed_flux']:
            fixed[fi] = True; fixed_values[fi] = value
        free = ~fixed; residual = M@(q-old)-dt*force-dt*B.T@pressure
        errors['fresh_flux_m3_s'] = check(B@q, np.zeros(len(t)), 1e-11, 'constraint')
        errors['fresh_momentum'] = check(residual[free], np.zeros(free.sum()), 1e-9, 'gravity-pressure impulse')
        errors['prescribed_flux_m3_s'] = check(q[fixed], fixed_values[fixed], 0., 'wall/inflow flux') if fixed.any() else 0.
        energy = float(q@M@q/2); errors['energy_j'] = check(energy, row['proof']['kinetic_after_j'], 1e-10, 'energy')
        # Independent predictor and projection metric/boundary-work ledger;
        # momentum is also checked above, without running the constructor.
        pred = np.linalg.solve(M, M@old+dt*force)
        loss = float((q-pred)@M@(q-pred)/2)
        work = float(q[fixed]@residual[fixed])
        closure = energy-float(pred@M@pred/2)+loss-work-float(dt*pressure@(B@q))
        errors['projection_energy_identity_j'] = check(closure, 0., 1e-9, 'projection energy closure')
        check(loss, row['proof']['projection_metric_loss_j'], 1e-9, 'metric loss')
        check(work, row['proof']['prescribed_boundary_work_j'], 1e-9, 'boundary work')
        speeds = np.array(all_speeds); errors['speed_m_s'] = check(speeds.max(), row['proof']['maximum_cell_vertex_speed_m_s'], 1e-12, 'speed')
        radii = 3*vols/area[np.asarray(all_ids)].sum(axis=1)
        check(np.max(dt*speeds.max(axis=1)/radii), row['proof']['maximum_inradius_courant'], 1e-12, 'step Courant')
        check(vols.sum(), .24, 1e-14, 'authored physical liquid volume')
        free_boundary = boundary & free
        check(q[boundary].sum(), 0., 1e-11, 'whole boundary flux')
        check(q[free_boundary].sum(), -q[fixed].sum(), 1e-11, 'internal free interface/source ledger')
        if row['case'] == 'inclined_hydrostatic':
            errors['analytic_pressure_pa'] = check(pressure, 1000*9.80665*(.5-centers[:, 2]), 1e-8, 'hydrostatic pressure')
            check(speeds, np.zeros_like(speeds), 1e-10, 'still water')
        elif row['case'] == 'ballistic':
            expected_u = np.array(row['initial_uniform_velocity_m_s'])+dt*np.array(row['gravity_m_s2'])
            check(q, area*(normal@expected_u), 1e-11, 'ballistic flux')
            check(pressure, 0., 1e-8, 'ambient pressure')
        elif row['case'] == 'tilted_surface':
            if not np.any(q[free_boundary] < -1e-12) or not np.any(q[free_boundary] > 1e-12):
                raise ValueError('Tilted free-interface motion missing one direction')
        else:
            check(q[fixed].sum(), -.006, 1e-12, 'authored inlet')
        rows.append(dict(label=row['label'], tetrahedra=len(t), faces=nf, errors=errors)); print('INDEPENDENT_RT0', row['label'], errors, flush=True)
    if any(digest(p) != sha for p, sha in hashes.items()):
        raise ValueError('Qualification modified evidence')
    result = dict(complete=True, accepted=False, dependency_sha256=hashes, runs=rows,
        total_seconds=time.perf_counter()-started, construction_helpers_imported=False,
        scope='Independent entire tetrahedral stencil geometry, cubature kinetic matrix, coupled gravity/pressure and physical boundary flux readbacks. Fixed-geometry impulse only, not full transport/feature/animation acceptance.')
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2); stream.write('\n')


if __name__ == '__main__':
    main()
