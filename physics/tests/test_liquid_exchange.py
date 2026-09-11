import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from analyze_liquid_exchange import audit_exchange


class LiquidExchangeTest(unittest.TestCase):
    def fixture(self):
        packed = np.zeros((260, 3))
        packed[2] = [32.8125, 1050, 350]
        packed[3] = [800/24, 64, 24]
        # Deliberately fractional cells: 1.75 m of wet aperture, not whole voxels.
        packed[4:] = [362.5, 537.5, 100]
        fields = {'Velocity': np.zeros((24, 68, 68, 3)),
                  'SolidVelocity_Boundary': np.zeros((24, 68, 68, 4))}
        return fields, {'packed_vectors': packed.tolist()}

    def test_uniform_translation_has_balanced_opposite_faces(self):
        fields, profile = self.fixture()
        fields['Velocity'][..., 0] = 200
        result = audit_exchange(fields, profile)
        faces = {f['face']: f for f in result['faces']}
        self.assertAlmostEqual(faces['west']['native_wet_area_m2'], 21*1.75)
        self.assertAlmostEqual(faces['west']['midpoint_profile_weighted_inward_m3s'], 73.5)
        self.assertAlmostEqual(faces['east']['midpoint_profile_weighted_inward_m3s'], -73.5)
        self.assertAlmostEqual(result['midpoint_profile_weighted_net_inward_m3s'], 0.)
        self.assertFalse(result['time_integrated_mass_budget'])
        self.assertNotEqual(faces['west']['profile_velocity_over_partial_aperture_inward_m3s'],
                            faces['west']['quantized_prescribed_target_inward_m3s'])

    def test_midpoint_uses_both_cells_and_reports_solid_aperture(self):
        fields, profile = self.fixture()
        fields['Velocity'][:, 2:66, 1, 0] = 300
        fields['Velocity'][:, 2:66, 2, 0] = 100
        fields['SolidVelocity_Boundary'][:, 2:66, 2, 3] = 1
        west = audit_exchange(fields, profile)['faces'][0]
        self.assertAlmostEqual(west['midpoint_profile_weighted_inward_m3s'], 73.5)
        self.assertAlmostEqual(west['native_aperture_adjacent_solid_m2'], 36.75)

    def test_nonfinite_state_is_rejected(self):
        fields, profile = self.fixture()
        fields['Velocity'][0, 0, 0, 0] = np.nan
        with self.assertRaises(ValueError):
            audit_exchange(fields, profile)


if __name__ == '__main__':
    unittest.main()
