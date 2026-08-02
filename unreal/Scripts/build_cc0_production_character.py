"""Build a game-engine crew body from an externally installed MPFB extension.

The MPFB extension itself is a build-time GPL tool and is intentionally not
vendored.  The generated mesh, bundled MPFB data, and MakeHuman skin atlases
are published as CC0 by the MakeHuman project.  This script only writes the
requested Blender/FBX/preview artifacts.

Run from Blender after installing/enabling MPFB 2.0.17 or newer::

    blender --background --python build_cc0_production_character.py -- \
      --skin-atlas /path/to/young_lightskinned_male_diffuse.png \
      --output-dir /path/to/output
"""

from __future__ import annotations

import argparse
import importlib
from pathlib import Path
import sys

import bpy
from mathutils import Matrix, Vector


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skin-atlas", required=True)
    parser.add_argument("--eye-atlas")
    parser.add_argument(
        "--hair-mhclo",
        help="Optional reviewed MakeHuman/MPFB hair proxy (.mhclo) to fit and rig before export.",
    )
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--name", default="RaftSim_CC0_Guide")
    parser.add_argument("--gender", type=float, default=0.82)
    parser.add_argument("--height", type=float, default=0.58)
    parser.add_argument("--muscle", type=float, default=0.52)
    parser.add_argument("--weight", type=float, default=0.46)
    parser.add_argument("--ethnicity", choices=("african", "asian", "caucasian"), default="caucasian")
    parser.add_argument("--preview-size", type=int, default=1200)
    parser.add_argument("--omit-eye-details", action="store_true")
    script_args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    return parser.parse_args(script_args)


def _mpfb_symbol(module_suffix: str, symbol: str):
    for module_name in tuple(sys.modules):
        if module_name.endswith(module_suffix):
            module = importlib.import_module(module_name)
            return getattr(module, symbol)
    raise RuntimeError(f"MPFB module ending in {module_suffix!r} is not loaded")


def _clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def _set_principled_input(node, names: tuple[str, ...], value) -> None:
    for name in names:
        socket = node.inputs.get(name)
        if socket is not None:
            socket.default_value = value
            return


def _new_skin_material(name: str, atlas_path: Path) -> bpy.types.Material:
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    atlas = nodes.new("ShaderNodeTexImage")
    atlas.image = bpy.data.images.load(str(atlas_path), check_existing=True)
    atlas.interpolation = "Linear"
    atlas.extension = "REPEAT"
    links.new(atlas.outputs["Color"], shader.inputs["Base Color"])
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    _set_principled_input(shader, ("Roughness",), 0.54)
    _set_principled_input(shader, ("IOR",), 1.42)
    _set_principled_input(shader, ("Subsurface Weight", "Subsurface"), 0.075)
    _set_principled_input(shader, ("Subsurface Radius",), (1.0, 0.42, 0.22))

    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 430.0
    noise.inputs["Detail"].default_value = 3.0
    noise.inputs["Roughness"].default_value = 0.64
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.075
    bump.inputs["Distance"].default_value = 0.0015
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    return material


def _new_simple_material(name: str, color: tuple[float, float, float, float], roughness: float) -> bpy.types.Material:
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = color
    _set_principled_input(shader, ("Roughness",), roughness)
    return material


def _new_eye_material(name: str, atlas_path: Path) -> bpy.types.Material:
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    atlas = nodes.new("ShaderNodeTexImage")
    atlas.image = bpy.data.images.load(str(atlas_path), check_existing=True)
    atlas.interpolation = "Linear"
    links.new(atlas.outputs["Color"], shader.inputs["Base Color"])
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    _set_principled_input(shader, ("Roughness",), 0.31)
    _set_principled_input(shader, ("IOR",), 1.376)
    return material


def _find_exported_hair(source_hair: bpy.types.Object, rig: bpy.types.Object) -> bpy.types.Object:
    """Resolve the deep-copied hair mesh produced by MPFB's export-copy service."""
    expected_name = f"{source_hair.name}_Export"
    exact = bpy.data.objects.get(expected_name)
    if exact is not None and exact.type == "MESH":
        return exact
    candidates = [
        child
        for child in rig.children_recursive
        if child.type == "MESH" and child.name.startswith(expected_name)
    ]
    if len(candidates) != 1:
        raise RuntimeError(
            f"Expected exactly one exported hair mesh matching {expected_name!r}; "
            f"found {[candidate.name for candidate in candidates]}"
        )
    return candidates[0]


