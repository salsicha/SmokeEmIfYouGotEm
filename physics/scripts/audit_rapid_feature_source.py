"""Audit an authored shared-kernel layout against hash-bound source geometry.

This does not solve water, assign a difficulty class, or accept a playable map.
The footprint matches RaftSimRapidChallengeProfiles::OverlapsReach. Reference
depth is constructed bathymetry, not a measured or accepted runtime depth.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def contained(root, name):
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Source path escapes its root')
    return path


def audit(candidate, root=ROOT):
    source = contained(root, candidate['source_directory'])
    expected = candidate['source_sha256']
    required = {'coordinate_map.json', 'reference.npz', 'scenario/bed.npy'}
    if set(expected) != required:
        raise ValueError('Bind coordinate map, reference and constructed bed')
    for name, value in expected.items():
        if digest(contained(source, name)) != value:
            raise ValueError('Source hash mismatch: ' + name)
    with np.load(source/'reference.npz', allow_pickle=False) as reference:
        x, y = reference['station'], reference['lateral']
        surface = reference['reference_surface']
        wet = reference['classified_water']
    bed = np.load(source/'scenario/bed.npy', allow_pickle=False)
    if (x.ndim != 1 or y.ndim != 1 or len(x) < 2 or len(y) < 2 or
            surface.shape != x.shape or bed.shape != (len(y), len(x)) or
            wet.shape != bed.shape or not np.isfinite(bed).all() or
            not np.isfinite(x).all() or not np.isfinite(y).all() or
            not np.isfinite(surface).all() or np.any(np.diff(x) <= 0) or
            np.any(np.diff(y) <= 0) or not np.isin(wet, [0, 1]).all()):
        raise ValueError('Invalid source grid')
    quiet = np.asarray(candidate['quiet_station_intervals_m'], dtype=float)
    if quiet.ndim != 2 or quiet.shape[1] != 2 or not np.isfinite(quiet).all() or np.any(quiet[:, 0] > quiet[:, 1]):
        raise ValueError('Invalid quiet intervals')
    features = candidate['features']
    if not features:
        raise ValueError('Empty feature layout')
    xx, yy = np.meshgrid(x, y)
    rows = []
    for feature in features:
        values = np.asarray(feature, dtype=float)
        if values.shape != (6,) or not np.isfinite(values).all():
            raise ValueError('Expected six finite shared-kernel feature values')
        station, lateral, angle, height, length, spill = values
        if not (0 < height <= 1.2 and 2 <= length <= 7 and 0 <= spill <= 1):
            raise ValueError('Outside existing shared-kernel bounds')
        if not (x[0] <= station <= x[-1] and y[0] <= lateral <= y[-1]):
            raise ValueError('Feature centre outside source grid')
        i, j = int(np.argmin(abs(x-station))), int(np.argmin(abs(y-lateral)))
        # Require exact source nodes so a nearest-cell snap cannot conceal a
        # dry or shallow proposed centre. Off-node layouts need another audit.
        if abs(x[i]-station) > 1e-6 or abs(y[j]-lateral) > 1e-6:
            raise ValueError('This source-node audit refuses snapped centres')
        depth = float(surface[i]-bed[j, i])
        if not wet[j, i] or depth < .35:
            raise ValueError(f'Dry/shallow feature centre: {station}, {lateral}, {depth}')
        c, s = np.cos(np.deg2rad(angle)), np.sin(np.deg2rad(angle))
        bounds = (station + min(-3*length*c, 7*length*c)-12*abs(s),
                  station + max(-3*length*c, 7*length*c)+12*abs(s))
        if any(bounds[1] >= lo and bounds[0] <= hi for lo, hi in quiet):
            raise ValueError('Authored relief/froth footprint overlaps quiet interval')
        along = (xx-station)*c + (yy-lateral)*s
        across = -(xx-station)*s + (yy-lateral)*c
        support = (along >= -3*length) & (along <= 7*length) & (abs(across) <= 12)
        rows.append(dict(feature=list(map(float, values)), centre_classified_water=True,
                         constructed_reference_depth_m=depth,
                         footprint_station_bounds_m=list(map(float, bounds)),
                         support_cells=int(support.sum()),
                         dry_support_cells=int((support & ~wet.astype(bool)).sum())))
    return dict(schema='raftsim.rapid_feature_source_audit.v1', rapid=candidate['rapid'],
                source_directory=candidate['source_directory'], source_sha256=expected,
                sites=rows, all_centres_passed=True, quiet_intervals_clear=True,
                qualification='Source-node and compact-support checks only. Dry footprint cells require runtime wet/depth clipping. Dimensions are authored, not surveyed; no native, hydraulic, visual or difficulty acceptance.',
                engine_accepted=False, catalog_class_match_accepted=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = audit(json.loads(args.candidate.read_text(encoding='utf-8-sig')))
    result['candidate_sha256'] = digest(args.candidate)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(f"{result['rapid']}: {len(result['sites'])} source centres passed; NOT engine acceptance")


if __name__ == '__main__':
    main()
