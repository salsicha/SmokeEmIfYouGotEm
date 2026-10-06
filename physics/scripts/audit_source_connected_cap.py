"""Audit a source-cap extension and plot its registered aerial footprint.

This is a geometric/provenance review, not rock classification, collision,
hydraulic or visual acceptance. Boundary area is an endpoint estimate only.
"""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import numpy as np
from shapely import union_all
from shapely.geometry import Polygon

from build_troublemaker_dem_rock_cap import ROOT
from south_fork_registered_mesh import RegisteredMeshSampler
from south_fork_rock_union import SourceRockUnion, sha


def describe(xyz, faces, sampler):
    edges = np.sort(np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]]), axis=1)
    edges, count = np.unique(edges, axis=0, return_counts=True)
    if np.any(count > 2):
        raise ValueError('Nonmanifold roof edge')
    boundary = edges[count == 1]
    gap = xyz[:, 2] - sampler.sample(xyz[:, 0], xyz[:, 1])
    length = np.linalg.norm(xyz[boundary[:, 1], :2] - xyz[boundary[:, 0], :2], axis=1)
    footprint = union_all([Polygon(p) for p in xyz[faces, :2]])
    parts = [footprint] if footprint.geom_type == 'Polygon' else list(footprint.geoms)
    report = dict(vertices=len(xyz), triangles=len(faces), components=len(parts),
        holes=sum(len(p.interiors) for p in parts), projected_area_m2=footprint.area,
        perimeter_m=float(length.sum()),
        boundary_gap_min_max_m=[float(gap[boundary].min()), float(gap[boundary].max())],
        boundary_length_both_endpoints_within_clearance_prior_m=float(length[gap[boundary].max(axis=1) <= .3].sum()),
        positive_boundary_gap_endpoint_area_estimate_m2=float((length * np.maximum(gap[boundary].mean(axis=1), 0)).sum()),
        boundary_estimate_is_not_exact_parent_intersection=True)
    return report, boundary, gap, footprint


