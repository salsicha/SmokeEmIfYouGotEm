"""Read-only asset-reference inventory used before retiring project content.

Run in UnrealEditor-Cmd with -ExecutePythonScript. This never opens, modifies,
saves, or deletes a map. Source/config references must be checked separately.
"""
from pathlib import Path
import json
import unreal

ROOT=Path(__file__).resolve().parents[2]
registry=unreal.AssetRegistryHelpers.get_asset_registry()
registry.search_all_assets(synchronous_search=True)
options=unreal.AssetRegistryDependencyOptions(
    include_soft_package_references=True,include_hard_package_references=True,
    include_searchable_names=True,include_soft_management_references=True,
    include_hard_management_references=True)
maps=[]
for file in sorted((ROOT/'unreal/Content/RaftSim/Maps').rglob('*.umap')):
    package='/Game/'+file.relative_to(ROOT/'unreal/Content').with_suffix('').as_posix()
    maps.append({'package':package,'file':file.relative_to(ROOT).as_posix(),'bytes':file.stat().st_size,
        'referencers':sorted(str(p) for p in registry.get_referencers(package,options)),
        'dependencies':sorted(str(p) for p in registry.get_dependencies(package,options))})
report={'kind':'read_only_asset_registry_inventory','maps':maps,
    'note':'No references is not sufficient proof of unused content: check C++, config and scripts too.'}
out=ROOT/'tmp/project-cleanup/asset_inventory.json';out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(report,indent=2),encoding='utf-8')
unreal.log(f'Project asset audit: {len(maps)} maps; {out}')
