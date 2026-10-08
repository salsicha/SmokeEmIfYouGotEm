"""Full connected Futaleufu terrain candidate on the engine's shared lattice.

Render, collision and future fluid cooks must use these same decoded triangles.
This exports construction geometry, not a playable/flow/performance acceptance.
"""
import argparse
import json
from pathlib import Path
import shutil

import numpy as np
import shapely

from build_futaleufu_corridor_sources import ROOT, sha
from futaleufu_corridor_bed import FutaleufuBed
from chilko_triangle_ownership import preserve_triangle_support, support_policy
from export_colorado_continuous_terrain import VERTICES, HEIGHT_RANGE, LandscapeTriangles, write_png_u16

HEIGHT_BASE = 0.
RESERVE = 40*1024**3


def encode(height):
    height = np.asarray(height, float)
    if not np.isfinite(height).all() or np.any(height < HEIGHT_BASE) or np.any(height > HEIGHT_RANGE):
        raise ValueError('Terrain outside explicit EGM2008 encoding; no clamp')
    return np.rint(height/HEIGHT_RANGE*65535).astype('uint16')


def chunk_indices(lines, origin, buffer_m, spacing_m):
    support_policy(spacing_m)
    origin = np.asarray(origin, float)
    if origin.shape != (2,) or not np.isfinite(origin).all() or not 100 <= buffer_m <= 200:
        raise ValueError('Finite geographic origin and 100-200 m source-supported terrain corridor required')
    footprint = shapely.union_all(lines).buffer(buffer_m)
    span = (VERTICES-1)*spacing_m
    low = np.floor((np.array(footprint.bounds[:2])-origin)/span).astype(int)
    high = np.floor((np.array(footprint.bounds[2:])-origin)/span).astype(int)
    return [(i,j) for i in range(low[0],high[0]+1) for j in range(low[1],high[1]+1)
            if footprint.intersects(shapely.box(*(origin+[i*span,j*span]),
                                                *(origin+[(i+1)*span,(j+1)*span])))]


class TerrainBed:
    def __init__(self, bed):
        self.bed = bed

    def sample(self, xy):
        xy = np.asarray(xy, float)
        if xy.ndim < 2 or xy.shape[-1] != 2:
            raise ValueError('Geographic point lattice required')
        return {k:v.reshape(xy.shape[:-1]) for k,v in self.bed.sample(xy.reshape(-1,2)).items()}


