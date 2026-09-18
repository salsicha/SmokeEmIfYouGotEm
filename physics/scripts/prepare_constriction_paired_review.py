"""Seal an unaccepted source-extension PIE review; never a release descriptor."""
import argparse
import json
import math
from pathlib import Path
from prepare_south_fork_joint_preview import Dependencies, asset_file, require, verify_audits, verify_native_state, add_cap_dependencies
from south_fork_rock_union import sha

ROOT=Path(__file__).resolve().parents[2]
LEVEL='/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach'
SCHEMA='raftsim.source_supported_paired_review.v1'


def verify_union_evidence(geometry,probes,collision):
    require(probes['schema']=='raftsim.constriction_installed_union_probes.v1','Separate source-extension contract required')
    require(geometry['terrain_revision']==probes['terrain_revision']==collision['terrain_revision'], 'Different terrain revision')
    require(geometry['terrain_union']['terrain_revision']==geometry['terrain_revision'],'Different hydraulic union')
    require(collision['assets']==probes['assets'],'Different native assets')
    require(collision['failures']==[] and collision['sampled_full_map_union_verified'] is True and
        collision['hydraulic_state_verified'] is True and collision['fresh_saved_candidate_reload_verified'] is True,
        'Native source/collision/water verification required')
    require(collision['position_tolerance_cm']==.1 and collision['saved_assets'] is False and
        collision['saved_levels'] is False and collision['duplicate_ground_added'] is False,'Changed collision/installation contract')
    require(collision['candidate_translation_cm']==probes['translation_cm'],'Different engine translation')
    for role,expected in probes['assets'].items():
        actual=collision['native_sources'][role]
        require(actual['available'] is True and actual['allow_cpu_access'] is True and
            actual['collision_source_sha256']==expected['native_source_sha256'] and
            actual['triangle_count']==expected['triangle_count'],'Native source differs: '+role)


def validate(path,root=ROOT):
    deps=Dependencies(root);record=deps.read(path)
    require(record['schema']==SCHEMA and record['target_level']==LEVEL and record['candidate'] is True and
        record['production_promoted'] is False and record['settled_hydraulics'] is False,'Explicit unaccepted PIE review required')
    station=record['review_start_station_m']
    require(type(station) in (int,float) and math.isfinite(station) and 0<=station<=33334,'Finite full-reach review station required')
    for name,digest in record['dependencies'].items():deps.add(deps.root/name,digest)
    def read(key):
        require(record[key] in record['dependencies'],'Unbound evidence: '+key)
        return deps.read(deps.root/record[key])
    geometry,probes,collision=read('geometry_manifest'),read('union_probes'),read('collision_audit')
    verify_union_evidence(geometry,probes,collision)
    require(collision['source_probe_sha256']==deps.hashes[record['union_probes']],'Different collision probes')
    require(collision['geometry_manifest_sha256']==deps.hashes[record['geometry_manifest']],'Different collision geometry')
    atlas=read('atlas_manifest');stream=read('streaming_manifest');expected=read('runtime_expectations')
    verify_audits(atlas,read('snapshot_audit'),read('bank_audit'),read('coverage_audit'),
        deps.hashes[record['atlas_manifest']],deps.hashes[record['streaming_manifest']])
    require(atlas['terrain_union']==geometry['terrain_union'],'Different atlas geometry')
    require(read('flow_input_manifest')['geometry_manifest_sha256']==deps.hashes[record['geometry_manifest']],'Different flow geometry')
    require(expected['source_probe_sha256']==deps.hashes[record['union_probes']] and
        collision['native_runtime']['expectation_sha256']==deps.hashes[record['runtime_expectations']],'Different field expectations')
    require(expected['coordinate_map']==record['coordinate_map'] and
        expected['coordinate_map_sha256']==deps.hashes[record['coordinate_map']],'Different hydraulic coordinate frame')
    verify_native_state(collision,deps.hashes[record['atlas_manifest']],atlas['source_time_seconds'],
        record['initial_fields_manifest'],deps.hashes[record['initial_fields_manifest']],record['window_center_m'],
        deps.hashes[record['geometry_manifest']],sum(bool(r.get('terrain_union')) for r in geometry['regions'])*6400)
    require(record['source_time_seconds']==atlas['source_time_seconds'],'Different review time')
    windows=[w for w in stream['windows'] if w['cooked_fields_manifest']==record['initial_fields_manifest']]
    x,y=record['window_center_m']
    require(len(stream['windows'])==799 and len(windows)==1 and any(r[0]<=x<=r[2] and r[1]<=y<=r[3]
        for r in windows[0]['valid_live_center_bounds_m']),'Initial center outside audited stream coverage')
    for role,asset in probes['assets'].items():deps.add(asset_file(asset['asset'],deps.root),asset['package_sha256'])
    require(deps.hashes[record['map_file']]==probes['map_sha256'],'Saved map changed')
    return record,collision,probes


