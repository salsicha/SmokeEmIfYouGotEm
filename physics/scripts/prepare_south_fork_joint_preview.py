"""Bind a candidate rock and audited hydraulic state for ephemeral editor play.

No default scenario/asset is changed. This is a preview, not settled hydraulics,
raft contact, visual or performance acceptance. Dependencies remain local files.
"""
import argparse
import json
import math
from pathlib import Path

from south_fork_rock_union import sha
from south_fork_rock_union_packets import dependencies as source_dependencies

ROOT = Path(__file__).resolve().parents[2]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def asset_file(asset, root=ROOT):
    require(asset.startswith('/Game/'), 'Only project assets are permitted')
    require('..' not in asset and '\\' not in asset, 'Invalid asset path')
    package = asset[6:].split('.')[0]
    require(package and all(package.split('/')), 'Invalid asset package')
    path = (root / 'unreal/Content' / (package + '.uasset')).resolve()
    require(path.is_relative_to((root / 'unreal/Content').resolve()), 'Asset escapes content')
    return path


class Dependencies:
    def __init__(self, root=ROOT):
        self.root = Path(root).resolve()
        self.hashes = {}

    def add(self, path, expected=None):
        path = Path(path).resolve()
        require(path.is_relative_to(self.root), 'Dependency escapes repository')
        name = path.relative_to(self.root).as_posix()
        digest = self.hashes.get(name)
        if digest is None:
            digest = sha(path)
            self.hashes[name] = digest
        require(expected is None or digest == expected, 'Changed dependency: ' + name)
        return name

    def read(self, path, expected=None):
        self.add(path, expected)
        return json.loads(Path(path).read_text())


def verify_audits(atlas, snapshot, banks, coverage, atlas_hash, stream_hash):
    require(snapshot['passed'] is True, 'Snapshot failed')
    require(banks['all_artificial_banks_exactly_dry'] is True and
            banks['maximum_bank_depth_m'] == 0, 'Artificial bank is wet')
    require(coverage['passed'] is True and not coverage['failed_rectangles'], 'Coverage failed')
    require(coverage['minimum_raft_interior_margin_m'] >= 8 and
            coverage['original_water_probes'] == 406823, 'Original coverage gate changed')
    require(coverage['atlas_manifest_sha256'] == atlas_hash and
            coverage['repaired_streaming_manifest_sha256'] == stream_hash, 'Coverage belongs to another export')
    require(atlas['input_manifest_sha256'] == snapshot['input_manifest_sha256'] ==
            banks['input_manifest_sha256'], 'Audits belong to different flow inputs')
    time = atlas['source_time_seconds']
    require(math.isfinite(time) and time > 0 and
            abs(time - snapshot['time_seconds']) <= 1e-9 and
            abs(time - banks['time_seconds']) <= 1e-9 and
            snapshot['step'] == banks['step'], 'Audits belong to different snapshots')
    for name in ('h', 'u', 'v'):
        require(atlas['arrays'][name]['sha256'] == snapshot['arrays'][name]['sha256'],
                'Snapshot array mismatch: ' + name)
    require(atlas['arrays']['h']['sha256'] == banks['h_sha256'], 'Bank audit has different water')


