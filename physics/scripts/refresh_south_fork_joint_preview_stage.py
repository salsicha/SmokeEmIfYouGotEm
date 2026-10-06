"""Rebind a preview after proven CPU-retention metadata changes, never geometry.

Preserve the original stage and require independent native readback of the new
package. This does not import/save assets or promote a preview into normal play.
"""
import argparse
import json
from pathlib import Path

from prepare_south_fork_joint_preview import ROOT, asset_file, require
from source_asset_retention import RECEIPT, retained_asset_digest
from south_fork_rock_union import sha


def refresh(stage_path, collision_path, *, root=ROOT, receipt=RECEIPT):
    stage = json.loads(Path(stage_path).read_text())
    collision = json.loads(Path(collision_path).read_text())
    mesh = asset_file(stage['mesh_asset'], root)
    require(mesh == (root / stage['mesh_file']).resolve(), 'Mesh file mismatch')
    digest = retained_asset_digest(mesh, stage['mesh_sha256'], root=root, receipt=receipt)
    require(digest != stage['mesh_sha256'], 'No metadata revision to rebind')
    document = json.loads(Path(receipt).read_text())
    rows = [r for r in document['assets'] if asset_file(r['asset'], root) == mesh]
    require(len(rows) == 1, 'Unique retained package required')
    row = rows[0]
    require(digest == row['retained_asset_sha256'] and
            stage['mesh_sha256'] == row['original_asset_sha256'], 'Not the recorded revision')
    require(row['material_paths'] == [stage['material_asset']], 'Material assignment changed')
    for name, digest_key in [('material_asset', 'material_sha256'),
                             ('parent_material', 'parent_material_sha256')]:
        require(sha(asset_file(stage[name], root)) == stage[digest_key], 'Material package changed')
    require(stage['world_position_offset'] is False and
            stage['original_materials_unchanged'] is True, 'Original material proof required')
    require(collision.get('saved_candidate_verified') is True and
            asset_file(collision['saved_candidate_asset'], root) == mesh and
            collision['saved_candidate_sha256'] == digest and
            collision['saved_candidate_source_sha256'] == row['after']['collision_source_sha256'],
            'Fresh saved native source mismatch')
    require(collision.get('failures') == [] and collision['sampled_full_map_union_verified'] is True and
            collision['native_runtime']['field_queries_verified'] is True, 'Native union/field proof failed')
    require(all(collision[k] is False for k in ('saved_assets', 'saved_levels', 'water_state_modified')),
            'Read-only native proof required')
    require(stage['triangle_count'] == row['after']['triangle_count'] and
            stage['source_cap_sha256'] == collision['source_cap_sha256'] and
            stage['fbx_sha256'] == collision['fbx_sha256'] and
            stage['translation_cm'] == collision['candidate_translation_cm'] and
            stage['scale'] == [1, -1, 1], 'Different geometry or transform')
    result = dict(stage, mesh_sha256=digest, collision_report_sha256=sha(collision_path))
    result['cpu_retention_rebind'] = {
        'original_stage': Path(stage_path).resolve().relative_to(root).as_posix(),
        'original_stage_sha256': sha(stage_path),
        'retention_receipt': Path(receipt).resolve().relative_to(root).as_posix(),
        'retention_receipt_sha256': sha(receipt),
        'native_collision_report': Path(collision_path).resolve().relative_to(root).as_posix(),
        'source_geometry_unchanged': True,
    }
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', type=Path)
    parser.add_argument('collision', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    require(output.is_relative_to(ROOT / 'tmp') and not output.exists(), 'Fresh tmp output required')
    result = refresh(args.stage, args.collision)
    with output.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'stage': str(output), 'sha256': sha(output), 'production_promoted': False}))
