"""Reconstruct the shared physical crest on the existing fine carrier."""
from pathlib import Path
import hashlib
import json
import unreal

ROOT = Path(__file__).resolve().parents[2]
SOURCE = '/Game/RaftSim/Environment/SouthForkSurveyCandidate/M_RaftSim_LiveRiverSurface_StatefulFoamReview'
DEST = '/Game/RaftSim/Environment/SouthForkSurveyCandidate/M_RaftSim_LiveRiverSurface_StatefulCrestReview'
INCLUDE = '/Plugin/RaftSimWaterDetail/Private/RaftSimCrestSurfaceSample.ush'


def main():
    lib = unreal.MaterialEditingLibrary
    if unreal.EditorAssetLibrary.does_asset_exist(DEST):
        raise RuntimeError('Destination already exists; retain comparison evidence')
    source_path = ROOT / 'unreal/Content' / (SOURCE.removeprefix('/Game/') + '.uasset')
    source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
    material = unreal.EditorAssetLibrary.duplicate_asset(SOURCE, DEST)
    if material is None:
        raise RuntimeError('Duplicate failed')
    nodes = list(lib.get_material_expressions(material))
    def labelled(label):
        found = [n for n in nodes if isinstance(n, unreal.MaterialExpressionCustom)
                 and n.get_editor_property('description') == label]
        if len(found) != 1:
            raise RuntimeError('Expected one ' + label)
        return found[0]
    current = labelled('Authoritative macro band 0')
    previous = labelled('Previous rendered frame: Authoritative macro band 0')
    for node in (current, previous):
        node.set_editor_property('include_file_paths', [INCLUDE])
        node.set_editor_property('code', 'return RaftSimCrestMacroSample(Atlas,GridPosition,int2(Size.xy));')
    # Evaluate analytic slopes in the vertex stage, not a site loop per pixel.
    slope = lib.create_material_expression(material, unreal.MaterialExpressionCustom)
    slope.set_editor_property('description', 'Shared fine crest world slope correction')
    slope.set_editor_property('include_file_paths', [INCLUDE])
    slope.set_editor_property('code', 'return RaftSimCrestCorrection(Atlas,GridPosition,int2(Size.xy),false).yz;')
    slope.set_editor_property('output_type', unreal.CustomMaterialOutputType.CMOT_FLOAT2)
    slope.set_editor_property('inputs', current.get_editor_property('inputs'))
    for name, source in zip(lib.get_material_expression_input_names(current), lib.get_inputs_for_material_expression(material, current)):
        output = str(lib.get_input_node_output_name_for_material_expression(current, source))
        if not lib.connect_material_expressions(source, output, slope, str(name)):
            raise RuntimeError('Slope input failed: ' + str(name))
    interpolator = lib.create_material_expression(material, unreal.MaterialExpressionVertexInterpolator)
    if not lib.connect_material_expressions(slope, '', interpolator, 'VS'):
        raise RuntimeError('Vertex-only slope connection failed')
    normal = labelled('GPU macro normal with existing detail')
    pins = list(normal.get_editor_property('inputs'))
    pin = unreal.CustomInput(); pin.set_editor_property('input_name', 'CrestSlope'); pins.append(pin)
    normal.set_editor_property('inputs', pins)
    if not lib.connect_material_expressions(interpolator, '', normal, 'CrestSlope'):
        raise RuntimeError('Normal correction connection failed')
    normal.set_editor_property('code',
        'float3 n=Macro.xyz; n.xy-=n.z*CrestSlope; n*=rsqrt(max(dot(n,n),1.e-8)); '
        'float3 coarse=TransformWorldVectorToTangent(Parameters.TangentToWorld,n); '
        'return normalize(lerp(Base,coarse+Base-float3(0,0,1),Enable));')
    errors = lib.recompile_material(material)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    if errors:
        raise RuntimeError('Material compilation failed: ' + str(errors))
    if not unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False):
        raise RuntimeError('Save failed')
    if hashlib.sha256(source_path.read_bytes()).hexdigest() != source_hash:
        raise RuntimeError('Source changed')
    dest_path = ROOT / 'unreal/Content' / (DEST.removeprefix('/Game/') + '.uasset')
    report = dict(material=DEST, sha256=hashlib.sha256(dest_path.read_bytes()).hexdigest(),
                  source=SOURCE, unchanged_source_sha256=source_hash,
                  current_and_previous_crest=True, vertex_only_slope=True,
                  new_physical_amplitude=False, visual_accepted=False, performance_accepted=False)
    (ROOT / 'docs/reconstruction-review-2026-09-07/stateful-crest-material-setup.json').write_text(
        json.dumps(report, indent=2), encoding='utf-8')


if __name__ == '__main__':
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
