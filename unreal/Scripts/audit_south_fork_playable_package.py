"""Fresh-process dependency closure for the saved normal gameplay map."""
import json
from pathlib import Path
import unreal

registry = unreal.AssetRegistryHelpers.get_asset_registry()
registry.search_all_assets(synchronous_search=True)
options = unreal.AssetRegistryDependencyOptions(include_soft_package_references=True, include_hard_package_references=True)
seen = set()
pending = ['/Game/RaftSim/Maps/L_SouthFork_Troublemaker']
while pending:
    package = pending.pop()
    if package in seen or not package.startswith('/Game/'):
        continue
    assert not package.startswith('/Game/RaftSim/Maps/Review/'), package
    assert not package.startswith('/Game/RaftSim/Environment/SouthForkSurveyCandidate/'), package
    seen.add(package)
    pending.extend(str(p) for p in registry.get_dependencies(package, options))
for asset in ('M_TroublemakerCapturedGround','T_TroublemakerNAIP','T_TroublemakerSurfaceAuthority','SM_TroublemakerCapturedGround'):
    assert '/Game/RaftSim/Environment/SouthForkReconstruction/Troublemaker/'+asset in seen
assert any('T_RockGround_BaseColor' in p for p in seen)
assert any('FoamLace' in p for p in seen)
output = Path(unreal.Paths.project_saved_dir()) / 'RaftSimValidation/southfork-playable-package-surface-20260912.json'
output.write_text(json.dumps({'fresh_process': True, 'game_dependencies': sorted(seen),
                              'no_never_cook_review_dependencies': True}, indent=2))
unreal.log(f'Fresh playable package dependency audit passed: {len(seen)} game assets')
