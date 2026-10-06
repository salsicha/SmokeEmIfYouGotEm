"""Audit shipped-candidate payloads against the source packets and 600 s cook.

Read-only except a fresh receipt. No recook, engine launch, or acceptance claim.
"""
import argparse
import json
from pathlib import Path

import numpy as np

from audit_south_fork_discharge_bed_tiles import require, verified
from package_runtime_bundle import relative_dependency, sha, verify_bundle

ROOT = Path(__file__).resolve().parents[2]


def preserved_packet(source_bed, source_mask, owner, runtime_bed, runtime_mask, datum):
    require(source_bed.shape == source_mask.shape == owner.shape == runtime_bed.shape == runtime_mask.shape,
            'Packet shape mismatch')
    require(np.array_equal(source_mask, runtime_mask), 'Captured water mask changed')
    protected = ~np.isin(owner, (1, 4))
    expected = source_bed[protected] - datum
    require(np.array_equal(expected, runtime_bed[protected]), 'Registered/protected bed changed')
    require(np.isfinite(runtime_bed).all(), 'Nonfinite runtime bed')
    return int(protected.sum()), int(source_mask.size)


def audit(bundle, export, cook, imports):
    inventory = verify_bundle(bundle)
    payloads = {row['destination']: bundle / row['source'] for row in inventory['files']}
    export_report = json.loads(export.read_text())
    sources_path = verified(ROOT / export_report['source_packets_manifest'], export_report['source_packets_manifest_sha256'])
    sources = json.loads(sources_path.read_text())
    entries = inventory['entrypoints']
    stream_path = payloads[entries['streaming_manifest']]
    require(sha(stream_path) == export_report['streaming_manifest_sha256'], 'Wrong runtime stream')
    windows = json.loads(stream_path.read_text())['windows']
    require([w['window_id'] for w in windows] == [r['name'] for r in sources['regions']], 'Packet order changed')
    # Saved normal-scene bindings must still match the frozen bundle inventory.
    for asset in inventory['saved_scene_assets']:
        verified(ROOT / asset['path'], asset['sha256'])
    result = dict(schema='raftsim.south_fork.discharge_runtime_audit.v1', bundle_manifest_sha256=sha(bundle / 'manifest.json'),
                  windows_checked=0, protected_packet_cells_checked=0, captured_mask_cells_checked=0,
                  saved_scene_hashes_checked=len(inventory['saved_scene_assets']),
                  engine_started=False, fresh_collision_traces=False, settled_hydraulics=False,
                  normal_menu_motion_verified=False, performance_accepted=False, full_reconstruction_accepted=False)
    atlas_logical = None
    for window, source in zip(windows, sources['regions']):
        logical = window['cooked_fields_manifest']
        fields = json.loads(payloads[logical].read_text())
        require(fields['discharge_bed_manifest_sha256'] == export_report['discharge_bed_manifest_sha256'], 'Mixed bed version')
        band = fields['bands'][0]
        shared = relative_dependency(logical, band['shared_cartesian_state']['manifest'])
        require(atlas_logical is None or shared == atlas_logical, 'Multiple state atlases')
        atlas_logical = shared
        require(fields['source_geometry_sha256'] == source['geometry_sha256'], 'Wrong source packet')
        source_path = verified(ROOT / source['geometry_file'], source['geometry_sha256'])
        arrays = band['arrays']
        with np.load(source_path, allow_pickle=False) as original:
            bed = np.load(payloads[relative_dependency(logical, arrays['bed']['file'])], allow_pickle=False)
            mask = np.load(payloads[relative_dependency(logical, arrays['captured_water_mask']['file'])], allow_pickle=False)
            protected, masks = preserved_packet(original['bed_navd88_m'], original['captured_water_mask'],
                                                 original['terrain_owner'], bed, mask, fields['source_elevation_datum_m'])
        result['windows_checked'] += 1
        result['protected_packet_cells_checked'] += protected
        result['captured_mask_cells_checked'] += masks
    atlas = json.loads(payloads[atlas_logical].read_text())
    require(sha(payloads[atlas_logical]) == export_report['atlas_manifest_sha256'], 'Wrong atlas')
    arrays = atlas['arrays']
    for name in ('h', 'u', 'v'):
        require(sha(payloads[relative_dependency(atlas_logical, arrays[name]['file'])]) == sha(cook / 'frame_012000' / (name + '.npy')),
                'Packaged state differs from completed cook: ' + name)
    flow = json.loads((cook / 'input_manifest.json').read_text())
    require(sha(cook / 'input_manifest.json') == atlas['input_manifest_sha256'], 'Wrong cook input')
    complete = json.loads((cook / 'frame_012000/complete.json').read_text())
    require(complete['step'] == 12000 and complete['snapshot'], 'Incomplete cook snapshot')
    input_path = Path((cook / 'input_manifest_path.txt').read_text().strip())
    require(sha(input_path) == atlas['input_manifest_sha256'], 'Cook input changed')
    require(len(atlas['tiles']) == len(flow['packages']), 'Atlas tile count mismatch')
    beds = np.load(payloads[relative_dependency(atlas_logical, arrays['bed']['file'])], mmap_mode='r', allow_pickle=False)
    records = {row['name']: row for row in flow['inputs']}
    for index, name in enumerate(flow['packages']):
        original_path = verified(input_path.parent / name / 'bed.npy', records[name]['files']['bed.npy'])
        require(np.array_equal(beds[index * 80:(index + 1) * 80], np.load(original_path, allow_pickle=False)), 'Atlas/cook bed mismatch')
        grid = json.loads((input_path.parent / name / 'scenario.json').read_text())['grid']
        require(atlas['tiles'][index]['origin_m'] == [grid['origin_x'], grid['origin_y']], 'Atlas/cook origin mismatch')
    result['atlas_tiles_checked'] = len(atlas['tiles'])
    result['atlas_bed_cells_checked'] = int(beds.size)
    result['snapshot_time_seconds'] = complete['time_seconds']
    result['imported_terrain_assets_checked'] = 0
    # Verify saved packages still match the owner's completed import receipts.
    # This is NOT a second collision trace or fresh engine readback.
    result['import_receipts'] = []
    for receipt_path in imports:
        receipt = json.loads(receipt_path.read_text())
        require(receipt['completed'], 'Incomplete terrain import')
        for tile in receipt['tiles']:
            require(tile['asset'].startswith('/Game/'), 'Nonproject asset')
            verified(ROOT / ('unreal/Content/' + tile['asset'][6:] + '.uasset'), tile['asset_sha256_after'])
        result['imported_terrain_assets_checked'] += len(receipt['tiles'])
        result['import_receipts'].append(dict(path=receipt_path.relative_to(ROOT).as_posix(), sha256=sha(receipt_path)))
    result['passed'] = True
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--export', type=Path, required=True)
    parser.add_argument('--cook', type=Path, required=True)
    parser.add_argument('--imports', type=Path, nargs='+', required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    require(not args.report.exists(), 'Fresh report required')
    result = audit(args.bundle.resolve(), args.export, args.cook, [p.resolve() for p in args.imports])
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
