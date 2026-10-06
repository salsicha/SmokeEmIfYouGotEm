"""Analytical and source contracts, not shader/GPU visual acceptance."""
import math
from pathlib import Path
import unittest
from test_local_froth_phase import phases

ROOT = Path(__file__).resolve().parents[2]


def normal(p, v, time):
    a, b, w = phases(time)
    gradient = lambda age: (math.sin(p[0]-v[0]*age), math.cos(p[1]-v[1]*age))
    ga, gb = gradient(a), gradient(b)
    slope = tuple(gb[i]*(1-w)+ga[i]*w for i in range(2))
    scale = math.sqrt(1+sum(x*x for x in slope))
    return (-slope[0]/scale, -slope[1]/scale, 1/scale)


class LocalCurrentNormalTest(unittest.TestCase):
    def test_shared_clock_and_physical_coordinates(self):
        shader = (ROOT/'unreal/Shaders/Private/RaftSimLocalCurrentNormal.hlsl').read_text()
        foam = (ROOT/'unreal/Shaders/Private/RaftSimLocalFoamLace.hlsl').read_text()
        for line in ('float phaseA = frac(TimeSeconds);',
                     'float phaseB = frac(phaseA + 0.5);',
                     'float weightA = 1.0 - abs(2.0*phaseA-1.0);'):
            self.assertIn(line, shader)
            self.assertIn(line, foam)
        self.assertIn('(UV + Origin.xy) * 3.0', shader)
        self.assertIn('p - Flow.xy * phaseA', shader)
        self.assertIn('p - Flow.xy * phaseB', shader)
        self.assertNotIn('Current.xy', shader)
        self.assertIn('max(length(ddx(p)), length(ddy(p)))', shader)

    def test_zero_flow_and_phase_seams(self):
        for t in (0., .3, .5, 1., 1.5, 2., 4., 6., 40000., 40000.5):
            self.assertEqual(normal((.2,.7),(0,0),t), normal((.2,.7),(0,0),0))
            a, b = normal((3,-4),(2,-.85),t-1.e-8), normal((3,-4),(2,-.85),t+1.e-8)
            for x, y in zip(a,b):
                self.assertAlmostEqual(x,y,places=6)

    def test_local_reversal_and_upward_unit_normal(self):
        for t in (.1,.5,1.3,2.7,3.9):
            a, b = normal((3,-4),(2,-.85),t), normal((3,-4),(-2,.85),t)
            self.assertNotEqual(a,b)
            self.assertAlmostEqual(sum(x*x for x in a),1.)
            self.assertGreater(a[2],0.)

    def test_material_upgrade_is_south_fork_only_and_removes_shared_current(self):
        author = (ROOT/'unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/RaftSimEditorCurrentWaterMaterial.cpp').read_text()
        start = author.index('if (RiverLabel == TEXT("SouthFork"))\n    {\n        FString LocalNormalCode;')
        end = author.index('Material->GetEditorOnlyData()->Normal.Connect', start)
        block = author[start:end]
        self.assertIn('Input.InputName == TEXT("Current")', block)
        self.assertIn('Flow->CoordinateIndex = 3;', block)
        self.assertIn('HasInput(TEXT("Flow"))', block)
        self.assertIn('HasInput(TEXT("TimeSeconds"))', block)


if __name__ == '__main__':
    unittest.main()
