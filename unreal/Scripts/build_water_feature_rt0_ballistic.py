"""Coupled free-flight liquid parcel transport benchmark, without impact.

Uniform translation is the exact inviscid zero-surface-tension / no-air-drag
solution. It does NOT establish waterfall thinning, breakup, splash or visual
acceptance. Retains solver pressure and velocities; checks all one-sided traces
before any shared vertex is transported. Never averages inconsistent traces.
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
    parser.add_argument('--pressure-audit', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    prior = json.loads(args.pressure_audit.read_text()); hashes = {str(args.pressure_audit.resolve()): digest(args.pressure_audit),
        **prior['dependency_sha256'], **prior['outputs_sha256']}
    for name in (Path(__file__).name, 'water_feature_rt0_step.py'):
        p = Path(__file__).with_name(name); hashes[str(p.resolve())] = digest(p)
    if any(digest(p) != sha for p, sha in hashes.items()):
        raise ValueError('Pinned pressure controls changed')
    v, t = tank_mesh(1, length=(.25, .12, .06)); v += [-.125, -.06, 1.1]
    model = LiquidTetrahedra(v, t); initial = v.copy(); g = np.array([0., 0., -9.80665]); u0 = np.array([.1, 0., -.2])
    q = model.uniform_flux(u0); dt = .0001; poses = [v.copy()]; times = [0.]; qs = [q.copy()]; pressures = [np.zeros(len(t))]
    max_div = max_cfl = max_energy_error = max_trace_error = max_pressure = 0.; started = time.perf_counter()
    energy_initial = float(q@model.M@q/2)-float(1000*np.sum(model.volumes*(model.centroids@g)))
    for step in range(1, 4001):
        old_u = model.velocity_at_vertices(q)
        new_q, pressure, proof = model.step(q, dt, g, {})
        new_u = model.velocity_at_vertices(new_q)
        # Translation-only scope. General RT0 tangential jumps need an actual
        # transport scheme; reject them here instead of hiding them by averaging.
        error = max(float(np.max(np.abs(old_u-old_u[0, 0]))), float(np.max(np.abs(new_u-new_u[0, 0]))))
        if error > 1e-10 or proof['maximum_inradius_courant'] > .1:
            raise ValueError('Uniform free-flight trace/Courant condition failed')
        displacement = dt*(old_u[0, 0]+new_u[0, 0])/2
        model.vertices += displacement; model.centroids += displacement; model.face_centroids += displacement
        # Exact translation preserves areas/normals/volumes and kinetic matrix;
        # independent qualification recomputes actual geometry at every pose.
        q = new_q; time_s = step*dt
        energy = float(q@model.M@q/2)-float(1000*np.sum(model.volumes*(model.centroids@g)))
        max_energy_error = max(max_energy_error, abs(energy-energy_initial)); max_trace_error = max(max_trace_error, error)
        max_div = max(max_div, proof['maximum_divergence_per_second']); max_cfl = max(max_cfl, proof['maximum_inradius_courant'])
        max_pressure = max(max_pressure, float(np.max(np.abs(pressure))))
        if step % 200 == 0:
            poses.append(model.vertices.copy()); times.append(time_s); qs.append(q.copy()); pressures.append(pressure.copy())
            print('RT0_TRANSLATION', time_s, max_cfl, max_energy_error, flush=True)
    poses = np.array(poses); times = np.array(times); qs = np.array(qs); pressures = np.array(pressures)
    expected = initial[None, :, :]+times[:, None, None]*u0+.5*times[:, None, None]**2*g
    error = float(np.max(np.abs(poses-expected)))
    if error > 1e-10 or max_energy_error > 1e-8 or max_pressure > 1e-7 or np.min(poses[:, :, 2]) <= 0:
        raise ValueError('Free-flight metric/energy/no-impact reference failed')
    args.output.mkdir(); outputs = {}; arrays = {}
    for name, array in dict(poses=poses, times=times, tetrahedra=model.tetrahedra, boundary_faces=model.faces[model.boundary],
                            faces=model.faces, normals=model.normals, areas=model.areas, flux=qs, pressure=pressures).items():
        p = args.output/(name+'.npy')
        with p.open('xb') as stream:
            np.save(stream, array, allow_pickle=False)
        arrays[name] = str(p.resolve()); outputs[str(p.resolve())] = digest(p)
    if any(digest(p) != sha for p, sha in hashes.items()):
        raise ValueError('Free-flight benchmark changed previous work')
    report = dict(complete=True, accepted=False, dependency_sha256=hashes, outputs_sha256=outputs, arrays=arrays,
        density_kg_m3=1000., gravity_m_s2=g.tolist(), initial_velocity_m_s=u0.tolist(), step_seconds=dt,
        steps=4000, physical_duration_seconds=.4, poses=21, mass_kg=float(model.volumes.sum()*1000),
        maximum_analytic_position_error_m=error, maximum_energy_drift_j=max_energy_error,
        maximum_uniform_trace_error_m_s=max_trace_error, maximum_divergence_s_inverse=max_div,
        maximum_pressure_pa=max_pressure, maximum_inradius_courant=max_cfl,
        total_seconds=time.perf_counter()-started,
        scope='Actual gravity/pressure impulses and uniform moving tetrahedral parcel, no contact/impact. Inviscid, zero surface tension, no air drag/emission. Translation-only transport consistency benchmark, NOT an accepted waterfall, splash or feature animation.')
    with (args.output/'report.json').open('x') as stream:
        json.dump(report, stream, indent=2); stream.write('\n')


if __name__ == '__main__':
    main()
