"""Verify fixed-state optical comparisons; never certify photorealism or turbidity."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import numpy as np


def effective_coefficients(value):
    pairs=dict(re.findall(r'([RGBA])=([-+\d.eE]+)',value))
    values=np.array([float(pairs[c]) for c in 'RGBA'])
    if not np.isfinite(values).all() or (values<0).any():
        raise ValueError('Nonfinite or negative optical coefficient')
    return values[:3]*values[3]


def verify_material(material,case):
    return bool(np.allclose(effective_coefficients(material['vectors']['Absorption']),case['absorption_per_cm'],rtol=0,atol=1e-7)
        and np.allclose(effective_coefficients(material['vectors']['Scattering']),case['scattering_per_cm'],rtol=0,atol=1e-7)
        and abs(material['scalars']['River Roughness']-case['roughness'])<1e-6
        and material['scalars']['Opacity']==0 and material['scalars']['River Foam Strength']==1)


def simulation_hash(snapshot):
    # Ignore material parameters, but not a single captured particle attribute,
    # simulation time or domain transform. All nine cases must be identical.
    state={k:v for k,v in snapshot.items() if k!='runtime_materials'}
    return hashlib.sha256(json.dumps(state,sort_keys=True).encode()).hexdigest()


def audit(path):
    capture=json.loads((path/'capture.json').read_text())
    errors=[line for line in path.with_suffix('.log').read_text(errors='replace').splitlines()
            if re.search(r'\b(?:Error|Fatal):',line)]
    records=[]
    for i,case in enumerate(capture['river_optics_cases']):
        name=f'optics_{i:02d}'
        snapshot=json.loads((path/f'{name}_particles.json').read_text())
        material=[m for m in snapshot['runtime_materials'] if 'River Roughness' in m['scalars']]
        actual=next(c for c in capture['captures'] if c['name']==name)
        control=actual['optics_control']
        records.append(dict(name=name,profile=case,simulation_hash=simulation_hash(snapshot),
            material_verified=len(material)==1 and verify_material(material[0],case),
            fixed_control_verified=control['exposure_bias']==-10 and control['simulation_frozen']
                and control['camera_fixed'] and all(control[k]==v for k,v in case.items()),
            image_hash_verified=hashlib.sha256((path/f'{name}.png').read_bytes()).hexdigest()==actual['image_sha256']))
    fixed=len({r['simulation_hash'] for r in records})==1
    result=dict(records=records,all_captured_simulation_state_identical=fixed,engine_errors=errors,
        optical_comparison_verified=bool(capture['complete'] and not capture['error'] and not errors
            and len(records)==9 and fixed and all(r['material_verified'] and r['fixed_control_verified']
                                                and r['image_hash_verified'] for r in records)),
        coefficients_measured=False,photoreal_or_physical_acceptance=False)
    output=path/'optical_controls_audit.json'
    if output.exists():raise FileExistsError(output)
    output.write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path',type=Path)
    result=audit(parser.parse_args().path)
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['optical_comparison_verified'] else 1)
