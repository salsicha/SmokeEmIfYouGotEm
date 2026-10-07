"""Art-directed dryland cover on registered terrain, never surveyed vegetation.

Uses existing first-party Colorado meshes. Source water and actual cooked water
both exclude placements; no geometry, water field or solid obstacle is changed.
"""
import argparse
import hashlib
import json
from collections import OrderedDict
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt, map_coordinates
from scipy.spatial import cKDTree

from build_colorado_catalog_evidence import ROOT, sha
from export_colorado_continuous_runtime import registered_queries
from export_colorado_continuous_terrain import LandscapeTriangles, load_sources

MESH_ROOT = '/Game/RaftSim/Environment/ColoradoRun/Vegetation/Meshes/'
MESHES = ['SM_RaftSim_Hance_DesertShrub_A_OpaqueV2',
          'SM_RaftSim_Hance_DesertShrub_B_OpaqueV2',
          'SM_RaftSim_Hance_DryGroundCover_A_OpaqueV2',
          'SM_RaftSim_Hance_DryGroundCover_B_OpaqueV2']


def candidates(corner, span=252., spacing=12., seed_prefix='colorado-dryland-v1', probability=.22):
    """Global integer-cell seed makes extension independent of chunk ordering."""
    if not np.isfinite([span,spacing,probability]).all() or min(span,spacing)<=0 or not 0<=probability<=1:
        raise ValueError('Invalid vegetation candidate sampling')
    lo = np.ceil(np.asarray(corner)/spacing).astype(int)
    hi = np.ceil((np.asarray(corner)+span)/spacing).astype(int)
    result = []
    for i in range(lo[0], hi[0]):
        for j in range(lo[1], hi[1]):
            digest = hashlib.sha256(f'{seed_prefix}:{i}:{j}'.encode()).digest()
            r = np.frombuffer(digest, dtype='<u4').astype(float)/2**32
            if r[0] < probability:
                result.append([i*spacing, j*spacing, 360*r[1], .65+.55*r[2], int(r[3]*4)])
    return np.asarray(result, dtype=float).reshape(-1, 5)


def eligible(height, slope, source_distance, water_distance):
    return (np.isfinite(height) & np.isfinite(slope) &
            (slope < np.tan(np.deg2rad(30))) &
            (source_distance >= 12.) & (source_distance <= 180.) &
            (water_distance >= 12.))


class SourceWaterClearance:
    """Conservative overlap minimum with only a few retained distance grids."""
    def __init__(self, sources, max_grids=2):
        if type(max_grids) is not int or max_grids <= 0:
            raise ValueError('Positive source-distance cache size required')
        self.sources = sources; self.max_grids = max_grids
        self.distances = OrderedDict()

    def sample(self, xy):
        xy = np.asarray(xy, dtype=float)
        distance = np.full(len(xy), np.inf)
        covered = np.zeros(len(xy), bool)
        for index, source in enumerate(self.sources):
            x, y, h, w = source['bounds']
            r, c = y-xy[:,1]-.5, xy[:,0]-x-.5
            valid = (r>=0)&(r<=h-1)&(c>=0)&(c<=w-1)
            if not valid.any(): continue
            # LazySourceGrid validates source identity even on cached reads.
            source['grid']['corner_east_north_m']
            if index not in self.distances:
                while len(self.distances) >= self.max_grids:
                    self.distances.popitem(last=False)
                wet = source['grid']['classified_water_mask'].astype(bool)
                self.distances[index] = distance_transform_edt(~wet)
            self.distances.move_to_end(index)
            value = map_coordinates(self.distances[index], [r[valid],c[valid]], order=1, prefilter=False)
            # A neighbouring crop must never conceal a closer classified bank.
            distance[valid] = np.minimum(distance[valid], value); covered |= valid
        return distance, covered


