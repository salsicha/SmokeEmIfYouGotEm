"""New aperture candidate: zero only faces proved wholly inside actual boxes."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from water_feature_box_face_certificate import certified_box_faces


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apertures', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    original = json.loads(args.apertures.read_text())
    if not original['complete']:
        raise ValueError('Completed preserved actual geometry construction required')
    hashes = {**original['dependency_sha256'], **original['outputs_sha256'],
        str(args.apertures.resolve()): digest(args.apertures), str(Path(__file__).resolve()): digest(__file__)}
    helper = Path(__file__).with_name('water_feature_box_face_certificate.py'); hashes[str(helper.resolve())] = digest(helper)
    if any(digest(p) != sha for p, sha in hashes.items()):
        raise ValueError('Pinned original apertures changed')
    arrays = [np.load(p, allow_pickle=False) for p in original['arrays']]
    old = [a.copy() for a in arrays]; covered = [np.zeros(a.shape, bool) for a in arrays]; proofs = []
    for mesh in original['meshes']:
        if mesh['name'] == 'Obstacle approach bed':
            continue  # No bounding-box substitution for the sloped bed.
        v = np.load(mesh['vertices'], allow_pickle=False); t = np.load(mesh['triangles'], allow_pickle=False)
        masks = certified_box_faces(v, t, original['shape'], original['origin_m'], original['cell_m'])
        counts = []
        for axis in range(3):
            counts.append(dict(axis=axis, covered=int(np.count_nonzero(masks[axis])),
                prior_nonzero=int(np.count_nonzero(masks[axis] & (old[axis] != 0)))))
            covered[axis] |= masks[axis]
        proofs.append(dict(name=mesh['name'], geometry_sha256=mesh['geometry_sha256'], counts=counts))
    args.output.mkdir(); paths = []; outputs = {}; rows = []
    for axis in range(3):
        changed = covered[axis] & (arrays[axis] != 0); values = old[axis][changed]
        arrays[axis][covered[axis]] = 0.
        np.testing.assert_array_equal(arrays[axis][~covered[axis]], old[axis][~covered[axis]])
        for label, a in (('open-area', arrays[axis]), ('certified-covered', covered[axis])):
            path = args.output/f'{label}-axis-{axis}.npy'
            with path.open('xb') as stream:
                np.save(stream, a, allow_pickle=False)
            outputs[str(path.resolve())] = digest(path)
            if label == 'open-area':
                paths.append(str(path.resolve()))
        rows.append(dict(axis=axis, changed_faces=len(values), maximum_removed_area_m2=float(values.max()) if len(values) else 0.,
            minimum_removed_area_m2=float(values.min()) if len(values) else 0., uncertified_faces_bitexact=True))
    if any(digest(p) != sha for p, sha in hashes.items()):
        raise ValueError('Read-only original changed')
    report = dict(complete=True, accepted=False, frame=original['frame'], shape=original['shape'],
        origin_m=original['origin_m'], cell_m=original['cell_m'], meshes=original['meshes'], arrays=paths,
        certificates=proofs, changes=rows, dependency_sha256=hashes, outputs_sha256=outputs,
        original_unchanged=True, scope='Exact box containment certificates, no aperture threshold or fitted clearance. Partial/uncertified faces unchanged; general union full-coverage certification and liquid volumes still open.')
    (args.output/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print('CERTIFIED_BLOCKED_FACES', rows, flush=True)


if __name__ == '__main__':
    main()
