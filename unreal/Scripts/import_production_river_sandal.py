"""Import and audit RaftSim's project-owned left and right river sandals."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import unreal


REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPO_ROOT / "unreal/SourceArt/RaftSim/Equipment/ProductionRiverSandal"
MANIFEST_PATH = SOURCE_ROOT / "production_river_sandal_manifest.json"
DESTINATION = "/Game/RaftSim/Equipment/Production"
ASSET_NAMES = ["SM_RaftSim_RiverSandal_L", "SM_RaftSim_RiverSandal_R"]
REPORT_PATH = REPO_ROOT / "unreal/Saved/RaftSimValidation/m9/production-river-sandal.json"
EXPECTED_SLOTS = ["SandalSole", "SandalFootbed", "SandalStrap", "SandalHardware"]
MATERIAL_PATHS = [
    "/Game/RaftSim/Materials/M_RaftSim_RiverBootRubber",
    "/Game/RaftSim/Materials/M_RaftSim_RiverBootUpper",
    "/Game/RaftSim/Materials/M_RaftSim_PFDWebbing",
    "/Game/RaftSim/Materials/M_RaftSim_PaddleShaft",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_and_verify_manifest() -> dict[str, object]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("ownership") != (
        "Project-owned deterministic source art; no external mesh or texture input."
    ):
        raise RuntimeError("River-sandal ownership declaration is missing or changed")
    if manifest.get("material_slots") != EXPECTED_SLOTS:
        raise RuntimeError(f"Unexpected source slots: {manifest.get('material_slots')}")
    if manifest.get("construction", {}).get("straps") != ["toe", "instep", "heel"]:
        raise RuntimeError("River sandals must keep toe, instep and heel straps")
    for name in ASSET_NAMES:
        entry = manifest["meshes"][name]
        fbx_path = REPO_ROOT / entry["fbx"]
        if not fbx_path.is_file() or sha256(fbx_path) != entry["fbx_sha256"]:
            raise RuntimeError(f"River-sandal FBX is absent or stale: {fbx_path}")
    return manifest


def import_mesh(name: str, fbx_path: Path) -> unreal.StaticMesh:
    asset_path = f"{DESTINATION}/{name}"
    existing = unreal.load_asset(asset_path) if unreal.EditorAssetLibrary.does_asset_exist(asset_path) else None
    subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    if isinstance(existing, unreal.StaticMesh) and subsystem:
        nanite = subsystem.get_nanite_settings(existing)
        if nanite.enabled:
            nanite.enabled = False
            subsystem.set_nanite_settings(existing, nanite)

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
    task.destination_name = name
    task.replace_existing = True
    task.replace_existing_settings = True
    task.automated = True
    task.save = False
    task.factory = unreal.FbxFactory()
    task.options = options
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    mesh = unreal.load_asset(asset_path)
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"River-sandal import did not produce a StaticMesh: {task.imported_object_paths}")
    return mesh


def configure_and_audit(mesh: unreal.StaticMesh) -> dict[str, object]:
    slot_names = [str(slot.material_slot_name) for slot in mesh.static_materials]
    if slot_names != EXPECTED_SLOTS:
        raise RuntimeError(f"Imported material slot contract changed: {slot_names}")
    materials = [unreal.load_asset(path) for path in MATERIAL_PATHS]
    if any(material is None for material in materials):
        raise RuntimeError(f"One or more river-sandal materials are absent: {MATERIAL_PATHS}")
    for index, assigned_material in enumerate(materials):
        mesh.set_material(index, assigned_material)
    mesh.modify()
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)

    bounds = mesh.get_bounding_box()
    dimensions = [bounds.max.x - bounds.min.x, bounds.max.y - bounds.min.y, bounds.max.z - bounds.min.z]
    # A sandal: about a foot long, a hand wide, and its straps standing no
    # higher than the ankle it is centred on.
    if not (22.0 <= dimensions[0] <= 30.0 and 9.0 <= dimensions[1] <= 13.0 and 7.0 <= dimensions[2] <= 12.0):
        raise RuntimeError(f"River-sandal import has implausible centimetre bounds: {dimensions}")
    if bounds.max.z > 0.5 or bounds.min.z > -8.0:
        raise RuntimeError(f"River sandal must hang below its ankle origin: {bounds.min.z}..{bounds.max.z}")
    return {
        "asset_path": mesh.get_path_name(),
        "dimensions_cm": [round(float(value), 4) for value in dimensions],
        "triangles": mesh.get_num_triangles(0),
        "material_slots": [
            {
                "slot": str(slot.material_slot_name),
                "material": slot.material_interface.get_path_name() if slot.material_interface else None,
            }
            for slot in mesh.static_materials
        ],
    }


def main() -> None:
    unreal.log("import_production_river_sandal: begin")
    manifest = load_and_verify_manifest()
    report = {"schema_version": 1, "status": "production_mesh_imported", "meshes": {}}
    for name in ASSET_NAMES:
        mesh = import_mesh(name, REPO_ROOT / manifest["meshes"][name]["fbx"])
        report["meshes"][name] = configure_and_audit(mesh)
        report["meshes"][name]["source_fbx_sha256"] = manifest["meshes"][name]["fbx_sha256"]
    report["runtime_boundary"] = manifest["runtime_boundary"]
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    unreal.log("RAFTSIM_PRODUCTION_RIVER_SANDAL_IMPORT=" + json.dumps(report, sort_keys=True))
    unreal.log("import_production_river_sandal: complete")


if __name__ == "__main__":
    main()
