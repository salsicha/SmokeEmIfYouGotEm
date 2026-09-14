"""Validate actual extended source samples, never invent pressure boundary data."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def ring_coordinates(nx, ny, width):
    return [(x, y) for y in range(-width, ny+width) for x in range(-width, nx+width)
            if not (0 <= x < nx and 0 <= y < ny)]


def decode(record):
    nx, ny, width = record['nx'], record['ny'], record.get('pressure_stencil_width')
    if (nx, ny, width) != (128, 128, 3) or record['cell_meters'] != .5:
        raise ValueError('Missing or invalid explicit pressure-stencil registration')
    for key in ('origin_x', 'origin_y', 'native_seconds', 'revision'):
        if not np.isfinite(record[key]):
            raise ValueError('Invalid source registration')
    coordinates = ring_coordinates(nx, ny, width)
    def array(key, shape):
        value = np.asarray(record[key], dtype=float)
        if value.size != int(np.prod(shape)) or not np.isfinite(value).all():
            raise ValueError('Invalid source array '+key)
        return value.reshape(shape)
    state = array('state', (ny, nx, 4)); bed = array('bed', (ny, nx))
    ring = array('pressure_stencil_state', (len(coordinates), 4))
    ring_bed = array('pressure_stencil_bed', (len(coordinates),))
    exterior = array('exterior_state', (2*(nx+ny), 4))
    exterior_bed = array('exterior_bed', (2*(nx+ny),))
    array('face_normal_velocity', (2*(nx+ny),))
    full = np.empty((ny+2*width, nx+2*width, 4)); full_bed = np.empty(full.shape[:2])
    full[width:width+ny, width:width+nx] = state
    full_bed[width:width+ny, width:width+nx] = bed
    for i, (x, y) in enumerate(coordinates):
        full[y+width, x+width] = ring[i]
        full_bed[y+width, x+width] = ring_bed[i]
    if (np.any(full[..., 0] < 0) or np.any(full[..., 3] != 0)
            or np.any(full[..., 1:3][full[..., 0] == 0] != 0)):
        raise ValueError('Invalid conserved source; no masking or repair')
    velocity = np.divide(full[..., 1:3], full[..., 0, None], out=np.zeros_like(full[..., 1:3]),
                         where=full[..., 0, None] > 0)
    if not np.isfinite(velocity).all():
        raise ValueError('Unrepresentable source velocity')
    # Existing independent west/east/south/north records must match exactly.
    old_positions = ([(-1, y) for y in range(ny)]+[(nx, y) for y in range(ny)]
                     +[(x, -1) for x in range(nx)]+[(x, ny) for x in range(nx)])
    for i, (x, y) in enumerate(old_positions):
        if not np.array_equal(full[y+width, x+width], exterior[i]) or full_bed[y+width, x+width] != exterior_bed[i]:
            raise ValueError('Extended stencil differs from original exterior observation')
    return full, full_bed, dict(revision=record['revision'], native_seconds=record['native_seconds'],
        origin=[record['origin_x'], record['origin_y']], halo_width=width, halo_cells=len(coordinates),
        old_exterior_cells_exact=len(old_positions), new_samples_beyond_old_exterior=len(coordinates)-len(old_positions),
        full_shape=list(full.shape), minimum_depth=float(full[..., 0].min()),
        maximum_speed_mps=float(np.linalg.norm(velocity, axis=-1).max()),
        state_sha256=hashlib.sha256(full.tobytes()).hexdigest(), bed_sha256=hashlib.sha256(full_bed.tobytes()).hexdigest())


def audit(record):
    if record.get('schema') != 'raftsim.live_temporal_boundary_inputs.v1':
        raise ValueError('Expected actual temporal source capture')
    a, b = record['first'], record['second']
    first, first_bed, ra = decode(a); second, second_bed, rb = decode(b)
    if (ra['origin'] != rb['origin'] or ra['native_seconds'] >= rb['native_seconds']
            or ra['revision'] >= rb['revision'] or not np.array_equal(first_bed, second_bed)):
        raise ValueError('Unregistered or changed-bed temporal stencil')
    return dict(passed=True, observations=[ra, rb], unchanged_physical_bed=True,
        pressure_boundary_qualified=False, gameplay_or_performance_accepted=False,
        limitations='Actual registered point samples, not surveyed subgrid terrain or a conservative remap. '
        'Additional h/hu/hv/bed samples do not prescribe pressure, scalar derivative traces, or outgoing waves. '
        'No old replay is extended or replaced by this new capture.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    raw = args.input.read_bytes()
    result = audit(json.loads(raw))
    result.update(input=str(args.input.resolve()), input_sha256=hashlib.sha256(raw).hexdigest())
    with args.report.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
