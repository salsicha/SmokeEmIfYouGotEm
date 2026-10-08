"""Single full-route inferred bed over immutable, source-classified terrain.

This is initial construction geometry, not solved hydraulics, bathymetry or
rapid calibration. Only low mapped-water terrain is carved. No imagery-derived
boulders or named rapids are invented where supporting observations are absent.
"""
import json
from pathlib import Path

import numpy as np
import shapely
from scipy.ndimage import gaussian_filter1d
from shapely.geometry import LineString

from chilko_planform import load_planform, route_planform_policy
from correct_chilko_route import compatible_capture_route
from build_chilko_corridor_profile import bridge_short_reference_gaps
from chilko_corridor_terrain import CorridorTerrain
from mosaic_lidarbc_crops import sha
from plan_lidarbc_corridor_capture import route_xy


def inferred_depth_parameters(station, surface, width, discharge, roughness):
    station, surface, width = [np.asarray(a, dtype=float) for a in (station, surface, width)]
    if (station.ndim != 1 or len(station) < 3 or
            any(a.shape != station.shape or not np.isfinite(a).all() for a in (surface, width)) or
            not np.isfinite(station).all() or np.any(np.diff(station) <= 0) or
            np.any(width <= 0) or np.any(np.diff(surface) > 1e-8) or
            not np.isfinite([discharge, roughness]).all() or not 0 < discharge <= 500 or
            not .02 <= roughness <= .1):
        raise ValueError('Finite ordered surface/width and bounded hydraulic assumptions required')
    step = float(np.median(np.diff(station)))
    if not np.allclose(np.diff(station)[:-1], step, rtol=0, atol=1e-7):
        raise ValueError('Uniform profile with only a terminal partial interval required')
    smooth = gaussian_filter1d(surface, 20. / step, mode='nearest')
    slope = np.maximum(-np.gradient(smooth, station), .001)
    # f=sqrt(distance-to-bank / half-width) on an ideal straight section:
    # integral(f**(5/3))=6*width/11; mean(f)=2/3. Real polygon geometry and
    # emergent ground differ, so this is an INITIAL inferred bed, not a Q proof.
    depth = (discharge * roughness / (np.sqrt(slope) * width * 6. / 11.)) ** .6
    critical = ((discharge / width) ** 2 / 9.81) ** (1. / 3.)
    return np.maximum(depth, critical * 1.5), slope


def source_water_reference(station, raw_reference):
    """Local DEM-water classifier, independent of regressed hydraulic stage.

    Only the existing bounded interior-gap policy may fill missing raw samples.
    Neither regression nor a solved water level may change which observed
    emergent features are owned by the initial bathymetry inference.
    """
    reference, gaps = bridge_short_reference_gaps(station, raw_reference)
    if not np.isfinite(reference).all():
        raise ValueError('Local source-water classification has unsupported gaps')
    return reference, gaps


def carve_mapped_water(terrain, source_kind, mapped, reference, bank_distance, width, depth,
                       ownership_reference=None):
    if ownership_reference is None:
        ownership_reference = reference
    arrays = np.broadcast_arrays(np.asarray(terrain, dtype=float), source_kind, mapped,
                                 reference, bank_distance, width, depth, ownership_reference)
    terrain, kind, mapped, reference, bank_distance, width, depth, ownership_reference = arrays
    if (not np.isfinite(terrain).all() or not np.isin(kind, [1, 2, 3]).all() or
            mapped.dtype.kind != 'b' or
            any(not np.isfinite(a[mapped]).all() for a in (reference, bank_distance, width, depth, ownership_reference)) or
            np.any(bank_distance[mapped] < 0) or np.any(width[mapped] <= 0) or np.any(depth[mapped] <= 0)):
        raise ValueError('Mapped bed inference requires finite source support and reference')
    # FWA is a mapped waterbody, NOT a flight-day shoreline. Preserve emergent
    # rocks, bars and bank terrain higher than the existing 0.25 m core allowance.
    # The source's local channel-water elevation is NOT the regressed stage.
    # Using stage here can turn a captured water surface into an artificial dam
    # (or carve an emergent bar where stage regression raises the water level).
    wet = mapped & (terrain <= ownership_reference + .25)
    bed = terrain.copy()
    section_shape = np.sqrt(np.clip(2. * bank_distance[wet] / width[wet], 0., 1.))
    proposed = reference[wet] - np.maximum(depth[wet] * section_shape, .05)
    # Never raise existing lower terrain or manufacture a submerged obstruction.
    bed[wet] = np.minimum(terrain[wet], proposed)
    inferred = wet & (bed < terrain)
    return bed, inferred


