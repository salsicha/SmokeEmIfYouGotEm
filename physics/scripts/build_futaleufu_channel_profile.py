"""Continuous three-arm stage/width construction from native captured pixels.

All stages are INFERRED. Mainstem banks use captured OSM mapping; unmapped
tributary banks use spectral span inference. GLO-30 is an edited DSM, not
bathymetry; neither mapping nor classification is a surveyed bank. Keep raw
support and every fallback alongside the construction values. No discharge,
bed excavation or native hydraulic acceptance is asserted here.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import shapely
from scipy.ndimage import distance_transform_edt

from build_futaleufu_corridor_sources import ROOT, BASE, sha
from build_futaleufu_corridor_water_reference import classify, consensus, route_components
from build_pacuare_evidence_grid import pava_nonincreasing
from futaleufu_planform import load_planform, mapped_span

PLANFORM_CAPTURE=BASE/'futaleufu_sources_2026_09/osm/futaleufu_overpass.json'


def fit_stage(raw, weights, junction, incoming):
    raw, weights = np.asarray(raw, float), np.asarray(weights, float)
    if (raw.ndim != 1 or len(raw) < 2 or weights.shape != raw.shape or
            not np.isfinite(raw).all() or not np.isfinite(weights).all() or
            np.any(weights <= 0) or not np.isfinite(junction) or not isinstance(incoming, bool)):
        raise ValueError('Finite supported profile, positive weights and junction required')
    fitted = pava_nonincreasing(raw, weights)
    # An exact boundary constraint, not an enormous pseudo-observation weight.
    # The independent fits cannot create a step at the common junction.
    return np.maximum(fitted, junction) if incoming else np.minimum(fitted, junction)


def choose_stage(interior, wet, near):
    interior, wet, near = [np.asarray(a, float) for a in (interior, wet, near)]
    if any(a.ndim != 1 or not np.isfinite(a).all() for a in (interior, wet, near)):
        raise ValueError('Finite one-dimensional DSM supports required')
    if len(interior) >= 2:
        return float(np.median(interior)), float(len(interior)), 'interior_water_dsm'
    if len(wet) >= 2:
        return float(np.median(wet)), .25*len(wet), 'edge_water_dsm'
    if len(near) >= 2:
        return float(np.percentile(near, 10)), .01*len(near), 'near_route_dsm_fallback'
    raise ValueError('No local DSM support: cannot fabricate a stage')


def fill_spans(station, left, right):
    station, left, right = map(lambda a: np.asarray(a, float), (station, left, right))
    if (station.ndim != 1 or len(station) < 2 or left.shape != station.shape or right.shape != station.shape
            or not np.isfinite(station).all() or np.any(np.diff(station) <= 0)):
        raise ValueError('Increasing aligned section stations required')
    have = np.isfinite(left) & np.isfinite(right)
    if np.count_nonzero(have) < 2 or np.any(right[have] <= left[have]):
        raise ValueError('At least two positive source-supported bank spans required')
    # Constant extension outside observed support and linear interpolation in
    # gaps are explicitly flagged, not represented as captured shoreline.
    return (np.interp(station, station[have], left[have]),
            np.interp(station, station[have], right[have]), ~have)


def stage_anchors(records, length, junction, incoming, spacing=200.):
    """Do not turn every noisy 50 m DSM sample into a hydraulic drop.

    Use the established evidence-grid 200 m anchor scale. Within an anchor
    interval, interior water outranks edge water, which outranks canopy-prone
    route fallback. This is inferred macro-grade, not named rapid geometry.
    """
    if not np.isfinite([length,spacing]).all() or length<=0 or spacing<50:
        raise ValueError('Positive route length and at least 50 m anchor spacing required')
    middle=np.array([(r['start_m']+r['end_m'])/2 for r in records])
    edges=np.r_[np.arange(0,length,spacing),length]
    anchors=[]
    for a,b in zip(edges[:-1],edges[1:]):
        selected=[r for r,s in zip(records,middle) if a<=s<b]
        if not selected:
            continue
        for kind in ('interior_water_dsm','edge_water_dsm','near_route_dsm_fallback'):
            support=[r for r in selected if r['kind']==kind]
            if support:
                break
        values=np.array([r['raw_dsm_stage_m'] for r in support])
        weights=np.array([r['weight'] for r in support])
        if kind=='near_route_dsm_fallback':
            # The least elevated local DSM estimate avoids averaging canopy
            # heights into a fictional impoundment; still not a measured stage.
            value=float(values.min())
        else:
            order=np.argsort(values);cumulative=np.cumsum(weights[order])
            value=float(values[order[np.searchsorted(cumulative,cumulative[-1]/2)]])
        anchors.append(dict(station_m=float((a+b)/2),raw_stage_m=value,weight=float(weights.sum()),
                            kind=kind,support_sections=len(support)))
    if len(anchors)<2:
        raise ValueError('At least two stage anchor intervals required')
    fitted=fit_stage([r['raw_stage_m'] for r in anchors],[r['weight'] for r in anchors],junction,incoming)
    for r,value in zip(anchors,fitted):r['inferred_stage_m']=float(value)
    return anchors


def build(source_folder, network_path, output):
    source_folder, network_path, output = map(lambda p: Path(p).resolve(), (source_folder, network_path, output))
    output.relative_to(ROOT)
    if output.exists():
        raise ValueError('Fresh channel-profile output required')
    manifest_path = source_folder/'manifest.json'
    source, network = [json.loads(p.read_text()) for p in (manifest_path, network_path)]
    if (source.get('schema') != 'raftsim.futaleufu_continuous_sources.v1' or
            network.get('schema') != 'raftsim.futaleufu_confluence_network.v1'):
        raise ValueError('Verified native sources and captured confluence required')
    pins = {manifest_path: sha(manifest_path), network_path: sha(network_path)}
    pins[PLANFORM_CAPTURE]=sha(PLANFORM_CAPTURE)
    planform=shapely.union_all([g for _,_,g in load_planform(PLANFORM_CAPTURE)])
    for item in (source, network):
        for relative, digest in item['sources_sha256'].items():
            path = (ROOT/relative).resolve(); path.relative_to(ROOT)
            if sha(path) != digest:
                raise ValueError('Changed source input')
            pins[path] = digest
    if network['sources_sha256'].get(manifest_path.relative_to(ROOT).as_posix()) != sha(manifest_path):
        raise ValueError('Network must bind this source window')
    t = source['grid']['transform']; shape = tuple(source['grid']['shape'])
    if source['grid']['epsg'] != 32718 or t[0] != 10 or t[4] != -10 or t[1] != 0 or t[3] != 0:
        raise ValueError('Native north-up UTM18S ten-metre grid required')
    valid, wet, bright = [], [], []
    for item in source['optical']:
        path = (source_folder/item['file']).resolve(); path.relative_to(source_folder)
        if sha(path) != item['sha256']:
            raise ValueError('Changed optical pixels')
        pins[path] = item['sha256']
        with np.load(path, allow_pickle=False) as data:
            v, w, b = classify(dict(data))
        if v.shape != shape:
            raise ValueError('Native optical shape mismatch')
        valid.append(v); wet.append(w); bright.append(b)
    counts, _, _, repeated = consensus(valid, wet, bright)
    path = (source_folder/source['dsm']['file']).resolve(); path.relative_to(source_folder)
    if sha(path) != source['dsm']['sha256']:
        raise ValueError('Changed DSM pixels')
    pins[path] = source['dsm']['sha256']
    with np.load(path, allow_pickle=False) as data:
        dsm = data['dsm_m']
    if dsm.shape != shape or not np.isfinite(dsm).all():
        raise ValueError('Finite native aligned DSM required')
    names = ['rio_azul', 'upstream_mainstem', 'downstream_mainstem']
    if set(network['branches']) != set(names):
        raise ValueError('Exactly two inlets and one downstream branch required')
    lines = [shapely.LineString(np.asarray(network['branches'][name]['points_station_easting_northing_m'])[:,1:]) for name in names]
    junction = np.asarray(network['junction']['easting_northing_m'])
    for j, line in enumerate(lines):
        if not np.array_equal(np.asarray(line.coords)[-1 if j < 2 else 0], junction):
            raise ValueError('Branches do not share the captured junction')
    rows, cols = np.indices(shape)
    east, north = t[2]+(cols+.5)*10, t[5]-(rows+.5)*10
    geometry = shapely.points(east, north)
    distances = np.array([shapely.distance(geometry,line) for line in lines])
    owner = distances.argmin(axis=0)
    associated, _, _ = route_components(repeated, distances.min(axis=0))
    interior = associated & (distance_transform_edt(associated)*10 >= 20)
    junction_support = associated & (np.hypot(east-junction[0],north-junction[1]) <= 40)
    if junction_support.sum() < 4:
        raise ValueError('Insufficient native water DSM support at the common junction')
    junction_stage = float(np.median(dsm[junction_support]))
    arrays = {}; summaries = {}
    for j, (name, line) in enumerate(zip(names,lines)):
        stations = shapely.line_locate_point(line,geometry)
        foot = shapely.line_interpolate_point(line,stations)
        before = shapely.line_interpolate_point(line,np.maximum(stations-1,0))
        after = shapely.line_interpolate_point(line,np.minimum(stations+1,line.length))
        dx,dy = shapely.get_x(after)-shapely.get_x(before),shapely.get_y(after)-shapely.get_y(before)
        norm = np.hypot(dx,dy)
        lateral = ((east-shapely.get_x(foot))*(-dy)+(north-shapely.get_y(foot))*dx)/norm
        edges = np.r_[np.arange(0,line.length,50.),line.length]
        records=[]; raw=[]; weights=[]; left=[]; right=[]
        for a,b in zip(edges[:-1],edges[1:]):
            own=(owner==j)&(stations>=a)&(stations<b)&(stations>0)&(stations<line.length)
            water=own&associated; inner=water&interior
            near=own&(distances[j]<=20)
            value,weight,kind=choose_stage(dsm[inner],dsm[water],dsm[near])
            raw.append(value);weights.append(weight)
            if water.sum()>=2:
                # Native pixel-centre distribution plus half a cell, not a
                # subpixel shoreline estimate or a minimum playable width.
                lo,hi=np.percentile(lateral[water],[5,95])+[-5,5]
            else:
                lo=hi=np.nan
            left.append(lo);right.append(hi)
            records.append(dict(start_m=float(a),end_m=float(b),kind=kind,
                interior_pixels=int(inner.sum()),water_pixels=int(water.sum()),near_route_pixels=int(near.sum()),
                raw_dsm_stage_m=value,weight=weight,
                raw_left_m=float(lo) if np.isfinite(lo) else None,
                raw_right_m=float(hi) if np.isfinite(hi) else None))
        middle=(edges[:-1]+edges[1:])/2
        anchors=stage_anchors(records,line.length,junction_stage,j<2)
        anchor_s=np.array([r['station_m'] for r in anchors])
        anchor_z=np.array([r['inferred_stage_m'] for r in anchors])
        support_s=np.r_[0,anchor_s,line.length]
        support_z=np.r_[anchor_z[0] if j<2 else junction_stage,anchor_z,
                        junction_stage if j<2 else anchor_z[-1]]
        fit=np.interp(middle,support_s,support_z)
        lo,hi,span_inferred=fill_spans(middle,left,right)
        sample_s=np.unique(np.r_[np.arange(0,line.length,10),line.length])
        sample_z=np.interp(sample_s,support_s,support_z)
        center=shapely.line_interpolate_point(line,sample_s)
        for key,value in dict(station_m=sample_s,stage_m=sample_z,
                easting_m=shapely.get_x(center),northing_m=shapely.get_y(center),
                left_m=np.interp(sample_s,middle,lo),right_m=np.interp(sample_s,middle,hi),
                raw_section_stage_m=np.array(raw),fitted_section_stage_m=fit,
                section_station_m=middle,spectral_span_interpolated=span_inferred).items():
            arrays[name+'_'+key]=value
        for i,r in enumerate(records):
            r['inferred_stage_m']=float(fit[i]);r['stage_adjustment_m']=float(fit[i]-raw[i])
            r['spectral_span_interpolated']=bool(span_inferred[i])
        # Mainstem source mapping covers dark water missed by NDWI, and its
        # disconnected cross-section components preserve islands/side pools.
        # Rio Azul lacks mapped banks except where it overlaps the confluence;
        # do not borrow the mainstem footprint for its tributary width.
        mapped_samples=0
        if name!='rio_azul':
            before=shapely.line_interpolate_point(line,np.maximum(sample_s-1,0))
            after=shapely.line_interpolate_point(line,np.minimum(sample_s+1,line.length))
            tangent=np.c_[shapely.get_x(after)-shapely.get_x(before),shapely.get_y(after)-shapely.get_y(before)]
            normals=np.c_[-tangent[:,1],tangent[:,0]]/np.linalg.norm(tangent,axis=1)[:,None]
            spans=[]
            for point,normal in zip(np.c_[shapely.get_x(center),shapely.get_y(center)],normals):
                span=mapped_span(planform,point,normal)
                if span is None:
                    raise ValueError(f'Captured mainstem route leaves mapped water: {name}')
                spans.append(span)
            spans=np.asarray(spans)
            arrays[name+'_left_m'],arrays[name+'_right_m']=spans[:,0],spans[:,1]
            mapped_samples=len(spans)
        arrays[name+'_bank_span_mapped']=np.full(len(sample_s),mapped_samples>0,dtype=bool)
        summaries[name]=dict(length_m=float(line.length),samples=len(sample_s),sections=records,stage_anchors=anchors,
            fallback_stage_sections=sum(r['kind']=='near_route_dsm_fallback' for r in records),
            interpolated_span_sections=0 if mapped_samples else int(span_inferred.sum()),
            spectral_interpolated_span_sections=int(span_inferred.sum()),
            stage_adjustment_max_abs_m=float(np.max(abs(fit-np.array(raw)))),
            width_m_p10_p50_p90=np.percentile(arrays[name+'_right_m']-arrays[name+'_left_m'],[10,50,90]).tolist(),
            bank_span_basis='captured_OSM_component_containing_route' if mapped_samples else 'spectral_span_with_explicit_interpolation',
            mapped_bank_samples=mapped_samples,
            stage_start_m=float(sample_z[0]),stage_end_m=float(sample_z[-1]),
            maximum_inferred_interval_slope=float(np.max(-np.diff(sample_z)/np.diff(sample_s))))
    if not all(sha(p)==digest for p,digest in pins.items()):
        raise ValueError('Source changed during profile construction')
    output.mkdir(parents=True)
    np.savez_compressed(output/'profile.npz',**arrays)
    report=dict(schema='raftsim.futaleufu_channel_profile.v1',
        sources_sha256={p.relative_to(ROOT).as_posix():digest for p,digest in pins.items()},
        profile_sha256=sha(output/'profile.npz'),junction_stage_m=junction_stage,
        junction_support_pixels=int(junction_support.sum()),branches=summaries,
        vertical_reference='EGM2008; edited GLO-30 DSM-based inference, not observed local stage',
        mapped_planform_source=PLANFORM_CAPTURE.relative_to(ROOT).as_posix(),
        construction_policy=dict(section_length_m=50,profile_sample_m=10,stage_anchor_interval_m=200,
            junction_support_radius_m=40,near_route_fallback_radius_m=20,
            bank_span='Mainstem: exact captured OSM water component containing route at each sample, islands retained. Unmapped Rio Azul: 5th/95th native water lateral percentiles plus half-cell; missing spans linearly interpolated, endpoints held.',
            stage='Quality-prioritized 200 m DSM anchors; weighted nonincreasing regression, exactly constrained to a common inferred junction stage',
            ownership='Closest captured branch and clamped segment station; endpoint caps excluded from section evidence'),
        attribution=dict(route=network['rights'],optical=source['optical_attribution'],
            optical_license=source['optical_license'],dsm_license_url=source['dsm']['license_url'],
            dsm_distribution_requires_article_6_notices=True),
        limitations=['Every stage is inferred; OSM banks are mapped, not surveyed or image-date shoreline. Raw DSM and spectral evidence retained separately.',
            'Near-route DSM fallback can contain canopy; no bare-earth or underwater measurement implied.',
            'Missing optical spans are flagged, not proof of dry river or permission to narrow a channel. Mapped mainstem banks override spectral spans only, not the retained raw DSM stage observations.',
            'Monotone stage is construction scaffolding, not a solved free surface; rapid drops still need local evidence and hydraulic checks.',
            'Interpolated width and stage do not establish bank stability, nonfolding cross-sections or boat passage.'],
        unknown_optical_observations=int((3-counts).sum()),discharge_assigned=False,
        bed_constructed=False,installed_in_engine=False,full_river_complete=False)
    (output/'manifest.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sources',type=Path,required=True);p.add_argument('--network',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();r=build(a.sources,a.network,a.out)
    print(json.dumps(dict(junction_stage_m=r['junction_stage_m'],branches={name:{k:v[k] for k in
        ('samples','fallback_stage_sections','interpolated_span_sections','stage_adjustment_max_abs_m',
         'width_m_p10_p50_p90','stage_start_m','stage_end_m','maximum_inferred_interval_slope')} for name,v in r['branches'].items()})))
