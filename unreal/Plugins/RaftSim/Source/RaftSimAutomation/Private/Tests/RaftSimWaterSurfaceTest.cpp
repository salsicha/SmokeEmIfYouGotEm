// P2 water-rendering v1 test: the water surface actor spawns with the raft,
// builds a procedural mesh, and its bounds track the live solver surface.

#include "Components/MeshComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Materials/MaterialParameterCollection.h"
#include "Materials/MaterialParameterCollectionInstance.h"
#include "Misc/AutomationTest.h"
#include "ProceduralMeshComponent.h"
#include "RaftSimRaftActor.h"
#include "RaftSimWaterSurfaceActor.h"
#include "Tests/AutomationCommon.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimWaterSurfaceRendersTest,
    "RaftSim.P2.WaterSurfaceRenders",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext |
        EAutomationTestFlags::ProductFilter)

namespace
{

UWorld* GetSurfaceTestWorld()
{
    for (const FWorldContext& Context : GEngine->GetWorldContexts())
    {
        if (Context.World() != nullptr &&
            (Context.WorldType == EWorldType::PIE || Context.WorldType == EWorldType::Game))
        {
            return Context.World();
        }
    }
    return nullptr;
}

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(
    FRaftSimAssertWaterSurfaceCommand, FAutomationTestBase*, Test);
bool FRaftSimAssertWaterSurfaceCommand::Update()
{
    UWorld* World = GetSurfaceTestWorld();
    if (World == nullptr)
    {
        Test->AddError(TEXT("No active game world"));
        return true;
    }
    ARaftSimWaterSurfaceActor* Surface = nullptr;
    if (TActorIterator<ARaftSimWaterSurfaceActor> It(World); It)
    {
        Surface = *It;
    }
    if (Surface == nullptr)
    {
        Test->AddError(TEXT("No water surface actor spawned with the raft"));
        return true;
    }
    Test->TestFalse(
        TEXT("straight dev tank retains the base presentation grid"),
        Surface->IsRiverPresentationGridRefined());
    Test->TestTrue(
        TEXT("straight dev tank retains three-metre presentation spacing"),
        FMath::IsNearlyEqual(
            Surface->GetPresentationVertexSpacingMeters(), 3.0f, 0.001f));

    UMaterialParameterCollection* FoamOcclusionCollection =
        LoadObject<UMaterialParameterCollection>(
            nullptr,
            TEXT("/Game/RaftSim/Materials/MPC_RaftSim_RaftFoamOcclusion."
                 "MPC_RaftSim_RaftFoamOcclusion"));
    Test->TestNotNull(
        TEXT("raft foam exclusion collection is loadable"),
        FoamOcclusionCollection);
    if (FoamOcclusionCollection)
    {
        UMaterialParameterCollectionInstance* FoamOcclusion =
            World->GetParameterCollectionInstance(FoamOcclusionCollection);
        Test->TestNotNull(
            TEXT("game world has a foam exclusion collection instance"),
            FoamOcclusion);
        if (FoamOcclusion)
        {
            float Enabled = 0.0f;
            FLinearColor CenterAndWidth = FLinearColor::Transparent;
            FLinearColor ForwardAndLength = FLinearColor::Transparent;
            float InteriorWaterEnabled = 0.0f;
            FLinearColor InteriorCenterAndWidth = FLinearColor::Transparent;
            FLinearColor InteriorForwardAndLength = FLinearColor::Transparent;
            Test->TestTrue(
                TEXT("foam exclusion enable parameter exists"),
                FoamOcclusion->GetScalarParameterValue(
                    TEXT("RaftFoamExclusionEnabled"), Enabled));
            Test->TestTrue(
                TEXT("foam exclusion center parameter exists"),
                FoamOcclusion->GetVectorParameterValue(
                    TEXT("RaftFoamExclusionCenterAndHalfWidthCm"),
                    CenterAndWidth));
            Test->TestTrue(
                TEXT("foam exclusion forward parameter exists"),
                FoamOcclusion->GetVectorParameterValue(
                    TEXT("RaftFoamExclusionForwardAndHalfLengthCm"),
                    ForwardAndLength));
            Test->TestTrue(
                TEXT("raft-interior transmission enable parameter exists"),
                FoamOcclusion->GetScalarParameterValue(
                    TEXT("RaftInteriorWaterTransmissionEnabled"),
                    InteriorWaterEnabled));
            Test->TestTrue(
                TEXT("raft-interior transmission center parameter exists"),
                FoamOcclusion->GetVectorParameterValue(
                    TEXT("RaftInteriorWaterCenterAndHalfWidthCm"),
                    InteriorCenterAndWidth));
            Test->TestTrue(
                TEXT("raft-interior transmission forward parameter exists"),
                FoamOcclusion->GetVectorParameterValue(
                    TEXT("RaftInteriorWaterForwardAndHalfLengthCm"),
                    InteriorForwardAndLength));
            Test->TestEqual(
                TEXT("raft-present world enables the foam exclusion"),
                Enabled,
                1.0f);
            Test->TestEqual(
                TEXT("foam exclusion protects the seated-crew beam"),
                CenterAndWidth.A,
                190.0f);
            Test->TestEqual(
                TEXT("foam exclusion protects the deformed raft length"),
                ForwardAndLength.A,
                320.0f);
            Test->TestEqual(
                TEXT("raft-present world enables interior water transmission"),
                InteriorWaterEnabled,
                1.0f);
            Test->TestEqual(
                TEXT("transmission aperture clears the complete floor beam"),
                InteriorCenterAndWidth.A,
                82.0f);
            Test->TestEqual(
                TEXT("transmission aperture clears the complete floor length"),
                InteriorForwardAndLength.A,
                215.0f);
        }
    }

    UProceduralMeshComponent* Mesh =
        Surface->FindComponentByClass<UProceduralMeshComponent>();
    Test->TestNotNull(TEXT("surface has a procedural mesh"), Mesh);
    if (Mesh != nullptr)
    {
        Test->TestTrue(
            TEXT("surface mesh has a section built"), Mesh->GetNumSections() > 0);
        Test->TestTrue(
            TEXT("live surface uses its presentation-safe non-transmitting material"),
            Mesh->GetMaterial(0) != nullptr &&
                Mesh->GetMaterial(0)->GetPathName().Contains(
                    TEXT("M_RaftSim_LiveRiverSurface")));
        Test->TestEqual(
            TEXT("live surface uses a continuous alpha edge-transition material"),
            Mesh->GetMaterial(0)->GetBlendMode(),
            BLEND_Translucent);
        Test->TestFalse(
            TEXT("live solver overlay does not cast a duplicate moving-grid shadow"),
            Mesh->CastShadow);
        Test->TestEqual(
            TEXT("live solver overlay remains non-colliding"),
            Mesh->GetCollisionEnabled(),
            ECollisionEnabled::NoCollision);
        // A built water grid has non-trivial bounds over the tank footprint.
        const FBoxSphereBounds Bounds = Mesh->Bounds;
        Test->TestTrue(
            FString::Printf(TEXT("surface spans the tank (extent %.0f cm)"),
                Bounds.BoxExtent.X),
            Bounds.BoxExtent.X > 1000.0f);
        const FProcMeshSection* Section = Mesh->GetProcMeshSection(0);
        Test->TestNotNull(TEXT("surface exposes its authored mesh section"), Section);
        if (Section != nullptr && Section->ProcVertexBuffer.Num() >= 2)
        {
            const float StationUvStep = FMath::Abs(
                Section->ProcVertexBuffer[1].UV0.X -
                Section->ProcVertexBuffer[0].UV0.X);
            Test->TestTrue(
                FString::Printf(
                    TEXT("water UVs retain the three-metre river scale (step %.3f)"),
                    StationUvStep),
                FMath::IsNearlyEqual(StationUvStep, 1.0f, 0.01f));
            uint8 MinimumCoverage = 255;
            uint8 MaximumCoverage = 0;
            int32 TransitionalCoverageVertices = 0;
            for (const FProcMeshVertex& Vertex : Section->ProcVertexBuffer)
            {
                MinimumCoverage = FMath::Min(MinimumCoverage, Vertex.Color.A);
                MaximumCoverage = FMath::Max(MaximumCoverage, Vertex.Color.A);
                TransitionalCoverageVertices +=
                    Vertex.Color.A > 0 && Vertex.Color.A < 255 ? 1 : 0;
            }
            Test->TestEqual(
                TEXT("live surface reaches zero coverage at station edges"),
                MinimumCoverage,
                static_cast<uint8>(0));
            Test->TestEqual(
                TEXT("live surface reaches full coverage away from station edges"),
                MaximumCoverage,
                static_cast<uint8>(255));
            Test->TestTrue(
                TEXT("station and lateral edge feathers contain transitional coverage"),
                TransitionalCoverageVertices > 0);
        }
    }
    UProceduralMeshComponent* RapidFoamMesh = nullptr;
    UProceduralMeshComponent* LiveVolumeCoreMesh = nullptr;
    TArray<UProceduralMeshComponent*> ProceduralMeshes;
    Surface->GetComponents<UProceduralMeshComponent>(ProceduralMeshes);
    for (UProceduralMeshComponent* Candidate : ProceduralMeshes)
    {
        if (Candidate && Candidate->GetFName() == TEXT("RapidFoamMesh"))
        {
            RapidFoamMesh = Candidate;
        }
        if (Candidate && Candidate->GetFName() == TEXT("LiveVolumeCoreMesh"))
        {
            LiveVolumeCoreMesh = Candidate;
        }
    }
    Test->TestNotNull(
        TEXT("surface exposes a separate solver-conforming optical core"),
        LiveVolumeCoreMesh);
    if (LiveVolumeCoreMesh)
    {
        Test->TestEqual(
            TEXT("volume core remains non-colliding"),
            LiveVolumeCoreMesh->GetCollisionEnabled(),
            ECollisionEnabled::NoCollision);
        Test->TestFalse(
            TEXT("volume core does not cast a moving-grid shadow"),
            LiveVolumeCoreMesh->CastShadow);
        Test->TestTrue(
            TEXT("volume core binds the raft-transmission Single Layer Water parent"),
            LiveVolumeCoreMesh->GetMaterial(0) &&
                LiveVolumeCoreMesh->GetMaterial(0)->GetPathName().Contains(
                    TEXT("M_RaftSim_SouthForkRaftTransmissionWater")));
        Test->TestFalse(
            TEXT("dev tank does not opt into the river-wide optical core"),
            Surface->IsLiveVolumeCoreEnabled());
        Test->TestFalse(
            TEXT("disabled dev-tank optical core stays hidden"),
            Surface->IsLiveVolumeCoreVisible());
    }
    Test->TestNotNull(
        TEXT("surface exposes a separate solver-owned rapid-foam mesh"),
        RapidFoamMesh);
    if (RapidFoamMesh)
    {
        Test->TestEqual(
            TEXT("rapid foam remains non-colliding"),
            RapidFoamMesh->GetCollisionEnabled(),
            ECollisionEnabled::NoCollision);
        Test->TestFalse(
            TEXT("rapid foam does not cast a duplicate water shadow"),
            RapidFoamMesh->CastShadow);
        Test->TestTrue(
            TEXT("rapid foam uses the raft-occluded masked lace material"),
            RapidFoamMesh->GetMaterial(0) &&
                RapidFoamMesh->GetMaterial(0)->GetPathName().Contains(
                    TEXT("M_RaftSim_SolverFieldFoamCandidate")) &&
                RapidFoamMesh->GetMaterial(0)->GetBlendMode() == BLEND_Masked);
    }
    const FVector2D RapidCoordinateM(960.0f, 0.0f);
    const float FirstRapidWaveM =
        ARaftSimWaterSurfaceActor::ComputePresentationStandingWaveDisplacementMeters(
            RapidCoordinateM, 1.778f, 0.412f);
    const float SecondRapidWaveM =
        ARaftSimWaterSurfaceActor::ComputePresentationStandingWaveDisplacementMeters(
            RapidCoordinateM, 1.778f, 0.412f);
    Test->TestEqual(
        TEXT("presentation standing wave is deterministic"),
        FirstRapidWaveM,
        SecondRapidWaveM);
    Test->TestTrue(
        FString::Printf(
            TEXT("four-band rapid relief stays inside its 24.8 cm bound (%.3f m)"),
            FirstRapidWaveM),
        FMath::Abs(FirstRapidWaveM) <= 0.2481f);

    const float RefinedRapidWaveM =
        ARaftSimWaterSurfaceActor::ComputePresentationStandingWaveDisplacementMeters(
            RapidCoordinateM + FVector2D(1.5f, 0.0f), 1.778f, 0.412f);
    Test->TestTrue(
        FString::Printf(
            TEXT("refined grid resolves short river-coordinate rapid relief (delta %.4f m)"),
            FMath::Abs(RefinedRapidWaveM - FirstRapidWaveM)),
        FMath::Abs(RefinedRapidWaveM - FirstRapidWaveM) > 0.01f);

    const float CalmRippleM =
        ARaftSimWaterSurfaceActor::ComputePresentationStandingWaveDisplacementMeters(
            RapidCoordinateM, 0.0f, 2.0f);
    Test->TestTrue(
        FString::Printf(
            TEXT("calm water retains only the authored 1.8 cm ripple (%.3f m)"),
            CalmRippleM),
        FMath::Abs(CalmRippleM) <= 0.0181f);
    Test->TestFalse(
        TEXT("near-critical flow adds hydraulic standing-wave response"),
        FMath::IsNearlyEqual(FirstRapidWaveM, CalmRippleM, 1.0e-4f));

    const float SolverCrestReliefM =
        ARaftSimWaterSurfaceActor::ComputePresentationHydraulicReliefDisplacementMeters(
            -2.731f,
            -2.550f,
            -2.628f,
            -3.340f,
            -3.928f,
            1.778f,
            0.412f);
    Test->TestTrue(
        FString::Printf(
            TEXT("solver-resolved rapid crest receives positive relief (%.3f m)"),
            SolverCrestReliefM),
        SolverCrestReliefM > 0.12f && SolverCrestReliefM <= 0.26f);

    const float SolverHoleReliefM =
        ARaftSimWaterSurfaceActor::ComputePresentationHydraulicReliefDisplacementMeters(
            -3.928f,
            -2.731f,
            -3.340f,
            -3.967f,
            -4.078f,
            2.30f,
            0.119f);
    Test->TestTrue(
        FString::Printf(
            TEXT("solver-resolved rapid hole receives negative relief (%.3f m)"),
            SolverHoleReliefM),
        SolverHoleReliefM < -0.15f && SolverHoleReliefM >= -0.24f);
    const float PlanarReliefM =
        ARaftSimWaterSurfaceActor::ComputePresentationHydraulicReliefDisplacementMeters(
            10.0f,
            10.4f,
            10.2f,
            9.8f,
            9.6f,
            3.0f,
            0.5f);
    Test->TestTrue(
        FString::Printf(
            TEXT("linear river grade receives no invented hydraulic relief (%.6f m)"),
            PlanarReliefM),
        FMath::IsNearlyZero(PlanarReliefM, 1.0e-6f));
    const float CalmReliefM =
        ARaftSimWaterSurfaceActor::ComputePresentationHydraulicReliefDisplacementMeters(
            1.0f,
            0.5f,
            0.6f,
            0.6f,
            0.5f,
            0.0f,
            2.0f);
    Test->TestTrue(
        FString::Printf(
            TEXT("calm water receives no relief despite synthetic curvature (%.6f m)"),
            CalmReliefM),
        FMath::IsNearlyZero(CalmReliefM, 1.0e-6f));

    const float SmoothedStepM =
        ARaftSimWaterSurfaceActor::ComputePresentationSmoothedSurfaceHeightMeters(
            1.0f,
            0.0f,
            0.0f,
            0.0f,
            0.0f,
            0.72f);
    Test->TestTrue(
        FString::Printf(
            TEXT("presentation filter reduces a one-cell cooked step (%.4f m)"),
            SmoothedStepM),
        SmoothedStepM > 0.0f && SmoothedStepM < 1.0f);
    const float SmoothedPlaneM =
        ARaftSimWaterSurfaceActor::ComputePresentationSmoothedSurfaceHeightMeters(
            10.0f,
            10.6f,
            9.4f,
            10.2f,
            9.8f,
            0.72f);
    Test->TestTrue(
        FString::Printf(
            TEXT("presentation filter preserves a linear river plane (%.6f m)"),
            SmoothedPlaneM),
        FMath::IsNearlyEqual(SmoothedPlaneM, 10.0f, 1.0e-6f));
    const float DisabledSmoothingM =
        ARaftSimWaterSurfaceActor::ComputePresentationSmoothedSurfaceHeightMeters(
            1.0f,
            0.0f,
            0.0f,
            0.0f,
            0.0f,
            0.0f);
    Test->TestEqual(
        TEXT("zero smoothing strength returns the authoritative sample"),
        DisabledSmoothingM,
        1.0f);

    const FVector2D LipStart =
        ARaftSimWaterSurfaceActor::ComputeBreakingLipProfileCentimeters(0.0f, 1.0f);
    const FVector2D LipCrest =
        ARaftSimWaterSurfaceActor::ComputeBreakingLipProfileCentimeters(0.375f, 1.0f);
    const FVector2D LipNose =
        ARaftSimWaterSurfaceActor::ComputeBreakingLipProfileCentimeters(0.75f, 1.0f);
    const FVector2D LipCurl =
        ARaftSimWaterSurfaceActor::ComputeBreakingLipProfileCentimeters(1.0f, 1.0f);
    const FVector2D ModerateLipTail =
        ARaftSimWaterSurfaceActor::ComputeBreakingLipProfileCentimeters(1.0f, 0.35f);
    const FVector2D ModerateLipCrest =
        ARaftSimWaterSurfaceActor::ComputeBreakingLipProfileCentimeters(0.375f, 0.35f);
    const FVector2D ModerateLipShoulder =
        ARaftSimWaterSurfaceActor::ComputeBreakingLipProfileCentimeters(0.83f, 0.35f);
    Test->TestTrue(
        TEXT("breaking lip starts on the sampled free surface"),
        FMath::IsNearlyZero(LipStart.X, 0.01f) &&
            FMath::IsNearlyZero(LipStart.Y, 0.01f));
    Test->TestTrue(
        TEXT("breaking lip rises before its downstream nose"),
        LipCrest.Y > 100.0f && LipNose.X > LipCrest.X);
    Test->TestTrue(
        TEXT("breaking lip curls upstream and below the free surface"),
        LipCurl.X < LipNose.X && LipCurl.Y < 0.0f);
    Test->TestTrue(
        TEXT("breaking lip geometry remains inside its presentation bound"),
        LipNose.X <= 260.01f && FMath::Abs(LipCurl.Y) <= 105.01f);
    Test->TestTrue(
        TEXT("moderate hydraulic jumps form an attached roller and long surface tail"),
        ModerateLipCrest.Y > 20.0f && ModerateLipCrest.Y < 50.0f &&
            ModerateLipShoulder.Y > 5.0f &&
            ModerateLipTail.X > 300.0f && ModerateLipTail.X < 330.0f &&
            FMath::IsNearlyZero(ModerateLipTail.Y, 0.01f));

    const FVector2D RollerEntry =
        ARaftSimWaterSurfaceActor::
            ComputeBreakingRollerVolumeProfileCentimeters(0.0f, 0.35f, 0.0f);
    const FVector2D RollerCrown =
        ARaftSimWaterSurfaceActor::
            ComputeBreakingRollerVolumeProfileCentimeters(0.5f, 0.35f, 0.0f);
    const FVector2D RollerReturn =
        ARaftSimWaterSurfaceActor::
            ComputeBreakingRollerVolumeProfileCentimeters(1.0f, 0.35f, 0.0f);
    const FVector2D OuterRollerCrown =
        ARaftSimWaterSurfaceActor::
            ComputeBreakingRollerVolumeProfileCentimeters(0.5f, 0.35f, 1.0f);
    Test->TestTrue(
        TEXT("moderate jump roller forms an open multi-valued circulation loop"),
        RollerEntry.X > RollerCrown.X &&
            RollerReturn.X < RollerCrown.X &&
            RollerCrown.Y > 80.0f &&
            RollerEntry.Y < 0.0f && RollerReturn.Y < 0.0f);
    Test->TestTrue(
        TEXT("roller depth offsets support nested fallback shells"),
        OuterRollerCrown.Y > RollerCrown.Y + 25.0f &&
            OuterRollerCrown.X > RollerCrown.X + 40.0f);
    Test->TestTrue(
        TEXT("roller profile stays inside its bounded presentation envelope"),
        RollerEntry.X < 300.0f && RollerReturn.X > 50.0f &&
            OuterRollerCrown.Y < 130.0f);
    Test->TestTrue(
        TEXT("presentation edge clearance is zero on a sampled riverbank"),
        FMath::IsNearlyZero(
            ARaftSimWaterSurfaceActor::
                ComputePresentationSurfaceEdgeClearanceMeters(
                    40, 81, 0, 0, 20, 3.0f)));
    Test->TestTrue(
        TEXT("presentation edge clearance uses the nearest station or bank edge"),
        FMath::IsNearlyEqual(
            ARaftSimWaterSurfaceActor::
                ComputePresentationSurfaceEdgeClearanceMeters(
                    40, 81, 10, 0, 20, 3.0f),
            30.0f));
    TArray<ARaftSimWaterSurfaceActor::FBreakingSite> BreakingSites;
    Surface->GetBreakingSites(BreakingSites);
    for (const ARaftSimWaterSurfaceActor::FBreakingSite& Site : BreakingSites)
    {
        Test->TestTrue(
            TEXT("every visible breaking site is on full-coverage live water"),
            Site.PresentationCoverage >= 0.999f);
        Test->TestTrue(
            TEXT("every visible breaking site has hero-safe edge clearance"),
            Site.PresentationEdgeClearanceMeters >= 15.0f);
    }
    Test->TestTrue(
        TEXT("breaking lip population stays inside the 24-site triangle budget"),
        Surface->GetBreakingLipTriangleCount() <= 12288);
    Test->TestTrue(
        TEXT("breaking roller fallback stays inside its 24-site triangle budget"),
        Surface->GetBreakingRollerVolumeTriangleCount() <= 36288);
    return true;
}

} // namespace

bool FRaftSimWaterSurfaceRendersTest::RunTest(const FString&)
{
    AutomationOpenMap(TEXT("/Game/RaftSim/Maps/L_RaftSimTestTank"));
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(2.0f));
    ADD_LATENT_AUTOMATION_COMMAND(FRaftSimAssertWaterSurfaceCommand(this));
    return true;
}

#endif // WITH_AUTOMATION_TESTS
