"""Stage the two catalogued Lower Pinball obstacles without changing live assets.

The catalogue documents two rocks, not surveyed dimensions. The first install
uses inferred footprints and water-relative crests; revisions preserve the
absolute datum except for explicitly authored absolute elevations below.
The same surfaces are applied to both solver bed and Landscape height data. A shallow
right-side bypass shelf is explicitly authored gameplay geometry, not a third
observed rock or surveyed bathymetry. A compact
flat crown preserves the crest on the 2 m hydraulic grid. No flow is invented:
the staged scenario must be recooked and validated before installation.
"""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
RIVER = ROOT / 'physics/data/real_world/pacuare_river_costa_rica'
PACKAGE = RIVER / 'scenario_huacas_evidence_2017'
TERRAIN = RIVER / 'terrain/huacas_evidence_2017'
CATALOG = RIVER / 'observed_rapids/huacas_observed_rapids.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rock_height(station, lateral, feature, base, crest):
    """One compact elliptical closed mound, in physical metres, no wet mask."""
    r = np.hypot((station-feature['station_m'])/(feature['length_m']*.5),
                 (lateral-feature['lateral_m'])/(feature['width_m']*.5))
    crown_fraction = float(feature.get('flat_crown_fraction', .4))
    if not 0. < crown_fraction < 1.:
        raise ValueError('Flat crown fraction must be inside (0, 1)')
    t = np.clip((r-crown_fraction)/(1.-crown_fraction),0.,1.)
    weight = 1.-t*t*(3.-2.*t)
    return np.where(r<1.,base+(crest-base)*weight,-np.inf)


