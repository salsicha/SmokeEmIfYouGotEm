"""Generate the five compact signature-rapid maps.

The source-scale Zambezi reference run is built separately by
RaftSim.CreateLandscapeImportCandidateMaps and the packaging preflight.
"""
import unreal
unreal.log("bootstrap_river_maps: creating river maps")
unreal.SystemLibrary.execute_console_command(None, "RaftSim.CreateRiverMaps")
unreal.log("bootstrap_river_maps: done")
