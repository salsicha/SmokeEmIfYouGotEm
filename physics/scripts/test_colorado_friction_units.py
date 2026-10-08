import copy
import unittest
from chilko_native_friction import validate_friction, runtime_friction_fields
from continue_colorado_catalog_cook import roughness_sensitivity
from repair_colorado_friction_inputs import corrected_scenario


class ColoradoFrictionUnits(unittest.TestCase):
    def setUp(self):
        self.report=dict(continuous_terrain={'manifest':'same'},shared_hydraulic_frame={'manifest':'same'},roughness_hypothesis=.04)
        self.scenario=dict(roughness=.04,grid={'nx':100},boundaries=[dict(edge='west',kind='discharge_profile')],
            metadata=dict(river_id='colorado_river_grand_canyon_rowing',provenance={'source':'unchanged'}))

    def test_correct_once_and_preserve_every_other_field(self):
        original=copy.deepcopy(self.scenario)
        result=corrected_scenario(self.scenario,self.report)
        self.assertEqual(self.scenario,original)
        self.assertAlmostEqual(result['roughness'],.015696,places=14)
        validate_friction(result,.04)
        self.assertEqual(runtime_friction_fields(result)['manning_n'],result['roughness'])
        result['roughness']=original['roughness']
        del result['metadata']['provenance']['friction']
        self.assertEqual(result,original)

    def test_double_conversion_refused(self):
        candidate=corrected_scenario(self.scenario,self.report)
        with self.assertRaisesRegex(ValueError,'twice'):
            corrected_scenario(candidate,self.report)

    def test_unrelated_or_ambiguous_packet_refused(self):
        for key,value in [('roughness',.03),('metadata',{'river_id':'chilko_river_bc'})]:
            s=copy.deepcopy(self.scenario);s[key]=value
            with self.assertRaises(ValueError):corrected_scenario(s,self.report)
        for key in ('continuous_terrain','shared_hydraulic_frame'):
            r=copy.deepcopy(self.report);r[key]=None
            with self.assertRaises(ValueError):corrected_scenario(self.scenario,r)

    def test_future_sensitivity_uses_physical_n_not_native_coefficient(self):
        candidate=corrected_scenario(self.scenario,self.report)
        result,receipt=roughness_sensitivity(candidate,.035)
        validate_friction(result,.035)
        self.assertEqual(receipt['original'],.04)
        self.assertAlmostEqual(result['roughness'],9.81*.035**2)
        validate_friction(candidate,.04)

    def test_no_sensitivity_does_not_convert_again(self):
        candidate=corrected_scenario(self.scenario,self.report)
        result,receipt=roughness_sensitivity(candidate,None)
        self.assertEqual(result,candidate)
        self.assertIsNone(receipt)

    def test_invalid_contract_cannot_continue_even_without_sensitivity(self):
        candidate=corrected_scenario(self.scenario,self.report)
        candidate['roughness']=.04
        with self.assertRaisesRegex(ValueError,'disagree'):
            roughness_sensitivity(candidate,None)


if __name__=='__main__':unittest.main()
