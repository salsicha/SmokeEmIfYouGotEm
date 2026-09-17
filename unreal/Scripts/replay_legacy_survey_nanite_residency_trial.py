"""Reproduce the rejected September17 LEGACY survey-candidate residency trial.

This is NOT the current playable captured-ground mesh. The trial was restored
and does not diagnose residency of SM_TroublemakerCapturedGround. Explicit
authoring ablation only; preserve the backup and never treat it as acceptance.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import unreal

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = '/Game/RaftSim/Environment/SouthForkRockRegisteredCandidate20260907/SM_TroublemakerSurveyCandidate'
EXPECTED = '12ba8d8ac76f378cedfdb6c5cc8bd7e8708b0914a9aa43c9389e6753e0d90d56'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def native_geometry_hashes(mesh):
    """Exact native fallback positions, indices, normals and UVs at every LOD."""
    rows = []
    for lod in range(mesh.get_num_lods()):
        for section in range(mesh.get_num_sections(lod)):
            positions, indices, normals, uvs, _ = unreal.ProceduralMeshLibrary.get_section_from_static_mesh(mesh, lod, section)
            assert positions and indices and len(indices) % 3 == 0
            digest = hashlib.sha256()
            for values, fields in ((positions, ('x', 'y', 'z')), (normals, ('x', 'y', 'z')), (uvs, ('x', 'y'))):
                digest.update(struct.pack('<Q', len(values)))
                for value in values:
                    digest.update(struct.pack('<'+'d'*len(fields), *(getattr(value, field) for field in fields)))
            digest.update(struct.pack('<Q', len(indices)))
            for index in indices:
                digest.update(struct.pack('<I', index))
            rows.append(dict(lod=lod, section=section, vertices=len(positions),
                triangles=len(indices)//3, native_geometry_sha256=digest.hexdigest()))
    return rows


def main():
    assert unreal.SystemLibrary.get_command_line().split().count('-RaftSimRebuildRapidNaniteResidency') == 1
    output = Path(os.environ['RAFTSIM_RESIDENCY_TRIAL']).resolve()
    assert output.is_relative_to(ROOT/'tmp') and not output.exists()
    source = ROOT/'unreal/Content'/f'{PACKAGE.removeprefix("/Game/")}.uasset'
    assert sha(source) == EXPECTED, 'Unexpected source package; preserve it'
    editor = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    assert editor is not None, 'Use -ExecutePythonScript; the commandlet lacks this editor subsystem'
    output.mkdir()
    backup = output/source.name
    shutil.copy2(source, backup)
    assert sha(backup) == EXPECTED
    mesh = unreal.load_asset(PACKAGE)
    assert isinstance(mesh, unreal.StaticMesh)
    settings = editor.get_nanite_settings(mesh)
    before = dict(enabled=settings.enabled,
        target_minimum_residency_in_kb=settings.get_editor_property('target_minimum_residency_in_kb'),
        keep_percent_triangles=settings.keep_percent_triangles,
        trim_relative_error=settings.trim_relative_error,
        fallback_percent_triangles=settings.fallback_percent_triangles,
        fallback_relative_error=settings.fallback_relative_error,
        position_precision=settings.position_precision)
    counts = [mesh.get_num_triangles(i) for i in range(mesh.get_num_lods())]
    geometry_before = native_geometry_hashes(mesh)
    assert counts[0] == 803842 and before['enabled']
    assert before['keep_percent_triangles'] == 1 and before['trim_relative_error'] == 0
    assert before['fallback_percent_triangles'] == 1 and before['fallback_relative_error'] == 0
    body = mesh.get_editor_property('body_setup')
    collision = body.get_editor_property('collision_trace_flag')
    assert collision == unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE
    # EngineTypes.h explicitly defines MAX_uint32 as the whole resource.
    # Only this captured rapid changes; no global Nanite or LOD quality override.
    settings.set_editor_property('target_minimum_residency_in_kb', 4294967295)
    editor.set_nanite_settings(mesh, settings)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    assert counts == [mesh.get_num_triangles(i) for i in range(mesh.get_num_lods())]
    assert geometry_before == native_geometry_hashes(mesh), 'Native fallback geometry or shading changed'
    assert body.get_editor_property('collision_trace_flag') == collision
    assert editor.get_nanite_settings(mesh).get_editor_property('target_minimum_residency_in_kb') == 4294967295
    assert unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
    report = dict(accepted=False, package=PACKAGE, before=before,
        source_sha256=EXPECTED, backup=str(backup), backup_sha256=sha(backup),
        candidate_sha256=sha(source), lod_triangle_counts=counts,
        native_geometry_before_and_after=geometry_before, exact_native_geometry_unchanged=True,
        collision_trace_flag=str(collision), target_minimum_residency_in_kb=4294967295,
        scope='Nanite residency build setting only. No source/fallback simplification, collision policy, water or material edit. Actual rendered geometry, residency memory cost, performance and release acceptance remain required.')
    with (output/'report.json').open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2)
    unreal.log(f'Rapid Nanite residency trial saved: {output}')


if __name__ == '__main__':
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
