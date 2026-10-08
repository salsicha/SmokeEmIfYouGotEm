"""Independent all-pixel audit against the original optical and DSM captures.

The DSM reference reads the two original tiles directly, without the builder's
crop/merge/interpolation functions. Agreement verifies numerical registration,
not the DSM's surveying accuracy or its suitability as underwater ground.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio
from pyproj import Transformer

ROOT=Path(__file__).resolve().parents[2]
OPTICAL=ROOT/'physics/data/real_world/futaleufu_river_chile/futaleufu_sources_2026_09/sentinel2'
BANDS=('blue','green','red','nir')


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def audit(folder):
    folder=Path(folder).resolve()
    output=folder/'all-pixel-audit.json'
    if output.exists():
        raise ValueError('Fresh independent audit required')
    manifest=folder/'manifest.json';digest=sha(manifest)
    m=json.loads(manifest.read_text());r0,r1,c0,c1=m['grid']['native_optical_crop_rc']
    for name,expected in m['sources_sha256'].items():
        path=(ROOT/name).resolve();path.relative_to(ROOT)
        if sha(path)!=expected:raise ValueError('Changed original source: '+name)
    all_valid=[]
    for item in m['optical']:
        if sha(folder/item['file'])!=item['sha256']:raise ValueError('Changed cropped optical artifact')
        with np.load(OPTICAL/item['source']) as original,np.load(folder/item['file']) as crop:
            valid=np.ones(m['grid']['shape'],dtype=bool)
            for band in BANDS:
                if not np.array_equal(original[band][r0:r1,c0:c1],crop[band]):
                    raise ValueError('Original optical pixels were changed')
                valid &= crop[band]!=0
            if not np.array_equal(valid,crop['valid']) or int((~valid).sum())!=item['missing_pixels']:
                raise ValueError('Nodata validity was changed')
            all_valid.append(valid)
    originals=[];transforms=[]
    for item in m['dsm']['sources']:
        with rasterio.open(ROOT/item['path']) as source:
            originals.append(source.read(1));transforms.append(source.transform)
    a,b=transforms
    if len(originals)!=2 or abs(a.c+originals[0].shape[1]*a.a-b.c)>1e-10 or any(abs(a[k]-b[k])>1e-10 for k in (0,1,3,4,5)):
        raise ValueError('Original adjacent tile lattice changed')
    raw=np.concatenate(originals,axis=1)
    rows,cols=np.indices(m['grid']['shape'])
    g=m['grid']['transform'];east=g[2]+(cols+.5)*g[0];north=g[5]+(rows+.5)*g[4]
    longitude,latitude=Transformer.from_crs(32718,4326,always_xy=True).transform(east,north)
    column=(longitude-a.c)/a.a-.5;row=(latitude-a.f)/a.e-.5
    i=np.floor(column).astype(int);j=np.floor(row).astype(int);u=column-i;v=row-j
    if i.min()<0 or j.min()<0 or i.max()+1>=raw.shape[1] or j.max()+1>=raw.shape[0]:
        raise ValueError('Original DSM support missing')
    expected=raw[j,i]*(1-u)*(1-v)+raw[j,i+1]*u*(1-v)+raw[j+1,i]*(1-u)*v+raw[j+1,i+1]*u*v
    if sha(folder/m['dsm']['file'])!=m['dsm']['sha256']:raise ValueError('Changed DSM artifact')
    with np.load(folder/m['dsm']['file']) as archive:
        error=np.abs(archive['dsm_m']-expected)
        counts=archive['valid_optical_dates']
        if not np.array_equal(counts,np.sum(all_valid,axis=0)) or counts.min()<1:
            raise ValueError('Incorrect temporal source support')
    if not np.isfinite(error).all() or error.max()>.001:
        raise ValueError('Source interpolation differs by more than 1 mm: '+str(error.max()))
    if sha(manifest)!=digest:raise ValueError('Manifest changed during audit')
    result=dict(schema='raftsim.futaleufu_source_window_all_pixel_audit.v1',manifest_sha256=digest,
        native_optical_pixels_preserved=True,
        missing_pixels_by_date={i['datetime']:i['missing_pixels'] for i in m['optical']},
        dsm_probe_count=error.size, dsm_sampler='Independent exact pyproj and four original tile pixels; no builder crop/merge/sampler',
        seam_crossing_interpolations=int((i==originals[0].shape[1]-1).sum()),
        dsm_error_m=dict(maximum=float(error.max()),p95=float(np.quantile(error,.95))),
        numerical_tolerance_m=.001,minimum_valid_optical_dates=int(counts.min()),engine_validated=False)
    with output.open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder',type=Path)
    print(json.dumps(audit(parser.parse_args().folder),indent=2))
