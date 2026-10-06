import tempfile
import unittest
from pathlib import Path
from PIL import Image
from audit_water_capture_series import audit


class CaptureCoordinateFrameTest(unittest.TestCase):
    def test_recorded_downstream_frame_cannot_be_relabelled_as_hydraulic(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            log = root/'capture.log'
            log.write_text('\n'.join(
                f'capture-series request: index={i} world_s={10+i}.0 frame={100+i} '
                f'raft_river_valid=1 raft_station_m={8330+i}.0 raft_lateral_m=2.0 '
                'camera_valid=1 camera_world_cm=V(X=1.0, Y=2.0, Z=3.0) '
                'camera_pitch_deg=-8.0 camera_yaw_deg=120.0 camera_roll_deg=0.0 '
                'camera_fov_deg=90.0 raft_coordinates=scenario_downstream' for i in range(2)))
            for i in range(2):
                Image.new('RGB', (4, 4), (i*50, 0, 0)).save(root/f'fixture_{i:03d}.png')
            result = audit(log, root, 'fixture', [0, 0, 4, 4])
            self.assertEqual(result['raft_coordinate_frame'], 'scenario_downstream')
            self.assertEqual(result['raft_station_range_m'], [8330., 8331.])
            self.assertNotIn('hydraulic_coordinate_frame', result)
            self.assertEqual(result['camera_max_angle_change_deg'], 0.)
            self.assertEqual(result['camera_fov_range_deg'], [90., 90.])
            self.assertFalse(result['photorealism_accepted'])
            for wrong in ('cartesian_east_north', 'river_station_lateral'):
                with self.assertRaisesRegex(ValueError, 'contradicts'):
                    audit(log, root, 'fixture', [0, 0, 4, 4], wrong)

    def test_cartesian_fields_never_report_easting_as_descent_chainage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            log = root/'capture.log'
            log.write_text('\n'.join(
                f'capture-series request: index={i} world_s={10+i}.0 frame={100+i} '
                f'raft_river_valid=1 raft_station_m={-5400-i}.0 raft_lateral_m={3600+i}.0 '
                'camera_valid=1 camera_world_cm=V(X=1.0, Y=2.0, Z=3.0)' for i in range(2)))
            for i in range(2):
                Image.new('RGB', (4, 4), (i*50, 0, 0)).save(root/f'fixture_{i:03d}.png')
            legacy = audit(log, root, 'fixture', [0, 0, 4, 4])
            self.assertEqual(legacy['raft_station_range_m'], [-5401., -5400.])
            cartesian = audit(log, root, 'fixture', [0, 0, 4, 4], 'cartesian_east_north')
            self.assertNotIn('raft_station_range_m', cartesian)
            self.assertNotIn('raft_station_m', cartesian['requests'][0])
            self.assertEqual(cartesian['requests'][0]['raft_east_m'], -5400.)
            self.assertEqual(cartesian['raft_hydraulic_coordinate_ranges_m'], [[-5401., -5400.], [3600., 3601.]])
            self.assertEqual(cartesian['camera_max_displacement_cm'], 0.)
            self.assertFalse(cartesian['photorealism_accepted'])


if __name__ == '__main__':
    unittest.main()
