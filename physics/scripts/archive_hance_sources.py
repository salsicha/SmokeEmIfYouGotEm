"""Archive the downloaded Hance Rapid sources with provenance (numpy only).

Inputs (tmp/hance-sources-20260926, downloaded 2026-09-26 with the user's
permission): the USGS/GCMRC April-May 2014 channel-mapping release (river miles
61-88), the 2021 corridor DEM zone 5, and two ImageServer exports of the 2021
corridor imagery. All are U.S. public domain / CC0.

Output: physics/data/real_world/colorado_river_grand_canyon_rowing/hance_sources_2026_09/
  bathymetry_2014/  original 7z archives + FGDC metadata (unchanged bytes)
  dem_2021/         1 m crop of DEME_Zone5_2021.tif over the Hance window (npz),
                    zeros outside the corridor kept as NaN
  imagery_2021/     the two exported GeoTIFFs and their export responses
  manifest.json     sources, DOIs, CRS/datums, epochs, flows, hashes
"""
import hashlib
import json
import shutil
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'physics/scripts'))
from tiff_numpy import read_geotiff  # noqa: E402

SRC = ROOT / 'tmp/hance-sources-20260926'
OUT = ROOT / 'physics/data/real_world/colorado_river_grand_canyon_rowing/hance_sources_2026_09'
WINDOW = dict(xmin=211300.0, ymin=559088.0, xmax=213800.0, ymax=560300.0)


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 22), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    assert not OUT.exists(), 'Fresh archive folder required'
    (OUT / 'bathymetry_2014').mkdir(parents=True)
    (OUT / 'dem_2021').mkdir()
    (OUT / 'imagery_2021').mkdir()
    files = {}
    for name in ('dem.7z', 'bed_sediment.7z', 'fiducial.7z', 'hillshade.7z', 'metadata.xml'):
        dst = OUT / 'bathymetry_2014' / name
        shutil.copyfile(SRC / 'bathy_2014' / name, dst)
        files[dst.relative_to(ROOT).as_posix()] = sha(dst)
    zone = SRC / 'dem2021/DEME_Zone5_2021.tif'
    a, g, _ = read_geotiff(zone)
    x0, y0 = g['corner_utm_m']
    c0 = int(round(WINDOW['xmin'] - x0)); c1 = int(round(WINDOW['xmax'] - x0))
    r0 = int(round(y0 - WINDOW['ymax'])); r1 = int(round(y0 - WINDOW['ymin']))
    crop = a[r0:r1, c0:c1].astype(np.float32)
    crop[(crop <= 0) | (crop > 5000)] = np.nan
    dem_path = OUT / 'dem_2021/dem2021_hance_1m.npz'
    np.savez_compressed(dem_path, elevation_ellipsoid_m=crop)
    files[dem_path.relative_to(ROOT).as_posix()] = sha(dem_path)
    shutil.copyfile(SRC / 'dem2021_metadata.xml', OUT / 'dem_2021/DEME_Zone1-Zone15_2021_Metadata.xml')
    files[(OUT / 'dem_2021/DEME_Zone1-Zone15_2021_Metadata.xml').relative_to(ROOT).as_posix()] = sha(OUT / 'dem_2021/DEME_Zone1-Zone15_2021_Metadata.xml')
    for name in ('hance_broad_0p5m', 'hance_rapid_0p2m'):
        for ext in ('.tif', '.json'):
            dst = OUT / 'imagery_2021' / (name + ext)
            shutil.copyfile(SRC / 'img2021' / (name + ext), dst)
            files[dst.relative_to(ROOT).as_posix()] = sha(dst)
    manifest = dict(
        schema='raftsim.colorado.hance_sources.v1',
        retrieved_on='2026-09-26',
        retrieval_permission='user approved downloading the Hance data on 2026-09-26',
        rights='U.S. public domain / CC0 (USGS Southwest Biological Science Center, Grand Canyon Monitoring and Research Center); imagery acquired by Fugro under contract',
        horizontal_crs='NAD83(2011) / Arizona Central (ftUS not used; metres), EPSG:6404',
        vertical_datum='NAD83(2011) ellipsoid heights (all three sources; not NAVD88)',
        window_state_plane_m=WINDOW,
        sources=dict(
            bathymetry_2014=dict(
                title='Channel Mapping of the Colorado River in Grand Canyon National Park, Arizona - April 2014, river miles 61 to 88 - Data',
                doi='https://doi.org/10.5066/P99SSSU6', sciencebase_item='5f45276582ce4c3d122516ea',
                acquired='2014-05-03 to 2014-05-16', method='multibeam + singlebeam sonar, total-station banks, TIN to 1 m raster',
                coverage_note='The rapid itself (about 900 m at Hance) has no sonar coverage; pools above and below are measured.'),
            dem_2021=dict(
                title='Digital elevation model (DEM) data for the Colorado River corridor ... (2021)',
                doi='https://doi.org/10.5066/P93Y4FMJ', sciencebase_item='62ab6770d34e74f0d80eb3af',
                source_zip_sha256=(SRC / 'dem2021_zones.zip.sha256').read_text().strip(),
                source_member='DEME_Zone1-Zone15_2021/DEME_Zone5_2021.tif', source_member_sha256=sha(zone),
                acquired='2021-05-29 to 2021-06-04', flow='steady ~8,000 cfs release from Glen Canyon Dam',
                method='stereo photogrammetric DSM (Leica ADS100), above-ground features filtered',
                crop_rows_cols=[r0, r1, c0, c1], note='values outside the corridor are 0 in the source and NaN here'),
            imagery_2021=dict(
                title='Aerial imagery data of the Colorado River Corridor, Arizona - 2021 (four band, 20 cm)',
                service='https://grandcanyon.usgs.gov/server/rest/services/Imagery/Imagery_ColoradoRiver_2021/ImageServer',
                acquired='2021-05-29 to 2021-06-04 (same flights as the DEM)', bands='1 red, 2 green, 3 blue, 4 near infrared (U16)',
                exports={'hance_broad_0p5m': dict(bbox=[211300, 559088, 213800, 560300], size=[5000, 2424]),
                         'hance_rapid_0p2m': dict(bbox=[212250, 559350, 213150, 559850], size=[4500, 2500])},
                substitution_note='Used instead of the 2013 mosaic (3.4-8.3 GB zone archives): same provider and resolution, and it matches the 2021 DEM epoch and flow.')),
        files=files,
        measured=dict(bed='2014 sonar/total station outside the rapid', surface_and_banks='2021 photogrammetry', imagery='2021'),
        not_measured='bed inside the rapid (sonar gap); must be inferred and labelled')
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(dict(files=len(files), crop_shape=list(crop.shape), crop_valid=float(np.isfinite(crop).mean())), indent=1))


if __name__ == '__main__':
    main()