def stage(out, revise=False):
    if out.exists():
        raise ValueError('Fresh candidate directory required')
    cm=json.loads((PACKAGE/'cooked_flow_fields/manifest.json').read_text())
    previous=cm.get('pinball_reference')
    if previous and not revise:
        raise ValueError('Pinball patch already installed; do not raise its crowns again')
    band=cm['bands'][0]['band_id']; grid=cm['grid']
    source=PACKAGE/'cooked_flow_fields'/band
    arrays={k:np.load(source/(k+'.npy')).astype(float) for k in ('bed','h','u','v')}
    bed=arrays['bed']; eta=bed+arrays['h']; new=bed.copy()
    s=grid['origin_x_m']+np.arange(grid['nx'])*grid['dx_m']
    l=grid['origin_y_m']+np.arange(grid['ny'])*grid['dy_m']
    ss,ll=np.meshgrid(s,l)
    features=[f for f in json.loads(CATALOG.read_text())['features'] if f['id'].startswith('lower_pinball_rock_')]
    assert len(features)==2
    # Closing the measured seam raises local stage by about 0.1 m. The old
    # inferred second crown then submerged by 0.047 m in candidate v5. Keep
    # this observed exposed obstacle exposed with an explicit absolute datum;
    # do not repeatedly add height relative to each candidate's backwater.
    for feature in features:
        if feature['id']=='lower_pinball_rock_2':
            feature['authored_absolute_crest_m']=155.90
    features.append(dict(id='lower_pinball_authored_bypass_shelf',type='bed_shelf',
        station_m=2052.,lateral_m=-26.,width_m=42.,length_m=24.,crest_below_ws_m=-.5,
        flat_crown_fraction=.8,
        authored_absolute_crest_m=155.19,
        evidence='Authored gameplay calibration of inferred underwater geometry; not surveyed.',
        purpose='Bank-attached bar with a continuous shallow crown to rock 2. Native hands-off evidence found a 0.72 m-deep seam at lateral -16.6. Candidate v5 closed its shape but raised local stage, so this explicitly authored absolute crown preserves shallow depth without a cumulative water-relative height increase.'))
    records=[]
    for f in features:
        near=(abs(ss-f['station_m'])<=4)&(abs(ll-f['lateral_m'])<=4)&(arrays['h']>.05)
        prior=next((r for r in previous['rocks'] if r['feature']['id']==f['id']),None) if previous else None
        if prior:
            old=prior['feature']
            if any(f[k]!=old[k] for k in ('station_m','lateral_m')) or any(f[k]<old[k] for k in ('width_m','length_m')):
                raise ValueError('Revision may only expand an installed footprint; relocation or shrinkage requires the preserved pre-patch bed and terrain')
        # A footprint revision keeps the original absolute crown, not a new
        # increment above its own upstream backwater. Never stack rock heights.
        crest=prior['crest_m'] if prior else float(np.median(eta[near]))-f['crest_below_ws_m']
        # Absolute revisions are explicitly authored gameplay dimensions,
        # never automatic re-raising from a candidate's own backwater.
        if 'authored_absolute_crest_m' in f:
            target=float(f['authored_absolute_crest_m'])
            if prior and target<prior['crest_m']:
                raise ValueError('Lowering an installed crown requires the preserved pre-patch source')
            crest=target
        base=prior['base_m'] if prior else float(np.min(bed[near]))
        new=np.maximum(new,rock_height(ss,ll,f,base,crest))
        records.append(dict(feature=f,base_m=base,crest_m=crest,
                            crown_reference_surface_m=crest+f['crest_below_ws_m'],
                            reference_note='Crown-relative authoring datum, not a post-cook measured water surface.'))
    assert np.isfinite(new).all() and np.all(new>=bed)
    out.mkdir(parents=True)
    shutil.copytree(PACKAGE/'scenario',out/'scenario')
    np.save(out/'scenario/bed.npy',new)
    h=np.maximum(eta-new,0.); wet=h>1.e-6
    u=np.where(wet,arrays['u'],0.); v=np.where(wet,arrays['v'],0.)
    np.savez(out/'scenario/initial_state.npz',depth=h,eta=new+h,u=u,v=v,hu=h*u,hv=h*v,wet=wet)
    sc=json.loads((out/'scenario/scenario.json').read_text())
    sc.setdefault('metadata',{})['scenario_id']='pacuare_lower_pinball_reference_candidate'
    sc['metadata']['pinball_reference']={'catalogue_sha256':sha(CATALOG),'inferred':True}
    (out/'scenario/scenario.json').write_text(json.dumps(sc,indent=2)+'\n')

    # Apply the same crown to the actual heightfield, with the existing ENU
    # centreline and north-up raster contract. Do not alter colour or banks.
    tm=json.loads((TERRAIN/'huacas_evidence_terrain_manifest.json').read_text())
    land=tm['landscape']; hfpath=ROOT/tm['outputs']['heightfield']
    hf=np.array(Image.open(hfpath)); n=hf.shape[0]
    terrain=land['terrain_min_m']+hf.astype(float)/65535*(land['terrain_max_m']-land['terrain_min_m'])
    points=np.array(json.loads((TERRAIN/'huacas_evidence_runtime_coordinate_map.json').read_text())['points'])
    for rec in records:
        f=rec['feature']; st=f['station_m']
        xy=np.array([np.interp(st,points[:,0],points[:,i]) for i in (1,2)])
        before=np.array([np.interp(st-1,points[:,0],points[:,i]) for i in (1,2)])
        after=np.array([np.interp(st+1,points[:,0],points[:,i]) for i in (1,2)])
        tangent=(after-before)/np.linalg.norm(after-before); left=np.array([-tangent[1],tangent[0]])
        center=xy+left*f['lateral_m']
        sx=land['horizontal_span_x_m']/(n-1); sy=land['horizontal_span_y_m']/(n-1)
        cx=center[0]/sx; cy=(land['horizontal_span_y_m']*.5-center[1])/sy
        radius=max(f['width_m'],f['length_m'])*.5
        rx=int(np.ceil(radius/sx))+2;ry=int(np.ceil(radius/sy))+2
        c0=max(0,int(cx-rx));c1=min(n,int(cx+rx+1));r0=max(0,int(cy-ry));r1=min(n,int(cy+ry+1))
        rr,cc=np.mgrid[r0:r1,c0:c1]
        x=cc*sx-xy[0]; y=land['horizontal_span_y_m']*.5-rr*sy-xy[1]
        local_s=st+x*tangent[0]+y*tangent[1]; local_l=x*left[0]+y*left[1]
        terrain[r0:r1,c0:c1]=np.maximum(terrain[r0:r1,c0:c1],rock_height(local_s,local_l,f,rec['base_m'],rec['crest_m']))
    raw=np.rint((terrain-land['terrain_min_m'])/(land['terrain_max_m']-land['terrain_min_m'])*65535)
    assert np.all((raw>=0)&(raw<=65535))
    Image.fromarray(raw.astype(np.uint16)).save(out/'huacas_evidence_heightfield_2017.png')
    report=dict(schema='raftsim.pinball_reference_candidate.v1',status='candidate_not_installed',
                catalogue=str(CATALOG.relative_to(ROOT)),catalogue_sha256=sha(CATALOG),
                cooked_manifest_sha256=sha(PACKAGE/'cooked_flow_fields/manifest.json'),
                source_heightfield_sha256=sha(hfpath),scenario_bed_sha256=sha(out/'scenario/bed.npy'),
                candidate_heightfield_sha256=sha(out/'huacas_evidence_heightfield_2017.png'),
                changed_solver_cells=int(np.count_nonzero(new>bed+.001)),
                newly_dry_cells=int(np.count_nonzero((arrays['h']>.05)&~wet)),rocks=records,
                acceptance_required=['recook finite stable water and discharge','same rocks rendered and colliding',
                                     'native linked versus first-only route','normal launch','packaged 20 FPS'])
    (out/'candidate.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


def continue_candidate(candidate, run, out):
    """Continue the same bed/constant boundaries; retain the spin-up failure."""
    from export_hance_evidence_runtime import read_frame
    if out.exists():raise ValueError('Fresh continuation directory required')
    sc=json.loads((candidate/'scenario/scenario.json').read_text())
    if any(b.get('hydrograph') for b in sc['boundaries']):
        raise ValueError('Clock-reset continuation requires constant boundaries')
    receipt=json.loads((candidate/'candidate.json').read_text())
    if sha(candidate/'scenario/bed.npy')!=receipt['scenario_bed_sha256']:
        raise ValueError('Candidate bed changed')
    validation=json.loads((run/'validation.json').read_text())
    if not validation['finite_state'] or validation['velocity_limit_reached']:
        raise ValueError('Cannot continue an invalid state')
    rm=json.loads((run/'manifest.json').read_text())
    if rm['scenario_id']!=sc['metadata']['scenario_id'] or not rm['disable_fixture_calibrations']:
        raise ValueError('Wrong run or fixture forcing')
    frame=run/rm['frames'][-1];g=sc['grid'];f=read_frame(frame,g['ny'],g['nx'])
    bed=np.load(candidate/'scenario/bed.npy')
    if not all(np.isfinite(f[k]).all() for k in ('h','eta','hu','hv')) or np.any(f['h']<0):
        raise ValueError('Nonfinite or negative continuation state')
    if not (np.allclose(f['eta']-f['h'],bed,rtol=0,atol=1e-5) and
        np.allclose(f['x'],g['origin_x']+np.arange(g['nx'])*g['dx'],rtol=0,atol=1e-6) and
        np.allclose(f['y'],(g['origin_y']+np.arange(g['ny'])*g['dy'])[:,None],rtol=0,atol=1e-6)):
        raise ValueError('Continuation frame does not match bed/grid')
    shutil.copytree(candidate,out)
    np.savez(out/'scenario/initial_state.npz',depth=f['h'],eta=f['eta'],u=f['u'],v=f['v'],
             hu=f['hu'],hv=f['hv'],wet=f['h']>1e-6)
    receipt['continuation']=dict(source_frame=str(frame),source_frame_sha256=sha(frame),
        source_validation=validation,source_scenario_sha256=sha(candidate/'scenario/scenario.json'),
        method='Unchanged bed, grid and constant forcing; conserved-state restart after initial backwater adjustment. Export thresholds unchanged.')
    for rock in receipt['rocks']:
        if 'source_water_surface_m' in rock:
            rock['crown_reference_surface_m']=rock.pop('source_water_surface_m')
        rock['reference_note']='Crown-relative authoring datum, not a post-cook measured water surface.'
    (out/'candidate.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--revise',action='store_true',help='Explicit footprint expansion; preserve the installed absolute crowns')
    parser.add_argument('--continue-from',type=Path,help='Finite run to continue with unchanged constant forcing')
    parser.add_argument('--candidate',type=Path,help='Original candidate for continuation')
    args=parser.parse_args()
    if bool(args.continue_from)!=bool(args.candidate):parser.error('Continuation requires both --candidate and --continue-from')
    if args.continue_from and args.revise:parser.error('Continuation cannot revise geometry')
    result=continue_candidate(args.candidate,args.continue_from,args.out) if args.continue_from else stage(args.out,args.revise)
    print(json.dumps(result,indent=2))
