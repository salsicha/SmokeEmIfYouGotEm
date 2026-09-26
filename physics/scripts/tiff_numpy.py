"""Minimal numpy/zlib reader for the project's single-band GeoTIFF grids.

Supports the layouts written by the reconstruction scripts (rasterio, tiled
or striped, uncompressed or deflate, optional horizontal/float predictor)
so grid tools can run where rasterio is unavailable. Georeferencing is read
from ModelPixelScale/ModelTiepoint only; callers must still check the grid
against the manifest that owns the file.
"""
import struct
import zlib
from pathlib import Path

import numpy as np

_TYPES = {1: 'B', 2: 's', 3: 'H', 4: 'I', 5: 'II', 11: 'f', 12: 'd', 16: 'Q'}
_SIZES = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 11: 4, 12: 8, 16: 8}


def _ifd(data, endian, offset):
    count = struct.unpack_from(endian + 'H', data, offset)[0]
    tags = {}
    for k in range(count):
        tag, typ, n, value = struct.unpack_from(endian + 'HHI4s', data, offset + 2 + 12 * k)
        size = _SIZES[typ] * n
        raw = value[:size] if size <= 4 else data[struct.unpack_from(endian + 'I', value)[0]:][:size]
        if typ == 2:
            tags[tag] = raw.rstrip(b'\0').decode('ascii', 'replace')
        elif typ == 5:
            tags[tag] = [a / b for a, b in zip(*[iter(struct.unpack(endian + 'I' * (2 * n), raw))] * 2)]
        else:
            tags[tag] = list(struct.unpack(endian + _TYPES[typ] * n, raw))
    return tags


def read_geotiff(path):
    """Return (array[rows, cols], dict(first_vertex_utm_m=(x, y), cell_m=...), nodata)."""
    data = Path(path).read_bytes()
    endian = {b'II': '<', b'MM': '>'}[data[:2]]
    assert struct.unpack_from(endian + 'H', data, 2)[0] == 42, 'BigTIFF not supported'
    tags = _ifd(data, endian, struct.unpack_from(endian + 'I', data, 4)[0])
    width, height = tags[256][0], tags[257][0]
    bits = tags[258][0]
    compression = tags.get(259, [1])[0]
    predictor = tags.get(317, [1])[0]
    sample_format = tags.get(339, [1])[0]
    assert tags.get(277, [1])[0] == 1, 'single band only'
    dtype = {(3, 32): 'f4', (3, 64): 'f8', (1, 8): 'u1', (1, 16): 'u2', (2, 16): 'i2', (1, 32): 'u4', (2, 32): 'i4'}[(sample_format, bits)]
    dt = np.dtype(endian + dtype)
    out = np.empty((height, width), dt.newbyteorder('='))
    if 322 in tags:
        tw, th = tags[322][0], tags[323][0]
        offsets, counts = tags[324], tags[325]
        blocks = [(r, c, tw, th) for r in range(0, height, th) for c in range(0, width, tw)]
    else:
        rps = tags.get(278, [height])[0]
        offsets, counts = tags[273], tags[279]
        blocks = [(r, 0, width, rps) for r in range(0, height, rps)]
    for (r, c, bw, bh), off, cnt in zip(blocks, offsets, counts):
        raw = data[off:off + cnt]
        if compression == 8 or compression == 32946:
            raw = zlib.decompress(raw)
        else:
            assert compression == 1, f'compression {compression} unsupported'
        rows_here = min(bh, height - r) if 322 not in tags else bh
        if predictor == 3:
            b = np.frombuffer(raw, np.uint8).reshape(rows_here, bw * dt.itemsize)
            b = np.cumsum(b, axis=1, dtype=np.uint8)
            # Float predictor stores byte planes most-significant first.
            b = b.reshape(rows_here, dt.itemsize, bw).transpose(0, 2, 1)
            block = np.ascontiguousarray(b).view(np.dtype('>' + dtype)).reshape(rows_here, bw)
        else:
            block = np.frombuffer(raw, dt).reshape(rows_here, bw)
            if predictor == 2:
                block = np.cumsum(block, axis=1, dtype=block.dtype)
        h = min(bh, height - r); w = min(bw, width - c)
        out[r:r + h, c:c + w] = block[:h, :w]
    scale = tags.get(33550); tie = tags.get(33922)
    geo = None
    if scale and tie:
        # Tie point (i, j, k, x, y, z): raster (0, 0) corner. PixelIsArea by default.
        area = True
        if 34735 in tags:
            keys = tags[34735]
            for k in range(4, len(keys), 4):
                if keys[k] == 1025:  # GTRasterTypeGeoKey
                    area = keys[k + 3] == 1
        x0, y0 = tie[3] - tie[0] * scale[0], tie[4] + tie[1] * scale[1]
        geo = dict(corner_utm_m=(x0, y0), cell_m=(scale[0], scale[1]), pixel_is_area=area)
    nodata = tags.get(42113)
    return out, geo, (float(nodata) if nodata and nodata.strip() not in ('', 'nan') else (np.nan if nodata else None))
