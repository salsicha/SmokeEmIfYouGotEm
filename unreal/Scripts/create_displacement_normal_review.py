"""Create an isolated South Fork displacement-normal experiment; never edit its source.

The initial variant rotates the existing smooth/detail normal by the actual
rasterized face rotation; it exposed coarse WPO triangle facets in live review.
The opt-in smooth variant instead interpolates a vertex-evaluated local-fluid
gradient. Neither adds geometry, overturning crests, or resolves a coarse mesh.
"""
import unreal

SOURCE = '/Game/RaftSim/Environment/SouthForkFullReach/Water/Materials/M_RaftSim_SouthForkRaftTransmissionWaterV4'
DEST = '/Game/RaftSim/Rendering/Review/M_RaftSim_DisplacementNormalReview'
CODE = r'''
float3 beforeFace = cross(ddx(Before), ddy(Before));
float3 afterFace = cross(ddx(After), ddy(After));
float beforeLength = length(beforeFace);
float afterLength = length(afterFace);
float3 n = normalize(DetailNormal);
if (beforeLength < 1e-8 || afterLength < 1e-8) return n;
beforeFace /= beforeLength;
afterFace /= afterLength;
// Both faces share winding; orient together, not independently.
float orientation = dot(beforeFace, VertexNormal) < 0.0 ? -1.0 : 1.0;
beforeFace *= orientation;
afterFace *= orientation;
float c = clamp(dot(beforeFace, afterFace), -1.0, 1.0);
// A folded/degenerate face is not a valid heightfield correction.
if (c < -0.999) return n;
float3 axis = cross(beforeFace, afterFace);
float3 rotated = n + cross(axis, n) + cross(axis, cross(axis, n)) / (1.0 + c);
return normalize(lerp(n, rotated, saturate(Strength)));
'''


