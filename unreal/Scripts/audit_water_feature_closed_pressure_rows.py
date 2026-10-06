"""Recount zero-face fluid cells without mistaking ghost-fluid rows for zero rows."""
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
    parser.add_argument('--apertures', type=Path, required=True)
    parser.add_argument('--pressure', type=Path, required=True)
    parser.add_argument('--empty-type', type=int, required=True,
                        help='FlagEmpty from the actual installed host namespace (this build: 4)')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    areas = json.loads(args.apertures.read_text()); pressure = json.loads(args.pressure.read_text())
    shape = tuple(areas['shape']); h = areas['cell_m']; fractions = np.empty((*shape, 3), np.float32)
    native = pressure['rows'][0]; hashes = {str(p.resolve()): digest(p)
        for p in (args.apertures, args.pressure, Path(__file__))}
    for i, path in enumerate(areas['arrays']):
        if digest(path) != areas['outputs_sha256'][path]:
            raise ValueError('Pinned geometric areas changed')
        hashes[path] = digest(path)
        slices = [slice(None)]*3; slices[i] = slice(0, shape[i])
        fractions[..., i] = np.load(path, allow_pickle=False)[tuple(slices)]/(h*h)
    flag_path = native['arrays']['flags']
    if digest(flag_path) != native['outputs_sha256'][flag_path]:
        raise ValueError('Pinned baseline flags changed')
    hashes[flag_path] = digest(flag_path); flags = np.load(flag_path, allow_pickle=False)
    interior = (slice(1, -1),)*3
    fluid = (flags[interior] & pressure['native_settings']['FlagFluid']) != 0
    closed = np.ones_like(fluid); empty_neighbor = np.zeros_like(fluid)
    for axis in range(3):
        for side in (-1, 1):
            cells = list(interior); cells[axis] = slice(0, -2) if side == -1 else slice(2, None)
            empty_neighbor |= (flags[tuple(cells)] & args.empty_type) != 0
            face = list(interior); face[axis] = slice(1, -1) if side == -1 else slice(2, None)
            closed &= fractions[tuple(face)+(axis,)] == 0
    counts = dict(closed_fluid_cells=int(np.count_nonzero(closed & fluid)),
        closed_fluid_with_empty_neighbor=int(np.count_nonzero(closed & fluid & empty_neighbor)),
        closed_fluid_without_empty_neighbor=int(np.count_nonzero(closed & fluid & ~empty_neighbor)))
    if counts['closed_fluid_cells'] != native['before_pressure']['geometric_closed_fluid_cells']:
        raise ValueError('Closed-fluid count differs from native experiment')
    report = dict(complete=True, accepted=False, counts=counts, empty_flag_type=args.empty_type,
        dependency_sha256=hashes, zero_face_no_empty_indices=(np.argwhere(closed & fluid & ~empty_neighbor)+1).tolist(),
        scope='Geometry/flags-only row classification. Fully closed rows with empty neighbors can still receive unweighted native ghost-fluid diagonal terms; do not claim all closed cells have zero operator rows.',
        caveat='No direct native matrix readback or unique CG failure attribution. Zero-face/no-empty cells have neither geometric face weights nor empty-neighbor ghost-fluid diagonal contributions in the matching pressure source.')
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2); stream.write('\n')
    print('CLOSED_PRESSURE_ROWS', counts, flush=True)


if __name__ == '__main__':
    main()
