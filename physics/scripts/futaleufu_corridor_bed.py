"""Source-bound initial bed for the three-arm Futaleufu corridor.

Edited GLO-30 DSM is not bathymetry. Depth, shoreline taper and excavation
limit are explicit construction assumptions, NOT measured flow or a solve.
Mainstem ownership follows captured polygons; Azul spans remain inferred.
"""
import json
from pathlib import Path

import numpy as np
import shapely

from build_futaleufu_corridor_sources import ROOT, sha
from futaleufu_planform import load_planform

NAMES = ('rio_azul', 'upstream_mainstem', 'downstream_mainstem')


def inferred_bank_ribbon(line, station, lower, upper, *, return_receipt=False):
    """Explicit inferred strip, not a correction to captured source geometry.

    Consecutive cross-sections sweep quadrilaterals. At sharp captured-route
    turns their sides may cross: use a local convex bevel bounded by those four
    inferred endpoints, explicitly recorded. This does NOT repair or widen any
    captured polygon. Internal section edges cannot become hydraulic banks.
    """
    station, lower, upper = [np.asarray(a, float) for a in (station, lower, upper)]
    if (station.ndim != 1 or len(station) < 2 or lower.shape != station.shape
            or upper.shape != station.shape or not np.isfinite([station, lower, upper]).all()
            or np.any(np.diff(station) <= 0) or station[0] != 0
            or abs(station[-1]-line.length) > 1e-6 or np.any(lower >= upper)):
        raise ValueError('Complete ordered inferred bank spans required')
    before = shapely.get_coordinates(shapely.line_interpolate_point(line, np.maximum(station-1, 0)))
    after = shapely.get_coordinates(shapely.line_interpolate_point(line, np.minimum(station+1, line.length)))
    tangent = after-before
    normal = np.c_[-tangent[:, 1], tangent[:, 0]]/np.linalg.norm(tangent, axis=1)[:, None]
    centre = shapely.get_coordinates(shapely.line_interpolate_point(line, station))
    low, high = centre+normal*lower[:, None], centre+normal*upper[:, None]
    strips = [shapely.Polygon([low[i], high[i], high[i+1], low[i+1]]) for i in range(len(station)-1)]
    joins = []
    for i, strip in enumerate(strips):
        if not strip.is_valid or strip.area <= 0:
            join = shapely.MultiPoint([low[i], high[i], high[i+1], low[i+1]]).convex_hull
            if join.geom_type != 'Polygon' or join.area <= 0:
                raise ValueError(f'Degenerate inferred bank interval: {i}')
            strips[i] = join
            joins.append(dict(interval_index=i, station_m=[float(station[i]), float(station[i+1])],
                              area_m2=float(join.area)))
    polygon = shapely.union_all(strips)
    receipt = dict(policy='Adjacent inferred cross-section sweep with explicitly bounded convex bevels',
                   corner_joins=joins, inferred_area_m2=float(polygon.area), captured_banks_modified=False)
    return (polygon, receipt) if return_receipt else polygon


def source_heights(xy, grid, transform):
    """Bilinear pixel-centre sampling, without boundary clamping/extrapolation."""
    xy = np.asarray(xy, float)
    if xy.ndim != 2 or xy.shape[1] != 2 or not np.isfinite(xy).all():
        raise ValueError('Finite N by 2 coordinates required')
    t = transform
    if t[0] != 10 or t[4] != -10 or t[1] != 0 or t[3] != 0:
        raise ValueError('Verified native ten-metre source frame required')
    c = (xy[:, 0]-t[2])/10-.5
    r = (t[5]-xy[:, 1])/10-.5
    if np.any((c < 0) | (r < 0) | (c > grid.shape[1]-1) | (r > grid.shape[0]-1)):
        raise ValueError('Bed query leaves source support')
    ci = np.minimum(np.floor(c).astype(int), grid.shape[1]-2)
    ri = np.minimum(np.floor(r).astype(int), grid.shape[0]-2)
    u, v = c-ci, r-ri
    return ((1-u)*(1-v)*grid[ri, ci]+u*(1-v)*grid[ri, ci+1]
            +(1-u)*v*grid[ri+1, ci]+u*v*grid[ri+1, ci+1])


