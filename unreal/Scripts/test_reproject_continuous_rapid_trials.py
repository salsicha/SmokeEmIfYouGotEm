"""Pure contract tests; adapter stub is not native/gameplay validation."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


class Vector:
    def __init__(self, x, y, z=0.):
        self.x, self.y, self.z = x, y, z


class LinearAdapter:
    def configure_river_coordinate_map(self, name):
        self.data = json.loads(Path(name).read_text())
        return True

    def river_to_world_position(self, point, height):
        return Vector(100.*(point.x-self.data.get('offset', 0.)), 100.*point.y, height)

    def world_to_river_coordinates(self, point):
        return (Vector(point.x/100.+self.data.get('offset', 0.), point.y/100.),
                Vector(1., 0.), Vector(0., 1.))


class ReprojectionContract(unittest.TestCase):
    def setUp(self):
        fake = types.SimpleNamespace(RaftSimWaterRuntimeAdapter=LinearAdapter,
                                     Vector2D=Vector, log=lambda message: None)
        path = Path(__file__).with_name('reproject_continuous_rapid_trials.py')
        spec = importlib.util.spec_from_file_location('reprojection_test_subject', path)
        self.module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, unreal=fake):
            spec.loader.exec_module(self.module)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root/'tmp').mkdir()
        self.module.ROOT = self.root
        chart = dict(schema='raftsim.curved_river_coordinate_map.v1', world_y_sign=-1,
                     horizontal_origin_epsg6404_m=[0., 0.], vertical_datum_m=310.,
                     points=[[0.], [500.]])
        self.write('source.json', chart)
        self.write('target.json', dict(chart, offset=1000., points=[[1000.], [1500.]]))
        self.plan = [dict(river='old', map='old', scenario='old', trials=[dict(
            id='line', start_m=100., finish_m=200., control_m=150., strict_route=True,
            lane_m=-4., lookahead_m=45., initial_heading_deg=30.,
            route_laterals=[[100., -4.], [140., -4.], [200., 5.]],
            steering_start_m=130., gates=[dict(id='middle', station_m=150.)])])]
        self.write('plan.json', self.plan)
        self.request = dict(plan='plan.json', source_chart='source.json', target_chart='target.json',
                            output='tmp/output', river='new', map='new', scenario='new',
                            runtime_manifest='pending/manifest.json', coverage_m=[1000., 1500.])
        self.write('request.json', self.request)
        self.env = patch.dict(os.environ, RAFTSIM_TRIAL_REPROJECTION='request.json')
        self.env.start()
        self.addCleanup(self.env.stop)

    def write(self, name, value):
        (self.root/name).write_text(json.dumps(value))

    def test_route_events_heading_and_receipt(self):
        self.module.main()
        trial = json.loads((self.root/'tmp/output/plan.json').read_text())[0]['trials'][0]
        self.assertEqual(trial['start_m'], 1100.)
        self.assertEqual(trial['finish_m'], 1200.)
        self.assertEqual(trial['control_m'], 1150.)
        self.assertEqual(trial['steering_start_m'], 1130.)
        self.assertEqual(trial['gates'][0]['station_m'], 1150.)
        self.assertEqual(trial['initial_heading_deg'], 30.)
        self.assertEqual(trial['route_laterals'][0], [1100., -4.])
        self.assertEqual(trial['route_laterals'][-1], [1200., 5.])
        receipt = json.loads((self.root/'tmp/output/receipt.json').read_text())
        self.assertFalse(receipt['boat_trials_run'])
        self.assertFalse(receipt['performance_accepted'])
        self.assertAlmostEqual(receipt['native_roundtrip_max_error_m'], 0.)

    def test_unknown_distance_field_refused(self):
        self.plan[0]['trials'][0]['new_event_m'] = 180.
        self.write('plan.json', self.plan)
        with self.assertRaisesRegex(ValueError, 'Unreviewed'):
            self.module.main()
        self.assertFalse((self.root/'tmp/output').exists())

    def test_coverage_refused(self):
        self.request['coverage_m'] = [1000., 1150.]
        self.write('request.json', self.request)
        with self.assertRaises(AssertionError):
            self.module.main()
        self.assertFalse((self.root/'tmp/output').exists())

    def test_frame_mismatch_refused(self):
        chart = json.loads((self.root/'target.json').read_text())
        chart['vertical_datum_m'] += 1.
        self.write('target.json', chart)
        with self.assertRaisesRegex(AssertionError, 'Different geographic frames'):
            self.module.main()

    def test_heading_hold_not_silently_translated(self):
        trial = dict(self.plan[0]['trials'][0], id='hold', heading_offset_deg=60.)
        self.plan[0]['trials'].append(trial)
        self.write('plan.json', self.plan)
        self.module.main()
        receipt = json.loads((self.root/'tmp/output/receipt.json').read_text())
        self.assertEqual([t['id'] for t in receipt['trials']], ['line'])
        self.assertEqual([t['id'] for t in receipt['excluded']], ['hold'])

    def test_existing_output_not_overwritten(self):
        self.module.main()
        with self.assertRaisesRegex(AssertionError, 'Fresh evidence'):
            self.module.main()


if __name__ == '__main__':
    unittest.main()
