"""Independent actual moving-mesh pose/velocity/mass/energy readback.

No constructor import or solver execution. Checks all 21 stored poses; does not
claim independent readback of the 4,000 unstored intermediate substeps.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--motion', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    r = json.loads(args.motion.read_text()); pins = {str(args.motion.resolve()): digest(args.motion),
        str(Path(__file__).resolve()): digest(__file__), **r['dependency_sha256'], **r['outputs_sha256']}
    if any(digest(p) != sha for p, sha in pins.items()):
        raise ValueError('Pinned physical motion changed')
    arrays = {k: np.load(p, allow_pickle=False) for k, p in r['arrays'].items()}
    poses, times, cells = arrays['poses'], arrays['times'], arrays['tetrahedra']; g = np.array(r['gravity_m_s2']); u = np.array(r['initial_velocity_m_s'])
    if poses.shape != (21, 8, 3) or len(times) != 21 or not np.allclose(times, np.arange(21)*.02, rtol=0., atol=1e-16):
        raise ValueError('Complete declared discrete physical trajectory required')
    if not all(np.isfinite(x).all() for x in arrays.values()):
        raise ValueError('Nonfinite saved motion')
    expected = poses[0]+times[:, None, None]*u+.5*times[:, None, None]**2*g
    position_error = float(np.max(np.abs(poses-expected))); volume_error = trace_error = energy_error = flux_error = 0.
    energy0 = None; masses = []; actualfaces = arrays['faces']; lookup = {tuple(row): i for i, row in enumerate(actualfaces)}
    for frame, (xyz, time_s) in enumerate(zip(poses, times)):
        totalvolume = totalenergy = 0.; cellfluxes = []; q = arrays['flux'][frame]; exact_u = u+time_s*g
        expected_q = arrays['areas']*(arrays['normals']@exact_u)
        flux_error = max(flux_error, float(np.max(np.abs(q-expected_q))))
        for tet in cells:
            v = xyz[tet]; vol = np.dot(v[1]-v[0], np.cross(v[2]-v[0], v[3]-v[0]))/6
            if vol <= 0:
                raise ValueError('Moving tetrahedron inverted')
            coeff = []
            for opposite in range(4):
                key = tuple(sorted(int(x) for j, x in enumerate(tet) if j != opposite)); fi = lookup[key]
                tri = xyz[list(key)]; normal = np.cross(tri[1]-tri[0], tri[2]-tri[0])/2
                if np.dot(normal, v[opposite]-tri[0]) > 0:
                    normal = -normal
                sign = 1 if np.dot(normal, arrays['normals'][fi]) > 0 else -1
                coeff.append(sign*q[fi])
            centroid = v.mean(axis=0); velocity = sum((centroid-v[j])*coeff[j] for j in range(4))/(3*vol)
            trace_error = max(trace_error, float(np.max(np.abs(velocity-exact_u)))); cellfluxes.append(sum(coeff))
            totalvolume += vol
            totalenergy += 1000*vol*(.5*np.dot(velocity, velocity)-np.dot(g, centroid))
        masses.append(1000*totalvolume); volume_error = max(volume_error, abs(totalvolume-.25*.12*.06))
        if energy0 is None:
            energy0 = totalenergy
        energy_error = max(energy_error, abs(totalenergy-energy0))
        if max(abs(x) for x in cellfluxes) > 1e-11:
            raise ValueError('Moving-cell divergence readback failed')
    maximum_pressure = float(np.max(np.abs(arrays['pressure'])))
    if (position_error > 1e-10 or volume_error > 1e-14 or trace_error > 1e-9
            or energy_error > 1e-8 or flux_error > 1e-10 or maximum_pressure > 1e-7 or np.min(poses[:, :, 2]) <= 0):
        raise ValueError('Free-flight analytic/contact/mass/energy qualification failed')
    if any(digest(p) != sha for p, sha in pins.items()):
        raise ValueError('Qualification modified prior evidence')
    report = dict(complete=True, accepted=False, dependency_sha256=pins, stored_poses_checked=21,
        moving_tetrahedra_checked=126, maximum_position_error_m=position_error, maximum_volume_error_m3=volume_error,
        maximum_velocity_error_m_s=trace_error, maximum_energy_error_j=energy_error, maximum_flux_error_m3_s=flux_error,
        maximum_pressure_pa=maximum_pressure, mass_range_kg=[min(masses), max(masses)],
        minimum_ground_clearance_m=float(np.min(poses[:, :, 2])),
        scope='Independent exact free-flight reference against all stored moving tetrahedral poses, not all intermediate steps. No capillarity, drag, impact or waterfall/visual-feature acceptance.')
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2); stream.write('\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'dependency_sha256'}, indent=2))


if __name__ == '__main__':
    main()
