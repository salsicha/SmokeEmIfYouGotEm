"""Finish the original tiles, then import their additive captured context."""
from pathlib import Path
import sys
import unreal

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from import_south_fork_composite_tiles import main

try:
    main()
    main(
        source_path=ROOT/'unreal/SourceArt/RaftSim/SouthForkCompositeTerrain20260912/ContextTiles1024m/manifest.json',
        asset_directory='/Game/RaftSim/Environment/SouthForkReconstruction/FullReach/ContextTiles',
        report_path=ROOT/'unreal/Saved/RaftSimValidation/south-fork-context-tiles-20260912.json',
        material_path='/Game/RaftSim/Environment/SouthForkReconstruction/FullReach/MI_SouthForkCompositeGround')
finally:
    unreal.SystemLibrary.quit_editor()
