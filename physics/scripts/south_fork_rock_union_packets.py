"""Explicit runtime source packets for the retained terrain / inferred rock union."""
import argparse
import copy
import json
from pathlib import Path
import numpy as np
from south_fork_rock_union import SourceRockUnion,sha

ROOT=Path(__file__).resolve().parents[2]
FIELDS=('bed_navd88_m','captured_surface_navd88_m','captured_water_mask','terrain_owner')


def packet_fields(fields,center,union):
    if any(np.shape(fields[k])!=(321,321) for k in FIELDS):
        raise ValueError('Complete original 321 by 321 packet required')
    x,y=np.meshgrid(center[0]+np.arange(321)-160,center[1]+np.arange(321)-160)
    bed,changed=union.apply(x,y,fields['bed_navd88_m'])
    result={k:fields[k].copy() for k in FIELDS};result['bed_navd88_m']=bed
    result['terrain_owner'][changed]=5
    return result,changed


def dependencies(geometry_path,root=ROOT):
    geometry_path=Path(geometry_path);geometry=json.loads(geometry_path.read_text())
    source_path=(root/geometry['regions'][0]['source_geometry_file']).parent/'manifest.json'
    if sha(source_path)!=geometry['source_manifest_sha256']:raise ValueError('Retained source manifest changed')
    source=json.loads(source_path.read_text())
    cap_path=root/geometry['rock_cap_manifest'];cap=json.loads(cap_path.read_text())
    origin=cap['origin_utm_and_vertical_datum_m']
    union=SourceRockUnion(cap_path,root,root/cap['source_mesh_path'],origin[:2],origin[2])
    if geometry['terrain_union']!=union.identity:raise ValueError('Different source union in hydraulic geometry')
    return geometry,source_path,source,union


def changed_record(original,path,values,changed,union,root):
    row=copy.deepcopy(original)
    row.update(geometry_file=path.relative_to(root).as_posix(),geometry_sha256=sha(path),
        retained_geometry_file=original['geometry_file'],retained_geometry_sha256=original['geometry_sha256'],
        terrain_union=union.identity,changed_union_samples=int(changed.sum()),
        owner_cell_counts={str(k):int(np.sum(values['terrain_owner']==k)) for k in (1,2,3,4,5)})
    return row


def prepare(geometry_path,output):
    geometry_path=Path(geometry_path).resolve();output=Path(output).resolve()
    if output.exists() or not output.is_relative_to(ROOT/'tmp'):raise ValueError('Fresh project tmp output required')
    geometry,source_path,source,union=dependencies(geometry_path)
    for record in source['regions']:
        if sha(ROOT/record['geometry_file'])!=record['geometry_sha256']:raise ValueError('Original source packet changed')
    output.mkdir();result=copy.deepcopy(source);rows=[]
    for original in source['regions']:
        center=np.asarray(original['center_utm_m'])
        if np.any(center+160<union.lower) or np.any(center-160>union.upper):
            rows.append(copy.deepcopy(original));continue
        with np.load(ROOT/original['geometry_file'],allow_pickle=False) as data:
            fields={k:data[k] for k in FIELDS}
        values,changed=packet_fields(fields,center,union)
        if not changed.any():rows.append(copy.deepcopy(original));continue
        path=output/(original['name']+'.npz');np.savez_compressed(path,**values)
        rows.append(changed_record(original,path,values,changed,union,ROOT))
    result.update(schema='raftsim.cartesian_source_packet_union.v1',regions=rows,
        retained_source_manifest=source_path.relative_to(ROOT).as_posix(),retained_source_manifest_sha256=sha(source_path),
        hydraulic_geometry_manifest=geometry_path.relative_to(ROOT).as_posix(),hydraulic_geometry_manifest_sha256=sha(geometry_path),
        terrain_union=union.identity,source_geometry_sha256=None,
        source_geometry_authority='Explicit retained terrain plus original-return roof / inferred-flank solid; not an unchanged captured source',
        original_sources_modified=False,hydraulic_state_solved=False,normal_map_integrated=False,
        full_reconstruction_accepted=False)
    path=output/'manifest.json';path.write_text(json.dumps(result,indent=2)+'\n')
    verify(path,geometry_path)
    audit=dict(passed=True,manifest_sha256=sha(path),retained_source_manifest_sha256=sha(source_path),
        packet_count=len(rows),changed_packet_count=sum('terrain_union' in r for r in rows),
        changed_packet_samples=sum(r.get('changed_union_samples',0) for r in rows),
        all_captured_masks_and_stages_unchanged=True,all_union_fields_recomputed_and_verified=True,
        original_sources_modified=False,settled_hydraulics=False,normal_map_integrated=False)
    (output/'packet_audit.json').write_text(json.dumps(audit,indent=2)+'\n');return audit


def verify(path,geometry_path,root=ROOT):
    """Hashes alone are insufficient: reconstruct every changed packet again."""
    path=Path(path);geometry_path=Path(geometry_path)
    geometry,source_path,original,union=dependencies(geometry_path,root)
    source=json.loads(path.read_text())
    if (source['schema']!='raftsim.cartesian_source_packet_union.v1' or
        source['hydraulic_geometry_manifest_sha256']!=sha(geometry_path) or
        source['retained_source_manifest_sha256']!=sha(source_path) or source['terrain_union']!=union.identity):
        raise ValueError('Runtime packets belong to a different source/cook union')
    for key in ('world_origin_utm_m','vertical_datum_navd88_m','grid_spacing_m'):
        if source[key]!=original[key]:raise ValueError('Runtime packet frame/lattice changed')
    if len(source['regions'])!=len(original['regions']):raise ValueError('Source packet coverage changed')
    for actual,retained in zip(source['regions'],original['regions']):
        rp=root/retained['geometry_file'];ap=root/actual['geometry_file']
        if sha(rp)!=retained['geometry_sha256'] or sha(ap)!=actual['geometry_sha256']:
            raise ValueError('Packet source dependency changed')
        center=np.asarray(retained['center_utm_m'])
        intersects=not (np.any(center+160<union.lower) or np.any(center-160>union.upper))
        if intersects:
            with np.load(rp,allow_pickle=False) as data:
                values,changed=packet_fields({k:data[k] for k in FIELDS},center,union)
            if changed.any():
                expected=changed_record(retained,ap,values,changed,union,root)
                if actual!=expected:raise ValueError('Changed packet identity/frame/provenance differs')
                with np.load(ap,allow_pickle=False) as saved:
                    if any(not np.array_equal(saved[k],values[k]) for k in FIELDS):
                        raise ValueError('Runtime packet differs from source-exact solid union')
                continue
        if actual!=retained:raise ValueError('Unaffected source packet changed')
    return source


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('geometry',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    print(json.dumps(prepare(a.geometry,a.output),indent=2),flush=True)
