"""Declared modeled daylight, not a measured river lighting calibration."""
import math
import bpy


def daylight_study(scene):
    hidden = []
    for name in ('Key', 'Rim'):
        lamp = bpy.data.objects[name]
        if lamp.type != 'LIGHT' or lamp.data.type != 'AREA':
            raise ValueError('Expected the authored studio area lamps')
        lamp.hide_render = True
        hidden.append(name)
    world = bpy.data.worlds.new('Declared modeled daylight study')
    world.use_nodes = True
    sky = world.node_tree.nodes.new('ShaderNodeTexSky')
    sky.sky_type = 'MULTIPLE_SCATTERING'
    sky.sun_disc = True
    sky.sun_elevation = math.radians(35.)
    sky.sun_rotation = math.radians(60.)
    # Retain inspected installed-build defaults for atmospheric densities,
    # angular sun size and intensity. No desired-image parameter fitting.
    background = world.node_tree.nodes['Background']
    background.inputs['Strength'].default_value = 1.
    world.node_tree.links.new(sky.outputs['Color'], background.inputs['Color'])
    scene.world = world
    fields = ('sun_disc', 'sun_size', 'sun_intensity', 'sun_elevation', 'sun_rotation',
              'altitude', 'air_density', 'aerosol_density', 'ozone_density')
    return dict(model=sky.sky_type, parameters={key: getattr(sky, key) for key in fields},
                world_strength=1., hidden_studio_lights=hidden,
                exposure=scene.view_settings.exposure, view_transform=scene.view_settings.view_transform,
                measured_lighting=False,
                scope='Declared clear-sky study orientation; not dated site lighting or measured exposure. Water material and cached motion unchanged.')
