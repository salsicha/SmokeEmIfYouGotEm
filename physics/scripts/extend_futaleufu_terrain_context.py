"""Surround the continuous river with captured terrain, preserving every bed tile.

Use only complete Landscape tiles within the independently verified source
pixel centres. Keep the original 2 m lattice/encoding and all parent bytes.
No excavation, clamped source edges, invented elevation or borrowed scenery.
"""
import argparse
import copy
import json
from pathlib import Path
import shutil

import numpy as np
from PIL import Image

from build_futaleufu_corridor_sources import ROOT, sha
from futaleufu_corridor_bed import source_heights
from export_futaleufu_corridor_terrain import encode, RESERVE
from export_colorado_continuous_terrain import LandscapeTriangles, write_png_u16


def supported_chunks(grid, origin, span):
    t=grid['transform'];h,w=grid['shape'];origin=np.asarray(origin,float)
    if (grid['epsg']!=32718 or t[:2]!=[10,0] or t[3:5]!=[0,-10]
            or min(h,w)<2 or origin.shape!=(2,) or not np.isfinite([*t,*origin,span]).all() or span<=0):
        raise ValueError('Reviewed north-up source frame and positive shared span required')
    low=np.array([t[2]+5,t[5]-(h-.5)*10])
    high=np.array([t[2]+(w-.5)*10,t[5]-5])
    first=np.ceil((low-origin)/span).astype(int)
    last=np.floor((high-origin)/span).astype(int)-1
    return [(i,j) for i in range(first[0],last[0]+1) for j in range(first[1],last[1]+1)]


def lattice(chunk, origin, spacing):
    west,south=np.asarray(origin)+np.asarray(chunk)*126*spacing
    row,col=np.indices((127,127))
    return np.stack((west+col*spacing,south+126*spacing-row*spacing),axis=-1)


def verify_join(parent, original, unmodified_source, keys):
    i,j=parent
    for di,dj,edge in ((-1,0,(slice(None),0)),(1,0,(slice(None),-1)),
                       (0,1,(0,slice(None))),(0,-1,(-1,slice(None)))):
        if (i+di,j+dj) not in keys and not np.array_equal(original[edge],unmodified_source[edge]):
            raise ValueError(f'Original inferred terrain touches context seam at {parent}: {(di,dj)}')


