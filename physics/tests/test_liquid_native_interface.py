import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_liquid_native_interface import exchange_scalars, validate_ledger, validate_transport_schedule


class NativeInterfaceTest(unittest.TestCase):
    def test_reset_is_not_a_transport_step(self):
        def group(name, first=False, reset=False):
            return dict(complete=True, aligned=True, entries=[dict(owner=i, name=name, first=first, reset=reset) for i in range(12)])
        groups = [group('ParticleSpawnUpdate', True, True), group('ParticleSpawnUpdate', True),
                  group('Project Pressure'), group('ParticleSpawnUpdate', True), group('Project Pressure')]
        self.assertEqual(validate_transport_schedule(groups, 3), 2)
        self.assertEqual(validate_transport_schedule(groups, 2), 1)
        for bad in (groups[:-1], groups+[group('Project Pressure')],
                    [groups[0], group('Project Pressure')]+groups[1:],
                    [groups[0], group('ParticleSpawnUpdate', True, True)]+groups[2:]):
            with self.assertRaises(ValueError):
                validate_transport_schedule(bad, 3)

    def test_bidirectional_exchange_uses_physical_source(self):
        a = np.arange(6*8*10).reshape(6,8,10).astype(float)
        b = a+1000
        out = exchange_scalars([a,b], [[0,1,2,3,0,2], [1,0,3,2,1,1]])
        np.testing.assert_array_equal(out[1][:,2,0], a[:,3,2])
        np.testing.assert_array_equal(out[0][:,1,1], b[:,2,3])
        np.testing.assert_array_equal(out[0][:,2:-2,2:-2], a[:,2:-2,2:-2])

    def test_unified_transport_requires_post_projection_stage_each_step(self):
        def group(name,first=False,reset=False):
            return dict(complete=True,aligned=True,entries=[dict(owner=i,name=name,first=first,reset=reset) for i in range(12)])
        groups=[group('Spawn',True,True),group('Spawn',True),group('Project Pressure'),group('Extrapolate Velocities Again')]
        self.assertEqual(validate_transport_schedule(groups,2,'Extrapolate Velocities Again'),1)
        for bad in (groups[:-1],groups[:2]+[groups[-1],groups[-2]],groups+[groups[-1]]):
            with self.assertRaises(ValueError):validate_transport_schedule(bad,2,'Extrapolate Velocities Again')

    def test_reject_invalid_copy(self):
        fields = [np.zeros((6,8,10))]*2
        for columns in ([[0,1,0,0,0,0]], [[0,1,2,2,2,2]], [[0,1,2,2,0,0]]*2):
            with self.assertRaises(ValueError):
                exchange_scalars(fields, columns)

    def test_ledger_all_steps_required(self):
        sizes = [[10,8,6], [8,8,6]]
        words = [48,0,0,32,0,0]*3
        self.assertEqual(validate_ledger(words, sizes, 3), 240)
        for bad in (words[:-1], [47]+words[1:], [48,1]+words[2:]):
            with self.assertRaises(ValueError):
                validate_ledger(bad, sizes, 3)


if __name__ == '__main__':
    unittest.main()
