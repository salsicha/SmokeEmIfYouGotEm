"""Art-directed rainforest cover on the full-run Pacuare continuous terrain.

The same placement rules as the Chilko continuous dressing (deterministic
per-chunk candidates; 12 m from source water and from solved water; slopes
under 30 degrees; unknown support excluded), with the project's opaque
rainforest canopy, riparian shrub and ground-cover meshes. No surveyed trees,
species or crown positions are claimed. Source water is the IGN active
channel and the photographed wetted water of the stitched evidence.
"""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt, map_coordinates

from build_colorado_catalog_evidence import ROOT, sha
from build_colorado_continuous_dressing import candidates, terrain_support_slope
from build_chilko_continuous_dressing import eligible
from cooked_water_clearance import CookedWaterClearance
from export_colorado_continuous_terrain import LandscapeTriangles

RIVER_ID = 'pacuare_river_costa_rica'
MESH_ROOT = '/Game/RaftSim/Environment/PacuareRun/Vegetation/Meshes/'
MESHES = ['SM_RaftSim_Pacuare_CanopyTree_A_OpaqueV2', 'SM_RaftSim_Pacuare_CanopyTree_B_OpaqueV2',
          'SM_RaftSim_Pacuare_RiparianShrub_A_OpaqueV2', 'SM_RaftSim_Pacuare_RainforestGroundCover_A_OpaqueV2']


def source_clearance_sampler(source):
    evidence = json.loads(Path(source['manifest']).read_text())
    g = evidence['grid']
    with np.load(source['grid'], allow_pickle=False) as data:
        water = data['river'] | data['channel']
        # Cells no segment covers are unknown, not land: keep them out.
        unknown = ~np.isfinite(data['bed'])
    distances = distance_transform_edt(~water)
    distances[unknown] = np.nan

    def sample(xy):
        r = g['y_top'] - xy[:, 1] - .5
        c = xy[:, 0] - g['x0'] - .5
        covered = (r >= 0) & (r <= g['ny'] - 1) & (c >= 0) & (c <= g['nx'] - 1)
        clearance = np.full(len(xy), np.nan)
        clearance[covered] = map_coordinates(distances, [r[covered], c[covered]], order=1, prefilter=False,
                                             cval=np.nan) - np.sqrt(2)
        return clearance
    return sample, dict(evidence_manifest_sha256=source['manifest_sha256'], evidence_grid_sha256=source['grid_sha256'])


def build(runtime):
    runtime = runtime.resolve()
    runtime.relative_to(ROOT)
    manifest = json.loads((runtime / 'manifest.json').read_text())
    if (manifest.get('schema') != 'raftsim.continuous_runtime_candidate.v1' or
            manifest.get('river_id') != RIVER_ID or (runtime / 'REJECTED.json').exists()):
        raise ValueError('Screened continuous Pacuare runtime required')
    for name, digest in manifest['files_sha256'].items():
        path = (runtime / name).resolve()
        path.relative_to(runtime)
        if sha(path) != digest:
            raise ValueError('Changed runtime dependency')
    triangles = LandscapeTriangles(runtime / 'terrain')
    terrain = triangles.manifest
    source_clearance, source_receipt = source_clearance_sampler(terrain['evidence_source'])
    fields = runtime / 'cooked_flow_fields'
    flow = json.loads((fields / 'manifest.json').read_text())
    f = flow['grid']
    grid = dict(nx=f['nx'], ny=f['ny'], dx=f['dx_m'], dy=f['dy_m'], origin_x=f['origin_x_m'], origin_y=f['origin_y_m'])
    mapping = json.loads((runtime / 'coordinate_map.json').read_text())
    wet = np.load(fields / flow['bands'][0]['arrays']['wet_mask']['file'], allow_pickle=False, mmap_mode='r')
    cooked_clearance = CookedWaterClearance(mapping, terrain, grid, wet)
    origin = np.asarray(terrain['horizontal_origin_m'])
    chunks, total = [], 0
    for chunk in terrain['chunks']:
        corner = np.asarray(chunk['origin_m']) - [0, triangles.span]
        rows = candidates(corner, span=triangles.span, seed_prefix='pacuare-rainforest-v1', probability=.7)
        if not len(rows):
            continue
        xy = rows[:, :2]
        z = triangles.sample(xy)
        slope = terrain_support_slope(triangles.sample, xy, z)
        keep = eligible(z, slope, source_clearance(xy), cooked_clearance.sample(xy))
        instances = []
        for row, height in zip(rows[keep], z[keep]):
            world = (row[:2] - origin) * [100, -100]
            instances.append(dict(mesh=int(row[4]), location_cm=[*world.tolist(), (float(height) - terrain['vertical_datum_m']) * 100],
                                  yaw_deg=float(row[2]), scale=float(row[3])))
        if instances:
            chunks.append(dict(chunk=chunk['chunk'], instances=instances))
            total += len(instances)
    mesh_files = {}
    for name in MESHES:
        path = ROOT / 'unreal/Content' / Path((MESH_ROOT + name).removeprefix('/Game/')).with_suffix('.uasset')
        mesh_files[path.relative_to(ROOT).as_posix()] = sha(path)
    return dict(schema='raftsim.pacuare_continuous_dressing.v1', river_id=RIVER_ID,
        runtime_sha256=sha(runtime / 'manifest.json'), terrain_sha256=sha(runtime / 'terrain/manifest.json'),
        **source_receipt,
        source_policy='Art-directed rainforest canopy, riparian shrub and ground cover; not measured canopy, species or individual plants.',
        collision_policy='Nonblocking decorative vegetation; bank and rock collision remain native terrain.',
        minimum_water_clearance_m=12., maximum_slope_degrees=30.,
        slope_policy='Maximum of central gradient and eight one-sided one-metre cardinal/diagonal terrain offsets; unknown support excluded',
        meshes=[MESH_ROOT + n + '.' + n for n in MESHES], mesh_files_sha256=mesh_files,
        cull_start_cm=45000, cull_end_cm=65000, chunks=chunks, instance_count=total,
        rendered_validated=False, performance_validated=False)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    if a.out.exists():
        raise SystemExit('Fresh dressing output required')
    result = build(a.runtime)
    with a.out.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps(dict(instances=result['instance_count'], chunks=len(result['chunks']))))
