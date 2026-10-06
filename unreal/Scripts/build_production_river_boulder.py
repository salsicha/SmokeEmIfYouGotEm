"""Build RaftSim's project-owned production river boulder in Blender.

The mesh is a presentation-only closed shell fitted inside the existing D4
contact radius.  It uses deterministic water-worn faceting and physical
fracture grooves without claiming site-specific South Fork geology.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOT = REPO_ROOT / "unreal/SourceArt/RaftSim/Rocks/ProductionRiverBoulder"
FBX_PATH = OUTPUT_ROOT / "SM_RaftSim_ProductionRiverBoulder.fbx"
BLEND_PATH = OUTPUT_ROOT / "SM_RaftSim_ProductionRiverBoulder.blend"
MANIFEST_PATH = OUTPUT_ROOT / "production_river_boulder_manifest.json"
GENERATOR_VERSION = 3
MATERIAL_NAME = "RiverBoulder"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reset_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.materials):
        for datablock in list(datablocks):
            if datablock.users == 0:
                datablocks.remove(datablock)


def fracture_depth(direction: Vector) -> float:
    """Return bounded radial cuts for three nonparallel physical fissures."""
    cuts = (
        (
            Vector((0.13, 0.94, -0.31)).normalized(),
            0.030,
            0.025,
            0.86,
            Vector((0.45, -0.65, 0.62)).normalized(),
        ),
        (
            Vector((0.76, -0.41, 0.50)).normalized(),
            -0.095,
            0.019,
            0.72,
            Vector((-0.60, -0.30, 0.74)).normalized(),
        ),
        (
            Vector((-0.52, -0.38, 0.76)).normalized(),
            0.165,
            0.021,
            0.58,
            Vector((0.20, 0.70, 0.68)).normalized(),
        ),
    )
    depth = 0.0
    for plane_normal, offset, width, strength, centre in cuts:
        signed_distance = direction.dot(plane_normal) - offset
        groove = math.exp(-((signed_distance / width) ** 2))
        upper_gate = max(0.0, min(1.0, direction.z * 1.8 + 0.65))
        angular_offset = max(0.0, 1.0 - direction.dot(centre))
        local_gate = math.exp(-((angular_offset / 0.28) ** 2))
        depth += groove * upper_gate * local_gate * strength
    return min(depth, 1.0)


def build_boulder() -> bpy.types.Object:
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=7, radius=1.0)
    obj = bpy.context.object
    obj.name = "SM_RaftSim_ProductionRiverBoulder"
    obj.data.name = obj.name

    # Start from a dense, uniform triangular field and move vertices directly;
    # no random state, simulation, or external displacement map is involved.
    for vertex in obj.data.vertices:
        direction = vertex.co.normalized()
        theta = math.atan2(direction.y, direction.x)
        phi = math.asin(max(-1.0, min(1.0, direction.z)))
        macro = (
            1.0
            + 0.036 * math.sin(3.0 * theta + 0.48)
            + 0.033 * math.cos(5.0 * theta - 1.7 * phi)
            + 0.022 * math.sin(9.0 * theta + 2.4 * phi)
            + 0.012 * math.cos(17.0 * theta - 4.0 * phi)
        )
        # Quantized directional response creates broad eroded planes while
        # retaining enough curvature to read as water-worn granitic rock.
        facet = (
            1.0
            - 0.042 * abs(direction.dot(Vector((0.83, 0.31, 0.46)).normalized())) ** 5
            - 0.032 * abs(direction.dot(Vector((-0.24, 0.91, 0.34)).normalized())) ** 7
        )
        shoulder = 1.0 + 0.045 * direction.x - 0.028 * direction.y
        groove = 1.0 - 0.075 * fracture_depth(direction)
        radial = macro * facet * shoulder * groove
        x = direction.x * 114.0 * radial
        y = direction.y * 105.0 * radial
        z = direction.z * 108.0 * radial
        # Give the contact obstacle one raised, tilted crown and one grounded
        # submerged seat.  The prior 84 cm Z radius plus heavy crown clamp read
        # as two smooth pancakes from the wrap camera.  This closed monolith is
        # taller without changing the D4 horizontal contact envelope.
        crown_direction = Vector((-0.34, 0.18, 0.92)).normalized()
        crown_distance = max(0.0, 1.0 - direction.dot(crown_direction))
        crown_bump = 13.0 * math.exp(-((crown_distance / 0.18) ** 2))
        z += crown_bump * max(direction.z, 0.0)
        z += 5.0 * direction.x - 2.5 * direction.y
        if z > 72.0:
            z = 72.0 + (z - 72.0) * 0.72
        if z < -72.0:
            z = -72.0 + (z + 72.0) * 0.26
        z += 3.0 * math.sin(theta * 2.0 + 0.7) * (1.0 - direction.z**2)
        vertex.co = (x, y, z)

    rock_material = bpy.data.materials.new(MATERIAL_NAME)
    rock_material.diffuse_color = (0.14, 0.15, 0.15, 1.0)
    rock_material.roughness = 0.66
    obj.data.materials.append(rock_material)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True

    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(58.0), island_margin=0.008)
    bpy.ops.object.mode_set(mode="OBJECT")

    # Alpha zero selects the project-owned mineral branch in the shared river-
    # boulder material. The importer explicitly replaces static-mesh colors.
    colors = obj.data.color_attributes.new(name="Col", type="BYTE_COLOR", domain="CORNER")
    for entry in colors.data:
        entry.color = (0.24, 0.23, 0.20, 0.0)
    return obj


def validate(obj: bpy.types.Object) -> dict[str, object]:
    if [slot.name for slot in obj.data.materials] != [MATERIAL_NAME]:
        raise RuntimeError("Production boulder material contract changed")
    if not obj.data.uv_layers or "Col" not in obj.data.color_attributes:
        raise RuntimeError("Production boulder requires UVs and source vertex color")
    if len(obj.data.polygons) < 70_000:
        raise RuntimeError("Production boulder is unexpectedly low detail")
    coordinates = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    minimum = Vector(tuple(min(v[index] for v in coordinates) for index in range(3)))
    maximum = Vector(tuple(max(v[index] for v in coordinates) for index in range(3)))
    dimensions = maximum - minimum
    if not (
        205.0 <= dimensions.x <= 240.0
        and 190.0 <= dimensions.y <= 225.0
        and 160.0 <= dimensions.z <= 200.0
    ):
        raise RuntimeError(f"Production boulder bounds are implausible: {tuple(dimensions)}")
    return {
        "vertex_count": len(obj.data.vertices),
        "polygon_count": len(obj.data.polygons),
        "material_slots": [MATERIAL_NAME],
        "uv_channel_count": len(obj.data.uv_layers),
        "vertex_color_alpha": 0.0,
        "bounds_min_cm": [round(value, 4) for value in minimum],
        "bounds_max_cm": [round(value, 4) for value in maximum],
        "dimensions_cm": [round(value, 4) for value in dimensions],
    }


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    reset_scene()
    mesh_object = build_boulder()
    audit = validate(mesh_object)
    bpy.context.view_layer.objects.active = mesh_object
    mesh_object.select_set(True)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH), check_existing=False)
    bpy.ops.export_scene.fbx(
        filepath=str(FBX_PATH),
        use_selection=True,
        object_types={"MESH"},
        global_scale=0.01,
        use_mesh_modifiers=True,
        colors_type="LINEAR",
        add_leaf_bones=False,
        bake_anim=False,
        axis_forward="-Z",
        axis_up="Y",
        apply_unit_scale=True,
        use_space_transform=True,
        path_mode="AUTO",
    )
    manifest = {
        "schema": "raftsim.production_river_boulder_source.v1",
        "generator_version": GENERATOR_VERSION,
        "ownership": "Project-owned deterministic source art; no external mesh or texture input.",
        "source_inputs": [],
        "geology_claim": "Appearance analog only; not represented as site-specific South Fork geology.",
        "fbx": str(FBX_PATH.relative_to(REPO_ROOT)),
        "blend": str(BLEND_PATH.relative_to(REPO_ROOT)),
        "fbx_sha256": sha256(FBX_PATH),
        "blend_sha256": sha256(BLEND_PATH),
        "construction": {
            "closed_watertight_shells": 1,
            "physical_fracture_bands": 3,
            "water_worn_facet_fields": 2,
            "contact_envelope_fraction": 0.96,
        },
        "runtime_boundary": "Collisionless fitted visual only; D4 obstacle radius, friction, contact, wrap and pin authority remain native.",
        **audit,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, sort_keys=True))


if __name__ == "__main__":
    main()
