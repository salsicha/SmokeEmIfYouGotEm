"""Native water inputs on one full-route chart and exact engine terrain.

The Gaussian chart smooths only coordinates, not geography. Classified
water and elevations are resampled at physical positions. This is construction
input, not a solved flow, navigability proof or substitute for the full map.
"""
import argparse
import copy
import json
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry import LineString, Polygon

from build_curvilinear_river_scenario import TEMPLATE
from chilko_corridor_chart import full_route_frame, hydraulic_frame
from chilko_corridor_bed import CorridorBed
from chilko_native_friction import friction_contract
from export_colorado_continuous_terrain import LandscapeTriangles, sha


def validate_chart_footprint(frame, half_width, profile, source_length):
    """Both local metric and global strip topology must remain unambiguous.

    A numerical centreline may lie on land provided its strip covers the actual
    source channel. Moving banks to match that centreline is never permitted.
    """
    xy, normal = frame['xy'], frame['normal']
    metric_min = float(1-np.abs(frame['curvature']).max()*half_width)
    strip = Polygon(np.r_[xy+normal*half_width, (xy-normal*half_width)[::-1]])
    if metric_min <= .1 or not strip.is_valid:
        raise ValueError('Full numerical strip folds locally or overlaps globally')
    selected = (profile['station_m'] >= 20.) & (profile['station_m'] <= source_length-20.)
    probes = np.concatenate([profile['xy_m'][selected],
        profile['xy_m'][selected]+profile['normal_xy'][selected]*profile['right_bank_m'][selected, None],
        profile['xy_m'][selected]+profile['normal_xy'][selected]*profile['left_bank_m'][selected, None]])
    shapely.prepare(strip)
    if not len(probes) or not shapely.covers(strip, shapely.points(probes)).all():
        raise ValueError('Full numerical strip clips source route or mapped banks')
    return dict(minimum_full_strip_metric=metric_min, full_strip_valid=True,
                source_route_and_bank_probes_covered=len(probes), half_width_m=half_width)


def initialize(bed, stage, channel, metric, discharge, spacing=2.):
    bed, channel, metric = np.asarray(bed), np.asarray(channel), np.asarray(metric)
    stage = np.asarray(stage)
    if (bed.ndim != 2 or channel.shape != bed.shape or metric.shape != bed.shape or
            channel.dtype.kind != 'b' or stage.shape not in ((bed.shape[0],), bed.shape) or
            not np.isfinite(bed).all() or
            not np.isfinite(metric).all() or not np.isfinite([discharge, spacing]).all() or
            discharge <= 0 or spacing <= 0):
        raise ValueError('Aligned finite bed, stage and classified channel required')
    if stage.ndim == 1: stage = np.broadcast_to(stage[:, None], bed.shape)
    if not np.isfinite(stage[channel]).all():
        raise ValueError('Every classified cell needs its geographic stage')
    # Retain the existing construction no-fold gate, checking ALL classified
    # channel, not only initially wet cells which can hide a dry obstruction.
    if not channel.any() or np.min(metric[channel]) <= .1:
        raise ValueError('Classified channel folds or is empty on this chart')
    if channel[:, 0].any() or channel[:, -1].any():
        raise ValueError('Classified water clipped by lateral domain boundary')
    delta = np.where(channel, stage, bed)-bed
    depth = np.where(channel & (delta > .02), delta, 0.)
    conveyance = (depth**(5/3)).sum(axis=1)*spacing
    if np.any(conveyance <= 0):
        bad = np.flatnonzero(conveyance <= 0)
        raise ValueError(f'Dry hydraulic cross sections: {bad[:20].tolist()} ({len(bad)} total)')
    velocity = discharge * depth**(2/3)/conveyance[:, None]
    if not np.isfinite(velocity).all(): raise ValueError('Nonfinite initial velocity')
    return depth, velocity


def validate_branch_coverage(frame, half_width, polygon, source_line):
    """A strip covering the main route must not silently discard mapped branches.

    Four-metre boundary sampling is only a coverage screen, not a mesh or rapid
    reconstruction. Source-end extrapolations are excluded by the same 20 m
    longitudinal buffers as the full-corridor input builder.
    """
    xy,normal=frame['xy'],frame['normal']
    strip=Polygon(np.r_[xy+normal*half_width,(xy-normal*half_width)[::-1]])
    if not strip.is_valid or np.min(1-abs(frame['curvature'])*half_width)<=.1:
        raise ValueError('Invalid or folded strip for branch coverage')
    boundary=shapely.get_coordinates(shapely.segmentize(polygon.boundary,4.))
    points=shapely.points(boundary)
    station=shapely.line_locate_point(source_line,points)
    active=(station>=20.)&(station<=source_line.length-20.)
    if not active.any():raise ValueError('No interior mapped branch boundary')
    points=points[active]
    covered=shapely.covers(strip,points)
    result=dict(mapped_boundary_probe_count=len(points),mapped_boundary_uncovered_count=int((~covered).sum()),
                boundary_probe_step_m=4.,all_mapped_branches_covered=bool(covered.all()))
    if not covered.all():
        missing=station[active][~covered]
        raise ValueError(f'Numerical strip clips mapped river branches: {result["mapped_boundary_uncovered_count"]}/{len(points)} boundary probes, source range {missing.min():.3f}..{missing.max():.3f} m')
    return result