def initial_cut(source, stage, owned, bank_distance, width, *, depth_m,
                bank_taper_m, max_cut_m):
    if (not np.isfinite([depth_m, bank_taper_m, max_cut_m]).all()
            or not 0 < depth_m <= 10 or not 0 < bank_taper_m <= 20
            or not 0 < max_cut_m <= 25):
        raise ValueError('Explicit bounded construction assumptions required')
    source, stage, owned, distance, width = np.broadcast_arrays(
        np.asarray(source, float), stage, owned, bank_distance, width)
    if (owned.dtype.kind != 'b' or any(not np.isfinite(a).all() for a in
            (source, stage, distance, width)) or np.any(distance < 0) or np.any(width <= 0)):
        raise ValueError('Finite aligned source, stage and bank geometry required')
    shape = np.sqrt(np.clip(2*distance/width, 0, 1))
    target = stage-depth_m*shape
    taper = np.clip(distance/bank_taper_m, 0, 1)
    taper = taper*taper*(3-2*taper)
    requested = np.where(owned, np.maximum(source-target, 0)*taper, 0)
    cut = np.minimum(requested, max_cut_m)
    height = source-cut
    return dict(height_m=height, source_height_m=source.copy(), inferred_bed=height < source,
                cut_limit_reached=owned & (requested > max_cut_m),
                unresolved_above_stage=owned & (height >= stage), reference_m=stage.copy())


