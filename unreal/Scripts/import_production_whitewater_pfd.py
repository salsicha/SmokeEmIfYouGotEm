"""Import and audit RaftSim's project-owned production whitewater PFD."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import unreal


REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPO_ROOT / "unreal/SourceArt/RaftSim/Equipment/ProductionPfd"
MANIFEST_PATH = SOURCE_ROOT / "production_whitewater_pfd_manifest.json"
DESTINATION = "/Game/RaftSim/Equipment/Production"
ASSET_NAME = "SM_RaftSim_WhitewaterRescuePfd"
ASSET_PATH = f"{DESTINATION}/{ASSET_NAME}"
REPORT_PATH = (
    REPO_ROOT / "unreal/Saved/RaftSimValidation/m9/production-whitewater-pfd.json"
)
EXPECTED_SLOTS = [
    "PfdShell",
    "PfdWebbing",
    "PfdHardware",
    "PfdReflective",
    "PfdLabel",
]
MATERIAL_PATHS = [
    "/Game/RaftSim/Materials/M_RaftSim_CrewPFD",
    "/Game/RaftSim/Materials/M_RaftSim_PFDWebbing",
    "/Game/RaftSim/Materials/M_RaftSim_PaddleShaft",
    "/Game/RaftSim/Materials/M_RaftSim_Helmet_White",
    "/Game/RaftSim/Materials/M_RaftSim_PFDWebbing",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_and_verify_manifest() -> tuple[dict[str, object], Path]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("ownership") != (
        "Project-owned deterministic source art; no external mesh or texture input."
    ):
        raise RuntimeError("PFD ownership declaration is missing or changed")
    if manifest.get("source_inputs") != []:
        raise RuntimeError("Production PFD must not contain external source inputs")
    if manifest.get("material_slots") != EXPECTED_SLOTS:
        raise RuntimeError(f"Unexpected source slots: {manifest.get('material_slots')}")
    construction = manifest.get("construction", {})
    expected_counts = {
        "front_carrier_panels": 2,
        "back_carrier_panels": 1,
        "front_foam_panels": 4,
        "back_panels": 2,
        "rear_flex_channels": 1,
        "side_wings": 0,
        "side_webbing_connectors": 4,
        "side_adjustment_sliders": 4,
        "shoulder_adjustment_points": 4,
        "shoulder_foam_pads": 0,
        "shoulder_webbing_runs": 2,
        "front_pockets": 2,
        "front_zip": 1,
        "backup_buckles": 2,
        "front_backup_webbing_runs": 4,
        "adjustment_points": 8,
        "quick_release_rescue_belts": 1,
        "rescue_tether_rings": 1,
        "reflective_chest_zones": 2,
        "blank_back_placards": 1,
        "front_lash_tabs": 3,
    }
    for field, expected in expected_counts.items():
        if construction.get(field) != expected:
            raise RuntimeError(
                f"Production PFD {field} changed: {construction.get(field)}"
            )
    fbx_path = REPO_ROOT / str(manifest["fbx"])
    if not fbx_path.is_file() or sha256(fbx_path) != manifest.get("fbx_sha256"):
        raise RuntimeError("Production PFD FBX is absent or stale")
    return manifest, fbx_path


def import_mesh(fbx_path: Path) -> unreal.StaticMesh:
    existing = unreal.load_asset(ASSET_PATH)
    if isinstance(existing, unreal.StaticMesh):
        subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        settings = subsystem.get_nanite_settings(existing)
        if settings.enabled:
            settings.enabled = False
            subsystem.set_nanite_settings(existing, settings)
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
        raise RuntimeError(
            f"PFD import did not produce a StaticMesh: {task.imported_object_paths}"
        )
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
        raise RuntimeError(f"One or more PFD materials are absent: {MATERIAL_PATHS}")
    for index, assigned_material in enumerate(materials):
        mesh.set_material(index, assigned_material)

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
        36.0 <= dimensions[0] <= 48.0
        and 32.0 <= dimensions[1] <= 44.0
        and 40.0 <= dimensions[2] <= 56.0
    ):
        raise RuntimeError(
            f"PFD import has implausible centimetre bounds: {dimensions}"
        )
    if not (15_000 <= source_triangles <= 80_000):
        raise RuntimeError(
            f"PFD production triangle budget changed: {source_triangles}"
        )
    return {
        "schema_version": 1,
        "status": "production_mesh_imported",
        "asset_path": mesh.get_path_name(),
        "source_fbx_sha256": manifest["fbx_sha256"],
        "generator_version": manifest["generator_version"],
        "ownership": manifest["ownership"],
        "dimensions_cm": [round(float(value), 4) for value in dimensions],
        "authored_lod0_triangles": source_triangles,
        "nanite_fallback_triangles": fallback_triangles,
        "nanite_enabled": subsystem.get_nanite_settings(mesh).enabled,
        "construction": manifest["construction"],
        "soft_geometry": manifest["soft_geometry"],
        "material_slots": [
            {
                "slot": str(slot.material_slot_name),
                "material": slot.material_interface.get_path_name()
                if slot.material_interface
                else None,
            }
            for slot in mesh.static_materials
        ],
        "runtime_boundary": manifest["runtime_boundary"],
    }


def main() -> None:
    unreal.log("import_production_whitewater_pfd: begin")
    manifest, fbx_path = load_and_verify_manifest()
    mesh = import_mesh(fbx_path)
    report = configure_and_audit(mesh, manifest)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    unreal.log("RAFTSIM_PRODUCTION_PFD_IMPORT=" + json.dumps(report, sort_keys=True))
    unreal.log("import_production_whitewater_pfd: complete")


if __name__ == "__main__":
    main()
