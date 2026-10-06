"""Read-only source-observation traces against the normal saved FullReach map.

No replacement, asset save, cook, PIE or new geometry. This is not motion/FPS
acceptance or proof that any original observation represents a boulder.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import unreal

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def package_file(name):
    assert name.startswith('/Game/') and '..' not in name.split('/')
    return ROOT/'unreal/Content'/(name.removeprefix('/Game/')+'.uasset')


def main():
    probes_path = (ROOT/os.environ['RAFTSIM_IGNORED_GROUND_PROBES']).resolve()
    output = (ROOT/os.environ['RAFTSIM_IGNORED_GROUND_REPORT']).resolve()
    assert probes_path.is_relative_to(ROOT/'tmp') and output.is_relative_to(ROOT/'tmp') and not output.exists()
    probes = json.loads(probes_path.read_text())
    assert probes['schema'] == 'raftsim.ignored_ground_union_probes.v1' and len(probes['rows']) == 17
    protected = {probes_path: sha(probes_path)}
    for name, digest in probes['source_inputs'].items():
        path = (ROOT/name).resolve()
        assert path.is_relative_to(ROOT) and sha(path) == digest
        protected[path] = digest
    level = '/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach'
    assert probes['level'] == level
    map_file = ROOT/'unreal/Content/RaftSim/Maps/L_SouthForkAmerican_FullReach.umap'
    protected[map_file] = sha(map_file)
    assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(level)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    assert world.get_path_name().split('.')[0] == level
    descs = unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
    for d in descs:
        path = package_file(str(d.actor_package)); protected[path] = sha(path)
    points = [r['world_position_cm'] for r in probes['rows']]
    low = [min(p[i] for p in points)-100 for i in range(2)]
    high = [max(p[i] for p in points)+100 for i in range(2)]
    selected = [d for d in descs if d.native_class.get_name() == 'StaticMeshActor'
        and d.bounds.min.x <= high[0] and d.bounds.max.x >= low[0]
        and d.bounds.min.y <= high[1] and d.bounds.max.y >= low[1]]
    assert selected
    # Validate both source assets even if one cap's bounds miss the query box.
    # Bounds select additional possible occluders, not the identity witnesses.
    required = [d for d in descs if str(d.name) in probes['installed_actor_names']]
    assert len(required) == len(probes['installed_actor_names']), 'Missing installed source actor descriptor'
    selected += [d for d in required if d not in selected]
    unreal.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in selected])
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    actors = list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
    grounds = [a for a in actors if 'RaftSimPhysicalGround' in map(str, a.tags)]
    assert grounds
    native = []
    for row in probes['installed_meshes']:
        mesh = unreal.load_asset(row['asset']); assert mesh
        path = package_file(row['asset']); assert sha(path) == row['sha256']; protected[path] = sha(path)
        owners = [a for a in grounds if isinstance(a, unreal.StaticMeshActor) and a.static_mesh_component.static_mesh == mesh]
        assert len(owners) == 1, (row['asset'], len(owners), [(a.get_name(), str(a.tags)) for a in actors if a.get_name() in probes['installed_actor_names']])
        owner = owners[0]; p = owner.get_actor_location(); rot = owner.get_actor_rotation()
        assert [p.x,p.y,p.z] == probes['translation_cm'] and owner.get_actor_scale3d() == unreal.Vector(1,-1,1)
        assert max(abs(rot.pitch), abs(rot.yaw), abs(rot.roll)) < .00001
        proof = json.loads(unreal.RaftSimGroundSourceLibrary.audit_collision_source(mesh))
        assert proof['collision_source_sha256'] == row['native_source']['collision_source_sha256']
        assert proof['triangle_count'] == mesh.get_num_triangles(0) == row['native_source']['triangle_count']
        native.append(proof)
    for actor in grounds:
        if isinstance(actor, unreal.StaticMeshActor) and actor.static_mesh_component.static_mesh:
            path = package_file(actor.static_mesh_component.static_mesh.get_path_name().split('.')[0])
            protected[path] = sha(path)
    ignored = [a for a in actors if a not in grounds]
    results = []; failures = []
    for row in probes['rows']:
        p = unreal.Vector(*row['world_position_cm'])
        for complex_trace in (False, True):
            hit = unreal.SystemLibrary.line_trace_single(world, p+unreal.Vector(0,0,2000), p-unreal.Vector(0,0,2000),
                unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, complex_trace, ignored, unreal.DrawDebugTrace.NONE, False)
            v = hit.to_tuple() if hit else None
            result = dict(original_return_index=row['original_return_index'], trace_complex=complex_trace, hit=bool(v and v[0]))
            if not result['hit']:
                failures.append(dict(result, reason='no_hit'))
            else:
                q = v[5]; owner = next((a for a in v if isinstance(a, unreal.Actor)), None)
                error = math.sqrt((q.x-p.x)**2+(q.y-p.y)**2+(q.z-p.z)**2)
                result.update(hit_position_cm=[q.x,q.y,q.z], source_union_error_cm=error,
                    observation_minus_collision_m=row['observation_minus_union_m']+(p.z-q.z)/100.,
                    actor=owner.get_name() if owner else None,
                    mesh=owner.static_mesh_component.static_mesh.get_path_name() if isinstance(owner, unreal.StaticMeshActor) else None)
                if error > .1 or owner not in grounds:
                    failures.append(dict(result, reason='unexpected_union_height_or_owner'))
            results.append(result)
    for path, digest in protected.items():
        assert sha(path) == digest, 'Changed protected file: '+str(path)
    report = dict(schema='raftsim.ignored_ground_installed_union.v1', passed=not failures,
        rows=results, failures=failures, native_meshes=native, probes_sha256=sha(probes_path),
        level=level, protected_files={p.relative_to(ROOT).as_posix():d for p,d in protected.items()},
        saved_assets=False, geometry_changed=False, reconstructed_rocks_accepted=False,
        motion_verified=False, performance_accepted=False, scope=__doc__)
    with output.open('x') as f: json.dump(report, f, indent=2, allow_nan=False)
    assert not failures, 'Installed source-union mismatch; inspect report'
    unreal.log('Ignored-ground installed union:34 traces passed; no geometry mutation')


if __name__ == '__main__':
    try: main()
    finally: unreal.SystemLibrary.quit_editor()
