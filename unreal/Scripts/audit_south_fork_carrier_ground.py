"""Read-only combined ground collision at exact captured water-source vertices."""
import csv
import hashlib
import json
import math
from pathlib import Path
import unreal

ROOT = Path(__file__).resolve().parents[2]
CAPTURE = ROOT/'tmp/south-fork-dry-rock-motion-v1-20260914.json'
OUTPUT = ROOT/'unreal/Saved/RaftSimValidation/south-fork-carrier-ground-v2-20260914.json'
LEVEL = '/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def package_file(package):
    assert package.startswith('/Game/') and '..' not in package.split('/')
    return ROOT/'unreal/Content'/(package.removeprefix('/Game/')+'.uasset')


def main():
    assert not OUTPUT.exists(), 'Preserve prior audit'
    metadata = json.loads(CAPTURE.read_text(encoding='utf-8-sig'))
    assert metadata['schema'] == 'raftsim.submitted_carrier_shape.v2'
    sign = metadata['world_y_sign']; assert sign in (-1, 1)
    source_path = Path(str(CAPTURE)+'.source.csv')
    with source_path.open(encoding='utf-8-sig', newline='') as stream:
        source = list(csv.DictReader(stream))
    assert len(source) == metadata['source_nx']*metadata['source_ny']
    focus = metadata['focus_x_cm'], metadata['focus_y_cm']
    selected = []
    for index, row in enumerate(source):
        assert int(row['id']) == index
        x, y = float(row['field_x_m'])*100, float(row['field_y_m'])*sign*100
        if math.hypot(x-focus[0], y-focus[1]) <= 3000:
            selected.append((row, x, y))
    vertices_path = Path(str(CAPTURE)+'.vertices.csv')
    triangles_path = Path(str(CAPTURE)+'.triangles.csv')
    with vertices_path.open(encoding='utf-8-sig', newline='') as stream:
        vertices = list(csv.DictReader(stream))
    with triangles_path.open(encoding='utf-8-sig', newline='') as stream:
        referenced = {int(value) for row in csv.DictReader(stream) for value in row.values()}
    assert len(vertices) == metadata['active_vertices'] and max(referenced) < len(vertices)
    nx, ny = metadata['source_nx'], metadata['source_ny']
    x0, y0 = float(source[0]['field_x_m']), float(source[0]['field_y_m'])
    dx = float(source[1]['field_x_m'])-x0
    dy = float(source[nx]['field_y_m'])-y0
    assert dx > 0 and dy > 0
    rendered = []
    for index in sorted(referenced):
        vertex = vertices[index]; assert int(vertex['id']) == index
        x, y = float(vertex['x_cm']), float(vertex['y_cm'])
        if math.hypot(x-focus[0], y-focus[1]) > 3000: continue
        gx, gy = (x*.01-x0)/dx, (y*.01*sign-y0)/dy
        assert 0 <= gx <= nx-1 and 0 <= gy <= ny-1
        c, r = min(math.floor(gx), nx-2), min(math.floor(gy), ny-2)
        fx, fy = gx-c, gy-r
        corners = [source[r*nx+c], source[r*nx+c+1], source[(r+1)*nx+c], source[(r+1)*nx+c+1]]
        weights = [(1-fx)*(1-fy), fx*(1-fy), (1-fx)*fy, fx*fy]
        bed = sum(w*(float(q['source_bed_plus_depth_m'])-float(q['source_depth_m'])) for w, q in zip(weights, corners))*100
        stage = float(vertex['carrier_z_cm'])+float(vertex['detail_cm'])
        rendered.append((index, x, y, bed, stage, all(int(q['clipping_wet']) for q in corners)))
    protected = [ROOT/'unreal/Content/RaftSim/Maps/L_SouthForkAmerican_FullReach.umap',
                 CAPTURE, source_path, vertices_path, triangles_path]
    profile = ROOT/'unreal/Saved/SaveGames/RaftSimVerticalSlice.sav'
    if profile.exists(): protected.append(profile)
    before = {str(path): sha(path) for path in protected}
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    assert levels.load_level(LEVEL)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    assert world.get_path_name().split('.')[0] == LEVEL
    descriptors = unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
    assert descriptors
    packages = {str(d.actor_package): sha(package_file(str(d.actor_package))) for d in descriptors}
    relevant = [d for d in descriptors if d.native_class.get_name() == 'StaticMeshActor'
                and d.bounds.min.x <= focus[0]+3200 and d.bounds.max.x >= focus[0]-3200
                and d.bounds.min.y <= focus[1]+3200 and d.bounds.max.y >= focus[1]-3200]
    assert relevant
    unreal.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in relevant])
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    ground = [actor for actor in actors if 'RaftSimPhysicalGround' in map(str, actor.tags)]
    assert ground
    ignored = [actor for actor in actors if actor not in ground]
    ground_rows = []
    for actor in ground:
        mesh = actor.static_mesh_component.static_mesh if isinstance(actor, unreal.StaticMeshActor) else None
        ground_rows.append(dict(actor=actor.get_name(), mesh=mesh.get_path_name() if mesh else None))
        if mesh:
            path = package_file(mesh.get_path_name().split('.')[0])
            before[str(path)] = sha(path)
    config = [actor for actor in actors if actor.get_class().get_name() == 'RaftSimRiverWaterConfig']
    assert len(config) == 1
    configuration = {name: str(config[0].get_editor_property(name)) for name in
                     ('streaming_manifest_path', 'coordinate_map_path', 'flow_band')}
    rows = []
    queries = [('source', int(row['id']), x, y,
                (float(row['source_bed_plus_depth_m'])-float(row['source_depth_m']))*100,
                float(row['source_bed_plus_depth_m'])*100, bool(int(row['clipping_wet']))) for row, x, y in selected]
    queries += [('submitted', *entry) for entry in rendered]
    for kind, identifier, x, y, bed, stage, wet in queries:
        hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, bed+10000),
            unreal.Vector(x, y, bed-10000), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
            False, ignored, unreal.DrawDebugTrace.NONE, False)
        values = hit.to_tuple() if hit else None
        record = dict(query_kind=kind, vertex_id=identifier, world_xy_cm=[x, y], sampled_bed_cm=bed,
                      captured_stage_cm=stage, height_above_sampled_bed_cm=stage-bed,
                      captured_clipping_wet=int(wet), hit=bool(values and values[0]))
        if record['hit']:
            z = values[5].z
            owner = next((value for value in values if isinstance(value, unreal.Actor)), None)
            record.update(ground_z_cm=z, ground_minus_sampled_bed_cm=z-bed,
                          captured_stage_above_ground_cm=stage-z,
                          hit_actor=owner.get_name() if owner else None)
        rows.append(record)
    for path, digest in before.items():
        assert sha(Path(path)) == digest, ('Protected file changed', path)
    for package, digest in packages.items():
        assert sha(package_file(package)) == digest, ('Saved actor changed', package)
    hits = [row for row in rows if row['hit']]
    assert hits
    errors = sorted(abs(row['ground_minus_sampled_bed_cm']) for row in hits)
    wet = [row for row in hits if row['captured_clipping_wet']]
    groups = {}
    for kind in ('source', 'submitted'):
        values = [row for row in hits if row['query_kind'] == kind]
        differences = sorted(abs(row['ground_minus_sampled_bed_cm']) for row in values)
        assert differences
        wet_values = [row for row in values if row['captured_clipping_wet']]
        groups[kind] = dict(queries=sum(row['query_kind'] == kind for row in rows), hits=len(values),
            median_absolute_bed_error_cm=differences[len(differences)//2],
            p95_absolute_bed_error_cm=differences[math.ceil(.95*len(differences))-1],
            maximum_absolute_bed_error_cm=differences[-1], fully_wet_footprint_points=len(wet_values),
            fully_wet_points_below_ground=sum(row['captured_stage_above_ground_cm'] < 0 for row in wet_values))
    result = dict(accepted=False, level=LEVEL, configuration=configuration, groups=groups,
        source_capture_sha256=before[str(CAPTURE)], source_csv_sha256=before[str(source_path)],
        captured_world_seconds=metadata['world_seconds'], radius_m=30, query_points=len(rows),
        hit_points=len(hits), missing_points=len(rows)-len(hits), wet_hit_points=len(wet),
        absolute_bed_error_cm=dict(median=errors[len(errors)//2], p95=errors[math.ceil(.95*len(errors))-1], maximum=errors[-1]),
        wet_points_with_ground_above_captured_stage=sum(row['captured_stage_above_ground_cm'] < 0 for row in wet),
        ground_actors=ground_rows, queried_partition_actors=[str(d.name) for d in relevant],
        protected_sha256=before, protected_actor_packages=packages, saved_nothing=True, probes=rows,
        scope='Combined tagged physical ground in the saved normal map, queried with the existing simple trace path at exact source vertices and actually referenced submitted water vertices. Source queries use captured state stage; submitted queries use carrier plus paired CPU detail, not raw physical depth. Submitted bed reference is bilinear interpolation of the captured source bed; fully-wet flag requires all four source corners. Includes dry points and reports missing hits. Discrepancy is not by itself proof that captured terrain is wrong. No render visibility, actual collision traversal, subcell convergence or full-scene acceptance.')
    with OUTPUT.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    unreal.log(f'Combined captured-carrier ground audit: {OUTPUT}')


if __name__ == '__main__':
    main()
