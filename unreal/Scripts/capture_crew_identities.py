"""Portraits of the five crew identities (URaftSimCrewRoster) for look review.

Run in the editor (UnrealEditor -ExecutePythonScript=unreal/Scripts/capture_crew_identities.py
-RenderOffscreen): spawns each gameplay crew host in a lit studio on the active
CC0 bodies, and renders a three-quarter face portrait, a full-body front and a
profile to Saved/RaftSimValidation/crew-identities/. Presentation review only;
it asserts nothing about fit (capture_cc0_production_roster.py does).
"""
from pathlib import Path
import traceback

import unreal

HOST_CLASS = '/Script/RaftSimRaft.RaftSimCrewAvatarActor'
IDENTITIES = (('guide', True, 0), ('kwame', False, 0), ('kenji', False, 1), ('ingrid', False, 2), ('amara', False, 3))
OUT = Path(unreal.Paths.project_saved_dir()) / 'RaftSimValidation' / 'crew-identities'


def spawn(cls, location, rotation=unreal.Rotator()):
    return unreal.EditorLevelLibrary.spawn_actor_from_class(cls, location, rotation)


def look_at(location, target):
    return unreal.MathLibrary.find_look_at_rotation(location, target)


def rect_light(location, target, intensity, width, height, color):
    light = spawn(unreal.RectLight, location, look_at(location, target))
    component = light.get_component_by_class(unreal.RectLightComponent)
    component.set_editor_property('intensity', intensity)
    component.set_editor_property('source_width', width)
    component.set_editor_property('source_height', height)
    component.set_editor_property('light_color', color)
    component.set_editor_property('attenuation_radius', 1200.0)
    return light


class Studio:
    """Lit studio plus a frame-driven capture queue.

    Captures run across editor ticks, not inside one Python call: textures
    and freshly compiled gear materials stream in over frames, and a capture
    taken on the spawn frame shows grey placeholder faces and checker helmets.
    """

    SETTLE_TICKS = 150
    VIEW_TICKS = 12

    def __init__(self):
        OUT.mkdir(parents=True, exist_ok=True)
        self.world = unreal.EditorLevelLibrary.get_editor_world()
        self.host_class = unreal.load_class(None, HOST_CLASS)
        floor = spawn(unreal.StaticMeshActor, unreal.Vector(0.0, 0.0, -1.0))
        floor.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Plane.Plane'))
        floor.set_actor_scale3d(unreal.Vector(6.0, 6.0, 6.0))
        target = unreal.Vector(0.0, 0.0, 95.0)
        rect_light(unreal.Vector(220.0, 160.0, 240.0), target, 140.0, 180.0, 180.0, unreal.Color(255, 244, 228, 255))
        rect_light(unreal.Vector(-160.0, -200.0, 170.0), target, 70.0, 220.0, 220.0, unreal.Color(200, 222, 255, 255))
        rect_light(unreal.Vector(60.0, -170.0, 220.0), target, 60.0, 120.0, 120.0, unreal.Color(190, 212, 255, 255))
        sky = spawn(unreal.SkyLight, unreal.Vector())
        sky.get_component_by_class(unreal.SkyLightComponent).set_editor_property('intensity', 0.35)
        capture = spawn(unreal.SceneCapture2D, unreal.Vector())
        self.capture = capture
        self.component = capture.capture_component2d
        self.component.set_editor_property('capture_source', unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
        self.component.set_editor_property('capture_every_frame', False)
        self.target_rt = unreal.RenderingLibrary.create_render_target2d(
            self.world, 1280, 960, unreal.TextureRenderTargetFormat.RTF_RGBA8,
            unreal.LinearColor(0.02, 0.024, 0.03, 1.0), False)
        self.component.set_editor_property('texture_target', self.target_rt)
        for command in ('r.EyeAdaptationQuality 0', 'r.ExposureOffset -0.4', 'r.Lumen.GlobalIllumination 0',
                        'r.Lumen.Reflections 0', 'r.SkeletalMeshLODBias 0', 'r.ForceLOD 0',
                        'r.Streaming.FullyLoadUsedTextures 1', 'r.Streaming.PoolSize 4000'):
            unreal.SystemLibrary.execute_console_command(self.world, command)
        self.steps = []
        for name, is_guide, variant in IDENTITIES:
            self.steps.append(lambda n=name, g=is_guide, v=variant: self.spawn_identity(n, g, v))
            self.steps.extend([self.settle] * self.SETTLE_TICKS)
            for view in ('portrait', 'front', 'profile'):
                self.steps.append(lambda view=view: self.aim(view))
                self.steps.extend([self.settle] * self.VIEW_TICKS)
                self.steps.append(lambda n=name, view=view: self.shoot(n, view))
            self.steps.append(self.destroy_identity)
        self.actor = None
        self.views = {}
        self.handle = None

    def spawn_identity(self, name, is_guide, variant):
        actor = spawn(self.host_class, unreal.Vector())
        actor.initialize_avatar_visual()
        actor.configure_appearance(variant, 1, is_guide)
        actor.activate_cc0_fallback_for_validation()
        actor.set_avatar_action(unreal.RaftSimCrewAvatarAction.SEATED_IDLE, 1.0)
        actor.get_production_helmet_head_error_cm()   # fits the headgear and accessories
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
        visual = actor.get_production_visual_actor()
        head = visual.get_solved_head_world_location()
        forward = visual.get_solved_face_forward_world_vector()
        up = visual.get_solved_face_up_world_vector()
        right = unreal.Vector.cross(up, forward)
        face = head + up * 4.0
        origin, _extent = actor.get_actor_bounds(False, False)
        self.views = {
            'portrait': (face + forward * 78.0 + right * 42.0 + up * 6.0, face, 30.0),
            'front': (unreal.Vector(origin.x, origin.y, 0.0) + forward * 330.0 + unreal.Vector(0.0, 0.0, 100.0),
                      unreal.Vector(origin.x, origin.y, 80.0), 34.0),
            'profile': (unreal.Vector(origin.x, origin.y, 0.0) + right * 330.0 + unreal.Vector(0.0, 0.0, 100.0),
                        unreal.Vector(origin.x, origin.y, 80.0), 34.0),
        }
        self.actor = actor
        self.aim('portrait')   # stream the close-up mips first

    def settle(self):
        # Keep the scene capture rendering so streaming sees the views it needs.
        self.component.capture_scene()

    def aim(self, view):
        location, look, fov = self.views[view]
        self.capture.set_actor_location(location, False, False)
        self.capture.set_actor_rotation(look_at(location, look), False)
        self.component.set_editor_property('fov_angle', fov)

    def shoot(self, name, view):
        self.component.capture_scene()
        unreal.RenderingLibrary.export_render_target(self.world, self.target_rt, str(OUT), f'{name}_{view}.png')

    def destroy_identity(self):
        self.actor.destroy_actor()
        self.actor = None

    def tick(self, _delta):
        try:
            if self.steps:
                self.steps.pop(0)()
                return
            unreal.log(f'RaftSim crew identity captures written to {OUT}')
        except Exception:
            unreal.log_error(traceback.format_exc())
        unreal.unregister_slate_post_tick_callback(self.handle)
        unreal.SystemLibrary.quit_editor()


try:
    STUDIO = Studio()
    STUDIO.handle = unreal.register_slate_post_tick_callback(STUDIO.tick)
except Exception:
    unreal.log_error(traceback.format_exc())
    unreal.SystemLibrary.quit_editor()
