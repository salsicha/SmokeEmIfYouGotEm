"""Build a registered terrain/collision candidate, preserving uncertainty.

Surveyed dry ground is immutable. Exposed rock is reconstructed only where
original returns support it inside reviewed search regions. Underwater bed is
explicitly estimated, never represented as captured bathymetry.
"""
from pathlib import Path
import sys
import json
import hashlib

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tmp/south-fork-geospatial-deps'))
import numpy as np
import rasterio
from rasterio.features import rasterize
from scipy.ndimage import distance_transform_edt, label, median_filter
from shapely.geometry import Polygon, mapping
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource

BASE=ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09'
OUT=BASE/'troublemaker/geometry_candidate'


def inferred_depth(wet, cell):
    """Uncalibrated shallow-bank / deeper-channel prior, no dry-land edits."""
    clearance=distance_transform_edt(wet)*cell
    return np.where(wet,2.4*(1-np.exp(-clearance/4.)),0).astype(np.float32)


def main():
    OUT.mkdir(exist_ok=True)
    control=next(f for f in json.loads((BASE/'corrected_route_candidate.geojson').read_text())['features']
                 if f.get('id')=='troublemaker_crux_search')
    center=np.array(control['properties']['metric_xy'])
    with rasterio.open(BASE/'troublemaker/survey_surface_navd88_m.tif') as ds:
        window=rasterio.windows.from_bounds(center[0]-180,center[1]-140,center[0]+180,center[1]+140,ds.transform).round_offsets().round_lengths()
        surface=ds.read(1,window=window)
        affine=ds.window_transform(window)
        profile=ds.profile.copy(); profile.update(width=surface.shape[1],height=surface.shape[0],transform=affine)
    with rasterio.open(BASE/'troublemaker/unknown_submerged_bed_mask.tif') as ds:
        wet=ds.read(1,window=window)==1
    depth=inferred_depth(wet,.5)
    bed=surface-depth
    data=np.load(BASE/'troublemaker/classified_lidar_returns.npz')
    reviews=json.loads((BASE/'troublemaker/rock_review_regions.json').read_text())
    regions=[(mapping(Polygon(np.asarray(r['polygon'])+center)),i+1) for i,r in enumerate(reviews['regions'])]
    region_mask=rasterize(regions,out_shape=bed.shape,transform=affine,dtype='uint8')
    col,row=(~affine)*(data['utm_easting_m'],data['utm_northing_m'])
    col,row=np.floor(col).astype(int),np.floor(row).astype(int)
    inside=(row>=0)&(col>=0)&(row<bed.shape[0])&(col<bed.shape[1])
    good=inside & np.isin(data['classification'],[1,2,20]) & (data['height_above_flattened_surface_m']>.3)
    good &= data['height_above_flattened_surface_m']<8
    indices=np.where(good)[0]
    indices=indices[(region_mask[row[indices],col[indices]]>0)&wet[row[indices],col[indices]]]
    minimum=np.full(bed.shape,np.inf,dtype=np.float32)
    counts=np.zeros(bed.shape,dtype=np.int32)
    np.minimum.at(minimum,(row[indices],col[indices]),data['navd88_m'][indices])
    np.add.at(counts,(row[indices],col[indices]),1)
    supported=(counts>=2)&np.isfinite(minimum)
    # Remove isolated returns; never span multi-metre missing-return holes.
    groups,total=label(supported)
    sizes=np.bincount(groups.ravel())
    supported &= sizes[groups]>=8
    rock_height=np.where(supported,minimum,np.nan)
    bed[supported]=np.maximum(bed[supported],rock_height[supported])
    yy,xx=np.indices(bed.shape)
    east,north=affine*(xx+.5,yy+.5)
    # The aerial whitewater constriction establishes a location, not measured
    # submerged elevation. Keep this hydraulic-control hypothesis explicit.
    dx,dy=east-center[0]+9.,north-center[1]-1.
    along=-.93*dx+.36756*dy
    across=-.36756*dx-.93*dy
    shelf=np.exp(-((along+2.)/2.)**4)*np.exp(-(across/7.)**6)
    plunge=np.exp(-((along-5.)/4.)**2)*np.exp(-(across/7.)**4)
    editable=wet & ~supported
    hypothesized=bed + shelf*np.maximum(depth-.7,0) - .7*plunge
    bed[editable]=hypothesized[editable]
    if not np.array_equal(bed[~wet],surface[~wet]):
        raise ValueError('Captured dry ground changed')
    # 1: captured DEM ground, 2: explicitly estimated bed, 3: original-return
    # exposed rock inside interpreted review regions. No missing data is zero.
    authority=np.where(wet,2,1).astype(np.uint8); authority[supported]=3
    bed_path=OUT/'shared_render_collision_hydraulic_bed_navd88_m.tif'
    with rasterio.open(bed_path,'w',**profile) as dst:
        dst.write(bed,1); dst.set_band_unit(1,'metre')
        dst.update_tags(vertical_datum='NAVD88',bathymetry='INFERRED_NOT_SURVEYED')
    with rasterio.open(OUT/'geometry_authority.tif','w',**dict(profile,dtype='uint8',nodata=0)) as dst:
        dst.write(authority,1)
    # Packed source for Blender/engine consumers without GIS dependencies.
    datum=220.
    np.savez_compressed(OUT/'engine_mesh_source.npz',east_m=east-center[0],north_m=north-center[1],
        z_m=bed-datum,source_surface_m=surface-datum,authority=authority)
    report={'schema':'raftsim.troublemaker.captured_geometry_candidate.v1',
        'status':'geometry_candidate_requires_hydraulic_and_engine_validation',
        'origin_utm_m':center.tolist(),'vertical_origin_navd88_m':datum,
        'cell_m':.5,'shape_rows_cols':list(bed.shape),
        'shared_geometry_path':bed_path.relative_to(ROOT).as_posix(),
        'shared_geometry_sha256':hashlib.sha256(bed_path.read_bytes()).hexdigest(),
        'measured_dry_ground_max_change_m':float(np.max(np.abs(bed[~wet]-surface[~wet]))),
        'exposed_rock_supported_cells':int(supported.sum()),
        'exposed_rock_supported_area_m2':float(supported.sum()*.25),
        'rock_outline_authority':'Original non-noise LiDAR returns inside interpreted photo-reviewed regions',
        'submerged_bed_authority':'Uncalibrated depth prior; not surveyed bathymetry',
        'inferred_hole_control':{'source':'User footage description and dated NAIP constriction',
            'center_local_east_north_m':[-9.,1.], 'shelf_depth_prior_m':.7,
            'plunge_extra_depth_prior_m':.7,'status':'Hypothesis awaiting flow/footage calibration'},
        'inferred_max_depth_m':float(depth.max()),'random_rocks_added':0,
        'source_discharge_known':False,'hydraulic_validation_passed':False,
        'game_integrated':False,'production_promoted':False}
    (OUT/'manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    fig,axes=plt.subplots(1,2,figsize=(15,6),layout='constrained')
    extent=[float(east.min()),float(east.max()),float(north.min()),float(north.max())]-center[[0,0,1,1]]
    shade=LightSource(315,40).hillshade(bed,dx=.5,dy=.5)
    axes[0].imshow(shade,extent=extent,cmap='gray')
    axes[1].imshow(authority,extent=extent,cmap='viridis',vmin=1,vmax=3)
    for ax in axes:
        ax.set_xlim(-115,115); ax.set_ylim(-100,100); ax.set_aspect('equal')
        ax.set_xlabel('East of crux control (m)'); ax.set_ylabel('North (m)')
    axes[0].set_title('Shared geometry candidate: no generic boulder meshes')
    axes[1].set_title('Dark: captured bank / Green: estimated bed / Yellow: recovered rock')
    fig.savefig(ROOT/'docs/reconstruction-review-2026-09-06/troublemaker_recovered_geometry.png',dpi=160)
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':
    main()