def _configure_body_materials(
    body: bpy.types.Object,
    skin: bpy.types.Material,
    wetsuit: bpy.types.Material,
) -> None:
    body.data.materials.clear()
    body.data.materials.append(skin)
    body.data.materials.append(wetsuit)
    skin_bones = {
        "head",
        "neck_01",
        "hand_l",
        "hand_r",
        "index_01_l", "index_02_l", "index_03_l",
        "middle_01_l", "middle_02_l", "middle_03_l",
        "ring_01_l", "ring_02_l", "ring_03_l",
        "pinky_01_l", "pinky_02_l", "pinky_03_l",
        "thumb_01_l", "thumb_02_l", "thumb_03_l",
        "index_01_r", "index_02_r", "index_03_r",
        "middle_01_r", "middle_02_r", "middle_03_r",
        "ring_01_r", "ring_02_r", "ring_03_r",
        "pinky_01_r", "pinky_02_r", "pinky_03_r",
        "thumb_01_r", "thumb_02_r", "thumb_03_r",
    }
    skin_group_indices = {
        group.index for group in body.vertex_groups if group.name in skin_bones
    }
    vertex_skin_weight: list[float] = []
    for vertex in body.data.vertices:
        vertex_skin_weight.append(sum(
            assignment.weight
            for assignment in vertex.groups
            if assignment.group in skin_group_indices
        ))
    for polygon in body.data.polygons:
        skin_average = sum(vertex_skin_weight[index] for index in polygon.vertices) / len(polygon.vertices)
        polygon.material_index = 0 if skin_average >= 0.34 else 1


def _bind_rigid_mesh(mesh: bpy.types.Object, rig: bpy.types.Object, bone_name: str) -> None:
    mesh.parent = rig
    modifier = mesh.modifiers.new("Armature", "ARMATURE")
    modifier.object = rig
    group = mesh.vertex_groups.new(name=bone_name)
    group.add(range(len(mesh.data.vertices)), 1.0, "REPLACE")


def _replace_with_rigid_bone_weights(mesh: bpy.types.Object, bone_name: str) -> None:
    """Keep helmet-contained detail meshes coherent under component-space poses."""
    mesh.vertex_groups.clear()
    group = mesh.vertex_groups.new(name=bone_name)
    group.add(range(len(mesh.data.vertices)), 1.0, "REPLACE")


def _rigidify_high_confidence_head_vertices(
    body: bpy.types.Object,
    minimum_head_weight: float = 0.75,
) -> int:
    """Keep facial skin with rigid eyes/hair under component-space head poses."""
    head_group = body.vertex_groups.get("head")
    if head_group is None:
        raise RuntimeError(f"{body.name} has no head vertex group")
    seeds = {
        vertex.index
        for vertex in body.data.vertices
        if any(
            assignment.group == head_group.index
            and assignment.weight >= minimum_head_weight
            for assignment in vertex.groups
        )
    }
    if not seeds:
        raise RuntimeError(f"{body.name} has no high-confidence head vertices")

    skin_materials = {
        index
        for index, material in enumerate(body.data.materials)
        if material is not None and "skin" in material.name.casefold()
    }
    skin_polygons = [
        set(polygon.vertices)
        for polygon in body.data.polygons
        if polygon.material_index in skin_materials
    ]
    vertex_to_polygons: dict[int, list[int]] = {}
    for polygon_index, vertices in enumerate(skin_polygons):
        for vertex_index in vertices:
            vertex_to_polygons.setdefault(vertex_index, []).append(polygon_index)

    selected = set(seeds)
    pending = list(seeds)
    visited_polygons: set[int] = set()
    while pending:
        vertex_index = pending.pop()
        for polygon_index in vertex_to_polygons.get(vertex_index, ()):
            if polygon_index in visited_polygons:
                continue
            visited_polygons.add(polygon_index)
            for connected_index in skin_polygons[polygon_index]:
                if connected_index not in selected:
                    selected.add(connected_index)
                    pending.append(connected_index)

    selected_indices = sorted(selected)
    for group in body.vertex_groups:
        group.remove(selected_indices)
    head_group.add(selected_indices, 1.0, "REPLACE")
    return len(selected_indices)


