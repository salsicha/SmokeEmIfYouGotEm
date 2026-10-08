"""Archive the bounded 2021 USGS Horn Creek export and visible rock caps.

Manual pixel outlines are exposed surface observations, not submerged solids.
This script never changes native maps, solver inputs or a running job.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[2]
BASE = 'physics/data/real_world/colorado_river_grand_canyon_rowing'
MAP = BASE+'/catalog_solver_inputs_2026_10_v3/horn_creek/coordinate_map.json'
MAP_HASH = 'ee671a4fe0150b56bd44e760d3e3165d80c44a4851c4dba0c3fa297fd82d90c3'
IMAGE_HASH = '01d1a03312c88abab54ddd1921171441f21a78f7ed17890aa634d411b6fa4f06'
# Column,row at source pixel centres, manually inspected at native resolution.
# Conservative outlines exclude surrounding foam, shadow and wetted aprons.
CAPS = {
    'upstream_bankward_exposed_cap': [[1523,1453],[1530,1452],[1533,1460],[1537,1474],[1534,1480],[1522,1479],[1517,1473],[1518,1461]],
    'downstream_channelward_exposed_cap': [[1474,1388],[1480,1387],[1483,1394],[1480,1402],[1477,1408],[1467,1408],[1462,1403],[1463,1396]],
}

def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def native_projection(xy, mapping):
    """Nearest chart segment, left-positive lateral; never infer rock height."""
    xy=np.asarray(xy,dtype=float)
    if xy.shape!=(2,) or not np.isfinite(xy).all():
        raise ValueError('Invalid geographic point')
    points=np.asarray(mapping['points'], dtype=float)
    line=points[:,1:3]+mapping['horizontal_origin_epsg6404_m']
    segments=np.diff(line,axis=0)
    length2=np.sum(segments*segments,axis=1)
    if not np.isfinite(points).all() or np.any(length2<=0):
        raise ValueError('Invalid chart')
    delta=xy-line[:-1]
    t=np.clip(np.sum(delta*segments,axis=1)/length2,0,1)
    displacement=delta-t[:,None]*segments
    i=int(np.argmin(np.sum(displacement**2,axis=1)))
    normal=(1-t[i])*points[i,3:5]+t[i]*points[i+1,3:5]
    if not np.isfinite(normal).all() or normal@normal<.5:
        raise ValueError('Invalid chart normal')
    lateral=float(displacement[i]@normal/(normal@normal))
    station=float(points[i,0]+t[i]*(points[i+1,0]-points[i,0]))
    residual=float(np.linalg.norm(displacement[i]-lateral*normal))
    if residual>.02:
        raise ValueError('Chart projection residual exceeds 2 cm')
    return [station,lateral],residual

def archive(source, destination):
    if destination.exists():
        raise ValueError('Fresh archive directory required')
    capture=json.loads((source/'completed.json').read_text())
    for name,digest in capture['files'].items():
        if Path(name).name!=name or sha(source/name)!=digest:
            raise ValueError('Capture hash mismatch or unsafe name: '+name)
    if sha(source/'horn_creek_2021_0p2m.tif')!=IMAGE_HASH or sha(ROOT/MAP)!=MAP_HASH:
        raise ValueError('Unexpected geographic source')
    mapping=json.loads((ROOT/MAP).read_text())
    features=[]
    with rasterio.open(source/'horn_creek_2021_0p2m.tif') as src:
        if src.crs.to_epsg()!=6404 or src.count!=4 or src.dtypes!=('uint16',)*4 or not np.allclose(src.res,[.2,.2],atol=1e-7,rtol=0):
            raise ValueError('Unexpected source raster')
        bands=src.read()
        nonzero=np.any(bands!=0,axis=0)
        points=np.asarray(mapping['points'])
        active=points[(points[:,0]>=600)&(points[:,0]<=1100)]
        centre_xy=active[:,1:3]+mapping['horizontal_origin_epsg6404_m']
        rows,cols=rasterio.transform.rowcol(src.transform,centre_xy[:,0],centre_xy[:,1])
        if not nonzero[rows,cols].all():
            raise ValueError('Missing centreline imagery')
        for name,pixels in CAPS.items():
            xy=np.asarray([src.xy(r,c) for c,r in pixels])
            if not all(nonzero[r,c] for c,r in pixels):
                raise ValueError('Uncovered observed footprint')
            native=[native_projection(point,mapping) for point in xy]
            centre,residual=native_projection(xy.mean(axis=0),mapping)
            local=xy-xy[0]
            area=round(abs(float(np.sum(local[:,0]*np.roll(local[:,1],-1)-local[:,1]*np.roll(local[:,0],-1))*.5)),6)
            features.append(dict(id=name,pixel_column_row=pixels,exposed_cap_polygon_epsg6404_m=xy.tolist(),native_station_left_lateral_polygon_m=[v[0] for v in native],native_vertex_mean_station_left_lateral_m=centre,exposed_cap_area_m2=area,max_chart_projection_residual_m=max([residual]+[v[1] for v in native]),interpretation='Visible exposed cap near the documented entrance horns; association inferred from image position and guide description, not surveyed rock identification.',height_m=None,submerged_volume=None,collision_ready=False))
        coverage=dict(dataset_mask_valid_fraction=float((src.dataset_mask()>0).mean()),nonzero_any_band_fraction=float(nonzero.mean()),source_chart_centreline_samples=len(active),source_chart_centreline_nonzero_fraction=1.0,note='Black mosaic corners have zero values despite a valid dataset mask; do not treat the mask alone as data coverage.')
    destination.mkdir(parents=True)
    for name in (*capture['files'],'completed.json'):
        shutil.copyfile(source/name,destination/name)
    manifest=dict(schema='raftsim.horn_creek_surface_evidence.v1',source_doi='https://doi.org/10.5066/P9BBGN6G',source_catalog='https://data.usgs.gov/datacatalog/data/USGS%3A65b042fed34ef34c3506eb3b',license='U.S. public domain; source catalog license http://www.usa.gov/publicdomain/label/1.0/',retrieved_on='2026-10-07',acquired='2021-05-29 through 2021-06-04; corridor acquisition interval, exact crop flight timestamp unresolved',bands=['red','green','blue','near_infrared'],pixel_size_m=.2,horizontal_crs='EPSG:6404',source_horizontal_accuracy_m={'confidence_95':.514,'rmse':.297},source_accuracy_scope='Release-wide assessment, not a new survey of these rocks; manual outline uncertainty is additional.',manual_outline_uncertainty_m=1.0,manual_outline_uncertainty_scope='Conservative working allowance, not statistically measured accuracy.',coordinate_map=MAP,coordinate_map_sha256=MAP_HASH,coverage=coverage,features=features,guide=dict(url='https://gorafting.com/united-states/arizona/grand-canyon/horn-creek-rapid/',finding='Two entrance pour-overs lie on the left; alternatives are the gap between them or a right entry followed by a leftward move. A lower left-wall feature also matters.',scope='Qualitative sequence only. No copyrighted photos or guide maps reproduced.'),limitations=['Exposed horizontal footprints only, not full obstacles or measured heights.','Submerged extent, pillows and flow field remain unmeasured here.','Bright whitewater is not automatically a rock or persistent hole.','No engine integration, difficulty classification or performance acceptance.'],files={p.name:sha(p) for p in destination.iterdir() if p.is_file()})
    (destination/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    return manifest

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    result=archive(args.source,args.out)
    print(json.dumps(dict(features=result['features'],coverage=result['coverage']),indent=2))
