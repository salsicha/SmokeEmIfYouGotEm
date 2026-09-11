"""Register saved hydraulic hotspots to original imagery and LiDAR returns.

Read-only evidence review. Sparse returns, water and registration uncertainty
must not be relabeled as measured bathymetry or a verified boulder outline.
"""
from pathlib import Path
import json
import sys
import hashlib

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tmp/south-fork-geospatial-deps'))
import numpy as np
import rasterio
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE=ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09'
OUT=ROOT/'docs/reconstruction-review-2026-09-07'
GEOMETRY=ROOT/'tmp/south-fork-rock-gap-candidate-20260907'


def main():
    output=OUT/'rock-pocket-source-review.json'
    if output.exists(): raise ValueError('Retain earlier evidence; choose a new report name')
    manifest=json.loads((GEOMETRY/'manifest.json').read_text())
    bed_path=ROOT/manifest['shared_geometry_path']
    if hashlib.sha256(bed_path.read_bytes()).hexdigest()!=manifest['shared_geometry_sha256']:
        raise ValueError('Source geometry identity changed')
    with rasterio.open(bed_path) as ds:
        bed=ds.read(1); transform=ds.transform
    with rasterio.open(GEOMETRY/'geometry_authority.tif') as ds: authority=ds.read(1)
    points=np.load(BASE/'troublemaker/classified_lidar_returns.npz')
    x,y,z=[points[k] for k in ('utm_easting_m','utm_northing_m','navd88_m')]
    col,row=(~transform)*(x,y); col,row=np.floor(col).astype(int),np.floor(row).astype(int)
    classes=points['classification']; dz=points['height_above_flattened_surface_m']
    accepted=np.isin(classes,[1,2,10])&(dz>.3)&(dz<8.)
    peak=json.loads((OUT/'gap-continuation-hotspots.json').read_text())['regions'][2]['largest_sampled_stage_variation_locations'][0]
    px,py=peak['east_north_utm_m']
    c,r=(~transform)*(px,py); c,r=int(np.floor(c)),int(np.floor(r))
    reviewed=[]
    for rr in range(r-3,r+4):
        for cc in range(c-3,c+4):
            selected=(row==rr)&(col==cc)
            candidates=selected&accepted
            reviewed.append({'source_row_col':[rr,cc],'authority':int(authority[rr,cc]),
                'bed_navd88_m':float(bed[rr,cc]),'return_count':int(selected.sum()),
                'accepted_return_count':int(candidates.sum()),
                'accepted_heights_navd88_m':z[candidates].tolist(),
                'all_return_classes':classes[selected].astype(int).tolist(),
                'all_heights_above_hydroflat_m':dz[selected].tolist()})
    image=plt.imread(BASE/'sources/troublemaker_naip.png')
    extent=json.loads((BASE/'sources/troublemaker_naip_export.json').read_text())['extent']
    roi=[px-12,px+12,py-12,py+12]
    selected=(x>roi[0])&(x<roi[1])&(y>roi[2])&(y<roi[3])&np.isin(classes,[1,2,10])
    fig,axes=plt.subplots(1,3,figsize=(15,5),layout='constrained')
    axes[0].imshow(image,extent=[extent['xmin'],extent['xmax'],extent['ymin'],extent['ymax']])
    axes[0].set_title('Dated NAIP; registration uncertainty ~3 m')
    bounds=rasterio.transform.array_bounds(*bed.shape,transform)
    axes[1].imshow(authority,extent=[bounds[0],bounds[2],bounds[1],bounds[3]],
        interpolation='nearest',vmin=1,vmax=4,cmap='viridis')
    axes[1].set_title('Source authority: 2 inferred bed / 3 rock')
    dots=axes[2].scatter(x[selected],y[selected],c=z[selected],s=8,cmap='terrain',vmin=225,vmax=232)
    fig.colorbar(dots,ax=axes[2],label='Return height (m NAVD88)',shrink=.65)
    axes[2].set_title('Original non-noise returns; not filtered rock')
    for ax in axes:
        ax.scatter([px],[py],marker='+',s=160,color='red')
        ax.set_xlim(roi[:2]); ax.set_ylim(roi[2:]); ax.set_aspect('equal')
        ax.ticklabel_format(useOffset=False,style='plain'); ax.tick_params(axis='x',labelrotation=30)
    fig.savefig(OUT/'rock-pocket-source-review.png',dpi=160)
    report={'scope':__doc__.strip(),'geometry_sha256':manifest['shared_geometry_sha256'],
        'authority_sha256':hashlib.sha256((GEOMETRY/'geometry_authority.tif').read_bytes()).hexdigest(),
        'point_cloud_sha256':hashlib.sha256((BASE/'troublemaker/classified_lidar_returns.npz').read_bytes()).hexdigest(),
        'hotspot':peak,'source_cell_containing_hotspot':[r,c], 'reviewed_cells':reviewed,
        'source_image_sha256':hashlib.sha256((BASE/'sources/troublemaker_naip.png').read_bytes()).hexdigest(),
        'accepted_filter':'class 1,2,10; height above hydroflattened surface >0.3 and <8 m',
        'registered_rapid_identity_verified':False,'geometry_modified':False,'production_promoted':False}
    output.write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps([p for p in reviewed if p['authority']==2],indent=2))


if __name__=='__main__': main()