def _extract_helper_eyes(
    body: bpy.types.Object,
    rig: bpy.types.Object,
    material: bpy.types.Material,
    name: str,
) -> bpy.types.Object:
    eyes = body.copy()
    eyes.data = body.data.copy()
    eyes.name = f"{name}_Eyes"
    bpy.context.collection.objects.link(eyes)

    eye_group_indices = {
        group.index
        for group in eyes.vertex_groups
        if group.name in {"helper-l-eye", "helper-r-eye"}
    }
    keep_vertices = {
        vertex.index
        for vertex in eyes.data.vertices
        if any(assignment.group in eye_group_indices for assignment in vertex.groups)
    }
    if not keep_vertices:
        raise RuntimeError("MPFB eye helper vertex groups were not found")

    for modifier in tuple(eyes.modifiers):
        eyes.modifiers.remove(modifier)
    bpy.context.view_layer.objects.active = eyes
    eyes.select_set(True)
    if eyes.data.shape_keys:
        bpy.ops.object.shape_key_remove(all=True, apply_mix=True)
    for vertex in eyes.data.vertices:
        vertex.select = vertex.index not in keep_vertices
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.delete(type="VERT")
    bpy.ops.object.mode_set(mode="OBJECT")

    uv_layer = eyes.data.uv_layers.active or eyes.data.uv_layers.new(name="UVMap")
    atlas_centers = {True: Vector((0.716, 0.731)), False: Vector((0.302, 0.302))}
    for positive_x in (True, False):
        vertices = [vertex for vertex in eyes.data.vertices if (vertex.co.x >= 0.0) == positive_x]
        center_x = sum(vertex.co.x for vertex in vertices) / len(vertices)
        center_z = sum(vertex.co.z for vertex in vertices) / len(vertices)
        radius_x = max(abs(vertex.co.x - center_x) for vertex in vertices)
        radius_z = max(abs(vertex.co.z - center_z) for vertex in vertices)
        atlas_center = atlas_centers[positive_x]
        for polygon in eyes.data.polygons:
            for loop_index in polygon.loop_indices:
                vertex = eyes.data.vertices[eyes.data.loops[loop_index].vertex_index]
                if (vertex.co.x >= 0.0) != positive_x:
                    continue
                uv_layer.data[loop_index].uv = (
                    atlas_center.x + ((vertex.co.x - center_x) / radius_x) * 0.205,
                    atlas_center.y + ((vertex.co.z - center_z) / radius_z) * 0.205,
                )

    eyes.vertex_groups.clear()
    eyes.data.materials.clear()
    eyes.data.materials.append(material)
    _bind_rigid_mesh(eyes, rig, "head")
    return eyes


def _add_brows(
    eyes: bpy.types.Object,
    rig: bpy.types.Object,
    material: bpy.types.Material,
    name: str,
) -> list[bpy.types.Object]:
    eye_front_y = min(vertex.co.y for vertex in eyes.data.vertices)
    eye_center_z = sum(vertex.co.z for vertex in eyes.data.vertices) / len(eyes.data.vertices)
    eye_centers_x = {
        positive_x: sum(
            vertex.co.x for vertex in eyes.data.vertices if (vertex.co.x >= 0.0) == positive_x
        ) / sum(1 for vertex in eyes.data.vertices if (vertex.co.x >= 0.0) == positive_x)
        for positive_x in (True, False)
    }
    brows: list[bpy.types.Object] = []
    for positive_x, suffix in ((True, "L"), (False, "R")):
        direction = 1.0 if positive_x else -1.0
        center_x = eye_centers_x[positive_x]
        curve_data = bpy.data.curves.new(f"{name}_Brow_{suffix}_Curve", "CURVE")
        curve_data.dimensions = "3D"
        curve_data.bevel_depth = 0.00165
        curve_data.bevel_resolution = 2
        spline = curve_data.splines.new("BEZIER")
        spline.bezier_points.add(2)
        for point, co in zip(
            spline.bezier_points,
            (
                Vector((center_x - direction * 0.016, eye_front_y - 0.010, eye_center_z + 0.021)),
                Vector((center_x, eye_front_y - 0.011, eye_center_z + 0.025)),
                Vector((center_x + direction * 0.017, eye_front_y - 0.009, eye_center_z + 0.020)),
            ),
        ):
            point.co = co
            point.handle_left_type = "AUTO"
            point.handle_right_type = "AUTO"
        brow = bpy.data.objects.new(f"{name}_Brow_{suffix}", curve_data)
        bpy.context.collection.objects.link(brow)
        curve_data.materials.append(material)
        bpy.context.view_layer.objects.active = brow
        brow.select_set(True)
        bpy.ops.object.convert(target="MESH")
        _bind_rigid_mesh(brow, rig, "head")
        brows.append(brow)
    return brows


