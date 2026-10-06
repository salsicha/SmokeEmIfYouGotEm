#include "RaftSimWaterSurfaceActor.h"
#include "RaftSimRaftActor.h"
#include "RaftSimRiverWaterConfig.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "Engine/World.h"
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCartesianSurfaceGridTest,
    "RaftSim.M4.CartesianSurfaceGrid",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimCartesianSurfaceGridTest::RunTest(const FString&)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Editor, false);
    if (!TestNotNull(TEXT("isolated surface world"), World)) return false;
    ON_SCOPE_EXIT { World->DestroyWorld(false); World->RemoveFromRoot(); };
    auto* Surface = World->SpawnActor<ARaftSimWaterSurfaceActor>();
    auto* Raft = World->SpawnActor<ARaftSimRaftActor>();
    if (!Surface || !Raft) { AddError(TEXT("surface fixture actors did not spawn")); return false; }
    auto* Water = NewObject<URaftSimWaterRuntimeAdapter>(Surface);
    if (!TestTrue(TEXT("actual full-river Cartesian coordinate map loads"), Water->ConfigureRiverCoordinateMap(
        TEXT("physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach/hydraulic_regions_context/coordinate_map.json")))) return false;
    Surface->WaterAdapter = Water;
    Surface->VertexSpacingMeters = 2.f;
    Surface->CurvedGridLengthMeters = 32.f;
    Surface->CurvedGridWidthMeters = 24.f;
    Surface->CurvedGridRecenterDistanceMeters = 6.f;
    Raft->SetActorLocation(FVector(-540000., -360000., 0.));
    Surface->BuildGrid(); // Actual production construction, not a duplicate grid formula.
    TestEqual(TEXT("initial carrier east follows raft"), Surface->CurvedGridCenterStationM, -5400.f);
    TestEqual(TEXT("initial carrier north follows raft instead of zero"), Surface->CartesianGridCenterNorthM, 3600.f);
    Surface->bRebaseWaterTextureCoordinates = true;
    const int32 Nx = Surface->GridStationN, Ny = Surface->GridLateralN, Count = Nx * Ny;
    int32 CheckedOverlap = 0;
    for (const FVector2D Target : {FVector2D(-5400,3608), FVector2D(-5408,3608),
        FVector2D(-5400,3600), FVector2D(-5392,3592),
        FVector2D(-5392,3656), FVector2D(-5392,3640)})
    {
        const FVector2D PreviousCenter(Surface->CurvedGridCenterStationM, Surface->CartesianGridCenterNorthM);
        const auto PreviousCoordinates = Surface->RiverCoordinatesM;
        Surface->VisualBankTerrainZCm.SetNum(Count);
        Surface->VisualBankProbeState.SetNum(Count);
        Surface->VisualFilmCullState.SetNum(Count);
        Surface->LiveVolumeCoreNormals.SetNum(Count);
        Surface->LiveVolumeCoreVertexColors.SetNum(Count);
        Surface->RenderedLiveVolumeCoreVertices.SetNum(Count);
        Surface->RenderedLiveVolumeCoreNormals.SetNum(Count);
        Surface->RenderedLiveVolumeCoreVertexColors.SetNum(Count);
        Surface->RenderedLiveVolumeCoreFlowVelocity.SetNum(Count);
        Surface->RenderedLiveVolumeCoreWakeData.SetNum(Count);
        for (int32 I = 0; I < Count; ++I)
        {
            Surface->LiveVolumeCoreWetPresence[I] = I + .1f;
            Surface->SmoothedRapidFoamCoverage[I] = I + .2f;
            Surface->SmoothedBreakingLiftCm[I] = I + .3f;
            Surface->ShoreSmoothedSurfaceZCm[I] = I + .4f;
            Surface->VisualBankTerrainZCm[I] = I + .5f;
            Surface->VisualBankProbeState[I] = 1 + I % 2;
            Surface->VisualFilmCullState[I] = 1 + I % 3;
            Surface->FlowVelocityMetersPerSecond[I] = FVector2D(I, -I);
            Surface->RenderedLiveVolumeCoreVertices[I] = FVector(I, I+1, I+2);
            Surface->RenderedLiveVolumeCoreNormals[I] = FVector(I+.1, I+.2, I+.3);
            Surface->RenderedLiveVolumeCoreVertexColors[I] = FLinearColor(I, I+1, I+2, .7f);
            Surface->RenderedLiveVolumeCoreFlowVelocity[I] = FVector2D(I+3, I+4);
            Surface->RenderedLiveVolumeCoreWakeData[I] = FVector2D(I+5, I+6);
            Surface->LiveVolumeCoreVertices[I] = FVector(-1,-2,-3);
            Surface->LiveVolumeCoreNormals[I] = FVector::UpVector;
            Surface->LiveVolumeCoreVertexColors[I] = FLinearColor::Black;
            Surface->BoatWakePresentationData[I] = FVector2D(-5,-6);
        }
        Raft->SetActorLocation(FVector(Target.X*100., -Target.Y*100., 0.));
        Surface->RecenterCurvedGrid();
        TestEqual(TEXT("recenter follows east"), Surface->CurvedGridCenterStationM, static_cast<float>(Target.X));
        TestEqual(TEXT("recenter follows north"), Surface->CartesianGridCenterNorthM, static_cast<float>(Target.Y));
        TestEqual(TEXT("north texture origin rebases across both sides of a bucket boundary"),
            Surface->WaterTextureOriginMeters.Y, static_cast<double>(Surface->ComputeWaterTextureOriginMeters(Target.Y)));
        const int32 Sx = FMath::RoundToInt((Target.X-PreviousCenter.X)/2.);
        const int32 Sy = FMath::RoundToInt((Target.Y-PreviousCenter.Y)/2.);
        Surface->CarryRenderedGridHistory(Sx,Sy); // Same method used by RefreshSurface mid-blend.
        for (int32 Y=0; Y<Ny; ++Y) for (int32 X=0; X<Nx; ++X)
        {
            const int32 I=Y*Nx+X, SourceX=X+Sx, SourceY=Y+Sy;
            const bool Overlap=SourceX>=0 && SourceX<Nx && SourceY>=0 && SourceY<Ny;
            const int32 J=Overlap ? SourceY*Nx+SourceX : 0;
            FVector WorldPosition;
            TestTrue(TEXT("every carrier vertex remains in the real coordinate domain"), Water->RiverToWorldPosition(
                Surface->RiverCoordinatesM[I],Water->GetRiverVerticalDatumM(),WorldPosition));
            TestTrue(TEXT("visible XY matches hydraulic coordinates with correct north sign"),
                FVector2D(Surface->Vertices[I].X,Surface->Vertices[I].Y).Equals(FVector2D(WorldPosition.X,WorldPosition.Y),.001));
            TestTrue(TEXT("rebased UVs keep the global XY texture phase"),
                (Surface->UVs[I]*3.+Surface->WaterTextureOriginMeters).Equals(Surface->RiverCoordinatesM[I],1.e-6));
            if (Overlap) { ++CheckedOverlap; TestTrue(TEXT("overlap vertices retain exact XY"), Surface->RiverCoordinatesM[I]==PreviousCoordinates[J]); }
            TestEqual(TEXT("wet history follows both axes"),Surface->LiveVolumeCoreWetPresence[I],Overlap ? J+.1f : 0.f);
            TestEqual(TEXT("foam history follows both axes"),Surface->SmoothedRapidFoamCoverage[I],Overlap ? J+.2f : 0.f);
            TestEqual(TEXT("crest history follows both axes"),Surface->SmoothedBreakingLiftCm[I],Overlap ? J+.3f : 0.f);
            TestEqual(TEXT("shore history seeds incoming cells"),Surface->ShoreSmoothedSurfaceZCm[I],Overlap ? J+.4f : MAX_flt);
            TestEqual(TEXT("bank elevation follows both axes"),Surface->VisualBankTerrainZCm[I],Overlap ? J+.5f : 0.f);
            TestEqual(TEXT("incoming bank cells request a new trace"),Surface->VisualBankProbeState[I],static_cast<uint8>(Overlap ? 1+J%2 : 0));
            TestEqual(TEXT("film cull state follows both axes"),Surface->VisualFilmCullState[I],static_cast<uint8>(Overlap ? 1+J%3 : 0));
            TestTrue(TEXT("smoothed flow follows both axes"),Surface->FlowVelocityMetersPerSecond[I]==(Overlap ? FVector2D(J,-J) : FVector2D::ZeroVector));
            TestTrue(TEXT("mid-blend position carries overlap and seeds incoming targets"),Surface->RenderedLiveVolumeCoreVertices[I]==(Overlap ? FVector(J,J+1,J+2) : Surface->LiveVolumeCoreVertices[I]));
            TestTrue(TEXT("mid-blend normals retained"),Surface->RenderedLiveVolumeCoreNormals[I]==(Overlap ? FVector(J+.1,J+.2,J+.3) : Surface->LiveVolumeCoreNormals[I]));
            TestTrue(TEXT("mid-blend colors retained"),Surface->RenderedLiveVolumeCoreVertexColors[I]==(Overlap ? FLinearColor(J,J+1,J+2,.7f) : Surface->LiveVolumeCoreVertexColors[I]));
            TestTrue(TEXT("mid-blend flow retained"),Surface->RenderedLiveVolumeCoreFlowVelocity[I]==(Overlap ? FVector2D(J+3,J+4) : Surface->FlowVelocityMetersPerSecond[I]));
            TestTrue(TEXT("mid-blend wake retained"),Surface->RenderedLiveVolumeCoreWakeData[I]==(Overlap ? FVector2D(J+5,J+6) : Surface->BoatWakePresentationData[I]));
        }
    }
    Raft->SetActorLocation(FVector(-539100.,-364100.,0.));
    Surface->RecenterCurvedGrid();
    TestEqual(TEXT("subthreshold north motion does not rebuild"),Surface->CartesianGridCenterNorthM,3640.f);
    FBox2D Bounds;
    TestTrue(TEXT("explicit XY bounds are available without station semantics"),Water->GetCartesianWaterBoundsM(Bounds));
    Surface->CurvedGridCenterStationM=Bounds.Max.X;
    Surface->CartesianGridCenterNorthM=Bounds.Min.Y;
    Surface->ClampCurvedGridCenter();
    TestTrue(TEXT("entire carrier fits east bound"),Surface->CurvedGridCenterStationM+16.<=Bounds.Max.X);
    TestTrue(TEXT("entire carrier fits south bound"),Surface->CartesianGridCenterNorthM-12.>=Bounds.Min.Y);
    TestTrue(TEXT("clamped X remains on presentation lattice"),FMath::Fmod(Surface->CurvedGridCenterStationM,2.f)==0.f);
    TestTrue(TEXT("clamped Y remains on presentation lattice"),FMath::Fmod(Surface->CartesianGridCenterNorthM,2.f)==0.f);
    auto* Config = World->SpawnActor<ARaftSimRiverWaterConfig>();
    Config->CookedFieldsDir = TEXT("production-source-with-no-map-name-special-case");
    Config->bLiveSolverOwnsRuntimeRendering = true;
    Config->bEnableLiveSolverVolumeCore = true;
    Config->bEnableLiveRapidSurfaceRefinement = false;
    Surface->BuildGrid();
    TestFalse(TEXT("unconfigured production breaking stays disabled"), Surface->bSharedBreakingReliefEnabled);
    Config->bEnableLiveSharedBreakingRelief = true;
    Surface->BuildGrid();
    TestTrue(TEXT("authored production opt-in enables shared spatial carrier/support crests without review flags"),
        Surface->bSharedBreakingReliefEnabled && Surface->bSpatialBreakingReview && Surface->bSingleLiveWaterSurfaceEnabled);
    TestFalse(TEXT("full-river opt-in does not enable rapid-origin-only refinement"), Surface->bPlayableCrestRefinement);
    AddInfo(FString::Printf(TEXT("Actual carrier construction/recenter and rendered-history paths: %d exact overlap vertices across north/west/diagonal moves. Geometry/history regression, not visual realism or full-river flow acceptance."),CheckedOverlap));
    return !HasAnyErrors();
}
#endif
