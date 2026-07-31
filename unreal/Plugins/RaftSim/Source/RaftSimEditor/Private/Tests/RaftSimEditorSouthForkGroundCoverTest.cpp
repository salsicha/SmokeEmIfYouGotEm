#include "Environment/RaftSimEditorEnvironmentInternal.h"

#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimSouthForkOrganicGroundPresentationTest,
    "RaftSim.M9.EGroundCoverOrganicPresentation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimSouthForkOrganicGroundPresentationTest::RunTest(
    const FString& Parameters)
{
    using namespace RaftSimEditorEnvironment;

    constexpr int32 Width = 5;
    constexpr int32 Height = 5;
    TArray<FVector> PlaneVertices;
    PlaneVertices.Reserve(Width * Height);
    for (int32 Row = 0; Row < Height; ++Row)
    {
        for (int32 Column = 0; Column < Width; ++Column)
        {
            const float X = Column * 400.0f;
            const float Y = Row * 400.0f;
            PlaneVertices.Add(FVector(X, Y, X * 0.10f + Y * 0.20f));
        }
    }
    const TArray<FVector> Normals =
        BuildSouthForkSmoothedTerrainPresentationNormals(
            PlaneVertices, Width, Height, /*Radius=*/2);
    const FVector ExpectedNormal = FVector(-0.10f, -0.20f, 1.0f).GetSafeNormal();
    TestEqual(TEXT("Every DEM vertex receives a presentation normal"),
        Normals.Num(), PlaneVertices.Num());
    for (const FVector& Normal : Normals)
    {
        TestTrue(TEXT("Broad derivatives retain the source plane normal"),
            Normal.Equals(ExpectedNormal, 0.001f));
        TestTrue(TEXT("Terrain presentation normals face upward"), Normal.Z > 0.0f);
    }
    TestTrue(TEXT("Invalid terrain grids fail without partial output"),
        BuildSouthForkSmoothedTerrainPresentationNormals(
            PlaneVertices, Width - 1, Height, 2).IsEmpty());

    const FLinearColor RepresentativeDensity(0.55f, 0.68f, 0.35f, 0.72f);
    const FVector GroundLocation(125000.0f, -84000.0f, 4200.0f);
    FSouthForkGroundCoverPlacement Accepted;
    int32 AcceptedCoordinate = INDEX_NONE;
    for (int32 CoordinateIndex = 0; CoordinateIndex < 2048; ++CoordinateIndex)
    {
        Accepted = ComputeSouthForkGroundCoverPlacement(
            CoordinateIndex, 72, 56.0f, 0.12f,
            RepresentativeDensity, GroundLocation);
        if (Accepted.bAccepted)
        {
            AcceptedCoordinate = CoordinateIndex;
            break;
        }
    }
    TestTrue(TEXT("Representative dry bank admits a grass patch"),
        AcceptedCoordinate != INDEX_NONE);
    TestTrue(TEXT("An accepted sample expands into a visible compact patch"),
        Accepted.ClusterCount >= 3 && Accepted.ClusterCount <= 6);
    const FSouthForkGroundCoverPlacement Repeated =
        ComputeSouthForkGroundCoverPlacement(
            AcceptedCoordinate, 72, 56.0f, 0.12f,
            RepresentativeDensity, GroundLocation);
    TestTrue(TEXT("Ground-cover placement is deterministic"),
        Repeated.bAccepted == Accepted.bAccepted &&
            Repeated.ClusterCount == Accepted.ClusterCount &&
            FMath::IsNearlyEqual(Repeated.BaseScale, Accepted.BaseScale));

    TestFalse(TEXT("Grass stays out of the wetted shoreline corridor"),
        ComputeSouthForkGroundCoverPlacement(
            17, 72, 18.0f, 0.12f,
            RepresentativeDensity, GroundLocation).bAccepted);
    TestFalse(TEXT("Grass stays off implausibly steep DEM faces"),
        ComputeSouthForkGroundCoverPlacement(
            17, 72, 56.0f, 0.50f,
            RepresentativeDensity, GroundLocation).bAccepted);

    return true;
}

#endif
