"""Encode a bounded Chilko evidence window on the native continuous terrain lattice.

This does not assign rapid names, extrapolate missing terrain, or certify a full
river. The evidence retains measured dry ground and explicitly inferred bed.
Water inputs must subsequently sample these triangles, not resample the DEM.
"""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.ndimage import map_coordinates

from export_colorado_continuous_terrain import (
    VERTICES, SPACING, SPAN, HEIGHT_BASE, HEIGHT_RANGE, LandscapeTriangles,
    encode_height, sha, write_png_u16)


def export(evidence, out, origin, datum):
    evidence=Path(evidence).resolve();out=Path(out).resolve()
    if out.exists():raise ValueError('Fresh terrain export required')
    origin=np.asarray(origin,dtype=float)
    if origin.shape!=(2,) or not np.isfinite(origin).all() or not np.isfinite(datum):
        raise ValueError('Invalid geographic frame')
    manifest_path=evidence/'manifest.json';grid_path=evidence/'evidence_grid.npz'
    m=json.loads(manifest_path.read_text())
    if (m.get('schema')!='raftsim.chilko.lava_canyon_evidence_grid.v1' or
            m.get('crs')!='EPSG:3157 NAD83(CSRS) / UTM zone 10N' or
            m.get('vertical')!='CGVD2013 orthometric metres (LidarBC)' or
            m['grid'].get('cell_m')!=1):
        raise ValueError('Unsupported Chilko evidence frame')
    g=m['grid'];x0,y1,nx,ny=(g[k] for k in ('x0','y_top','nx','ny'))
    if type(nx) is not int or type(ny) is not int or min(nx,ny)<2:
        raise ValueError('Invalid evidence dimensions')
    with np.load(grid_path,allow_pickle=False) as arrays:
        bed=arrays['bed'].astype(float);classes=arrays['class_code']
    if (bed.shape!=(ny,nx) or classes.shape!=bed.shape or not np.isfinite([x0,y1]).all() or
            not np.isfinite(bed).all() or not np.isin(classes,[0,2,4]).all()):
        raise ValueError('Missing or invalid source evidence')
    receipt=dict(manifest=str(manifest_path),manifest_sha256=sha(manifest_path),
                 grid=str(grid_path),grid_sha256=sha(grid_path))
    # Use only the cell-centre interpolation domain. Even the outer half cell
    # is not clamped, and partially covered chunks are omitted explicitly.
    lo=np.floor((np.array([x0+.5,y1-ny+.5])-origin)/SPAN).astype(int)
    hi=np.floor((np.array([x0+nx-.5,y1-.5])-origin)/SPAN).astype(int)
    prepared=[];missing=[]
    for i in range(lo[0],hi[0]+1):
        for j in range(lo[1],hi[1]+1):
            west,south=origin+np.array([i,j])*SPAN
            east,north=np.meshgrid(west+np.arange(VERTICES)*SPACING,
                                  south+SPAN-np.arange(VERTICES)*SPACING)
            rows=y1-north-.5;cols=east-x0-.5
            inside=(rows>=0)&(rows<=ny-1)&(cols>=0)&(cols<=nx-1)
            if not inside.all():
                missing.append(dict(chunk=[int(i),int(j)],missing_vertices=int((~inside).sum())))
                continue
            height=map_coordinates(bed,[rows,cols],order=1,mode='constant',cval=np.nan,prefilter=False)
            prepared.append((int(i),int(j),float(west),float(south+SPAN),encode_height(height)))
    if not prepared:raise ValueError('No completely source-backed terrain chunks')
    out.mkdir(parents=True);chunks=[]
    for i,j,west,north,encoded in prepared:
        name=f'height_{i}_{j}.png';write_png_u16(out/name,encoded)
        chunks.append(dict(chunk=[i,j],heightfield=name,sha256=sha(out/name),
            origin_m=[west,north],world_northwest_xy_cm=[i*SPAN*100,-(j+1)*SPAN*100]))
    result=dict(schema='raftsim.continuous_landscape.v1',river_id='chilko_river_bc',
        horizontal_crs='EPSG:3157',vertical_reference='CGVD2013 (EPSG:6647)',world_y_sign=-1,
        horizontal_origin_m=origin.tolist(),vertical_datum_m=float(datum),evidence_source=receipt,
        geographic_scope=m.get('geographic_scope',{}),
        landscape=dict(vertices=VERTICES,spacing_m=SPACING,span_m=SPAN,
            subsections_per_component=2,quads_per_subsection=63,height_base_m=HEIGHT_BASE,
            height_range_m=HEIGHT_RANGE,actor_z_cm=(HEIGHT_BASE+HEIGHT_RANGE*32768/65535-datum)*100,
            scale_xyz=[SPACING*100,SPACING*100,HEIGHT_RANGE*100/512*65536/65535]),
        shared_edge_max_encoded_difference=0,chunks=chunks,incomplete_source_chunks=missing,
        scope='Bounded canonical Chilko terrain; dry DEM measured, submerged bed/boulders inferred; no rapid bounds assigned',
        vegetation_complete=False,engine_validated=False,full_river_complete=False)
    (out/'manifest.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    # Re-read hashes, common lattice and every shared edge using the same
    # triangle reader that supplies hydraulic inputs.
    LandscapeTriangles(out)
    if sha(manifest_path)!=receipt['manifest_sha256'] or sha(grid_path)!=receipt['grid_sha256']:
        raise ValueError('Evidence changed during terrain export; candidate must not be used')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--evidence',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--origin',type=float,nargs=2,required=True)
    p.add_argument('--vertical-datum-m',type=float,required=True)
    a=p.parse_args();r=export(a.evidence,a.out,a.origin,a.vertical_datum_m)
    print(json.dumps(dict(chunks=len(r['chunks']),incomplete_chunks=len(r['incomplete_source_chunks']),
                         shared_edge_max_encoded_difference=r['shared_edge_max_encoded_difference'])))
