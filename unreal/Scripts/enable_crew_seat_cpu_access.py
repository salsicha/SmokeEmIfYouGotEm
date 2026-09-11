"""Retain LOD0 buffers needed for one-time seating in packaged CC0 meshes."""
import json
from pathlib import Path
import unreal

records = []
subsystem = unreal.get_editor_subsystem(unreal.SkeletalMeshEditorSubsystem)
for name in ("Guide", "Crew01", "Crew02", "Crew03", "Crew04"):
    path = f"/Game/RaftSim/Characters/Production/CC0/SK_RaftSim_CC0_{name}"
    mesh = unreal.load_asset(path)
    if not isinstance(mesh, unreal.SkeletalMesh):
        raise RuntimeError(f"Missing production body: {path}")
    subsystem.set_allow_cpu_access(mesh, True)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    if not unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False):
        raise RuntimeError(f"Could not save CPU seating data: {path}")
    records.append({"mesh": path, "cpu_access_requested": True, "saved": True})
out = Path(unreal.Paths.project_dir()).resolve().parent / "docs/crew-review-2026-09-06/seat-contact"
out.mkdir(parents=True, exist_ok=True)
(out / "cpu-access.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
