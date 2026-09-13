"""Join existing reconstruction evidence into an exact Unreal placement manifest.

This does not save a map or accept appearance, performance, hydraulic settling,
or final collision alignment. It verifies immutable inputs for scene assembly.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach'
SOURCE = ROOT/'unreal/SourceArt/RaftSim/SouthForkCompositeTerrain20260912'
REPORTS = ROOT/'unreal/Saved/RaftSimValidation'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(path.read_text())


def relative(path):
    return path.resolve().relative_to(ROOT).as_posix()


def asset_file(package):
    assert package.startswith('/Game/') and '..' not in package.split('/')
    return ROOT/'unreal/Content'/(package.removeprefix('/Game/')+'.uasset')


def validate_rapid_geometry_binding(composite, export, evidence):
    """A valid old import is not evidence for the current hydraulic terrain."""
    geometry = composite['registered_rapid_sha256']
    assert export['source_geometry_sha256'] == geometry, 'Render rapid differs from hydraulic rapid geometry'
    assert evidence['source_geometry_sha256'] == geometry, 'Collision evidence belongs to another rapid revision'


def prepare(runtime_export, inventory_path):
    inventory = read(inventory_path)
    assert inventory['level'] == '/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach'
    assert inventory['descriptor_count'] == len(inventory['descriptors'])
    assert inventory['descriptor_count'] > inventory['actor_count'], 'Must include unloaded partition actors'
    for name, digest in inventory['protected_files'].items():
        assert sha(ROOT/name) == digest, ('changed normal map/profile', name)
    for desc in inventory['descriptors']:
        assert sha(asset_file(desc['package'])) == desc['package_sha256'], desc['package']

    route_path = BASE/'playable_route/coordinate_map.json'
    hydraulic_path = BASE/'hydraulic_regions_context/coordinate_map.json'
    route, hydraulic = read(route_path), read(hydraulic_path)
    assert route['origin_utm_m'] == hydraulic['world_origin_utm_m']
    assert route['world_y_sign'] == hydraulic['world_y_sign'] == -1
    assert route['vertical_datum_m'] == hydraulic['vertical_datum_m'] == 220.
    route_report = read(BASE/'playable_route/integration.json')
    assert sha(route_path) == route_report['coordinate_map.json']['sha256']
    assert route['points'][-1][0] == route_report['route_length_m']
    contracts_path = BASE/'playable_route/session_contracts.json'
    contracts = read(contracts_path)
    assert contracts['coordinate_map_sha256'] == sha(route_path)
    assert contracts['coordinate_map'] == relative(route_path)
    assert contracts['source_route_extent_m'] == [0., route_report['route_length_m']]
    sessions = contracts['sessions']
    assert len(sessions) == 5 and len({item['id'] for item in sessions}) == 5
    assert sessions[-1]['id'] == 'south_fork_full_descent'
    assert all(item['id'] != 'troublemaker_challenge' for item in sessions)
    assert [sessions[0]['start_m'], sessions[3]['finish_m']] == contracts['playable_extent_m']
    for index, session in enumerate(sessions):
        assert 0. <= session['start_m'] < session['finish_m'] <= route_report['route_length_m']
        if index in (1, 2, 3):
            assert session['start_m'] == sessions[index-1]['finish_m']
    assert [sessions[-1]['start_m'], sessions[-1]['finish_m']] == contracts['playable_extent_m']

    material_report = read(REPORTS/'south-fork-composite-material-20260912.json')
    material = material_report['instance']
    assert sha(asset_file(material)) == material_report['instance_sha256']
    assert sha(asset_file(material_report['material'])) == material_report['material_sha256']
    placement_path = BASE/'playable_route/troublemaker_placement.json'
    placement = read(placement_path)
    assert sha(placement_path) == material_report['placement_sha256']
    assert placement['parent_scenario_id'] == 'south_fork_full_descent'
    assert placement['separate_menu_scenario'] is False

    actors = []
    for directory, report_name, expected in (
        ('Tiles', 'south-fork-composite-tiles-20260912.json', 390),
        ('ContextTiles1024m', 'south-fork-context-tiles-20260912.json', 51),
    ):
        source_path = SOURCE/directory/'manifest.json'
        source, report = read(source_path), read(REPORTS/report_name)
        assert report['completed'] and len(source['tiles']) == len(report['tiles']) == expected
        assert sha(source_path) == report['source_export_manifest_sha256']
        imported = {row['asset'].rsplit('/', 1)[1]: row for row in report['tiles']}
        for tile in source['tiles']:
            record = imported[tile['asset_name']]
            assert sha(asset_file(record['asset'])) == record['asset_sha256'], record['asset']
            assert tile['fbx_sha256'] == record['fbx_sha256']
            assert tile['triangle_count'] == record['triangle_count']
            assert tile['actor_translation_cm'] == record['actor_translation_cm']
            assert tile['actor_scale'] == [1., -1., 1.]
            assert record['collision_probe_count'] > 0 and record['maximum_collision_error_cm'] < .1
            actors.append(dict(asset=record['asset'], asset_sha256=record['asset_sha256'],
                role='coarse_terrain' if directory == 'Tiles' else 'captured_context',
                translation_cm=tile['actor_translation_cm'], scale=tile['actor_scale'],
                rotation_degrees=[0., 0., 0.], material_override=material,
                expected_triangle_count=tile['triangle_count'],
                export_manifest=relative(source_path),
                source_tile_sha256=tile['sha256'],
                collision_evidence=relative(REPORTS/report_name)))

    composite = read(BASE/'composite_terrain/manifest.json')
    assert sha(BASE/'composite_terrain/troublemaker_registered_source.npz') == composite['registered_rapid_sha256']
    for role, package, export_path, collision_report in (
        ('retained_rapid', '/Game/RaftSim/Environment/SouthForkReconstruction/Troublemaker/SM_TroublemakerCapturedGround',
         ROOT/'unreal/SourceArt/RaftSim/TroublemakerInferredRockFlanks20260912/manifest.json',
         REPORTS/'troublemaker-inferred-flanks-integration-20260912.json'),
        ('inferred_join', '/Game/RaftSim/Environment/SouthForkReconstruction/FullReach/SM_SouthForkTroublemakerJoin',
         SOURCE/'manifest.json', REPORTS/'south-fork-composite-seam-20260912.json'),
    ):
        export, evidence = read(export_path), read(collision_report)
        if role == 'retained_rapid':
            validate_rapid_geometry_binding(composite, export, evidence)
            assert evidence['mesh'] == package
            assert sha(asset_file(package)) == evidence['mesh_sha256'], 'Rapid collision proof is stale for the imported asset'
        assert sha(ROOT/export['fbx']) == export['fbx_sha256']
        assert export['source_geometry_sha256'] == evidence['source_geometry_sha256']
        assert evidence['collision_probe_count'] > 0 and evidence['maximum_collision_error_cm'] < .1
        actors.append(dict(asset=package, asset_sha256=sha(asset_file(package)), role=role,
            translation_cm=placement['translation_from_existing_rapid_world_cm'], scale=[1., -1., 1.],
            rotation_degrees=[0., 0., 0.], material_override=material,
            expected_triangle_count=export['triangle_count'], export_manifest=relative(export_path),
            source_geometry_sha256=export['source_geometry_sha256'], collision_evidence=relative(collision_report),
            combined_scene_collision_recheck_required=True))
    assert len(actors) == 443 and len({a['asset'] for a in actors}) == 443

    atlas_path = runtime_export/'atlas/manifest.json'
    stream_path = runtime_export/'streaming_manifest_verified.json'
    coverage, atlas = read(runtime_export/'source-coverage-verified.json'), read(atlas_path)
    exported = read(runtime_export/'export_audit.json')
    assert exported['completed']
    assert exported['source_manifest_sha256'] == hydraulic['source_geometry_regions_sha256']
    assert sha(BASE/'hydraulic_regions_context/manifest.json') == exported['source_manifest_sha256']
    assert atlas['schema'] == 'raftsim.cartesian_state_atlas.v1'
    assert atlas['source_elevation_datum_m'] == hydraulic['vertical_datum_m']
    assert atlas['grid_spacing_m'] == 1. and atlas['tile_shape'] == [80, 80]
    assert len(atlas['tiles']) == exported['atlas_tile_count']
    assert coverage['passed'] and not coverage['failed_rectangles']
    assert coverage['atlas_manifest_sha256'] == sha(atlas_path)
    assert coverage['streaming_manifest_sha256'] == sha(stream_path)
    assert read(stream_path)['live_window_extent_m'] == [224., 224.]
    for item in atlas['arrays'].values():
        assert item['shape'] == [len(atlas['tiles'])*80, 80] and item['dtype'] == '<f8'
        assert sha((atlas_path.parent/item['file']).resolve()) == item['sha256']
    return dict(schema='raftsim.south_fork.scene_assembly.v1',
        target_level=inventory['level'], scenario_id='south_fork_full_descent',
        rapid_has_no_scenario=True, map_inventory=relative(inventory_path),
        map_inventory_sha256=sha(inventory_path), existing_partition_actor_count=inventory['descriptor_count'],
        coordinate_frame=dict(origin_utm_m=route['origin_utm_m'], vertical_datum_m=220., world_y_sign=-1),
        route_coordinate_map=relative(route_path), route_sha256=sha(route_path),
        hydraulic_coordinate_map=relative(hydraulic_path), hydraulic_map_sha256=sha(hydraulic_path),
        route_length_m=route_report['route_length_m'],
        session_contracts=relative(contracts_path), session_contracts_sha256=sha(contracts_path),
        section_landmark_georeferencing_accepted=contracts['landmark_georeferencing_accepted'],
        runtime_streaming_manifest=relative(stream_path), streaming_sha256=sha(stream_path),
        atlas_manifest=relative(atlas_path), atlas_sha256=sha(atlas_path),
        source_time_seconds=atlas['source_time_seconds'], terrain_actors=actors,
        terrain_triangle_count=sum(a['expected_triangle_count'] for a in actors),
        source_provenance='Captured exposed terrain retained; submerged bed, join and missing appearance include documented inference.',
        map_saved=False, scene_accepted=False, settled_hydraulics=False,
        remaining=['combined scene collision/rapid vertex checks', 'restationed starts, finish and saved progression',
            'current-driven shared crests and shore/support consistency', 'normal scene material and motion review',
            'full-frame performance and release staging'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('runtime_export', type=Path)
    parser.add_argument('inventory', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    assert not args.output.exists(), 'Do not overwrite earlier assembly evidence'
    result = prepare(args.runtime_export.resolve(), args.inventory.resolve())
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'terrain_actors'}, indent=2))


if __name__ == '__main__':
    main()
