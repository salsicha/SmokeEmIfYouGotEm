"""Render an existing liquid bake without modifying its .blend or cache.

Opaque diagnostic shading exposes geometry, not an approved water material.
Secondary particles are not rendered by this inspection script.
"""
import argparse
import json
from pathlib import Path
import sys
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def material(name, color, roughness):
    result = bpy.data.materials.new(name)
    result.use_nodes = True
    shader = result.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*color, 1.)
    shader.inputs['Roughness'].default_value = roughness
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--frames', type=int, nargs='+', default=[48, 96, 144])
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    args.output.mkdir(parents=True, exist_ok=False)
    scene = bpy.context.scene
    domain = bpy.data.objects['Liquid review domain']
    bed = bpy.data.objects['Exact source bed']
    domain.data.materials.clear()
    domain.data.materials.append(material('Opaque liquid shape review', (.018,.17,.12), .3))
    bed.data.materials.clear()
    bed.data.materials.append(material('Diagnostic bed', (.18,.13,.085), .85))
    for polygon in domain.data.polygons:
        polygon.use_smooth = True
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 24
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 960
    scene.render.resolution_y = 600
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.world = bpy.data.worlds.new('Neutral diagnostic world')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.25,.3,.4,1.)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value = .4
    bpy.ops.object.light_add(type='AREA', location=(4.,-3.,12.))
    lamp = bpy.context.object
    lamp.data.energy = 1800
    lamp.data.shape = 'DISK'
    lamp.data.size = 5.
    lamp.rotation_euler = (Vector((6.,4.,1.))-lamp.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.camera_add(location=(-5.,-7.,8.))
    camera = bpy.context.object
    camera.rotation_euler = (Vector((5.7,4.,1.2))-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = 18.
    scene.camera = camera
    results = []
    for frame in args.frames:
        if not scene.frame_start <= frame <= scene.frame_end:
            raise ValueError('Requested frame outside bake')
        scene.frame_set(frame)
        evaluated = domain.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = evaluated.to_mesh()
        try:
            vertices = [evaluated.matrix_world @ v.co for v in mesh.vertices]
            if len(vertices) <= 8:
                raise RuntimeError('Liquid cache did not evaluate to a surface')
            bounds = [[min(v[i] for v in vertices), max(v[i] for v in vertices)] for i in range(3)]
            tree = BVHTree.FromPolygons(vertices, [list(p.vertices) for p in mesh.polygons])
            profiles = []
            # Top-surface rays exclude the closed underside from the height
            # evidence: whole-mesh thickness is not a breaking-wave height.
            for fraction in (.25,.5,.75):
                y = bounds[1][0]+fraction*(bounds[1][1]-bounds[1][0])
                samples = []
                x = bounds[0][0]+.5
                while x < bounds[0][1]-.5:
                    position, normal, index, distance = tree.ray_cast(
                        Vector((x,y,bounds[2][1]+1.)), Vector((0.,0.,-1.)))
                    samples.append(dict(x=x, surface_z=None if position is None else position.z))
                    x += .5
                profiles.append(dict(y=y,samples=samples))
            result = dict(frame=frame, seconds=(frame-1)/scene.render.fps,
                vertices=len(vertices), polygons=len(mesh.polygons),
                bounds=bounds, top_surface_profiles=profiles,
                particles=[dict(name=p.name, count=len(p.particles)) for p in evaluated.particle_systems])
        finally:
            evaluated.to_mesh_clear()
        scene.render.filepath = str((args.output/f'liquid_{frame:04d}.png').resolve())
        bpy.ops.render.render(write_still=True)
        result['image'] = scene.render.filepath
        results.append(result)
        print('LIQUID_REVIEW_FRAME', json.dumps({k:v for k,v in result.items() if k != 'top_surface_profiles'}), flush=True)
    (args.output/'inspection.json').write_text(json.dumps(dict(
        source_blend=bpy.data.filepath, diagnostic_shading=True, secondary_particles_rendered=False,
        game_integrated=False, photorealism_accepted=False, frames=results), indent=2))


if __name__ == '__main__':
    main()
