"""Exercise the native verifier contract without installing or loading a map."""
import importlib.util,math,sys,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


class FoliageActor:
    def __init__(self,component):self.component=component
    def get_editor_property(self,name):return True
    def get_components_by_class(self,cls):return [self.component]
    def get_package(self):return SimpleNamespace(get_name=lambda:'/Game/__ExternalActors__/fixture')


class Component:
    def __init__(self,rows):
        self.rows=rows;self.collision=0;self.cull=65000
        self.static_mesh=SimpleNamespace(get_path_name=lambda:'mesh0')
    def get_collision_enabled(self):return self.collision
    def get_editor_property(self,name):return 45000 if name=='instance_start_cull_distance' else self.cull
    def get_num_materials(self):return 1
    def get_material(self,i):return SimpleNamespace(get_path_name=lambda:'material')
    def get_instance_count(self):return len(self.rows)
    def get_instance_transform(self,i,world):
        row=self.rows[i];angle=math.radians(row['yaw_deg'])/2
        return SimpleNamespace(translation=SimpleNamespace(**dict(zip('xyz',row['location_cm']))),
            scale3d=SimpleNamespace(**dict(zip('xyz',row['scale_xyz']))),
            rotation=SimpleNamespace(x=0.,y=0.,z=math.sin(angle),w=math.cos(angle)))


class SavedCanopyTests(unittest.TestCase):
    def setUp(self):
        native=SimpleNamespace(InstancedFoliageActor=FoliageActor,InstancedStaticMeshComponent=Component,
            CollisionEnabled=SimpleNamespace(NO_COLLISION=0))
        spec=importlib.util.spec_from_file_location('canopy_verifier_under_test',Path(__file__).with_name('install_futaleufu_continuous_canopy.py'))
        self.module=importlib.util.module_from_spec(spec)
        # Successful import also proves the installer no longer runs on import.
        with patch.dict(sys.modules,unreal=native):spec.loader.exec_module(self.module)
        self.row=dict(mesh=0,location_cm=[-25200.123,30201.3,2314.1],scale_xyz=[1.2,1.2,1.4],yaw_deg=359.9999)
        self.plan=dict(meshes=[dict(asset='mesh'+str(i),materials=['material']) for i in range(3)],
            chunks=[dict(instances=[self.row])],instances_per_mesh=[1,0,0])

    def verify(self,rows):return self.module.verify([FoliageActor(Component(rows))],self.plan)[0]

    def test_wrapped_yaw_and_small_serialization_roundoff_pass_original_limits(self):
        row=dict(self.row,location_cm=[-25200.1231,30201.3001,2314.1],yaw_deg=-.0001)
        self.assertEqual(self.verify([row])['verified_instances'],1)

    def test_missing_and_duplicate_instances_fail(self):
        for rows in ([],[self.row,self.row]):
            with self.assertRaises(RuntimeError):self.verify(rows)

    def test_position_scale_yaw_and_nonfinite_changes_fail(self):
        for row in (dict(self.row,location_cm=[-25202.,30201.3,2314.1]),
                    dict(self.row,scale_xyz=[1.21,1.2,1.4]),dict(self.row,yaw_deg=359.98),
                    dict(self.row,scale_xyz=[float('nan'),1.2,1.4]),
                    dict(self.row,scale_xyz=[1.2,float('nan'),1.4]),
                    dict(self.row,scale_xyz=[1.2,1.2,float('inf')])):
            with self.assertRaises(RuntimeError):self.verify([row])

    def test_collision_and_culling_regressions_fail(self):
        for field,value in [('collision',1),('cull',0)]:
            component=Component([self.row]);setattr(component,field,value)
            with self.assertRaises(RuntimeError):self.module.verify([FoliageActor(component)],self.plan)


if __name__=='__main__':unittest.main()
