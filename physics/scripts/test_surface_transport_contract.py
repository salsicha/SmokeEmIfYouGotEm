"""Source wiring contracts complement native packing and actual game audits."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class SurfaceTransportContractTest(unittest.TestCase):
    def test_pocket_and_boil_generation_budget_does_not_scale_geometry_or_transport(self):
        cpp = (ROOT/'unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimWaterSurfaceActor.cpp').read_text()
        self.assertIn('LocalWeight,Site.HydraulicSpillingFraction,',cpp)
        self.assertIn('PocketFoam, Pocket.Y * FoamSourceWeight',cpp)
        self.assertIn('BoilFoam, Boil.Y * FoamSourceWeight',cpp)
        self.assertIn('Pocket.X * LocalWeight',cpp)
        self.assertIn('Boil.X * LocalWeight',cpp)
        advection = cpp[cpp.index('TArray<float> NewFoamField;'):cpp.index('FoamField = MoveTemp(NewFoamField);')]
        self.assertNotIn('FoamSourceWeight',advection)

    def test_export_is_after_roller_and_eddy_and_before_exact_backtrace(self):
        cpp = (ROOT/'unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimWaterSurfaceActor.cpp').read_text()
        start = cpp.index('FieldVelocity += RollerVelocity.GetClampedToMaxSize(')
        eddy = cpp.index('FieldVelocity = FMath::Lerp(',start)
        export = cpp.index('FoamTransportVelocityMetersPerSecond[Index] = FieldVelocity;',eddy)
        trace = cpp.index('FieldPosition - FieldVelocity * FoamDeltaSeconds;',export)
        self.assertLess(start,eddy)
        self.assertLess(eddy,export)
        self.assertLess(export,trace)
        self.assertIn('FoamTransportVelocityMetersPerSecond.Init(FVector2D::ZeroVector,Vertices.Num());',cpp)

    def test_carrier_preserves_bulk_and_wake(self):
        pack = (ROOT/'unreal/Plugins/RaftSim/Source/RaftSimRaft/Public/RaftSimWaterSourcePacking.h').read_text()
        self.assertIn('V.UV1=Flow[I]; V.UV2=Wake[I];',pack)
        self.assertIn('V.UV3=SurfaceTransport.Num() ? SurfaceTransport[I] : FVector2D::ZeroVector;',pack)
        self.assertIn('(SurfaceTransport.Num()!=0 && SurfaceTransport.Num()!=N)',pack)


if __name__ == '__main__':
    unittest.main()
