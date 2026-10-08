"""Strict native CSV/gzip readers; bound parsing scratch without dropping fields.

The returned numeric arrays still cost eight bytes per field per cell. This
removes whole-file text parsing overhead, not the caller's full-domain budget.
"""
import csv
import gzip
import shutil
import tempfile
from itertools import islice
from pathlib import Path
import numpy as np


def native_frame_paths(cook, native, minimum=1):
    cook = Path(cook)
    names = native.get('frames')
    storage = native.get('frame_storage')
    if storage not in (None, 'streamed_lossless_gzip_csv_v1'):
        raise ValueError('Unknown native frame storage')
    suffix = '.csv.gz' if storage else '.csv'
    if not isinstance(names, list) or len(names) < minimum:
        raise ValueError('Incomplete native frame collection')
    expected = [f'frames/frame_{i:04d}{suffix}' for i in range(len(names))]
    if names != expected:
        raise ValueError('Invalid native frame paths or order')
    directory = (cook/'frames').resolve()
    paths = [cook/name for name in names]
    if any(not p.is_file() or p.resolve().parent != directory for p in paths):
        raise ValueError('Missing or escaped native frame')
    # Reject orphaned, mixed-format or partial frames, not just missing entries.
    actual = {p.name for p in (cook/'frames').glob('frame_*')}
    if actual != {p.name for p in paths}:
        raise ValueError('Unregistered native frame collection')
    return paths


def load_frame(path, shape, *, block_cells=16384):
    return _load_frame(path,shape,block_cells,np.empty)


class NativeFrameStore:
    """Scoped disk-backed frames. Borrowed arrays must not outlive this scope.

    Only fresh private scratch files are removed on exit; native sources are
    never changed. Reserve forty GiB on the same volume before every allocation.
    """
    def __init__(self,parent):
        self.parent=Path(parent);self._temporary=None;self._arrays=[]

    def __enter__(self):
        if self._temporary is not None:raise ValueError('Frame store already open')
        self._temporary=tempfile.TemporaryDirectory(prefix='raftsim-frame-review-',dir=self.parent)
        return self

    def _allocate(self,count,dtype):
        if self._temporary is None:raise ValueError('Frame store is not open')
        required=int(count)*np.dtype(dtype).itemsize+65536
        if shutil.disk_usage(self._temporary.name).free<required+40*1024**3:
            raise ValueError('Insufficient frame scratch disk headroom; forty GiB reserve required')
        path=Path(self._temporary.name)/f'frame_{len(self._arrays):04d}.npy'
        array=np.lib.format.open_memmap(path,mode='w+',dtype=dtype,shape=(count,))
        self._arrays.append(array)
        return array

    def load(self,path,shape,*,block_cells=16384):
        if self._temporary is None:raise ValueError('Frame store is not open')
        return _load_frame(path,shape,block_cells,self._allocate)

    def __exit__(self,*exc):
        # Explicit close is necessary before TemporaryDirectory cleanup on
        # Windows; returned field views otherwise keep the mapping open.
        for array in self._arrays:array._mmap.close()
        self._arrays.clear()
        if self._temporary is not None:
            self._temporary.cleanup();self._temporary=None


def _load_frame(path, shape, block_cells, allocate):
    if (len(shape) != 2 or any(not isinstance(n, (int, np.integer)) or n <= 0 for n in shape)
            or not isinstance(block_cells, int) or block_cells <= 0):
        raise ValueError('Invalid native frame shape or parsing block')
    count = int(shape[0])*int(shape[1])
    path = Path(path)
    opener = gzip.open if path.name.endswith('.csv.gz') else open
    with opener(path, 'rt', encoding='utf-8', newline='') as stream:
        reader = csv.reader(stream)
        names = next(reader, [])
        if (not names or len(names) != len(set(names)) or any(not n.isidentifier() for n in names)
                or not {'row', 'col', 'h'} <= set(names)):
            raise ValueError('Invalid native frame header')
        table = allocate(count, dtype=[(name, '<f8') for name in names])
        row_index, col_index, h_index = (names.index(k) for k in ('row', 'col', 'h'))
        offset = 0
        while lines := list(islice(reader, block_cells)):
            block = np.asarray(lines, dtype=np.float64)
            if block.shape != (len(lines), len(names)) or offset+len(lines) > count:
                raise ValueError('Incomplete or oversized native frame')
            if not np.isfinite(block).all():
                raise ValueError('Nonfinite native state')
            indices = np.arange(offset, offset+len(lines))
            if (not np.array_equal(block[:, row_index], indices//shape[1])
                    or not np.array_equal(block[:, col_index], indices % shape[1])):
                raise ValueError('Unordered frame cells')
            if (block[:, h_index] < 0).any():
                raise ValueError('Negative water depth')
            for i, name in enumerate(names):
                table[name][offset:offset+len(lines)] = block[:, i]
            offset += len(lines)
        if offset != count:
            raise ValueError('Incomplete native frame')
    return {name: table[name].reshape(shape) for name in names}
