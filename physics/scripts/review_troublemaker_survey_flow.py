"""Measure the staged solve; a solver 'passed' flag is not hydraulic acceptance."""
from pathlib import Path
import sys
import json
import argparse

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tmp/south-fork-geospatial-deps'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--cell',default='1')
    parser.add_argument('--mixed-inlet',action='store_true')
    parser.add_argument('--label',default='')
    args=parser.parse_args()
    work=ROOT/f'tmp/south-fork-survey-hydraulics/{args.cell}m'
    suffix='-mixed-inlet' if args.mixed_inlet else ''
    if args.label: suffix+='-'+args.label
    if suffix: work=work.with_name(work.name+suffix)
    run=json.loads((work/'run_result.json').read_text())
    folder=ROOT/run['output_dir']
    manifest=json.loads((folder/'manifest.json').read_text())
    scenario=json.loads(next((work/'scenario').glob('*/scenario.json')).read_text())
    registration=json.loads((work/'registration.json').read_text())
    nx,ny=scenario['grid']['nx'],scenario['grid']['ny']; cell=float(args.cell)
    target=registration['target_discharge_m3s']
    snapshots=[]
    steps=int(run['command'][run['command'].index('--steps')+1])
    interval=int(run['command'][run['command'].index('--frame-interval')+1])
    for index,name in enumerate(manifest['frames']):
        data=np.genfromtxt(folder/name,delimiter=',',names=True)
        h=data['h'].reshape(ny,nx); eta=data['eta'].reshape(ny,nx)
        u=data['u'].reshape(ny,nx); v=data['v'].reshape(ny,nx)
        x=data['x'].reshape(ny,nx); y=data['y'].reshape(ny,nx)
        columns=[int(np.argmin(abs(x[0]-p))) for p in (-125,-50,0,25,75,125)]
        region=(abs(x)<25)&(abs(y)<30)&(h>.1)
        snapshots.append({'seconds':min(index*interval,steps)*scenario['fixed_dt'],
            'volume_m3':float(h.sum()*cell*cell),
            'section_discharge_m3s':[float((h[:,c]*u[:,c]).sum()*cell) for c in columns],
            'crux_stage_median_navd88_m':float(np.median(eta[region])+registration['vertical_origin_navd88_m']),
            'crux_supercritical_area_m2':float(np.sum(region&(data['froude'].reshape(ny,nx)>1))*cell*cell),
            'crux_upstream_velocity_area_m2':float(np.sum(region&(u<-.2))*cell*cell)})
    tail=snapshots[-4:]
    storage=[(b['volume_m3']-a['volume_m3'])/(b['seconds']-a['seconds']) for a,b in zip(tail[:-1],tail[1:])]
    qerror=max(abs(q-target)/target for f in tail for q in f['section_discharge_m3s'])
    checks={'section_flux_within_5_percent_of_target':qerror<=.05,
        'storage_within_2_percent_of_target':max(map(abs,storage))<=.02*target,
        'regional_stage_change_below_1cm':np.ptp([f['crux_stage_median_navd88_m'] for f in tail])<=.01}
    report={'status':'numerical_review_not_visual_acceptance','target_discharge_m3s':target,
        'geometry_sha256':registration['geometry_sha256'],'snapshots':snapshots,
        'source_bed_sampling':registration.get('bed_sampling','bilinear'),
        'last_intervals_storage_m3s':storage,'maximum_tail_section_relative_error':qerror,
        'checks':{k:bool(v) for k,v in checks.items()},'mean_flow_screen_passed':bool(all(checks.values())),
        'actual_numerical_boundary_flux_audited':False,
        'measured_bathymetry':False,'rapid_geometry_and_animation_accepted':False,'production_promoted':False}
    output=ROOT/'docs/reconstruction-review-2026-09-06'
    (output/f'troublemaker_survey_flow_{args.cell}m{suffix}.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    fig,axes=plt.subplots(1,3,figsize=(16,5),layout='constrained')
    wet=h>.03
    for ax,field,title,cmap in zip(axes,[eta+220,np.hypot(u,v),data['froude'].reshape(ny,nx)],
            ['Water elevation NAVD88 (m)','Current speed (m/s)','Froude number'],['viridis','turbo','magma']):
        artist=ax.imshow(np.where(wet,field,np.nan),origin='lower',extent=[x.min(),x.max(),y.min(),y.max()],cmap=cmap)
        ax.set_title(title); ax.set_xlabel('Rigid downstream coordinate (m)'); ax.set_ylabel('Rigid left coordinate (m)')
        fig.colorbar(artist,ax=ax,shrink=.7)
    fig.savefig(output/f'troublemaker_survey_flow_{args.cell}m{suffix}.png',dpi=150)
    print(json.dumps({k:v for k,v in report.items() if k!='snapshots'},indent=2),flush=True)


if __name__=='__main__':main()
