"""Install only the engine-reviewed optical lattice hash, with exact rollback.

Run with -RaftSimInstallIntegerNormalHash, then run without that flag in a fresh
editor for read-only persisted graph verification. No geometry/foam changes.
"""
import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT/'tmp/south-fork-integer-normal-hash-install-v1-20260917.json'


def main():
    import unreal
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import integrate_south_fork_local_froth as source
    from create_south_fork_normal_filter_review import BASELINE, control_code
    from raftsim_material_graph_signature import canonical_graph
    install = 'RaftSimInstallIntegerNormalHash' in unreal.SystemLibrary.get_command_line()
    output = REPORT if install else REPORT.with_name('south-fork-integer-normal-hash-reload-v1-20260917.json')
    if output.exists():
        raise FileExistsError(output)
    shader = (ROOT/'unreal/Shaders/Private/RaftSimLocalCurrentNormal.hlsl').read_text()
    material = unreal.load_asset(source.PATH)
    assert material
    lib = unreal.MaterialEditingLibrary
    nodes = list(lib.get_material_expressions(material))
    normal, = [n for n in nodes if n.get_editor_property('desc') == 'SouthForkCurrentGradientNormalV1']

    def all_nodes():
        return {n.get_name(): canonical_graph(source.graph(material, n)[n.get_name()]) for n in nodes}

    def protected():
        properties = ('MP_WORLD_POSITION_OFFSET', 'MP_BASE_COLOR', 'MP_ROUGHNESS', 'MP_OPACITY', 'MP_OPACITY_MASK')
        return canonical_graph({p: source.graph(material, lib.get_material_property_input_node(
            material, getattr(unreal.MaterialProperty, p))) for p in properties})

    before_hash = source.sha(source.FILE)
    if not install:
        evidence = json.loads(REPORT.read_text())
        assert before_hash == evidence['installed_sha256']
        assert normal.get_editor_property('code') == shader
        assert all_nodes() == evidence['installed_nodes']
        assert protected() == evidence['protected_graphs']
        assert source.sha(source.FILE) == before_hash
        result = dict(read_only_reload_passed=True, material_sha256=before_hash,
                      source_shader_matches=True, all_saved_nodes_exact=True)
    else:
        assert before_hash == BASELINE, 'Unreviewed production material revision'
        review = json.loads((ROOT/'tmp/south-fork-normal-filter-review_integer_hash-v1-20260917.json').read_text())
        candidate = unreal.load_asset(review['material'])
        assert candidate
        candidate_file = ROOT/'unreal/Content'/(review['material'].removeprefix('/Game/')+'.uasset')
        assert source.sha(candidate_file) == review['material_sha256']
        candidate_normal, = [n for n in lib.get_material_expressions(candidate)
                             if n.get_editor_property('desc') == 'SouthForkCurrentGradientNormalV1']
        assert control_code(normal.get_editor_property('code'), 'integer-hash') == shader
        assert candidate_normal.get_editor_property('code') == shader
        assert review['source_sha256'] == before_hash and review['source_unchanged']
        expected = all_nodes()
        expected[normal.get_name()]['code'] = shader
        protected_before = protected()
        assert protected_before == review['protected_graphs']
        backup = REPORT.with_suffix('.backup.zip')
        relative = source.FILE.relative_to(ROOT).as_posix()
        with zipfile.ZipFile(backup, 'x', zipfile.ZIP_DEFLATED) as archive:
            archive.write(source.FILE, relative)
        with zipfile.ZipFile(backup) as archive:
            assert hashlib.sha256(archive.read(relative)).hexdigest() == before_hash
        normal.set_editor_property('code', shader)
        assert all_nodes() == expected and protected() == protected_before
        lib.recompile_material(material)
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
        assert unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
        result = dict(source_sha256=before_hash, installed_sha256=source.sha(source.FILE),
                      backup=str(backup), installed_nodes=expected, protected_graphs=protected_before,
                      only_optical_hash_changed=True, candidate_sha256=review['material_sha256'])
    result.update(physical_accepted=False, visual_accepted=False, performance_accepted=False, release_accepted=False)
    with output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
    unreal.log('Integer normal hash evidence: '+str(output))


if __name__ == '__main__':
    import unreal
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
