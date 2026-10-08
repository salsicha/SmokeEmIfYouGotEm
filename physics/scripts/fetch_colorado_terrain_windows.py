"""Capture bounded USGS terrain windows; do not infer rapid bathymetry.

The default 3DEP source uses NAVD88 in CONUS. Its hydro-flattened water pixels
are not bathymetry or the 2021 water surface. The legacy service has conflicting
vertical metadata and is retained only for comparison. Export resolution does
not establish source accuracy; no automatic datum conversion is performed.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
from urllib.parse import urlencode, urlparse
from fetch_colorado_catalog_sources import read, validate_json

SERVICES={
    'gcmrc-legacy':'https://grandcanyon.usgs.gov/server/rest/services/Topography/GrandCanyonTopography10meter/ImageServer',
    '3dep':'https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer',
}


def verify_colorado_pixels(values, valid):
    import numpy as np
    values=np.asarray(values);valid=np.asarray(valid,dtype=bool)
    # This corridor is hundreds of metres above NAVD88 zero. ImageServer can
    # return zero-filled pixels with no TIFF nodata tag; finite alone is unsafe.
    if values.shape!=valid.shape or not valid.all() or not np.isfinite(values).all() or (values<=0).any():
        raise ValueError('Missing or zero-filled Colorado terrain; do not compose as valid banks')


def nominal_resolution_matches(value, cell_m):
    """Allow catalogue floating-point roundoff, not a coarser source class.

    USGS tile 64838 reports LowPS=0.9999999999999971 for its native 1 m
    product. Preserve that raw value in receipts; never round source metadata.
    """
    return (type(value) in (int, float) and math.isfinite(value) and value > 0
            and math.isclose(value, cell_m, rel_tol=0., abs_tol=1e-12))


def fine_source_selection(features, cell_m, allow_empty=False):
    """Do not mistake upsampled coarse DEMs for surveyed metre-scale terrain."""
    selected=[]
    for feature in features:
        a=feature['attributes']; resolution=a.get('LowPS')
        if (type(resolution) not in (int,float) or not math.isfinite(resolution) or resolution<=0 or
                not (resolution<=cell_m or nominal_resolution_matches(resolution,cell_m))):continue
        datum=str(a.get('VerticalDatum','')).upper().replace(' ','')
        if 'NAVD88' not in datum:raise ValueError('Fine source has unreviewed vertical datum')
        if type(a.get('OBJECTID')) is not int:raise ValueError('Missing fine-source raster identity')
        selected.append(a)
    if not selected:
        if not allow_empty:raise ValueError('No native fine-resolution source covers this window')
        # Absence must be positively supported by an empty catalogue or known
        # coarser sources, not by malformed/unknown catalogue resolutions.
        if any(not isinstance(f['attributes'].get('LowPS'),(int,float)) or
               not math.isfinite(f['attributes']['LowPS']) or f['attributes']['LowPS']<=0
               for f in features):
            raise ValueError('Unknown source resolution cannot establish fine-source absence')
        return []
    # Record and prefer the service catalog's newer acquisition field. This is
    # not an assertion that that field is an independently verified flight date.
    selected.sort(key=lambda a:(a.get('AcquisitionDate') or 0,a['OBJECTID']),reverse=True)
    return selected


def fine_coverage(values, valid, allow_partial=False, allow_empty=False):
    import numpy as np
    values=np.asarray(values);valid=np.asarray(valid,dtype=bool)
    if values.shape!=valid.shape:raise ValueError('Coverage shapes disagree')
    good=valid&np.isfinite(values)&(values>0)
    if allow_empty and not allow_partial:
        raise ValueError('Empty fine coverage requires explicit partial raw capture')
    if not good.any() and not allow_empty:raise ValueError('Fine export contains no usable terrain')
    if not allow_partial:verify_colorado_pixels(values,valid)
    return dict(valid_pixel_coverage_verified=bool(good.all()),
                valid_native_pixels=int(good.sum()),missing_native_pixels=int((~good).sum()),
                partial_fine_capture=not bool(good.all()),
                native_coverage_absent=not bool(good.any()))


def capture_bounds(bounds, margin_m=400):
    """Outward ten-metre alignment; a smaller halo never crops the request."""
    if (len(bounds)!=4 or any(type(v) not in (int,float) or not math.isfinite(v) for v in bounds)
            or bounds[0]>=bounds[2] or bounds[1]>=bounds[3]):
        raise ValueError('Invalid terrain capture bounds')
    if type(margin_m) is not int or not 0<=margin_m<=1000 or margin_m%10:
        raise ValueError('Capture margin must be a bounded multiple of ten metres')
    x0,y0,x1,y1=bounds
    return (math.floor(x0/10)*10-margin_m,math.floor(y0/10)*10-margin_m,
            math.ceil(x1/10)*10+margin_m,math.ceil(y1/10)*10+margin_m)


def capture(windows, out, selected, service_name='3dep', cell_m=10, allow_partial_fine=False,
            allow_empty_fine=False, margin_m=400):
    if out.exists(): raise ValueError('Fresh terrain source directory required')
    if cell_m not in (1,2,10):raise ValueError('Only bounded 1, 2 or 10 m exports supported')
    if cell_m<10 and service_name!='3dep':raise ValueError('Fine exports require audited 3DEP catalog sources')
    if allow_partial_fine and (cell_m>=10 or service_name!='3dep'):
        raise ValueError('Partial capture is only for explicitly locked fine 3DEP sources')
    if allow_empty_fine and not allow_partial_fine:
        raise ValueError('Empty fine coverage requires explicit partial raw capture')
    index=json.loads((windows/'index.json').read_text(encoding='utf-8'))
    entries=[w for w in index['windows'] if not selected or w['name'] in selected]
    if not entries or set(selected)-{w['name'] for w in entries}: raise ValueError('Unknown or empty selection')
    # Validate all request extents before network traffic or partial outputs.
    request_bounds=[capture_bounds(w['bounds_epsg6404'],margin_m) for w in entries]
    if any((b[2]-b[0])*(b[3]-b[1])//(cell_m*cell_m)>8_000_000 for b in request_bounds):
        raise ValueError('Terrain window exceeds bounded source budget')
    endpoint=SERVICES[service_name]
    raw=read(endpoint+'?f=pjson')
    service=validate_json(raw)
    if service['bandCount']!=1 or service['pixelType']!='F32':
        raise ValueError('Unexpected terrain service format or resolution')
    if service_name=='gcmrc-legacy' and service.get('heightModelInfo',{}).get('heightModel')!='ellipsoidal':
        raise ValueError('Vertical reference changed; review it before acquisition')
    out.mkdir(parents=True)
    (out/'service.json').write_bytes(raw)
    receipts=[]
    for entry,bounds in zip(entries,request_bounds):
        key=Path(next(p.name for p in windows.glob('*.json') if p.name!='index.json' and
            json.loads(p.read_text(encoding='utf-8'))['name']==entry['name'])).stem
        nx,ny=(bounds[2]-bounds[0])//cell_m,(bounds[3]-bounds[1])//cell_m
        if nx*ny>8_000_000: raise ValueError('Terrain window exceeds bounded source budget')
        fine_sources=[]; catalog_receipt=None; mosaic={}
        if cell_m<10:
            catalog_url=endpoint+'/query?'+urlencode(dict(f='json',where='Category=1',
                geometry=','.join(map(str,bounds)),geometryType='esriGeometryEnvelope',inSR=6404,
                spatialRel='esriSpatialRelIntersects',returnGeometry='false',
                outFields='OBJECTID,Name,LowPS,HighPS,ProductName,VerticalDatum,AcquisitionDate,URL,Metadata,Resolution_X'))
            catalog_raw=read(catalog_url); catalog=validate_json(catalog_raw)
            if catalog.get('exceededTransferLimit'):raise ValueError('Incomplete source catalog query')
            fine_sources=fine_source_selection(catalog['features'],cell_m,allow_empty_fine)
            catalog_name=key+'_source_catalog.json'
            (out/catalog_name).write_bytes(catalog_raw)
            catalog_receipt=dict(file=catalog_name,url=catalog_url,sha256=hashlib.sha256(catalog_raw).hexdigest())
            if not fine_sources:
                # Never send an empty lockRasterIds request: the service might
                # silently select a coarse source and export it at metre spacing.
                receipts.append(dict(name=entry['name'],file=None,url=None,
                    source_service=endpoint,bounds_epsg6404=bounds,shape=[ny,nx],cell_m=cell_m,
                    valid_pixel_coverage_verified=False,valid_native_pixels=0,
                    missing_native_pixels=nx*ny,partial_fine_capture=True,native_coverage_absent=True,
                    source_absence_reason='complete_catalog_has_no_native_fine_source',
                    locked_native_sources=[],source_catalog=catalog_receipt,
                    bytes=0,sha256=None,response_sha256=None))
                print(f"{entry['name']}: complete catalogue confirms no native {cell_m} m source; no raster exported",flush=True)
                continue
            mosaic=dict(mosaicRule=json.dumps(dict(mosaicMethod='esriMosaicLockRaster',
                lockRasterIds=[s['OBJECTID'] for s in fine_sources],mosaicOperation='MT_FIRST')))
        url=endpoint+'/exportImage?'+urlencode(dict(f='json',bbox=','.join(map(str,bounds)),
            bboxSR=6404,imageSR=6404,size=f'{nx},{ny}',format='tiff',pixelType='F32',
            renderingRule=json.dumps({'rasterFunction':'None'}),
            interpolation='RSP_BilinearInterpolation',adjustAspectRatio='false',noDataInterpretation='esriNoDataMatchAny',**mosaic))
        response=read(url)
        export=validate_json(response)
        href=export['href']
        if urlparse(href).hostname!=urlparse(endpoint).hostname or not href.startswith('https://'):
            raise ValueError('Unexpected generated-raster host')
        image=read(href,limit=64*1024*1024)
        if image[:4] not in (b'II*\x00',b'MM\x00*',b'II+\x00',b'MM\x00+'):
            raise ValueError('Export is not a TIFF')
        if export.get('width')!=nx or export.get('height')!=ny:
            raise ValueError('Export dimensions disagree with request')
        (out/(key+'.tif')).write_bytes(image)
        (out/(key+'_export.json')).write_bytes(response)
        coverage=dict(valid_pixel_coverage_verified=False)
        if cell_m<10:
            import rasterio
            with rasterio.open(out/(key+'.tif')) as raster:
                coverage=fine_coverage(raster.read(1),raster.read_masks(1)>0,allow_partial_fine,allow_empty_fine)
        receipts.append(dict(name=entry['name'],file=key+'.tif',url=url,
            source_service=endpoint,bounds_epsg6404=bounds,shape=[ny,nx],cell_m=cell_m,
            **coverage,
            locked_native_sources=fine_sources,source_catalog=catalog_receipt,
            bytes=len(image),sha256=hashlib.sha256(image).hexdigest(),
            response_sha256=hashlib.sha256(response).hexdigest()))
        print(f"{entry['name']}: {nx}x{ny} at {cell_m} m; datum/coverage audit still required",flush=True)
    result=dict(schema='raftsim.colorado_terrain_windows_capture.v1',
        construction_margin_m=margin_m,
        source_service=endpoint,source_credit=service['copyrightText'],
        source_height_model=service.get('heightModelInfo'),source_crs=service['spatialReference'],
        vertical_reference=('NAVD88 orthometric metres (CONUS 3DEP)' if service_name=='3dep' else
                            'Conflicting legacy metadata; DO NOT compose until independently resolved'),
        vertical_reference_authority='https://www.usgs.gov/faqs/what-projection-horizontal-datum-vertical-datum-and-resolution-a-usgs-digital-elevation-model',
        service_sha256=hashlib.sha256(raw).hexdigest(),
        rights_scope='USGS National Map terrain; federal public-domain data, preserve attribution',
        limitations=[f'{cell_m} m exported terrain; native fine-source catalog locked for sub-10 m exports. No measured underwater bed implied.',
                    'Partial fine captures are raw sources only: use explicitly mapped fallback before composition, never zero-fill holes.',
                    'Catalog tile intersection alone does not prove valid-pixel coverage; compose must refuse missing terrain.',
                    'No automatic vertical conversion; explicitly transform NAVD88 before mixing with the ellipsoidal survey.',
                    'Image export alone does not construct a map or establish difficulty.'],windows=receipts)
    (out/'manifest.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--windows',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--names',nargs='*',default=[])
    p.add_argument('--service',choices=SERVICES,default='3dep')
    p.add_argument('--cell-m',type=int,choices=(1,2,10),default=10)
    p.add_argument('--margin-m',type=int,default=400,help='Outward capture halo, metres; defaults unchanged. Use a small explicit halo for missing outer terrain tiles.')
    p.add_argument('--allow-partial-fine',action='store_true',help='Preserve incomplete raw fine capture for explicit coverage blending; direct composition remains refused')
    p.add_argument('--allow-empty-fine',action='store_true',help='Record absent native pixels or a complete catalogue with no fine source; never make an unlocked export. Requires partial capture and a separate verified coarse fallback')
    a=p.parse_args();capture(a.windows,a.out,a.names,a.service,a.cell_m,a.allow_partial_fine,a.allow_empty_fine,a.margin_m)
