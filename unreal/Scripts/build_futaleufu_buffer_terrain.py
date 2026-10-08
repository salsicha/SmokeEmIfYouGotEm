"""Bounded hydraulic-buffer terrain candidate; never overwrites the native map.

Reuses the production inferred bed, encoding and 37-probe triangle safeguard.
Every unaffected chunk is copied byte-for-byte and all shared edges validated.
"""
import argparse
import copy
import json
from pathlib import Path
import shutil

import numpy as np
import shapely
from PIL import Image
from shapely.ops import substring

from build_futaleufu_continuous_water_domain import ROOT, LandscapeTriangles, sha
from futaleufu_corridor_bed import FutaleufuBed
from export_futaleufu_corridor_terrain import TerrainBed, encode, RESERVE
from extend_futaleufu_terrain_context import lattice
from chilko_triangle_ownership import preserve_triangle_support
from export_colorado_continuous_terrain import write_png_u16


def candidate_indices(lines, lengths, origin, span):
    if len(lines)!=3 or len(lengths)!=3 or not np.isfinite(lengths).all() or min(lengths)<300:
        raise ValueError('Three complete captured buffers required')
    arms = [substring(line,0,length) if i<2 else substring(line,line.length-length,line.length)
            for i,(line,length) in enumerate(zip(lines,lengths))]
    # The production bed's ownership radius is 256 m; include triangle support
    # and a full extra metre beyond that, not merely the inferred bank ribbon.
    area = shapely.union_all(arms).buffer(260.)
    lower = np.floor((np.array(area.bounds[:2])-origin)/span).astype(int)
    upper = np.floor((np.array(area.bounds[2:])-origin)/span).astype(int)
    return {(i,j) for i in range(lower[0],upper[0]+1) for j in range(lower[1],upper[1]+1)
            if area.intersects(shapely.box(*(origin+np.array([i,j])*span),
                                         *(origin+np.array([i+1,j+1])*span)))}


def build(sources, network, profile, terrain, output):
    sources,network,profile,terrain,output = [Path(p).resolve() for p in (sources,network,profile,terrain,output)]
    output.relative_to(ROOT)
    if output.exists(): raise ValueError('Fresh buffer terrain candidate required')
    parent = LandscapeTriangles(terrain)
    if (parent.manifest.get('river_id')!='futaleufu_river_chile' or parent.spacing!=2.
            or parent.manifest['landscape']['height_base_m']!=0.
            or parent.manifest['landscape']['height_range_m']!=2400.):
        raise ValueError('Existing 2 m Futaleufu terrain and common encoding required')
    bed = FutaleufuBed(sources,profile,network,depth_m=1.8)
    model = TerrainBed(bed)
    m = json.loads((profile/'manifest.json').read_text())
    lengths = [m['hydraulic_buffers']['branches'][n]['length_m'] for n in bed.arrays]
    selected = candidate_indices(bed.lines,lengths,parent.origin,parent.span)
    if not selected.issubset(parent.by_index): raise ValueError('Buffer influence leaves captured terrain chunks')
    if shutil.disk_usage(ROOT).free<RESERVE+2*1024**3: raise ValueError('40 GiB reserve plus candidate capacity required')
    pins = copy.deepcopy(bed.receipt['sources_sha256'])
    for rel,h in parent.manifest['evidence_source']['sources_sha256'].items():
        if rel in pins and pins[rel]!=h: raise ValueError('Parent and buffer source conflict')
        pins[rel]=h
    for p in (Path(__file__).resolve(),terrain/'manifest.json',
              ROOT/'physics/scripts/chilko_triangle_ownership.py',
              ROOT/'physics/scripts/export_futaleufu_corridor_terrain.py',
              ROOT/'physics/scripts/extend_futaleufu_terrain_context.py',
              ROOT/'physics/scripts/export_colorado_continuous_terrain.py'):
        pins[p.relative_to(ROOT).as_posix()]=sha(p)
    def verify():
        for rel,h in pins.items():
            if sha(ROOT/rel)!=h: raise ValueError('Changed buffer terrain input: '+rel)
    verify()
    output.mkdir(parents=True)
    chunks = copy.deepcopy(parent.manifest['chunks']); changed=[]; evaluated=[]
    for c in chunks:
        index=tuple(c['chunk'])
        if shutil.disk_usage(ROOT).free<RESERVE: raise ValueError('Disk reserve reached; retain partial candidate')
        for key,digest in (('heightfield','sha256'),('source_receipt','source_receipt_sha256')):
            if sha(terrain/c[key])!=c[digest]: raise ValueError('Parent chunk changed')
        if index in selected:
            xy=lattice(index,parent.origin,parent.spacing)
            result=preserve_triangle_support(model,xy,model.sample(xy),spacing_m=parent.spacing)
            encoded=encode(result['height_m'])
            with Image.open(terrain/c['heightfield']) as img: original=np.asarray(img)
            delta=encoded.astype(np.int32)-original.astype(np.int32)
            different=delta!=0
            receipt=dict(chunk=list(index),changed_vertices_including_shared_edges=int(different.sum()),
                maximum_encoded_height_change_m=float(abs(delta).max()*2400/65535),
                maximum_inferred_cut_m=float(np.max(result['source_height_m']-result['height_m'])),
                triangle_support_vetoes=int(result['inference_support_veto'].sum()))
            evaluated.append(receipt)
            if different.any():
                write_png_u16(output/c['heightfield'],encoded)
                np.savez_compressed(output/c['source_receipt'],**result)
                c['sha256']=sha(output/c['heightfield']);c['source_receipt_sha256']=sha(output/c['source_receipt'])
                changed.append(receipt)
            else:
                for key in ('heightfield','source_receipt'): shutil.copyfile(terrain/c[key],output/c[key])
            print('Buffer terrain '+str(len(evaluated))+'/'+str(len(selected))+': '+json.dumps(receipt),flush=True)
        else:
            for key in ('heightfield','source_receipt'): shutil.copyfile(terrain/c[key],output/c[key])
    verify();parent.verify_unchanged()
    result=copy.deepcopy(parent.manifest)
    result.update(chunks=chunks,evidence_source=copy.deepcopy(bed.receipt),
        engine_validated=False,vegetation_complete=False,full_river_complete=False,
        scope='Buffered inferred terrain candidate; not installed, cooked, or accepted in packaged gameplay')
    result['evidence_source']['sources_sha256']=pins
    # Parent statistics describe the retained snapshot, not this modified one.
    for key in ('context_extension','inferred_vertices_including_shared_edges','support_vetoes_including_shared_edges',
                'maximum_inferred_cut_m','maximum_height_quantization_error_m'):
        result.pop(key,None)
    result['geographic_scope']['branch_lengths_m']={n:float(l.length) for n,l in zip(bed.arrays,bed.lines)}
    result['hydraulic_buffer_terrain']=dict(parent_manifest_sha256=parent.manifest_sha256,
        evaluated_chunks=evaluated,changed_chunks=changed,unchanged_byte_identical_chunks=len(chunks)-len(changed),
        influence_radius_m=260.,production_ownership_radius_m=256.,
        native_map_modified=False,canopy_revalidation_required=True)
    (output/'manifest.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    # This independently decodes all PNGs and checks exact shared edges.
    LandscapeTriangles(output).verify_unchanged()
    print(json.dumps(dict(chunks=len(chunks),evaluated=len(evaluated),changed=len(changed),shared_edges_exact=True)),flush=True)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('sources','network','profile','terrain','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();build(a.sources,a.network,a.profile,a.terrain,a.out)
