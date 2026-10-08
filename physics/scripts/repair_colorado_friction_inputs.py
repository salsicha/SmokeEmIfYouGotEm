"""Create a fresh continuous input with explicit Manning/native-drag units.

Legacy packet is retained. Only scenario friction and provenance change; the
initial water state, geometry, sources and constant boundaries remain exact.
This is a new candidate, not an accepted cook or an exact native continuation.
"""
import argparse
import copy
import json
import shutil
from pathlib import Path

from build_colorado_catalog_evidence import ROOT, sha
from build_colorado_catalog_scenario import checked_roughness
from chilko_native_friction import with_manning_friction


def corrected_scenario(scenario, report):
    if not report.get('continuous_terrain') or not report.get('shared_hydraulic_frame'):
        raise ValueError('Only new shared-frame continuous Colorado inputs are eligible')
    if scenario.get('metadata',{}).get('river_id')!='colorado_river_grand_canyon_rowing':
        raise ValueError('Different river')
    if 'friction' in scenario.get('metadata',{}).get('provenance',{}):
        raise ValueError('Already has an explicit friction contract; do not convert twice')
    n=checked_roughness(report['roughness_hypothesis'])
    if scenario['roughness']!=n:
        raise ValueError('Ambiguous legacy resistance; no inferred conversion')
    return with_manning_friction(scenario,n)


def prepare(inputs, out):
    inputs,out=Path(inputs).resolve(),Path(out).resolve()
    inputs.relative_to(ROOT);out.relative_to(ROOT)
    if out.exists():raise ValueError('Fresh repaired-input directory required')
    report_path=inputs/'build_report.json'
    report_hash=sha(report_path)
    report=json.loads(report_path.read_text())
    paths={}
    for name,expected in report['files_sha256'].items():
        path=(inputs/name).resolve();path.relative_to(inputs)
        if sha(path)!=expected:raise ValueError('Changed source input')
        paths[name]=path
    scenario=json.loads((inputs/'scenario/scenario.json').read_text())
    candidate=corrected_scenario(scenario,report)
    out.mkdir(parents=True)
    for name,path in paths.items():
        target=out/name;target.parent.mkdir(parents=True,exist_ok=True)
        if name.replace('\\','/')=='scenario/scenario.json':
            target.write_text(json.dumps(candidate,indent=2,allow_nan=False)+'\n')
        else:
            shutil.copyfile(path,target)
            if sha(target)!=report['files_sha256'][name]:raise ValueError('Non-friction field changed')
    result=copy.deepcopy(report)
    result['friction']=candidate['metadata']['provenance']['friction']
    result['friction_unit_repair']=dict(source_inputs=inputs.relative_to(ROOT).as_posix(),
        source_report_sha256=report_hash,previous_native_coefficient=scenario['roughness'],
        current_native_coefficient=candidate['roughness'],
        state_and_geometry_byte_identical=True,
        scope='Physical-unit repair only; fresh native cook and unchanged acceptance gates required')
    result['roughness_scope']='Inferred Manning n; native scenario coefficient g*n*n; not measured resistance'
    result.update(solved=False,playable_map_created=False,accepted=False)
    result['files_sha256']={name:sha(out/name) for name in paths}
    if sha(report_path)!=report_hash or any(sha(path)!=report['files_sha256'][name] for name,path in paths.items()):
        raise ValueError('Source changed during repair')
    (out/'build_report.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    return result['friction_unit_repair']


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(prepare(args.inputs,args.out),indent=2))
