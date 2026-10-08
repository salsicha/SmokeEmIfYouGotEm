"""Cook adjoining source windows as one domain, without an internal boundary.

Only exact shared-coordinate inputs are eligible. All rendered bed triangles
must exist. Uncovered lateral padding must be classified dry; it never becomes
an invented water connection. The original source inputs remain immutable.
"""
import argparse
import copy
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

import numpy as np

from build_colorado_catalog_evidence import ROOT, sha
from build_colorado_catalog_scenario import sample_grid
from export_colorado_continuous_terrain import LandscapeTriangles, TerrainMosaic, load_sources
from chilko_native_friction import validate_friction


def initial_conveyance_velocity(depth,dy,discharge):
    depth=np.asarray(depth,dtype=float)
    if (depth.ndim!=2 or not np.isfinite(depth).all() or np.any(depth<0) or
            not np.isfinite([dy,discharge]).all() or dy<=0 or discharge<=0):
        raise ValueError('Invalid initial conveyance parameters')
    # Preserve the original reduction shape/order: a one-column block changes
    # NumPy's pairwise reduction and can change the initialization's last bits.
    # Reuse the output allocation for pointwise operations instead.
    conveyance=(depth**(5/3)).sum(axis=0)*dy
    if np.any(conveyance<=0):raise ValueError('Dry initial cross-section')
    velocity=depth**(2/3)
    velocity*=discharge
    velocity/=conveyance[None,:]
    np.copyto(velocity,0.,where=depth<=0)
    return velocity


def validate_initial_conveyance(item,discharge):
    """Prove this is untouched source-stage initialization, not cooked flow."""
    depth=np.asarray(item['depth']);bed=np.asarray(item['bed']);mask=np.asarray(item['classified_water'])
    surface=np.asarray(item['reference_surface'])
    if (depth.ndim!=2 or bed.shape!=depth.shape or mask.shape!=depth.shape or
            surface.shape!=(depth.shape[1],) or not np.isfinite(bed).all() or not np.isfinite(surface).all()):
        raise ValueError('Invalid source initial-state geometry')
    stage_depth=surface[None,:]-bed
    expected=np.where(mask.astype(bool)&(stage_depth>.02),stage_depth,0.)
    if not np.array_equal(depth,expected):raise ValueError('Depth is not the captured-stage initial hypothesis')
    velocity=initial_conveyance_velocity(depth,item['grid']['dy'],discharge)
    if (np.shape(item['u'])!=depth.shape or np.shape(item['v'])!=depth.shape or
            not np.allclose(item['u'],velocity,atol=1e-12,rtol=0) or not np.all(np.asarray(item['v'])==0)):
        raise ValueError('Flow is not the original un-cooked conveyance initialization')


def validate_reinitialization_contract(report,scenario):
    if (report.get('solved') is not False or report.get('accepted') is not False or
            scenario.get('metadata',{}).get('generator')!='build_colorado_catalog_scenario.py' or
            scenario.get('feature_count')!=0 or scenario.get('probe_count')!=0):
        raise ValueError('Only explicit un-cooked source initialization may be rebuilt')


