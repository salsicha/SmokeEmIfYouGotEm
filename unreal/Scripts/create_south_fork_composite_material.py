"""Create a full-river-frame ground material without changing source assets.

Registered rapid imagery/classification is used only inside its source domain.
Outside it, the existing procedural/scanned rock response is an appearance
prior, not an invented aerial survey. Map actors will override this material;
terrain mesh packages and collision remain immutable.
"""
import hashlib
import json
from pathlib import Path
import sys
import unreal

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from configure_playable_troublemaker_foam import graph_signature

SOURCE = '/Game/RaftSim/Environment/SouthForkReconstruction/Troublemaker'
DEST = '/Game/RaftSim/Environment/SouthForkReconstruction/FullReach'
REPORT = ROOT/'unreal/Saved/RaftSimValidation/south-fork-composite-material-20260912.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def asset_file(package):
    return ROOT/'unreal/Content'/(package.removeprefix('/Game/')+'.uasset')


def main():
    parent = SOURCE+'/M_TroublemakerCapturedGround'
    instance = SOURCE+'/MI_TroublemakerGround'
    destination = DEST+'/M_SouthForkCompositeGround'
    destination_instance = DEST+'/MI_SouthForkCompositeGround'
    assert not REPORT.exists(), 'Existing evidence requires inspection, not overwrite'
    assert not unreal.EditorAssetLibrary.does_asset_exist(destination)
    assert not unreal.EditorAssetLibrary.does_asset_exist(destination_instance)
    protected = {p: sha(asset_file(p)) for p in (parent, instance)}
    placement_path = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach/playable_route/troublemaker_placement.json'
    translation = json.loads(placement_path.read_text())['translation_from_existing_rapid_world_cm']
    assert translation[2] == 0
    lib = unreal.MaterialEditingLibrary
    material = unreal.EditorAssetLibrary.duplicate_asset(parent, destination)
    assert isinstance(material, unreal.Material)
    props = {k: getattr(unreal.MaterialProperty, 'MP_'+k) for k in ('NORMAL', 'ROUGHNESS', 'WORLD_POSITION_OFFSET')}
    before = {k: graph_signature(material, p) for k, p in props.items()}
    nodes = list(lib.get_material_expressions(material))
    uvs = [n for n in nodes if isinstance(n, unreal.MaterialExpressionCustom)
           and n.get_editor_property('output_type') == unreal.CustomMaterialOutputType.CMOT_FLOAT2
           and [str(p.get_editor_property('input_name')) for p in n.get_editor_property('inputs')] == ['P']
           and str(n.get_editor_property('code')).startswith('return float2((P.x*.01')]
    assert len(uvs) == 2, 'Expected only the original registered photo and class-map UV expressions'
    mask_uvs = [n for n in uvs if 'P.x*.01-(' in str(n.get_editor_property('code'))]
    assert len(mask_uvs) == 1
    for node in uvs:
        original = str(node.get_editor_property('code'))
        node.set_editor_property('code',
            f'P -= float3({translation[0]:.12f}, {translation[1]:.12f}, 0.0);\n'+original)
        node.set_editor_property('description', 'Full river world to retained rapid source frame')
    colors = [n for n in nodes if isinstance(n, unreal.MaterialExpressionCustom)
              and str(n.get_editor_property('description')) == 'Registered captured bank color V1']
    assert len(colors) == 1
    color = colors[0]
    inputs = list(color.get_editor_property('inputs'))
    pin = unreal.CustomInput()
    pin.set_editor_property('input_name', 'AuthorityUV')
    inputs.append(pin)
    color.set_editor_property('inputs', inputs)
    assert lib.connect_material_expressions(mask_uvs[0], '', color, 'AuthorityUV')
    original = str(color.get_editor_property('code'))
    color.set_editor_property('code',
        '// Clamped texture edges are not evidence outside the captured domain.\n'
        'Classes *= (all(AuthorityUV >= 0.0) && all(AuthorityUV <= 1.0)) ? 1.0 : 0.0;\n'+original)
    color.set_editor_property('description', 'Registered source color bounded in full river world V1')
    assert {k: graph_signature(material, p) for k, p in props.items()} == before
    lib.recompile_material(material)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    assert unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    output = unreal.EditorAssetLibrary.duplicate_asset(instance, destination_instance)
    assert isinstance(output, unreal.MaterialInstanceConstant)
    lib.set_material_instance_parent(output, material)
    assert unreal.EditorAssetLibrary.save_loaded_asset(output, only_if_is_dirty=False)
    for package, digest in protected.items():
        assert sha(asset_file(package)) == digest
    REPORT.write_text(json.dumps(dict(material=destination, instance=destination_instance,
        material_sha256=sha(asset_file(destination)), instance_sha256=sha(asset_file(destination_instance)),
        source_packages_unchanged=protected, placement_sha256=sha(placement_path),
        source_translation_cm=translation, uv_expression_count=len(uvs),
        source_classification_bounded=True, protected_graphs=before,
        geometry_collision_unchanged=True, normal_map_integrated=False,
        outside_source_appearance_is_inferred=True, visual_accepted=False), indent=2)+'\n')
    unreal.log(f'Full-river ground material prepared: {REPORT}')


if __name__ == '__main__':
    main()