class FutaleufuBed:
    def __init__(self, source_folder, profile_folder, network_path, *, depth_m,
                 bank_taper_m=5., max_cut_m=25.):
        source_folder, profile_folder = Path(source_folder), Path(profile_folder)
        network_path = Path(network_path)
        source_path, profile_path = source_folder/'manifest.json', profile_folder/'manifest.json'
        source, profile, network = [json.loads(p.read_text(encoding='utf-8')) for p in
                                    (source_path, profile_path, network_path)]
        if (source.get('schema') != 'raftsim.futaleufu_continuous_sources.v1'
                or profile.get('schema') != 'raftsim.futaleufu_channel_profile.v1'
                or network.get('schema') != 'raftsim.futaleufu_confluence_network.v1'
                or source['grid']['epsg'] != 32718):
            raise ValueError('Verified Futaleufu sources, profile and network required')
        pins = {p.resolve(): sha(p) for p in (source_path, profile_path, network_path,
            Path(__file__), Path(__file__).with_name('futaleufu_planform.py'))}
        for manifest in (source, profile, network):
            for relative, digest in manifest['sources_sha256'].items():
                path = (ROOT/relative).resolve(); path.relative_to(ROOT)
                if sha(path) != digest:
                    raise ValueError('Changed construction source: '+relative)
                pins[path] = digest
        for p in (source_path, network_path):
            if profile['sources_sha256'].get(p.resolve().relative_to(ROOT).as_posix()) != sha(p):
                raise ValueError('Profile does not bind this terrain and branch network')
        dsm_path, data_path = source_folder/source['dsm']['file'], profile_folder/'profile.npz'
        if sha(dsm_path) != source['dsm']['sha256'] or sha(data_path) != profile['profile_sha256']:
            raise ValueError('Changed terrain/profile arrays')
        pins[dsm_path.resolve()], pins[data_path.resolve()] = sha(dsm_path), sha(data_path)
        with np.load(dsm_path, allow_pickle=False) as z:
            self.grid = z['dsm_m'].copy()
        if self.grid.shape != tuple(source['grid']['shape']) or not np.isfinite(self.grid).all():
            raise ValueError('Incomplete terrain source')
        self.transform = source['grid']['transform']
        with np.load(data_path, allow_pickle=False) as z:
            self.arrays = {name: {k: z[name+'_'+k].copy() for k in
                ('station_m', 'stage_m', 'left_m', 'right_m')} for name in NAMES}
        self.lines = [shapely.LineString(np.asarray(network['branches'][name]
                     ['points_station_easting_northing_m'])[:, 1:]) for name in NAMES]
        self.junction = np.asarray(network['junction']['easting_northing_m'])
        for j, (name, line) in enumerate(zip(NAMES, self.lines)):
            a = self.arrays[name]; s = a['station_m']
            if (not all(np.isfinite(v).all() and v.shape == s.shape for v in a.values())
                    or len(s) < 3 or s[0] != 0 or abs(s[-1]-line.length) > 1e-6
                    or np.any(np.diff(s) <= 0) or np.any(np.diff(a['stage_m']) > 1e-8)
                    or np.any(a['right_m'] <= a['left_m'])
                    or not np.array_equal(np.asarray(line.coords)[-1 if j < 2 else 0], self.junction)
                    or a['stage_m'][-1 if j < 2 else 0] != profile['junction_stage_m']):
                raise ValueError('Inconsistent full branch profile or junction')
        planform_path = ROOT/profile['mapped_planform_source']
        if pins.get(planform_path.resolve()) != sha(planform_path):
            raise ValueError('Unbound mapped banks')
        self.polygon = shapely.union_all([g for _, _, g in load_planform(planform_path)])
        holes = [shapely.Polygon(ring) for p in shapely.get_parts(self.polygon) for ring in p.interiors]
        self.islands = shapely.union_all(holes)
        shapely.prepare(self.polygon); shapely.prepare(self.islands)
        self.initialize_bed_footprint()
        self.parameters = dict(depth_m=depth_m, bank_taper_m=bank_taper_m, max_cut_m=max_cut_m)
        initial_cut([0.], [0.], [False], [0.], [1.], **self.parameters)
        self.receipt = dict(schema='raftsim.futaleufu_initial_bed.v1',
            sources_sha256={p.relative_to(ROOT).as_posix(): h for p, h in pins.items()},
            construction_assumptions=self.parameters, branch_competition_distance_m=20.,
            scope='Initial inferred bathymetry; no flow assigned, hydraulic solution or engine acceptance',
            mainstem_ownership='Captured water polygons with islands excluded; no interpolated bank ribbon',
            azul_ownership='Explicit inferred spectral bank ribbon; captured mainstem islands excluded',
            inferred_bank_construction=self.ribbon_receipt,
            bank_distance_policy='Boundary of the connected mapped-plus-inferred water union; no bank across tributary mouth',
            source_attribution=profile['attribution'], source_detail_m=30,
            measured_bed=False, discharge_assigned=False, installed_in_engine=False)

    def initialize_bed_footprint(self):
        a = self.arrays['rio_azul']
        self.inferred_polygon, self.ribbon_receipt = inferred_bank_ribbon(
            self.lines[0], a['station_m'], a['left_m'], a['right_m'], return_receipt=True)
        self.bed_polygon = shapely.difference(shapely.union_all([self.polygon, self.inferred_polygon]), self.islands)
        if not self.bed_polygon.is_valid:
            raise ValueError('Invalid connected construction footprint')
        shapely.prepare(self.inferred_polygon); shapely.prepare(self.bed_polygon)

    def sample(self, xy):
        xy = np.asarray(xy, float)
        source = source_heights(xy, self.grid, self.transform)
        pts = shapely.points(xy)
        distances = np.array([shapely.distance(pts, line) for line in self.lines])
        stations = np.array([shapely.line_locate_point(line, pts) for line in self.lines])
        owner = distances.argmin(axis=0); index = np.arange(len(xy))
        values = {k: np.array([np.interp(stations[j], self.arrays[name]['station_m'],
                    self.arrays[name][k]) for j, name in enumerate(NAMES)])
                  for k in ('stage_m', 'left_m', 'right_m')}
        # Compact partition of unity is continuous across branch Voronoi
        # boundaries, unlike a blend of a discontinuous nearest-branch value.
        # An arm more than 20 m farther away than the closest arm contributes
        # nothing. All projections share the exact junction stage. This is
        # construction geometry, not a hydraulic mixing solution.
        weights = np.clip(1-(distances-distances.min(axis=0))/20., 0, 1)**2
        stage = np.sum(weights*values['stage_m'], axis=0)/weights.sum(axis=0)
        mapped = shapely.contains(self.polygon, pts)
        inferred_azul = shapely.contains(self.inferred_polygon, pts) & ~mapped
        inside = np.array([(stations[j] > 0) & (stations[j] < line.length)
                           for j, line in enumerate(self.lines)])
        # A junction is an internal point even when one projected arm ends.
        domain = inside[owner, index] | (np.linalg.norm(xy-self.junction, axis=1) < 1e-6)
        owned = shapely.contains(self.bed_polygon, pts) & domain & (distances.min(axis=0) < 256)
        owned &= ~shapely.intersects(self.islands, pts)
        bank_distance = shapely.distance(pts, self.bed_polygon.boundary)
        width = np.sum(weights*(values['right_m']-values['left_m']), axis=0)/weights.sum(axis=0)
        result = initial_cut(source, stage, owned, bank_distance, width, **self.parameters)
        result.update(mapped_water=mapped & owned, inferred_planform=inferred_azul & owned,
                      bed_owned=owned, branch_index=owner, bank_distance_m=bank_distance)
        return result
