"""Generate the four compact signature-rapid maps (not South Fork).

The source-scale Zambezi reference run is built separately by
RaftSim.CreateLandscapeImportCandidateMaps and the packaging preflight.
"""
import unreal
unreal.log("bootstrap_river_maps: creating river maps")
unreal.SystemLibrary.execute_console_command(None, "RaftSim.CreateRiverMaps")
unreal.log("bootstrap_river_maps: done")
