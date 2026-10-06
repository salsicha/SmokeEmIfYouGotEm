#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "Engine/World.h"
#include "Engine/TextureRenderTarget2D.h"
#include "RaftSimWaterSurfaceActor.h"
#include "RaftSimWaterRuntimeAdapter.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimVisibleSprayCarrierTest,
    "RaftSim.M4.VisibleSprayCarrier", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimVisibleSprayCarrierTest::RunTest(const FString&)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Editor, false);
    if (!TestNotNull(TEXT("fixture world"), World)) return false;
    ON_SCOPE_EXIT { World->DestroyWorld(false); World->RemoveFromRoot(); };
    auto* Surface = World->SpawnActor<ARaftSimWaterSurfaceActor>();
    if (!TestNotNull(TEXT("fixture carrier"), Surface)) return false;
    Surface->SetActorTransform(FTransform(FRotator(0, 20, 0), FVector(100, 200, 50)));
    Surface->bStatefulGPUCarrierReview = true;
    Surface->bStatefulCrestReview = true;
    Surface->bSingleLiveWaterSurfaceEnabled = false;
    Surface->GridStationN = Surface->GridLateralN = 2;
    Surface->ResolvedVertexSpacingMeters = 1.5f;
    Surface->ResolvedPresentationHydraulicReliefScale = 0.8f;
    Surface->RiverCoordinatesM = {FVector2D(0,0), FVector2D(1.5,0), FVector2D(0,1.5), FVector2D(1.5,1.5)};
    Surface->Triangles = {0,2,1,1,2,3};
    Surface->SprayWetCarrierMask.Init(1,4);
    Surface->MacroCrestShoreWeights = {1,1,1,0.2f};
    Surface->MacroCrestSites = {FVector4f(0.4f,0.3f,0.5f,3), FVector4f(1,1,1,0)};
    Surface->MacroSurfaceTexture = NewObject<UTextureRenderTarget2D>(Surface);
    URaftSimWaterRuntimeAdapter::FSupportBreakingSite Site;
    Site.RiverCoordinatesMeters = FVector2D(0.4f,0.3f);
    Site.PhysicalCrestHeightMeters = 0.5f; Site.PhysicalCrestLengthMeters = 3;
    Site.Intensity = Site.SpillingFraction = 1; Site.bLocalEnvelopeCap = true;
    TArray<URaftSimWaterRuntimeAdapter::FSupportBreakingSite> Sites = {Site};
    for (int32 I=0; I<4; ++I)
    {
        const FVector2D P = Surface->RiverCoordinatesM[I];
        const float Crest = 80 * Surface->MacroCrestShoreWeights[I] *
            URaftSimWaterRuntimeAdapter::ComputeCoupledBreakingReliefMeters(P, Sites, 1, 1.5f);
        Surface->MacroCrestDisplacementCm.Add(Crest);
        Surface->Vertices.Add(FVector(P.X*100, P.Y*100, 100+ Crest));
    }
    Surface->SurfaceMesh->CreateMeshSection(0, Surface->Vertices, Surface->Triangles,
        TArray<FVector>(), TArray<FVector2D>(), TArray<FColor>(), TArray<FProcMeshTangent>(), false);
    Surface->SurfaceMesh->SetVisibility(true);
    Surface->SurfaceMesh->SetMeshSectionVisible(0,true);
    Surface->LiveVolumeCoreMesh->SetVisibility(false);
    for (const FVector2D P : {FVector2D(0.6,0.45), FVector2D(0.9,1.2)})
    {
        FVector Actual;
        if (!TestTrue(TEXT("visible GPU carrier works with legacy mesh hidden"),
            Surface->SampleVisibleCarrierAtRiverCoordinates(P, Actual))) continue;
        const float Corner3Weight = FMath::Max(0.0, P.X/1.5 + P.Y/1.5 - 1);
        const float Shore = 1 - 0.8f*Corner3Weight;
        FVector Expected = Surface->GetActorTransform().TransformPosition(FVector(P.X*100,P.Y*100,100));
        Expected.Z += 80*Shore*URaftSimWaterRuntimeAdapter::ComputeCoupledBreakingReliefMeters(P,Sites,1,1.5f);
        TestTrue(TEXT("both triangles replace coarse crest once in world coordinates"), Actual.Equals(Expected,0.001));
    }
    FVector Point;
    Surface->SprayWetCarrierMask[0] = 0;
    TestFalse(TEXT("dry weighted corner rejected"), Surface->SampleVisibleCarrierAtRiverCoordinates(FVector2D(0.2,0.2),Point));
    TestTrue(TEXT("zero-weight dry corner cannot reject another wet vertex"), Surface->SampleVisibleCarrierAtRiverCoordinates(FVector2D(1.5,1.5),Point));
    Surface->SprayWetCarrierMask[0] = 1;
    Surface->VisualBankProbeState.Init(1,4);
    Surface->VisualBankTerrainZCm.Init(1000,4);
    TestFalse(TEXT("buried measured bank rejected"), Surface->SampleVisibleCarrierAtRiverCoordinates(FVector2D(0.6,0.45),Point));
    Surface->VisualBankProbeState.Reset(); Surface->VisualBankTerrainZCm.Reset();
    TestFalse(TEXT("outside source footprint rejected"), Surface->SampleVisibleCarrierAtRiverCoordinates(FVector2D(-0.1,0),Point));
    Surface->SurfaceMesh->SetVisibility(false);
    TestFalse(TEXT("hidden carrier cannot authorize spray"), Surface->SampleVisibleCarrierAtRiverCoordinates(FVector2D(0.6,0.45),Point));
    Surface->SurfaceMesh->SetVisibility(true);
    Surface->MacroSurfaceTexture = nullptr;
    TestFalse(TEXT("missing GPU atlas cannot authorize spray"), Surface->SampleVisibleCarrierAtRiverCoordinates(FVector2D(0.6,0.45),Point));
    AddInfo(TEXT("CPU presentation anchor fixture, not GPU perturbation readback, particle collision or rapid realism acceptance."));
    return true;
}
#endif
