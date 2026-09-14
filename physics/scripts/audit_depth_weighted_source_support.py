"""Inspect proposed scalar support on original captured South Fork samples.

Rank, affine reproduction, and interactions crossing dry cells are reported
independently. This does not manufacture an evolving mass direction from two
source snapshots or claim pressure, energy, history, or playable acceptance.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from audit_pressure_stencil_source import audit, decode
from depth_weighted_scalar_gradient import DepthWeightedScalarGradient


def inspect(full, dx):
    h = full[..., 0]
    core = (slice(3, -3), slice(3, -3))
    wet = h[core] > 0
    g = DepthWeightedScalarGradient(h, dx)
    y, x = np.indices(h.shape, dtype=float) * dx
    affine = g.gradient(2*x-3*y+1)[core]
    constant = g.gradient(np.ones_like(h))[core]
    components = []
    for component, axis in enumerate((1, 0)):
        rank = g.ranks[component][core]
        # The diagonal WLS weights must not be mistaken for connected fluid
        # support: inspect intervening cells for each used two-cell link.
        crossing = np.zeros_like(h, dtype=bool)
        examples = []
        link_count = 0
        for i, offset in enumerate(g.offsets):
            if abs(offset) != 2:
                continue
            gap = (g.weights[component][i] > 0) & (np.roll(h, -offset//2, axis) == 0)
            crossing |= gap
            indices = np.argwhere(gap[core] & wet)
            link_count += len(indices)
            for cy, cx in indices[:4]:
                owner = [int(cy)+3, int(cx)+3]
                middle = owner.copy(); middle[axis] += offset//2
                neighbor = owner.copy(); neighbor[axis] += offset
                examples.append(dict(owner_core_yx=[int(cy), int(cx)], offset=offset,
                    owner_depth=float(h[tuple(owner)]), intervening_depth=float(h[tuple(middle)]),
                    neighbor_depth=float(h[tuple(neighbor)])))
        supported = wet & (rank > 0)
        components.append(dict(axis='x' if component == 0 else 'y',
            wet_rank_counts={str(r): int(np.sum(wet & (rank == r))) for r in (0, 1, 2)},
            affine_supported_max_error=float(abs(affine[..., component][supported]-(2., -3.)[component]).max())
                if np.any(supported) else None,
            wet_links_crossing_exactly_dry_cells=link_count,
            wet_owners_crossing_exactly_dry_cells=int(np.sum(crossing[core] & wet)),
            crossing_examples=examples))
    return dict(full_shape=list(h.shape), core_wet_cells=int(np.sum(wet)),
        constant_gradient_exact_zero=bool(np.all(constant == 0)), components=components,
        stationary_source_only=True, native_or_gameplay_accepted=False)


def main():
    global DepthWeightedScalarGradient
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--connected', action='store_true')
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError(args.report)
    if args.connected:
        from connected_depth_weighted_scalar_gradient import ConnectedDepthWeightedScalarGradient
        DepthWeightedScalarGradient = ConnectedDepthWeightedScalarGradient
    raw = args.input.read_bytes(); record = json.loads(raw)
    source = audit(record)
    endpoints = []
    for name in ('first', 'second'):
        full, _, metadata = decode(record[name])
        before = full.copy()
        result = inspect(full, record[name]['cell_meters'])
        if not np.array_equal(full, before):
            raise AssertionError('Original source was modified')
        endpoints.append(dict(endpoint=name, source=metadata, **result))
    result = dict(scope=__doc__, input_sha256=hashlib.sha256(raw).hexdigest(),
        source_audit_passed=source['passed'], endpoints=endpoints, connected=args.connected,
        implementation_hashes={name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in ('depth_weighted_scalar_gradient.py', 'audit_pressure_stencil_source.py',
                         'audit_depth_weighted_source_support.py', 'connected_depth_weighted_scalar_gradient.py')},
        full_history_energy_or_playable_accepted=False)
    with args.report.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