def prepare(args):
    from south_fork_rock_union_packets import dependencies
    output=args.output.resolve();require(not output.exists() and output.is_relative_to(ROOT/'tmp'),'Fresh tmp descriptor required')
    deps=Dependencies();export=args.export.resolve()
    probes=deps.read(args.probes);collision=deps.read(args.collision)
    geometry_path=ROOT/probes['geometry_manifest'];geometry,source_path,source,union=dependencies(geometry_path)
    verify_union_evidence(geometry,probes,collision)
    expected=deps.read(args.expected);atlas_path=export/'atlas/manifest.json';atlas=deps.read(atlas_path)
    stream_path=export/'streaming_manifest_coverage_checked.json';stream=deps.read(stream_path)
    for row in stream['windows']:
        packet_path=ROOT/row['cooked_fields_manifest'];packet=deps.read(packet_path)
        for band in packet['bands']:
            shared=band['shared_cartesian_state']
            require((packet_path.parent/shared['manifest']).resolve()==atlas_path and shared['sha256']==sha(atlas_path),'Different shared state')
            for meta in band['arrays'].values():deps.add((packet_path.parent/meta['file']).resolve(),meta['sha256'])
    for meta in atlas['arrays'].values():deps.add((atlas_path.parent/meta['file']).resolve(),meta['sha256'])
    for row in geometry['regions']:deps.add(ROOT/row['geometry_file'],row['geometry_sha256'])
    revision=geometry['terrain_revision']
    deps.add(ROOT/revision['manifest'],revision['manifest_sha256']);deps.add(ROOT/revision['mesh_path'],revision['revised_geometry_sha256'])
    for item in revision['source_dependencies'].values():
        if isinstance(item,dict) and 'path' in item:deps.add(ROOT/item['path'],item['sha256'])
    deps.add(source_path,geometry['source_manifest_sha256'])
    cap=deps.read(ROOT/geometry['rock_cap_manifest'],union.identity['cap_manifest_sha256'])
    add_cap_dependencies(deps,cap)
    for asset in probes['assets'].values():deps.add(asset_file(asset['asset']),asset['package_sha256'])
    material=asset_file(collision['material_asset']);deps.add(material)
    route=source_path.parents[1]/'playable_route/coordinate_map.json'
    require(route.is_file(),'Original full-reach progress route required')
    files=dict(geometry_manifest=geometry_path,union_probes=args.probes,collision_audit=args.collision,
        runtime_expectations=args.expected,flow_input_manifest=args.flow,atlas_manifest=atlas_path,
        streaming_manifest=stream_path,initial_fields_manifest=ROOT/expected['fields_manifest'],
        coordinate_map=ROOT/expected['coordinate_map'],route_coordinate_map=route,
        snapshot_audit=args.snapshot,bank_audit=args.banks,coverage_audit=args.coverage,
        map_file=ROOT/'unreal/Content/RaftSim/Maps/L_SouthForkAmerican_FullReach.umap')
    record=dict(schema=SCHEMA,target_level=LEVEL,candidate=True,production_promoted=False,settled_hydraulics=False,
        review_start_station_m=args.station,window_center_m=expected['window_center_m'],source_time_seconds=atlas['source_time_seconds'],
        **{key:deps.add(path) for key,path in files.items()},dependencies=deps.hashes,
        linked_cpp_preview_loader_exercised=False,semantic_classification_accepted=False,visual_accepted=False,performance_accepted=False)
    # Re-read and validate the saved record using the exact preplay validator.
    # A failed validation remains a clearly unaccepted local descriptor.
    output.write_text(json.dumps(record,indent=2)+'\n');validate(output)
    print(json.dumps(dict(descriptor=str(output.relative_to(ROOT)),sha256=sha(output),dependencies=len(deps.hashes)),indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('export',type=Path)
    for name in ('probes','collision','expected','flow','snapshot','banks','coverage','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--station',type=float,required=True);prepare(p.parse_args())
