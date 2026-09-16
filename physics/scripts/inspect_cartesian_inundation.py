"""Bind zero-step numerical tile-face fluxes to source-mask inundation history.

This diagnoses a candidate; source water masks are not current-flow shoreline
measurements, and instantaneous flux is not a time-integrated mass budget.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import numpy as np

ROOT=Path(__file__).resolve().parents[2]


def require(value,message):
    if not value:raise ValueError(message)


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def inundation(bed,surface,source_water,initial_depth,depth,selected,area):
    bed,surface,initial_depth,depth=map(lambda a:np.asarray(a,dtype=float),(bed,surface,initial_depth,depth))
    source_water=np.asarray(source_water);selected=np.asarray(selected,dtype=bool)
    require(all(a.shape==bed.shape for a in (surface,source_water,initial_depth,depth,selected)), 'Mismatched cell arrays')
    require(all(np.isfinite(a).all() for a in (bed,surface,initial_depth,depth)), 'Nonfinite cell arrays')
    require(np.all(initial_depth>=0) and np.all(depth>=0), 'Negative depth')
    require(np.all((source_water==0)|(source_water==1)), 'Nonbinary source water mask')
    require(np.isfinite(area) and area>0 and selected.any(), 'Positive area and nonempty footprint required')
    wet=selected & (depth>1.e-6)
    new_wet=wet & (initial_depth==0)
    outside=wet & (source_water==0)
    common=wet & (source_water!=0) & (initial_depth>1.e-6)
    stage_error=bed[common]+depth[common]-surface[common]
    return dict(cells=int(selected.sum()),area_m2=float(selected.sum()*area),
        volume_m3=float(depth[selected].sum()*area),wet_area_m2=float(wet.sum()*area),
        initially_zero_depth_now_wet_area_m2=float(new_wet.sum()*area),
        initially_zero_depth_now_wet_volume_m3=float(depth[new_wet].sum()*area),
        outside_source_water_mask_wet_area_m2=float(outside.sum()*area),
        outside_source_water_mask_wet_volume_m3=float(depth[outside].sum()*area),
        maximum_outside_source_water_mask_depth_m=float(depth[outside].max()) if outside.any() else 0.,
        common_source_water_wet_cells=int(common.sum()),
        common_source_water_stage_minus_captured_p10_p50_p90_m=np.percentile(stage_error,[10,50,90]).tolist() if len(stage_error) else [])


def internal_flux_error(rows,grids):
    values={r['tile_index']:r['inward_flux_m3s'] for r in rows};errors=[]
    require(len(values)==len(rows), 'Repeated flux tile')
    require(all(len(f)==4 and np.isfinite(f).all() for f in values.values()), 'Invalid native flux')
    for i,gi in grids.items():
        for j,gj in grids.items():
            if i>=j:continue
            require((gi['nx'],gi['ny'],gi['dx'],gi['dy'])==(gj['nx'],gj['ny'],gj['dx'],gj['dy']), 'Different tile dimensions')
            x=(gj['origin_x']-gi['origin_x'])/(gi['nx']*gi['dx'])
            y=(gj['origin_y']-gi['origin_y'])/(gi['ny']*gi['dy'])
            for dx,dy,a,b in ((1,0,1,0),(-1,0,0,1),(0,1,3,2),(0,-1,2,3)):
                if abs(x-dx)<1.e-8 and abs(y-dy)<1.e-8:errors.append(abs(values[i][a]+values[j][b]))
    return max(errors,default=0.)


def inspect(cook,steps,packages,solver,center,radius):
    cook=Path(cook).resolve();solver=Path(solver).resolve();dependencies={}
    def checked(path,expected=None):
        path=Path(path).resolve();digest=sha(path)
        require(expected is None or digest==expected,'Changed dependency: '+str(path))
        dependencies[str(path)]=digest
        return path
    manifest_path=Path((cook/'input_manifest_path.txt').read_text().strip())
    if not manifest_path.is_absolute():manifest_path=ROOT/manifest_path
    checked(manifest_path);checked(cook/'input_manifest.json',sha(manifest_path))
    manifest=json.loads(manifest_path.read_text())
    require(bool(steps) and all(type(s) is int and s>=0 for s in steps) and len(steps)==len(set(steps)) and steps==sorted(steps),'Distinct increasing nonnegative steps required')
    require(len(packages)==len(set(packages)) and bool(packages),'Distinct nonempty packages required')
    require(np.asarray(center).shape==(2,) and np.isfinite(center).all() and np.isfinite(radius) and radius>0,'Finite center and positive radius required')
    indices=[manifest['packages'].index(name) for name in packages]
    require(len(manifest['packages'])==len(set(manifest['packages'])),'Repeated manifest package')
    require([row['name'] for row in manifest['inputs']]==manifest['packages'],'Incomplete or reordered input identities')
    for row in manifest['inputs']:
        require(set(row['files'])=={'scenario.json','bed.npy','initial_state.npz','features.json','probes.json'},'Incomplete package identities')
        for name,digest in row['files'].items():checked(manifest_path.parent/row['name']/name,digest)
    geometry_path=checked(ROOT/manifest['geometry_manifest'],manifest['geometry_manifest_sha256'])
    geometry=json.loads(geometry_path.read_text());geometry_rows={r['name']:r for r in geometry['regions']}
    require(geometry['vertical_datum_navd88_m']==manifest['vertical_datum_navd88_m'],'Input/source vertical datum mismatch')
    grids={};beds=[];surfaces=[];water=[];initial=[];local=[];area=None;ny=None;nx=None
    h0=np.load(checked(cook/'frame_000000/h.npy'),mmap_mode='r',allow_pickle=False)
    for index,name in zip(indices,packages):
        base=manifest_path.parent/name;scenario=json.loads((base/'scenario.json').read_text());g=scenario['grid'];grids[index]=g
        require(scenario['array_files']==dict(bed='bed.npy',initial_state='initial_state.npz',features='features.json',probes='probes.json'),'Scenario array identities differ from checked inputs')
        require((g['ny'],g['nx'])==tuple(geometry['core_shape']) and g['dx']==g['dy']==geometry['grid_spacing_m'],'Input/source grid dimensions or spacing mismatch')
        if area is None:ny,nx=g['ny'],g['nx'];area=g['dx']*g['dy']
        require((ny,nx,area)==(g['ny'],g['nx'],g['dx']*g['dy']), 'Different selected grids')
        require(h0.shape==(len(manifest['packages'])*ny,nx),'Invalid initial stacked dimensions')
        r=geometry_rows[name]
        require([g['origin_x'],g['origin_y']]==r['grid_origin_local_m'],'Input/source grid origin mismatch')
        with np.load(checked(ROOT/r['geometry_file'],r['geometry_sha256']),allow_pickle=False) as a:
            bed=np.load(base/'bed.npy',allow_pickle=False)
            require(np.array_equal(bed,a['bed_navd88_m']-manifest['vertical_datum_navd88_m']),'Input/source bed mismatch')
            beds.append(bed);surfaces.append(a['captured_surface_navd88_m'].astype(float)-manifest['vertical_datum_navd88_m'])
            water.append(a['captured_water_mask'].copy())
        initial_depth=h0[index*ny:(index+1)*ny].copy()
        with np.load(base/'initial_state.npz',allow_pickle=False) as state:
            require(np.array_equal(initial_depth,state['depth']),'Frame-zero/input depth mismatch')
        initial.append(initial_depth)
        xx,yy=np.meshgrid(g['origin_x']+np.arange(nx)*g['dx'],g['origin_y']+np.arange(ny)*g['dy'])
        local.append((xx-center[0])**2+(yy-center[1])**2<=radius**2)
    beds,surfaces,water,initial,local=map(np.asarray,(beds,surfaces,water,initial,local))
    checked(solver);history=[]
    for step in steps:
        frame=cook/f'frame_{step:06d}';record=json.loads(checked(frame/'complete.json').read_text())
        require(record['snapshot'] and record['step']==step,'Completed matching frame required')
        before={k:sha(checked(frame/f'{k}.npy')) for k in ('h','u','v')}
        command=[str(solver),str(manifest_path.resolve()),str(frame),*map(str,indices)]
        native=json.loads(subprocess.run(command,capture_output=True,text=True,check=True).stdout)
        require(native['state_unchanged'] and native['solver_steps_run']==0 and native['time_seconds']==record['time_seconds'],'Native inspection changed state/time')
        require([r['tile_index'] for r in native['tiles']]==sorted(indices),'Native selection mismatch')
        for k,digest in before.items():checked(frame/f'{k}.npy',digest)
        error=internal_flux_error(native['tiles'],grids)
        require(error<1.e-9,'Internal paired faces do not cancel')
        full=np.load(frame/'h.npy',mmap_mode='r',allow_pickle=False)
        require(full.shape==h0.shape,'Invalid checkpoint dimensions')
        depth=np.array([full[i*ny:(i+1)*ny] for i in indices])
        metrics=inundation(beds,surfaces,water,initial,depth,np.ones_like(local),area)
        require(abs(metrics['volume_m3']-native['selected_volume_m3'])<1.e-6,'Native/array regional volume mismatch')
        history.append(dict(step=step,time_seconds=record['time_seconds'],native=native,
            internal_face_cancellation_error_m3s=error,whole_selected_tiles=metrics,
            local_circle=inundation(beds,surfaces,water,initial,depth,local,area)))
    for previous,current in zip(history,history[1:]):
        dt=current['time_seconds']-previous['time_seconds'];require(dt>0,'Non-increasing source age')
        current['interval_selected_volume_rate_m3s']=(current['native']['selected_volume_m3']-previous['native']['selected_volume_m3'])/dt
    return dict(schema='raftsim.cartesian_inundation_inspection.v1',packages=packages,
        local_center_field_m=center,local_radius_m=radius,history=history,dependencies=dependencies,
        scope='Native fluxes enclose all selected tiles; local-circle metrics cover selected cells inside the circle and have NO corresponding flux measurement. Source water mask and captured stage are historical source observations, not a current-flow shoreline calibration. Instantaneous net inflow is not a time-integrated budget or a cause identified by itself.',
        settling_accepted=False,visual_accepted=False,normal_map_integrated=False)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('cook',type=Path)
    p.add_argument('--steps',type=int,nargs='+',required=True);p.add_argument('--packages',nargs='+',required=True)
    p.add_argument('--solver',type=Path,required=True);p.add_argument('--center',type=float,nargs=2,required=True)
    p.add_argument('--radius',type=float,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    output=a.report.resolve();require(output.is_relative_to(ROOT/'tmp') and not output.exists(),'Fresh project tmp report required')
    result=inspect(a.cook,a.steps,a.packages,a.solver,a.center,a.radius)
    with output.open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False)
    print(json.dumps({k:v for k,v in result.items() if k!='dependencies'},indent=2))