def merge_registered(items, bed, grid, padding_water,initial_discharge=None):
    """Merge actual cell states; disagreement or missing wet coverage is fatal."""
    shape = bed.shape
    fields = {key: np.zeros(shape) for key in ('depth', 'u', 'v')}
    covered = np.zeros(shape, bool)
    classified = np.zeros(shape, bool)
    surface = np.full(shape[1], np.nan)
    for item in items:
        if initial_discharge is not None:validate_initial_conveyance(item,initial_discharge)
        g = item['grid']
        offset = np.array([(g['origin_y']-grid['origin_y'])/grid['dy'],
                           (g['origin_x']-grid['origin_x'])/grid['dx']])
        if not np.allclose(offset, np.rint(offset), atol=1e-9, rtol=0):
            raise ValueError('Inputs do not share an exact cell lattice')
        row, col = np.rint(offset).astype(int)
        if row < 0 or col < 0 or row+g['ny'] > shape[0] or col+g['nx'] > shape[1]:
            raise ValueError('Source outside joined grid')
        sl = (slice(row, row+g['ny']), slice(col, col+g['nx']))
        if not np.array_equal(item['bed'], bed[sl], equal_nan=True):
            raise ValueError('Source bed differs from shared rendered triangles')
        overlap = covered[sl]
        for key in fields:
            values = np.asarray(item[key])
            if values.shape != item['bed'].shape or not np.isfinite(values).all():
                raise ValueError('Incomplete or nonfinite source state')
            if (not (initial_discharge is not None and key=='u') and
                    not np.allclose(fields[key][sl][overlap], values[overlap], atol=1e-10, rtol=0)):
                raise ValueError('Source states disagree in overlap')
            # Keep the first owner bit-for-bit. No averaging or blend conceals
            # differences at the source boundary.
            fields[key][sl][~overlap] = values[~overlap]
        mask = item['classified_water'].astype(bool)
        if not np.array_equal(classified[sl][overlap], mask[overlap]):
            raise ValueError('Source water classifications disagree')
        classified[sl][~overlap] = mask[~overlap]
        target = surface[col:col+g['nx']]
        valid = np.isfinite(target)
        if not np.allclose(target[valid], item['reference_surface'][valid], atol=1e-9, rtol=0):
            raise ValueError('Source stage references disagree')
        target[~valid] = item['reference_surface'][~valid]
        covered[sl] = True
    if not np.isfinite(surface).all():
        raise ValueError('Source gap in continuous domain')
    if np.any(~covered & padding_water):
        raise ValueError('Uncovered classified water cannot be initialized as dry padding')
    if not np.isfinite(bed).all() or (fields['depth'] < 0).any():
        raise ValueError('Missing bed or negative depth')
    if initial_discharge is not None:
        # Independently normalized source windows can include different side
        # channels in their HALOS. Reconstruct the initial Q distribution on
        # the complete joined depth; never average velocities or blend cooked
        # states. Bed, depth, stage, classification and wet coverage still
        # have to agree exactly under the ordinary merge checks above.
        fields['u']=initial_conveyance_velocity(fields['depth'],grid['dy'],initial_discharge)
    return fields, classified, surface, covered


def write_native_arrays(pkg, bed, h, u, v):
    """Native arrays are row-major, including a transposed terrain sample."""
    np.save(pkg/'bed.npy', np.ascontiguousarray(bed, dtype='<f8'))
    # Keep only one derived serialization array live, not eta/hu/hv together.
    # This remains an ordinary, lossless NumPy NPZ package for the native reader.
    target=pkg/'initial_state.npz';partial=pkg/'initial_state.npz.partial'
    with ZipFile(partial,'w',compression=ZIP_DEFLATED,allowZip64=True) as archive:
        for key in ('depth','eta','u','v','hu','hv','wet'):
            if key=='eta':value=bed+h
            elif key=='hu':value=h*u
            elif key=='hv':value=h*v
            elif key=='wet':value=h>1e-6
            else:value={'depth':h,'u':u,'v':v}[key]
            value=np.ascontiguousarray(value,dtype=bool if key=='wet' else '<f8')
            with archive.open(key+'.npy','w',force_zip64=True) as member:
                np.lib.format.write_array(member,value,allow_pickle=False)
            del value
    partial.replace(target)


def load_join_item(item):
    """Load one immutable source package; never retain every source's arrays."""
    folder=item['folder']
    with np.load(folder/'scenario/initial_state.npz',allow_pickle=False) as state:
        result={key:state[key] for key in ('depth','u','v')}
    with np.load(folder/'reference.npz',allow_pickle=False) as reference:
        result.update({key:reference[key] for key in ('classified_water','reference_surface')})
    result.update(grid=item['grid'],bed=np.load(folder/'scenario/bed.npy',allow_pickle=False))
    return result