def load_available_depth(folder, station, previous_depth, expected):
    folder=Path(folder).resolve();dm=json.loads((folder/'manifest.json').read_text())
    if any(dm.get(k)!=v for k,v in expected.items()) or sha(folder/'depth.npz')!=dm['depth_sha256']:
        raise ValueError('Changed or unrelated available-channel depth inference')
    with np.load(folder/'depth.npz',allow_pickle=False) as z:
        amplitude=z['depth_amplitude_m']
        if (not np.array_equal(z['station_m'],station) or amplitude.shape!=previous_depth.shape or
                not np.isfinite(amplitude).all() or np.any(amplitude<=0) or np.any(amplitude>10.) or
                not np.array_equal(z['previous_depth_amplitude_m'],previous_depth)):
            raise ValueError('Depth inference differs from source profile or bounded construction assumptions')
        if dm.get('native_calibration'):
            verify_calibrated_depth(dm,z)
        result=amplitude.copy()
    return result,dict(manifest=str(folder/'manifest.json'),manifest_sha256=sha(folder/'manifest.json'),
                       depth_sha256=dm['depth_sha256'])


def verify_calibrated_depth(manifest, arrays):
    """Calibrated geometry remains a bounded, traceable inference, not a solve."""
    receipt=manifest['native_calibration'];parent=Path(receipt['parent_manifest'])
    if (sha(parent)!=receipt['parent_manifest_sha256'] or
            sha(parent.parent/'depth.npz')!=receipt['parent_depth_sha256'] or
            sha(Path(receipt['review']))!=receipt['review_sha256'] or
            sha(Path(receipt['frame']))!=receipt['frame_sha256']):
        raise ValueError('Changed native calibration lineage')
    pm=json.loads(parent.read_text())
    if pm.get('native_calibration') or pm['depth_sha256']!=receipt['parent_depth_sha256']:
        raise ValueError('One bounded calibration step requires its original depth source')
    for key in ('source_profile_sha256','source_terrain_sha256','source_route_sha256',
                'source_planform_sha256','ownership_policy','discharge_m3s','manning_n'):
        if pm[key]!=manifest[key]:raise ValueError('Calibration changed source identity or assumptions')
    with np.load(parent.parent/'depth.npz',allow_pickle=False) as original:
        for key in ('station_m','previous_depth_amplitude_m'):
            if not np.array_equal(original[key],arrays[key]):
                raise ValueError('Calibration changed original profile')
        if not np.array_equal(original['depth_amplitude_m'],arrays['calibration_parent_depth_amplitude_m']):
            raise ValueError('Calibration parent amplitude changed')
    step=arrays['calibration_step_m'];station=arrays['station_m']
    bounds=np.asarray(receipt['statistics']['bounds_m'])
    if (step.shape!=station.shape or not np.isfinite(step).all() or np.any(step<0)
            or np.any(step>.75+1e-12) or bounds.shape!=(2,) or not np.isfinite(bounds).all()
            or not station[0]<=bounds[0]<bounds[1]<=station[-1]
            or np.any(step[(station<=bounds[0])|(station>=bounds[1])]!=0)
            or not np.array_equal(arrays['depth_amplitude_m'],arrays['calibration_parent_depth_amplitude_m']+step)
            or receipt.get('requires_fresh_canonical_export_and_native_review') is not True):
        raise ValueError('Unbounded or unregistered calibrated depth')


