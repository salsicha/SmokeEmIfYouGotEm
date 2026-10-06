"""Acquire a bounded four-band NAIP window for source interpretation, not terrain.

The named raster is locked and every window corner must lie in its catalog
footprint. Preserve provider responses and raw bytes. No point classification,
source XYZ, cooked flow, image colours or playable assets are changed.
"""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
SERVICE = 'https://imagery.nationalmap.gov/arcgis/rest/services/USGSNAIPImagery/ImageServer'
RASTER = 'm_3812009_se_10_060_20220721'
ORIGIN = (683805.1336302214, 4296673.447587562)
BBOX = (ORIGIN[0]-30, ORIGIN[1]-4, ORIGIN[0]+42, ORIGIN[1]+44)


def fetch(url):
    if urlparse(url).hostname != 'imagery.nationalmap.gov':
        raise ValueError('Unexpected provider host')
    with urlopen(Request(url, headers={'User-Agent': 'RaftSim-source-review/1.0'}), timeout=45) as response:
        data = response.read(5_000_001)
    if len(data) > 5_000_000:
        raise ValueError('Bounded intake exceeded 5 MB')
    return data


def run(output):
    import rasterio
    from shapely.geometry import Polygon, box
    output = output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/'tmp'):
        raise ValueError('Fresh project tmp output required')
    output.mkdir(parents=True)
    records = []

    def acquire(name, url, as_json=True):
        data = fetch(url)
        (output/name).write_bytes(data)
        records.append(dict(file=name, url=url, bytes=len(data), sha256=hashlib.sha256(data).hexdigest()))
        (output/'downloads.json').write_text(json.dumps(records, indent=2)+'\n')
        result = json.loads(data) if as_json else data
        if as_json and 'error' in result:
            raise ValueError(result['error'])
        return result

    service = acquire('service.json', SERVICE+'?f=pjson')
    query = dict(geometry=','.join(map(str, BBOX)), geometryType='esriGeometryEnvelope',
                 inSR=32610, outSR=32610, spatialRel='esriSpatialRelIntersects',
                 where='Category=1', outFields='*', returnGeometry='true', f='pjson')
    catalog = acquire('catalog.json', SERVICE+'/query?'+urlencode(query))
    matches = [f for f in catalog['features'] if f['attributes']['Name'] == RASTER]
    if len(matches) != 1 or catalog.get('exceededTransferLimit'):
        raise ValueError('Exact named raster not uniquely available')
    feature = matches[0]
    attrs = feature['attributes']
    rings = feature['geometry']['rings']
    if len(rings) != 1 or not Polygon(rings[0]).covers(box(*BBOX)):
        raise ValueError('Entire requested window must be inside the source footprint')
    if attrs['band_count'] != 4 or attrs['resolution_value'] != .6 or attrs['acquisition_date'] != 1658361600000:
        raise ValueError('Unexpected source bands, resolution or date')
    params = dict(bbox=','.join(map(str, BBOX)), bboxSR=32610, imageSR=32610,
                  size='120,80', format='tiff', pixelType='U8', bandIds='0,1,2,3',
                  interpolation='RSP_NearestNeighbor', f='pjson',
                  renderingRule=json.dumps({'rasterFunction': 'None'}),
                  mosaicRule=json.dumps({'mosaicMethod': 'esriMosaicLockRaster',
                                        'lockRasterIds': [attrs['OBJECTID']]}))
    exported = acquire('export.json', SERVICE+'/exportImage?'+urlencode(params))
    acquire('raw-four-band.tif', exported['href'], as_json=False)
    with rasterio.open(output/'raw-four-band.tif') as dataset:
        if dataset.count != 4 or dataset.width != 120 or dataset.height != 80:
            raise ValueError('Provider did not return the requested four-band grid')
        if dataset.crs.to_epsg() != 32610 or max(abs(a-b) for a,b in zip(dataset.bounds, BBOX)) > 1e-6:
            raise ValueError('Export grid georeferencing differs from the locked window')
        if not (dataset.read_masks() == 255).all():
            raise ValueError('Source window contains nodata')
        extent = list(dataset.bounds)
    report = dict(schema='raftsim.troublemaker_spectral_source.v1', source=attrs,
                  bbox_utm32610_m=extent, shape=[80,120], resolution_m=.6,
                  bands=['red','green','blue','near_infrared'], rendering_rule='None',
                  footprint_covers_entire_window=True, all_bands_valid=True,
                  provider_service_description=service['serviceDescription'],
                  license='USGS service describes NAIP compressed orthoimagery as public domain; retain source attribution.',
                  registration_uncertainty_m=3.0,
                  limits='2022 spectral interpretation is not classification of 2019 individual LiDAR returns. No bathymetry or playable acceptance.',
                  source_geometry_modified=False, normal_play_changed=False, downloads=records)
    (output/'manifest.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(dict(manifest=str(output/'manifest.json'), source=RASTER, bands=4, shape=report['shape'])))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    run(parser.parse_args().output)