def iter_join_items(items,station,step):
    for source in items:
        item=load_join_item(source);g=item['grid']
        start=max(0,int(round((station[0]-g['origin_x'])/step)))
        stop=min(g['nx'],int(round((station[-1]-g['origin_x'])/step))+1)
        for key in ('bed','depth','u','v','classified_water'):
            item[key]=item[key][:,start:stop]
        item['reference_surface']=item['reference_surface'][start:stop]
        item['grid']=dict(g,origin_x=g['origin_x']+start*step,nx=stop-start)
        yield item
        del item


def sample_owned_classification(sources, queries, owner):
    """Sample every query once from its selected source, not every raster.

    Ownership and nearest-neighbour classification are unchanged. Sampling
    the whole full-river query grid for each short source window otherwise
    creates hundreds of river-sized temporary arrays.
    """
    queries=np.asarray(queries,dtype=float);owner=np.asarray(owner)
    if (queries.shape!=owner.shape+(2,) or not np.isfinite(queries).all() or
            not np.issubdtype(owner.dtype,np.integer) or
            np.any(owner<0) or np.any(owner>=len(sources))):
        raise ValueError('Missing or invalid classified-water ownership')
    water=np.zeros(owner.shape,bool)
    for index,source in enumerate(sources):
        selected=owner==index
        if not selected.any():continue
        grid=source['grid']
        mask=np.asarray(grid['classified_water_mask']);corner=np.asarray(grid['corner_east_north_m'])
        points=queries[selected]
        if mask.ndim!=2 or min(mask.shape)<=0 or corner.shape!=(2,) or not np.isfinite(corner).all():
            raise ValueError('Invalid source classification raster')
        height,width=mask.shape;x,y=corner
        if np.any((points[:,0]<x)|(points[:,0]>x+width)|(points[:,1]<y-height)|(points[:,1]>y)):
            raise ValueError('Unclassified terrain padding outside source pixel footprint')
        # Ownership uses the full cell-centred raster footprint. Its outer
        # half-pixel belongs to the existing edge pixel, not to unknown land.
        # This is nearest categorical sampling INSIDE captured pixels only;
        # never extrapolate classification beyond that footprint.
        centers=points.copy()
        centers[:,0]=np.clip(centers[:,0],x+.5,x+width-.5)
        centers[:,1]=np.clip(centers[:,1],y-height+.5,y-.5)
        sampled=sample_grid(mask,centers,corner,True)
        if not np.isfinite(sampled).all():
            raise ValueError('Unclassified terrain padding')
        water[selected]=sampled>.5
    return water


def registered_query_blocks(xy,normal,lateral,max_points=262144):
    """Yield identical chart queries in bounded station blocks; no resampling."""
    xy,normal,lateral=(np.asarray(a,dtype=float) for a in (xy,normal,lateral))
    if (xy.ndim!=2 or xy.shape[1]!=2 or len(xy)==0 or normal.shape!=xy.shape or
            lateral.ndim!=1 or len(lateral)<2 or np.any(np.diff(lateral)<=0) or
            not all(np.isfinite(a).all() for a in (xy,normal,lateral)) or
            not isinstance(max_points,int) or max_points<len(lateral)):
        raise ValueError('Invalid bounded registered query grid')
    columns=max_points//len(lateral)
    for first in range(0,len(xy),columns):
        last=min(first+columns,len(xy))
        yield slice(first,last),xy[first:last,None,:]+normal[first:last,None,:]*lateral[None,:,None]


def sample_registered_terrain(triangles,xy,normal,lateral,max_points=262144):
    bed=np.empty((len(lateral),len(xy)),dtype=float)
    for section,queries in registered_query_blocks(xy,normal,lateral,max_points):
        bed[:,section]=triangles.sample(queries).T
    return bed


def sample_registered_classification(mosaic,xy,normal,lateral,max_points=262144):
    water=np.empty((len(lateral),len(xy)),dtype=bool)
    for section,queries in registered_query_blocks(xy,normal,lateral,max_points):
        _,owner=mosaic.sample(queries[...,0],queries[...,1])
        if (owner<0).any():raise ValueError('Missing classified-water source')
        water[:,section]=sample_owned_classification(mosaic.sources,queries,owner).T
    return water