def prepare(args):
    output = args.output.resolve()
    require(not output.exists() and output.is_relative_to(ROOT / 'tmp'), 'Fresh project tmp output required')
    deps = Dependencies()
    export = args.export.resolve()
    atlas_path = export / 'atlas/manifest.json'
    stream_path = export / 'streaming_manifest_coverage_checked.json'
    atlas = deps.read(atlas_path)
    atlas_hash = sha(atlas_path)
    stream = deps.read(stream_path)
    snapshot = deps.read(args.snapshot_audit)
    banks = deps.read(args.bank_audit, atlas['bank_audit_sha256'])
    coverage = deps.read(args.coverage_audit)
    verify_audits(atlas, snapshot, banks, coverage, atlas_hash, sha(stream_path))
    geometry, source_path, source, union = source_dependencies(args.geometry_manifest.resolve())
    deps.add(args.geometry_manifest)
    require(geometry['terrain_union'] == atlas['terrain_union'] == union.identity, 'Different terrain union')
    flow = deps.read(args.flow_input, atlas['input_manifest_sha256'])
    # The cold input carries the exact geometry SHA, not the old captured bed.
    require(flow['geometry_manifest_sha256'] == sha(args.geometry_manifest), 'Different hydraulic geometry')
    cap_path = ROOT / geometry['rock_cap_manifest']
    cap = deps.read(cap_path, union.identity['cap_manifest_sha256'])
    for name in ('source_mesh', 'original_returns', 'cap'):
        deps.add(ROOT / cap[name + '_path'], cap[name + '_sha256'])
    deps.add(source_path, geometry['source_manifest_sha256'])
    for row in geometry['regions']:
        deps.add(ROOT / row['geometry_file'], row['geometry_sha256'])
    for meta in atlas['arrays'].values():
        deps.add(atlas_path.parent / meta['file'], meta['sha256'])
    coordinate_path = source_path.parent / 'coordinate_map.json'
    deps.add(coordinate_path, geometry['coordinate_map_sha256'])
    chosen = None
    for window in stream['windows']:
        fields_path = ROOT / window['cooked_fields_manifest']
        fields = deps.read(fields_path)
        for band in fields['bands']:
            shared = band['shared_cartesian_state']
            require((fields_path.parent / shared['manifest']).resolve() == atlas_path,
                    'Streaming packet points to different water')
            require(shared['sha256'] == atlas_hash, 'Streaming packet atlas hash mismatch')
            for meta in band['arrays'].values():
                deps.add(fields_path.parent / meta['file'], meta['sha256'])
        if window['window_id'] == args.initial_window:
            chosen = fields_path
            x, y = args.center
            require(all(math.isfinite(v) for v in args.center) and any(
                r[0] <= x <= r[2] and r[1] <= y <= r[3]
                for r in window['valid_live_center_bounds_m']), 'Initial center outside verified coverage')
    require(chosen is not None and len(stream['windows']) == 799, 'Incomplete source-window collection')
    render = deps.read(args.render_stage)
    collision = deps.read(args.collision_audit, render['collision_report_sha256'])
    require(render['source_cap_sha256'] == collision['source_cap_sha256'] == union.identity['cap_sha256'],
            'Different source rock in render or collision')
    require(render['fbx_sha256'] == collision['fbx_sha256'] and
            collision['sampled_full_map_union_verified'] is True and
            collision['native_runtime']['field_queries_verified'] is True, 'Collision/native evidence failed')
    require(render['translation_cm'] == collision['candidate_translation_cm'] and render['scale'] == [1, -1, 1],
            'Render and collision transform differ')
    require(render['world_position_offset'] is False and render['original_materials_unchanged'] is True,
            'Preview changed physical geometry through material')
    mesh_path = asset_file(render['mesh_asset'])
    require(mesh_path == (ROOT / render['mesh_file']).resolve(), 'Mesh asset/file mismatch')
    deps.add(mesh_path, render['mesh_sha256'])
    material_path = asset_file(render['material_asset'])
    deps.add(material_path, render['material_sha256'])
    deps.add(asset_file(render['parent_material']), render['parent_material_sha256'])
    files = dict(streaming_manifest=stream_path, initial_fields_manifest=chosen,
                 coordinate_map=coordinate_path, mesh_file=mesh_path, material_file=material_path,
                 geometry_manifest=args.geometry_manifest, flow_input_manifest=args.flow_input, atlas_manifest=atlas_path,
                 snapshot_audit=args.snapshot_audit, bank_audit=args.bank_audit,
                 coverage_audit=args.coverage_audit, render_stage=args.render_stage,
                 collision_audit=args.collision_audit)
    result = dict(schema='raftsim.south_fork_joint_preview.v1', candidate=True, production_promoted=False,
                  target_level='/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach',
                  **{key: deps.add(path) for key, path in files.items()},
                  mesh_asset=render['mesh_asset'], material_asset=render['material_asset'],
                  source_cap_sha256=union.identity['cap_sha256'], translation_cm=render['translation_cm'],
                  scale=render['scale'], window_center_m=args.center, dependencies=deps.hashes,
                  source_time_seconds=atlas['source_time_seconds'], settled_hydraulics=False,
                  visual_accepted=False, performance_accepted=False)
    output.write_text(json.dumps(result, indent=2) + '\n')
    return dict(descriptor=output.relative_to(ROOT).as_posix(), sha256=sha(output),
                dependency_count=len(deps.hashes), source_time_seconds=atlas['source_time_seconds'],
                production_promoted=False)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('export', type=Path)
    for option in ('geometry-manifest', 'flow-input', 'snapshot-audit', 'bank-audit',
                   'coverage-audit', 'render-stage', 'collision-audit', 'output'):
        p.add_argument('--' + option, type=Path, required=True)
    p.add_argument('--initial-window', required=True)
    p.add_argument('--center', type=float, nargs=2, required=True)
    print(json.dumps(prepare(p.parse_args()), indent=2), flush=True)
