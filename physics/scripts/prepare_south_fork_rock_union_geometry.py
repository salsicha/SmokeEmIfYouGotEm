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
    bed,changed,owners=union.apply(x,y,fields['bed_navd88_m'],with_owner=True)
    output={k:fields[k].copy() for k in FIELDS}
    output['bed_navd88_m']=bed
    output['terrain_owner'][changed]=owners[changed]
    return output,changed


def retained_union(geometry,root):
    """Rebuild the previous geometry from its own dependencies, never the new cap."""
    if not geometry.get('terrain_union'):return None
    root=Path(root).resolve()
    path=(root/geometry['rock_cap_manifest']).resolve()
    if not path.is_relative_to(root):raise ValueError('Previous cap outside project')
    cap=json.loads(path.read_text());origin=np.asarray(cap['origin_utm_and_vertical_datum_m'])
    revision=geometry.get('terrain_revision_manifest')
    if revision is not None:
        revision=(root/revision).resolve()
        if not revision.is_relative_to(root):raise ValueError('Previous revision outside project')
    previous=SourceRockUnion(path,root,root/cap['source_mesh_path'],origin[:2],origin[2],revision)
    if previous.identity!=geometry['terrain_union']:
        raise ValueError('Previous union dependencies do not match current geometry')
    return previous


def prepare(base_flow,cap_manifest,output,terrain_revision=None,replace_union=False):
    output=Path(output).resolve();base_flow=Path(base_flow).resolve()
    if output.exists() or not output.is_relative_to(ROOT/'tmp'):
        raise ValueError('Fresh project tmp candidate directory required')
    flow=json.loads(base_flow.read_text());geometry_path=ROOT/flow['geometry_manifest']
    if sha(geometry_path)!=flow['geometry_manifest_sha256']:
        raise ValueError('Current hydraulic geometry dependency changed')
    geometry=json.loads(geometry_path.read_text())
    if not geometry['completed'] or (geometry.get('terrain_union') and terrain_revision is None and not replace_union):
        raise ValueError('Completed retained geometry, without an earlier union, required')
    if [r['name'] for r in geometry['regions']]!=flow['packages']:
        raise ValueError('Physical domain and state package order differ')
    cap_manifest=Path(cap_manifest).resolve();cap=json.loads(cap_manifest.read_text())
    origin=np.asarray(cap['origin_utm_and_vertical_datum_m'])
    previous_union=retained_union(geometry,ROOT)
    if replace_union and previous_union is None:
        raise ValueError('Replacement requires a verified existing union')
    if replace_union and geometry.get('terrain_revision_manifest'):
        retained_revision=(ROOT/geometry['terrain_revision_manifest']).resolve()
        if terrain_revision is not None and Path(terrain_revision).resolve()!=retained_revision:
            raise ValueError('Cap replacement must preserve the current bed revision')
        terrain_revision=retained_revision
    union=SourceRockUnion(cap_manifest,ROOT,ROOT/cap['source_mesh_path'],origin[:2],origin[2],terrain_revision)
    if previous_union is not None:
        if not replace_union and previous_union.identity['cap_manifest_sha256']!=sha(cap_manifest):
            raise ValueError('Revision must retain the exact current rock union')
        if previous_union.identity['parent_geometry_sha256']!=union.identity['parent_geometry_sha256']:
            raise ValueError('Replacement must retain the same source terrain')
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
            base_fields={key:source[key][row:row+80,col:col+80] for key in FIELDS}
            expected=union_fields(base_fields,np.asarray(record['center_utm_m']),previous_union)[0] if previous_union else base_fields
            for key in FIELDS:
                if not np.array_equal(core[key],expected[key]):
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
        if (np.any(center+39<union.lower) or np.any(center-40>union.upper)) and not record.get('terrain_union'):continue
        old_path=ROOT/record.get('original_core_geometry_file',record['geometry_file'])
        expected_old_sha=record.get('original_core_geometry_sha256',record['geometry_sha256'])
        if sha(old_path)!=expected_old_sha:raise ValueError('Retained pre-union core changed')
        row,col=record['source_slice_row_column']
        with np.load(ROOT/record['source_geometry_file'],allow_pickle=False) as source,np.load(old_path,allow_pickle=False) as old:
            fields={k:source[k][row:row+80,col:col+80] for k in FIELDS}
            if any(not np.array_equal(fields[k],old[k]) for k in FIELDS):
                raise ValueError('Pre-union core differs from exact source packet slice')
        updated,changed=union_fields(fields,center,union)
        if not changed.any():
            # A smaller replacement must remove the prior cap, not leave stale
            # raised cells or ownership outside the new footprint.
            record.update(geometry_file=old_path.relative_to(ROOT).as_posix(),
                          geometry_sha256=expected_old_sha,copied_without_interpolation=True)
            for key in ('terrain_union','original_core_geometry_file','original_core_geometry_sha256'):
                record.pop(key,None)
            continue
        path=output/(record['name']+'.npz')
        np.savez_compressed(path,**updated)
        delta=updated['bed_navd88_m'][changed]-fields['bed_navd88_m'][changed]
        changes.append(dict(name=record['name'],changed_cells=int(changed.sum()),
            bed_raise_range_m=[float(delta.min()),float(delta.max())],
            original_geometry_file=old_path.relative_to(ROOT).as_posix(),original_geometry_sha256=expected_old_sha))
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
    if terrain_revision is not None:
        result.update(terrain_revision_manifest=Path(terrain_revision).resolve().relative_to(ROOT).as_posix(),
            terrain_revision=union.terrain_revision.identity,
            notes='Explicit registered terrain revision, then the selected source-rock solid. Captured masks/stages and physical endpoints retained. Fresh solve required; no old-bed state transfer.')
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
    parser.add_argument('--terrain-revision',type=Path,
                        help='Explicit source-preserving registered-bed candidate; requires a fresh solve')
    parser.add_argument('--replace-union',action='store_true',
                        help='Verify and replace the previous cap while retaining its bed revision; fresh solve required')
    args=parser.parse_args()
    print(json.dumps(prepare(args.base_flow,args.cap_manifest,args.output,args.terrain_revision,args.replace_union),indent=2),flush=True)
