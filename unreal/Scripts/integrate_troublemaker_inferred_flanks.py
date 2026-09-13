"""Replace the normal playable ground with matched, explicitly inferred flanks."""
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import integrate_troublemaker_sparse_rock_support as delivery

delivery.SOURCE = delivery.ROOT/'unreal/SourceArt/RaftSim/TroublemakerInferredRockFlanks20260912'
delivery.GEOMETRY = delivery.ROOT/'tmp/troublemaker-inferred-rock-flanks-20260912'
delivery.BACKUP = delivery.ROOT/'tmp/troublemaker-playable-before-inferred-flanks-20260912'
delivery.REPORT = delivery.ROOT/'unreal/Saved/RaftSimValidation/troublemaker-inferred-flanks-integration-20260912.json'
delivery.EXPECTED_LEVEL_SHA = '5e5bfe7f7b90919d04d8c8db0b2b0f15c4b99a5b5f5253b1e5fc7c7e8164a50f'
delivery.EXPECTED_MESH_SHA = '1ffe2b72bf1805d0d9bc722e94ab645e0c84ab162721b6560e7e789890e51a21'
delivery.MASK_SOURCE = delivery.ROOT/'unreal/SourceArt/RaftSim/TroublemakerInferredFlankAuthority20260912'
delivery.GROUND_LABEL = 'Captured ground and rock anchors - explicitly inferred connecting flanks and submerged bed'

try:
    delivery.main()
finally:
    unreal.SystemLibrary.quit_editor()
