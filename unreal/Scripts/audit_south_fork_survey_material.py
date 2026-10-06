"""Read the serialized review material without rebuilding or saving assets."""
from pathlib import Path
import hashlib
import json
import unreal

ROOT=Path(__file__).resolve().parents[2]
ASSET='/Game/RaftSim/Environment/SouthForkSurveyCandidate/M_RaftSim_LiveRiverSurface_SurfaceLitReview'
material=unreal.load_asset(ASSET)
if not isinstance(material,unreal.Material):raise RuntimeError('Missing review material')
lib=unreal.MaterialEditingLibrary
expressions=lib.get_material_expressions(material)
scalars={str(e.get_editor_property('parameter_name')):e.get_editor_property('default_value')
    for e in expressions if isinstance(e,unreal.MaterialExpressionScalarParameter)}
custom=[dict(name=e.get_name(),description=e.get_editor_property('description'),
             code=e.get_editor_property('code'))
    for e in expressions if isinstance(e,unreal.MaterialExpressionCustom)]
inputs={}
for name in ('BASE_COLOR','EMISSIVE_COLOR','NORMAL','ROUGHNESS','SPECULAR','OPACITY'):
    property=getattr(unreal.MaterialProperty,'MP_'+name)
    node=lib.get_material_property_input_node(material,property)
    inputs[name]=dict(node=node.get_name() if node else None,
        output=lib.get_material_property_input_node_output_name(material,property))
file=ROOT/'unreal/Content/RaftSim/Environment/SouthForkSurveyCandidate/M_RaftSim_LiveRiverSurface_SurfaceLitReview.uasset'
report=dict(material=ASSET,sha256=hashlib.sha256(file.read_bytes()).hexdigest(),
    expression_count=len(expressions),scalars=scalars,custom=custom,inputs=inputs,
    blend_mode=str(material.get_editor_property('blend_mode')),
    lighting_mode=str(material.get_editor_property('translucency_lighting_mode')),
    assets_modified=False)
out=ROOT/'docs/reconstruction-review-2026-09-07/survey-material-audit.json'
out.write_text(json.dumps(report,indent=2),encoding='utf-8')
unreal.log(f'Survey material audit: {len(expressions)} expressions, {len(scalars)} scalar parameters; no asset writes')
