"""Import RaftSim's per-wearer helmet retention straps (build_production_helmet_straps.py)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import unreal


REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPO_ROOT / "unreal/SourceArt/RaftSim/Equipment/ProductionHelmet/Straps"
MANIFEST_PATH = SOURCE_ROOT / "production_helmet_straps_manifest.json"
DESTINATION = "/Game/RaftSim/Equipment/Production"
WEARERS = ["Crew01", "Crew02", "Crew03", "Crew04", "Guide"]
REPORT_PATH = REPO_ROOT / "unreal/Saved/RaftSimValidation/m9/production-helmet-straps.json"
EXPECTED_SLOTS = ["HelmetWebbing", "HelmetHardware"]
MATERIAL_PATHS = [
    "/Game/RaftSim/Materials/M_RaftSim_PFDWebbing",
    "/Game/RaftSim/Materials/M_RaftSim_PaddleShaft",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def import_mesh(name: str, fbx_path: Path) -> unreal.StaticMesh:
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
    mesh = unreal.load_asset(f"{DESTINATION}/{name}")
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"Helmet-strap import did not produce a StaticMesh: {task.imported_object_paths}")
    return mesh


def main() -> None:
    unreal.log("import_production_helmet_straps: begin")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("material_slots") != EXPECTED_SLOTS:
        raise RuntimeError(f"Unexpected source slots: {manifest.get('material_slots')}")
    materials = [unreal.load_asset(path) for path in MATERIAL_PATHS]
    if any(material is None for material in materials):
        raise RuntimeError(f"One or more strap materials are absent: {MATERIAL_PATHS}")
    report = {"schema_version": 1, "status": "production_mesh_imported", "meshes": {}}
    for wearer in WEARERS:
        name = f"SM_RaftSim_HelmetStraps_{wearer}"
        entry = manifest["meshes"][name]
        fbx_path = REPO_ROOT / entry["fbx"]
        if not fbx_path.is_file() or sha256(fbx_path) != entry["fbx_sha256"]:
            raise RuntimeError(f"Helmet-strap FBX is absent or stale: {fbx_path}")
        if entry["min_skin_clearance_cm"] <= 0.0:
            raise RuntimeError(f"{name} touches or cuts the wearer's skin")
        mesh = import_mesh(name, fbx_path)
        slots = [str(slot.material_slot_name) for slot in mesh.static_materials]
        if slots != EXPECTED_SLOTS:
            raise RuntimeError(f"Imported material slot contract changed: {slots}")
        for index, material in enumerate(materials):
            mesh.set_material(index, material)
        mesh.modify()
        unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
        bounds = mesh.get_bounding_box()
        # The chin strap hangs below the shell's anchors, under the chin.
        if not (-20.0 <= bounds.min.z <= -12.0 and bounds.max.z <= 3.0):
            raise RuntimeError(f"{name} has implausible bounds: {bounds.min.z}..{bounds.max.z}")
        report["meshes"][name] = {
            "asset_path": mesh.get_path_name(),
            "source_fbx_sha256": entry["fbx_sha256"],
            "chin_point": entry["chin_point"],
            "min_skin_clearance_cm": entry["min_skin_clearance_cm"],
            "bounds_z_cm": [round(float(bounds.min.z), 3), round(float(bounds.max.z), 3)],
        }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    unreal.log("RAFTSIM_PRODUCTION_HELMET_STRAPS_IMPORT=" + json.dumps(report, sort_keys=True))
    unreal.log("import_production_helmet_straps: complete")


if __name__ == "__main__":
    main()
