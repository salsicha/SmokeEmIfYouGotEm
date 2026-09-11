"""Create an opt-in, code-native ripple-normal candidate; do not touch the map."""
from pathlib import Path
import hashlib
import json
import unreal

ROOT = Path(__file__).resolve().parents[2]
SOURCE = '/Game/RaftSim/Environment/SouthForkSurveyCandidate/M_RaftSim_LiveRiverSurface_SurfaceLitReview'
DEST = '/Game/RaftSim/Environment/SouthForkSurveyCandidate/M_RaftSim_LiveRiverSurface_CurrentNormalReview'


def main():
    version2 = '-RaftSimSurveyCurrentNormalV2Review' in unreal.SystemLibrary.get_command_line()
    destination = DEST + 'V2' if version2 else DEST
    if unreal.EditorAssetLibrary.does_asset_exist(destination):
        raise RuntimeError('Review destination exists; preserve the prior experiment')
    source = unreal.load_asset(SOURCE)
    if not isinstance(source, unreal.Material) or not source.get_editor_property('tangent_space_normal'):
        raise RuntimeError('Expected the isolated tangent-space surface-lit material')
    immutable = [ROOT/'unreal/Content/RaftSim/Maps/Review/SouthForkSurveyPlayable.umap',
        ROOT/'unreal/Content/RaftSim/Environment/SouthForkSurveyCandidate/M_RaftSim_LiveRiverSurface_SurfaceLitReview.uasset']
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in immutable}
    material = unreal.EditorAssetLibrary.duplicate_asset(SOURCE, destination)
    if material is None:
        raise RuntimeError('Material duplication failed')
    lib = unreal.MaterialEditingLibrary
    expressions = lib.get_material_expressions(material)
    displacements = [e for e in expressions if isinstance(e, unreal.MaterialExpressionCollectionParameter)
        and str(e.get_editor_property('parameter_name')) == 'RaftSimFoamAdvectionMeters']
    strengths = [e for e in expressions if isinstance(e, unreal.MaterialExpressionScalarParameter)
        and str(e.get_editor_property('parameter_name')) == 'LiveRippleStrength']
    if not displacements or len(strengths) != 1:
        raise RuntimeError('Missing existing current integral or ripple strength')
    uv = lib.create_material_expression(material, unreal.MaterialExpressionTextureCoordinate)
    uv.set_editor_property('coordinate_index', 0)
    uv.set_editor_property('u_tiling', 1.0)
    uv.set_editor_property('v_tiling', 1.0)
    inputs = [('RiverUV', uv), ('FlowDisplacement', displacements[0]), ('Strength', strengths[0])]
    pins = []
    for name, _ in inputs:
        pin = unreal.CustomInput()
        pin.set_editor_property('input_name', name)
        pins.append(pin)
    code_path = ROOT/'unreal/Shaders/Private'/('RaftSimCurrentSurfaceNormalV2.hlsl' if version2 else 'RaftSimCurrentSurfaceNormal.hlsl')
    code = code_path.read_text(encoding='utf-8')
    normal = lib.create_material_expression(material, unreal.MaterialExpressionCustom)
    normal.set_editor_property('description', 'Survey current-carried aperiodic ripple normal ' + ('V2' if version2 else 'V1'))
    normal.set_editor_property('code', code)
    normal.set_editor_property('output_type', unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    normal.set_editor_property('inputs', pins)
    for name, expression in inputs:
        if not lib.connect_material_expressions(expression, '', normal, name):
            raise RuntimeError(f'Cannot connect {name}')
    if not lib.connect_material_property(normal, '', unreal.MaterialProperty.MP_NORMAL):
        raise RuntimeError('Cannot connect the normal output')
    lib.recompile_material(material)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    if not unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False):
        raise RuntimeError('Candidate save failed')
    for path, sha in hashes.items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest() != sha:
            raise RuntimeError(f'Unexpected immutable change: {path}')
    report = dict(schema='raftsim.survey.current_normal_review.v1', material=destination,
        source_material=SOURCE, code_sha256=hashlib.sha256(code.encode()).hexdigest(),
        unchanged=hashes, geometry_modified=False, physics_modified=False,
        description='Shading-only aperiodic derivatives using the existing integrated current.',
        visual_accepted=False, performance_accepted=False, production_accepted=False)
    (ROOT/'docs/reconstruction-review-2026-09-07'/('current-normal-v2-setup.json' if version2 else 'current-normal-setup.json')).write_text(
        json.dumps(report, indent=2), encoding='utf-8')
    unreal.log('Survey current-normal candidate saved; runtime review required')


if __name__ == '__main__':
    main()
