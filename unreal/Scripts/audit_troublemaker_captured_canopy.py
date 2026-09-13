"""Read-only fresh-process validation of the saved playable canopy instances."""
import hashlib
import json
from pathlib import Path
import unreal

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/troublemaker/playable_canopy.json'
LEVEL = '/Game/RaftSim/Maps/L_SouthFork_Troublemaker'
data = json.loads(SOURCE.read_text())
assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(LEVEL)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
canopies = [a for a in actors if a.get_class().get_name() == 'RaftSimCapturedCanopyActor']
assert len(canopies) == 1
canopy = canopies[0]
assert canopy.get_editor_property('placement_source_sha256') == hashlib.sha256(SOURCE.read_bytes()).hexdigest()
assert canopy.get_actor_location() == unreal.Vector()
components = [canopy.get_editor_property(name) for name in ('canopy_a', 'canopy_b', 'canopy_c')]
errors = []
for form,component in enumerate(components):
    expected = [item for item in data['instances'] if item['form_index'] == form]
    assert component.get_instance_count() == len(expected)
    assert component.get_collision_enabled() == unreal.CollisionEnabled.NO_COLLISION
    bounds = component.static_mesh.get_bounding_box()
    for i,item in enumerate(expected):
        transform = component.get_instance_transform(i, True)
        position = transform.translation
        scale = transform.scale3d
        x,y,z = item['location_cm']
        err = max(abs(position.x-x),abs(position.y-y),abs(position.z+bounds.min.z*scale.z-z),
                  abs((bounds.max.z-bounds.min.z)*scale.z-item['height_m']*100))
        assert err < .1, (i,err)
        errors.append(err)
registry = unreal.AssetRegistryHelpers.get_asset_registry()
registry.search_all_assets(synchronous_search=True)
options = unreal.AssetRegistryDependencyOptions(include_soft_package_references=True, include_hard_package_references=True)
seen = set(); pending = [LEVEL]
while pending:
    package = pending.pop()
    if package in seen or not package.startswith('/Game/'):
        continue
    assert not package.startswith('/Game/RaftSim/Maps/Review/')
    assert not package.startswith('/Game/RaftSim/Environment/SouthForkSurveyCandidate/')
    seen.add(package)
    pending.extend(str(p) for p in registry.get_dependencies(package,options))
assert sum('CrownFamilyV3_' in p and '/Meshes/' in p for p in seen) == 3
output = ROOT/'unreal/Saved/RaftSimValidation/troublemaker-canopy-fresh-audit-20260912.json'
output.write_text(json.dumps({'fresh_process':True, 'saved_instance_count':len(errors),
    'maximum_transform_or_height_error_cm':max(errors), 'canopy_collision_enabled':False,
    'no_never_cook_dependencies':True, 'game_dependencies':sorted(seen)},indent=2)+'\n')
unreal.log(f'Fresh playable canopy audit passed: {len(errors)} instances;{len(seen)} dependencies')
