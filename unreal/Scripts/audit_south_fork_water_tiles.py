"""Audit/repair water UV buffers; use -ExecutePythonScript (editor subsystem required)."""
import json
from pathlib import Path
import unreal

repair = "-RaftSimRepairWaterTiles" in unreal.SystemLibrary.get_command_line()
root = "/Game/RaftSim/Environment/SouthForkFullReach/Water"
subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
assert subsystem is not None, "Use -ExecutePythonScript, not the Python commandlet; this audit needs StaticMeshEditorSubsystem"
rows = []
for path in sorted(unreal.EditorAssetLibrary.list_assets(root, recursive=False)):
    name = path.rsplit("/", 1)[-1].split(".")[0]
    if not (name.startswith("SM_south_fork_") and "_Water_" in name
            or name == "SM_SalmonFalls_VisualContinuation"):
        continue
    mesh = unreal.load_asset(path)
    options = subsystem.get_lod_build_settings(mesh, 0)
    before = bool(options.get_editor_property("use_full_precision_u_vs"))
    if repair and not before:
        options.set_editor_property("use_full_precision_u_vs", True)
        subsystem.set_lod_build_settings(mesh, 0, options)
        assert unreal.EditorAssetLibrary.save_loaded_asset(mesh), path
    after = bool(subsystem.get_lod_build_settings(mesh, 0).get_editor_property("use_full_precision_u_vs"))
    rows.append({"asset": path, "full_precision_before": before, "full_precision_after": after})
    unreal.log(f"South Fork water UV audit: {name}: {before} -> {after}")
assert len(rows) >= 39, f"Incomplete water tile inventory: {len(rows)}"
if repair:
    assert all(row["full_precision_after"] for row in rows)
output = Path(unreal.Paths.project_saved_dir()) / "RaftSimValidation" / ("south-fork-water-tiles-repaired.json" if repair else "south-fork-water-tiles-audit.json")
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps({"repair": repair, "tiles": rows}, indent=2), encoding="utf-8")
unreal.log(f"South Fork water UV audit complete: {len(rows)} tiles, {output}")
