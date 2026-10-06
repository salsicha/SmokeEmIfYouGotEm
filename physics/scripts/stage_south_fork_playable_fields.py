"""Package the source-matched bounded rapid without re-cooking or moving data."""
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'tmp/south-fork-survey-hydraulics/1m-mixed-inlet-registered-rock-xy-20260907/engine_review'
DEST = ROOT / 'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/troublemaker/playable_flow'
COORDINATES = DEST.parent / 'geographic_engine_review/coordinate_map.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy_verified(source, destination, expected):
    assert sha(source) == expected, source
    if destination.exists():
        assert sha(destination) == expected, f'Existing delivery differs: {destination}'
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    assert sha(destination) == expected


def main():
    manifest = json.loads((SOURCE / 'manifest.json').read_text())
    review = manifest['review']
    assert review['source_geometry_sha256'] == '4b0dfeac342607c118e91b2182fced676b4fc0c9ea08c2ff70e2166818255d40'
    assert review['source_bed_sampling'] == 'registered_triangles'
    geometry = json.loads((ROOT / review['source_geometry_manifest']).read_text())
    assert sha(ROOT / geometry['mesh_path']) == review['source_geometry_sha256']
    assert review['saved_frame_sanity'] and all(f['passed'] for f in review['saved_frame_sanity'])
    assert manifest['solver']['runtime_replay_offline_config']
    coordinates = json.loads(COORDINATES.read_text())
    assert coordinates['world_y_sign'] == -1
    files = {'manifest.json': (SOURCE / 'manifest.json', sha(SOURCE / 'manifest.json')),
             'coordinate_map.json': (COORDINATES, sha(COORDINATES))}
    for band in manifest['bands']:
        for array in band['arrays'].values():
            name = array['file']
            assert not Path(name).is_absolute() and '..' not in Path(name).parts
            files[name] = (SOURCE / name, array['sha256'])
    for name, (source, digest) in files.items():
        copy_verified(source, DEST / name, digest)
    delivery = {'schema': 'raftsim.captured_rapid_playable_delivery.v1',
                'source_fields': SOURCE.relative_to(ROOT).as_posix(),
                'source_geometry_sha256': review['source_geometry_sha256'],
                'files': {name: digest for name, (_, digest) in files.items()},
                'captured_coordinates_and_solver_arrays_unchanged': True,
                'bounded_playable_integration': True, 'full_reconstruction_accepted': False,
                'underwater_bed_measured': False,
                'scope': 'Bounded Troublemaker reconstruction; exposed captured geometry, inferred submerged bed; not the full South Fork route.'}
    (DEST / 'delivery.json').write_text(json.dumps(delivery, indent=2) + '\n')
    route_path = ROOT / 'docs/reconstruction-review-2026-09-07/guided-route-registered-rock.json'
    route = json.loads(route_path.read_text())
    assert route['cooked_fields_dir'] == SOURCE.relative_to(ROOT).as_posix()
    route['cooked_fields_dir'] = DEST.relative_to(ROOT).as_posix()
    route['source_route_sha256'] = sha(route_path)
    (route_path.parent / 'guided-route-playable.json').write_text(json.dumps(route, indent=2) + '\n')
    print(json.dumps(delivery, indent=2))


if __name__ == '__main__':
    main()
