"""Exact authored-solid subtraction from a native liquid render mesh.

This is surface extraction, not a solver mass correction. Never writes caches.
"""
import bpy
from water_feature_triangulation import triangulate_extraction

EDDY_SOLIDS = ('Flume floor', 'Obstacle approach bed', 'Bank spur', 'Far wall')


def clipped_surface(evaluated_liquid, solids, union_solids=False, contact_materials=False,
                    triangulated=False, constrained=False):
    mesh = bpy.data.meshes.new_from_object(evaluated_liquid)
    obj = bpy.data.objects.new('Collider-consistent liquid surface diagnostic', mesh)
    bpy.context.collection.objects.link(obj)
    obj.matrix_world = evaluated_liquid.matrix_world.copy()
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    united = None
    try:
        if union_solids:
            if not solids:
                raise ValueError('Shared solids required')
            first = solids[0].evaluated_get(bpy.context.evaluated_depsgraph_get())
            united = bpy.data.objects.new('Shared collider union diagnostic',
                                         bpy.data.meshes.new_from_object(first))
            bpy.context.collection.objects.link(united)
            united.matrix_world = first.matrix_world.copy()
            bpy.context.view_layer.objects.active = united
            united.select_set(True)
            for solid in solids[1:]:
                boolean = united.modifiers.new('Union shared collider '+solid.name, 'BOOLEAN')
                boolean.operation = 'UNION'
                boolean.solver = 'EXACT'
                boolean.object = solid
                if contact_materials:
                    boolean.material_mode = 'TRANSFER'
                bpy.ops.object.modifier_apply(modifier=boolean.name)
            solids = [united]
            bpy.context.view_layer.objects.active = obj
        for solid in solids:
            boolean = obj.modifiers.new('Subtract shared collider '+solid.name, 'BOOLEAN')
            boolean.operation = 'DIFFERENCE'
            boolean.solver = 'EXACT'
            boolean.object = solid
            if contact_materials:
                boolean.material_mode = 'TRANSFER'
            bpy.ops.object.modifier_apply(modifier=boolean.name)
        if len(obj.data.vertices) < 4 or not obj.data.polygons:
            raise ValueError('Empty collider-consistent liquid mesh')
        if triangulated:
            import json
            obj['extraction_triangulation'] = json.dumps(triangulate_extraction(obj, constrained))
        return obj
    except BaseException:
        remove_surface(obj)
        raise
    finally:
        if united is not None:
            remove_surface(united)


def remove_surface(obj):
    mesh = obj.data
    bpy.data.objects.remove(obj, do_unlink=True)
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)
