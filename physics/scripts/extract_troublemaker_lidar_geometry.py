"""Inspect original classified returns at the real rapid, including ignored ground.

Keep water and ground returns separate; no return is treated as bathymetry.
"""
from pathlib import Path
import sys
import json
import hashlib

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tmp/south-fork-geospatial-deps'))
import numpy as np
import laspy
from pyproj import Transformer, CRS
import rasterio
from scipy.ndimage import map_coordinates
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE = ROOT / 'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09'


def main():
    records = json.loads((BASE / 'sources/point_cloud/downloads.json').read_text())
    features = json.loads((BASE / 'corrected_route_candidate.geojson').read_text())['features']
    control = next(f for f in features if f.get('id') == 'troublemaker_crux_search')
    center = np.array(control['properties']['metric_xy'])
    to_source = Transformer.from_crs(32610, 6418, always_xy=True)
    to_metric = Transformer.from_crs(6418, 32610, always_xy=True)
    bbox = to_source.transform_bounds(center[0]-180, center[1]-140, center[0]+180, center[1]+140)
    selected, sources = [], []
    for record in records:
        path = BASE / 'sources/point_cloud' / record['file']
        if hashlib.sha256(path.read_bytes()).hexdigest() != record['sha256']:
            raise ValueError('LAZ source hash mismatch')
        with laspy.open(path) as reader:
            crs = reader.header.parse_crs()
            hcrs = crs.sub_crs_list[0] if crs and crs.is_compound else crs
            if hcrs is None or hcrs.to_epsg() != 6418:
                raise ValueError(f'Unexpected point-cloud CRS: {crs}')
            # The original delivery is NAVD88 US survey feet, as specified by
            # source metadata. LAS scale/offset decoding is performed by laspy.
            for points in reader.chunk_iterator(1_000_000):
                x,y = np.asarray(points.x), np.asarray(points.y)
                good = (x>=bbox[0]) & (x<=bbox[2]) & (y>=bbox[1]) & (y<=bbox[3]) & (np.asarray(points.withheld)==0)
                if not good.any():
                    continue
                e,n = to_metric.transform(x[good], y[good])
                z = np.asarray(points.z)[good]*(1200/3937)
                selected.append(np.column_stack([e,n,z,np.asarray(points.classification)[good]]))
        sources.append(record)
        print('Read', record['tile_id'], flush=True)
    data = np.concatenate(selected)
    crop = (abs(data[:,0]-center[0])<=180) & (abs(data[:,1]-center[1])<=140)
    data = data[crop]
    with rasterio.open(BASE / 'troublemaker/survey_surface_navd88_m.tif') as ds:
        xy = (~ds.transform)*(data[:,0],data[:,1])
        dem = map_coordinates(ds.read(1), [xy[1]-.5,xy[0]-.5], order=1, mode='constant', cval=np.nan)
    with rasterio.open(BASE / 'troublemaker/unknown_submerged_bed_mask.tif') as ds:
        water = map_coordinates(ds.read(1), [xy[1]-.5,xy[0]-.5], order=0, mode='constant', cval=255)==1
    # Eldorado survey metadata: 2 = bare earth, 20 = ignored ground (not 10).
    # Eligibility is an exposed-ground hypothesis, not a verified rock label.
    ground = np.isin(data[:,3], [2,20])
    candidate = ground & water & (data[:,2] > dem+.3) & (data[:,2] < dem+12)
    out = BASE / 'troublemaker'
    np.savez_compressed(out / 'classified_lidar_returns.npz',
        utm_easting_m=data[:,0], utm_northing_m=data[:,1], navd88_m=data[:,2],
        classification=data[:,3].astype(np.uint8), within_survey_water=water,
        height_above_flattened_surface_m=data[:,2]-dem,
        exposed_ground_candidate=candidate)
    classes, counts = np.unique(data[:,3].astype(int), return_counts=True)
    report = {'status': 'classified_return_review_not_promoted', 'source_tile_count':len(records),
        'return_count':len(data), 'class_counts':dict(zip(map(str,classes),map(int,counts))),
        'ground_returns':int(ground.sum()), 'ground_inside_water_polygon':int((ground&water).sum()),
        'exposed_ground_candidates':int(candidate.sum()),
        'candidate_rule':'ground/ignored-ground classification inside hydro polygon, 0.3 to 12 m above flattened surface',
        'candidate_is_verified_boulder':False, 'is_bathymetry':False, 'production_promoted':False,
        'sources':sources}
    (out / 'classified_lidar_review.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    fig, ax = plt.subplots(figsize=(11,8), layout='constrained')
    keep = ground & np.isfinite(dem)
    scatter = ax.scatter(data[keep,0]-center[0],data[keep,1]-center[1],c=(data[keep,2]-dem[keep]),
                         s=.8,vmin=-1,vmax=4,cmap='terrain')
    ax.set_aspect('equal'); ax.set_xlabel('East of crux candidate (m)'); ax.set_ylabel('North (m)')
    ax.set_title('Original classified LiDAR ground returns at Troublemaker\nHeight relative to hydro-flattened DEM; gaps are missing returns, not flat bed')
    fig.colorbar(scatter,ax=ax,label='Height difference (m)')
    fig.savefig(ROOT / 'docs/reconstruction-review-2026-09-06/troublemaker_original_lidar.png',dpi=160)
    plt.close(fig)
    fig, axes = plt.subplots(1,2,figsize=(15,7),layout='constrained')
    positive = water & np.isin(data[:,3],[1,2,9,10]) & (data[:,2]>dem+.3) & (data[:,2]<dem+8)
    for ax, selected_mask, title in zip(axes,[water & np.isin(data[:,3],[1,2,9,10]),positive],
            ['All non-noise water-polygon returns','Positive-height candidates, NOT verified rocks']):
        draw = selected_mask & (abs(data[:,0]-center[0])<110) & (abs(data[:,1]-center[1])<100)
        artist=ax.scatter(data[draw,0]-center[0],data[draw,1]-center[1],c=data[draw,2]-dem[draw],
                         s=3,vmin=0,vmax=4,cmap='terrain')
        ax.set_aspect('equal'); ax.set_xlim(-110,110); ax.set_ylim(-100,100)
        ax.set_title(title); ax.set_xlabel('East of crux control (m)'); ax.set_ylabel('North (m)')
    fig.colorbar(artist,ax=axes,label='Height above hydro-flattened DEM (m)')
    fig.savefig(ROOT/'docs/reconstruction-review-2026-09-06/troublemaker_unclassified_water_returns.png',dpi=160)
    plt.close(fig)
    print(json.dumps(report,indent=2),flush=True)


if __name__ == '__main__':
    main()
