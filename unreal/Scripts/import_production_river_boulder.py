"""Import and audit RaftSim's project-owned production river boulder."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import unreal


REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPO_ROOT / "unreal/SourceArt/RaftSim/Rocks/ProductionRiverBoulder"
MANIFEST_PATH = SOURCE_ROOT / "production_river_boulder_manifest.json"
DESTINATION = "/Game/RaftSim/Environment/Rocks/Production"
ASSET_NAME = "SM_RaftSim_ProductionRiverBoulder"
ASSET_PATH = f"{DESTINATION}/{ASSET_NAME}"
REPORT_PATH = REPO_ROOT / "unreal/Saved/RaftSimValidation/m9/production-river-boulder.json"
EXPECTED_SLOTS = ["RiverBoulder"]
MATERIAL_PATH = "/Game/RaftSim/Materials/M_RaftSim_ProductionRiverBoulder"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_and_verify_manifest() -> tuple[dict[str, object], Path]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("ownership") != (
        "Project-owned deterministic source art; no external mesh or texture input."
    ):
        raise RuntimeError("Production boulder ownership declaration is missing or changed")
    if manifest.get("source_inputs") != []:
        raise RuntimeError("Production boulder must not contain external source inputs")
    if manifest.get("material_slots") != EXPECTED_SLOTS:
        raise RuntimeError(f"Unexpected source slots: {manifest.get('material_slots')}")
    construction = manifest.get("construction", {})
    if construction.get("closed_watertight_shells") != 1:
        raise RuntimeError("Production boulder must remain a closed shell")
    if construction.get("physical_fracture_bands") != 3:
        raise RuntimeError("Production boulder fracture contract changed")
    fbx_path = REPO_ROOT / str(manifest["fbx"])
    if not fbx_path.is_file() or sha256(fbx_path) != manifest.get("fbx_sha256"):
        raise RuntimeError("Production boulder FBX is absent or stale")
    return manifest, fbx_path


def import_mesh(fbx_path: Path) -> unreal.StaticMesh:
    existing = unreal.load_asset(ASSET_PATH)
    if isinstance(existing, unreal.StaticMesh):
        subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        settings = subsystem.get_nanite_settings(existing)
        if settings.enabled:
            settings.enabled = False
            subsystem.set_nanite_settings(existing, settings)
            unreal.EditorAssetLibrary.save_loaded_asset(existing, only_if_is_dirty=False)

    options = unreal.FbxImportUI()
    options.automated_import_should_detect_type = False
    options.import_mesh = True
    options.import_as_skeletal = False
    options.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
    options.original_import_type = unreal.FBXImportType.FBXIT_STATIC_MESH
    options.import_materials = False
    options.import_textures = False
    options.import_animations = False
    options.static_mesh_import_data.combine_meshes = True
    options.static_mesh_import_data.generate_lightmap_u_vs = True
    options.static_mesh_import_data.remove_degenerates = True
    options.static_mesh_import_data.transform_vertex_to_absolute = False
    options.static_mesh_import_data.bake_pivot_in_vertex = True
    options.static_mesh_import_data.vertex_color_import_option = (
        unreal.VertexColorImportOption.REPLACE
    )

    task = unreal.AssetImportTask()
    task.filename = str(fbx_path)
    task.destination_path = DESTINATION
    task.destination_name = ASSET_NAME
    task.replace_existing = True
    task.replace_existing_settings = True
    task.automated = True
    task.save = False
    task.factory = unreal.FbxFactory()
    task.options = options
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    mesh = unreal.load_asset(ASSET_PATH)
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(
            f"Production boulder import did not produce a StaticMesh: {task.imported_object_paths}"
        )
    return mesh


def configure_and_audit(mesh: unreal.StaticMesh, manifest: dict[str, object]) -> dict[str, object]:
    subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    if not subsystem:
        raise RuntimeError("StaticMeshEditorSubsystem is unavailable")
    slot_names = [str(slot.material_slot_name) for slot in mesh.static_materials]
    if slot_names != EXPECTED_SLOTS:
        raise RuntimeError(f"Imported material slot contract changed: {slot_names}")
    material = unreal.load_asset(MATERIAL_PATH)
    if material is None:
        raise RuntimeError(f"Production boulder material is absent: {MATERIAL_PATH}")
    mesh.set_material(0, material)

    source_triangles = mesh.get_num_triangles(0)
    nanite = subsystem.get_nanite_settings(mesh)
    nanite.enabled = True
    subsystem.set_nanite_settings(mesh, nanite)
    mesh.modify()
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)

    bounds = mesh.get_bounding_box()
    dimensions = [
        bounds.max.x - bounds.min.x,
        bounds.max.y - bounds.min.y,
        bounds.max.z - bounds.min.z,
    ]
    fallback_triangles = mesh.get_num_triangles(0)
    if not (
        205.0 <= dimensions[0] <= 240.0
        and 190.0 <= dimensions[1] <= 225.0
        and 160.0 <= dimensions[2] <= 200.0
    ):
        raise RuntimeError(f"Production boulder import has implausible bounds: {dimensions}")
    if not 70_000 <= source_triangles <= 100_000:
        raise RuntimeError(f"Production boulder triangle budget changed: {source_triangles}")
    return {
        "schema_version": 1,
        "status": "production_mesh_imported",
        "asset_path": mesh.get_path_name(),
        "source_fbx_sha256": manifest["fbx_sha256"],
        "ownership": manifest["ownership"],
        "geology_claim": manifest["geology_claim"],
        "dimensions_cm": [round(float(value), 4) for value in dimensions],
        "authored_lod0_triangles": source_triangles,
        "nanite_fallback_triangles": fallback_triangles,
        "nanite_enabled": subsystem.get_nanite_settings(mesh).enabled,
        "material_slots": [
            {
                "slot": str(slot.material_slot_name),
                "material": slot.material_interface.get_path_name()
                if slot.material_interface
                else None,
            }
            for slot in mesh.static_materials
        ],
        "collision_enabled": False,
        "runtime_boundary": manifest["runtime_boundary"],
    }


def main() -> None:
    unreal.log("import_production_river_boulder: begin")
    manifest, fbx_path = load_and_verify_manifest()
    mesh = import_mesh(fbx_path)
    report = configure_and_audit(mesh, manifest)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    unreal.log("RAFTSIM_PRODUCTION_BOULDER_IMPORT=" + json.dumps(report, sort_keys=True))
    unreal.log("import_production_river_boulder: complete")


if __name__ == "__main__":
    main()
