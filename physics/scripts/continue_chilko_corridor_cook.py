"""Continue a reviewed finite Chilko state without claiming a passed river cook.

An unsettled construction review can continue, but its exact source, native
settings and final frame must still match. Nothing is remapped or retuned.
"""
import argparse
import copy
import json
import shutil
from pathlib import Path

import numpy as np

from build_colorado_catalog_evidence import sha
from continue_colorado_catalog_cook import restart_state
from review_chilko_continuous_cook import read_inputs, validate_native, validate_frame
from review_colorado_catalog_cook import load_frame


def validate_parent(receipt, hashes, scenario, native, validation, frame_name, frame_hash):
    validate_native(native, validation, scenario)
    if (receipt.get('schema') != 'raftsim.chilko_continuous_cook_review.v1' or
            receipt.get('name') != scenario['metadata']['scenario_id'] or
            receipt.get('input_files_sha256') != hashes or
            receipt.get('native_manifest') != native or receipt.get('native_validation') != validation or
            receipt.get('comparison_frames', [])[-1:] != [frame_name] or
            receipt.get('frame_sha256', {}).get(frame_name) != frame_hash):
        raise ValueError('Changed or unrelated reviewed continuation source')
    allowed = {'edge', 'kind', 'ghost_cells', 'metadata', 'stage'}
    if (scenario.get('cascading') or scenario.get('feature_count') != 0 or
            any(set(b)-allowed or b['kind'] not in ('discharge_profile','outflow','bank','wall')
                for b in scenario['boundaries'])):
        raise ValueError('Continuation requires unforced constant boundaries')


def prepare(inputs, cook, review, out):
    if out.exists(): raise ValueError('Fresh Chilko continuation directory required')
    parent_hashes={str(p):sha(p) for p in (review,cook/'manifest.json',cook/'validation.json')}
    build, scenario, mapping, terrain, bed, ref, hashes = read_inputs(inputs)
    receipt = json.loads(review.read_text())
    native = json.loads((cook/'manifest.json').read_text())
    validation = json.loads((cook/'validation.json').read_text())
    relative = Path(native['frames'][-1])
    if relative.parent != Path('frames') or relative.suffix != '.csv':
        raise ValueError('Invalid native final frame path')
    frame_path = cook/relative; frame_hash = sha(frame_path)
    validate_parent(receipt, hashes, scenario, native, validation, relative.name, frame_hash)
    frame = load_frame(frame_path, bed.shape)
    validate_frame(frame, bed, scenario['grid'])
    state = restart_state(frame, bed, scenario['grid'])
    out.mkdir(parents=True)
    for name in hashes:
        if name in ('build_report.json', 'scenario/initial_state.npz'): continue
        target = out/name; target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(inputs/name, target)
    np.savez_compressed(out/'scenario/initial_state.npz', **state)
    result = copy.deepcopy(build)
    result['native_continuation'] = dict(source_inputs=str(inputs), source_review=str(review),
        source_review_sha256=parent_hashes[str(review)], source_inputs_sha256=hashes,
        frame=str(frame_path), frame_sha256=frame_hash,
        native_manifest_sha256=parent_hashes[str(cook/'manifest.json')],
        validation_sha256=parent_hashes[str(cook/'validation.json')],
        previous=build.get('native_continuation'),
        policy='Exact saved native state; unchanged geography, bed, friction and constant boundaries; native clock restarts at zero.',
        original_initial_diagnostics_are_not_restart_diagnostics=True,
        construction_screen_passed=receipt['construction_screen_passed'])
    if (any(sha(inputs/name)!=digest for name,digest in hashes.items()) or
            sha(frame_path)!=frame_hash or any(sha(Path(p))!=digest for p,digest in parent_hashes.items())):
        raise ValueError('Continuation source changed during preparation')
    (out/'build_report.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    return result['native_continuation']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('inputs','cook','review','out'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();r=prepare(*(getattr(a,k).resolve() for k in ('inputs','cook','review','out')))
    print(json.dumps({k:v for k,v in r.items() if k not in ('source_inputs_sha256','previous')},indent=2))
