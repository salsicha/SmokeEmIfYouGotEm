"""Verify the generated Zambezi reference-run map and gameplay bootstrap."""

from __future__ import annotations

import json
from pathlib import Path
import traceback

import unreal


MAP_PACKAGE = (
    "/Game/RaftSim/Maps/EnvironmentPreviews/LandscapeCandidates/"
    "L_ZambeziBatokaGorge_PhysicalCorridorCandidate"
)
REPORT_RELATIVE = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "zambezi_reference_scenario_map_validation.json"
)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    report_path = repo_root / REPORT_RELATIVE
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report: dict[str, object] = {
        "schema": "raftsim.unreal.zambezi_reference_scenario_map_validation.v2",
        "map_package": MAP_PACKAGE,
        "passed": False,
    }
    try:
        world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PACKAGE)
        if not world:
            raise RuntimeError(f"Could not load {MAP_PACKAGE}")
        subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        if not subsystem:
            raise RuntimeError("EditorActorSubsystem is unavailable")
        actors = list(subsystem.get_all_level_actors())
        markers = [
            actor
            for actor in actors
            if actor.get_actor_label().startswith("RaftSim_ZambeziRapid_")
        ]
        marker_rows = []
        for actor in markers:
            tags = sorted(str(tag) for tag in actor.tags)
            marker_rows.append(
                {
                    "actor_label": actor.get_actor_label(),
                    "tags": tags,
                    "location_cm": [
                        round(actor.get_actor_location().x, 3),
                        round(actor.get_actor_location().y, 3),
                        round(actor.get_actor_location().z, 3),
                    ],
                }
            )
        portages = [row for row in marker_rows if "RaftSimMandatoryPortage" in row["tags"]]
        player_rafts = [
            actor
            for actor in actors
            if actor.get_actor_label() == "RaftSim_Zambezi_PlayerRaft"
            and actor.get_class().get_name() == "RaftSimRaftActor"
        ]
        water_configs = [
            actor
            for actor in actors
            if actor.get_actor_label() == "RaftSim_Zambezi_RuntimeWaterConfig"
            and actor.get_class().get_name() == "RaftSimRiverWaterConfig"
        ]
        player_starts = [
            actor
            for actor in actors
            if actor.get_actor_label() == "RaftSim_GuideSeat_PlayerStart"
            and actor.get_class().get_name() == "PlayerStart"
        ]
        world_settings = world.get_world_settings()
        default_game_mode = (
            world_settings.get_editor_property("default_game_mode")
            if world_settings
            else None
        )
        game_mode_path = (
            default_game_mode.get_path_name() if default_game_mode else None
        )
        rapid_numbers = []
        for row in marker_rows:
            suffix = str(row["actor_label"]).removeprefix("RaftSim_ZambeziRapid_")
            rapid_numbers.append(int(suffix.split("_", 1)[0]))
        report.update(
            {
                "actor_count": len(actors),
                "scenario_marker_count": len(markers),
                "rapid_numbers": sorted(rapid_numbers),
                "mandatory_portage_marker_count": len(portages),
                "mandatory_portage_actor": portages[0]["actor_label"] if portages else None,
                "markers": sorted(marker_rows, key=lambda row: row["actor_label"]),
                "runnable": {
                    "player_raft_count": len(player_rafts),
                    "water_config_count": len(water_configs),
                    "player_start_count": len(player_starts),
                    "game_mode": game_mode_path,
                },
            }
        )
        passed = (
            len(markers) == 25
            and sorted(rapid_numbers) == list(range(1, 26))
            and len(portages) == 1
            and "_9_Commercial_Suicide" in str(portages[0]["actor_label"])
            and all("RaftSimScenarioMarker" in row["tags"] for row in marker_rows)
            and all("RaftSimZambeziRun" in row["tags"] for row in marker_rows)
            and len(player_rafts) == 1
            and len(water_configs) == 1
            and len(player_starts) == 1
            and str(game_mode_path).endswith("RaftSimVerticalSliceGameMode")
        )
        report["passed"] = passed
        if not passed:
            raise RuntimeError("Generated Zambezi scenario marker contract did not pass")
        unreal.log(
            f"Zambezi reference run validation passed with {len(markers)} markers, "
            f"{len(player_rafts)} raft, and {len(water_configs)} runtime water config"
        )
    except Exception as error:
        report["error"] = str(error)
        report["traceback"] = traceback.format_exc()
        unreal.log_error(report["traceback"])
    finally:
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        unreal.log(f"Zambezi scenario map validation report: {report_path}")
        unreal.SystemLibrary.quit_editor()


main()
