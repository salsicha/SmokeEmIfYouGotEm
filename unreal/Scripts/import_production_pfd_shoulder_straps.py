"""Import RaftSim's per-wearer PFD shoulder straps (build_production_pfd_shoulder_straps.py).

Each mesh shares SM_RaftSim_WhitewaterRescuePfd's local frame: attach it to
the wearer's ProductionPfd component with an identity relative transform.
Import the vest first; the straps refuse to import against another vest build.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import unreal


REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPO_ROOT / "unreal/SourceArt/RaftSim/Equipment/ProductionPfd/ShoulderStraps"
MANIFEST_PATH = SOURCE_ROOT / "production_pfd_shoulder_straps_manifest.json"
PFD_MANIFEST_PATH = (
    REPO_ROOT / "unreal/SourceArt/RaftSim/Equipment/ProductionPfd/production_whitewater_pfd_manifest.json"
)
DESTINATION = "/Game/RaftSim/Equipment/Production"
WEARERS = ["Crew01", "Crew02", "Crew03", "Crew04", "Guide"]
REPORT_PATH = REPO_ROOT / "unreal/Saved/RaftSimValidation/m9/production-pfd-shoulder-straps.json"
# The vest's own slots, so the runtime can give the straps the vest's
# per-wearer shell tint and webbing exactly as on the vest.
EXPECTED_SLOTS = ["PfdShell", "PfdWebbing", "PfdHardware", "PfdReflective", "PfdLabel"]
MATERIAL_PATHS = [
    "/Game/RaftSim/Materials/M_RaftSim_CrewPFD",
    "/Game/RaftSim/Materials/M_RaftSim_PFDWebbing",
    "/Game/RaftSim/Materials/M_RaftSim_PaddleShaft",
    "/Game/RaftSim/Materials/M_RaftSim_Helmet_White",
    "/Game/RaftSim/Materials/M_RaftSim_PFDWebbing",
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
        raise RuntimeError(f"PFD shoulder-strap import did not produce a StaticMesh: {task.imported_object_paths}")
    return mesh


def main() -> None:
    unreal.log("import_production_pfd_shoulder_straps: begin")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("ownership") != (
        "Project-owned deterministic source art; no external mesh or texture input."
    ):
        raise RuntimeError("Shoulder-strap ownership declaration is missing or changed")
    if manifest.get("material_slots") != EXPECTED_SLOTS:
        raise RuntimeError(f"Unexpected source slots: {manifest.get('material_slots')}")
    pfd_manifest = json.loads(PFD_MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("fitted_to_pfd", {}).get("fbx_sha256") != pfd_manifest.get("fbx_sha256"):
        raise RuntimeError("Shoulder straps were fitted to a different PFD build")
    for source in manifest.get("source_inputs", []):
        if sha256(REPO_ROOT / source["path"]) != source["sha256"]:
            raise RuntimeError(f"Shoulder-strap source input changed: {source['path']}")
    materials = [unreal.load_asset(path) for path in MATERIAL_PATHS]
    if any(material is None for material in materials):
        raise RuntimeError(f"One or more strap materials are absent: {MATERIAL_PATHS}")
    report = {"schema_version": 1, "status": "production_mesh_imported", "meshes": {}}
    for wearer in WEARERS:
        name = f"SM_RaftSim_PfdShoulderStraps_{wearer}"
        entry = manifest["meshes"][name]
        fbx_path = REPO_ROOT / entry["fbx"]
        if not fbx_path.is_file() or sha256(fbx_path) != entry["fbx_sha256"]:
            raise RuntimeError(f"Shoulder-strap FBX is absent or stale: {fbx_path}")
        for side, stats in entry["straps"].items():
            if stats["min_skin_gap_cm"] <= 0.0:
                raise RuntimeError(f"{name} {side} touches or cuts the wearer")
        mesh = import_mesh(name, fbx_path)
        slots = [str(slot.material_slot_name) for slot in mesh.static_materials]
        if slots != EXPECTED_SLOTS:
            raise RuntimeError(f"Imported material slot contract changed: {slots}")
        for index, material in enumerate(materials):
            mesh.set_material(index, material)
        mesh.modify()
        unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
        bounds = mesh.get_bounding_box()
        # Chest tab to back anchor over the shoulder, in the vest's frame.
        if not (13.0 <= bounds.min.z <= 20.0 and 22.0 <= bounds.max.z <= 36.0):
            raise RuntimeError(f"{name} has implausible bounds: {bounds.min.z}..{bounds.max.z}")
        report["meshes"][name] = {
            "asset_path": mesh.get_path_name(),
            "source_fbx_sha256": entry["fbx_sha256"],
            "straps": entry["straps"],
            "bounds_z_cm": [round(float(bounds.min.z), 3), round(float(bounds.max.z), 3)],
            "triangles": mesh.get_num_triangles(0),
        }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    unreal.log("RAFTSIM_PRODUCTION_PFD_SHOULDER_STRAPS_IMPORT=" + json.dumps(report, sort_keys=True))
    unreal.log("import_production_pfd_shoulder_straps: complete")


if __name__ == "__main__":
    main()
