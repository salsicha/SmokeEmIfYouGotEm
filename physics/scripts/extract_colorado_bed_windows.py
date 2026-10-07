"""Read small construction windows from the sparse USGS 2021 BigTIFF.

Requires rasterio (already available in tmp/south-fork-geospatial-deps).
Never allocate the complete 26-billion-cell source. Preserve NoData: this
survey measures pools near the centreline, NOT the rapids or shallow water.
"""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path

import numpy as np
import rasterio
from rasterio.windows import Window, from_bounds


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''): h.update(chunk)
    return h.hexdigest()


def crop_bounds(bounds, margin_m=80):
    if not isinstance(margin_m,int) or not 20<=margin_m<=400:
        raise ValueError('Construction crop margin must be an integer between 20 and 400 m')
    if len(bounds)!=4 or not all(math.isfinite(v) for v in bounds) or bounds[0]>=bounds[2] or bounds[1]>=bounds[3]:
        raise ValueError('Invalid source bounds')
    x0,y0,x1,y1=bounds
    bbox=(math.floor(x0)-margin_m,math.floor(y0)-margin_m,
          math.ceil(x1)+margin_m,math.ceil(y1)+margin_m)
    if (bbox[2]-bbox[0])*(bbox[3]-bbox[1])>8_000_000:
        raise ValueError('Crop exceeds bounded memory budget')
    return bbox


def selected_windows(index,names):
    rows=[r for r in index['windows'] if not names or r['name'] in names]
    if not rows or set(names)-{r['name'] for r in rows}:
        raise ValueError('Unknown or empty source-window selection')
    return rows


def read_survey_window(source, window, allow_partial=False):
    """Read only the intersection; retain off-raster cells as unknown, not bed.

    Avoid GDAL boundless VRT reads over the enormous sparse source. Allocate
    only the explicitly bounded crop and record source-extent coverage.
    """
    if window.width*window.height>8_000_000:
        raise ValueError('Survey crop exceeds memory budget')
    extent=Window(0,0,source.width,source.height)
    from rasterio.errors import WindowError
    try:
        overlap=window.intersection(extent)
    except WindowError:
        overlap=None
    if not allow_partial and overlap!=window:
        raise ValueError('Construction window outside source extent')
    bed=np.full((int(window.height),int(window.width)),np.nan,dtype=np.float32)
    covered=0
    if overlap is not None:
        y=int(overlap.row_off-window.row_off); x=int(overlap.col_off-window.col_off)
        h,w=int(overlap.height),int(overlap.width)
        bed[y:y+h,x:x+w]=source.read(1,window=overlap,masked=True).filled(np.nan)
        covered=h*w
    return bed,covered


def extract(raster, windows, out, names=(), margin_m=80, allow_partial_survey=False):
    if out.exists(): raise ValueError('Fresh bed-crop output required')
    index=json.loads((windows/'index.json').read_text(encoding='utf-8'))
    results=[]
    with rasterio.open(raster) as source:
        if source.crs.to_epsg()!=6404 or source.count!=1 or source.res!=(1.,1.):
            raise ValueError('Unexpected bathymetry CRS, band count or resolution')
        if source.nodata is None: raise ValueError('Missing source NoData convention')
        out.mkdir(parents=True)
        for entry in selected_windows(index,names):
            key=re.sub(r'[^a-z0-9]+','_',entry['name'].lower()).strip('_')
            definition=json.loads((windows/(key+'.json')).read_text(encoding='utf-8'))
            # Source acquisition margin, never inferred river width or padding.
            bbox=crop_bounds(definition['bounds_epsg6404'],margin_m)
            w=from_bounds(*bbox,transform=source.transform).round_offsets().round_lengths()
            if w.width*w.height>8_000_000: raise ValueError('Crop exceeds bounded memory budget')
            bed,source_extent_cells=read_survey_window(source,w,allow_partial_survey)
            valid=np.isfinite(bed)
            if np.any(valid & ((bed<300.) | (bed>930.))):
                raise ValueError('Unexpected source height; refuse datum/raster substitution')
            transform=source.window_transform(w)
            np.savez_compressed(out/(key+'.npz'),
                elevation_ellipsoid_m=bed,measured_pool_bed_mask=valid,
                corner_east_north_m=np.array((transform.c,transform.f)),cell_m=np.array(source.res))
            pts=[(s['easting'],s['northing']) for s in definition['samples']]
            sampled=np.array([float(p[0]) if not np.ma.getmaskarray(p)[0] else np.nan
                              for p in source.sample(pts,masked=True)])
            station=np.array([s['local_arc_station_m'] for s in definition['samples']])
            rapid_station=definition.get('rapid_point_local_station_m')
            crux=None if rapid_station is None else np.abs(station-rapid_station)<=200.
            # A location sample is not a wet-area or full-width coverage measure.
            result=dict(name=definition['name'],file=key+'.npz',bbox_epsg6404=bbox,
                shape=list(bed.shape),measured_pool_bed_cells=int(valid.sum()),
                within_source_raster_extent_cells=source_extent_cells,
                outside_source_raster_extent_cells=int(bed.size-source_extent_cells),
                sampled_profile_points=len(pts),profile_points_with_bed=int(np.isfinite(sampled).sum()),
                rapid_point_plus_minus_200m_samples=int(crux.sum()) if crux is not None else None,
                rapid_point_plus_minus_200m_samples_with_bed=int(np.isfinite(sampled[crux]).sum()) if crux is not None else None,
                full_channel_bathymetry_coverage=None,
                sha256=sha(out/(key+'.npz')))
            results.append(result)
            print(f"{result['name']}: {result['measured_pool_bed_cells']} surveyed pool cells; "
                  f"near-label profile samples with bed={result['rapid_point_plus_minus_200m_samples_with_bed']}/{result['rapid_point_plus_minus_200m_samples']}",flush=True)
    manifest=dict(schema='raftsim.colorado_pool_bed_windows.v1',
        source_doi=index['source_doi'],rights=index['source_rights'],rights_url=index['source_rights_url'],
        source_raster_sha256=sha(raster),construction_index_sha256=sha(windows/'index.json'),
        horizontal_crs='EPSG:6404',vertical_datum='NAD83(2011) ellipsoid metres',
        measured_scope='Multibeam pools near centreline at approximately 8400 cfs; NOT rapids or shallow water',
        missing_data_policy='Preserved as NaN with an explicit measured mask; no interpolation or invented underwater rocks',
        construction_margin_m=margin_m,runnable_maps_created=0,windows=results)
    manifest['allow_partial_survey']=allow_partial_survey
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    return manifest


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--raster',type=Path,required=True)
    p.add_argument('--windows',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--names',nargs='*',default=[])
    p.add_argument('--margin-m',type=int,default=80)
    p.add_argument('--allow-partial-survey',action='store_true',
                   help='Keep off-raster cells explicitly missing; never infer survey coverage')
    a=p.parse_args()
    extract(a.raster,a.windows,a.out,a.names,a.margin_m,a.allow_partial_survey)