class CorridorBed:
    def __init__(self, terrain_folder, profile_folder, discharge=45., roughness=.045, depth_profile=None):
        self.terrain = CorridorTerrain(terrain_folder)
        profile_folder = Path(profile_folder).resolve()
        path = profile_folder / 'manifest.json'
        m = json.loads(path.read_text())
        if (m.get('schema') != 'raftsim.chilko_corridor_profile.v1' or
                m.get('river_id') != 'chilko_river_bc' or m.get('horizontal_crs') != 'EPSG:3157' or
                m.get('vertical_reference') != 'CGVD2013 (EPSG:6647)' or
                m.get('continuous_reference_complete') is not True or m.get('diagnostic_only') is not False or
                m.get('measured_surface') is not False or m.get('measured_bed') is not False or
                m['source_terrain']['sha256'] != sha(self.terrain.folder / 'manifest.json') or
                m['profile_sha256'] != sha(profile_folder / 'profile.npz')):
            raise ValueError('Complete hash-verified inferred profile on this terrain required')
        route = Path(m['route']['path']); planform = Path(m['planform']['path'])
        if (sha(route) != m['route']['sha256'] or sha(planform) != m['planform']['sha256'] or
                sha(planform.with_suffix('.json')) != m['planform']['metadata_sha256']):
            raise ValueError('Changed route or planform source')
        self.polygon = load_planform(planform, route)
        planform_policy=route_planform_policy(route)
        if m.get('planform_policy',dict(kind='original_FWA_polygons'))!=planform_policy:
            raise ValueError('Changed source/derived planform policy')
        if not self.polygon.is_valid:
            raise ValueError('Invalid source planform')
        shapely.prepare(self.polygon)
        self.line = LineString(route_xy(route))
        with np.load(profile_folder / 'profile.npz', allow_pickle=False) as z:
            self.station, self.surface, self.width = [z[key] for key in ('station_m', 'reference_m', 'width_m')]
            self.ownership_reference, ownership_gaps = source_water_reference(self.station, z['raw_reference_m'])
        if (abs(self.station[0]) > 1e-8 or abs(self.station[-1] - self.line.length) > 1e-6 or
                not compatible_capture_route(route, self.terrain.manifest['route_sha256'])):
            raise ValueError('Profile and terrain must cover the identical complete source route')
        self.depth, self.slope = inferred_depth_parameters(self.station, self.surface, self.width, discharge, roughness)
        self.receipt = dict(profile_manifest=str(path), profile_manifest_sha256=sha(path),
            profile_sha256=m['profile_sha256'], terrain_manifest_sha256=m['source_terrain']['sha256'],
            route_sha256=m['route']['sha256'], planform_sha256=m['planform']['sha256'],
            discharge_m3s=discharge, manning_n=roughness, min_reference_slope=.001,
            scope='Initial inferred bed only; no solved discharge, named-rapid geometry or measured bathymetry',
            source_reference_max_regression_adjustment_m=m['regression_abs_adjustment_max_m'],
            source_reference_weight_policy=m.get('regression_weight_policy', 'legacy equal sample weights'),
            ownership_policy='local_raw_channel_reference_plus_0.25m_v1',
            ownership_reference_gaps=ownership_gaps,
            inferred_reference_gaps=m['inferred_reference_gaps'])
        if planform_policy['kind']!='original_FWA_polygons':
            self.receipt['planform_policy']=planform_policy
        if depth_profile is not None:
            expected=dict(schema='raftsim.chilko_available_channel_depth.v1',
                source_profile_sha256=sha(path),source_terrain_sha256=m['source_terrain']['sha256'],
                source_route_sha256=m['route']['sha256'],source_planform_sha256=m['planform']['sha256'],
                ownership_policy=self.receipt['ownership_policy'],discharge_m3s=discharge,manning_n=roughness,
                hydraulic_solution=False)
            self.depth,self.receipt['available_channel_depth']=load_available_depth(
                depth_profile,self.station,self.depth,expected)

    def sample(self, xy):
        xy = np.asarray(xy, dtype=float)
        terrain, kind = self.terrain.sample(xy)
        if not np.isfinite(terrain).all():
            raise ValueError('Missing terrain support; no edge clamp or invented dry ground')
        mapped = shapely.contains_xy(self.polygon, xy[..., 0], xy[..., 1])
        reference = np.full(terrain.shape, np.nan)
        ownership_reference = reference.copy()
        width = np.full(terrain.shape, np.nan); depth = width.copy(); distance = width.copy()
        if mapped.any():
            p = shapely.points(xy[mapped])
            s = shapely.line_locate_point(self.line, p)
            # Do not extend reference stages past source endpoints in a tangent
            # direction. Uncovered upper/lower river outside the run stays terrain.
            interior = (s > self.station[0]) & (s < self.station[-1])
            selected = np.flatnonzero(mapped)
            mapped.flat[selected[~interior]] = False
            selected = selected[interior]; p = p[interior]; s = s[interior]
            reference.flat[selected] = np.interp(s, self.station, self.surface)
            ownership_reference.flat[selected] = np.interp(s, self.station, self.ownership_reference)
            width.flat[selected] = np.interp(s, self.station, self.width)
            depth.flat[selected] = np.interp(s, self.station, self.depth)
            distance.flat[selected] = shapely.distance(p, self.polygon.boundary)
        bed, inferred = carve_mapped_water(terrain, kind, mapped, reference, distance, width, depth,
                                          ownership_reference)
        return dict(height_m=bed, source_height_m=terrain, source_kind=kind,
                    inferred_bed=inferred, mapped_water=mapped, reference_m=reference,
                    ownership_reference_m=ownership_reference)
