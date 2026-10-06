"""Source-space approach review, not a measured navigation route or flow pass."""
import argparse
import json
from pathlib import Path
import numpy as np
from prepare_constriction_native_geometry import ROOT,BASE
from south_fork_registered_mesh import RegisteredMeshSampler
from south_fork_rock_union import sha


def route_xy(route,stations):
    points=np.asarray(route['points'],float);stations=np.asarray(stations,float)
    if (points.ndim!=2 or points.shape[1]!=5 or not np.isfinite(points).all()
            or not np.all(np.diff(points[:,0])>0) or not np.isfinite(stations).all()
            or np.any(stations<points[0,0]) or np.any(stations>points[-1,0])):
        raise ValueError('Finite increasing route and in-range stations required')
    return np.column_stack([np.interp(stations,points[:,0],points[:,i]) for i in (1,2)])+route['origin_utm_m']


def run(candidate_dir,output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    candidate_dir=candidate_dir.resolve();output=output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/'tmp'):
        raise ValueError('Fresh project tmp report required')
    candidate=json.loads((candidate_dir/'manifest.json').read_text())
    paths=dict(candidate_manifest=candidate_dir/'manifest.json',candidate=ROOT/candidate['mesh_path'],
        installed=BASE/'full_reach/source_matched_20260917/registered_mesh_source.npz',
        route=BASE/'full_reach/playable_route/coordinate_map.json',selection=ROOT/candidate['selection_path'],
        aerial=BASE/'sources/troublemaker_naip.png',aerial_export=BASE/'sources/troublemaker_naip_export.json')
    assert sha(paths['candidate'])==candidate['mesh_sha256'] and sha(paths['installed'])==candidate['parent_mesh_sha256']
    assert sha(paths['selection'])==candidate['selection_sha256']
    selection=json.loads(paths['selection'].read_text());origin=np.asarray(selection['origin_utm_and_vertical_datum_m'])
    assert sha(paths['aerial'])==selection['source_naip_sha256'] and sha(paths['aerial_export'])==selection['source_naip_export_sha256']
    route=json.loads(paths['route'].read_text());assert sha(ROOT/route['source_axis_path'])==route['source_axis_sha256']
    meshes=[]
    for key in ('installed','candidate'):
        with np.load(paths[key],allow_pickle=False) as a:meshes.append({k:a[k] for k in a.files})
    old,new=meshes;old_sampler,new_sampler=map(RegisteredMeshSampler,meshes)
    stage_mesh=dict(old,z_m=old['source_surface_m']);stage_sampler=RegisteredMeshSampler(stage_mesh)
    stations=np.arange(8300.,8370.0001,.25);xy=route_xy(route,stations)-origin[:2]
    old_z=old_sampler.sample(*xy.T);new_z=new_sampler.sample(*xy.T);stage=stage_sampler.sample(*xy.T)
    above=new_z>=stage
    report=dict(schema='raftsim.constriction_approach_source_audit.v1',
        sources={k:dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for k,p in paths.items()},
        source_stage_is_not_evolved_water=True,route_is_not_measured_navigation_line=True,
        additional_source_classification_accepted=False,route_modified=False,geometry_modified=False,
        sample_spacing_m=.25,candidate_axis_at_or_above_source_stage_count=int(above.sum()),
        rows=[dict(station_m=float(s),xy_m=p.tolist(),installed_height_m=float(a),candidate_height_m=float(b),
                   captured_source_stage_m=float(c),candidate_at_or_above_source_stage=bool(d))
              for s,p,a,b,c,d in zip(stations,xy,old_z,new_z,stage,above)],
        accepted_review_start=None,hydraulic_or_hull_clearance_verified=False,
        limits='Aerial registration uncertainty 3m and differing source dates. Heights do not classify class1 returns as rock; source stage is not current flow.')
    extent=json.loads(paths['aerial_export'].read_text())['extent']
    assert extent['spatialReference']['wkid']==32610
    fig,axes=plt.subplots(1,2,figsize=(14,6),layout='constrained')
    axes[0].imshow(plt.imread(paths['aerial']),extent=[extent['xmin']-origin[0],extent['xmax']-origin[0],extent['ymin']-origin[1],extent['ymax']-origin[1]])
    polygon=np.array(selection['interpreted_selection_polygon_m']+[selection['interpreted_selection_polygon_m'][0]])
    axes[0].plot(*polygon.T,color='magenta',label='Interpreted candidate selection')
    axes[0].plot(*xy.T,'w-',label='Existing progress axis (not navigation)')
    for station in (8300,8310,8320,8330,8340,8350,8360):
        p=xy[np.flatnonzero(stations==station)[0]]
        axes[0].plot(*p,'wo',markersize=3);axes[0].annotate(str(station),p,xytext=(3,4),textcoords='offset points',color='white',fontsize=8)
    axes[0].set(xlim=(-20,48),ylim=(-20,20),xlabel='East of source origin (m)',ylabel='North (m)',title='Unaltered 2022 aerial; 2019 source returns')
    axes[0].legend(fontsize=8,loc='lower left')
    axes[1].plot(stations,old_z,label='Installed terrain')
    axes[1].plot(stations,new_z,label='Isolated candidate terrain')
    axes[1].plot(stations,stage,'--',label='Captured flattened source stage, NOT solved water')
    axes[1].axvline(8330,color='grey',linestyle=':',label='Old review start')
    axes[1].set(xlabel='Existing progress station (m)',ylabel='Height above 220m datum (m)',title='Same source coordinates; no terrain/route adjustment')
    axes[1].legend(fontsize=8)
    fig.suptitle('Candidate approach conflict: interpretation and fresh-flow qualification still required')
    output.mkdir();fig.savefig(output/'approach.png',dpi=140);plt.close(fig)
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('sources','rows')},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.candidate,a.output)
