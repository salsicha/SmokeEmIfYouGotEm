import importlib.util
from pathlib import Path
import math
import unittest

PATH=Path(__file__).resolve().parents[2]/'unreal/Scripts/south_fork_liquid_frame.py'
SPEC=importlib.util.spec_from_file_location('liquid_review_frame',PATH)
FRAME=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FRAME)


class LiquidFrameTests(unittest.TestCase):
    def test_geographic_frame_reflects_restored_parent_coordinates(self):
        for yaw in [0,90,158.43478935409635,-45]:
            with self.subTest(yaw=yaw):
                manifest=dict(local_to_engine_yaw_degrees=yaw,local_origin_engine_cm=[0,0,350])
                offset=[-10.035118225791255,1.815599679002005]
                geometry=dict(coordinate_rebase_only=True,parent_frame_offset_east_north_m=offset)
                old=FRAME.review_frame(manifest,geometry)
                reflected=FRAME.review_frame(manifest,geometry,True)
                for p in [(0,0,0),(1,0,0),(0,1,0),(-10,8,2.5)]:
                    x,y,z=FRAME.world_point_cm(old,p)
                    expected=(x+100*offset[0],-(y+100*offset[1]),z)
                    actual=FRAME.world_point_cm(reflected,p)
                    for a,b in zip(actual,expected):
                        self.assertAlmostEqual(a,b,delta=1e-10)
                self.assertEqual(reflected['scale'],(1,-1,1))

    def test_missing_rebase_and_nonfinite_inputs_are_rejected(self):
        manifest=dict(local_to_engine_yaw_degrees=0,local_origin_engine_cm=[0,0,350])
        with self.assertRaises(ValueError):
            FRAME.review_frame(manifest,{},True)
        with self.assertRaises(ValueError):
            FRAME.review_frame(manifest,dict(coordinate_rebase_only=True,parent_frame_offset_east_north_m=[math.nan,0]),True)
        for point in [(1,2),(1,2,3,4),(1,math.nan,3)]:
            with self.assertRaises(ValueError):
                FRAME.world_point_cm(FRAME.review_frame(manifest,{}),point)


if __name__=='__main__':
    unittest.main()
