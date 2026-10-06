"""Capture bounded USGS 10 m terrain windows; do not infer rapid bathymetry.

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


def capture(windows, out, selected, service_name='3dep'):
    if out.exists(): raise ValueError('Fresh terrain source directory required')
    index=json.loads((windows/'index.json').read_text(encoding='utf-8'))
    entries=[w for w in index['windows'] if not selected or w['name'] in selected]
    if not entries or set(selected)-{w['name'] for w in entries}: raise ValueError('Unknown or empty selection')
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
    for entry in entries:
        key=Path(next(p.name for p in windows.glob('*.json') if p.name!='index.json' and
            json.loads(p.read_text(encoding='utf-8'))['name']==entry['name'])).stem
        x0,y0,x1,y1=entry['bounds_epsg6404']
        bounds=(math.floor(x0/10)*10-400,math.floor(y0/10)*10-400,
                math.ceil(x1/10)*10+400,math.ceil(y1/10)*10+400)
        nx,ny=(bounds[2]-bounds[0])//10,(bounds[3]-bounds[1])//10
        if nx*ny>1_000_000: raise ValueError('Terrain window exceeds bounded source budget')
        url=endpoint+'/exportImage?'+urlencode(dict(f='json',bbox=','.join(map(str,bounds)),
            bboxSR=6404,imageSR=6404,size=f'{nx},{ny}',format='tiff',pixelType='F32',
            renderingRule=json.dumps({'rasterFunction':'None'}),
            interpolation='RSP_BilinearInterpolation',adjustAspectRatio='false',noDataInterpretation='esriNoDataMatchAny'))
        response=read(url)
        export=validate_json(response)
        href=export['href']
        if urlparse(href).hostname!=urlparse(endpoint).hostname or not href.startswith('https://'):
            raise ValueError('Unexpected generated-raster host')
        image=read(href,limit=8*1024*1024)
        if image[:4] not in (b'II*\x00',b'MM\x00*',b'II+\x00',b'MM\x00+'):
            raise ValueError('Export is not a TIFF')
        if export.get('width')!=nx or export.get('height')!=ny:
            raise ValueError('Export dimensions disagree with request')
        (out/(key+'.tif')).write_bytes(image)
        (out/(key+'_export.json')).write_bytes(response)
        receipts.append(dict(name=entry['name'],file=key+'.tif',url=url,
            source_service=endpoint,bounds_epsg6404=bounds,shape=[ny,nx],cell_m=10,
            bytes=len(image),sha256=hashlib.sha256(image).hexdigest(),
            response_sha256=hashlib.sha256(response).hexdigest()))
        print(f"{entry['name']}: {nx}x{ny} at 10 m; datum/coverage audit still required",flush=True)
    result=dict(schema='raftsim.colorado_terrain_windows_capture.v1',
        source_service=endpoint,source_credit=service['copyrightText'],
        source_height_model=service.get('heightModelInfo'),source_crs=service['spatialReference'],
        vertical_reference=('NAVD88 orthometric metres (CONUS 3DEP)' if service_name=='3dep' else
                            'Conflicting legacy metadata; DO NOT compose until independently resolved'),
        vertical_reference_authority='https://www.usgs.gov/faqs/what-projection-horizontal-datum-vertical-datum-and-resolution-a-usgs-digital-elevation-model',
        service_sha256=hashlib.sha256(raw).hexdigest(),
        rights_scope='USGS National Map terrain; federal public-domain data, preserve attribution',
        limitations=['10 m regional terrain, not detailed boulders or measured rapid bed.',
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
    a=p.parse_args();capture(a.windows,a.out,a.names,a.service)
