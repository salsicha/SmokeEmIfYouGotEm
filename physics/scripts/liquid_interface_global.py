"""Assemble an independently checked rectangular owner layout for whole-grid reference.

No averaging at cuts: overlapping samples must agree exactly, including physical
exterior data. Missing/inconsistent grids are errors, not implicit boundary values.
"""
import numpy as np


def layout(sizes, columns):
    sizes = np.asarray(sizes)
    if sizes.ndim != 2 or sizes.shape[1] != 3 or not 2 <= len(sizes) <= 16 or not np.issubdtype(sizes.dtype, np.integer):
        raise ValueError('Bounded integer multi-owner dimensions required')
    if (sizes <= 4).any() or (sizes > 4096).any() or not np.all(sizes[:, 2] == sizes[0, 2]):
        raise ValueError('Compatible two-halo owner dimensions required')
    edges = []; written = set()
    for row in columns:
        if len(row) != 6 or any(not isinstance(x, (int, np.integer)) for x in row):
            raise ValueError('Integer owner-copy column required')
        source, dest, sx, sy, dx, dy = row
        if not 0 <= source < len(sizes) or not 0 <= dest < len(sizes) or source == dest:
            raise ValueError('Distinct valid owners required')
        if (not (2 <= sx < sizes[source, 0]-2 and 2 <= sy < sizes[source, 1]-2) or
                not (0 <= dx < sizes[dest, 0] and 0 <= dy < sizes[dest, 1]) or
                (2 <= dx < sizes[dest, 0]-2 and 2 <= dy < sizes[dest, 1]-2) or (dest, dx, dy) in written):
            raise ValueError('Unique physical-owner to halo copy required')
        written.add((dest, dx, dy)); edges.append((source, dest, np.array([sx-dx, sy-dy])))
    offsets = {0: np.zeros(2, dtype=int)}
    for _ in range(len(sizes)):
        for source, dest, delta in edges:
            if source in offsets and dest not in offsets:
                offsets[dest] = offsets[source]+delta
            if dest in offsets and source not in offsets:
                offsets[source] = offsets[dest]-delta
            if source in offsets and dest in offsets and not np.array_equal(offsets[dest], offsets[source]+delta):
                raise ValueError('Inconsistent physical owner translations')
    if len(offsets) != len(sizes):
        raise ValueError('Disconnected owner graph')
    offsets = np.array([offsets[i] for i in range(len(sizes))]); offsets -= offsets.min(axis=0)
    xy = (offsets+sizes[:, :2]).max(axis=0)
    if np.prod(xy, dtype=np.int64)*sizes[0, 2] > 4_000_000:
        raise ValueError('Whole interface reference exceeds bounded capacity')
    coverage = np.zeros(xy[::-1], dtype=np.uint8)
    for (x, y), (nx, ny, _) in zip(offsets, sizes):
        coverage[y+2:y+ny-2, x+2:x+nx-2] += 1
    if not np.all(coverage[2:-2, 2:-2] == 1):
        raise ValueError('Physical owners overlap or leave holes')
    return offsets, tuple([int(sizes[0, 2]), int(xy[1]), int(xy[0])])


def assemble(fields, offsets, shape):
    tail = fields[0].shape[3:]
    result = np.zeros((*shape, *tail), dtype=fields[0].dtype)
    covered = np.zeros(shape, dtype=bool)
    for owner, (field, (x, y)) in enumerate(zip(fields, offsets, strict=True)):
        if field.ndim not in (3, 4) or field.shape[3:] != tail or field.shape[0] != shape[0] or not np.isfinite(field).all():
            raise ValueError('Matching finite scalar/vector owner fields required')
        nz, ny, nx = field.shape[:3]; box = (slice(None), slice(y, y+ny), slice(x, x+nx))
        target, previous = result[box], covered[box]
        if not np.array_equal(target[previous], field[previous]):
            error = np.abs(target[previous].astype(float)-field[previous].astype(float))
            raise ValueError(f'Owner {owner} overlapping field disagrees, maximum {error.max()}')
        target[...] = field; covered[box] = True
    if not covered.all():
        raise ValueError('Whole reference contains uncovered exterior samples')
    return result


def extract(field, offsets, sizes):
    return [field[:, y:y+ny, x:x+nx].copy() for (x, y), (nx, ny, _) in zip(offsets, sizes, strict=True)]