def build(runtime):
    runtime = runtime.resolve(); runtime.relative_to(ROOT)
    manifest = json.loads((runtime/'manifest.json').read_text())
    if manifest['schema'] != 'raftsim.colorado_continuous_runtime_candidate.v1' or (runtime/'REJECTED.json').exists():
        raise ValueError('Screened continuous runtime required')
    for name, digest in manifest['files_sha256'].items():
        path = (runtime/name).resolve(); path.relative_to(runtime)
        if sha(path) != digest: raise ValueError('Changed runtime dependency')
    triangles = LandscapeTriangles(runtime/'terrain')
    terrain = triangles.manifest
    for s in terrain['source_inputs']:
        if (sha(ROOT/s['evidence']/'manifest.json') != s['evidence_manifest_sha256'] or
                sha(ROOT/s['profile']) != s['profile_sha256']):
            raise ValueError('Changed terrain evidence registration')
    sources = load_sources([ROOT/s['evidence'] for s in terrain['source_inputs']],
                           [ROOT/s['profile'] for s in terrain['source_inputs']], bounded=True)
    source_clearance = SourceWaterClearance(sources)
    fields = runtime/'cooked_flow_fields'
    flow = json.loads((fields/'manifest.json').read_text()); g = flow['grid']
    grid = dict(nx=g['nx'], ny=g['ny'], dx=g['dx_m'], dy=g['dy_m'],
                origin_x=g['origin_x_m'], origin_y=g['origin_y_m'])
    mapping = json.loads((runtime/'coordinate_map.json').read_text())
    _, water_xy = registered_queries(mapping, terrain, grid)
    arrays = flow['bands'][0]['arrays']
    wet = np.load(fields/arrays['wet_mask']['file']).astype(bool)
    tree = cKDTree(water_xy[wet])
    origin = np.asarray(terrain['horizontal_origin_epsg6404_m'])
    chunks = []
    total = 0
    for chunk in terrain['chunks']:
        corner = np.asarray(chunk['origin_epsg6404_m'])-[0., 252.]
        rows = candidates(corner)
        xy = rows[:, :2]
        if not len(xy): continue
        z = triangles.sample(xy)
        dx = (triangles.sample(xy+[1.,0.])-triangles.sample(xy-[1.,0.]))/2
        dy = (triangles.sample(xy+[0.,1.])-triangles.sample(xy-[0.,1.]))/2
        distance, covered = source_clearance.sample(xy)
        # Subtract a cell diagonal so clearance is to wet cell area, not centres.
        actual_distance = tree.query(xy)[0]-np.hypot(grid['dx'],grid['dy'])
        keep = covered & eligible(z,np.hypot(dx,dy),distance,actual_distance)
        instances=[]
        for row, height in zip(rows[keep], z[keep]):
            world = (row[:2]-origin)*[100.,-100.]
            instances.append(dict(mesh=int(row[4]), location_cm=[*world.tolist(),(float(height)-terrain['vertical_datum_m'])*100.],
                                  yaw_deg=float(row[2]),scale=float(row[3])))
        if instances: chunks.append(dict(chunk=chunk['chunk'],instances=instances)); total+=len(instances)
    mesh_files={}
    for name in MESHES:
        path=ROOT/'unreal/Content'/Path((MESH_ROOT+name).removeprefix('/Game/')).with_suffix('.uasset')
        mesh_files[path.relative_to(ROOT).as_posix()]=sha(path)
    return dict(schema='raftsim.colorado_continuous_dressing.v1',
        terrain_sha256=sha(runtime/'terrain/manifest.json'),runtime_sha256=sha(runtime/'manifest.json'),
        source_policy='Art-directed sparse dryland vegetation; not surveyed species or individual plants.',
        collision_policy='Nonblocking decorative cover only; never rapid obstacles or bank collision.',
        minimum_water_clearance_m=12.,maximum_slope_degrees=30.,
        meshes=[MESH_ROOT+n+'.'+n for n in MESHES],mesh_files_sha256=mesh_files,
        cull_start_cm=45000,cull_end_cm=65000,chunks=chunks,instance_count=total,
        rendered_validated=False,performance_validated=False)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime',type=Path,required=True); p.add_argument('--out',type=Path,required=True)
    a=p.parse_args(); result=build(a.runtime)
    with a.out.open('x',encoding='utf-8') as stream: json.dump(result,stream,indent=2,allow_nan=False)
    print(json.dumps(dict(instances=result['instance_count'],chunks=len(result['chunks']))))
