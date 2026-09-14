"""Independently check game contact against the registered source triangles.

Only the interior registered footprint is covered. No bathymetry, hydraulic,
visual, performance, or whole-river acceptance is inferred from this audit.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'physics/scripts'))
from south_fork_registered_mesh import RegisteredMeshSampler


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def compare(probes, exact_cm):
    if not probes or len(probes) != len(exact_cm):
        raise ValueError('Nonempty matching independent ground heights required')
    counts = dict(points=len(probes), missing_ground=0, unavailable_support=0,
                  buried_points=0, buried_wet=0, raw_wet_clear_dry=0,
                  raw_dry_wet=0, classification_disagreements=0)
    errors = []
    for p, exact in zip(probes, exact_cm):
        if not np.isfinite([p['x_cm'], p['y_cm'], p['water_z_cm'], exact]).all():
            raise ValueError('Nonfinite probe')
        buried = p['water_z_cm'] <= exact
        counts['buried_points'] += int(buried)
        counts['buried_wet'] += int(buried and p['support_wet'])
        counts['unavailable_support'] += int(not p['support_available'])
        counts['missing_ground'] += int(not p['ground_hit'])
        if p['ground_hit']:
            if not np.isfinite(p['ground_z_cm']):
                raise ValueError('Nonfinite collision ground')
            errors.append(abs(p['ground_z_cm']-exact))
            counts['classification_disagreements'] += int(buried != (p['water_z_cm'] <= p['ground_z_cm']))
        counts['raw_wet_clear_dry'] += int(p['raw_available'] and p['raw_wet'] and not buried and not p['support_wet'])
        counts['raw_dry_wet'] += int((not p['raw_available'] or not p['raw_wet']) and p['support_wet'])
    counts['maximum_ground_error_cm'] = float(max(errors)) if errors else None
    counts['scoped_contact_pass'] = bool(all(counts[k] == 0 for k in
        ('missing_ground', 'unavailable_support', 'buried_wet', 'raw_wet_clear_dry',
         'raw_dry_wet', 'classification_disagreements')) and len(errors) == len(probes)
        and max(errors) <= .001)
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError(args.report)
    base = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach'
    mesh = base/'composite_terrain/troublemaker_registered_source.npz'
    geometry_path = base/'composite_terrain/manifest.json'
    mapping_path = base/'hydraulic_regions_context/coordinate_map.json'
    read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
    capture, geometry, mapping = map(read, (args.capture, geometry_path, mapping_path))
    if sha(mesh) != geometry['registered_rapid_sha256']:
        raise ValueError('Registered source provenance changed')
    with np.load(mesh, allow_pickle=False) as source:
        sampler = RegisteredMeshSampler(source)
    probes = capture['ground_contact_probes']
    world_xy = np.array([[p['x_cm'], p['y_cm']] for p in probes])*.01
    offset = np.array(mapping['world_origin_utm_m'])-geometry['rapid_origin_utm_m']
    local_xy = world_xy*[1, mapping['world_y_sign']]+offset
    # A full cell inset keeps the selected footprint inside registered triangles
    # even where boundary vertices moved. No outside clamping or gap filling.
    selected = ((local_xy[:, 0] >= sampler.east[0]+sampler.dx) &
                (local_xy[:, 0] <= sampler.east[-1]-sampler.dx) &
                (local_xy[:, 1] >= sampler.north[-1]+sampler.dy) &
                (local_xy[:, 1] <= sampler.north[0]-sampler.dy))
    exact = (sampler.sample(*local_xy[selected].T) +
             geometry['rapid_datum_navd88_m']-mapping['vertical_datum_m'])*100
    result = compare([p for p, keep in zip(probes, selected) if keep], exact)
    result.update(schema='raftsim.registered_ground_contact.v1', accepted=False,
                  scope=__doc__, total_exported_probes=len(probes),
                  outside_registered_interior=int((~selected).sum()),
                  outside_buried_wet=sum(p['ground_hit'] and p['water_z_cm'] <= p['ground_z_cm']
                      and p['support_wet'] for p, keep in zip(probes, selected) if not keep),
                  source_sha256={str(p): sha(p) for p in (args.capture, mesh,
                      geometry_path, mapping_path, Path(__file__),
                      ROOT/'physics/scripts/south_fork_registered_mesh.py')})
    encoded = json.dumps(result, indent=2) + '\n'
    with args.report.open('x', encoding='utf-8') as stream:
        stream.write(encoded)
    print(json.dumps(result, indent=2))
    if not result['scoped_contact_pass']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
