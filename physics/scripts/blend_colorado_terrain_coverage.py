"""Use valid native 1 m terrain with explicitly mapped captured coarse fallback.

No source pixels are overwritten. The resolution mask prevents calling missing
fine coverage surveyed at one metre. Water pixels are not used as bathymetry.
"""
import argparse
import json
from pathlib import Path
import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling
from build_colorado_catalog_evidence import sha
from fetch_colorado_terrain_windows import verify_colorado_pixels,fine_source_selection,nominal_resolution_matches


def verify_catalog_absence(folder,row):
    """Only a complete hash-bound catalogue may authorize an absent fine raster."""
    expected=dict(cell_m=1,file=None,url=None,sha256=None,response_sha256=None,bytes=0,
                  valid_pixel_coverage_verified=False,valid_native_pixels=0,
                  partial_fine_capture=True,native_coverage_absent=True,locked_native_sources=[],
                  source_absence_reason='complete_catalog_has_no_native_fine_source')
    if any(k not in row or row[k]!=v for k,v in expected.items()):
        raise ValueError('Unverified absent fine-source receipt')
    spec=row['source_catalog'];path=(folder/spec['file']).resolve()
    if path.parent!=folder.resolve() or sha(path)!=spec['sha256']:
        raise ValueError('Changed or unsafe fine-source catalogue')
    catalog=json.loads(path.read_text())
    if ('error' in catalog or catalog.get('exceededTransferLimit') or
            fine_source_selection(catalog['features'],1,allow_empty=True)):
        raise ValueError('Catalogue does not establish fine-source absence')
    x0,y0,x1,y1=row['bounds_epsg6404'];ny,nx=row['shape']
    if (not np.isfinite([x0,y0,x1,y1,nx,ny]).all() or min(nx,ny)<=0 or
            nx!=int(nx) or ny!=int(ny) or nx*ny>8_000_000 or
            x1-x0!=nx or y1-y0!=ny or row['missing_native_pixels']!=nx*ny):
        raise ValueError('Invalid absent-source target lattice')


def combine(fine, valid, coarse, coarse_cell_m):
    fine=np.asarray(fine);coarse=np.asarray(coarse);valid=np.asarray(valid,dtype=bool)
    if fine.shape!=coarse.shape or fine.shape!=valid.shape:
        raise ValueError('Coverage grids differ')
    if not np.isfinite(coarse_cell_m) or coarse_cell_m<1:
        raise ValueError('Invalid fallback resolution')
    take=valid&np.isfinite(fine)&(fine>0)
    result=np.where(take,fine,coarse).astype('float32')
    verify_colorado_pixels(result,np.ones(result.shape,bool))
    return result,np.where(take,1.,coarse_cell_m).astype('float32')


def blend(fine_dir,coarse_dir,out):
    if out.exists():raise ValueError('Fresh mixed-resolution output required')
    fm=json.loads((fine_dir/'manifest.json').read_text())
    cm=json.loads((coarse_dir/'manifest.json').read_text())
    for m in (fm,cm):
        if (m['source_service']!='https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer'
                or m['vertical_reference']!='NAVD88 orthometric metres (CONUS 3DEP)'):
            raise ValueError('Unreviewed source or datum')
    out.mkdir(parents=True);windows=[]
    for row in fm['windows']:
        coarse=next(c for c in cm['windows'] if c['name']==row['name'])
        absent=row.get('source_absence_reason')=='complete_catalog_has_no_native_fine_source'
        if absent:
            verify_catalog_absence(fine_dir,row)
        elif row['cell_m']!=1 or not row.get('locked_native_sources') or any(not nominal_resolution_matches(s.get('LowPS'),1) for s in row['locked_native_sources']):
            raise ValueError('Fine input must identify locked native metre sources')
        if row['bounds_epsg6404']!=coarse['bounds_epsg6404']:
            raise ValueError('Fallback does not cover the exact fine-source extent')
        inputs=[]
        for folder,spec in ([(coarse_dir,coarse)] if absent else [(fine_dir,row),(coarse_dir,coarse)]):
            path=(folder/spec['file']).resolve()
            if path.parent!=folder.resolve() or sha(path)!=spec['sha256']:
                raise ValueError('Changed or unsafe terrain input')
            inputs.append(path)
        with rasterio.open(inputs[-1]) as fallback:
            if (fallback.crs.to_epsg()!=6404 or fallback.res!=(coarse['cell_m'],coarse['cell_m']) or
                    list(fallback.bounds)!=coarse['bounds_epsg6404'] or coarse['cell_m']<=1):
                raise ValueError('Unexpected terrain registration')
            if absent:
                from rasterio.transform import from_origin
                ny,nx=row['shape'];x0,y0,x1,y1=row['bounds_epsg6404']
                profile=fallback.profile.copy()
                profile.update(width=nx,height=ny,transform=from_origin(x0,y1,1.,1.))
                a=np.full((ny,nx),np.nan,dtype='float32');valid=np.zeros((ny,nx),dtype=bool)
            else:
                with rasterio.open(inputs[0]) as src:
                    if src.crs.to_epsg()!=6404 or src.res!=(1.,1.):
                        raise ValueError('Unexpected terrain registration')
                    profile=src.profile.copy();a=src.read(1);valid=src.read_masks(1)>0
            b=np.full(a.shape,np.nan,dtype='float32')
            reproject(rasterio.band(fallback,1),b,src_transform=fallback.transform,src_crs=fallback.crs,
                dst_transform=profile['transform'],dst_crs=profile['crs'],dst_nodata=np.nan,resampling=Resampling.bilinear)
            values,resolution=combine(a,valid,b,coarse['cell_m'])
        profile.update(dtype='float32',count=1,nodata=-99999.,compress='deflate')
        image_name=coarse['file'] if absent else row['file']
        mask_name=Path(image_name).stem+'_source_resolution.tif'
        for name,data in ((image_name,values),(mask_name,resolution)):
            with rasterio.open(out/name,'w',**profile) as target:target.write(data,1)
        result=dict(name=row['name'],file=image_name,sha256=sha(out/image_name),cell_m=1,
            shape=row['shape'],bounds_epsg6404=row['bounds_epsg6404'],valid_pixel_coverage_verified=True,
            source_resolution_mask=dict(file=mask_name,sha256=sha(out/mask_name)),
            native_fine_cells=int((resolution==1).sum()),coarse_fallback_cells=int((resolution!=1).sum()),
            source_files=[dict(path=str(p),sha256=sha(p)) for p in inputs],
            fine_source_catalog=row['source_catalog'],locked_native_sources=row['locked_native_sources'],
            native_source_catalog_absent=absent)
        windows.append(result)
        print(json.dumps({k:result[k] for k in ('name','native_fine_cells','coarse_fallback_cells')}),flush=True)
    manifest=dict(schema='raftsim.colorado_terrain_windows_capture.v1',
        source_service=fm['source_service'],source_credit=fm['source_credit'],
        vertical_reference=fm['vertical_reference'],rights_scope=fm['rights_scope'],
        source_manifests=[dict(path=str(p),sha256=sha(p)) for p in (fine_dir/'manifest.json',coarse_dir/'manifest.json')],
        policy='Use finite positive native 1 m pixels; retain captured 10 m fallback only in mapped gaps. Export spacing is not native resolution.',
        limitations=['Mixed-resolution terrain, not uniformly metre-surveyed.',
                     'No measured underwater bed, boulder identity, vegetation or playable acceptance implied.'],windows=windows)
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('fine','coarse','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();blend(a.fine.resolve(),a.coarse.resolve(),a.out.resolve())
