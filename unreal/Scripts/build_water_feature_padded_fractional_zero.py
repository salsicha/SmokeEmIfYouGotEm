"""Matched native fractional control with ZERO artificial particle clearance.

Zero is the authored point-contact boundary, not a fitted radius/volume value.
All native particle/mesh radii and physical geometry remain unchanged.
"""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys
import bpy

sys.path.insert(0,str(Path(__file__).resolve().parent))
from prepare_modular_water_feature import settings_snapshot


def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():raise FileExistsError(args.output)
    builder=Path(__file__).with_name('build_water_feature_padded_fractional.py')
    sys.argv=[str(builder),'--','--reference',str(args.reference.resolve()),'--output',str(args.output.resolve())]
    runpy.run_path(str(builder),run_name='__main__')
    root=args.output.resolve();domain=bpy.data.objects['Feature liquid'];state=domain.modifiers[0].domain_settings
    before=settings_snapshot(state)
    if not state.use_fractions or state.fractions_distance!=.5 or state.has_cache_baked_data:
        raise ValueError('Fresh default fractional preparation required')
    if any(p.is_file() for p in (root/'cache').rglob('*')):raise ValueError('Empty native cache required')
    state.fractions_distance=0
    after=settings_snapshot(state);changes={k:[before[k],v] for k,v in after.items() if v!=before[k]}
    if changes!={'fractions_distance':[.5,0.]}:raise ValueError('Unexpected native setting change: '+str(changes))
    setup=json.loads((root/'setup.json').read_text());setup['boundary_control']=__doc__
    setup['fractional_clearance_cells']=0.;setup['fractional_clearance_fitted']=False
    (root/'setup.json').write_text(json.dumps(setup,indent=2));(root/'domain-settings.json').write_text(json.dumps(after,indent=2))
    proof=json.loads((root/'padding-preflight.json').read_text())
    proof['dependency_sha256'][str(Path(__file__).resolve())]=digest(Path(__file__))
    proof.update(zero_artificial_clearance_control=True,zero_only_setting_change=changes,
        effective_fraction_parameters={k:v for k,v in after.items() if 'frac' in k},scope=__doc__)
    proof['domain_setting_differences'].update(changes)
    (root/'padding-preflight.json').write_text(json.dumps(proof,indent=2))
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(root/'feature.blend'))
    print('PADDED_FRACTIONAL_ZERO_PREPARED',changes,flush=True)


if __name__=='__main__':main()
