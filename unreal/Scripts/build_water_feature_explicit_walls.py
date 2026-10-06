"""Fresh eddy with explicit intended1.6m viewing walls and padded outer cage.

Changes physical boundary representation; not an unchanged old effective flume.
Never changes preserved cache RNA before redirecting to a fresh empty cache.
"""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys
import bpy
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from prepare_modular_water_feature import settings_snapshot
from build_water_feature_lab import solid
from build_water_feature_padded_eddy import boundaries


def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('reference','kernel-preflight','output'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--fractional',action='store_true')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():raise FileExistsError(args.output)
    kernel=json.loads(args.kernel_preflight.read_text())
    if not kernel['complete'] or not kernel['passed'] or kernel['accepted']:raise ValueError('Passed unaccepted native analytic preflight required')
    if any(digest(p)!=sha for p,sha in kernel['dependency_sha256'].items()):raise ValueError('Kernel evidence changed')
    builder=Path(__file__).with_name('build_water_feature_padded_eddy.py')
    sys.argv=[str(builder),'--','--reference',str(args.reference.resolve()),'--output',str(args.output.resolve())]
    runpy.run_path(str(builder),run_name='__main__')
    root=args.output.resolve();domain=bpy.data.objects['Feature liquid'];state=domain.modifiers[0].domain_settings
    if state.has_cache_baked_data or any(p.is_file() for p in (root/'cache').rglob('*')):raise ValueError('Fresh empty cache required')
    old=boundaries();before=settings_snapshot(state);old_center=np.array(domain.location)
    domain.dimensions=(6.75,2.325,3.15);bpy.context.view_layer.objects.active=domain
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    state.resolution_max=90;state.use_fractions=args.fractional;state.fractions_distance=0
    mat=bpy.data.materials['Warm neutral stone']
    added=(('Explicit front viewing wall',(-.5,-1.3,-.5),(6.5,-.8,2.85)),
        ('Explicit upstream end wall',(-.5,-1.3,-.5),(0,1.3,2.85)),
        ('Explicit downstream end wall',(6,-1.3,-.5),(6.5,1.3,2.85)),
        ('Outer back wall fill',(-.5,.9,-.5),(6.5,1.3,2.85)))
    for name,lo,hi in added:
        obj=solid(name,lo,hi,mat);obj.hide_render=True
    # Cutaway viewing walls are physically active and disclosed, not a hidden
    # bank obstacle or a post-solve surface clip. Existing solids remain visible.
    if {k:v for k,v in boundaries().items() if k in old}!=old:raise ValueError('Existing source/collider changed')
    after=settings_snapshot(state);changes={k:[before[k],v] for k,v in after.items() if before[k]!=v}
    allowed={'resolution_max':[80,90],'fractions_distance':[.5,0.]}
    if args.fractional:allowed['use_fractions']=[False,True]
    if changes!=allowed:raise ValueError('Unexpected physical settings: '+str(changes))
    shape=(90,31,42);h=.075;origin=np.asarray(domain.location)-np.array(shape)*h/2
    old_origin=old_center-np.array((80,21,42))*h/2
    if not np.allclose(origin+np.array((5,5,0))*h,old_origin,atol=2e-7,rtol=0):raise ValueError('Original world knots moved')
    setup=json.loads((root/'setup.json').read_text());setup.update(dimensions_m=list(domain.dimensions),resolution=90,
        fractional_obstacles=args.fractional,fractional_clearance_cells=0,explicit_physical_walls=True,
        boundaries='Explicit physical x0..6,y-0.8..0.8; old far wall retained; invisible cutaway viewing/end walls plus outer back fill. Top open. Original inlet/level drain.',
        physical_boundaries_unchanged=False,old_authoring_preserved=True,physical_accuracy_accepted=False,
        grid_alignment=dict(lower_m=origin.tolist(),allocated_shape=list(shape),cell_m=h,side_padding_cells=5,bottom_padding_cells=3),
        boundary_control=__doc__)
    (root/'setup.json').write_text(json.dumps(setup,indent=2));(root/'domain-settings.json').write_text(json.dumps(after,indent=2))
    proof=json.loads((root/'padding-preflight.json').read_text());proof['dependency_sha256'][str(Path(__file__).resolve())]=digest(__file__)
    proof['dependency_sha256'][str(args.kernel_preflight.resolve())]=digest(args.kernel_preflight)
    proof.update(explicit_wall_control=True,old_authoring_preserved=True,physical_boundaries_unchanged=False,
        shape=list(shape),cell_m=h,origin_m=origin.tolist(),dimensions_m=list(domain.dimensions),
        domain_setting_differences=changes,all_physical_boundaries=boundaries(),
        explicit_inner_planes_m=dict(x=[0,6],y=[-.8,.8],bed=0),scope=__doc__)
    (root/'padding-preflight.json').write_text(json.dumps(proof,indent=2))
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(root/'feature.blend'))
    print('EXPLICIT_WALL_SCENE_PREPARED',args.fractional,shape,origin.tolist(),changes,flush=True)


if __name__=='__main__':main()
