"""Import and audit RaftSim's project-owned production helmet static mesh."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import unreal


REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPO_ROOT / "unreal/SourceArt/RaftSim/Equipment/ProductionHelmet"
MANIFEST_PATH = SOURCE_ROOT / "production_whitewater_helmet_manifest.json"
DESTINATION = "/Game/RaftSim/Equipment/Production"
ASSET_NAME = "SM_RaftSim_WhitewaterHelmet"
ASSET_PATH = f"{DESTINATION}/{ASSET_NAME}"
REPORT_PATH = REPO_ROOT / "unreal/Saved/RaftSimValidation/m9/production-whitewater-helmet.json"
EXPECTED_SLOTS = ["HelmetShell", "HelmetLiner", "HelmetWebbing", "HelmetHardware"]
MATERIAL_PATHS = [
    "/Game/RaftSim/Materials/M_RaftSim_Helmet",
    "/Game/RaftSim/Materials/M_RaftSim_PFDWebbing",
    "/Game/RaftSim/Materials/M_RaftSim_PFDWebbing",
    "/Game/RaftSim/Materials/M_RaftSim_PaddleShaft",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_and_verify_manifest() -> tuple[dict[str, object], Path]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("ownership") != (
        "Project-owned deterministic source art; no external mesh or texture input."
    ):
        raise RuntimeError("Helmet ownership declaration is missing or changed")
    if manifest.get("physical_cut_through_vents") != 6:
        raise RuntimeError("Production helmet must retain six physical vents")
    if manifest.get("material_slots") != EXPECTED_SLOTS:
        raise RuntimeError(f"Unexpected source slots: {manifest.get('material_slots')}")
    fbx_path = REPO_ROOT / str(manifest["fbx"])
    if not fbx_path.is_file() or sha256(fbx_path) != manifest.get("fbx_sha256"):
        raise RuntimeError("Production helmet FBX is absent or stale")
    return manifest, fbx_path


def import_mesh(fbx_path: Path) -> unreal.StaticMesh:
    # Reimport preserves existing build settings.  Disable Nanite first so the
    # post-import LOD0 query measures authored FBX triangles, not a previous
    # Nanite fallback.  configure_and_audit re-enables it after recording.
    existing = unreal.load_asset(ASSET_PATH)
    if isinstance(existing, unreal.StaticMesh):
        subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        # The subsystem can be unavailable during commandlet start-up even
        # though it is registered after the import task initializes the mesh
        # editor module.  In that case, reimport first; configure_and_audit()
        # performs the authoritative Nanite configuration and verification.
        if subsystem:
            nanite_settings = subsystem.get_nanite_settings(existing)
            if nanite_settings.enabled:
                nanite_settings.enabled = False
                subsystem.set_nanite_settings(existing, nanite_settings)
                existing.modify()
                unreal.EditorAssetLibrary.save_loaded_asset(
                    existing, only_if_is_dirty=False
                )

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
        raise RuntimeError(f"Helmet import did not produce a StaticMesh: {task.imported_object_paths}")
    return mesh


def configure_and_audit(
    mesh: unreal.StaticMesh, manifest: dict[str, object]
) -> dict[str, object]:
    subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    if not subsystem:
        raise RuntimeError("StaticMeshEditorSubsystem is unavailable")

    slot_names = [str(slot.material_slot_name) for slot in mesh.static_materials]
    if slot_names != EXPECTED_SLOTS:
        raise RuntimeError(f"Imported material slot contract changed: {slot_names}")
    materials = [unreal.load_asset(path) for path in MATERIAL_PATHS]
    if any(material is None for material in materials):
        raise RuntimeError(f"One or more helmet materials are absent: {MATERIAL_PATHS}")
    for index, material in enumerate(materials):
        mesh.set_material(index, material)

    # Capture the authored LOD0 count before Nanite replaces the conventional
    # render-data query with its reduced fallback mesh.
    source_triangles = mesh.get_num_triangles(0)
    nanite_settings = subsystem.get_nanite_settings(mesh)
    nanite_settings.enabled = True
    subsystem.set_nanite_settings(mesh, nanite_settings)
    mesh.modify()
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)

    bounds = mesh.get_bounding_box()
    dimensions = [
        bounds.max.x - bounds.min.x,
        bounds.max.y - bounds.min.y,
        bounds.max.z - bounds.min.z,
    ]
    if not (24.0 <= min(dimensions) <= 35.0 and 24.0 <= max(dimensions) <= 35.0):
        raise RuntimeError(f"Helmet import has implausible centimetre bounds: {dimensions}")
    nanite_fallback_triangles = mesh.get_num_triangles(0)
    if not (8_000 <= source_triangles <= 40_000):
        raise RuntimeError(
            f"Helmet production triangle budget changed: {source_triangles}"
        )

    persisted_slots = [
        {
            "slot": str(slot.material_slot_name),
            "material": slot.material_interface.get_path_name()
            if slot.material_interface
            else None,
        }
        for slot in mesh.static_materials
    ]
    return {
        "schema_version": 1,
        "status": "production_mesh_imported",
        "asset_path": mesh.get_path_name(),
        "source_fbx_sha256": manifest["fbx_sha256"],
        "ownership": manifest["ownership"],
        "dimensions_cm": [round(float(value), 4) for value in dimensions],
        "bounds_min_cm": [round(float(bounds.min.x), 4), round(float(bounds.min.y), 4), round(float(bounds.min.z), 4)],
        "bounds_max_cm": [round(float(bounds.max.x), 4), round(float(bounds.max.y), 4), round(float(bounds.max.z), 4)],
        "authored_lod0_triangles": source_triangles,
        "nanite_fallback_triangles": nanite_fallback_triangles,
        "nanite_enabled": subsystem.get_nanite_settings(mesh).enabled,
        "physical_cut_through_vents": manifest["physical_cut_through_vents"],
        "retention_anchor_count": manifest["retention_anchor_count"],
        "material_slots": persisted_slots,
        "runtime_boundary": manifest["runtime_boundary"],
    }


def main() -> None:
    unreal.log("import_production_whitewater_helmet: begin")
    manifest, fbx_path = load_and_verify_manifest()
    mesh = import_mesh(fbx_path)
    report = configure_and_audit(mesh, manifest)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    unreal.log("RAFTSIM_PRODUCTION_HELMET_IMPORT=" + json.dumps(report, sort_keys=True))
    unreal.log("import_production_whitewater_helmet: complete")


if __name__ == "__main__":
    main()