def extend(parent_folder, source_folder, output):
    parent_folder,source_folder,output=map(lambda p:Path(p).resolve(),(parent_folder,source_folder,output))
    output.relative_to(ROOT)
    if output.exists():raise ValueError('Fresh context output required')
    parent_path=parent_folder/'manifest.json';source_path=source_folder/'manifest.json'
    parent,source=[json.loads(p.read_text()) for p in (parent_path,source_path)]
    if (parent['river_id']!='futaleufu_river_chile' or parent['horizontal_crs']!='EPSG:32718'
            or source['schema']!='raftsim.futaleufu_continuous_sources.v1'
            or parent['landscape']['vertices']!=127 or parent['landscape']['height_base_m']!=0
            or parent['landscape']['height_range_m']!=2400 or parent['incomplete_source_chunks']):
        raise ValueError('Complete shared-grid Futaleufu parent required')
    pins=copy.deepcopy(parent['evidence_source']['sources_sha256'])
    source_relative=source_path.relative_to(ROOT).as_posix()
    if pins.get(source_relative)!=sha(source_path):raise ValueError('Context must use the same captured terrain source')
    pins[parent_path.relative_to(ROOT).as_posix()]=sha(parent_path)
    pins[Path(__file__).resolve().relative_to(ROOT).as_posix()]=sha(Path(__file__))
    for relative,digest in pins.items():
        if sha(ROOT/relative)!=digest:raise ValueError('Changed parent/source: '+relative)
    dsm_path=source_folder/source['dsm']['file']
    if sha(dsm_path)!=source['dsm']['sha256']:raise ValueError('Changed captured DSM')
    with np.load(dsm_path,allow_pickle=False) as z:grid=z['dsm_m'].copy()
    if grid.shape!=tuple(source['grid']['shape']) or not np.isfinite(grid).all():raise ValueError('Invalid source grid')
    origin=parent['horizontal_origin_m'];spacing=parent['landscape']['spacing_m'];span=126*spacing
    indices=supported_chunks(source['grid'],origin,span);keys={tuple(c['chunk']) for c in parent['chunks']}
    if not keys.issubset(indices) or len(keys)!=len(parent['chunks']) or not 0<len(indices)<=4096:
        raise ValueError('Source context must contain every unique original tile')
    if shutil.disk_usage(ROOT).free<RESERVE+len(indices)*2*1024**2:raise ValueError('40 GiB disk reserve unavailable')
    # Reject seams before creating output. Compare encoded vertices, not a
    # looser float tolerance that could conceal a shared-edge discontinuity.
    for c in parent['chunks']:
        for key,digest in (('heightfield','sha256'),('source_receipt','source_receipt_sha256')):
            path=parent_folder/c[key]
            if sha(path)!=c[digest]:raise ValueError('Changed original tile')
        with Image.open(parent_folder/c['heightfield']) as image:original=np.asarray(image)
        xy=lattice(c['chunk'],origin,spacing)
        heights=source_heights(xy.reshape(-1,2),grid,source['grid']['transform']).reshape(127,127)
        verify_join(tuple(c['chunk']),original,encode(heights),keys)
    output.mkdir(parents=True);chunks=copy.deepcopy(parent['chunks'])
    for c in chunks:
        for key in ('heightfield','source_receipt'):shutil.copyfile(parent_folder/c[key],output/c[key])
    for index in indices:
        if index in keys:continue
        if shutil.disk_usage(ROOT).free<RESERVE:raise ValueError('Disk reserve reached; preserve partial output, do not import')
        xy=lattice(index,origin,spacing)
        heights=source_heights(xy.reshape(-1,2),grid,source['grid']['transform']).reshape(127,127)
        i,j=index;image=f'height_{i}_{j}.png';proof=f'source_{i}_{j}.npz'
        write_png_u16(output/image,encode(heights))
        np.savez_compressed(output/proof,source_height_m=heights,height_m=heights,inferred_bed=np.zeros(heights.shape,bool))
        chunks.append(dict(chunk=[i,j],heightfield=image,sha256=sha(output/image),
                           source_receipt=proof,source_receipt_sha256=sha(output/proof),
                           origin_m=xy[0,0].tolist(),world_northwest_xy_cm=[i*span*100,-(j+1)*span*100]))
    for relative,digest in pins.items():
        if sha(ROOT/relative)!=digest:raise ValueError('Source changed during context export')
    for c in parent['chunks']:
        if sha(output/c['heightfield'])!=c['sha256'] or sha(output/c['source_receipt'])!=c['source_receipt_sha256']:
            raise ValueError('Parent tile changed during copy')
    result=copy.deepcopy(parent);result['chunks']=sorted(chunks,key=lambda c:c['chunk'])
    result['evidence_source']['sources_sha256']=pins
    result['context_extension']=dict(parent_manifest_sha256=sha(parent_path),preserved_parent_tiles=len(keys),
        added_unmodified_source_tiles=len(indices)-len(keys),native_optical_and_dsm_grid=source['grid'],
        boundary_rule='Only complete shared-lattice chunks within captured DSM pixel centres',
        parent_heightfields_and_receipts_byte_identical=True,shared_join_encoded_difference=0,
        caveat='GLO30 surface model resampled at 2 m, not a new survey or inferred bathymetry; finite outer source boundary remains')
    result['scope']='Continuous source-backed landscape context with original three-arm bed preserved; runtime water/vegetation pending'
    (output/'manifest.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    LandscapeTriangles(output).verify_unchanged()
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('parent','sources','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();r=extend(a.parent,a.sources,a.out)
    print(json.dumps(dict(chunks=len(r['chunks']),context=r['context_extension']),indent=2))
