"""Read-only impact audit; never overwrite the retained classified archive."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/troublemaker/classified_lidar_returns.npz'
SOURCE_SHA = '7f0a5d903a3914c830916390820cbf99260d7cb2f2cf667c57f2a1faa1c47cfe'


def audit():
    digest = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    if digest != SOURCE_SHA:
        raise ValueError('Retained original archive identity changed')
    with np.load(SOURCE, allow_pickle=False) as data:
        classes = data['classification']
        inside = data['within_survey_water'].astype(bool)
        height = data['height_above_flattened_surface_m']
        screen = inside & (height > .3) & (height < 12)
        old = screen & np.isin(classes, [2, 10])
        corrected = screen & np.isin(classes, [2, 20])
        values, counts = np.unique(classes, return_counts=True)
        added = np.flatnonzero(corrected & ~old)
        rows = [dict(original_return_index=int(i), classification=int(classes[i]),
            utm_easting_m=float(data['utm_easting_m'][i]),
            utm_northing_m=float(data['utm_northing_m'][i]),
            navd88_m=float(data['navd88_m'][i]),
            height_above_flattened_surface_m=float(height[i])) for i in added]
        result = dict(schema='raftsim.eldorado_ignored_ground_audit.v1',
            source_path=SOURCE.relative_to(ROOT).as_posix(), source_sha256=digest,
            metadata_url='https://www.fisheries.noaa.gov/inport/item/66639',
            class_counts={str(int(v)): int(n) for v, n in zip(values, counts)},
            ignored_ground_in_water_count=int((inside & (classes == 20)).sum()),
            previous_exposed_candidate_count=int(old.sum()),
            corrected_exposed_candidate_count=int(corrected.sum()),
            removed_candidate_count=int((old & ~corrected).sum()),
            added_candidate_count=len(rows), added_candidates=rows,
            source_archive_modified=False, geometry_modified=False,
            playable_integrated=False, semantic_rock_classification_verified=False)
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != digest:
        raise ValueError('Source changed during audit')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or not output.is_relative_to(ROOT):
        raise ValueError('Fresh in-repository report required')
    result = audit()
    with output.open('x', encoding='utf-8') as handle:
        handle.write(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'added_candidates'}, indent=2))


if __name__ == '__main__':
    main()