def main(smooth=False):
    destination = DEST.replace('DisplacementNormalReview', 'SmoothDisplacementNormalReview') if smooth else DEST
    if unreal.EditorAssetLibrary.does_asset_exist(destination):
        raise RuntimeError('Review destination already exists; do not overwrite evidence')
    source = unreal.load_asset(SOURCE)
    if not isinstance(source, unreal.Material):
        raise RuntimeError('Source water material missing')
    if not source.get_editor_property('tangent_space_normal'):
        raise RuntimeError('Experiment expects the source tangent-space normal graph')
    material = unreal.EditorAssetLibrary.duplicate_asset(SOURCE, destination)
    if not material:
        raise RuntimeError('Could not duplicate source')
    lib = unreal.MaterialEditingLibrary
    original = lib.get_material_property_input_node(material, unreal.MaterialProperty.MP_NORMAL)
    original_output = lib.get_material_property_input_node_output_name(material, unreal.MaterialProperty.MP_NORMAL)
    if not original:
        raise RuntimeError('Source normal graph missing')

    def node(cls, **properties):
        result = lib.create_material_expression(material, cls)
        for key, value in properties.items():
            result.set_editor_property(key, value)
        return result

    def connect(a, output, b, input_name):
        if not lib.connect_material_expressions(a, output, b, input_name):
            raise RuntimeError(f'Failed connection to {input_name}')

    before = node(unreal.MaterialExpressionWorldPosition,
        world_position_shader_offset=unreal.WorldPositionIncludedOffsets.WPT_CAMERA_RELATIVE_NO_OFFSETS)
    after = node(unreal.MaterialExpressionWorldPosition,
        world_position_shader_offset=unreal.WorldPositionIncludedOffsets.WPT_CAMERA_RELATIVE)
    vertex = node(unreal.MaterialExpressionVertexNormalWS)
    detail_world = node(unreal.MaterialExpressionTransform,
        transform_source_type=unreal.MaterialVectorCoordTransformSource.TRANSFORMSOURCE_TANGENT,
        transform_type=unreal.MaterialVectorCoordTransform.TRANSFORM_WORLD)
    connect(original, original_output, detail_world, '')
    strength = node(unreal.MaterialExpressionScalarParameter,
        parameter_name='DisplacementNormalReviewStrength', default_value=1.0)
    inputs = [('Before', before), ('After', after), ('VertexNormal', vertex),
              ('DetailNormal', detail_world), ('Strength', strength)]
    correction_code = CODE
    if smooth:
        # Differentiate the local-fluid function at vertices, then interpolate
        # the gradient. Foam/depth/window inputs are held fixed within each
        # 15 cm finite difference; this is NOT full gate-gradient correction.
        fluids = [e for e in lib.get_material_expressions(material)
                  if isinstance(e, unreal.MaterialExpressionCustom)
                  and 'float boilPhase' in e.get_editor_property('code')]
        if len(fluids) != 1:
            raise RuntimeError('Expected one local-fluid function')
        fluid = fluids[0]
        gradient = lib.duplicate_material_expression(material, None, fluid)
        function = ('struct FluidGradientReview { float3 Eval(float2 UV, float Foam, float Speed, '
                    'float Wet, float DepthNorm, float3 FlowDisplacement, float WaveClock, '
                    'float3 RaftCenter, float3 WorldPosition, float Strength, float WindowMeters) {\n'
                    + fluid.get_editor_property('code') + '\n} };\nFluidGradientReview f;\n')
        suffix = ', Foam, Speed, Wet, DepthNorm, FlowDisplacement.xyz, WaveClock, RaftCenter.xyz, WorldPosition.xyz, Strength, WindowMeters)'
        gradient.set_editor_property('code',
            'if (Strength == 0.0 || Foam <= 0.025 || Wet <= 0.0 || DepthNorm * 4.0 <= 0.10) return float2(0,0);\n'
            + function + 'float h = f.Eval(UV' + suffix + '.z;\n'
            + 'float hx = f.Eval(UV + float2(0.05,0)' + suffix + '.z;\n'
            + 'float hy = f.Eval(UV + float2(0,0.05)' + suffix + '.z;\n'
            + 'return float2(hx-h,hy-h)/0.15;')
        gradient.set_editor_property('output_type', unreal.CustomMaterialOutputType.CMOT_FLOAT2)
        gradient.set_editor_property('description', 'Vertex-only finite gradient of existing local-fluid displacement')
        interpolator = node(unreal.MaterialExpressionVertexInterpolator)
        connect(gradient, '', interpolator, 'VS')
        # UE's input iterator includes unconnected advanced-property pins.
        uv = next(e for e in lib.get_inputs_for_material_expression(material, fluid) if e)
        if not isinstance(uv, unreal.MaterialExpressionAdd):
            raise RuntimeError('Expected the existing rebased river-UV Add input')
        inputs = [(name, expression) for name, expression in inputs if name != 'After']
        inputs += [('Gradient', interpolator), ('RiverUV', uv)]
        correction_code = CODE.replace(
            'float3 afterFace = cross(ddx(After), ddy(After));',
            'float3 dx = ddx(Before);\nfloat3 dy = ddy(Before);\n'
            'dx.z += dot(Gradient, ddx(RiverUV) * 3.0);\n'
            'dy.z += dot(Gradient, ddy(RiverUV) * 3.0);\n'
            'float3 afterFace = cross(dx, dy);')
    custom_inputs = []
    for name, _ in inputs:
        entry = unreal.CustomInput()
        entry.set_editor_property('input_name', name)
        custom_inputs.append(entry)
    correction = node(unreal.MaterialExpressionCustom, code=correction_code,
        description='Relative WPO face rotation; preserve smooth and ripple normal',
        output_type=unreal.CustomMaterialOutputType.CMOT_FLOAT3,
        inputs=custom_inputs)
    for name, expression in inputs:
        connect(expression, '', correction, name)
    result = node(unreal.MaterialExpressionTransform,
        transform_source_type=unreal.MaterialVectorCoordTransformSource.TRANSFORMSOURCE_WORLD,
        transform_type=unreal.MaterialVectorCoordTransform.TRANSFORM_TANGENT)
    connect(correction, '', result, '')
    if not lib.connect_material_property(result, '', unreal.MaterialProperty.MP_NORMAL):
        raise RuntimeError('Failed final normal connection')
    lib.recompile_material(material)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    if not unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False):
        raise RuntimeError('Review material save failed')
    unreal.log(f'DisplacementNormalReview created {destination}; source untouched; visual acceptance unproven')


if __name__ == '__main__':
    main('-RaftSimSmoothDisplacementNormalReview' in unreal.SystemLibrary.get_command_line())