def join(inputs, out,rebuild_initial_conveyance=False,terrain_extension=None,shared_frame_override=None):
    if out.exists() or len(inputs) < 2:
        raise ValueError('At least two sources and fresh output required')
    reports, scenarios, items = [], [], []
    compatibility=None
    if shared_frame_override is not None:
        from colorado_frame_compatibility import SharedFrameCompatibility
        compatibility=SharedFrameCompatibility(shared_frame_override)
    for folder in inputs:
        folder = folder.resolve()
        report = json.loads((folder/'build_report.json').read_text())
        for name, expected in report['files_sha256'].items():
            if sha(folder/name) != expected:
                raise ValueError('Changed source input')
        if not report.get('shared_hydraulic_frame') or not report.get('continuous_terrain'):
            raise ValueError('Independent source charts cannot be joined')
        common_keys=('continuous_terrain',) if compatibility is not None else ('shared_hydraulic_frame','continuous_terrain')
        if reports and any(report[key] != reports[0][key] for key in common_keys):
            raise ValueError('Different shared frame or terrain')
        scenario = json.loads((folder/'scenario/scenario.json').read_text())
        if compatibility is not None:compatibility.check(report,scenario['grid'])
        if rebuild_initial_conveyance:validate_reinitialization_contract(report,scenario)
        friction=scenario.get('metadata',{}).get('provenance',{}).get('friction')
        if friction is not None:validate_friction(scenario,friction['inferred_manning_n'])
        if scenarios and friction!=scenarios[0].get('metadata',{}).get('provenance',{}).get('friction'):
            raise ValueError('Different physical friction contracts')
        if scenarios and any(scenario[key] != scenarios[0][key] for key in ('roughness', 'fixed_dt')):
            raise ValueError('Different solver parameters')
        items.append(dict(grid=scenario['grid'],folder=folder))
        reports.append(report)
        scenarios.append(scenario)
    ordering = np.argsort([item['grid']['origin_x'] for item in items])
    inputs = [inputs[i].resolve() for i in ordering]
    reports = [reports[i] for i in ordering]
    scenarios = [scenarios[i] for i in ordering]
    items = [items[i] for i in ordering]
    target_q = scenarios[0]['boundaries'][0]['metadata']['target_discharge_m3s']
    if rebuild_initial_conveyance:
        for item,scenario in zip(items,scenarios):
            if scenario['boundaries'][0]['metadata']['target_discharge_m3s']!=target_q:
                raise ValueError('Different source discharge hypotheses')
            validate_initial_conveyance(load_join_item(item),target_q)
    frame_receipt=compatibility.receipt if compatibility is not None else reports[0]['shared_hydraulic_frame']
    frame_path = ROOT/frame_receipt['manifest']
    terrain_path = ROOT/reports[0]['continuous_terrain']['manifest']
    for path, receipt in ((frame_path, frame_receipt),
                          (terrain_path, reports[0]['continuous_terrain'])):
        if sha(path) != receipt['sha256']:
            raise ValueError('Shared dependency changed')
    terrain_receipt=reports[0]['continuous_terrain']
    original_terrain_path=terrain_path
    if terrain_extension is not None:
        from extend_colorado_continuous_terrain import validate_additive_manifest
        terrain_path=Path(terrain_extension).resolve()/'manifest.json'
        terrain_path.relative_to(ROOT)
        original=json.loads(original_terrain_path.read_text())
        extended=json.loads(terrain_path.read_text())
        validate_additive_manifest(original,extended,terrain_receipt['sha256'])
        for chunk in original['chunks']:
            if sha(original_terrain_path.parent/chunk['heightfield'])!=chunk['sha256']:
                raise ValueError('Original terrain tile changed')
        terrain_receipt=dict(manifest=str(terrain_path.relative_to(ROOT)),sha256=sha(terrain_path))
    frame_manifest = json.loads(frame_path.read_text())
    for name, expected in frame_manifest['files_sha256'].items():
        if sha(frame_path.parent/name) != expected:
            raise ValueError('Shared frame file changed')
    arrays = dict(np.load(frame_path.parent/'frame.npz', allow_pickle=False))
    step = frame_manifest['grid_step_m']
    if any(g['grid']['dx'] != step or g['grid']['dy'] != step for g in items):
        raise ValueError('Different source cell resolution')
    lo = items[0]['grid']['origin_x']
    hi = max(i['grid']['origin_x']+(i['grid']['nx']-1)*step for i in items)
    select = (arrays['station_m'] >= lo) & (arrays['station_m'] <= hi)
    station = arrays['station_m'][select]
    ymin = min(i['grid']['origin_y'] for i in items)
    ymax = max(i['grid']['origin_y']+(i['grid']['ny']-1)*step for i in items)
    lateral = np.arange(ymin, ymax+step*.5, step)
    xy = arrays['east_north_m'][select]
    normal = arrays['normal_east_north'][select]
    triangles = LandscapeTriangles(terrain_path.parent)
    bed = sample_registered_terrain(triangles,xy,normal,lateral)
    # A wider common strip can lack dry fringe coverage at its ends. Crop only
    # exterior halo columns, and refuse any loss from the requested core run.
    complete = np.isfinite(bed).all(axis=0)
    indices = np.flatnonzero(complete)
    if not len(indices) or not complete[indices[0]:indices[-1]+1].all():
        raise ValueError('Missing interior rendered terrain')
    first, last = indices[0], indices[-1]+1
    if first:
        raise ValueError('Upstream terrain gap would invalidate the captured inlet boundary')
    source_station = arrays['source_global_station_m'][select][first:last]
    core_lo = min(r['source_core_interval_m'][0] for r in reports)
    core_hi = max(r['source_core_interval_m'][1] for r in reports)
    if source_station[0] > core_lo or source_station[-1] < core_hi:
        raise ValueError('Terrain does not cover the complete source cores')
    station,xy,normal,bed=station[first:last],xy[first:last],normal[first:last],bed[:,first:last]
    sources = load_sources([ROOT/r['construction_directory'] for r in reports],
                           [ROOT/r['source_profile'] for r in reports],bounded=True)
    padding_water=sample_registered_classification(TerrainMosaic(sources),xy,normal,lateral)
    grid = dict(nx=len(station), ny=len(lateral), dx=step, dy=step,
                origin_x=float(station[0]), origin_y=float(lateral[0]))
    state, classified, surface, covered = merge_registered(iter_join_items(items,station,step), bed, grid, padding_water,
        initial_discharge=target_q if rebuild_initial_conveyance else None)
    h, u, v = (state[key] for key in ('depth', 'u', 'v'))
    target_q = scenarios[0]['boundaries'][0]['metadata']['target_discharge_m3s']
    if not np.allclose((h*u).sum(axis=0)*step, target_q, atol=1e-8, rtol=0):
        raise ValueError('Joined initial discharge changed')
    scenario = copy.deepcopy(scenarios[0])
    scenario['grid'] = grid
    west = np.array(scenarios[0]['boundaries'][0]['ghost_cells']).reshape(2, items[0]['grid']['ny'], 4)
    # These scenarios share the same lateral lattice: embedding
    # the original west ghost in the wider strip retains its exact discharge.
    ghost = np.zeros((2, grid['ny'], 4)); ghost[:, :, 0] = bed[:, 0]
    row = int(round((items[0]['grid']['origin_y']-grid['origin_y'])/step))
    ghost[:, row:row+west.shape[1], :] = west
    scenario['boundaries'][0]['ghost_cells'] = ghost.reshape(-1, 4).tolist()
    scenario['boundaries'][1]['stage'] = float(surface[-1])
    scenario['metadata']['scenario_id'] = 'colorado_continuous_joined'
    scenario['metadata']['generator'] = Path(__file__).name
    scenario['metadata']['provenance']['joined_inputs'] = [p.relative_to(ROOT).as_posix() for p in inputs]
    if compatibility is not None:
        scenario['metadata']['provenance']['shared_hydraulic_frame']=frame_receipt
    initialization=None
    if rebuild_initial_conveyance:
        initialization=dict(policy='rebuild_uncooked_full_cross_section_conveyance_v1',
            target_discharge_m3s=target_q,source_initializations_verified=True,
            depth_stage_bed_and_classification_preserved=True,cooked_state_blending=False,
            scope='New native initial hypothesis only; fresh solve and convergence review required')
        scenario['metadata']['provenance']['initial_flow_reconstruction']=initialization
    triangles.verify_unchanged()
    if compatibility is not None:compatibility.verify_unchanged()
    for folder,report in zip(inputs,reports):
        for name,expected in report['files_sha256'].items():
            if sha(folder/name)!=expected:raise ValueError('Source input changed during join')
    if sha(original_terrain_path)!=reports[0]['continuous_terrain']['sha256']:
        raise ValueError('Original terrain dependency changed during join')
    out.mkdir(parents=True); pkg = out/'scenario'; pkg.mkdir()
    write_native_arrays(pkg, bed, h, u, v)
    for key in ('features', 'probes'):
        (pkg/(key+'.json')).write_text(json.dumps({key: []})+'\n')
    (pkg/'scenario.json').write_text(json.dumps(scenario, indent=2)+'\n')
    (out/'coordinate_map.json').write_bytes((frame_path.parent/'coordinate_map.json').read_bytes())
    np.savez_compressed(out/'reference.npz', station=station, lateral=lateral,
                        source_station=source_station, reference_surface=surface,
                        classified_water=classified)
    receipt = dict(schema='raftsim.colorado_catalog_solver_input.v1', name='Colorado continuous joined',
        grid=grid, source_core_interval_m=[core_lo, core_hi],
        source_station_range_m=[float(source_station[0]), float(source_station[-1])],
        source_inputs=[dict(path=p.relative_to(ROOT).as_posix(), sha256=sha(p/'build_report.json')) for p in inputs],
        continuous_terrain=terrain_receipt, shared_hydraulic_frame=frame_receipt,
        dry_padding_cells=int((~covered).sum()), roughness_hypothesis=scenario['roughness'],
        cropped_exterior_halo_columns=[int(first), int(len(complete)-last)],
        limitations=['One native domain, not proof of convergence, streaming, boat passage or playable acceptance.',
                     'No curvilinear metric terms added; geographic-space validation remains necessary.'],
        files_sha256={str(p.relative_to(out)): sha(p) for p in out.rglob('*') if p.is_file()},
        solved=False, playable_map_created=False, accepted=False)
    friction=scenario.get('metadata',{}).get('provenance',{}).get('friction')
    if friction is not None:
        receipt['friction']=friction
        receipt['roughness_hypothesis']=friction['inferred_manning_n']
    if initialization is not None:receipt['initial_flow_reconstruction']=initialization
    if terrain_extension is not None:receipt['source_terrain_before_additive_extension']=reports[0]['continuous_terrain']
    if compatibility is not None:
        receipt['exact_source_frame_reuse']=dict(policy='all_used_chart_arrays_and_render_coordinates_bit_identical_v1',
            inputs=compatibility.records,field_reprojection=False,cooked_state_blending=False)
    (out/'build_report.json').write_text(json.dumps(receipt, indent=2)+'\n')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, action='append', required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--terrain-extension',type=Path,
        help='Verified additive Landscape superset; every original tile and frame must be unchanged')
    parser.add_argument('--shared-frame-override',type=Path,
        help='Replacement chart; every used source coordinate, normal, curvature and source station must be bit-identical')
    parser.add_argument('--rebuild-initial-conveyance',action='store_true',
        help='Verify untouched source initial states, then initialize Q over complete joined cross-sections; never for cooked states')
    args = parser.parse_args()
    result = join(args.input, args.out.resolve(),args.rebuild_initial_conveyance,args.terrain_extension,args.shared_frame_override)
    print(json.dumps({k: v for k, v in result.items() if k != 'files_sha256'}, indent=2))