def build(terrain, profile, canonical, out, source_interval=None):
    out = Path(out).resolve()
    if out.exists(): raise ValueError('Fresh full-route hydraulic inputs required')
    triangles = LandscapeTriangles(canonical); m = triangles.manifest
    depth_spec=m['evidence_source'].get('available_channel_depth')
    model = CorridorBed(terrain, profile, m['evidence_source']['discharge_m3s'],
        m['evidence_source']['manning_n'],
        depth_profile=Path(depth_spec['manifest']).parent if depth_spec else None)
    if depth_spec!=model.receipt.get('available_channel_depth'):
        raise ValueError('Terrain and hydraulic available-channel depth sources disagree')
    if m['evidence_source'].get('planform_policy')!=model.receipt.get('planform_policy'):
        raise ValueError('Terrain and hydraulic branch-width inference disagree')
    if (m.get('river_id') != 'chilko_river_bc' or m.get('horizontal_crs') != 'EPSG:3157' or
            m.get('vertical_reference') != 'CGVD2013 (EPSG:6647)' or m.get('world_y_sign') != -1 or
            any(m['evidence_source'].get(key) != model.receipt[key] for key in
                ('profile_manifest_sha256', 'profile_sha256', 'terrain_manifest_sha256', 'route_sha256',
                 'planform_sha256', 'ownership_policy', 'discharge_m3s', 'manning_n'))):
        raise ValueError('Full-corridor source, terrain and hydraulic assumptions disagree')
    digest = sha(triangles.folder/'manifest.json')
    smoothing_m,half_width,end_extension_m=320.,256.,64.
    frame,chart_policy = hydraulic_frame(model.line,model.receipt.get('planform_policy'))
    with np.load(Path(profile)/'profile.npz', allow_pickle=False) as z: profile_data = dict(z)
    footprint = validate_chart_footprint(frame, half_width, profile_data, model.line.length)
    footprint.update(validate_branch_coverage(frame,half_width,model.polygon,model.line),
        smoothing_m=smoothing_m,numerical_end_extension_m=end_extension_m,
        repeated_source_vertex_projections=int((np.diff(frame['source_station'])==0).sum()))
    # Explicit boundary buffers, not a collection of disconnected rapid windows.
    interval = np.asarray(source_interval if source_interval is not None else
                           [20., model.line.length-20.], dtype=float)
    if (interval.shape != (2,) or not np.isfinite(interval).all() or
            not 0 < interval[0] < interval[1] < model.line.length):
        raise ValueError('Interior ordered source interval required')
    selected = (frame['source_station'] >= interval[0]) & (frame['source_station'] <= interval[1])
    if selected.sum() < 3: raise ValueError('Insufficient hydraulic interval')
    full_frame = frame
    frame = {k: v[selected] for k, v in frame.items()}
    lateral = np.arange(-half_width, half_width+2., 2.)
    shape = (len(frame['station']), len(lateral))
    bed = np.empty(shape); dem = np.empty(shape)
    mapped = np.empty(shape, bool); channel = np.empty(shape, bool)
    ownership = np.empty(shape); cell_stage = np.empty(shape); kinds = np.empty(shape, np.uint8)
    for start in range(0, shape[0], 256):
        sl = slice(start, start+256)
        xy = frame['xy'][sl, None, :] + frame['normal'][sl, None, :]*lateral[None, :, None]
        source = model.sample(xy)
        bed[sl] = triangles.sample(xy); dem[sl] = source['source_height_m']
        mapped[sl] = source['mapped_water']; ownership[sl] = source['ownership_reference_m']
        cell_stage[sl] = source['reference_m']
        channel[sl] = source['mapped_water'] & (source['source_height_m'] <= source['ownership_reference_m']+.25)
        kinds[sl] = source['source_kind']
        if start % 2048 == 0: print(f'canonical hydraulic sections {start}/{shape[0]}', flush=True)
    stage = np.interp(frame['source_station'], model.station, model.surface)
    metric = 1-frame['curvature'][:, None]*lateral[None, :]
    depth, velocity = initialize(bed, cell_stage, channel, metric, model.receipt['discharge_m3s'])
    q = model.receipt['discharge_m3s']; step = 2.
    h_in = depth[0]; active = h_in >= .15
    denominator = (np.where(active, h_in, 0.)**(5/3)).sum()*step
    if denominator <= 0: raise ValueError('No supported discharge inlet')
    u_in = np.where(active, q*h_in**(2/3)/denominator, 0.)
    origin = np.asarray(m['horizontal_origin_m'])
    mapping = dict(schema='raftsim.curved_river_coordinate_map.v1', river_id='chilko_river_bc',
        section_id='chilko_full_corridor', world_y_sign=-1, horizontal_crs=m['horizontal_crs'],
        vertical_reference=m['vertical_reference'], horizontal_origin_m=origin.tolist(),
        vertical_datum_m=m['vertical_datum_m'],
        mapping_policy=f'One full FWA route {smoothing_m:g} m Gaussian numerical chart, 2 m arc lattice; geography is not smoothed; vertex projection plateaus do not duplicate physical grid cells',
        numerical_chart_policy=chart_policy,
        points=np.c_[full_frame['station'], full_frame['xy']-origin, full_frame['normal']].tolist())
    receipt = dict(manifest=str(triangles.folder/'manifest.json'), manifest_sha256=digest,
        sampling='encoded_native_landscape_triangles', source_kind='full_chilko_corridor', **model.receipt)
    sc = copy.deepcopy(json.loads(TEMPLATE.read_text()))
    sc['grid'] = dict(nx=shape[0], ny=shape[1], dx=step, dy=step,
                      origin_x=float(frame['station'][0]), origin_y=float(lateral[0]))
    ghost = np.c_[bed[0], h_in, u_in, np.zeros_like(u_in)]
    sc['boundaries'] = [dict(edge='west', kind='discharge_profile', ghost_cells=np.tile(ghost, (2, 1)).tolist(),
                            metadata=dict(target_discharge_m3s=q, distribution='h^(5/3) conveyance')),
        dict(edge='east', kind='outflow', stage=float(stage[-1])), dict(edge='south', kind='bank'), dict(edge='north', kind='bank')]
    friction = friction_contract(model.receipt['manning_n'])
    sc.update(fixed_dt=.05, duration=1200., roughness=friction['native_roughness_coefficient'], feature_count=0, probe_count=0)
    sc['metadata'] = dict(scenario_id=out.name.replace('-', '_'), scenario_type='real_world', fixture_kind=None,
        river_id='chilko_river_bc', flow_band=f'inferred_{q:g}m3s', generator=Path(__file__).name,
        description='Continuous full-source construction inputs; no calibrated rapid forces',
        provenance=dict(continuous_terrain=receipt, friction=friction, target_discharge_m3s=q, measured_velocity=False,
            flow_source=f'{q:g} m3/s construction assumption, not a measured concurrent discharge',
            submerged_bed_is_inference=True, initial_velocity_is_inferred=True))
    report = dict(stations=shape[0], lateral_cells=shape[1], half_width_m=half_width, chart_footprint=footprint,
        evidence_station_range=frame['source_station'][[0, -1]].tolist(), requested_source_interval_m=interval.tolist(),
        complete_source_route_length_m=model.line.length, full_route_chart=True,
        stage_sampling='per_cell_exact_source_route_projection_v1', friction=friction,
        numerical_chart_policy=chart_policy,
        maximum_classified_stage_difference_from_row_m=float(abs(cell_stage-stage[:,None])[channel].max()),
        full_route_hydraulic_inputs=source_interval is None, continuous_terrain=receipt,
        metric_ratio_wet_min_max=[float(metric[depth>0].min()), float(metric[depth>0].max())],
        metric_ratio_classified_min_max=[float(metric[channel].min()), float(metric[channel].max())],
        metric_warning='Native solver has no curvilinear metric terms; solved physical-space flow needs review',
        initial_max_speed_mps=float(velocity.max()), initial_min_wet_width_m=float((depth>.05).sum(axis=1).min()*step),
        initial_discharge_max_error_m3s=float(abs((depth*velocity).sum(axis=1)*step-q).max()),
        hydraulic_solution=False, engine_validated=False)
    if sha(triangles.folder/'manifest.json') != digest: raise ValueError('Terrain changed during input generation')
    out.mkdir(parents=True); pkg = out/'scenario'; pkg.mkdir()
    np.save(pkg/'bed.npy', np.ascontiguousarray(bed.T))
    h, u = np.ascontiguousarray(depth.T), np.ascontiguousarray(velocity.T)
    np.savez_compressed(pkg/'initial_state.npz', depth=h, eta=bed.T+h, u=u, v=np.zeros_like(u),
                        hu=h*u, hv=np.zeros_like(u), wet=h>1e-6)
    xy = frame['xy'][:, None, :] + frame['normal'][:, None, :]*lateral[None, :, None]
    np.savez_compressed(out/'reference.npz', station=frame['station'], lateral=lateral,
        evidence_station=frame['source_station'], ws_reference=stage, ws_reference_grid=cell_stage.T, dem2021=dem.T,
        river=mapped.T, channel=channel.T, source_kind=kinds.T, ownership_reference=ownership.T,
        curvature=frame['curvature'], world_x=xy[..., 0].T, world_y=xy[..., 1].T)
    for path, value in [(pkg/'scenario.json', sc), (pkg/'features.json', {'features': []}),
                        (pkg/'probes.json', {'probes': []}), (out/'coordinate_map.json', mapping),
                        (out/'build_report.json', report)]:
        path.write_text(json.dumps(value, allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k != 'continuous_terrain'}, indent=2))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('terrain', 'profile', 'canonical', 'out'): parser.add_argument('--'+key, type=Path, required=True)
    parser.add_argument('--source-interval', type=float, nargs=2, help='Optional construction window on the SAME full-route chart')
    a = parser.parse_args(); build(a.terrain, a.profile, a.canonical, a.out, a.source_interval)
