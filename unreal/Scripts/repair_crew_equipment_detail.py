"""Keep close-view safety gear intact on conventional and Nanite render paths."""
import json
from pathlib import Path
import unreal

subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
report = []
for name in ("SM_RaftSim_WhitewaterHelmet", "SM_RaftSim_WhitewaterRescuePfd",
             "SM_RaftSim_WhitewaterRiverBoot"):
    mesh = unreal.load_asset(f"/Game/RaftSim/Equipment/Production/{name}")
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"Missing production gear: {name}")
    settings = subsystem.get_nanite_settings(mesh)
    before = mesh.get_num_triangles(0)
    # The default coarse proxy loses narrow straps, rounded rims and sole
    # edges. These small, bounded assets need the authored fallback silhouette.
    settings.fallback_relative_error = 0.0
    settings.fallback_percent_triangles = 1.0
    settings.fallback_target = unreal.NaniteFallbackTarget.PERCENT_TRIANGLES
    subsystem.set_nanite_settings(mesh, settings)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
    report.append({"mesh": name, "before_triangles": before,
                   "after_triangles": mesh.get_num_triangles(0)})
    unreal.log(f"Crew equipment detail: {report[-1]}")
path = Path(unreal.Paths.project_saved_dir()) / "RaftSimValidation/crew-equipment-detail.json"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(report, indent=2), encoding="utf-8")