def _look_at(camera: bpy.types.Object, target: Vector) -> None:
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()


def _render_preview(body: bpy.types.Object, output_path: Path, size: int) -> None:
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = size
    scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(output_path)
    scene.render.film_transparent = False
    scene.world.color = (0.018, 0.024, 0.032)

    bpy.ops.object.camera_add(location=(0.0, -1.82, 1.56))
    camera = bpy.context.object
    camera.data.lens = 78.0
    _look_at(camera, Vector((0.0, -0.035, 1.55)))
    scene.camera = camera

    for name, location, energy, size_m, color in (
        ("Key", (-0.8, -1.0, 2.35), 72.0, 1.1, (1.0, 0.84, 0.72)),
        ("Fill", (0.9, -0.65, 1.75), 34.0, 1.0, (0.68, 0.80, 1.0)),
        ("Rim", (0.1, 0.25, 2.05), 48.0, 0.8, (0.76, 0.88, 1.0)),
    ):
        data = bpy.data.lights.new(name, "AREA")
        data.energy = energy
        data.shape = "DISK"
        data.size = size_m
        data.color = color
        light = bpy.data.objects.new(name, data)
        bpy.context.collection.objects.link(light)
        light.location = location
        _look_at(light, Vector((0.0, -0.04, 1.52)))

    scene.view_settings.exposure = -0.35
    bpy.ops.render.render(write_still=True)


def _export_fbx(rig: bpy.types.Object, meshes: list[bpy.types.Object], output_path: Path) -> None:
    # Join the separately reviewed eye/brow surfaces into the weighted body.
    # Leaving them as sibling mesh nodes makes some FBX importers promote the
    # nodes to bones, which detaches the details once the head is posed.
    body = meshes[0]
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.join()

    # MPFB is authored in meters. Scale both vertices and rest bones—not just
    # the FBX root transform—so skinning and component-space procedural poses
    # share Unreal's centimeter coordinates.
    meters_to_centimeters = Matrix.Scale(100.0, 4)
    body.data.transform(meters_to_centimeters)
    body.data.update()
    rig.data.transform(meters_to_centimeters)
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.length_unit = "CENTIMETERS"
    bpy.context.scene.unit_settings.scale_length = 0.01

    bpy.ops.object.select_all(action="DESELECT")
    rig.select_set(True)
    body.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.export_scene.fbx(
        filepath=str(output_path),
        use_selection=True,
        object_types={"ARMATURE", "MESH"},
        apply_scale_options="FBX_SCALE_ALL",
        global_scale=1.0,
        apply_unit_scale=True,
        axis_forward="-Y",
        axis_up="Z",
        add_leaf_bones=False,
        use_armature_deform_only=True,
        bake_anim=False,
        path_mode="COPY",
        embed_textures=False,
    )


