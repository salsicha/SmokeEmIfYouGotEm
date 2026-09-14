"""Exact flat-pool/dry-rock fixtures for both native samplers; not river data."""
import copy
import json
from pathlib import Path
import prepare_cartesian_atlas_fixture as arrays


def main():
    root = Path(__file__).resolve().parents[2]
    output = root / 'tmp/cartesian-dry-rock-fixture-v1'
    output.mkdir(exist_ok=False)
    template = root / 'tmp/cartesian-atlas-fixture-v1'
    for axis in ('x', 'y'):
        directory = output / axis
        directory.mkdir()
        arrays.ROOT = directory
        def bed(r, c):
            return 2. if (c if axis == 'x' else r) >= 6 else 0.
        def global_rc(r, c):
            owner, row = divmod(r, 12)
            return row + (owner // 2)*12, c + (owner % 2)*12
        formulas = dict(bed=bed, h=lambda r, c: max(1.-bed(r, c), 0.),
                        u=lambda r, c: 0., v=lambda r, c: 0.)
        atlas = json.loads((template / 'atlas_valid/manifest.json').read_text())
        atlas['arrays'] = {key: arrays.array(key+'.npy', 48, 12,
            lambda r, c, f=f: f(*global_rc(r, c))) for key, f in formulas.items()}
        (directory / 'atlas').mkdir()
        digest = arrays.json_file(directory / 'atlas/manifest.json', atlas)
        packet = copy.deepcopy(json.loads((template / 'valid/manifest.json').read_text()))
        packet['bands'][0]['arrays'] = dict(
            bed=arrays.array('packet_bed.npy', 29, 31, bed),
            captured_water_mask=arrays.array('captured.npy', 29, 31, lambda r, c: 1, '|u1'))
        packet['bands'][0]['shared_cartesian_state'] = dict(manifest='../atlas/manifest.json', sha256=digest)
        (directory / 'packet').mkdir()
        arrays.json_file(directory / 'packet/manifest.json', packet)
    print(output)


if __name__ == '__main__':
    main()
