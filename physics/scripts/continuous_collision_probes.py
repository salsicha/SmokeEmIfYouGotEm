"""Lossless, chunk-owned native collision probes without a river-sized JSON list."""
import hashlib
import shutil
from pathlib import Path

import numpy as np

from export_colorado_continuous_runtime import _registered_geometry


def sha(path):
    with Path(path).open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def owners(probes, chunks):
    """Match native FindOwner, including its east/north edge tie-breaking."""
    probes = np.asarray(probes)
    if (probes.ndim != 2 or probes.shape[1] != 3 or not np.isfinite(probes).all()
            or np.any(abs(probes[:, :2]) > 1.e9)):
        raise ValueError('Invalid finite native collision probe')
    cells = np.floor(probes[:, :2] * [1., -1.] / 25200.).astype(np.int64)
    result = np.full(len(probes), -1, dtype=np.int32)
    for dx in (0, -1):
        for dy in (0, -1):
            pending = np.flatnonzero(result < 0)
            candidates = cells[pending] + [dx, dy]
            # Group instead of a Python dictionary lookup for every wet cell.
            unique, inverse = np.unique(candidates, axis=0, return_inverse=True)
            found = np.asarray([chunks.get(tuple(index), -1) for index in unique], dtype=np.int32)[inverse]
            origin = candidates * [25200., -25200.] + [0., -25200.]
            xy = probes[pending, :2]
            inside = (found >= 0) & np.all((xy >= origin) & (xy <= origin + 25200.), axis=1)
            result[pending[inside]] = found[inside]
    if np.any(result < 0):
        raise ValueError('Cooked wet cell has no source terrain chunk')
    return result


def write_chunks(directory, root, mapping, terrain, grid, bed, wet, *, block_cells=262144):
    """Write little-endian float64 xyz triples; retain original per-chunk order.

    All wet cells are kept, not sampled. Partial failed output is deliberately
    preserved and cannot be reused. Only a successful return supplies a contract.
    """
    directory = Path(directory).resolve(); root = Path(root).resolve()
    directory.relative_to(root)
    if type(block_cells) is not int or block_cells < 1:
        raise ValueError('Invalid probe block size')
    if bed.shape != (grid['ny'], grid['nx']) or wet.shape != bed.shape:
        raise ValueError('Collision array shape differs from cooked grid')
    _, selected, lateral, origin = _registered_geometry(mapping, terrain, grid)
    chunks = {}
    for i, chunk in enumerate(terrain['chunks']):
        index = tuple(chunk['chunk'])
        if (len(index) != 2 or any(type(x) is not int for x in index) or index in chunks
                or not np.allclose(chunk['world_northwest_xy_cm'],
                    [index[0]*25200., -(index[1]+1)*25200.], atol=.0001, rtol=0)):
            raise ValueError('Invalid or duplicate shared terrain chunk')
        chunks[index] = i
    if not chunks or len(chunks) > 32768:
        raise ValueError('Invalid terrain chunk count')
    directory.parent.mkdir(parents=True, exist_ok=True)
    # Conservative all-cell output estimate, preserving the project reserve.
    if shutil.disk_usage(directory.parent).free < 40*1024**3 + bed.size*24:
        raise ValueError('Collision probes would violate 40 GiB disk reserve')
    directory.mkdir(exist_ok=False)
    counts = np.zeros(len(chunks), dtype=np.int64)
    for row, side in enumerate(lateral):
        for start in range(0, grid['nx'], block_cells):
            sl = slice(start, min(start+block_cells, grid['nx']))
            mask = wet[row, sl]
            if not np.all((mask == 0) | (mask == 1)):
                raise ValueError('Nonbinary wet mask')
            keep = mask.astype(bool)
            # Preserve the legacy arithmetic (including origin addition and
            # subtraction) and the float32 bed subtraction before promotion.
            xy = ((selected[sl, 1:3] + side*selected[sl, 3:5]) + origin)[keep] - origin
            z = (bed[row, sl][keep] - mapping['vertical_datum_m'])*100
            probes = np.column_stack((xy[:, 0]*100, -xy[:, 1]*100, z))
            assigned = owners(probes, chunks)
            order = np.argsort(assigned, kind='stable')
            unique, starts, sizes = np.unique(assigned[order], return_index=True, return_counts=True)
            for owner, first, size in zip(unique, starts, sizes):
                values = probes[order[first:first+size]].astype('<f8', copy=False)
                with (directory/f'chunk_{owner:05d}.bin').open('ab') as output:
                    values.tofile(output)
                counts[owner] += len(values)
    if not counts.sum():
        raise ValueError('No cooked wet collision probes')
    records = []; files = {}
    for index, owner in chunks.items():
        if counts[owner]:
            path = directory/f'chunk_{owner:05d}.bin'
            relative = path.relative_to(root).as_posix()
            digest = sha(path); files[relative] = digest
            records.append(dict(chunk=list(index), file=relative, count=int(counts[owner]), sha256=digest))
    return dict(schema='raftsim.chunked_wet_bed_probes.v1', encoding='xyz_cm_float64_le',
                count=int(counts.sum()), chunks=records), files