def audit(previous_path, candidate_path, output):
    previous_path, candidate_path, output = map(lambda p: Path(p).resolve(), (previous_path, candidate_path, output))
    if output.exists() or not output.is_relative_to(ROOT / 'tmp'):
        raise ValueError('Fresh project tmp report directory required')
    manifests = [json.loads(p.read_text()) for p in (previous_path, candidate_path)]
    old, new = manifests
    for key in ('source_mesh_sha256', 'original_returns_sha256', 'source_naip_sha256', 'source_naip_export_sha256', 'origin_utm_and_vertical_datum_m'):
        if old[key] != new[key]:
            raise ValueError('Candidates use different original sources or frames: ' + key)
    if new['previous_cap_manifest_sha256'] != sha(previous_path):
        raise ValueError('Candidate does not name this previous cap')
    origin = np.asarray(new['origin_utm_and_vertical_datum_m'])
    parent_path = ROOT / new['source_mesh_path']
    unions = [SourceRockUnion(path, ROOT, parent_path, origin[:2], origin[2]) for path in (previous_path, candidate_path)]
    roof_exact = np.array_equal(unions[0].xyz[unions[0].faces], unions[1].xyz[unions[1].faces[:len(unions[0].faces)]])
    if not roof_exact:
        raise ValueError('Previous roof triangles changed')
    with np.load(parent_path, allow_pickle=False) as parent:
        sampler = RegisteredMeshSampler(parent)
    results = [describe(u.xyz, u.faces, sampler) for u in unions]
    selection = new.get('reviewed_extension_selection')
    selected_region = None
    if selection is not None:
        # SourceRockUnion already verified this file's digest and source frame.
        selection_record = json.loads((ROOT/selection['path']).read_text())
        selected_region = Polygon(selection_record['interpreted_selection_polygon_m'])
        allowed = selected_region.union(results[0][3])
        if not all(allowed.covers(Polygon(p)) for p in unions[1].xyz[unions[1].faces[len(unions[0].faces):], :2]):
            raise ValueError('Extension triangle crosses an image-review exclusion')
    lost = results[0][3].difference(results[1][3]).area
    if lost > 1e-10:
        raise ValueError('Previous projected roof coverage lost')
    source_dir = parent_path.parents[2] / 'sources'
    image_path = source_dir / 'troublemaker_naip.png'
    meta_path = source_dir / 'troublemaker_naip_export.json'
    if sha(image_path) != new['source_naip_sha256'] or sha(meta_path) != new['source_naip_export_sha256']:
        raise ValueError('Registered aerial source changed')
    meta = json.loads(meta_path.read_text())
    if meta['extent']['spatialReference']['latestWkid'] != 32610:
        raise ValueError('Aerial image is not registered in UTM 10N')
    extent = meta['extent']
    bounds = [extent['xmin']-origin[0], extent['xmax']-origin[0], extent['ymin']-origin[1], extent['ymax']-origin[1]]
    raster = plt.imread(image_path)
    if raster.shape[:2] != (meta['height'], meta['width']):
        raise ValueError('Aerial image dimensions differ from registration')
    lower = unions[1].xyz[:, :2].min(0)-5
    upper = unions[1].xyz[:, :2].max(0)+5
    fig, axes = plt.subplots(1, 3, figsize=(15, 6), layout='constrained')
    titles = ['Original NAIP (nearest pixels)', 'Original cap boundary: yellow', 'Extended boundary: height above parent']
    for ax, title in zip(axes, titles):
        ax.imshow(raster, extent=bounds, origin='upper', interpolation='nearest')
        ax.set(xlim=(lower[0], upper[0]), ylim=(lower[1], upper[1]), xlabel='East of source origin (m)', ylabel='North of source origin (m)', title=title)
        ax.set_aspect('equal')
    axes[1].add_collection(LineCollection(unions[0].xyz[results[0][1], :2], colors='yellow', linewidths=1.2))
    lines = LineCollection(unions[1].xyz[results[1][1], :2], cmap='coolwarm', linewidths=1.2)
    lines.set_array(results[1][2][results[1][1]].mean(axis=1))
    lines.set_clim(0, 4)
    axes[2].add_collection(lines)
    if selected_region is not None:
        xy = np.asarray(selected_region.exterior.coords)
        axes[2].plot(xy[:,0], xy[:,1], '--', color='yellow', linewidth=.8, label='Interpreted selection, not measured')
        axes[2].legend(loc='upper right', fontsize=6)
    fig.colorbar(lines, ax=axes[2], label='Endpoint-mean gap (m)', shrink=.65)
    resolution = (extent['xmax']-extent['xmin'])/meta['width']
    fig.suptitle(f'Original returns, NOT certified rock; NAIP {resolution:.3f} m/pixel; registration uncertainty {new["registration_uncertainty_m"]:g} m\nConnectivity/clearance are reconstruction priors; no measured outline, bathymetry or acceptance')
    output.mkdir()
    figure = output/'registered-boundaries.png'
    fig.savefig(figure, dpi=150)
    plt.close(fig)
    report = dict(schema='raftsim.source_connected_cap_audit.v1',
        previous_manifest_sha256=sha(previous_path), candidate_manifest_sha256=sha(candidate_path),
        previous=results[0][0], candidate=results[1][0],
        previous_roof_triangles_bit_exact=roof_exact, previous_roof_area_lost_m2=lost,
        original_xyz_classes_and_closed_solid_verified=True,
        registered_aerial_sha256=sha(image_path), figure_sha256=sha(figure),
        unsupported_connectivity_edges=len(new['source_connected_selection']['unsupported_directed_edges']),
        reviewed_selection_sha256=selection['sha256'] if selection else None,
        extension_respects_reviewed_selection=True if selection else None,
        measured_outline=False, measured_flanks=False, engine_collision_verified=False,
        hydraulic_recooked=False, playable_integrated=False, visual_acceptance=False, production_promoted=False)
    (output/'audit.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--previous', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.previous, args.candidate, args.output), indent=2), flush=True)
