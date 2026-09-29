"""Prepared-scene invariants, not acceptance of the ensuing liquid motion."""
import json
from pathlib import Path
import bpy
from mathutils import Vector

setup = json.loads((Path(bpy.data.filepath).parent/'setup.json').read_text())
assert setup['case'] == 'froth'
scene = bpy.context.scene
domain = bpy.data.objects['Feature liquid']
s = domain.modifiers[0].domain_settings
assert all(abs(a-b) < 1e-6 for a, b in zip(domain.dimensions, (2., 1.6, 2.9)))
assert s.use_collision_border_bottom and s.use_collision_border_front and s.use_collision_border_back
assert s.use_collision_border_left and s.use_collision_border_right and not s.use_collision_border_top
assert s.use_foam_particles and s.use_spray_particles and s.use_bubble_particles
assert s.use_fractions == setup['fractional_obstacles']
assert abs(s.particle_radius-setup.get('liquid_particle_radius_cells', 1.)) < 1e-6
assert abs(s.mesh_particle_radius-2.) < 1e-6  # Separate mesh-skin radius unchanged.
assert not domain.animation_data
assert 2*setup['emitter_radius_m']/setup['approximate_cell_m'] >= 8
source = bpy.data.objects['Finite downward jet source']
f = source.modifiers[0].flow_settings
assert f.flow_behavior == 'INFLOW' and f.flow_type == 'LIQUID'
assert abs(f.velocity_coord.z+1.8) < 1e-6
for frame, expected in ((1, True), (36, True), (72, True), (73, False), (96, False), (120, False)):
    scene.frame_set(frame)
    assert f.use_inflow == expected, (frame, f.use_inflow)
flows = [m.flow_settings for o in bpy.data.objects for m in o.modifiers if m.type == 'FLUID' and m.fluid_type == 'FLOW']
assert len(flows) == 2 and all(f.flow_behavior != 'OUTFLOW' for f in flows)
tube = bpy.data.objects['Hollow inlet nozzle']
assert tube.modifiers[0].fluid_type == 'EFFECTOR'
assert not tube.hide_render and len(tube.data.polygons) == 256
assert all(p.area > 0 for p in tube.data.polygons)
pool = bpy.data.objects['Initially still pool']
assert max((pool.matrix_world @ Vector(v)).z for v in pool.bound_box) < 1.42
scene.frame_set(1)
print('FROTH_SCENE_TESTS_PASSED: closed pool, finite inlet, shared nozzle, separate phases, no water animation', flush=True)
