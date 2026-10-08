"""Construct initial Cartesian water tiles on the actual encoded Landscape.

This is a connectivity prerequisite, not a flow solution or navigation test.
No source bank, bed, stage, island or flow budget is adjusted to make it pass.
Rows increase northward (native solver frame), unlike north-first PNG rows.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

import numpy as np
import shapely
from scipy.ndimage import label

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'physics/scripts'))
from export_colorado_continuous_terrain import LandscapeTriangles
from futaleufu_corridor_bed import FutaleufuBed, NAMES

PREFIX = ROOT/'physics/data/real_world/futaleufu_river_chile/production_corridor/rio_azul_swinging_bridge_to_pasarela'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def cell_centres(index, origin, span=252., spacing=2.):
    if span <= 0 or spacing <= 0 or span/spacing != int(span/spacing):
        raise ValueError('Positive integral cell lattice required')
    corner = np.asarray(origin, float)+np.asarray(index)*span
    offsets = (np.arange(int(span/spacing))+.5)*spacing
    x, y = np.meshgrid(corner[0]+offsets, corner[1]+offsets)
    return np.stack((x, y), axis=-1)


def initial_fields(height, stage, owned):
    height, stage, owned = np.asarray(height), np.asarray(stage), np.asarray(owned)
    if (height.shape != stage.shape or height.shape != owned.shape or owned.dtype.kind != 'b'
            or not np.isfinite(height).all() or not np.isfinite(stage).all()):
        raise ValueError('Finite aligned encoded terrain, stage and ownership required')
    depth = np.where(owned, np.maximum(stage-height, 0.), 0.)
    return depth, owned & (depth > .05)


def connected_tiles(tiles):
    """Global four-face connectivity; absent tiles and diagonal contacts stay dry."""
    if not tiles:
        raise ValueError('Nonempty tiles required')
    first = np.asarray(next(iter(tiles.values())))
    if first.ndim != 2 or first.shape[0] != first.shape[1] or not first.size:
        raise ValueError('Square nonempty tiles required')
    size = first.shape[0]
    keys = np.asarray(list(tiles))
    if keys.shape != (len(tiles), 2) or keys.dtype.kind not in 'iu':
        raise ValueError('Integer tile indices required')
    lower, upper = keys.min(axis=0), keys.max(axis=0)+1
    shape = (upper-lower)[::-1]*size
    if np.prod(shape) > 64_000_000:
        raise ValueError('Connectivity allocation exceeds bounded corridor')
    wet = np.zeros(tuple(shape), bool)
    for (i, j), mask in tiles.items():
        if mask.shape != first.shape or mask.dtype.kind != 'b':
            raise ValueError('Aligned Boolean tiles required')
        x, y = (np.array([i, j])-lower)*size
        wet[y:y+size, x:x+size] = mask
    components, count = label(wet, structure=np.array([[0,1,0],[1,1,1],[0,1,0]]))
    return components, lower*size, np.bincount(components.ravel(), minlength=count+1)


def labels_at(points, components, cell_offset, origin, spacing):
    points = np.asarray(points, float)
    if points.ndim != 2 or points.shape[1] != 2 or not np.isfinite(points).all():
        raise ValueError('Finite east/north points required')
    # Bound before integer conversion; outside observations are not clamped.
    q = (points-np.asarray(origin))/spacing-cell_offset
    inside = (q >= 0).all(axis=1) & (q < np.array(components.shape[::-1])).all(axis=1)
    result = np.zeros(len(points), np.int32)
    ij = np.floor(q[inside]).astype(np.int64)
    result[inside] = components[ij[:,1], ij[:,0]]
    return result


def observe_branches(bed, components, offset, origin, spacing):
    observations = []
    for name, line in zip(NAMES, bed.lines):
        # Interior endpoints avoid extrapolating the open source boundaries.
        stations = np.unique(np.r_[10., np.arange(20., line.length-10., 20.), line.length-10.])
        a = bed.arrays[name]
        for station in stations:
            centre = np.asarray(line.interpolate(station).coords)[0]
            tangent = np.asarray(line.interpolate(station+1).coords)[0]-np.asarray(line.interpolate(station-1).coords)[0]
            normal = np.array([-tangent[1], tangent[0]])/np.linalg.norm(tangent)
            low, high = [np.interp(station, a['station_m'], a[k]) for k in ('left_m','right_m')]
            points = centre+np.linspace(low, high, max(2, int(np.ceil((high-low)/spacing))+1))[:,None]*normal
            ids = labels_at(points, components, offset, origin, spacing)
            observations.append(dict(branch=name, station_m=float(station), centre_m=centre.tolist(),
                wet_components=np.unique(ids[ids>0]).tolist(), wet_samples=int(np.count_nonzero(ids)),
                sample_count=len(ids), inferred_profile_bank_span_m=[float(low), float(high)]))
    common = set(observations[0]['wet_components'])
    for row in observations[1:]:
        common.intersection_update(row['wet_components'])
    return observations, sorted(common)


def build(terrain_folder, footprint_folder, source_folder, output, *, spacing=2.):
    terrain_folder, footprint_folder, source_folder, output = map(Path,
        (terrain_folder, footprint_folder, source_folder, output))
    if output.exists():
        raise ValueError('Fresh domain output required')
    if isinstance(spacing, bool) or spacing not in (1., 2.):
        raise ValueError('Qualified one- or two-metre water sampling required')
    if shutil.disk_usage(ROOT).free < 42*1024**3:
        raise ValueError('Preserve 40 GiB disk reserve plus construction allowance')
    terrain = LandscapeTriangles(terrain_folder)
    manifest = terrain.manifest
    footprint_path = footprint_folder/'manifest.json'
    footprint = json.loads(footprint_path.read_text())
    if any(manifest.get(k) != v or footprint.get(k) != v for k, v in dict(
            schema='raftsim.continuous_landscape.v1', river_id='futaleufu_river_chile',
            horizontal_origin_m=[739986.,5195961.5], vertical_datum_m=150., world_y_sign=-1,
            horizontal_crs='EPSG:32718', vertical_reference='EGM2008').items()):
        raise ValueError('Reviewed Futaleufu frame required')
    if terrain.spacing != 2. or terrain.span != 252.:
        raise ValueError('Native two-metre encoded terrain required')
    bed = FutaleufuBed(source_folder, PREFIX/'hydrology/channel_profile_2026_10_v2',
        PREFIX/'hydrography/confluence_network_2026_10_v1/network.json', depth_m=1.8)
    for evidence in (manifest['evidence_source'], footprint['evidence_source']):
        for k, v in bed.receipt.items():
            matches = (all(evidence.get(k, {}).get(p) == h for p,h in v.items())
                       if k == 'sources_sha256' else evidence.get(k) == v)
            if not matches:
                raise ValueError('Water and terrain construction lineage differ: '+k)
    pins = {ROOT/p:h for p,h in manifest['evidence_source']['sources_sha256'].items()}
    pins.update({footprint_path:sha(footprint_path), Path(__file__):sha(__file__),
                 ROOT/'physics/scripts/export_colorado_catalog_runtime.py':sha(ROOT/'physics/scripts/export_colorado_catalog_runtime.py')})
    def verify_sources():
        for path, digest in pins.items():
            path.resolve().relative_to(ROOT)
            if sha(path) != digest:
                raise ValueError('Changed bound input: '+str(path))
        terrain.verify_unchanged()
    verify_sources()
    context = {tuple(c['chunk']):c for c in manifest['chunks']}
    indices = [tuple(c['chunk']) for c in footprint['chunks']]
    if len(indices) != len(set(indices)):
        raise ValueError('Duplicate footprint tile')
    for c in footprint['chunks']:
        if tuple(c['chunk']) not in context or context[tuple(c['chunk'])]['sha256'] != c['sha256']:
            raise ValueError('Original river terrain missing or changed in context')
    output.mkdir(parents=True)
    wet_tiles, rows = {}, []
    for index in sorted(indices):
        xy = cell_centres(index, terrain.origin, spacing=spacing)
        actual = terrain.sample(xy)
        sampled = bed.sample(xy.reshape(-1,2))
        stage = sampled['reference_m'].reshape(actual.shape)
        owned = sampled['bed_owned'].reshape(actual.shape)
        depth, wet = initial_fields(actual, stage, owned)
        name = 'tile_%d_%d.npz' % index
        np.savez_compressed(output/name, bed_m=actual, reference_stage_m=stage,
            initial_depth_m=depth, owned=owned, wet=wet)
        wet_tiles[index] = wet
        rows.append(dict(chunk=list(index), file=name, sha256=sha(output/name),
            owned_cells=int(owned.sum()), wet_cells=int(wet.sum()),
            owned_dry_cells=int((owned & ~wet).sum()), max_depth_m=float(depth.max())))
        if len(rows)%16 == 0:
            print(f'Encoded water tiles {len(rows)}/{len(indices)}', flush=True)
    components, offset, counts = connected_tiles(wet_tiles)
    observations, common = observe_branches(bed, components, offset, terrain.origin, spacing)
    np.savez_compressed(output/'components.npz', components=components, cell_offset=offset)
    verify_sources()
    report = dict(schema='raftsim.futaleufu_initial_cartesian_water.v1',
        scope='Initial geometric connectivity only; no assigned discharge, velocities, solver convergence, boat passage or engine acceptance',
        terrain_manifest_sha256=terrain.manifest_sha256, footprint_manifest_sha256=sha(footprint_path),
        sources_sha256={str(p.resolve().relative_to(ROOT)):h for p,h in pins.items()},
        horizontal_origin_m=terrain.origin.tolist(), horizontal_crs='EPSG:32718', vertical_reference='EGM2008',
        spacing_m=spacing, terrain_spacing_m=terrain.spacing, tile_cells=[int(terrain.span/spacing)]*2,
        rows_increase='north', wet_threshold_m=.05,
        tile_count=len(rows), wet_cells=int(counts[1:].sum()), component_count=len(counts)-1,
        largest_components=[dict(id=int(i), cells=int(counts[i])) for i in (np.argsort(counts[1:])[::-1][:20]+1)],
        common_route_components=common, sampled_cross_sections_share_component=bool(common),
        dry_cross_sections=[r for r in observations if not r['wet_components']],
        observations=observations, tiles=rows, components_sha256=sha(output/'components.npz'),
        construction_assumptions=bed.parameters, terrain_modified=False, engine_installed=False)
    (output/'manifest.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k:report[k] for k in ('tile_count','wet_cells','component_count',
        'common_route_components','sampled_cross_sections_share_component')}), flush=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--terrain', type=Path, required=True)
    parser.add_argument('--footprint', type=Path, required=True)
    parser.add_argument('--sources', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--spacing-m', type=float, choices=(1.,2.), default=2.)
    args = parser.parse_args()
    build(args.terrain, args.footprint, args.sources, args.out, spacing=args.spacing_m)
