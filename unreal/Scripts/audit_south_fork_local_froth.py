"""Fresh read-only local-froth graph and package verification."""
import json
from pathlib import Path
import sys
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import integrate_south_fork_local_froth as setup
from raftsim_material_graph_signature import canonical_graph


def main():
    output=setup.REPORT.with_name('south-fork-local-froth-fresh-v2-20260912.json')
    assert not output.exists()
    previous=json.loads(setup.REPORT.read_text())
    assert setup.sha(setup.FILE)==previous['material_sha256']
    assert setup.sha(setup.SHADER)==previous['shader_sha256']
    material=unreal.load_asset(setup.PATH)
    result=setup.verify(material)
    protected=setup.protected_graphs(material)
    assert canonical_graph(protected)==canonical_graph(previous['protected_graphs'])
    assert canonical_graph(result['local_lace_graph'])==canonical_graph(previous['local_lace_graph'])
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    assert setup.sha(setup.FILE)==previous['material_sha256']
    result.update(fresh_process=True, read_only=True, material_sha256=previous['material_sha256'],
        protected_graphs_unchanged=True, photoreal_accepted=False,
        signature_normalization='Only process-local Python wrapper addresses removed from texture/default_value fields; paths, numeric values, code and all links retained.',
        protected_graphs=canonical_graph(protected))
    output.write_text(json.dumps(result,indent=2)+'\n')
    unreal.log(f'Fresh local froth graph verified: {output}')


if __name__=='__main__':
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
