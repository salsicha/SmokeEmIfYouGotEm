import copy
import unittest
from chilko_native_friction import friction_contract, validate_friction, runtime_friction_fields


class NativeFrictionTests(unittest.TestCase):
    def scenario(self):
        c=friction_contract(.045)
        return dict(roughness=c['native_roughness_coefficient'],metadata=dict(provenance=dict(friction=c)))

    def test_manning_is_converted_once_to_native_drag_coefficient(self):
        s=self.scenario()
        self.assertAlmostEqual(s['roughness'],.01986525,places=14)
        validate_friction(s,.045)
        for value in (.045,9.81*s['roughness']**2,float('nan')):
            bad=copy.deepcopy(s);bad['roughness']=value
            with self.assertRaises(ValueError):validate_friction(bad,.045)

    def test_missing_changed_or_nonfinite_inference_is_rejected(self):
        for n in (0,-.01,.3,float('nan'),float('inf')):
            with self.assertRaises(ValueError):friction_contract(n)
        with self.assertRaises(ValueError):validate_friction(dict(roughness=.045),.045)
        with self.assertRaises(ValueError):validate_friction(self.scenario(),.05)

    def test_runtime_receives_identical_coefficient_not_second_conversion(self):
        s=self.scenario();fields=runtime_friction_fields(s)
        self.assertEqual(fields['manning_n'],s['roughness'])
        self.assertEqual(fields['effective_manning_n'],s['roughness'])
        self.assertEqual(fields['friction']['inferred_manning_n'],.045)
        self.assertIn('not_manning_n',fields['legacy_manning_fields_semantics'])

    def test_legacy_exports_unchanged(self):
        self.assertEqual(runtime_friction_fields(dict(roughness=.04)),
                         dict(manning_n=.04,effective_manning_n=.04))


if __name__=='__main__':unittest.main()
