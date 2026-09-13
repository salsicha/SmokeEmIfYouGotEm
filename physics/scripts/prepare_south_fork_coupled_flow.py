"""Prepare the full captured river for a conservative coupled flow cook.

Terrain is copied exactly in its declared vertical datum. Initial velocity is
an explicitly inferred station-binned conveyance seed, not settled/observed
flow. One upstream Q is partitioned over both actual exterior inlet edges.
"""
import copy
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach'
OUT=ROOT/'tmp/south-fork-coupled-flow-input-v2-20260912'
Q=45.3069545472
BIN=10.
LOWER=-1000.


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    from scipy.spatial import cKDTree
    from scipy.ndimage import gaussian_filter1d
    assert not OUT.exists(), 'Preserve prior flow preparations'
    geometry_path=BASE/'coupled_geometry/manifest.json'
    geometry=json.loads(geometry_path.read_text())
    audit=json.loads((geometry_path.parent/'source_exact_audit.json').read_text())
    assert audit['passed'] and audit['manifest_sha256']==sha(geometry_path)
    assert geometry['remaining_interior_wet_exterior_faces']==0
    route=json.loads((BASE/'playable_route/coordinate_map.json').read_text())
    points=np.asarray(route['points'])
    origin=np.asarray(route['origin_utm_m'])
    datum=float(geometry['vertical_datum_navd88_m'])
    tree=cKDTree(points[:,1:3])
    tangent=np.column_stack((points[:,4],-points[:,3]))
    assert np.allclose(np.linalg.norm(tangent,axis=1),1.,atol=1.e-8)
    centers=np.asarray([r['center_utm_m'] for r in geometry['regions']])
    offsets=np.arange(80)-40
    xx,yy=np.meshgrid(offsets,offsets)
    bins=int(np.ceil((points[-1,0]+2000)/BIN))
    conveyance=np.zeros(bins)
    cells=[]
    for record,center in zip(geometry['regions'],centers):
        path=ROOT/record['geometry_file']
        assert sha(path)==record['geometry_sha256']
        with np.load(path,allow_pickle=False) as arrays:
            source_bed=arrays['bed_navd88_m']
            source_surface=arrays['captured_surface_navd88_m']
            water=arrays['captured_water_mask'].astype(bool)
        bed=source_bed-datum
        surface=source_surface-datum
        depth=np.where(water,np.maximum(surface-bed,0.),0.)
        xy=np.column_stack(((center[0]+xx-origin[0]).ravel(),(center[1]+yy-origin[1]).ravel()))
        _,nearest=tree.query(xy)
        station=points[nearest,0].copy()
        # Extend only the initialization coordinate beyond each endpoint; this
        # never alters the captured geometry or the gameplay route/chainage.
        for endpoint in (0,len(points)-1):
            mask=nearest==endpoint
            station[mask]+=np.sum((xy[mask]-points[endpoint,1:3])*tangent[endpoint],axis=1)
        indices=np.floor((station-LOWER)/BIN).astype(int)
        assert indices.min()>=0 and indices.max()<bins
        conveyance+=np.bincount(indices,weights=depth.ravel()**(5./3.),minlength=bins)/BIN
        cells.append(dict(bed=bed,surface=surface,depth=depth,nearest=nearest,bin_indices=indices))
    # Only a smooth warm-start estimate; the actual FV solver must establish
    # momentum balance and discharge through the unchanged bed and roughness.
    smoothed=gaussian_filter1d(conveyance,1.,mode='nearest')
    for cell in cells:
        k=smoothed[cell['bin_indices']].reshape(80,80)
        magnitude=np.divide(Q*cell['depth']**(2./3.),k,out=np.zeros_like(k),where=k>1.e-9)
        direction=tangent[cell['nearest']].reshape(80,80,2)
        cell['u']=magnitude*direction[:,:,0]
        cell['v']=magnitude*direction[:,:,1]
        assert np.isfinite(magnitude).all() and magnitude.max()<=20., 'Initial inferred current exceeds velocity gate'
    index_by_name={r['name']:i for i,r in enumerate(geometry['regions'])}
    slices=dict(west=(slice(None),0),east=(slice(None),-1),south=(0,slice(None)),north=(-1,slice(None)))
    upstream=[]
    downstream_stages=[]
    for edge in geometry['open_geometry_edges']:
        i=index_by_name[edge['region']]
        index=slices[edge['edge']]
        if edge['endpoint']=='upstream':
            x_edge=edge['edge'] in ('west','east')
            sign=1. if edge['edge'] in ('west','south') else -1.
            projection=sign*tangent[0,0 if x_edge else 1]
            assert projection>0., 'Initial upstream direction does not enter an exterior face'
            h=cells[i]['depth'][index]
            upstream.append(dict(i=i,edge=edge['edge'],index=index,h=h,
                weight=h**(5./3.)*projection))
        else:
            h=cells[i]['depth'][index]
            downstream_stages.extend(cells[i]['surface'][index][h>1.e-6].tolist())
    weight=sum(item['weight'].sum() for item in upstream)
    assert weight>0. and len(upstream)==2 and downstream_stages
    outlet_stage=float(np.median(downstream_stages))
    profiles={}
    imposed_total=0.
    for item in upstream:
        h=item['h']
        magnitude=Q*h**(2./3.)/weight
        u=magnitude*tangent[0,0]; v=magnitude*tangent[0,1]
        bed=cells[item['i']]['bed'][item['index']]
        profile=np.column_stack((bed,h,u,v))
        assert np.isfinite(profile).all()
        profiles[item['i'],item['edge']]=np.tile(profile,(2,1)).tolist()
        imposed_total+=float(Q*item['weight'].sum()/weight)
    assert abs(imposed_total-Q)<1.e-12
    OUT.mkdir()
    template=json.loads((ROOT/'physics/data/validation/milestone17/analytic_fixtures/fixtures/lake_at_rest_balance/scenario/scenario.json').read_text())
    manifest=dict(schema='raftsim.cartesian_flow_cook.v1',dt_seconds=.05,packages=[],boundary_probes=[],
        geometry_manifest=geometry_path.relative_to(ROOT).as_posix(),geometry_manifest_sha256=sha(geometry_path),
        target_discharge_m3s=Q,authored_combined_inlet_discharge_m3s=imposed_total,
        inferred_outlet_stage_relative_datum_m=outlet_stage,vertical_datum_navd88_m=datum,
        initial_velocity_method='10 m station-bin depth^(5/3) conveyance, 10 m Gaussian warm start; nearest source-route tangent',
        measured_velocity=False,measured_bathymetry=False,settled_hydraulics=False,normal_map_integrated=False,
        inputs=[],maximum_initial_depth_m=max(float(c['depth'].max()) for c in cells),
        maximum_initial_speed_mps=max(float(np.hypot(c['u'],c['v']).max()) for c in cells))
    physical={(index_by_name[e['region']],e['edge']):e['endpoint'] for e in geometry['open_geometry_edges']}
    for i,(record,cell) in enumerate(zip(geometry['regions'],cells)):
        package=OUT/record['name']; package.mkdir()
        np.save(package/'bed.npy',cell['bed'])
        h,u,v=cell['depth'],cell['u'],cell['v']
        np.savez_compressed(package/'initial_state.npz',depth=h,eta=cell['bed']+h,u=u,v=v,hu=h*u,hv=h*v,wet=h>1.e-6)
        (package/'features.json').write_text('{"features":[]}\n')
        (package/'probes.json').write_text('{"probes":[]}\n')
        scenario=copy.deepcopy(template)
        scenario['metadata']=dict(scenario_id=record['name'],scenario_type='real_world',fixture_kind=None,
            river_id='south_fork_american',flow_band='median_runnable',
            generator='prepare_south_fork_coupled_flow.py',generator_version='20260912-v2',
            description='Source-exact full-river core with explicitly inferred warm-start flow; not accepted',confidence_score=.3,
            coordinate_reference_system='Unrotated EPSG:32610 east/north metres relative to declared world origin; NAVD88 minus datum',
            provenance=dict(source_geometry_file=record['geometry_file'],source_geometry_sha256=record['geometry_sha256'],
                original_source_geometry_file=record['source_geometry_file'],
                original_source_geometry_sha256=record['source_geometry_sha256'],
                terrain_geometry_modified=False,submerged_bed_is_uncalibrated_inference=True,
                initial_velocity_is_inferred=True,target_discharge_m3s=Q,normal_map_integrated=False))
        scenario['grid']=dict(nx=80,ny=80,dx=1.,dy=1.,origin_x=record['grid_origin_local_m'][0],origin_y=record['grid_origin_local_m'][1])
        scenario.update(fixed_dt=.05,duration=600.,roughness=.035,feature_count=0,probe_count=0)
        scenario['boundaries']=[]
        for edge in ('west','east','south','north'):
            boundary=dict(edge=edge,kind='bank')
            role=physical.get((i,edge))
            if role=='upstream':
                boundary.update(kind='discharge_profile',ghost_cells=profiles[i,edge])
            elif role=='downstream':
                boundary.update(kind='outflow',stage=outlet_stage)
            if role:
                manifest['boundary_probes'].append(dict(tile_index=i,edge=edge,role=role))
            scenario['boundaries'].append(boundary)
        (package/'scenario.json').write_text(json.dumps(scenario,indent=2)+'\n')
        manifest['packages'].append(record['name'])
        manifest['inputs'].append(dict(name=record['name'],source_geometry_sha256=record['geometry_sha256'],
            files={name:sha(package/name) for name in ('scenario.json','bed.npy','initial_state.npz','features.json','probes.json')}))
        if (i+1)%100==0:
            print(f'Prepared {i+1}/{len(cells)} coupled flow packages',flush=True)
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({k:v for k,v in manifest.items() if k not in ('inputs','packages')},indent=2),flush=True)


if __name__=='__main__':
    main()