def main() -> None:
    args = _arguments()
    atlas_path = Path(args.skin_atlas).resolve()
    eye_atlas_path = Path(args.eye_atlas).resolve() if args.eye_atlas else None
    hair_mhclo_path = Path(args.hair_mhclo).resolve() if args.hair_mhclo else None
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    if not atlas_path.is_file():
        raise FileNotFoundError(atlas_path)
    if not args.omit_eye_details and (eye_atlas_path is None or not eye_atlas_path.is_file()):
        raise FileNotFoundError("--eye-atlas is required unless --omit-eye-details is set")
    if hair_mhclo_path is not None and not hair_mhclo_path.is_file():
        raise FileNotFoundError(hair_mhclo_path)

    HumanService = _mpfb_symbol("mpfb.services.humanservice", "HumanService")
    TargetService = _mpfb_symbol("mpfb.services.targetservice", "TargetService")
    HumanObjectProperties = _mpfb_symbol("mpfb.entities.objectproperties", "HumanObjectProperties")
    ExportService = _mpfb_symbol("mpfb.services.exportservice", "ExportService")
    ObjectService = _mpfb_symbol("mpfb.services.objectservice", "ObjectService")

    _clear_scene()
    source_body = HumanService.create_human()
    source_body.name = f"{args.name}_Source"
    for key, value in (
        ("gender", args.gender),
        ("height", args.height),
        ("muscle", args.muscle),
        ("weight", args.weight),
        ("african", 1.0 if args.ethnicity == "african" else 0.0),
        ("asian", 1.0 if args.ethnicity == "asian" else 0.0),
        ("caucasian", 1.0 if args.ethnicity == "caucasian" else 0.0),
    ):
        HumanObjectProperties.set_value(key, value, entity_reference=source_body)
    TargetService.reapply_macro_details(source_body)
    HumanService.add_builtin_rig(source_body, "game_engine")

    source_hair = None
    if hair_mhclo_path is not None:
        source_hair = HumanService.add_mhclo_asset(
            str(hair_mhclo_path),
            source_body,
            asset_type="Hair",
            subdiv_levels=0,
            material_type="GAMEENGINE",
            set_up_rigging=True,
            interpolate_weights=True,
            import_subrig=False,
            import_weights=False,
        )
        if source_hair is None or source_hair.type != "MESH":
            raise RuntimeError(f"MPFB did not create a hair mesh from {hair_mhclo_path}")

    rig = ExportService.create_character_copy(source_body, name_suffix="_Export")
    body = ObjectService.find_object_of_type_amongst_nearest_relatives(rig, "Basemesh")
    rig.name = f"{args.name}_Rig"
    body.name = f"{args.name}_Body"

    detail_meshes: list[bpy.types.Object] = []
    hair = None
    if source_hair is not None:
        hair = _find_exported_hair(source_hair, rig)
        hair.name = f"{args.name}_Hair"
        # MPFB interpolates proxy weights across the scalp, neck and upper
        # spine. That is useful for long free hair, but these reviewed short
        # helmet styles must move as one island with the head. Mixed weights
        # visibly separate the groom when RaftSim drives component-space neck
        # transforms, so replace them before joining/export.
        _replace_with_rigid_bone_weights(hair, "head")
        for material in hair.data.materials:
            if material is not None:
                material.name = f"{args.name}_Hair"
        detail_meshes.append(hair)
    if not args.omit_eye_details:
        eye_material = _new_eye_material(f"{args.name}_Eyes", eye_atlas_path)
        brow_material = _new_simple_material(
            f"{args.name}_Brows", (0.012, 0.0045, 0.002, 1.0), 0.79)
        eyes = _extract_helper_eyes(body, rig, eye_material, args.name)
        detail_meshes.append(eyes)
        detail_meshes.extend(_add_brows(eyes, rig, brow_material, args.name))
    ExportService.bake_modifiers_remove_helpers(
        body, bake_masks=True, bake_subdiv=False, remove_helpers=True, also_proxy=True)
    _rigidify_high_confidence_head_vertices(body)

    materials = {
        "skin": _new_skin_material(f"{args.name}_Skin", atlas_path),
        "wetsuit": _new_simple_material(f"{args.name}_Wetsuit", (0.008, 0.014, 0.019, 1.0), 0.52),
    }
    _configure_body_materials(body, materials["skin"], materials["wetsuit"])

    source_rig = source_body.parent
    source_body.hide_render = True
    source_body.hide_viewport = True
    if source_rig:
        source_rig.hide_render = True
        source_rig.hide_viewport = True
    if source_hair:
        source_hair.hide_render = True
        source_hair.hide_viewport = True

    preview_path = output_dir / f"{args.name}_preview.png"
    blend_path = output_dir / f"{args.name}.blend"
    fbx_path = output_dir / f"{args.name}.fbx"
    hair_vertex_count = len(hair.data.vertices) if hair else 0
    _render_preview(body, preview_path, args.preview_size)
    _export_fbx(rig, [body, *detail_meshes], fbx_path)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    print(
        "RAFTSIM_CC0_CHARACTER_COMPLETE",
        f"body_vertices={len(body.data.vertices)}",
        f"body_polygons={len(body.data.polygons)}",
        f"hair_vertices={hair_vertex_count}",
        f"bones={len(rig.data.bones)}",
        f"preview={preview_path}",
        f"fbx={fbx_path}",
        f"blend={blend_path}",
    )


if __name__ == "__main__":
    main()
