"""Compare actual source-tile bed values near a full-river handoff.

Uses common geographic cell centres, not equal local station indices. This
tests construction geometry only, not independently cooked flow or engine seams.
"""
import argparse
import json
from pathlib import Path

import numpy as np

from build_colorado_catalog_evidence import sha


def overlap_views(a,b):
    for g in (a,b):
        if not np.array_equal(g['cell_m'],[1,1]):
            raise ValueError('Expected shared one-metre source lattice')
    def bounds(g):
        x,y=g['corner_east_north_m'];h,w=g['bed_ellipsoid_m'].shape
        return x,y-h,x+w,y
    A,B=bounds(a),bounds(b)
    x0,y0,x1,y1=max(A[0],B[0]),max(A[1],B[1]),min(A[2],B[2]),min(A[3],B[3])
    if x0>=x1 or y0>=y1:
        raise ValueError('Tiles have no source overlap')
    views=[]
    for g in (a,b):
        x,y=g['corner_east_north_m']
        offsets=np.array([y-y1,y-y0,x0-x,x1-x])
        if not np.array_equal(offsets,np.rint(offsets)):
            raise ValueError('Tile grids do not share cell centres')
        r0,r1,c0,c1=offsets.astype(int)
        views.append({k:g[k][r0:r1,c0:c1] for k in
            ('bed_ellipsoid_m','reference_surface_ellipsoid_m','classified_water_mask',
             'station_m','measured_pool_bed_mask')})
    return views


def compare(a,b,origin_a,origin_b,seam,half_width=100.):
    if not all(np.isfinite(x) for x in (origin_a,origin_b,seam,half_width)) or half_width<=0:
        raise ValueError('Invalid seam interval')
    A,B=overlap_views(a,b)
    # Both charts must place the cell within the seam neighbourhood. Endpoint
    # projection/clamping elsewhere in a rectangular crop is not seam evidence.
    near=(abs(A['station_m']+origin_a-seam)<=half_width)&(abs(B['station_m']+origin_b-seam)<=half_width)
    wet=near&A['classified_water_mask']&B['classified_water_mask']
    if not wet.any():raise ValueError('No shared wet cells near the handoff')
    def difference(key):
        d=abs(A[key][wet]-B[key][wet])
        if not np.isfinite(d).all():raise ValueError('Nonfinite seam geometry')
        return dict(p95_m=float(np.percentile(d,95)),maximum_m=float(d.max()))
    return dict(shared_wet_cells=int(wet.sum()),
        shoreline_disagreement_cells=int((near&(A['classified_water_mask']!=B['classified_water_mask'])).sum()),
        bed_difference=difference('bed_ellipsoid_m'),
        reference_surface_difference=difference('reference_surface_ellipsoid_m'),
        measured_bed_cells_in_either_tile=int((wet&(A['measured_pool_bed_mask']|B['measured_pool_bed_mask'])).sum()))


def screen(stats):
    """A matching bed alone cannot hide a discontinuous water reference."""
    differences=[stats[key]['maximum_m'] for key in
                 ('bed_difference','reference_surface_difference')]
    return bool(stats['shared_wet_cells']>0 and
                stats['shoreline_disagreement_cells']==0 and
                all(np.isfinite(value) and 0<=value<=.1 for value in differences))


def review(first,second,origin_a,origin_b,seam,out):
    arrays=[];sources=[]
    for path in (first,second):
        manifest=json.loads((path/'manifest.json').read_text())
        digest=sha(path/'evidence_grid.npz')
        if digest!=manifest['evidence_grid_sha256']:raise ValueError('Source grid changed')
        arrays.append(dict(np.load(path/'evidence_grid.npz',allow_pickle=False)))
        sources.append(dict(directory=str(path),manifest_sha256=sha(path/'manifest.json'),grid_sha256=digest))
    stats=compare(*arrays,origin_a,origin_b,seam)
    report=dict(schema='raftsim.colorado_continuous_bed_seam.v1',sources=sources,
        source_global_origins_m=[origin_a,origin_b],seam_global_station_m=seam,
        half_width_m=100.,statistics=stats,
        bed_screen_passed=screen(stats),
        screen_policy='Both wet-bed and reference-surface maximum differences <=0.1 m; no shoreline disagreement',
        scope='Shared one-metre construction bed near handoff; not rendered Landscape or cooked-flow continuity',
        engine_seam_validated=False)
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('x') as stream:json.dump(report,stream,indent=2,allow_nan=False)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--first',type=Path,required=True);p.add_argument('--second',type=Path,required=True)
    p.add_argument('--origin-first',type=float,required=True);p.add_argument('--origin-second',type=float,required=True)
    p.add_argument('--seam',type=float,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();print(json.dumps(review(a.first,a.second,a.origin_first,a.origin_second,a.seam,a.out),indent=2))
