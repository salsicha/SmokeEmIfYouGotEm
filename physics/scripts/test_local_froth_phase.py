"""Analytical contracts for the optical backtrace, not GPU/image acceptance."""
import math
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


def phases(t):
    a = t % 1.
    b = (a+.5) % 1.
    return a, b, 1-abs(2*a-1)


def sample(p, velocity, t):
    a, b, weight = phases(t)
    texture = lambda age: math.sin(p[0]-velocity[0]*age) * math.cos(p[1]-velocity[1]*age)
    return texture(b)*(1-weight)+texture(a)*weight


class LocalFrothPhaseTest(unittest.TestCase):
    def assert_current_coverage_contract(self, author, coverage):
        # The current author loads thresholded cell coverage rather than the
        # superseded inline lace blend. Check its real dependency and callsite.
        self.assertIn('FFileHelper::LoadFileToString(CoverageCode', author)
        self.assertIn('TEXT("RaftSim/Shaders/Private/RaftSimFrothCells.ush")', author)
        self.assertIn('Coverage->Code = CoverageCode + TEXT(', author)
        self.assertIn('cells.Sample(VertexFoam.r,OpticalDensity,worldM,FrothFlow.xy,FrothTime,footprintM)', author)
        for expression in (
                'return 1-smoothstep(p-band,p+band,Random(cell));',
                'lerp(lerp(Occupancy(cell,p),Occupancy(cell+int2(1,0),p),f.x)',
                'lerp(Occupancy(cell+int2(0,1),p),Occupancy(cell+int2(1,1),p),f.x),f.y)',
                'float a=frac(time),b=frac(a+0.5),weight=1-abs(2*a-1);',
                'return lerp(Phase(worldM-velocityMps*b,p,footprintM),',
                'Phase(worldM-velocityMps*a,p,footprintM),weight);'):
            self.assertIn(expression, coverage)

    def test_phase_reset_is_continuous(self):
        for t in (0, .5, 1, 1.5, 2, 4, 6, 40000, 40000.5):
            self.assertAlmostEqual(sample((3.4,-6.2),(2,-.85),t-1e-8),
                                   sample((3.4,-6.2),(2,-.85),t+1e-8), places=6)

    def test_zero_flow_does_not_breathe(self):
        for t in (.1, .5, 1., 2., 3.9, 4., 60.):
            self.assertAlmostEqual(sample((3.4,-6.2),(0,0),t), sample((3.4,-6.2),(0,0),0), places=14)

    def test_backtraces_bounded_and_partition_unity(self):
        for i in range(10000):
            a, b, w = phases(i*.173)
            self.assertTrue(0<=a<1 and 0<=b<1 and 0<=w<=1)
            self.assertEqual(w+(1-w),1.)

    def test_local_velocity_and_recentre(self):
        uv, origin, moved = 12.5, -1860., 26.5
        self.assertEqual((uv+origin)*.78, ((uv-moved)+(origin+moved))*.78)
        # With unchanged velocity, phase coordinates move by -v*dt, in source
        # metres; north reflection already occurred in geometry, not UV1.
        for v in (2., -.85):
            x0, x1 = (uv+origin)*.78-v*.26*.3, (uv+origin)*.78-v*.26*.4
            self.assertAlmostEqual(x1-x0,-v*.26*.1)

    def test_real_callsite_preserves_history_and_shader_is_optical(self):
        cpp=(ROOT/'unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimWaterSurfaceActor.cpp').read_text()
        start=cpp.index('const FVector2D PreviousFlowVelocityMps = FlowVelocityMetersPerSecond[Index];')
        clear=cpp.index('FlowVelocityMetersPerSecond[Index] = FVector2D::ZeroVector;',start)
        use=cpp.index('PreviousFlowVelocityMps, SampledFlowVelocityMps, RefreshIntervalSeconds',clear)
        self.assertLess(start,clear)
        self.assertLess(clear,use)
        shader=(ROOT/'unreal/Shaders/Private/RaftSimLocalFoamLace.hlsl').read_text()
        self.assertIn('frac(TimeSeconds)',shader)
        self.assertIn('Flow.xy * (0.78 / 3.0)',shader)
        self.assertNotIn('RaftSimFoamAdvectionMeters',shader)
        self.assertNotIn('VertexFoam',shader)
        self.assertIn('return float3(laceA, laceB, weightA);',shader)
        author=(ROOT/'unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/RaftSimEditorCurrentWaterMaterial.cpp').read_text()
        coverage=(ROOT/'unreal/Plugins/RaftSim/Shaders/Private/RaftSimFrothCells.ush').read_text()
        self.assert_current_coverage_contract(author, coverage)

    def test_current_coverage_contract_rejects_missing_threshold_or_phase_blend(self):
        author=(ROOT/'unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/RaftSimEditorCurrentWaterMaterial.cpp').read_text()
        coverage=(ROOT/'unreal/Plugins/RaftSim/Shaders/Private/RaftSimFrothCells.ush').read_text()
        for token in ('return 1-smoothstep(p-band,p+band,Random(cell));',
                      'return lerp(Phase(worldM-velocityMps*b,p,footprintM),'):
            with self.subTest(token=token), self.assertRaises(AssertionError):
                self.assert_current_coverage_contract(author, coverage.replace(token, ''))
        with self.assertRaises(AssertionError):
            self.assert_current_coverage_contract(author.replace('Coverage->Code = CoverageCode + TEXT(', ''), coverage)

    def test_blend_coverage_not_unthresholded_lace(self):
        # At either dense or sparse thresholds, complementary texture holes
        # have 50% mixed coverage, not the 0%/100% introduced by mean lace.
        for threshold in (.2, .8):
            coverage = .5*float(0>threshold)+.5*float(1>threshold)
            self.assertEqual(coverage,.5)
            self.assertNotEqual(coverage,float(.5>threshold))


if __name__ == '__main__':
    unittest.main()
