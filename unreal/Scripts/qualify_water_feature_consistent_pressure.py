"""Independent readback verification of certificates and pressure corrections.

Does not import the pressure solver, box certificate or their construction
functions. Preserves the first flux-passing but high-velocity counterexample.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def weighted_divergence(v, f):
    q = v.astype(float)*f.astype(float)
    return (q[2:, 1:-1, 1:-1, 0]-q[1:-1, 1:-1, 1:-1, 0]
        +q[1:-1, 2:, 1:-1, 1]-q[1:-1, 1:-1, 1:-1, 1]
        +q[1:-1, 1:-1, 2:, 2]-q[1:-1, 1:-1, 1:-1, 2])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--original-apertures', type=Path, required=True)
    parser.add_argument('--certified-apertures', type=Path, required=True)
    parser.add_argument('--response', type=Path, required=True)
    parser.add_argument('--certified-pressure', type=Path, required=True)
    parser.add_argument('--original-pressure', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    reports = [json.loads(p.read_text()) for p in
        (args.inputs, args.original_apertures, args.certified_apertures, args.response, args.certified_pressure, args.original_pressure)]
    inputs, original, certified, response, pressure, old_pressure = reports; hashes = {}
    for receipt, path in zip(reports, (args.inputs, args.original_apertures, args.certified_apertures,
                                     args.response, args.certified_pressure, args.original_pressure)):
        for p, sha in {**receipt['dependency_sha256'], **receipt['outputs_sha256']}.items():
            if p in hashes and sha != hashes[p]:
                raise ValueError('Conflicting evidence version')
            hashes[p] = sha
        hashes[str(path.resolve())] = digest(path)
    hashes[str(Path(__file__).resolve())] = digest(__file__)
    if any(digest(p) != sha for p, sha in hashes.items()):
        raise ValueError('Pinned evidence changed')
    shape = tuple(inputs['shape']); origin = np.array(inputs['origin_m']); h = inputs['cell_m']
    certificate_rows = []; fractions = np.empty((*shape, 3), np.float32)
    boxes = [m for m in inputs['meshes'] if m['name'] != 'Obstacle approach bed']
    if len(boxes) != 7:
        raise ValueError('Seven original actual boxes required')
    for axis, (a, b) in enumerate(zip(original['arrays'], certified['arrays'])):
        old, new = np.load(a, allow_pickle=False), np.load(b, allow_pickle=False)
        independently_covered = np.zeros(new.shape, bool)
        # Independent source-bounds proof, no intersection/union summation.
        for mesh in boxes:
            v = np.load(mesh['vertices'], allow_pickle=False); t = np.load(mesh['triangles'], allow_pickle=False)
            if hashlib.sha256(v.tobytes()+t.tobytes()).hexdigest() != mesh['geometry_sha256']:
                raise ValueError('Actual mesh hash mismatch')
            lower, upper = v.min(0), v.max(0); cover = np.ones(new.shape, bool)
            for a in range(3):
                points = origin[a]+np.arange(new.shape[a])*h
                end = points if a == axis else points+h
                valid = (points >= lower[a]) & (end <= upper[a])
                dims = [1, 1, 1]; dims[a] = len(points); cover &= valid.reshape(dims)
            independently_covered |= cover
        changes = old != new
        if np.any(changes & ~independently_covered) or np.any(new[independently_covered] != 0):
            raise ValueError('Certificate changed an unproved face or left a proved face open')
        np.testing.assert_array_equal(new[~independently_covered], old[~independently_covered])
        if np.count_nonzero(changes) != certified['changes'][axis]['changed_faces']:
            raise ValueError('Changed-face count mismatch')
        certificate_rows.append(dict(axis=axis, faces=new.size, changed_faces=int(np.count_nonzero(changes)),
            maximum_removed_area_m2=float(old[changes].max()), uncertified_bitexact=True))
        sl = [slice(None)]*3; sl[axis] = slice(0, shape[axis]); fractions[..., axis] = new[tuple(sl)]/(h*h)
    flags = np.load(pressure['native']['arrays']['flags'], allow_pickle=False)
    before = np.load(pressure['native']['arrays']['velocity-before'], allow_pickle=False)
    after = np.load(pressure['arrays']['velocity-consistent-native'], allow_pickle=False)
    after64 = np.load(pressure['arrays']['velocity-consistent-float64'], allow_pickle=False)
    p = np.load(pressure['arrays']['pressure-consistent'], allow_pickle=False)
    phi = np.load(inputs['fields']['phi'], allow_pickle=False).astype(float)
    # Actual constants come from previous native response setup for this build.
    fluid = (flags & 1) != 0; air = (flags & 4) != 0; outflow = (flags & 16) != 0
    predicted = before.astype(float).copy(); frozen_faces = 0; active_faces = 0
    for axis in range(3):
        lo = [slice(None)]*3; hi = list(lo); lo[axis] = slice(None, -1); hi[axis] = slice(1, None)
        lo, hi = tuple(lo), tuple(hi)
        frozen = (fluid[lo] & outflow[hi]) | (fluid[hi] & outflow[lo])
        free = ((fluid[lo] & air[hi]) | (fluid[hi] & air[lo])) & ~frozen
        active = ((fluid[lo] & fluid[hi]) | free) & (fractions[hi+(axis,)] > 0)
        distance = np.ones(active.shape)
        source_phi = np.where(fluid[lo], phi[lo], phi[hi]); target_phi = np.where(fluid[lo], phi[hi], phi[lo])
        if np.any(free & active & ((source_phi >= 0) | (target_phi < 0))):
            raise ValueError('Actual interface signs do not support reference distance')
        distance[free & active] = np.abs(source_phi[free & active])/(np.abs(source_phi[free & active])+np.abs(target_phi[free & active]))
        factor = np.where(active, 1./np.maximum(distance, 1e-4), 0.)
        predicted[hi+(axis,)] -= factor*(p[hi]-p[lo])
        np.testing.assert_array_equal(after[hi+(axis,)][frozen], before[hi+(axis,)][frozen])
        frozen_faces += int(np.count_nonzero(frozen & (fractions[hi+(axis,)] > 0)))
        active_faces += int(np.count_nonzero(active))
    np.testing.assert_allclose(after64, predicted, atol=1e-12, rtol=1e-12)
    np.testing.assert_array_equal(after, predicted.astype(np.float32))
    mask = fluid[1:-1, 1:-1, 1:-1]; residual = weighted_divergence(after, fractions)[mask]
    maximum = float(np.max(np.abs(residual))); rms = float(np.sqrt(np.mean(residual**2)))
    if maximum > 5e-5:
        raise ValueError('Independently recomputed native flux exceeds fixed allowance')
    saved_rhs = np.load(pressure['arrays']['native-consistent-rhs'], allow_pickle=False)[1:-1, 1:-1, 1:-1]
    if np.max(np.abs(residual+saved_rhs[mask])) > 5e-5:
        raise ValueError('Native RHS readback differs from independent weighted face flux')
    rejected = response['rows'][0]
    if rejected['reference_complete'] or '16 cells' not in rejected['reference_rejection']:
        raise ValueError('Unsupported old-input control was not retained')
    retained = response['rows'][1]; bad_velocity = np.load(retained['arrays']['consistent_native_float32'], allow_pickle=False)
    old_fractions = np.load(old_pressure['rows'][2]['arrays']['fractions'], allow_pickle=False)
    peak_index = tuple(np.unravel_index(np.argmax(np.abs(bad_velocity)), bad_velocity.shape))
    # Highest retained velocity is the known buried-floor roundoff-aperture jet.
    peak_area = float(old_fractions[peak_index]); peak_speed = float(bad_velocity[peak_index])*h*2.5
    if peak_area >= 1e-14 or abs(peak_speed) < 300:
        raise ValueError('High-velocity counterexample no longer matches pinned evidence')
    if fractions[peak_index] != 0 or after[peak_index] != before[peak_index]:
        raise ValueError('Certified closed face did not preserve zero pressure response')
    report = dict(complete=True, accepted=False, originals_unchanged=True, certificates=certificate_rows,
        independently_checked_faces=sum(r['faces'] for r in certificate_rows), frozen_outflow_faces=frozen_faces,
        active_response_faces=active_faces, independent_corrected_velocity_float32_bitexact=True,
        maximum_weighted_divergence_per_second=maximum*2.5, rms_weighted_divergence_per_second=rms*2.5,
        retained_high_velocity_counterexample=dict(index=[int(x) for x in peak_index], area_fraction=peak_area, speed_m_per_second=peak_speed),
        remaining_active_peak=pressure['peak_active_face'], dependency_sha256=hashes,
        scope='Every box coverage change, independent pressure gradient, native float32 flux and retained unsupported/high-velocity controls checked. Pressure snapshot only; physical velocities, volume/inertia/contact/surface/refinement and animation are NOT accepted.')
    if any(digest(p) != sha for p, sha in hashes.items()):
        raise ValueError('Qualification changed preserved inputs')
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2); stream.write('\n')
    print('CONSISTENT_PRESSURE_QUALIFIED', maximum*2.5, rms*2.5, frozen_faces, peak_speed, flush=True)


if __name__ == '__main__':
    main()
