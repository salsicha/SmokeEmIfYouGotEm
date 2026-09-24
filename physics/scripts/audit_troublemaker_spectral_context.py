"""Spectral context for diagnosed cap faces, never automatic rock classification."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from fetch_troublemaker_spectral_window import ROOT, ORIGIN


def ndvi(red, nir):
    red, nir = np.asarray(red, dtype=float), np.asarray(nir, dtype=float)
    if red.shape != nir.shape or not np.isfinite(red).all() or not np.isfinite(nir).all():
        raise ValueError('Matching finite red/NIR bands required')
    if np.any(red < 0) or np.any(nir < 0):
        raise ValueError('Negative source digital numbers are unsupported')
    denominator = nir + red
    return np.divide(nir-red, denominator, out=np.full(red.shape, np.nan), where=denominator>0)


def intersecting_pixels(xy, xs, ys, pixel_size, radius):
    if not np.isfinite([*xy, pixel_size, radius]).all() or pixel_size <= 0 or radius < 0:
        raise ValueError('Finite position and valid uncertainty required')
    # Include pixel squares intersecting the disk, not only their centres.
    dx = np.maximum(abs(xs-xy[0])-pixel_size/2, 0)
    dy = np.maximum(abs(ys-xy[1])-pixel_size/2, 0)
    return dy[:,None]**2+dx[None,:]**2 <= radius**2


def summary(values):
    values = np.asarray(values)
    finite = values[np.isfinite(values)]
    return dict(pixel_count=int(values.size), valid_ndvi_count=int(finite.size),
                minimum=float(finite.min()) if finite.size else None,
                median=float(np.median(finite)) if finite.size else None,
                maximum=float(finite.max()) if finite.size else None)


def run(source, ray_path, output):
    import rasterio
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    output = output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/'tmp'):
        raise ValueError('Fresh project tmp output required')
    manifest = json.loads((source/'manifest.json').read_text())
    if (manifest.get('schema') != 'raftsim.troublemaker_spectral_source.v1' or
            manifest.get('bands') != ['red','green','blue','near_infrared'] or
            manifest['source']['acquisition_date'] != 1658361600000):
        raise ValueError('Verified dated four-band source manifest required')
    for item in manifest['downloads']:
        if hashlib.sha256((source/item['file']).read_bytes()).hexdigest() != item['sha256']:
            raise ValueError('Source identity changed')
    rays = json.loads(ray_path.read_text())
    if rays['schema'] != 'raftsim.terrain_camera_source_audit.v1' or not rays['all_probes_match']:
        raise ValueError('Verified native/source camera rays required')
    cap_source = rays['source_identities']['cap']
    cap_path = ROOT/cap_source['path']
    if hashlib.sha256(cap_path.read_bytes()).hexdigest() != cap_source['sha256']:
        raise ValueError('Original cap changed')
    with np.load(cap_path, allow_pickle=False) as cap:
        vertices = cap['vertices_m'].copy()
        edges = cap['boundary_edges'].copy()
    with rasterio.open(source/'raw-four-band.tif') as dataset:
        raw = dataset.read()
        transform = dataset.transform
        if dataset.count != 4 or transform.b or transform.d or transform.a != -transform.e:
            raise ValueError('Expected four-band square north-up grid')
        pixel = transform.a
        xs = transform.c+(np.arange(dataset.width)+.5)*pixel-ORIGIN[0]
        ys = transform.f-(np.arange(dataset.height)+.5)*pixel-ORIGIN[1]
        bounds = dataset.bounds
    index = ndvi(raw[0],raw[3])
    radius = manifest['registration_uncertainty_m']
    rows = []
    for probe in rays['probes']:
        hit = probe['source_hit']
        if not hit or hit['source'] != 'cap':
            continue
        x,y = hit['local_hit_m'][:2]
        if not (xs[0]-pixel/2 <= x-radius and x+radius <= xs[-1]+pixel/2 and
                ys[-1]-pixel/2 <= y-radius and y+radius <= ys[0]+pixel/2):
            raise ValueError('Entire registration disk must be covered')
        region = intersecting_pixels((x,y),xs,ys,pixel,radius)
        centre = intersecting_pixels((x,y),xs,ys,pixel,0)
        rows.append(dict(pixel=probe['pixel'], triangle=hit['source_triangle'],
                         xy_local_m=[x,y], solid_face_kind=hit['solid_face_kind'],
                         nominal=summary(index[centre]), uncertainty_disk=summary(index[region])))
    report = dict(schema='raftsim.troublemaker_spectral_context.v1',
                  source_manifest_sha256=hashlib.sha256((source/'manifest.json').read_bytes()).hexdigest(),
                  camera_ray_sha256=hashlib.sha256(ray_path.read_bytes()).hexdigest(),
                  cap_source=cap_source, source_date='2022-07-21', lidar_year=2019,
                  registration_uncertainty_m=radius, pixel_size_m=pixel,
                  ndvi_definition='(NIR-red)/(NIR+red), source digital numbers; zero denominator invalid',
                  targets=rows, source_geometry_modified=False, point_classifications_modified=False,
                  normal_play_changed=False, acceptance=False,
                  limits='NDVI provides vegetation-sensitive context, not ground/rock labels, calibrated reflectance, surveyed boundaries or underwater geometry. Dates differ; registration disks are not per-point classification confidence.')
    output.mkdir(parents=True)
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    extent=[bounds.left-ORIGIN[0],bounds.right-ORIGIN[0],bounds.bottom-ORIGIN[1],bounds.top-ORIGIN[1]]
    fig,axes=plt.subplots(1,3,figsize=(15,5),layout='constrained')
    axes[0].imshow(np.moveaxis(raw[:3],0,-1),extent=extent)
    axes[1].imshow(np.moveaxis(raw[[3,0,1]],0,-1),extent=extent)
    im=axes[2].imshow(index,extent=extent,vmin=-1,vmax=1,cmap='RdYlGn')
    for axis,title in zip(axes,['Raw red/green/blue','Raw NIR/red/green','NDVI (digital numbers)']):
        axis.set_title(title+'\n2022-07-21; 2019 cap boundary in cyan')
        for edge in edges: axis.plot(vertices[edge,0],vertices[edge,1],color='cyan',lw=.5)
        for row in rows:
            x,y=row['xy_local_m'];axis.plot(x,y,'kx',ms=4)
            axis.add_patch(plt.Circle((x,y),radius,fill=False,color='black',alpha=.3,lw=.5))
        axis.set_xlabel('Local east (m)');axis.set_ylabel('Local north (m)')
        axis.set_xlim(-30,12);axis.set_ylim(5,40)
    fig.colorbar(im,ax=axes[2],shrink=.7)
    fig.savefig(output/'spectral-context.png',dpi=150);plt.close(fig)
    print(json.dumps(dict(targets=len(rows),report=str(output/'report.json'))))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('rays',type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();run(args.source,args.rays,args.output)
