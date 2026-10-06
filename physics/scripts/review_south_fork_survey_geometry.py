"""Plot captured terrain/orthophoto registration; no invented water or rocks."""
from pathlib import Path
import sys
import json

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tmp/south-fork-geospatial-deps'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource
from PIL import Image
import rasterio
from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import transform

BASE = ROOT / 'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09'
OUT = ROOT / 'docs/reconstruction-review-2026-09-06'
TO_METRIC = Transformer.from_crs(4326, 32610, always_xy=True)


def main():
    OUT.mkdir(exist_ok=True)
    route_data = json.loads((BASE / 'corrected_route_candidate.geojson').read_text())
    route = next(f for f in route_data['features'] if f['geometry']['type'] == 'LineString')
    xy = np.array([TO_METRIC.transform(*p[:2]) for p in route['geometry']['coordinates']])
    for label in ('chili_bar', 'troublemaker'):
        meta = json.loads((BASE / f'sources/{label}_naip_export.json').read_text())
        extent = meta['extent']
        bounds = [extent['xmin'], extent['xmax'], extent['ymin'], extent['ymax']]
        origin = np.array([(bounds[0]+bounds[1])*.5, (bounds[2]+bounds[3])*.5])
        image = np.asarray(Image.open(BASE / f'sources/{label}_naip.png'))
        with rasterio.open(BASE / label / 'survey_surface_navd88_m.tif') as ds:
            dem = ds.read(1)
            dem_bounds = [ds.bounds.left, ds.bounds.right, ds.bounds.bottom, ds.bounds.top]
            cell = ds.res[0]
        with rasterio.open(BASE / label / 'unknown_submerged_bed_mask.tif') as ds:
            wet = ds.read(1) == 1
        boundaries = json.loads((BASE / label / 'survey_water_boundaries.geojson').read_text())
        fig, axes = plt.subplots(1, 2, figsize=(15, 7), layout='constrained')
        local_bounds = np.asarray(bounds) - origin[[0,0,1,1]]
        local_dem_bounds = np.asarray(dem_bounds) - origin[[0,0,1,1]]
        axes[0].imshow(image, extent=local_bounds)
        shade = LightSource(315, 45).hillshade(dem, vert_exag=1, dx=cell, dy=cell)
        axes[1].imshow(shade, cmap='gray', extent=local_dem_bounds, vmin=0, vmax=1)
        overlay = np.zeros((*wet.shape, 4), dtype=np.float32)
        overlay[wet] = [.05, .5, .95, .45]
        axes[1].imshow(overlay, extent=local_dem_bounds)
        for ax in axes:
            for feature in boundaries['features']:
                geom = transform(TO_METRIC.transform, shape(feature['geometry']))
                for poly in (geom.geoms if hasattr(geom, 'geoms') else [geom]):
                    if poly.geom_type != 'Polygon':
                        continue
                    coords = np.asarray(poly.exterior.coords)
                    ax.plot(coords[:,0]-origin[0], coords[:,1]-origin[1], color='#42eafa', lw=1)
            ax.plot(xy[:,0]-origin[0], xy[:,1]-origin[1], '--', color='#ffd84c', lw=1, label='NHD route candidate')
            ax.set_xlim(local_bounds[:2]); ax.set_ylim(local_bounds[2:])
            ax.set_aspect('equal'); ax.set_xlabel('East (m, local offset)'); ax.set_ylabel('North (m, local offset)')
        axes[0].set_title('USDA NAIP • 21 July 2022 • native 0.6 m')
        axes[1].set_title('USGS LiDAR DEM • 0.5 m working grid\nBlue = hydro-flattened water, NOT measured bed')
        fig.suptitle(label.replace('_', ' ').title() + ' — geographic registration review (not a game capture)')
        fig.savefig(OUT / f'{label}_source_registration.png', dpi=150)
        if label == 'troublemaker':
            # Focus on the real constriction, keeping the same map frame.
            for ax in axes:
                ax.set_xlim(-80, 110); ax.set_ylim(-110, 30)
            fig.savefig(OUT / 'troublemaker_crux_registration.png', dpi=180)
        plt.close(fig)


if __name__ == '__main__':
    main()
