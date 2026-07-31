"""Import and audit RaftSim's project-owned production paddle-raft rest mesh."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import unreal


REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPO_ROOT / "unreal/SourceArt/RaftSim/Rafts/ProductionPaddleRaft"
MANIFEST_PATH = SOURCE_ROOT / "production_paddle_raft_manifest.json"
DESTINATION = "/Game/RaftSim/Rafts/Production"
ASSET_NAME = "SM_RaftSim_ProductionPaddleRaft"
ASSET_PATH = f"{DESTINATION}/{ASSET_NAME}"
REPORT_PATH = REPO_ROOT / "unreal/Saved/RaftSimValidation/m9/production-paddle-raft.json"
EXPECTED_SLOTS = [
    "RaftTube",
    "RaftFloor",
    "RaftRigging",
    "RaftMetal",
    "RaftRubber",
]
MATERIAL_PATHS = [
    "/Game/RaftSim/Materials/M_RaftSim_RaftTube",
    "/Game/RaftSim/Materials/M_RaftSim_RaftFloor",
    "/Game/RaftSim/Materials/M_RaftSim_RaftRigging",
    "/Game/RaftSim/Materials/M_RaftSim_GalvanizedSteel",
    "/Game/RaftSim/Materials/M_RaftSim_BootRubber",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_and_verify_manifest() -> tuple[dict[str, object], Path]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("ownership") != (
        "Project-owned deterministic source art; no external mesh or texture input."
    ):
        raise RuntimeError("Raft ownership declaration is missing or changed")
    if manifest.get("source_inputs") != []:
        raise RuntimeError("Production raft must not contain external source inputs")
    if manifest.get("material_slots") != EXPECTED_SLOTS:
        raise RuntimeError(f"Unexpected source slots: {manifest.get('material_slots')}")
    construction = manifest.get("construction", {})
    expected_counts = {
        "main_chambers": 4,
        "thwarts": 2,
        "d_rings": 12,
        "carry_handles": 4,
        "tube_valves": 4,
        "floor_pressure_relief_valves": 1,
        "self_bailing_drain_recesses": 8,
    }
    for field, expected in expected_counts.items():
        if construction.get(field) != expected:
            raise RuntimeError(f"Production raft {field} changed: {construction.get(field)}")
    fbx_path = REPO_ROOT / str(manifest["fbx"])
    if not fbx_path.is_file() or sha256(fbx_path) != manifest.get("fbx_sha256"):
        raise RuntimeError("Production raft FBX is absent or stale")
    return manifest, fbx_path


def import_mesh(fbx_path: Path) -> unreal.StaticMesh:
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
        raise RuntimeError(f"Raft import did not produce a StaticMesh: {task.imported_object_paths}")
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
        raise RuntimeError(f"One or more raft materials are absent: {MATERIAL_PATHS}")
    for index, assigned_material in enumerate(materials):
        mesh.set_material(index, assigned_material)

    # Runtime reads this rest topology once and moves only the collisionless
    # procedural presentation copy, so the cooked LOD must remain CPU-readable.
    mesh.set_editor_property("allow_cpu_access", True)
    nanite = subsystem.get_nanite_settings(mesh)
    nanite.enabled = False
    subsystem.set_nanite_settings(mesh, nanite)
    mesh.modify()
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)

    bounds = mesh.get_bounding_box()
    dimensions = [
        bounds.max.x - bounds.min.x,
        bounds.max.y - bounds.min.y,
        bounds.max.z - bounds.min.z,
    ]
    triangles = mesh.get_num_triangles(0)
    if not (420.0 <= dimensions[0] <= 450.0 and 195.0 <= dimensions[1] <= 220.0):
        raise RuntimeError(f"Raft import has implausible centimetre bounds: {dimensions}")
    if not (20_000 <= triangles <= 120_000):
        raise RuntimeError(f"Raft production triangle budget changed: {triangles}")

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
        "status": "production_rest_mesh_imported",
        "asset_path": mesh.get_path_name(),
        "source_fbx_sha256": manifest["fbx_sha256"],
        "ownership": manifest["ownership"],
        "dimensions_cm": [round(float(value), 4) for value in dimensions],
        "authored_lod0_triangles": triangles,
        "nanite_enabled": subsystem.get_nanite_settings(mesh).enabled,
        "allow_cpu_access": bool(mesh.get_editor_property("allow_cpu_access")),
        "construction": manifest["construction"],
        "material_slots": persisted_slots,
        "runtime_boundary": manifest["runtime_boundary"],
    }


def main() -> None:
    unreal.log("import_production_whitewater_raft: begin")
    manifest, fbx_path = load_and_verify_manifest()
    mesh = import_mesh(fbx_path)
    report = configure_and_audit(mesh, manifest)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    unreal.log("RAFTSIM_PRODUCTION_RAFT_IMPORT=" + json.dumps(report, sort_keys=True))
    unreal.log("import_production_whitewater_raft: complete")


if __name__ == "__main__":
    main()
