"""Derive fresh hydraulic core geometry from the retained terrain/rock union.

Original packets, captured masks and captured stages remain byte-identical.
This does not transfer evolved water to changed geometry or install a prop.
"""
import argparse
import copy
import json
from pathlib import Path
import numpy as np
from south_fork_rock_union import SourceRockUnion,sha

ROOT=Path(__file__).resolve().parents[2]
FIELDS=('bed_navd88_m','captured_surface_navd88_m','captured_water_mask','terrain_owner')


def union_fields(fields,center,union):
    if any(np.shape(fields[k])!=(80,80) for k in FIELDS):
        raise ValueError('Original 80 by 80 one-metre core required')
    offsets=np.arange(80,dtype=float)-40
    x,y=np.meshgrid(center[0]+offsets,center[1]+offsets)
    bed,changed=union.apply(x,y,fields['bed_navd88_m'])
    output={k:fields[k].copy() for k in FIELDS}
    output['bed_navd88_m']=bed
    output['terrain_owner'][changed]=5
    return output,changed


def prepare(base_flow,cap_manifest,output):
    output=Path(output).resolve();base_flow=Path(base_flow).resolve()
    if output.exists() or not output.is_relative_to(ROOT/'tmp'):
        raise ValueError('Fresh project tmp candidate directory required')
    flow=json.loads(base_flow.read_text());geometry_path=ROOT/flow['geometry_manifest']
    if sha(geometry_path)!=flow['geometry_manifest_sha256']:
        raise ValueError('Current hydraulic geometry dependency changed')
    geometry=json.loads(geometry_path.read_text())
    if not geometry['completed'] or geometry.get('terrain_union'):
        raise ValueError('Completed retained geometry, without an earlier union, required')
    if [r['name'] for r in geometry['regions']]!=flow['packages']:
        raise ValueError('Physical domain and state package order differ')
    cap_manifest=Path(cap_manifest).resolve();cap=json.loads(cap_manifest.read_text())
    origin=np.asarray(cap['origin_utm_and_vertical_datum_m'])
    union=SourceRockUnion(cap_manifest,ROOT,ROOT/cap['source_mesh_path'],origin[:2],origin[2])
    if geometry['vertical_datum_navd88_m']!=origin[2] or geometry['grid_spacing_m']!=1.:
        raise ValueError('Source union and hydraulic lattice/datum differ')
    result=copy.deepcopy(geometry);changes=[];checked=set();total=0
    centers={tuple(r['center_utm_m']) for r in geometry['regions']}
    if len(centers)!=len(geometry['regions']):raise ValueError('Overlapping hydraulic cores')
    observed=set()
    declared={(r['region'],r['edge']) for r in geometry['open_geometry_edges']}
    physical={(flow['packages'][p['tile_index']],p['edge']) for p in flow['boundary_probes']}
    if declared!=physical:raise ValueError('Geometry endpoints differ from current physical boundaries')
    # Validate ALL retained field provenance first; no outputs on bad inputs.
    for record in geometry['regions']:
        core_path=ROOT/record['geometry_file'];source_path=ROOT/record['source_geometry_file']
        if sha(core_path)!=record['geometry_sha256']:
            raise ValueError('Changed original core: '+record['name'])
        if source_path not in checked:
            if sha(source_path)!=record['source_geometry_sha256']:
                raise ValueError('Changed original source packet')
            checked.add(source_path)
        row,col=record['source_slice_row_column']
        with np.load(core_path,allow_pickle=False) as core,np.load(source_path,allow_pickle=False) as source:
            for key in FIELDS:
                if not np.array_equal(core[key],source[key][row:row+80,col:col+80]):
                    raise ValueError('Retained core differs from original source: '+key)
            water=core['captured_water_mask'];x,y=record['center_utm_m']
            for edge,delta,wet in [('west',(-80,0),water[:,0]),('east',(80,0),water[:,-1]),
                                  ('south',(0,-80),water[0,:]),('north',(0,80),water[-1,:])]:
                if (x+delta[0],y+delta[1]) not in centers and np.any(wet):
                    observed.add((record['name'],edge))
        total+=6400
    if observed!=declared:raise ValueError('Captured water crosses an undeclared exterior boundary')
    output.mkdir()
    for record in result['regions']:
        center=np.asarray(record['center_utm_m'])
        if np.any(center+39<union.lower) or np.any(center-40>union.upper):continue
        old_path=ROOT/record['geometry_file']
        with np.load(old_path,allow_pickle=False) as data:
            fields={k:data[k] for k in FIELDS}
        updated,changed=union_fields(fields,center,union)
        if not changed.any():continue
        path=output/(record['name']+'.npz')
        np.savez_compressed(path,**updated)
        delta=updated['bed_navd88_m'][changed]-fields['bed_navd88_m'][changed]
        changes.append(dict(name=record['name'],changed_cells=int(changed.sum()),
            bed_raise_range_m=[float(delta.min()),float(delta.max())],
            original_geometry_file=record['geometry_file'],original_geometry_sha256=record['geometry_sha256']))
        record.update(geometry_file=path.relative_to(ROOT).as_posix(),geometry_sha256=sha(path),
            copied_without_interpolation=False,terrain_union=union.identity,
            original_core_geometry_file=changes[-1]['original_geometry_file'],
            original_core_geometry_sha256=changes[-1]['original_geometry_sha256'])
        # Independently re-open every changed packet; compare exact source
        # roof evaluation and all untouched source fields before marking ready.
        with np.load(path,allow_pickle=False) as saved:
            expected,expected_changed=union_fields(fields,center,union)
            if not np.array_equal(expected_changed,changed) or any(
                    not np.array_equal(saved[k],expected[k]) for k in FIELDS):
                raise ValueError('Saved union differs from shared physical geometry')
    if not changes:raise ValueError('Rock candidate does not alter any hydraulic cell')
    result.update(terrain_union=union.identity,rock_cap_manifest=cap_manifest.relative_to(ROOT).as_posix(),
        retained_flow_manifest=base_flow.relative_to(ROOT).as_posix(),retained_flow_manifest_sha256=sha(base_flow),
        retained_geometry_manifest=geometry_path.relative_to(ROOT).as_posix(),
        retained_geometry_manifest_sha256=sha(geometry_path),
        hydraulic_state_solved=False,normal_map_integrated=False,completed=True,
        remaining_interior_wet_exterior_faces=0,new_exterior_wet_geometry_not_yet_audited=False,
        notes='Retained source fields plus explicit source-roof/vertical-flank solid union. Captured masks/stages unchanged. Requires a fresh hydraulic solve; not an exact-state restart.')
    manifest_path=output/'manifest.json';manifest_path.write_text(json.dumps(result,indent=2)+'\n')
    audit=dict(manifest_sha256=sha(manifest_path),passed=True,checked_core_count=len(result['regions']),
        checked_original_cell_count=total,changed_cores=changes,changed_cell_count=sum(r['changed_cells'] for r in changes),
        original_source_fields_exact_before_union=True,captured_masks_and_surfaces_unchanged=True,
        declared_endpoint_faces_match_current_flow=True,undeclared_captured_wet_exterior_faces=0,
        source_roof_sampler_and_saved_bed_match=True,original_sources_modified=False,
        native_collision_acceptance=False,hydraulic_state_solved=False,normal_map_integrated=False)
    (output/'source_exact_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    return audit


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-flow',type=Path,required=True)
    parser.add_argument('--cap-manifest',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(prepare(args.base_flow,args.cap_manifest,args.output),indent=2),flush=True)
