"""Import and audit RaftSim's project-owned guide flip line.

The mesh shares SM_RaftSim_WhitewaterRescuePfd's local frame: attach it to
the guide's ProductionPfd component with an identity relative transform.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import unreal


REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPO_ROOT / "unreal/SourceArt/RaftSim/Equipment/ProductionFlipLine"
MANIFEST_PATH = SOURCE_ROOT / "production_guide_flip_line_manifest.json"
PFD_MANIFEST_PATH = (
    REPO_ROOT
    / "unreal/SourceArt/RaftSim/Equipment/ProductionPfd/production_whitewater_pfd_manifest.json"
)
DESTINATION = "/Game/RaftSim/Equipment/Production"
ASSET_NAME = "SM_RaftSim_GuideFlipLine"
ASSET_PATH = f"{DESTINATION}/{ASSET_NAME}"
REPORT_PATH = (
    REPO_ROOT / "unreal/Saved/RaftSimValidation/m9/production-guide-flip-line.json"
)
EXPECTED_SLOTS = [
    "FlipLineWebbing",
    "FlipLineHardware",
]
# Rigging webbing (tinted at runtime like the raft's lines) and the steel
# used by the raft's other hardware.
MATERIAL_PATHS = [
    "/Game/RaftSim/Materials/M_RaftSim_RaftRigging",
    "/Game/RaftSim/Materials/M_RaftSim_GalvanizedSteel",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_and_verify_manifest() -> tuple[dict[str, object], Path]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("ownership") != (
        "Project-owned deterministic source art; no external mesh or texture input."
    ):
        raise RuntimeError("Flip line ownership declaration is missing or changed")
    if manifest.get("source_inputs") != []:
        raise RuntimeError("Guide flip line must not contain external source inputs")
    if manifest.get("material_slots") != EXPECTED_SLOTS:
        raise RuntimeError(f"Unexpected source slots: {manifest.get('material_slots')}")
    construction = manifest.get("construction", {})
    for field, expected in {"wraps": 2, "sewn_end_loops": 1, "locking_carabiners": 1}.items():
        if construction.get(field) != expected:
            raise RuntimeError(f"Guide flip line {field} changed: {construction.get(field)}")
    # The line is fitted to one specific vest; a regenerated vest needs a
    # regenerated line before either is imported.
    pfd_manifest = json.loads(PFD_MANIFEST_PATH.read_text(encoding="utf-8"))
    fitted = manifest.get("fitted_to_pfd", {})
    if fitted.get("fbx_sha256") != pfd_manifest.get("fbx_sha256"):
        raise RuntimeError("Guide flip line was fitted to a different PFD build")
    fbx_path = REPO_ROOT / str(manifest["fbx"])
    if not fbx_path.is_file() or sha256(fbx_path) != manifest.get("fbx_sha256"):
        raise RuntimeError("Guide flip line FBX is absent or stale")
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
        raise RuntimeError(
            f"Flip line import did not produce a StaticMesh: {task.imported_object_paths}"
        )
    return mesh


def configure_and_audit(
    mesh: unreal.StaticMesh, manifest: dict[str, object]
) -> dict[str, object]:
    slot_names = [str(slot.material_slot_name) for slot in mesh.static_materials]
    if slot_names != EXPECTED_SLOTS:
        raise RuntimeError(f"Imported material slot contract changed: {slot_names}")
    materials = [unreal.load_asset(path) for path in MATERIAL_PATHS]
    if any(material is None for material in materials):
        raise RuntimeError(f"One or more flip line materials are absent: {MATERIAL_PATHS}")
    for index, assigned_material in enumerate(materials):
        mesh.set_material(index, assigned_material)
    mesh.modify()
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)

    bounds = mesh.get_bounding_box()
    dimensions = [
        bounds.max.x - bounds.min.x,
        bounds.max.y - bounds.min.y,
        bounds.max.z - bounds.min.z,
    ]
    expected = manifest["dimensions_cm"]
    if any(abs(float(a) - float(b)) > 0.5 for a, b in zip(dimensions, expected)):
        raise RuntimeError(
            f"Flip line import changed its centimetre bounds: {dimensions} vs {expected}"
        )
    triangles = mesh.get_num_triangles(0)
    if not (5_000 <= triangles <= 60_000):
        raise RuntimeError(f"Flip line triangle budget changed: {triangles}")
    return {
        "schema_version": 1,
        "status": "production_mesh_imported",
        "asset_path": mesh.get_path_name(),
        "source_fbx_sha256": manifest["fbx_sha256"],
        "generator_version": manifest["generator_version"],
        "fitted_to_pfd": manifest["fitted_to_pfd"],
        "ownership": manifest["ownership"],
        "dimensions_cm": [round(float(value), 4) for value in dimensions],
        "authored_lod0_triangles": triangles,
        "construction": manifest["construction"],
        "frame": manifest["frame"],
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
    unreal.log("import_production_guide_flip_line: begin")
    manifest, fbx_path = load_and_verify_manifest()
    mesh = import_mesh(fbx_path)
    report = configure_and_audit(mesh, manifest)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    unreal.log("RAFTSIM_PRODUCTION_FLIP_LINE_IMPORT=" + json.dumps(report, sort_keys=True))
    unreal.log("import_production_guide_flip_line: complete")


if __name__ == "__main__":
    main()
