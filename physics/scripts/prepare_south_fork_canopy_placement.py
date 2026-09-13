"""Rebind existing evidence-constrained canopy to the rebuilt full river.

No new tree inventory/species claims, random scatter, terrain edits or water
changes. Original dry-ground roots must still match the current rapid triangles.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from south_fork_geometry_source import load_registered_mesh

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09'
GEOMETRY_SHA = '8bdf1a586e7bd2536eaf25a982763efd9e5a558e7172fd7897b8ae0ecc8fe06b'
FORMS = ('SpreadingMature', 'CompactRiverEdge', 'AsymmetricCompetition')
PREFIX = '/Game/RaftSim/Environment/SouthForkFullReach/Canopy/Meshes/SM_RaftSim_SouthForkInteriorLiveOakCrownFamilyV3_'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def translated_roots(instances, translation):
    positions = np.asarray([row['location_cm'] for row in instances], dtype=float)
    translation = np.asarray(translation, dtype=float)
    if positions.ndim != 2 or positions.shape[1] != 3 or translation.shape != (3,):
        raise ValueError('Three-dimensional canopy positions and translation required')
    if not np.isfinite(positions).all() or not np.isfinite(translation).all():
        raise ValueError('Finite canopy coordinates required')
    # Input already reflects north into Unreal -Y. Do NOT reflect it again.
    return positions+translation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError('Preserve earlier placement evidence')
    source_path = BASE/'troublemaker/playable_canopy.json'
    placement_path = BASE/'full_reach/playable_route/troublemaker_placement.json'
    geometry_path = BASE/'full_reach/composite_terrain/troublemaker_registered_source.npz'
    composite_path = geometry_path.with_name('manifest.json')
    source = json.loads(source_path.read_text())
    placement = json.loads(placement_path.read_text())
    composite = json.loads(composite_path.read_text())
    assert source['world_y_sign'] == -1 and not source['tree_inventory_surveyed']
    assert not source['terrain_or_hydraulic_geometry_modified']
    assert placement['parent_scenario_id'] == 'south_fork_full_descent' and not placement['separate_menu_scenario']
    assert placement['rotation_degrees'] == [0., 0., 0.] and placement['scale'] == [1., 1., 1.]
    for name, digest in source['sources'].items():
        path = (ROOT/name).resolve()
        assert path.is_relative_to(ROOT) and sha(path) == digest, name
    assert sha(geometry_path) == composite['registered_rapid_sha256'] == GEOMETRY_SHA
    mesh, sampler = load_registered_mesh(geometry_path)
    instances = source['instances']
    assert len(instances) == source['instance_count'] == 1268
    assert len({row['id'] for row in instances}) == len(instances)
    roots = np.asarray([row['location_cm'] for row in instances])/100.
    ground, normals = sampler.sample(roots[:, 0], -roots[:, 1], with_normals=True)
    errors = np.abs(ground-roots[:, 2])*100.
    assert np.all(errors <= .1), ('Existing canopy root no longer matches current source', float(errors.max()))
    rr = np.floor((mesh['nominal_north_axis_m'][0]+.25+roots[:, 1])/.5).astype(int)
    cc = np.floor((roots[:, 0]-mesh['nominal_east_axis_m'][0]+.25)/.5).astype(int)
    assert np.all(rr>=4) and np.all(rr+4<mesh['authority'].shape[0])
    assert np.all(cc>=4) and np.all(cc+4<mesh['authority'].shape[1])
    for dr in range(-4, 5):
        for dc in range(-4, 5):
            assert np.all(mesh['authority'][rr+dr, cc+dc] == 1), 'Captured dry collar changed'
    assert np.all(normals[:, 2] >= .55)
    world_roots = translated_roots(instances, placement['translation_from_existing_rapid_world_cm'])
    translated = []
    for row, location in zip(instances, world_roots):
        assert row['form_index'] in (0, 1, 2) and row['support_return_count'] >= 12
        assert 3.5 <= row['height_m'] <= 30. and row['ground_authority'] == 1
        translated.append(dict(row, world_root_cm=location.tolist()))
    assets = []
    for form in FORMS:
        package = PREFIX+form
        path = ROOT/'unreal/Content'/(package.removeprefix('/Game/')+'.uasset')
        assets.append(dict(package=package, sha256=sha(path)))
    result = dict(schema='raftsim.south_fork.full_river_canopy_placement.v1',
        level='/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach', scenario_id='south_fork_full_descent',
        retired_source_level=source['normal_playable_level'], source_canopy=str(source_path.relative_to(ROOT)),
        source_canopy_sha256=sha(source_path), source_geometry_sha256=GEOMETRY_SHA,
        dependencies={str(p.relative_to(ROOT)): sha(p) for p in (source_path, placement_path, geometry_path, composite_path)},
        world_y_sign=-1, translation_cm=placement['translation_from_existing_rapid_world_cm'],
        rotation_degrees=[0., 0., 0.], scale=[1., 1., 1.], instance_count=len(translated),
        maximum_current_source_root_error_cm=float(errors.max()), current_dry_collar_checks=len(instances)*81,
        original_instances_unchanged=True, source_dates_coincident=False, tree_inventory_surveyed=False,
        species_and_trunk_positions_measured=False, appearance=source['appearance'],
        collision='Visual non-colliding canopy; solid tree obstacles remain unverified',
        terrain_or_hydraulic_geometry_modified=False, no_rapid_scenario=True,
        photoreal_accepted=False, runtime_integration_verified=False, assets=assets, instances=translated)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({key: value for key, value in result.items() if key not in ('instances', 'dependencies')}, indent=2))


if __name__ == '__main__':
    main()
