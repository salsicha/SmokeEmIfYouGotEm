"""Prepare source-classified canopy on the continuous native triangle terrain.

Forest cover is inferred from captured 10 m reflectance; individual plants,
dimensions and species are art-directed, not surveyed. This does not save an
engine map or certify native grounding, water clearance after cooking, or FPS.
Kept beside the native canopy import tools; physics construction is read-only.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import shapely
from scipy.ndimage import uniform_filter
from scipy.spatial import cKDTree

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'physics/scripts'))
from export_colorado_continuous_terrain import LandscapeTriangles
from build_colorado_continuous_dressing import terrain_support_slope
from futaleufu_corridor_bed import FutaleufuBed
from futaleufu_canopy_transforms import transform_row

PREFIX=ROOT/'physics/data/real_world/futaleufu_river_chile/production_corridor/rio_azul_swinging_bridge_to_pasarela'
MESH_NAMES=('SM_RaftSim_Temperate_BroadleafTree_A_OpaqueV1','SM_RaftSim_Temperate_ConiferTree_A_OpaqueV1',
            'SM_RaftSim_Temperate_RiparianShrub_A_OpaqueV1')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def same_bed_source(terrain_source,bed_source):
    # Export/context extension add their own lineage, but may not replace any
    # construction assumption or captured source belonging to the shared bed.
    return all((all(terrain_source.get(k,{}).get(p)==h for p,h in value.items()) if k=='sources_sha256'
                else terrain_source.get(k)==value) for k,value in bed_source.items())


def forest_cover(raw):
    valid=np.asarray(raw['valid'])
    if valid.ndim!=2 or valid.dtype.kind!='b':raise ValueError('Boolean native validity required')
    reflectance={}
    for band in ('green','red','nir'):
        data=np.asarray(raw[band])
        if data.shape!=valid.shape or data.dtype!=np.uint16:raise ValueError('Aligned original uint16 bands required')
        valid=valid&(data!=0)
        reflectance[band]=data.astype(float)*.0001-.1
    g,r,n=[reflectance[k] for k in ('green','red','nir')]
    cover=valid&((n-r)/np.maximum(n+r,.001)>.6)&(g<.062)
    # Do not grow forest into bare/water pixels or through nodata. The 30 m
    # majority only removes isolated classifications; all nine pixels must exist.
    return cover&(uniform_filter(cover.astype(float),3,mode='constant')>.5)&(
        uniform_filter(valid.astype(float),3,mode='constant')>1-1e-10)


def cover_at(xy,cover,grid):
    xy=np.asarray(xy,float);t=grid['transform']
    if (xy.ndim!=2 or xy.shape[1]!=2 or not np.isfinite(xy).all() or grid['epsg']!=32718
            or t[:2]!=[10.,0.] or t[3:5]!=[0.,-10.] or list(cover.shape)!=grid['shape']):
        raise ValueError('Aligned finite native UTM18S cover required')
    c=(xy[:,0]-t[2])/10-.5;r=(t[5]-xy[:,1])/10-.5
    inside=(c>=0)&(r>=0)&(c<=cover.shape[1]-1)&(r<=cover.shape[0]-1)
    result=np.zeros(len(xy),bool)
    result[inside]=cover[np.floor(r[inside]+.5).astype(int),np.floor(c[inside]+.5).astype(int)]
    return result


def crown_radius(bounds,scale):
    extent=np.maximum(np.abs(bounds['min'][:2]),np.abs(bounds['max'][:2]))
    return float(np.linalg.norm(extent*np.asarray(scale)[:2])/100.)


def eligible(height,slope,clearance,radius):
    height,slope,clearance,radius=[np.asarray(v,float) for v in (height,slope,clearance,radius)]
    return (np.isfinite(height)&np.isfinite(slope)&np.isfinite(clearance)&np.isfinite(radius)
            &(slope<=np.tan(np.deg2rad(62.)))&(clearance>=np.maximum(12.,radius+8.))
            &(clearance<=650.)&(radius>0))


def chunk_index(point,origin,span):
    return tuple(int(i) for i in np.floor((np.asarray(point)-np.asarray(origin))/span))


def build(terrain_folder,source_folder,output,inventory):
    terrain_folder,source_folder,output,inventory=map(Path,(terrain_folder,source_folder,output,inventory))
    if output.exists():raise ValueError('Fresh canopy output required')
    terrain=LandscapeTriangles(terrain_folder);manifest=terrain.manifest
    if (manifest.get('river_id')!='futaleufu_river_chile' or manifest['horizontal_origin_m']!=[739986.,5195961.5]
            or manifest['vertical_datum_m']!=150. or manifest['world_y_sign']!=-1):
        raise ValueError('Reviewed continuous Futaleufu terrain frame required')
    sources=json.loads((source_folder/'manifest.json').read_text())
    if sources['schema']!='raftsim.futaleufu_continuous_sources.v1':raise ValueError('Verified full corridor sources required')
    optical=next(r for r in sources['optical'] if r['datetime'].startswith('2026-01-04'))
    optical_path=(source_folder/optical['file']).resolve();optical_path.relative_to(source_folder.resolve())
    if sha(optical_path)!=optical['sha256']:raise ValueError('Changed optical evidence')
    with np.load(optical_path,allow_pickle=False) as raw:cover=forest_cover(raw)
    bed=FutaleufuBed(source_folder,PREFIX/'hydrology/channel_profile_2026_10_v2',
        PREFIX/'hydrography/confluence_network_2026_10_v1/network.json',depth_m=1.8)
    if not same_bed_source(manifest['evidence_source'],bed.receipt):raise ValueError('Canopy and native terrain use different river footprints')
    for relative,digest in manifest['evidence_source']['sources_sha256'].items():
        path=(ROOT/relative).resolve();path.relative_to(ROOT)
        if sha(path)!=digest:raise ValueError('Changed exported terrain evidence: '+relative)
    inspected=json.loads(inventory.read_text())['canopy'];meshes=[]
    for name in MESH_NAMES:
        row=next(r for r in inspected if r['mesh'].endswith('.'+name))
        asset=ROOT/'unreal/Content'/Path(row['mesh'].split('.')[0].removeprefix('/Game/')).with_suffix('.uasset')
        meshes.append(dict(asset=row['mesh'],bounds=row['bounds'],materials=row['materials'],asset_sha256=sha(asset)))
    pins={str(p.resolve()):sha(p) for p in (source_folder/'manifest.json',optical_path,inventory,Path(__file__))}
    origin=np.asarray(manifest['horizontal_origin_m']);span=terrain.span
    grid=sources['grid'];t=grid['transform'];height,width=grid['shape'];spacing=9.
    x=np.arange(np.ceil((t[2]+5)/spacing)*spacing,t[2]+width*10-5,spacing)
    y=np.arange(np.ceil((t[5]-height*10+5)/spacing)*spacing,t[5]-5,spacing)
    xy=np.stack(np.meshgrid(x,y),axis=-1).reshape(-1,2)
    rng=np.random.default_rng(20261008);xy+=rng.uniform(-.35,.35,xy.shape)*spacing
    candidates=len(xy);xy=xy[cover_at(xy,cover,grid)]
    clearance=shapely.distance(shapely.points(xy),bed.bed_polygon)
    pre=(clearance>=12.)&(clearance<=650.);xy=xy[pre];clearance=clearance[pre]
    z=terrain.sample(xy);slope=terrain_support_slope(terrain.sample,xy,z)
    known=np.isfinite(z)&np.isfinite(slope)&(slope<=np.tan(np.deg2rad(62.)))
    xy,z,slope,clearance=xy[known],z[known],slope[known],clearance[known]
    if len(xy)<2:raise ValueError('Insufficient source-supported canopy')
    nearest=cKDTree(xy).query(xy,k=2)[0][:,1]
    radius=np.clip(.7*nearest,3.5,8.)
    heights=np.clip(3.2*radius+rng.uniform(0,4,len(xy)),14,30)
    forms=rng.integers(0,2,len(xy));yaw=rng.uniform(0,360,len(xy))
    chunks={};counts=[0,0,0];minimum_clearance=float('inf');minimum_crown_clearance=float('inf')
    def add(point,ground,sl,water,mesh,row,understory=False):
        nonlocal minimum_clearance,minimum_crown_clearance
        transform=transform_row(row,meshes[mesh]['bounds'],(ground-150.)*100,understory=understory)
        extent=crown_radius(meshes[mesh]['bounds'],transform['scale'])
        if not eligible(ground,sl,water,extent):return
        index=chunk_index(point,origin,span)
        if index not in terrain.by_index:raise ValueError('Placement has no native terrain owner')
        item=dict(mesh=mesh,location_cm=transform['location_cm'],ground_cm=transform['ground_cm'],
            scale_xyz=transform['scale'],yaw_deg=transform['yaw_degrees'],
            source_water_clearance_m=float(water),crown_bound_radius_m=extent)
        chunks.setdefault(index,[]).append(item);counts[mesh]+=1
        minimum_clearance=min(minimum_clearance,float(water));minimum_crown_clearance=min(minimum_crown_clearance,float(water-extent))
    for i,p in enumerate(xy):
        world=(p-origin)*[100,-100]
        row=[*world,(z[i]-150.)*100,radius[i],heights[i],int(forms[i]),1,yaw[i]]
        add(p,z[i],slope[i],clearance[i],int(forms[i]),row)
    # Recheck offset understory independently; a tree's eligibility cannot
    # authorize its shrub on a wet bank or a missing native triangle.
    near=clearance<=200.;angle=rng.uniform(0,2*np.pi,len(xy));offset=radius*rng.uniform(.4,.9,len(xy))
    shrubs=(xy+np.c_[np.cos(angle),np.sin(angle)]*offset[:,None])[near]
    shrubs=shrubs[cover_at(shrubs,cover,grid)]
    uz=terrain.sample(shrubs);us=terrain_support_slope(terrain.sample,shrubs,uz)
    uw=shapely.distance(shapely.points(shrubs),bed.bed_polygon)
    for p,ground,sl,water in zip(shrubs,uz,us,uw):
        if not np.isfinite([ground,sl,water]).all():continue
        world=(p-origin)*[100,-100]
        row=[*world,float(rng.uniform(3,6)),float(rng.uniform(4,7)),float(rng.uniform(0,360))]
        add(p,ground,sl,water,2,row,True)
    terrain.verify_unchanged()
    if any(sha(Path(p))!=digest for p,digest in pins.items()):raise ValueError('Changed canopy dependency')
    if not sum(counts):raise ValueError('No qualified vegetation')
    result=dict(schema='raftsim.futaleufu_continuous_canopy.v1',river_id='futaleufu_river_chile',
        terrain_manifest_sha256=terrain.manifest_sha256,sources_sha256=pins,
        optical_datetime=optical['datetime'],optical_attribution=sources['optical_attribution'].replace('[year]','2026'),
        optical_license=sources['optical_license'],horizontal_origin_m=origin.tolist(),vertical_datum_m=150.,world_y_sign=-1,
        classification='NDVI > 0.6 and green reflectance < 0.062; original valid pixel AND 30m majority, no growing through bare/water/nodata',
        inferred='Forest classification, individual positions, dimensions and species; no surveyed trees',
        source_water_policy='Connected captured mainstem and inferred Azul footprint, including all branches; islands remain land',
        source_water_minimum_clearance_m=minimum_clearance,minimum_crown_bound_clearance_m=minimum_crown_clearance,
        maximum_ground_slope_degrees=62.,grounding='Exact encoded exported Landscape triangles; native collision verification still required',
        meshes=meshes,chunks=[dict(chunk=list(index),instances=rows) for index,rows in sorted(chunks.items())],
        candidate_count=candidates,instance_count=sum(counts),instances_per_mesh=counts,
        cull_start_cm=45000,cull_end_cm=65000,collision_enabled=False,terrain_modified=False,
        cloud_screened=False,solved_water_clearance_verified=False,native_grounding_verified=False,
        rendered_validated=False,packaged_performance_validated=False)
    payload=json.dumps(result,separators=(',',':'),allow_nan=False)
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x') as f:f.write(payload)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('terrain','sources','out','inventory'):parser.add_argument('--'+name,type=Path,required=True)
    a=parser.parse_args();r=build(a.terrain,a.sources,a.out,a.inventory)
    print(json.dumps({k:v for k,v in r.items() if k not in ('chunks','meshes')},indent=2))
