"""One-metre full-route water geometry on buffered native Landscape triangles.

Fresh construction, no resampling/copying of old water arrays. The entire
playable route and all three captured hydraulic arms remain in the domain.
"""
import argparse
import json
from pathlib import Path
import shutil

import numpy as np

from build_futaleufu_continuous_water_domain import (
    ROOT, LandscapeTriangles, FutaleufuBed, sha, cell_centres,
    initial_fields, connected_tiles, observe_branches)
from export_futaleufu_corridor_terrain import chunk_indices


def build(sources, network, profile, terrain, output):
    sources,network,profile,terrain,output = [Path(p).resolve() for p in (sources,network,profile,terrain,output)]
    output.relative_to(ROOT)
    if output.exists(): raise ValueError('Fresh buffered water output required')
    if shutil.disk_usage(ROOT).free<42*1024**3: raise ValueError('40 GiB reserve plus construction allowance required')
    t = LandscapeTriangles(terrain)
    if (t.manifest.get('river_id')!='futaleufu_river_chile' or t.spacing!=2. or t.span!=252.
            or not t.manifest.get('hydraulic_buffer_terrain')):
        raise ValueError('Reviewed buffered Futaleufu terrain required')
    bed = FutaleufuBed(sources,profile,network,depth_m=1.8)
    for k,v in bed.receipt.items():
        evidence=t.manifest['evidence_source']
        agrees=(all(evidence.get(k,{}).get(p)==h for p,h in v.items()) if k=='sources_sha256' else evidence.get(k)==v)
        if not agrees: raise ValueError('Water differs from encoded terrain construction: '+k)
    pins={ROOT/p:h for p,h in t.manifest['evidence_source']['sources_sha256'].items()}
    for p in (terrain/'manifest.json',Path(__file__).resolve(),
              ROOT/'unreal/Scripts/build_futaleufu_continuous_water_domain.py',
              ROOT/'physics/scripts/export_colorado_catalog_runtime.py'):
        pins[p]=sha(p)
    def verify():
        for p,h in pins.items():
            p.relative_to(ROOT)
            if sha(p)!=h: raise ValueError('Changed buffered water dependency: '+str(p))
        t.verify_unchanged()
    verify()
    indices=chunk_indices(bed.lines,t.origin,200.,2.)
    if not set(indices).issubset(t.by_index): raise ValueError('Full hydraulic corridor leaves captured terrain')
    output.mkdir(parents=True)
    masks={};rows=[]
    for index in sorted(indices):
        if shutil.disk_usage(ROOT).free<40*1024**3: raise ValueError('Disk reserve reached; retain partial output')
        xy=cell_centres(index,t.origin,spacing=1.)
        actual=t.sample(xy);v=bed.sample(xy.reshape(-1,2))
        stage=v['reference_m'].reshape(actual.shape);owned=v['bed_owned'].reshape(actual.shape)
        depth,wet=initial_fields(actual,stage,owned)
        name='tile_%d_%d.npz'%index
        np.savez_compressed(output/name,bed_m=actual,reference_stage_m=stage,initial_depth_m=depth,owned=owned,wet=wet)
        masks[index]=wet
        rows.append(dict(chunk=list(index),file=name,sha256=sha(output/name),owned_cells=int(owned.sum()),
            wet_cells=int(wet.sum()),owned_dry_cells=int((owned&~wet).sum()),max_depth_m=float(depth.max())))
        if len(rows)%8==0: print(f'Buffered water tiles {len(rows)}/{len(indices)}',flush=True)
    components,offset,counts=connected_tiles(masks)
    observations,common=observe_branches(bed,components,offset,t.origin,1.)
    np.savez_compressed(output/'components.npz',components=components,cell_offset=offset)
    verify()
    result=dict(schema='raftsim.futaleufu_initial_cartesian_water.v1',
        scope='Full buffered initial water geometry only; no discharge, throughflow, boat or native gameplay acceptance',
        terrain_manifest_sha256=t.manifest_sha256,
        sources_sha256={p.relative_to(ROOT).as_posix():h for p,h in pins.items()},
        horizontal_origin_m=t.origin.tolist(),horizontal_crs='EPSG:32718',vertical_reference='EGM2008',
        spacing_m=1.,terrain_spacing_m=2.,tile_cells=[252,252],rows_increase='north',wet_threshold_m=.05,
        tile_count=len(rows),wet_cells=int(counts[1:].sum()),component_count=len(counts)-1,
        largest_components=[dict(id=int(i),cells=int(counts[i])) for i in np.argsort(counts[1:])[::-1][:20]+1],
        common_route_components=common,sampled_cross_sections_share_component=bool(common),
        dry_cross_sections=[r for r in observations if not r['wet_components']],observations=observations,
        tiles=rows,components_sha256=sha(output/'components.npz'),construction_assumptions=bed.parameters,
        boundary_faces_authored=False,terrain_modified=False,engine_installed=False)
    (output/'manifest.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('tile_count','wet_cells','component_count','common_route_components','dry_cross_sections')}),flush=True)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('sources','network','profile','terrain','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();build(a.sources,a.network,a.profile,a.terrain,a.out)
