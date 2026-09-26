"""Inspect original returns beyond the interpreted constriction search edge.

The plot is source evidence, not an engine image or measured rock outline.
No vertex, classification, or hydraulic state is modified.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from audit_troublemaker_sparse_rock_returns import inside_polygon
from south_fork_registered_mesh import RegisteredMeshSampler

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09'
ORIGIN = np.array([683805.1336302214, 4296673.447587562, 220.])


def lower_returns(points, cells, original_ids):
    """Original lowest return per cell, with stable source-ID tie breaking."""
    order = np.lexsort((original_ids, points[:, 2], cells))
    ordered = cells[order]
    unique, first, counts = np.unique(ordered, return_index=True, return_counts=True)
    return original_ids[order[first]], counts


def run(output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    if output.exists():
        raise ValueError('Fresh output directory required')
    paths = dict(ground=BASE/'full_reach/source_matched_20260917/registered_mesh_source.npz',
                 returns=BASE/'troublemaker/classified_lidar_returns.npz',
                 image=BASE/'sources/troublemaker_naip.png',
                 export=BASE/'sources/troublemaker_naip_export.json',
                 regions=BASE/'troublemaker/rock_review_regions.json')
    hashes = {k: hashlib.sha256(p.read_bytes()).hexdigest() for k, p in paths.items()}
    if hashes['ground'] != '8edf8a7fbfb675a22ac6736db600a3300f018f1c9037b1c0674bc1c376cfcca7' or hashes['returns'] != '7f0a5d903a3914c830916390820cbf99260d7cb2f2cf667c57f2a1faa1c47cfe':
        raise ValueError('Source geometry identity changed')
    with np.load(paths['ground'], allow_pickle=False) as archive:
        ground = {key: archive[key] for key in archive.files}
    with np.load(paths['returns'], allow_pickle=False) as archive:
        returns = {key: archive[key] for key in archive.files}
    xyz = np.column_stack([returns[k] for k in ('utm_easting_m', 'utm_northing_m', 'navd88_m')])-ORIGIN
    regions = json.loads(paths['regions'].read_text())
    polygon = next(r['polygon'] for r in regions['regions'] if r['id'] == 'constriction_north_bedrock')
    # A diagnostic rectangular viewport only: not an accepted selection mask.
    bounds = [-5., 48., -15., 18.]
    scope = (xyz[:, 0] >= bounds[0]) & (xyz[:, 0] < bounds[1]) & (xyz[:, 1] >= bounds[2]) & (xyz[:, 1] < bounds[3])
    scope &= np.isin(returns['classification'], [1, 2, 20])
    ids = np.flatnonzero(scope)
    # Preserve low/near-water returns in the picture; do not silently remove
    # the very evidence needed to distinguish a rock foot from whitewater.
    cell_xy = np.floor((xyz[ids, :2]-[bounds[0], bounds[2]])/.5).astype(int)
    cell_ids = cell_xy[:, 1]*int((bounds[1]-bounds[0])/.5)+cell_xy[:, 0]
    selected, counts = lower_returns(xyz[ids], cell_ids, ids)
    selected, counts = selected[counts >= 2], counts[counts >= 2]
    points = xyz[selected]
    prior_height = RegisteredMeshSampler(ground).sample(points[:, 0], points[:, 1])
    outside = ~inside_polygon(points[:, 0], points[:, 1], polygon)
    above = returns['height_above_flattened_surface_m'][selected]
    eligible = outside & (above > .3) & (above < 8) & returns['within_survey_water'][selected]
    extent = json.loads(paths['export'].read_text())['extent']
    if extent['spatialReference']['wkid'] != 32610:
        raise ValueError('Unexpected image coordinate frame')
    image_extent = [extent['xmin']-ORIGIN[0], extent['xmax']-ORIGIN[0], extent['ymin']-ORIGIN[1], extent['ymax']-ORIGIN[1]]
    fig, axes = plt.subplots(2, 2, figsize=(15, 10), layout='constrained')
    axes[0, 0].imshow(plt.imread(paths['image']), extent=image_extent, interpolation='nearest')
    axes[0, 0].set_title('Original 2022 aerial / old interpreted search edge')
    artist = axes[0, 1].scatter(points[:, 0], points[:, 1], c=points[:, 2], s=9, vmin=4, vmax=12, cmap='viridis')
    fig.colorbar(artist, ax=axes[0, 1], label='Original lower-return height above datum (m)')
    axes[0, 1].set_title('2019 original returns: >=2 samples per 0.5m bin')
    artist = axes[1, 0].scatter(points[:, 0], points[:, 1], c=points[:, 2]-prior_height, s=9, vmin=-4, vmax=4, cmap='coolwarm')
    fig.colorbar(artist, ax=axes[1, 0], label='Return minus installed ground height (m)')
    axes[1, 0].set_title('Difference is NOT a classification or acceptance decision')
    mx, my = ground['east_m'], ground['north_m']
    area = (mx >= bounds[0]) & (mx < bounds[1]) & (my >= bounds[2]) & (my < bounds[3])
    artist = axes[1, 1].scatter(mx[area], my[area], c=ground['authority'][area], s=9, vmin=1, vmax=5, cmap='tab10')
    fig.colorbar(artist, ax=axes[1, 1], ticks=[1, 2, 3, 4, 5], label='1 DEM; 2 bed prior; 3 captured rock; 4 seam; 5 inferred flank')
    axes[1, 1].set_title('Installed vertex authority')
    closed = np.array(polygon+[polygon[0]])
    for ax in axes.ravel():
        ax.plot(closed[:, 0], closed[:, 1], 'm-', linewidth=1)
        ax.set(xlim=bounds[:2], ylim=bounds[2:], aspect='equal', xlabel='East of source origin (m)', ylabel='North (m)')
    fig.suptitle('Search-edge investigation; image/return dates differ; registration uncertainty 3m')
    output.mkdir(parents=True)
    fig.savefig(output/'source-support.png', dpi=150)
    plt.close(fig)
    report = dict(schema='raftsim.constriction_source_support.v1',
                  sources={k: dict(path=str(p.relative_to(ROOT)), sha256=hashes[k]) for k, p in paths.items()},
                  scope_bounds_m=bounds, scope_is_selection=False,
                  registration_uncertainty_m=3., original_lower_returns=len(selected),
                  outside_prior_selection_above_water_candidates=int(eligible.sum()),
                  candidates=[dict(original_return_index=int(i), xyz_m=xyz[i].tolist(),
                                   classification=int(returns['classification'][i]), count=int(c),
                                   installed_height_m=float(h), height_above_surface_m=float(a))
                              for i, c, h, a in zip(selected[eligible], counts[eligible], prior_height[eligible], above[eligible])],
                  geometry_modified=False, candidate_returns_accepted=False,
                  limits='Original class 1 remains unclassified; lower returns can be water or vegetation. Search boundaries and surface interpolation are inferred.')
    (output/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'candidates'}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    run(parser.parse_args().output)
