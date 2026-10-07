"""Art-directed conifer/shrub cover on Chilko's actual source-backed terrain.

No surveyed individual trees or species locations are claimed. Source-supported
water, mapped planform core, solved water, steep ground and missing terrain all
exclude plants. Existing first-party opaque temperate meshes are reused.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from scipy.ndimage import distance_transform_edt,map_coordinates
from scipy.spatial import cKDTree

from build_colorado_catalog_evidence import ROOT,sha
from build_colorado_continuous_dressing import candidates
from export_colorado_continuous_runtime import registered_queries
from export_colorado_continuous_terrain import LandscapeTriangles

MESH_ROOT='/Game/RaftSim/Environment/TemperateRivers/Vegetation/Meshes/'
MESHES=['SM_RaftSim_Temperate_ConiferTree_A_OpaqueV1','SM_RaftSim_Temperate_ConiferTree_B_OpaqueV1',
        'SM_RaftSim_Temperate_RiparianShrub_A_OpaqueV1','SM_RaftSim_Temperate_RiparianShrub_B_OpaqueV1']


def eligible(z,slope,source_distance,solved_distance):
    return (np.isfinite(z)&np.isfinite(slope)&np.isfinite(source_distance)&np.isfinite(solved_distance)&
            (slope<np.tan(np.deg2rad(30)))&(source_distance>=12)&(source_distance<=350)&(solved_distance>=12))


def build(runtime):
    runtime=runtime.resolve();runtime.relative_to(ROOT)
    manifest=json.loads((runtime/'manifest.json').read_text())
    if (manifest.get('schema')!='raftsim.continuous_runtime_candidate.v1' or
            manifest.get('river_id')!='chilko_river_bc' or (runtime/'REJECTED.json').exists()):
        raise ValueError('Screened continuous Chilko runtime required')
    for name,digest in manifest['files_sha256'].items():
        path=(runtime/name).resolve();path.relative_to(runtime)
        if sha(path)!=digest:raise ValueError('Changed runtime dependency')
    triangles=LandscapeTriangles(runtime/'terrain');terrain=triangles.manifest
    source=terrain['evidence_source']
    for key in ('manifest','grid'):
        if sha(Path(source[key]))!=source[key+'_sha256']:raise ValueError('Changed terrain evidence')
    evidence=json.loads(Path(source['manifest']).read_text());g=evidence['grid']
    with np.load(source['grid'],allow_pickle=False) as data:
        source_water=data['river']|data['channel']|data['mapped_planform_core']
    distances=distance_transform_edt(~source_water)
    fields=runtime/'cooked_flow_fields';flow=json.loads((fields/'manifest.json').read_text());f=flow['grid']
    grid=dict(nx=f['nx'],ny=f['ny'],dx=f['dx_m'],dy=f['dy_m'],origin_x=f['origin_x_m'],origin_y=f['origin_y_m'])
    mapping=json.loads((runtime/'coordinate_map.json').read_text())
    _,water_xy=registered_queries(mapping,terrain,grid)
    wet=np.load(fields/flow['bands'][0]['arrays']['wet_mask']['file'],allow_pickle=False).astype(bool)
    if not wet.any():raise ValueError('No solved water for vegetation exclusion')
    tree=cKDTree(water_xy[wet]);origin=np.asarray(terrain['horizontal_origin_m']);chunks=[];total=0
    for chunk in terrain['chunks']:
        corner=np.asarray(chunk['origin_m'])-[0,252]
        rows=candidates(corner,seed_prefix='chilko-conifer-shrub-v1',probability=.55)
        if not len(rows):continue
        xy=rows[:,:2];z=triangles.sample(xy)
        sx=(triangles.sample(xy+[1,0])-triangles.sample(xy-[1,0]))/2
        sy=(triangles.sample(xy+[0,1])-triangles.sample(xy-[0,1]))/2
        r=g['y_top']-xy[:,1]-.5;c=xy[:,0]-g['x0']-.5
        covered=(r>=0)&(r<=g['ny']-1)&(c>=0)&(c<=g['nx']-1)
        clearance=np.full(len(rows),np.nan)
        # Subtract the full source-cell diagonal for a conservative distance
        # to water area, not just a possibly more distant cell centre.
        clearance[covered]=map_coordinates(distances,[r[covered],c[covered]],order=1,prefilter=False)-np.sqrt(2)
        solved=tree.query(xy)[0]-np.hypot(grid['dx'],grid['dy'])
        keep=eligible(z,np.hypot(sx,sy),clearance,solved);instances=[]
        for row,height in zip(rows[keep],z[keep]):
            world=(row[:2]-origin)*[100,-100]
            instances.append(dict(mesh=int(row[4]),location_cm=[*world.tolist(),(float(height)-terrain['vertical_datum_m'])*100],
                                  yaw_deg=float(row[2]),scale=float(row[3])))
        if instances:chunks.append(dict(chunk=chunk['chunk'],instances=instances));total+=len(instances)
    mesh_files={}
    for name in MESHES:
        path=ROOT/'unreal/Content'/Path((MESH_ROOT+name).removeprefix('/Game/')).with_suffix('.uasset')
        mesh_files[path.relative_to(ROOT).as_posix()]=sha(path)
    return dict(schema='raftsim.chilko_continuous_dressing.v1',river_id='chilko_river_bc',
        runtime_sha256=sha(runtime/'manifest.json'),terrain_sha256=sha(runtime/'terrain/manifest.json'),
        evidence_manifest_sha256=source['manifest_sha256'],evidence_grid_sha256=source['grid_sha256'],
        source_policy='Art-directed conifer and riparian shrub cover; not measured canopy, species or individual plants.',
        collision_policy='Nonblocking decorative vegetation; bank and rock collision remain native terrain.',
        minimum_water_clearance_m=12.,maximum_slope_degrees=30.,
        meshes=[MESH_ROOT+n+'.'+n for n in MESHES],mesh_files_sha256=mesh_files,
        cull_start_cm=45000,cull_end_cm=65000,chunks=chunks,instance_count=total,
        rendered_validated=False,performance_validated=False)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--runtime',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():raise SystemExit('Fresh dressing output required')
    result=build(a.runtime)
    with a.out.open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2,allow_nan=False)
    print(json.dumps(dict(instances=result['instance_count'],chunks=len(result['chunks']))))
