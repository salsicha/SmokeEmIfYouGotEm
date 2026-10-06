"""Check the prepared boil scene itself; run Blender with its feature.blend open."""
import json
import math
from pathlib import Path
import sys

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_water_feature_boil import piston_top


def main():
    setup = json.loads((Path(bpy.data.filepath).parent/'setup.json').read_text())
    assert setup['case'] == 'boil'
    assert np.allclose(setup['dimensions_m'], (3., 3., 2.9))
    values = [piston_top(i) for i in range(1, setup['frames']+1)]
    assert min(values) == .1 and abs(max(values)-.34) < 1e-12
    assert np.all(np.diff(values) >= 0)
    assert abs(piston_top(31)-.22) < 1e-12
    assert abs(setup['piston_displaced_volume_m3']-math.pi*.35**2*.24) < 1e-12
    assert setup['piston_top_initial_m']+setup['piston_stroke_m'] < setup['initial_depth_m']
    domain = bpy.data.objects['Feature liquid']
    assert domain.animation_data is None
    assert all(getattr(domain.modifiers[0].domain_settings, 'use_collision_border_'+side)
               for side in ('front', 'back', 'left', 'right', 'bottom'))
    behaviors = [m.flow_settings.flow_behavior for obj in bpy.data.objects for m in obj.modifiers
                 if m.type == 'FLUID' and m.fluid_type == 'FLOW']
    assert behaviors == ['GEOMETRY'], behaviors
    for frame in (1, 25, 31, 37, 53):
        bpy.context.scene.frame_set(frame)
        piston = bpy.data.objects['Submerged displacement piston'].evaluated_get(bpy.context.evaluated_depsgraph_get())
        corners = [piston.matrix_world @ Vector(p) for p in piston.bound_box]
        assert abs(max(p.z for p in corners)-piston_top(frame)) < 1e-6
        assert min(p.z for p in corners) < 0  # no opened cavity underneath
    initial = bpy.data.objects['Initially still pool']
    bvh = BVHTree.FromPolygons([initial.matrix_world @ v.co for v in initial.data.vertices],
                              [list(p.vertices) for p in initial.data.polygons])
    # Exiting liquid in +z has an upward normal; entering liquid above a dry
    # piston footprint has a downward normal. Do not seed the collider.
    for x, y in ((1.5, 0.), (1.6, 0.), (1.4, .1), (1.5, -.1)):
        hit, normal, _, _ = bvh.ray_cast(Vector((x, y, .05)), Vector((0., 0., 1.)))
        assert hit is not None and normal.z < -.9, (x, y, hit, normal)
    for x, y in ((2., 0.), (1., 0.), (1.5, .6)):
        hit, normal, _, _ = bvh.ray_cast(Vector((x, y, .3)), Vector((0., 0., 1.)))
        assert hit is not None and normal.z > .9, (x, y, hit, normal)
    print('BOIL_SETUP_TESTS_PASS: stroke, closed boundaries, no continuous flow, initial solid exclusion, unanimated liquid', flush=True)


if __name__ == '__main__':
    main()
