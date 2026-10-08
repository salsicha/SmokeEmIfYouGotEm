"""Mass-preserving native restart for one bounded inferred-depth experiment.

This is a changed-geometry initial guess, never exact continuation or a solved
water field. Preserve depth, velocity and momentum; move eta with the new bed.
"""
import argparse
import copy
import json
from pathlib import Path
import shutil
import numpy as np
from continue_colorado_catalog_cook import restart_state
from continue_chilko_corridor_cook import validate_parent
from review_chilko_continuous_cook import read_inputs,validate_frame
from review_colorado_catalog_cook import load_frame
from mosaic_lidarbc_crops import sha


def depth_state(frame,old_bed,bed,grid):
    state=restart_state(frame,old_bed,grid)
    if (bed.shape!=old_bed.shape or not np.isfinite(bed).all()
            or np.any(bed>old_bed) or np.any(old_bed-bed>.80)):
        raise ValueError('Only bounded inferred-bed lowering on the identical grid is eligible')
    changed=bed!=old_bed
    if not changed.any():raise ValueError('Use exact continuation for an unchanged bed')
    state['eta'][changed]=bed[changed]+state['depth'][changed]
    return state,dict(changed_bed_cells=int(changed.sum()),maximum_cut_m=float((old_bed-bed).max()),
        added_water_volume_m3=0.,depth_velocity_momentum_and_wetness_preserved_exactly=True)


def prepare(candidate,previous,cook,review,out):
    candidate,previous,cook,review,out=map(lambda p:Path(p).resolve(),(candidate,previous,cook,review,out))
    if out.exists():raise ValueError('Fresh changed-bed restart required')
    new,sc,mapping,terrain,bed,ref,hashes=read_inputs(candidate)
    old,old_sc,old_mapping,_,old_bed,old_ref,old_hashes=read_inputs(previous)
    if sc['grid']!=old_sc['grid'] or sc['roughness']!=old_sc['roughness'] or mapping!=old_mapping:
        raise ValueError('Restart grid, geographic mapping or resistance changed')
    if set(ref)!=set(old_ref):raise ValueError('Different reference fields')
    for key in ref:np.testing.assert_array_equal(ref[key],old_ref[key])
    # Endpoint tapers must leave all boundary conditions identical, not just Q.
    if sc['boundaries']!=old_sc['boundaries']:raise ValueError('Restart boundaries changed')
    receipt=json.loads(review.read_text());review_hash=sha(review)
    native=json.loads((cook/'manifest.json').read_text());validation=json.loads((cook/'validation.json').read_text())
    relative=Path(native['frames'][-1])
    if relative.parent!=Path('frames'):raise ValueError('Invalid native frame path')
    path=cook/relative;frame_hash=sha(path)
    validate_parent(receipt,old_hashes,old_sc,native,validation,relative.name,frame_hash)
    for key in ('discharge_abs_p95_below_5percent','settling_depth_p95_below_3cm'):
        if receipt['construction_screen'].get(key) is not True:raise ValueError('Settled parent required')
    depth_path=Path(terrain.manifest['evidence_source']['available_channel_depth']['manifest'])
    calibration=json.loads(depth_path.read_text())['native_calibration']
    if calibration['review_sha256']!=review_hash or calibration['frame_sha256']!=frame_hash:
        raise ValueError('Changed-bed candidate was derived from a different native source')
    frame=load_frame(path,bed.shape);validate_frame(frame,old_bed,sc['grid'])
    state,stats=depth_state(frame,old_bed,bed,sc['grid'])
    if (any(sha(candidate/k)!=v for k,v in hashes.items())
            or any(sha(previous/k)!=v for k,v in old_hashes.items())
            or sha(review)!=review_hash or sha(path)!=frame_hash):raise ValueError('Inputs changed during restart')
    out.mkdir(parents=True)
    for name in hashes:
        if name in ('build_report.json','scenario/initial_state.npz'):continue
        target=out/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(candidate/name,target)
    np.savez_compressed(out/'scenario/initial_state.npz',**state)
    result=copy.deepcopy(new)
    result['bed_edit_warm_start']=dict(candidate_inputs=str(candidate),previous_inputs=str(previous),
        candidate_hashes=hashes,previous_hashes=old_hashes,review=str(review),review_sha256=review_hash,
        frame=str(path),frame_sha256=frame_hash,statistics=stats,
        policy='Exact old h/u/v/hu/hv/wet; eta follows changed bed. Changed-geometry initial guess, not continuation or accepted flow.',
        original_initial_diagnostics_are_not_restart_diagnostics=True,requires_fresh_native_review=True)
    (out/'build_report.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(stats,indent=2));return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('candidate','previous','cook','review','out'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();prepare(*(getattr(a,key) for key in ('candidate','previous','cook','review','out')))
