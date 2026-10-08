"""Strict native-grid sampling for the archived Futaleufu Sentinel mosaics.

Requested acquisition rectangles are not raster transforms. This module does
not classify rapids, infer coordinates from brightness or alter source pixels.
"""
import hashlib
from pathlib import Path

import numpy as np

BANDS=('blue','green','red','nir')


def grid(item):
    if item.get('epsg')!=32718:
        raise ValueError('Expected Futaleufu Sentinel WGS84 / UTM 18S')
    reference=item['bands']['blue']
    for name in BANDS:
        band=item['bands'][name]
        if any(band[key]!=reference[key] for key in ('x0','y0','cell_m','shape')):
            raise ValueError('Sentinel reflectance bands have different native grids')
        shape=np.asarray(band['shape'],dtype=float)
        if (shape.shape!=(2,) or not np.isfinite(shape).all() or
                np.any(shape<2) or np.any(shape!=np.floor(shape)) or
                band['cell_m']!=10 or not np.isfinite([band['x0'],band['y0']]).all()):
            raise ValueError('Invalid captured Sentinel grid')
        radiometry=band['raster_bands']
        if (len(radiometry)!=1 or radiometry[0].get('scale')!=.0001 or
                radiometry[0].get('offset')!=-.1 or radiometry[0].get('nodata')!=0):
            raise ValueError('Unreviewed captured Sentinel radiometry')
    return reference


def sampling_points(east,north,item):
    meta=grid(item)
    east,north=np.broadcast_arrays(np.asarray(east,dtype=float),np.asarray(north,dtype=float))
    rows=(meta['y0']-north)/meta['cell_m']-.5
    cols=(east-meta['x0'])/meta['cell_m']-.5
    if (not np.isfinite(rows).all() or not np.isfinite(cols).all() or
            np.any(rows<0) or np.any(cols<0) or
            np.any(rows>meta['shape'][0]-1) or np.any(cols>meta['shape'][1]-1)):
        raise ValueError('Requested evidence lies outside captured Sentinel pixel centres')
    return rows,cols


def load_reflectance(folder,item):
    folder=Path(folder).resolve()
    path=(folder/item['npz']).resolve();path.relative_to(folder)
    if hashlib.sha256(path.read_bytes()).hexdigest()!=item['npz_sha256']:
        raise ValueError('Changed captured Sentinel mosaic')
    meta=grid(item)
    result={};valid=None
    with np.load(path,allow_pickle=False) as archive:
        for name in BANDS:
            raw=archive[name]
            if list(raw.shape)!=meta['shape'] or raw.dtype!=np.dtype('uint16'):
                raise ValueError('Captured Sentinel array disagrees with metadata')
            known=raw!=0
            valid=known if valid is None else valid & known
            result[name]=raw.astype(np.float32)*.0001-.1
    return result,valid


def require_sample_support(valid,rows,cols):
    """Refuse unknown bilinear neighbours instead of turning nodata into land."""
    r=np.minimum(np.floor(rows).astype(int),valid.shape[0]-2)
    c=np.minimum(np.floor(cols).astype(int),valid.shape[1]-2)
    if not (valid[r,c]&valid[r+1,c]&valid[r,c+1]&valid[r+1,c+1]).all():
        raise ValueError('Requested evidence touches Sentinel nodata; source coverage review required')
