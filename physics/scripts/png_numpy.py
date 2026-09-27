"""Minimal numpy/zlib PNG reader and writer (no PIL on this host).

Reads 8-bit greyscale, grey+alpha, RGB, RGBA and palette PNGs without
interlacing: the layouts WMTS/tile servers and the project's own tools write.
Returns [rows, cols] or [rows, cols, channels] uint8.
"""
import struct
import zlib
from pathlib import Path

import numpy as np

_CHANNELS = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}


def read_png(path_or_bytes):
    data = path_or_bytes if isinstance(path_or_bytes, (bytes, bytearray)) else Path(path_or_bytes).read_bytes()
    assert data[:8] == b'\x89PNG\r\n\x1a\n', 'not a PNG'
    pos, idat, palette, trns = 8, [], None, None
    while pos < len(data):
        n, tag = struct.unpack_from('>I4s', data, pos)
        body = data[pos + 8:pos + 8 + n]
        pos += 12 + n
        if tag == b'IHDR':
            w, h, depth, ctype, _, _, interlace = struct.unpack('>IIBBBBB', body)
        elif tag == b'PLTE':
            palette = np.frombuffer(body, np.uint8).reshape(-1, 3)
        elif tag == b'tRNS':
            trns = np.frombuffer(body, np.uint8)
        elif tag == b'IDAT':
            idat.append(body)
        elif tag == b'IEND':
            break
    assert depth == 8 and interlace == 0, f'unsupported PNG depth {depth} / interlace {interlace}'
    ch = _CHANNELS[ctype]
    stride = w * ch
    raw = np.frombuffer(zlib.decompress(b''.join(idat)), np.uint8).reshape(h, stride + 1)
    out = np.zeros((h, stride), np.uint8)
    prev = np.zeros(stride, np.int32)
    for r in range(h):
        f, line = raw[r, 0], raw[r, 1:].astype(np.int32)
        if f == 0:
            cur = line
        elif f == 1:
            cur = line.copy()
            for c in range(ch, stride, ch):
                cur[c:c + ch] = (cur[c:c + ch] + cur[c - ch:c]) & 255
        elif f == 2:
            cur = (line + prev) & 255
        elif f == 3:
            cur = line.copy()
            for c in range(stride):
                left = cur[c - ch] if c >= ch else 0
                cur[c] = (cur[c] + ((left + prev[c]) >> 1)) & 255
        elif f == 4:
            cur = line.copy()
            for c in range(stride):
                a = cur[c - ch] if c >= ch else 0
                b = prev[c]
                cc = prev[c - ch] if c >= ch else 0
                p = a + b - cc
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - cc)
                pred = a if (pa <= pb and pa <= pc) else (b if pb <= pc else cc)
                cur[c] = (cur[c] + pred) & 255
        else:
            raise ValueError(f'bad PNG filter {f}')
        out[r] = cur
        prev = cur
    img = out.reshape(h, w, ch) if ch > 1 else out
    if ctype == 3:
        idx = out
        rgb = palette[idx]
        if trns is not None:
            alpha = np.full(len(palette), 255, np.uint8); alpha[:len(trns)] = trns
            return np.concatenate([rgb, alpha[idx][..., None]], axis=2)
        return rgb
    return img


def write_png(path, img):
    """Write [rows, cols] grey or [rows, cols, 3|4] RGB(A) uint8."""
    img = np.asarray(img, np.uint8)
    h, w = img.shape[:2]
    ch = 1 if img.ndim == 2 else img.shape[2]
    raw = np.zeros((h, w * ch + 1), np.uint8)
    raw[:, 1:] = img.reshape(h, w * ch)

    def chunk(tag, body):
        return struct.pack('>I', len(body)) + tag + body + struct.pack('>I', zlib.crc32(tag + body) & 0xffffffff)
    ctype = {1: 0, 3: 2, 4: 6}[ch]
    Path(path).write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, ctype, 0, 0, 0))
                           + chunk(b'IDAT', zlib.compress(raw.tobytes(), 6)) + chunk(b'IEND', b''))
