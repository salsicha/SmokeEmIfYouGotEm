// P2 water-rendering v1 test: the water surface actor spawns with the raft,
// builds a procedural mesh, and its bounds track the live solver surface.

#include "Components/MeshComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Materials/MaterialParameterCollection.h"
#include "Materials/MaterialParameterCollectionInstance.h"
#include "Misc/AutomationTest.h"
#include "Math/Float16.h"
#include "ProceduralMeshComponent.h"
#include "RaftSimRaftActor.h"
#include "RaftSimWaterSurfaceActor.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "Tests/AutomationCommon.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimWaterBoilLongRunContinuityTest,
    "RaftSim.P2.WaterBoilLongRunContinuity",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext |
        EAutomationTestFlags::ProductFilter)

bool FRaftSimWaterBoilLongRunContinuityTest::RunTest(const FString&)
{
    for (float Seconds : {0.0f, 60.0f, 3600.0f, 14400.0f})
    {
        float MaxHeightChange = 0.0f;
        for (int32 Index = 0; Index < 128; ++Index)
        {
            const FVector2D River(8358.0 + Index * 0.271, -5.0 + Index * 0.083);
            const FVector2D Advection(40.0 + Index * 0.37, Index * 0.11);
            const float Height = URaftSimWaterRuntimeAdapter::ComputeCoupledLocalFluidHeightfieldMeters(
                River, Advection, 4.0f, 1.0f, Seconds, 1.0f, 1.0f);
            const float Shifted = URaftSimWaterRuntimeAdapter::ComputeCoupledLocalFluidHeightfieldMeters(
                River, Advection + FVector2D(0.01, 0.0), 4.0f, 1.0f, Seconds, 1.0f, 1.0f);
            MaxHeightChange = FMath::Max(MaxHeightChange, FMath::Abs(Shifted - Height));
        }
        // A centimetre of advection must not turn into decimetres of vertical
        // popping simply because the same run has been open for hours.
        TestTrue(FString::Printf(TEXT("1 cm advection remains continuous at %.0f s (max %.6f m)"),
            Seconds, MaxHeightChange), MaxHeightChange < 0.02f);
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimWaterSmoothingScaleTest,
    "RaftSim.P2.WaterSmoothingScale",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext |
        EAutomationTestFlags::ProductFilter)

bool FRaftSimWaterSmoothingScaleTest::RunTest(const FString&)
{
    // An 18 m wavelength on the actual 1.5 m carrier with 3 m analysis
    // neighbors. This measures filter attenuation, not visual acceptance.
    constexpr int32 Count = 12;
    TArray<float> Heights;
    for (int32 X = 0; X < Count; ++X)
    {
        Heights.Add(FMath::Cos(2.0f * PI * X / Count));
    }
    float TwoPassCrest = 0.0f;
    for (int32 Pass = 0; Pass < 16; ++Pass)
    {
        const TArray<float> Previous = Heights;
        for (int32 X = 0; X < Count; ++X)
        {
            Heights[X] = ARaftSimWaterSurfaceActor::ComputePresentationSmoothedSurfaceHeightMeters(
                Previous[X], Previous[(X + Count - 2) % Count],
                Previous[(X + 2) % Count], Previous[X], Previous[X], 1.0f);
        }
        if (Pass == 1)
        {
            TwoPassCrest = Heights[0];
        }
    }
    TestTrue(TEXT("two passes retain 56.25 percent of the 18 m crest"),
        FMath::IsNearlyEqual(TwoPassCrest, 0.5625f, 1.e-5f));
    TestTrue(TEXT("sixteen passes retain only about one percent"),
        FMath::IsNearlyEqual(Heights[0], FMath::Pow(0.75f, 16.0f), 1.e-5f));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimWaterDataLinearEncodingTest,
    "RaftSim.P2.WaterDataLinearEncoding",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext |
        EAutomationTestFlags::ProductFilter)

bool FRaftSimWaterDataLinearEncodingTest::RunTest(const FString&)
{
    UProceduralMeshComponent* Mesh = NewObject<UProceduralMeshComponent>();
    const TArray<FVector> Positions = {FVector(0,0,0), FVector(100,0,0), FVector(0,100,0)};
    const TArray<int32> Indices = {0,1,2};
    const TArray<FVector> Normals = {FVector::UpVector, FVector::UpVector, FVector::UpVector};
    const TArray<FVector2D> UV = {FVector2D(0,0), FVector2D(1,0), FVector2D(0,1)};
    const TArray<FProcMeshTangent> Tangents;
    const TArray<FLinearColor> Data = {
        FLinearColor(0.05f,0.25f,0.18f,1.0f),
        FLinearColor(0.0f,0.50f,0.01f,0.4f),
        FLinearColor(0.26f,1.0f,0.8f,0.0f)};
    Mesh->CreateMeshSection_LinearColor(0, Positions, Indices, Normals, UV, Data,
        Tangents, false, false);
    const FColor Initial = Mesh->GetProcMeshSection(0)->ProcVertexBuffer[0].Color;
    // Demonstrate the engine default that caused the first-update discontinuity.
    Mesh->UpdateMeshSection_LinearColor(0, Positions, Normals, UV, Data, Tangents);
    TestTrue(TEXT("default update incorrectly encodes data as display colour"),
        Mesh->GetProcMeshSection(0)->ProcVertexBuffer[0].Color.R > Initial.R * 4);
    for (int32 Frame = 0; Frame < 3; ++Frame)
    {
        Mesh->UpdateMeshSection_LinearColor(0, Positions, Normals, UV, Data, Tangents, false);
        for (int32 Index = 0; Index < Data.Num(); ++Index)
        {
            TestTrue(TEXT("foam depth speed and coverage remain identical to creation"),
                Mesh->GetProcMeshSection(0)->ProcVertexBuffer[Index].Color == Data[Index].ToFColor(false));
        }
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimSharedBreakingReliefTest,
    "RaftSim.P2.SharedBreakingRelief",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext |
        EAutomationTestFlags::ProductFilter)

bool FRaftSimSharedBreakingReliefTest::RunTest(const FString&)
{
    using FSite = URaftSimWaterRuntimeAdapter::FSupportBreakingSite;
    TArray<FSite> Sites;
    Sites.Add({FVector2D(300.0, 0.0), 0.8f});
    auto Height = [&Sites](float Station, float Lateral = 0.0f)
    {
        return URaftSimWaterRuntimeAdapter::ComputeCoupledBreakingReliefMeters(
            FVector2D(Station, Lateral), Sites, 0.22f, 1.0f);
    };
    TestEqual(TEXT("crest has one bounded owner, not the sum of raw detections"),
        Height(300.0f), 0.22f * 0.8f);
    TestTrue(TEXT("downstream toe is below the crest"), Height(301.0f) < 0.0f);
    TestEqual(TEXT("dry-side distant bank receives no breaking profile"), Height(300.0f, 20.0f), 0.0f);
    TestEqual(TEXT("profile is finite upstream"), Height(295.0f), 0.0f);
    TestEqual(TEXT("profile is finite downstream"), Height(323.0f), 0.0f);
    const float FullCrest = Height(300.0f);
    Sites[0].Intensity *= 0.5f;
    TestEqual(TEXT("persistent ownership fade affects the geometry continuously"),
        Height(300.0f), FullCrest * 0.5f);
    for (float Station = 298.0f; Station < 322.0f; Station += 1.0f)
    {
        TestTrue(TEXT("off-lattice support interpolates the same crest samples"),
            FMath::IsNearlyEqual(Height(Station + 0.5f),
                0.5f * (Height(Station) + Height(Station + 1.0f)), 1.e-5f));
    }
    const FSite OverlappingSite = Sites[0];
    Sites.Add(OverlappingSite);
    Sites.Add(OverlappingSite);
    Sites.Add(OverlappingSite);
    TestTrue(TEXT("overlapping owners cannot create an unbounded wall"),
        FMath::Abs(Height(300.0f)) <= 0.22f);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimWaterTexturePrecisionTest,
    "RaftSim.P2.WaterTexturePrecision",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext |
        EAutomationTestFlags::ProductFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimHydraulicCrestScaleTest,
    "RaftSim.P2.HydraulicCrestScale",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext |
        EAutomationTestFlags::ProductFilter)

bool FRaftSimHydraulicCrestScaleTest::RunTest(const FString&)
{
    using FAdapter = URaftSimWaterRuntimeAdapter;
    TestEqual(TEXT("subcritical flow creates no extra wave"),
        FAdapter::ComputeHydraulicCrestDimensionsMeters(1.0f, 0.9f, 0.0f), FVector2D::ZeroVector);
    TestEqual(TEXT("dry cells create no extra wave"),
        FAdapter::ComputeHydraulicCrestDimensionsMeters(0.01f, 3.0f, 0.0f), FVector2D::ZeroVector);
    const FVector2D Weak = FAdapter::ComputeHydraulicCrestDimensionsMeters(1.0f, 1.2f, 0.0f);
    TestTrue(TEXT("undular scale follows local depth, not foam strength"),
        FMath::IsNearlyEqual(Weak.X, 0.44, 1.e-5));
    TestTrue(TEXT("resolved rise is subtracted once"), FMath::IsNearlyEqual(
        FAdapter::ComputeHydraulicCrestDimensionsMeters(1.0f, 1.2f, 0.2f).X, 0.24, 1.e-5));
    TestEqual(TEXT("fully resolved rise is not doubled"),
        FAdapter::ComputeHydraulicCrestDimensionsMeters(1.0f, 1.2f, 0.6f).X, 0.0);
    for (float Depth : {0.1f, 0.5f, 1.0f, 4.0f})
    for (float Fr : {1.01f, 1.2f, 1.7f, 2.5f, 10.0f})
    {
        const FVector2D Dim = FAdapter::ComputeHydraulicCrestDimensionsMeters(Depth, Fr, -1.0f);
        TestTrue(TEXT("reconstruction is bounded by local depth and 1.2 m"),
            Dim.X >= 0.0 && Dim.X <= FMath::Min(0.8f * Depth, 1.2f) + 1.e-5);
        TestTrue(TEXT("face has bounded physical length"), Dim.Y >= 2.0 && Dim.Y <= 7.0);
    }
    TArray<FAdapter::FSupportBreakingSite> Sites;
    Sites.Add({FVector2D(300, 0), 0.1f, 0.44f, 3.0f});
    auto Height = [&Sites](float X, float Y = 0.0f)
    {
        return FAdapter::ComputeCoupledBreakingReliefMeters(FVector2D(X,Y), Sites, 0.22f, 1.0f);
    };
    TestTrue(TEXT("physical crest is not capped by legacy 22 cm"), Height(300) > 0.4f);
    TestTrue(TEXT("broad wave face extends upstream"), Height(298) > 0.2f);
    TestTrue(TEXT("downstream toe falls below mean surface"), Height(303) < 0.0f);
    TestEqual(TEXT("no wave outside lateral support"), Height(300, 13), 0.0f);
    TestEqual(TEXT("no wave upstream outside support"), Height(290), 0.0f);
    TestEqual(TEXT("no wave downstream outside support"), Height(322), 0.0f);
    const float FullHeight = Height(300);
    float Foam = -1.0f;
    Sites[0].SpillingFraction = 0.0f;
    FAdapter::ComputeCoupledBreakingReliefMeters(FVector2D(300,0), Sites, 0.22f, 1.0f, &Foam);
    TestEqual(TEXT("nonspilling undular crest stays green"), Foam, 0.0f);
    Sites[0].SpillingFraction = 1.0f;
    FAdapter::ComputeCoupledBreakingReliefMeters(FVector2D(300,0), Sites, 0.22f, 1.0f, &Foam);
    TestTrue(TEXT("spilling crest generates foam"), Foam > 0.8f);
    FAdapter::ComputeCoupledBreakingReliefMeters(FVector2D(297,0), Sites, 0.22f, 1.0f, &Foam);
    TestEqual(TEXT("upstream wave face is not painted white"), Foam, 0.0f);
    FAdapter::ComputeCoupledBreakingReliefMeters(FVector2D(303,0), Sites, 0.22f, 1.0f, &Foam);
    TestEqual(TEXT("toe does not create fresh foam"), Foam, 0.0f);
    Sites[0].PhysicalCrestHeightMeters *= 0.5f;
    TestTrue(TEXT("ownership release scales geometry continuously"),
        FMath::IsNearlyEqual(Height(300), FullHeight * 0.5f));
    for (float X = 290; X < 322; X += 0.1f)
        TestTrue(TEXT("continuous profile has no lattice jumps"), FMath::Abs(Height(X + 0.001f) - Height(X)) < 0.001f);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimSpatialBreakingLocalityTest,
    "RaftSim.P2.SpatialBreakingLocality",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimSpatialBreakingLocalityTest::RunTest(const FString&)
{
    using FAdapter = URaftSimWaterRuntimeAdapter;
    TArray<FAdapter::FSupportBreakingSite> Sites;
    Sites.Add({FVector2D(8358, 0), 0.3f, 0.1f, 3.0f, 0.6f, true});
    const auto DuplicateLocalSite = Sites[0];
    Sites.Add(DuplicateLocalSite);
    auto Height = [&Sites](float X, float Y = 0.0f)
    {
        return FAdapter::ComputeCoupledBreakingReliefMeters(FVector2D(X,Y), Sites, 0.22f, 1.5f);
    };
    const float LocalHeight = Height(8358);
    Sites.Add({FVector2D(8454, 0), 0.8f, 0.9f, 7.0f, 1.0f, true});
    TestTrue(TEXT("distant downstream wave cannot uncap overlapping local crests"),
        FMath::IsNearlyEqual(Height(8358), LocalHeight, 1.e-6f));
    Sites.Last().RiverCoordinatesMeters = FVector2D(8358, 40);
    TestTrue(TEXT("distant lateral wave cannot uncap overlapping local crests"),
        FMath::IsNearlyEqual(Height(8358), LocalHeight, 1.e-6f));
    for (float X = 8336; X < 8410; X += 0.7f)
    {
        TestTrue(TEXT("local evaluation remains bounded"), FMath::Abs(Height(X)) <= 0.10001f);
        TestTrue(TEXT("local envelope has no edge jump"), FMath::Abs(Height(X + 0.001f) - Height(X)) < 0.001f);
    }
    // The renderer evaluates a station subset; the raft evaluates the full
    // set. Omitted out-of-range sites must change neither height nor foam.
    for (float X = 8337.0f; X < 8507.0f; X += 1.5f)
    {
        TArray<FAdapter::FSupportBreakingSite> RowSites;
        for (const auto& Site : Sites)
        {
            const float Length = FMath::Clamp(Site.PhysicalCrestLengthMeters, 2.0f, 7.0f);
            if (X >= Site.RiverCoordinatesMeters.X - 3.0f * Length &&
                X <= Site.RiverCoordinatesMeters.X + 7.0f * Length)
                RowSites.Add(Site);
        }
        float FullFoam = 0.0f, RowFoam = 0.0f;
        const float FullHeight = FAdapter::ComputeCoupledBreakingReliefMeters(
            FVector2D(X, 0), Sites, 0.22f, 1.5f, &FullFoam);
        const float RowHeight = FAdapter::ComputeCoupledBreakingReliefMeters(
            FVector2D(X, 0), RowSites, 0.22f, 1.5f, &RowFoam);
        TestTrue(TEXT("row subset and full support height agree"), FMath::IsNearlyEqual(FullHeight, RowHeight, 1.e-6f));
        TestTrue(TEXT("row subset and full support foam agree"), FMath::IsNearlyEqual(FullFoam, RowFoam, 1.e-6f));
    }
    Sites.SetNum(2);
    for (auto& Site : Sites)
    {
        Site.Intensity = 0.25f;
        Site.PhysicalCrestHeightMeters = -1.0f;
    }
    const float LegacyLocalHeight = Height(8358);
    Sites.Add({FVector2D(8454, 0), 1.0f, 1.2f, 7.0f, 1.0f, true});
    TestTrue(TEXT("legacy profile also ignores distant overlap owners"),
        FMath::IsNearlyEqual(Height(8358), LegacyLocalHeight, 1.e-6f));
    TestTrue(TEXT("legacy local overlap respects faded intensity"), LegacyLocalHeight <= 0.05501f);
    return true;
}

bool FRaftSimWaterTexturePrecisionTest::RunTest(const FString&)
{
    for (const float Center : {0.0f, 8352.0f, 48900.0f})
    {
        const float Origin = ARaftSimWaterSurfaceActor::ComputeWaterTextureOriginMeters(Center);
        for (int32 Row = -200; Row <= 200; ++Row)
        {
            const float Station = Center + Row * 1.5f;
            const float PackedUV = FFloat16((Station - Origin) / 3.0f).GetFloat();
            const float RestoredStation = (PackedUV + Origin / 3.0f) * 3.0f;
            TestTrue(TEXT("half-precision carrier retains every 1.5 metre row"),
                FMath::IsNearlyEqual(RestoredStation, Station, 0.005f));
        }
    }
    const float BeforeOrigin = ARaftSimWaterSurfaceActor::ComputeWaterTextureOriginMeters(8254.5f);
    const float AfterOrigin = ARaftSimWaterSurfaceActor::ComputeWaterTextureOriginMeters(8257.5f);
    TestNotEqual(TEXT("test crosses an origin-rebase boundary"), BeforeOrigin, AfterOrigin);
    for (int32 Row = -100; Row <= 100; ++Row)
    {
        const float Station = 8256.0f + Row * 1.5f;
        const float BeforeUV = FFloat16((Station - BeforeOrigin) / 3.0f).GetFloat() + BeforeOrigin / 3.0f;
        const float AfterUV = FFloat16((Station - AfterOrigin) / 3.0f).GetFloat() + AfterOrigin / 3.0f;
        TestEqual(TEXT("recentering does not jump the water texture phase"), BeforeUV, AfterUV);
    }
    TestEqual(TEXT("regression reproduces old Troublemaker row collapse"),
        FFloat16(8352.0f / 3.0f).GetFloat(), FFloat16(8353.5f / 3.0f).GetFloat());
    return true;
}

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

    const FVector RaftMaskCenter(120.0f, -80.0f, 0.0f);
    const FVector RaftMaskForward(0.0f, 1.0f, 0.0f);
    const float HullCenterCoverage =
        ARaftSimWaterSurfaceActor::
            ComputeRaftHullSurfaceExclusion(
                RaftMaskCenter, RaftMaskCenter, RaftMaskForward);
    const float HullFeatherCoverage =
        ARaftSimWaterSurfaceActor::
            ComputeRaftHullSurfaceExclusion(
                RaftMaskCenter + RaftMaskForward * 320.0f,
                RaftMaskCenter,
                RaftMaskForward);
    const float HullOutsideCoverage =
        ARaftSimWaterSurfaceActor::
            ComputeRaftHullSurfaceExclusion(
                RaftMaskCenter + RaftMaskForward * 500.0f,
                RaftMaskCenter,
                RaftMaskForward);
    Test->TestTrue(
        TEXT("live hydraulic detail is fully transparent over the raft center"),
        FMath::IsNearlyZero(HullCenterCoverage));
    Test->TestTrue(
        TEXT("live hydraulic detail has a soft hull-edge feather"),
        HullFeatherCoverage > 0.0f && HullFeatherCoverage < 1.0f);
    Test->TestTrue(
        TEXT("live hydraulic detail remains fully visible beyond the raft"),
        FMath::IsNearlyEqual(HullOutsideCoverage, 1.0f));

    const FVector2D WakeBoatPosition = FVector2D::ZeroVector;
    const FVector2D WakeTravelDirection(1.0f, 0.0f);
    const float WakeArmAcrossMeters = 1.05f + 10.0f * 0.52f;
    const float PortWakeM =
        ARaftSimWaterSurfaceActor::ComputePaddleWakeDisplacementMeters(
            FVector2D(-10.0f, WakeArmAcrossMeters),
            WakeBoatPosition,
            WakeTravelDirection,
            1.0f,
            0.0f);
    const float StarboardWakeM =
        ARaftSimWaterSurfaceActor::ComputePaddleWakeDisplacementMeters(
            FVector2D(-10.0f, -WakeArmAcrossMeters),
            WakeBoatPosition,
            WakeTravelDirection,
            1.0f,
            0.0f);
    const float AdjacentWakeTroughM =
        ARaftSimWaterSurfaceActor::ComputePaddleWakeDisplacementMeters(
            FVector2D(-10.0f, WakeArmAcrossMeters + 2.0f),
            WakeBoatPosition,
            WakeTravelDirection,
            1.0f,
            0.0f);
    Test->TestTrue(
        TEXT("paddle wake produces equal geometry ripples on both sides"),
        PortWakeM > 0.005f &&
            FMath::IsNearlyEqual(PortWakeM, StarboardWakeM, 1.0e-6f));
    Test->TestTrue(
        TEXT("paddle wake alternates signed crests and troughs"),
        PortWakeM * AdjacentWakeTroughM < 0.0f);
    Test->TestTrue(
        TEXT("paddle wake geometry stays inside its 11 cm amplitude bound"),
        FMath::Abs(PortWakeM) <= 0.1101f &&
            FMath::Abs(AdjacentWakeTroughM) <= 0.1101f);
    Test->TestTrue(
        TEXT("paddle wake is absent ahead of the raft"),
        FMath::IsNearlyZero(
            ARaftSimWaterSurfaceActor::ComputePaddleWakeDisplacementMeters(
                FVector2D(5.0f, 0.0f),
                WakeBoatPosition,
                WakeTravelDirection,
                1.0f,
                0.0f)));
    Test->TestTrue(
        TEXT("zero paddling strength removes the geometry wake"),
        FMath::IsNearlyZero(
            ARaftSimWaterSurfaceActor::ComputePaddleWakeDisplacementMeters(
                FVector2D(-10.0f, WakeArmAcrossMeters),
                WakeBoatPosition,
                WakeTravelDirection,
                0.0f,
                0.0f)));

    constexpr float BoulderRadiusM = 1.5f;
    constexpr float BoulderWakeDownstreamM = 6.0f;
    const float BoulderWakeArmAcrossM =
        0.75f * BoulderRadiusM + 0.38f * BoulderWakeDownstreamM;
    const FVector2D PortBoulderWake =
        ARaftSimWaterSurfaceActor::ComputeBoulderWakePresentation(
            BoulderWakeDownstreamM,
            BoulderWakeArmAcrossM,
            BoulderRadiusM,
            1.4f,
            0.0f);
    const FVector2D StarboardBoulderWake =
        ARaftSimWaterSurfaceActor::ComputeBoulderWakePresentation(
            BoulderWakeDownstreamM,
            -BoulderWakeArmAcrossM,
            BoulderRadiusM,
            1.4f,
            0.0f);
    const FVector2D LaterAerationPhase =
        ARaftSimWaterSurfaceActor::ComputeBoulderWakePresentation(
            BoulderWakeDownstreamM,
            BoulderWakeArmAcrossM,
            BoulderRadiusM,
            1.4f,
            1.3f);
    const FVector2D BoulderWakeCenterline =
        ARaftSimWaterSurfaceActor::ComputeBoulderWakePresentation(
            BoulderWakeDownstreamM,
            0.0f,
            BoulderRadiusM,
            1.4f,
            0.0f);
    Test->TestTrue(
        TEXT("boulder wake forms symmetric downstream Y arms"),
        FMath::Abs(PortBoulderWake.X) > 0.01f &&
            FMath::IsNearlyEqual(
                PortBoulderWake.X, StarboardBoulderWake.X, 1.0e-6f) &&
            FMath::Abs(BoulderWakeCenterline.X) <
                0.15f * FMath::Abs(PortBoulderWake.X));
    Test->TestTrue(
        TEXT("boulder wake crest geometry remains locked to the obstruction"),
        FMath::IsNearlyEqual(
            PortBoulderWake.X, LaterAerationPhase.X, 1.0e-6f));
    Test->TestTrue(
        TEXT("boulder wake breaking crests generate bounded foam"),
        FMath::Min(PortBoulderWake.Y, LaterAerationPhase.Y) > 0.25f &&
            PortBoulderWake.Y >= 0.0f && PortBoulderWake.Y <= 1.0f &&
            LaterAerationPhase.Y >= 0.0f && LaterAerationPhase.Y <= 1.0f);
    Test->TestTrue(
        TEXT("boulder wake remains inside its 24 cm displacement bound"),
        FMath::Abs(PortBoulderWake.X) <= 0.2401f &&
            FMath::Abs(LaterAerationPhase.X) <= 0.2401f);
    Test->TestTrue(
        TEXT("boulder wake cannot appear upstream of the obstruction"),
        ARaftSimWaterSurfaceActor::ComputeBoulderWakePresentation(
            -2.0f, 0.0f, BoulderRadiusM, 1.4f, 0.0f).IsNearlyZero());
    const float BoulderPillowM = URaftSimWaterRuntimeAdapter::
        ComputeCoupledBoulderPillowDisplacementMeters(
            -1.1f * BoulderRadiusM,
            0.0f,
            BoulderRadiusM,
            1.8f);
    Test->TestTrue(
        TEXT("boulder nose forms a positive pressure pillow"),
        BoulderPillowM > 0.10f && BoulderPillowM <= 0.2201f);
    // Moderate drift current must still read: the raft passes Meat
    // Grinder's exposed boulders at ~0.8 m/s, and the pillow there has to
    // be visible, not the ~2 cm the old 0.45-1.65 ramp allowed.
    const float ModerateCurrentPillowM = URaftSimWaterRuntimeAdapter::
        ComputeCoupledBoulderPillowDisplacementMeters(
            -1.1f * BoulderRadiusM,
            0.0f,
            BoulderRadiusM,
            0.8f);
    Test->TestTrue(
        TEXT("boulder pillow stays readable in moderate drift current"),
        ModerateCurrentPillowM > 0.04f &&
            ModerateCurrentPillowM < BoulderPillowM);
    // Slow bank-edge drift past a pool rock still guarantees a readable
    // minimum mound; dead-still water guarantees none.
    const float SlowDriftPillowM = URaftSimWaterRuntimeAdapter::
        ComputeCoupledBoulderPillowDisplacementMeters(
            -1.1f * BoulderRadiusM, 0.0f, BoulderRadiusM, 0.3f);
    Test->TestTrue(
        TEXT("boulder pillow keeps a readable floor in slow drift"),
        SlowDriftPillowM > 0.03f &&
            SlowDriftPillowM <= ModerateCurrentPillowM);
    Test->TestTrue(
        TEXT("still water forms no pillow"),
        FMath::IsNearlyZero(
            URaftSimWaterRuntimeAdapter::
                ComputeCoupledBoulderPillowDisplacementMeters(
                    -1.1f * BoulderRadiusM, 0.0f, BoulderRadiusM, 0.05f)));
    Test->TestTrue(
        TEXT("boulder pressure pillow does not appear downstream"),
        FMath::IsNearlyZero(
            URaftSimWaterRuntimeAdapter::
                ComputeCoupledBoulderPillowDisplacementMeters(
                    1.1f * BoulderRadiusM,
                    0.0f,
                    BoulderRadiusM,
                    1.8f)));

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
            FLinearColor FoamAdvectionMeters = FLinearColor::Transparent;
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
                TEXT("solver-current foam advection parameter exists"),
                FoamOcclusion->GetVectorParameterValue(
                    TEXT("RaftSimFoamAdvectionMeters"),
                    FoamAdvectionMeters));
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

    const FVector2D AdvancedFoamMeters =
        ARaftSimWaterSurfaceActor::AdvanceFoamTextureAdvectionMeters(
            FVector2D(10.0f, 2.0f),
            FVector2D(1.5f, -0.2f),
            2.0f);
    Test->TestTrue(
        TEXT("foam texture phase integrates the physical river velocity"),
        AdvancedFoamMeters.Equals(FVector2D(13.0f, 1.6f), 1.0e-5f));
    const float RisingFoamCoverage =
        ARaftSimWaterSurfaceActor::SmoothRapidFoamCoverage(
            0.0f, 1.0f, 1.0f / 15.0f);
    const float FallingFoamCoverage =
        ARaftSimWaterSurfaceActor::SmoothRapidFoamCoverage(
            0.10f, 0.0f, 1.0f / 15.0f);
    Test->TestTrue(
        TEXT("new foam responds within one surface refresh"),
        RisingFoamCoverage > 0.0f && RisingFoamCoverage < 1.0f);
    Test->TestTrue(
        TEXT("marginal foam does not flash below the mask in one refresh"),
        FallingFoamCoverage > 0.09f && FallingFoamCoverage < 0.10f);
    const float DecayedFoamCoverage =
        ARaftSimWaterSurfaceActor::SmoothRapidFoamCoverage(
            0.10f, 0.0f, 2.0f);
    Test->TestTrue(
        TEXT("foam remains above the stable lace clip during a two-second decay"),
        DecayedFoamCoverage > 0.01f && DecayedFoamCoverage < 0.10f);

    UProceduralMeshComponent* Mesh =
        Surface->FindComponentByClass<UProceduralMeshComponent>();
    Test->TestNotNull(TEXT("surface has a procedural mesh"), Mesh);
    if (Mesh != nullptr)
    {
        Test->TestTrue(
            TEXT("surface mesh has base and physical paddle-wake sections"),
            Mesh->GetNumSections() > 1);
        Test->TestTrue(
            TEXT("paddle-wake section uses the texture-free ripple material"),
            Mesh->GetMaterial(1) != nullptr &&
                Mesh->GetMaterial(1)->GetPathName().Contains(
                    TEXT("M_RaftSim_PaddleWakeRipple")));
        Test->TestEqual(
            TEXT("paddle-wake ripple uses translucent water shading"),
            Mesh->GetMaterial(1)->GetBlendMode(),
            BLEND_Translucent);
        Test->TestFalse(
            TEXT("paddle-wake section stays hidden without paddling"),
            Mesh->IsMeshSectionVisible(1));
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
    UProceduralMeshComponent* BreakingRollerVolumeMesh = nullptr;
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
        if (Candidate && Candidate->GetFName() == TEXT("BreakingRollerVolumeMesh"))
        {
            BreakingRollerVolumeMesh = Candidate;
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
    Test->TestNotNull(
        TEXT("surface exposes a separate connected breaking-water curtain"),
        BreakingRollerVolumeMesh);
    if (BreakingRollerVolumeMesh)
    {
        Test->TestEqual(
            TEXT("connected breaking-water curtain remains non-colliding"),
            BreakingRollerVolumeMesh->GetCollisionEnabled(),
            ECollisionEnabled::NoCollision);
        Test->TestTrue(
            TEXT("connected breaking-water curtain uses masked aerated foam lace"),
            BreakingRollerVolumeMesh->GetMaterial(0) &&
                BreakingRollerVolumeMesh->GetMaterial(0)->GetPathName().Contains(
                    TEXT("M_RaftSim_SolverFieldFoamCandidate")) &&
                BreakingRollerVolumeMesh->GetMaterial(0)->GetBlendMode() ==
                    BLEND_Masked);
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
            TEXT("localized rapid relief stays inside its 16.8 cm bound (%.3f m)"),
            FirstRapidWaveM),
        FMath::Abs(FirstRapidWaveM) <= 0.1681f);

    const float RefinedRapidWaveM =
        ARaftSimWaterSurfaceActor::ComputePresentationStandingWaveDisplacementMeters(
            RapidCoordinateM + FVector2D(1.5f, 0.0f), 1.778f, 0.412f);
    Test->TestTrue(
        FString::Printf(
            TEXT("refined grid resolves phase-warped river-coordinate relief (delta %.4f m)"),
            FMath::Abs(RefinedRapidWaveM - FirstRapidWaveM)),
        FMath::Abs(RefinedRapidWaveM - FirstRapidWaveM) > 0.004f);

    const float FormerRepeatRapidWaveM =
        ARaftSimWaterSurfaceActor::ComputePresentationStandingWaveDisplacementMeters(
            RapidCoordinateM + FVector2D(2.0f * UE_PI / 0.19f, 0.0f),
            5.0f,
            0.5f);
    const float EnergeticRapidWaveM =
        ARaftSimWaterSurfaceActor::ComputePresentationStandingWaveDisplacementMeters(
            RapidCoordinateM, 5.0f, 0.5f);
    Test->TestTrue(
        FString::Printf(
            TEXT("rapid relief does not repeat at the former dominant wavelength (delta %.4f m)"),
            FMath::Abs(FormerRepeatRapidWaveM - EnergeticRapidWaveM)),
        FMath::Abs(FormerRepeatRapidWaveM - EnergeticRapidWaveM) > 0.01f);

    const float CalmRippleM =
        ARaftSimWaterSurfaceActor::ComputePresentationStandingWaveDisplacementMeters(
            RapidCoordinateM, 0.0f, 2.0f);
    Test->TestTrue(
        FString::Printf(
            TEXT("calm water retains only the authored split 1.8 cm ripple (%.3f m)"),
            CalmRippleM),
        FMath::Abs(CalmRippleM) <= 0.0181f);
    Test->TestFalse(
        TEXT("near-critical flow adds hydraulic standing-wave response"),
        FMath::IsNearlyEqual(FirstRapidWaveM, CalmRippleM, 1.0e-4f));

    const float LocalFluidA = URaftSimWaterRuntimeAdapter::
        ComputeCoupledLocalFluidHeightfieldMeters(
            RapidCoordinateM, FVector2D::ZeroVector,
            5.0f, 0.5f, 1.0f, 0.65f);
    const float LocalFluidB = URaftSimWaterRuntimeAdapter::
        ComputeCoupledLocalFluidHeightfieldMeters(
            RapidCoordinateM, FVector2D(1.0f, 0.2f),
            5.0f, 0.5f, 1.4f, 0.65f);
    Test->TestTrue(
        TEXT("raft-local fluid heightfield has bounded evolving 3D relief"),
        FMath::Abs(LocalFluidA) <= 0.79f &&
            FMath::Abs(LocalFluidB) <= 0.79f &&
            !FMath::IsNearlyEqual(LocalFluidA, LocalFluidB, 1.0e-4f));
    float MaximumWhitewaterReliefM = 0.0f;
    for (int32 StationStep = 0; StationStep < 80; ++StationStep)
    {
        for (int32 LateralStep = 0; LateralStep < 20; ++LateralStep)
        {
            const FVector2D WhitewaterCoordinate(
                900.0f + StationStep * 0.75f,
                -7.5f + LateralStep * 0.75f);
            MaximumWhitewaterReliefM = FMath::Max(
                MaximumWhitewaterReliefM,
                URaftSimWaterRuntimeAdapter::
                    ComputeCoupledLocalFluidHeightfieldMeters(
                        WhitewaterCoordinate,
                        FVector2D::ZeroVector,
                        5.0f, 0.5f, 1.3f, 0.95f,
                        /*HydraulicFeatureEnergy=*/1.0f));
        }
    }
    Test->TestTrue(
        FString::Printf(
            TEXT("solver-confirmed whitewater develops tall breaking relief (%.3f m)"),
            MaximumWhitewaterReliefM),
        MaximumWhitewaterReliefM > 0.45f &&
            MaximumWhitewaterReliefM <= 0.75f);
    Test->TestTrue(
        TEXT("raft-local fluid heightfield stays flat in still water"),
        FMath::IsNearlyZero(
            URaftSimWaterRuntimeAdapter::
                ComputeCoupledLocalFluidHeightfieldMeters(
                    RapidCoordinateM, FVector2D::ZeroVector,
                    0.0f, 2.0f, 1.0f, 0.65f),
            1.0e-6f));

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

    const float SlowStitchedCrestReliefM =
        ARaftSimWaterSurfaceActor::ComputePresentationHydraulicReliefDisplacementMeters(
            -2.731f,
            -2.550f,
            -2.628f,
            -3.340f,
            -3.928f,
            0.20f,
            0.412f);
    Test->TestTrue(
        FString::Printf(
            TEXT("resolved ledge remains visible with slow stitched velocity (%.3f m)"),
            SlowStitchedCrestReliefM),
        SlowStitchedCrestReliefM > 0.10f &&
            SlowStitchedCrestReliefM <= 0.30f);
    const float SlowStitchedFeatureEnergy =
        URaftSimWaterRuntimeAdapter::ComputeCoupledHydraulicFeatureEnergy(
            RapidCoordinateM, SlowStitchedCrestReliefM);
    Test->TestTrue(
        TEXT("resolved slow-water ledge energizes irregular rapid lobes"),
        SlowStitchedFeatureEnergy > 0.0f &&
            SlowStitchedFeatureEnergy <= 1.0f);

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
    const float RapidGradeWaveM =
        URaftSimWaterRuntimeAdapter::ComputeCoupledRapidGradeWaveMeters(
            RapidCoordinateM, 10.3f, 9.7f, 0.9f);
    Test->TestTrue(
        FString::Printf(
            TEXT("moving 0.6 m rapid grade produces bounded crest relief (%.3f m)"),
            RapidGradeWaveM),
        FMath::Abs(RapidGradeWaveM) > 0.01f &&
            FMath::Abs(RapidGradeWaveM) <= 0.26f);
    Test->TestTrue(
        TEXT("the same rapid grade stays flat without current"),
        FMath::IsNearlyZero(
            URaftSimWaterRuntimeAdapter::ComputeCoupledRapidGradeWaveMeters(
                RapidCoordinateM, 10.3f, 9.7f, 0.0f),
            1.0e-6f));
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
    const FVector2D PlungePocket =
        ARaftSimWaterSurfaceActor::ComputeBreakingPlungePocketPresentation(
            1.8f, 0.0f, 1.0f);
    const FVector2D JumpDrawdown =
        ARaftSimWaterSurfaceActor::ComputeBreakingPlungePocketPresentation(
            -2.1f, 0.0f, 1.0f);
    const FVector2D CurlingJumpLip =
        ARaftSimWaterSurfaceActor::ComputeBreakingPlungePocketPresentation(
            -0.25f, 0.0f, 1.0f);
    const FVector2D AeratedReturn =
        ARaftSimWaterSurfaceActor::ComputeBreakingPlungePocketPresentation(
            5.0f, 0.0f, 1.0f);
    const FVector2D BrokenShoulder =
        ARaftSimWaterSurfaceActor::ComputeBreakingPlungePocketPresentation(
            2.3f, 3.0f, 1.0f);
    const FVector2D DisabledPlungePocket =
        ARaftSimWaterSurfaceActor::ComputeBreakingPlungePocketPresentation(
            1.8f, 0.0f, 0.0f);
    Test->TestTrue(
        TEXT("breaking jump forms a bounded dark plunge pocket"),
        PlungePocket.X < -0.24f && PlungePocket.X >= -0.2801f &&
            PlungePocket.Y < AeratedReturn.Y);
    Test->TestTrue(
        TEXT("breaking jump connects upstream drawdown to an aerated curling lip"),
        JumpDrawdown.X < -0.03f &&
            CurlingJumpLip.X > 0.02f && CurlingJumpLip.Y > 0.45f);
    Test->TestTrue(
        TEXT("breaking jump rises into a strongly aerated downstream return"),
        AeratedReturn.X > 0.08f && AeratedReturn.X <= 0.1601f &&
            AeratedReturn.Y > 0.75f);
    Test->TestTrue(
        TEXT("breaking jump keeps a broken aerated side shoulder"),
        BrokenShoulder.Y > PlungePocket.Y &&
            BrokenShoulder.X > PlungePocket.X);
    Test->TestTrue(
        TEXT("zero-intensity jumps add no plunge-pocket presentation"),
        DisabledPlungePocket.IsNearlyZero());
    const FVector2D DownstreamBoil =
        ARaftSimWaterSurfaceActor::ComputeBreakingDownstreamBoilPresentation(
            7.2f, -0.8f, 1.0f, 0.0f, 0.0f);
    const FVector2D AnimatedDownstreamBoil =
        ARaftSimWaterSurfaceActor::ComputeBreakingDownstreamBoilPresentation(
            7.2f, -0.8f, 1.0f, 0.9f, 0.0f);
    const FVector2D UpstreamBoil =
        ARaftSimWaterSurfaceActor::ComputeBreakingDownstreamBoilPresentation(
            2.0f, 0.0f, 1.0f, 0.0f, 0.0f);
    const FVector2D FarTailBoil =
        ARaftSimWaterSurfaceActor::ComputeBreakingDownstreamBoilPresentation(
            24.0f, 0.0f, 1.0f, 0.0f, 0.0f);
    const FVector2D DisabledDownstreamBoil =
        ARaftSimWaterSurfaceActor::ComputeBreakingDownstreamBoilPresentation(
            7.2f, -0.8f, 0.0f, 0.0f, 0.0f);
    Test->TestTrue(
        TEXT("accepted jumps form bounded asymmetric downstream boil relief"),
        FMath::Abs(DownstreamBoil.X) > 0.01f &&
            DownstreamBoil.X >= -0.0451f && DownstreamBoil.X <= 0.0701f &&
            DownstreamBoil.Y >= 0.0f && DownstreamBoil.Y <= 0.3801f);
    Test->TestTrue(
        TEXT("downstream boil microrelief evolves without translating authority"),
        FMath::Abs(AnimatedDownstreamBoil.X - DownstreamBoil.X) > 0.001f);
    Test->TestTrue(
        TEXT("boil microrelief cannot appear upstream or beyond its tailwater bound"),
        UpstreamBoil.IsNearlyZero() && FarTailBoil.IsNearlyZero());
    Test->TestTrue(
        TEXT("zero-intensity jumps add no downstream boil presentation"),
        DisabledDownstreamBoil.IsNearlyZero());
    const FVector2D RollerSurfaceReturn =
        ARaftSimWaterSurfaceActor::
            ComputeBreakingRollerSurfaceVelocityMetersPerSecond(
                4.4f, 0.0f, 1.0f, 2.0f);
    const FVector2D RiverLeftRollerConvergence =
        ARaftSimWaterSurfaceActor::
            ComputeBreakingRollerSurfaceVelocityMetersPerSecond(
                4.4f, 2.4f, 1.0f, 2.0f);
    const FVector2D RiverRightRollerConvergence =
        ARaftSimWaterSurfaceActor::
            ComputeBreakingRollerSurfaceVelocityMetersPerSecond(
                4.4f, -2.4f, 1.0f, 2.0f);
    Test->TestTrue(
        TEXT("hydraulic roller foam returns upstream at the impact toe"),
        RollerSurfaceReturn.X < -1.0f &&
            FMath::IsNearlyZero(RollerSurfaceReturn.Y));
    Test->TestTrue(
        TEXT("hydraulic roller surface flow converges into the aerated core"),
        RiverLeftRollerConvergence.Y < 0.0f &&
            RiverRightRollerConvergence.Y > 0.0f);
    Test->TestTrue(
        TEXT("hydraulic roller return is bounded to accepted jump tailwater"),
        ARaftSimWaterSurfaceActor::
            ComputeBreakingRollerSurfaceVelocityMetersPerSecond(
                18.0f, 0.0f, 1.0f, 2.0f).IsNearlyZero() &&
        ARaftSimWaterSurfaceActor::
            ComputeBreakingRollerSurfaceVelocityMetersPerSecond(
                4.4f, 0.0f, 0.0f, 2.0f).IsNearlyZero());
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
    const float StraightBankCoverage =
        ARaftSimWaterSurfaceActor::ComputePresentationBankCoverage(
            128.0f, 1, 0, 20, 1.5f, 4.5f, false, 0.90f);
    const float NaturalRiverRightCoverage =
        ARaftSimWaterSurfaceActor::ComputePresentationBankCoverage(
            128.0f, 1, 0, 20, 1.5f, 4.5f, true, 0.90f);
    const float NaturalRiverLeftCoverage =
        ARaftSimWaterSurfaceActor::ComputePresentationBankCoverage(
            128.0f, 19, 0, 20, 1.5f, 4.5f, true, 0.90f);
    Test->TestTrue(
        TEXT("disabled bank naturalism preserves the existing one-third feather"),
        FMath::IsNearlyEqual(StraightBankCoverage, 7.0f / 27.0f, 1.0e-5f));
    Test->TestFalse(
        TEXT("enabled bank naturalism shifts the visual contour in station space"),
        FMath::IsNearlyEqual(
            NaturalRiverRightCoverage, StraightBankCoverage, 1.0e-3f));
    Test->TestFalse(
        TEXT("river-left and river-right presentation profiles are not mirrored"),
        FMath::IsNearlyEqual(
            NaturalRiverLeftCoverage, NaturalRiverRightCoverage, 1.0e-3f));
    Test->TestTrue(
        TEXT("bank naturalism never covers the outermost solver-wet vertex"),
        FMath::IsNearlyZero(
            ARaftSimWaterSurfaceActor::ComputePresentationBankCoverage(
                128.0f, 0, 0, 20, 1.5f, 4.5f, true, 0.90f)));
    Test->TestTrue(
        TEXT("rapid displacement is pinned at both sampled shore vertices"),
        FMath::IsNearlyZero(
            ARaftSimWaterSurfaceActor::
                ComputePresentationShoreDisplacementWeight(
                    0, 0, 20, 1.5f)) &&
        FMath::IsNearlyZero(
            ARaftSimWaterSurfaceActor::
                ComputePresentationShoreDisplacementWeight(
                    20, 0, 20, 1.5f)));
    const float FirstInteriorShoreWeight =
        ARaftSimWaterSurfaceActor::
            ComputePresentationShoreDisplacementWeight(
                1, 0, 20, 1.5f);
    Test->TestTrue(
        TEXT("rapid displacement eases through the first interior bank row"),
        FirstInteriorShoreWeight > 0.0f &&
            FirstInteriorShoreWeight < 0.25f);
    Test->TestTrue(
        TEXT("rapid displacement recovers fully inside the third bank row"),
        FMath::IsNearlyEqual(
            ARaftSimWaterSurfaceActor::
                ComputePresentationShoreDisplacementWeight(
                    3, 0, 20, 1.5f),
            1.0f));
    Test->TestTrue(
        TEXT("an in-channel boulder remains hydraulic"),
        ARaftSimWaterSurfaceActor::IsBoulderFootprintHydraulicallyExposed(
            3.0f, 2.0f, -18.0f, 18.0f, 1.5f));
    Test->TestFalse(
        TEXT("a boulder centred on the river-right wet edge cannot make a ghost wake"),
        ARaftSimWaterSurfaceActor::IsBoulderFootprintHydraulicallyExposed(
            -18.0f, 1.0f, -18.0f, 18.0f, 1.5f));
    Test->TestFalse(
        TEXT("a boulder centred on the river-left wet edge cannot make a ghost wake"),
        ARaftSimWaterSurfaceActor::IsBoulderFootprintHydraulicallyExposed(
            18.0f, 1.0f, -18.0f, 18.0f, 1.5f));
    Test->TestFalse(
        TEXT("invalid wet extents cannot admit a hydraulic boulder"),
        ARaftSimWaterSurfaceActor::IsBoulderFootprintHydraulicallyExposed(
            0.0f, 1.0f, 18.0f, -18.0f, 1.5f));
    const float RiverRightRetreat =
        ARaftSimWaterSurfaceActor::ComputePresentationBankRetreatMeters(
            128.0f, false, 1.5f, true, 0.90f);
    const float RiverLeftRetreat =
        ARaftSimWaterSurfaceActor::ComputePresentationBankRetreatMeters(
            128.0f, true, 1.5f, true, 0.90f);
    Test->TestTrue(
        TEXT("natural bank retreat stays inward and inside one render cell"),
        RiverRightRetreat > 0.0f && RiverRightRetreat <= 1.20f &&
            RiverLeftRetreat > 0.0f && RiverLeftRetreat <= 1.20f);
    Test->TestFalse(
        TEXT("the two optical-core bank retreats use independent profiles"),
        FMath::IsNearlyEqual(RiverRightRetreat, RiverLeftRetreat, 1.0e-3f));
    Test->TestTrue(
        TEXT("disabled optical-core bank retreat is exactly zero"),
        FMath::IsNearlyZero(
            ARaftSimWaterSurfaceActor::ComputePresentationBankRetreatMeters(
                128.0f, false, 1.5f, false, 0.90f)));
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
        TEXT("connected breaking curtain stays inside its three-site triangle budget"),
        Surface->GetBreakingRollerVolumeTriangleCount() <= 3132);
    Test->TestTrue(
        TEXT("connected breaking curtain stays inside its three-site vertex budget"),
        Surface->GetBreakingRollerVolumeVertexCount() <= 1710);
    Test->TestTrue(
        TEXT("connected breaking curtain never exceeds forty centimetres thickness"),
        Surface->GetBreakingRollerVolumeMaximumThicknessCm() <= 40.01f);
    Test->TestTrue(
        TEXT("downstream boil presentation stays inside its three-site budget"),
        Surface->GetActiveDownstreamBoilSiteCount() <= 3);
    Test->TestTrue(
        TEXT("combined downstream boil relief stays inside seven centimetres"),
        Surface->GetMaximumAbsoluteDownstreamBoilDisplacementMeters() <= 0.0701f);
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
