import copy
import unittest
from build_chilko_completed_corridor_inputs import validate_export, require_idle_headroom, watchdog_failure


class FullTerrainHandoffTests(unittest.TestCase):
    def test_shared_work_refuses_launch_and_stops_only_owned_builder(self):
        healthy=dict(available_physical_bytes=10*1024**3,available_commit_bytes=10*1024**3,free_disk_bytes=48*1024**3)
        busy=[dict(ProcessId=123,Name='UnrealEditor.exe')]
        with self.assertRaisesRegex(ValueError,'do not overlap'):
            require_idle_headroom(healthy,busy)
        self.assertIn('only owned',watchdog_failure(healthy,busy,0))
        require_idle_headroom(healthy,[])
        self.assertIsNone(watchdog_failure(healthy,[],0))

    def test_launch_and_runtime_reserves_remain_unchanged(self):
        healthy=dict(available_physical_bytes=10*1024**3,available_commit_bytes=10*1024**3,free_disk_bytes=48*1024**3)
        for key,launch,runtime in (('available_physical_bytes',8,3),('available_commit_bytes',8,3),('free_disk_bytes',43,40)):
            with self.subTest(key=key):
                require_idle_headroom({**healthy,key:launch*1024**3},[])
                with self.assertRaises(ValueError):require_idle_headroom({**healthy,key:launch*1024**3-1},[])
                self.assertIsNone(watchdog_failure({**healthy,key:runtime*1024**3},[],0))
                self.assertIsNotNone(watchdog_failure({**healthy,key:runtime*1024**3-1},[],0))
        self.assertIsNone(watchdog_failure(healthy,[],8*3600))
        self.assertIn('time bound',watchdog_failure(healthy,[],8*3600+.01))

    def fixture(self):
        request=dict(expected_chunks=4772,route_length_m=55723.04503105954,spacing_m=1.,buffer_m=600.)
        completed=dict(inputs_unchanged=True,chunks=4772,maximum_shared_edge_encoded_difference=0)
        manifest=dict(schema='raftsim.continuous_landscape.v1',river_id='chilko_river_bc',horizontal_crs='EPSG:3157',
            vertical_reference='CGVD2013 (EPSG:6647)',world_y_sign=-1,horizontal_origin_m=[442000.,5749000.],vertical_datum_m=900.,
            landscape=dict(spacing_m=1.,vertices=127,span_m=126.),chunks=[dict(chunk=[i,0]) for i in range(4772)],
            geographic_scope=dict(route_interval_m=[0.,55723.04503105954],buffer_m=600.),incomplete_source_chunks=[])
        return request,completed,manifest

    def test_complete_source_contract(self):
        validate_export(*self.fixture())

    def test_partial_or_shifted_route_refuses(self):
        for change in ('partial','duplicate','window','shift','coarse','incomplete'):
            r,c,m=self.fixture()
            if change=='partial':m['chunks'].pop()
            if change=='duplicate':m['chunks'][-1]=copy.deepcopy(m['chunks'][0])
            if change=='window':m['geographic_scope']['chunk_window_inclusive']=[0,0,10,10]
            if change=='shift':m['geographic_scope']['route_interval_m'][0]=100.
            if change=='coarse':m['landscape']['spacing_m']=2.
            if change=='incomplete':m['incomplete_source_chunks']=[[0,0]]
            with self.subTest(change=change),self.assertRaises(ValueError):validate_export(r,c,m)

    def test_failed_completion_and_seams_refuse(self):
        for key,value in (('inputs_unchanged',False),('chunks',4771),('maximum_shared_edge_encoded_difference',1)):
            r,c,m=self.fixture();c[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):validate_export(r,c,m)
