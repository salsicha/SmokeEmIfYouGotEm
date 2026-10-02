"""Native fractional-cell control AFTER repaired bottom padding, not acceptance.

Same physical scene and FLIP; no collider inflation or custom particle motion.
The old fractional boulder control did not have this repaired bottom domain.
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
    builder=Path(__file__).with_name('build_water_feature_padded_eddy.py')
    sys.argv=[str(builder),'--','--reference',str(args.reference.resolve()),'--output',str(args.output.resolve())]
    runpy.run_path(str(builder),run_name='__main__')
    root=args.output.resolve();domain=bpy.data.objects['Feature liquid'];state=domain.modifiers[0].domain_settings
    before=settings_snapshot(state)
    if state.use_fractions or state.simulation_method!='FLIP' or state.has_cache_baked_data:
        raise ValueError('Fresh standard padded FLIP preparation required')
    if any(p.is_file() for p in (root/'cache').rglob('*')):raise ValueError('Fresh empty cache required')
    state.use_fractions=True
    after=settings_snapshot(state);changed={k:[before[k],v] for k,v in after.items() if v!=before[k]}
    if changed!={'use_fractions':[False,True]}:raise ValueError('Unexpected coupled physical-setting change: '+str(changed))
    setup=json.loads((root/'setup.json').read_text());setup.update(fractional_obstacles=True,
        boundary_control='Three cells below unchanged bed, plus native fractional-cell boundary control. Not accepted.',
        physical_accuracy_accepted=False,visual_accuracy_accepted=False,game_integrated=False)
    (root/'setup.json').write_text(json.dumps(setup,indent=2));(root/'domain-settings.json').write_text(json.dumps(after,indent=2))
    proof=json.loads((root/'padding-preflight.json').read_text())
    proof['dependency_sha256'][str(Path(__file__).resolve())]=digest(Path(__file__))
    proof.update(native_fractional_control=True,fractional_only_setting_change=changed,
        default_fraction_parameters={k:v for k,v in after.items() if 'frac' in k},scope=__doc__)
    proof['domain_setting_differences'].update(changed)
    (root/'padding-preflight.json').write_text(json.dumps(proof,indent=2))
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(root/'feature.blend'))
    print('PADDED_FRACTIONAL_PREPARED',changed,proof['default_fraction_parameters'],flush=True)


if __name__=='__main__':main()