def export(sources, profile, network, output, *, depth_m, spacing_m=2., buffer_m=200.):
    output = Path(output).resolve(); output.relative_to(ROOT)
    if output.exists():
        raise ValueError('Fresh terrain candidate required')
    bed = FutaleufuBed(sources, profile, network, depth_m=depth_m)
    # The established full-route UE frame; not a per-chunk recentering.
    origin = np.array([739986.,5195961.5]); datum = 150.
    indices = chunk_indices(bed.lines, origin, buffer_m, spacing_m)
    span = (VERTICES-1)*spacing_m
    model = TerrainBed(bed)
    if not indices or len(indices) > 4096:
        raise ValueError('Unexpected full-corridor extent')
    if shutil.disk_usage(ROOT).free < RESERVE+len(indices)*2*1024**2:
        raise ValueError('Terrain export would violate the 40 GiB reserve')
    # Preflight all outer corners plus triangle-support margin against source
    # coverage before any files are created. No missing tiles silently dropped.
    t = bed.transform; rows, cols = bed.grid.shape
    lower = np.array([t[2]+5,t[5]-(rows-.5)*10])
    upper = np.array([t[2]+(cols-.5)*10,t[5]-5])
    for i,j in indices:
        if np.any(origin+[i*span,j*span]-spacing_m < lower) or np.any(origin+[(i+1)*span,(j+1)*span]+spacing_m > upper):
            raise ValueError(f'Entire terrain chunk and support must have source coverage: {(i,j)}')
    pins = bed.receipt['sources_sha256']
    for name in ('export_futaleufu_corridor_terrain.py','chilko_triangle_ownership.py',
                 'export_colorado_continuous_terrain.py'):
        p = Path(__file__).with_name(name).resolve(); pins[p.relative_to(ROOT).as_posix()] = sha(p)
    output.mkdir(parents=True)
    chunks=[]; inferred=0; vetoes=0; maximum_cut=0.; maximum_error=0.
    for number,(i,j) in enumerate(indices):
        if shutil.disk_usage(ROOT).free < RESERVE:
            raise ValueError('Disk reserve reached; retain partial candidate, do not import')
        west,south = origin+np.array([i,j])*span
        east,north = np.meshgrid(west+np.arange(VERTICES)*spacing_m,south+span-np.arange(VERTICES)*spacing_m)
        xy=np.stack((east,north),axis=-1)
        r=preserve_triangle_support(model,xy,model.sample(xy),spacing_m=spacing_m)
        encoded=encode(r['height_m']); decoded=encoded.astype(float)*HEIGHT_RANGE/65535
        maximum_error=max(maximum_error,float(abs(decoded-r['height_m']).max()))
        maximum_cut=max(maximum_cut,float((r['source_height_m']-r['height_m']).max()))
        inferred+=int(r['inferred_bed'].sum());vetoes+=int(r['inference_support_veto'].sum())
        name=f'height_{i}_{j}.png';proof=f'source_{i}_{j}.npz'
        write_png_u16(output/name,encoded);np.savez_compressed(output/proof,**r)
        chunks.append(dict(chunk=[int(i),int(j)],heightfield=name,sha256=sha(output/name),
            source_receipt=proof,source_receipt_sha256=sha(output/proof),origin_m=[float(west),float(south+span)],
            world_northwest_xy_cm=[i*span*100,-(j+1)*span*100]))
        print(f'Futaleufu shared terrain chunks {number+1}/{len(indices)}',flush=True)
    for relative,digest in pins.items():
        if sha(ROOT/relative)!=digest:raise ValueError('Source/code changed during export')
    manifest=dict(schema='raftsim.continuous_landscape.v1',river_id='futaleufu_river_chile',
        horizontal_crs='EPSG:32718',vertical_reference='EGM2008',world_y_sign=-1,
        horizontal_origin_m=origin.tolist(),vertical_datum_m=datum,evidence_source=bed.receipt,
        landscape=dict(vertices=VERTICES,spacing_m=spacing_m,span_m=span,
            subsections_per_component=2,quads_per_subsection=63,height_base_m=HEIGHT_BASE,
            height_range_m=HEIGHT_RANGE,actor_z_cm=(HEIGHT_RANGE*32768/65535-datum)*100,
            scale_xyz=[spacing_m*100,spacing_m*100,HEIGHT_RANGE*100/512*65536/65535]),
        geographic_scope=dict(branch_lengths_m={n:float(l.length) for n,l in zip(bed.arrays,bed.lines)},
                              buffer_m=buffer_m,all_three_arms=True),
        inference_support_policy=support_policy(spacing_m),chunks=chunks,incomplete_source_chunks=[],
        shared_edge_max_encoded_difference=0,inferred_vertices_including_shared_edges=inferred,
        support_vetoes_including_shared_edges=vetoes,maximum_inferred_cut_m=maximum_cut,
        maximum_height_quantization_error_m=maximum_error,
        scope='Full connected three-arm initial terrain/bed; not accepted hydraulics or playable rapid geometry',
        vegetation_complete=False,engine_validated=False,full_river_complete=False)
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    LandscapeTriangles(output).verify_unchanged()
    print(json.dumps(dict(chunks=len(chunks),inferred_vertices=inferred,maximum_cut_m=maximum_cut,
                         maximum_encoding_error_m=maximum_error)),flush=True)
    return manifest


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('sources','profile','network','out'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--depth-m',type=float,required=True)
    p.add_argument('--spacing-m',type=float,choices=(1.,2.),default=2.)
    a=p.parse_args();export(a.sources,a.profile,a.network,a.out,depth_m=a.depth_m,spacing_m=a.spacing_m)
