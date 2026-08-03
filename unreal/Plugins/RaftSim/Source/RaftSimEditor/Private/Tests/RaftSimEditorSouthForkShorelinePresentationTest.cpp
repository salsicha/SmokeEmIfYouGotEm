#include "Environment/RaftSimEditorEnvironmentInternal.h"

#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimSouthForkShorelinePresentationTest,
    "RaftSim.M9.EShorelinePresentationCompletion",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimSouthForkShorelinePresentationTest::RunTest(const FString& Parameters)
{
    using namespace RaftSimEditorEnvironment;

    int64 CompletionCount = 0;
    const FLinearColor Dry(0.15f, 0.05f, 0.25f, 0.0f);
    const FLinearColor Completed = CompleteSouthForkShorelinePresentation(
        Dry, 0.20f, CompletionCount);
    TestEqual(TEXT("A bounded submerged gap is completed"), Completed.A, 1.0f);
    TestTrue(TEXT("Completed depth data remains bounded"), Completed.G >= 0.08f);
    TestEqual(TEXT("Completed vertex is counted"), CompletionCount, int64{1});

    const FLinearColor TooShallow = CompleteSouthForkShorelinePresentation(
        Dry, 0.02f, CompletionCount);
    const FLinearColor TooDeep = CompleteSouthForkShorelinePresentation(
        Dry, 0.26f, CompletionCount);
    TestEqual(TEXT("Dry land below the minimum is not completed"), TooShallow.A, 0.0f);
    TestEqual(TEXT("Deep gaps outside the shoreline band are not completed"), TooDeep.A, 0.0f);
    TestEqual(TEXT("Rejected vertices are not counted"), CompletionCount, int64{1});

    const FLinearColor Wet(0.35f, 0.40f, 0.55f, 1.0f);
    const FLinearColor AlreadyWet = CompleteSouthForkShorelinePresentation(
        Wet, 0.20f, CompletionCount);
    TestEqual(TEXT("Existing wet presentation is retained"), AlreadyWet, Wet);
    TestEqual(TEXT("Existing wet vertices are not counted as infill"), CompletionCount, int64{1});

    TArray<FLinearColor> BoundaryPresentation{
        Dry, Dry, Wet, Wet, Wet, Dry, Dry};
    TArray<float> BoundarySurfaceM{
        470.0f, 455.0f, 446.8f, 446.7f, 446.6f, 452.0f, 468.0f};
    int32 LeftWetColumn = INDEX_NONE;
    int32 RightWetColumn = INDEX_NONE;
    TestTrue(
        TEXT("Dry hydraulic sentinels are conditioned from the solver-wet channel"),
        ConditionSouthForkDryWaterSurfaceRow(
            BoundaryPresentation, BoundarySurfaceM,
            LeftWetColumn, RightWetColumn));
    TestEqual(TEXT("Left solver-wet boundary is preserved"), LeftWetColumn, 2);
    TestEqual(TEXT("Right solver-wet boundary is preserved"), RightWetColumn, 4);
    TestTrue(
        TEXT("Dry bank heights no longer make the water surface climb uphill"),
        FMath::IsNearlyEqual(BoundarySurfaceM[0], 446.8f) &&
            FMath::IsNearlyEqual(BoundarySurfaceM[1], 446.8f) &&
            FMath::IsNearlyEqual(BoundarySurfaceM[5], 446.6f) &&
            FMath::IsNearlyEqual(BoundarySurfaceM[6], 446.6f));

    TArray<FLinearColor> VisibilityStep;
    VisibilityStep.Init(Dry, 9 * 2);
    for (int32 Row = 4; Row < 9; ++Row)
    {
        VisibilityStep[Row * 2] = Wet;
    }
    VisibilityStep[4 * 2 + 1] = Wet;
    TestTrue(
        TEXT("Longitudinal visibility filtering accepts an aligned hydraulic field"),
        SmoothSouthForkWaterVisibilityLongitudinally(
            4, 2, 9, VisibilityStep));
    TestTrue(
        TEXT("A four-metre shoreline width step becomes a bounded transition"),
        VisibilityStep[2 * 2].A > 0.0f &&
            VisibilityStep[2 * 2].A < VisibilityStep[4 * 2].A &&
            VisibilityStep[4 * 2].A < VisibilityStep[6 * 2].A);
    TestTrue(
        TEXT("An isolated dry-bank wet-mask spike stays below the visible contour"),
        VisibilityStep[4 * 2 + 1].A < 0.5f);

    int64 TransitionCount = 0;
    TestTrue(
        TEXT("A partly wet cell is emitted for terrain depth clipping"),
        ShouldEmitSouthForkShorelineCell(
            Wet, Wet, Dry, Dry,
            0.20f, 0.20f, -0.02f, -0.02f,
            TransitionCount));
    TestEqual(TEXT("Partly wet cell is counted once"), TransitionCount, int64{1});

    TestTrue(
        TEXT("A fully wet cell is emitted"),
        ShouldEmitSouthForkShorelineCell(
            Wet, Wet, Wet, Wet,
            0.20f, 0.20f, 0.20f, 0.20f,
            TransitionCount));
    TestEqual(TEXT("Fully wet cell is not a transition"), TransitionCount, int64{1});

    TestFalse(
        TEXT("A fully dry cell is omitted"),
        ShouldEmitSouthForkShorelineCell(
            Dry, Dry, Dry, Dry,
            -0.02f, -0.02f, -0.02f, -0.02f,
            TransitionCount));
    TestEqual(TEXT("Fully dry cell is not a transition"), TransitionCount, int64{1});

    TestFalse(
        TEXT("A deep dry solver gap is not promoted to visual water"),
        ShouldEmitSouthForkShorelineCell(
            Wet, Wet, Dry, Dry,
            0.20f, 0.20f, 0.80f, 0.80f,
            TransitionCount));
    TestFalse(
        TEXT("A tall dry bank is outside the bounded skirt"),
        ShouldEmitSouthForkShorelineCell(
            Wet, Wet, Dry, Dry,
            0.20f, 0.20f, -0.08f, -0.08f,
            TransitionCount));
    TestFalse(
        TEXT("A mixed shallow-bank and deep-gap cell remains absent"),
        ShouldEmitSouthForkShorelineCell(
            Wet, Wet, Dry, Dry,
            0.20f, 0.20f, -0.02f, 0.80f,
            TransitionCount));
    TestEqual(
        TEXT("Rejected partial cells are not transitions"),
        TransitionCount,
        int64{1});

    int32 GridWidth = 2;
    int32 GridHeight = 2;
    TArray<FVector> Vertices{
        FVector(0.0f, 0.0f, 0.0f), FVector(100.0f, 0.0f, 10.0f),
        FVector(0.0f, 100.0f, 20.0f), FVector(100.0f, 100.0f, 30.0f)};
    TArray<FVector2D> Uvs{
        FVector2D(0.0f, 0.0f), FVector2D(1.0f, 0.0f),
        FVector2D(0.0f, 1.0f), FVector2D(1.0f, 1.0f)};
    TArray<FLinearColor> Colors{Dry, Wet, Wet, Wet};
    TArray<float> Depths{0.0f, 0.2f, 0.4f, 0.6f};
    TestTrue(
        TEXT("Water presentation grid refines without changing source bounds"),
        RefineSouthForkWaterPresentationGrid(
            2, GridWidth, GridHeight, Vertices, Uvs, Colors, Depths));
    TestEqual(TEXT("Refined water width"), GridWidth, 3);
    TestEqual(TEXT("Refined water height"), GridHeight, 3);
    TestEqual(TEXT("Refined water vertex count"), Vertices.Num(), 9);
    TestTrue(
        TEXT("Refined center is bilinear in position and shoreline depth"),
        Vertices[4].Equals(FVector(50.0f, 50.0f, 15.0f), 0.01f) &&
            FMath::IsNearlyEqual(Depths[4], 0.3f, 0.001f));

    const TArray<FVector> ClipVertices{
        FVector(0.0f, 0.0f, 0.0f), FVector(100.0f, 0.0f, 0.0f),
        FVector(0.0f, 100.0f, 0.0f), FVector(100.0f, 100.0f, 0.0f)};
    const TArray<FVector2D> ClipUvs{
        FVector2D(0.0f, 0.0f), FVector2D(1.0f, 0.0f),
        FVector2D(0.0f, 1.0f), FVector2D(1.0f, 1.0f)};
    const TArray<FLinearColor> ClipColors{Wet, Wet, Wet, Wet};
    const TArray<float> ClipDepths{0.20f, -0.20f, 0.20f, -0.20f};
    TArray<FVector> ClippedVertices;
    TArray<int32> ClippedTriangles;
    TArray<FVector2D> ClippedUvs;
    TArray<FLinearColor> ClippedColors;
    TArray<FVector> ClippedNormals;
    TArray<FProcMeshTangent> ClippedTangents;
    int64 TerrainClipTransitionCount = 0;
    TestTrue(
        TEXT("Water geometry clips against terrain even when the solver mask is wet"),
        BuildSouthForkTerrainClippedWaterGeometry(
            ClipVertices, ClipUvs, ClipColors, ClipDepths, 2, 2,
            ClippedVertices, ClippedTriangles, ClippedUvs, ClippedColors,
            ClippedNormals, ClippedTangents, TerrainClipTransitionCount));
    float MaximumClippedX = -TNumericLimits<float>::Max();
    for (const FVector& Vertex : ClippedVertices)
    {
        MaximumClippedX = FMath::Max(MaximumClippedX, static_cast<float>(Vertex.X));
    }
    TestTrue(
        TEXT("Terrain clipping removes the rectangular uphill half of the water cell"),
        MaximumClippedX < 55.0f && ClippedTriangles.Num() >= 3);
    TestEqual(
        TEXT("Terrain-clipped shoreline cell is counted once"),
        TerrainClipTransitionCount, int64{1});

    TArray<FVector> ReliefVertices{
        FVector(0.0f, 0.0f, 0.0f),
        FVector(0.0f, 0.0f, 0.0f),
        FVector(0.0f, 0.0f, 0.0f)};
    const TArray<FVector2D> ReliefUvs{
        FVector2D(4.0f, 0.5f),
        FVector2D(7.0f, -1.0f),
        FVector2D(11.0f, 1.5f)};
    const TArray<FLinearColor> ReliefHydraulics{
        Wet,
        FLinearColor(0.95f, 0.5f, 0.85f, 1.0f),
        Dry};
    const TArray<float> ReliefDepths{1.0f, 1.5f, 0.02f};
    TArray<FVector> RepeatedReliefVertices = ReliefVertices;
    float MaximumReliefCm = 0.0f;
    float RepeatedMaximumReliefCm = 0.0f;
    TestTrue(
        TEXT("Visual water micro-relief accepts aligned refined fields"),
        ApplySouthForkWaterPresentationMicroRelief(
            ReliefVertices, ReliefUvs, ReliefHydraulics, ReliefDepths,
            MaximumReliefCm));
    TestTrue(
        TEXT("Visual water micro-relief is deterministic"),
        ApplySouthForkWaterPresentationMicroRelief(
            RepeatedReliefVertices, ReliefUvs, ReliefHydraulics, ReliefDepths,
            RepeatedMaximumReliefCm) &&
            ReliefVertices == RepeatedReliefVertices &&
            FMath::IsNearlyEqual(MaximumReliefCm, RepeatedMaximumReliefCm));
	TestTrue(
		TEXT("Visual water micro-relief stays below its forty-two centimetre source cap"),
		MaximumReliefCm > 0.0f && MaximumReliefCm <= 42.0f);
    TestEqual(
        TEXT("Visual water micro-relief leaves a dry shallow shoreline unchanged"),
        ReliefVertices[2].Z, double{0.0});

    const FSouthForkAeratedWaterOverlaySample CalmOverlay =
        ComputeSouthForkAeratedWaterOverlaySample(
            FLinearColor(0.0f, 0.55f, 0.85f, 1.0f),
            1.5f,
            968.0f,
            0.0f);
    TestEqual(
        TEXT("Fast calm water cannot gain an aerated overlay"),
        CalmOverlay.Opacity,
        0.0f);
    TestEqual(
        TEXT("Fast calm water cannot gain overlay displacement"),
        CalmOverlay.VerticalDisplacementCm,
        0.0f);
    const FSouthForkAeratedWaterOverlaySample DryOverlay =
        ComputeSouthForkAeratedWaterOverlaySample(
            FLinearColor(1.0f, 0.55f, 0.85f, 0.0f),
            1.5f,
            968.0f,
            0.0f);
    TestEqual(
        TEXT("Dry solver cells cannot gain an aerated overlay"),
        DryOverlay.Opacity,
        0.0f);
    const FSouthForkAeratedWaterOverlaySample ShoreOverlay =
        ComputeSouthForkAeratedWaterOverlaySample(
            FLinearColor(1.0f, 0.55f, 0.85f, 1.0f),
            0.05f,
            968.0f,
            0.0f);
    TestEqual(
        TEXT("The aerated overlay fades before the shallow shoreline"),
        ShoreOverlay.Opacity,
        0.0f);
    const FSouthForkAeratedWaterOverlaySample AeratedOverlay =
        ComputeSouthForkAeratedWaterOverlaySample(
            FLinearColor(0.95f, 0.55f, 0.85f, 1.0f),
            1.5f,
            968.0f,
            -4.0f);
    const FSouthForkAeratedWaterOverlaySample RepeatedAeratedOverlay =
        ComputeSouthForkAeratedWaterOverlaySample(
            FLinearColor(0.95f, 0.55f, 0.85f, 1.0f),
            1.5f,
            968.0f,
            -4.0f);
    TestTrue(
        TEXT("Positive solver foam produces a visible bounded overlay"),
        AeratedOverlay.Opacity > 0.5f &&
            AeratedOverlay.VerticalDisplacementCm > 0.0f &&
            AeratedOverlay.VerticalDisplacementCm <= 14.0f);
    TestTrue(
        TEXT("Aerated overlay sampling is deterministic"),
        FMath::IsNearlyEqual(
            AeratedOverlay.Opacity, RepeatedAeratedOverlay.Opacity) &&
            FMath::IsNearlyEqual(
                AeratedOverlay.VerticalDisplacementCm,
                RepeatedAeratedOverlay.VerticalDisplacementCm) &&
            AeratedOverlay.Color == RepeatedAeratedOverlay.Color);
    TestEqual(
        TEXT("Overlay color alpha carries the computed opacity"),
        AeratedOverlay.Color.A,
        AeratedOverlay.Opacity);

    constexpr int32 OverlayBaseWidth = 4;
    constexpr int32 OverlayBaseHeight = 4;
    TArray<FVector> OverlayBaseVertices;
    TArray<FVector2D> OverlayBaseUvs;
    TArray<FLinearColor> OverlayBaseHydraulics;
    TArray<float> OverlayBaseDepths;
    for (int32 Row = 0; Row < OverlayBaseHeight; ++Row)
    {
        for (int32 Column = 0; Column < OverlayBaseWidth; ++Column)
        {
            OverlayBaseVertices.Add(FVector(Column * 200.0f, Row * 200.0f, 0.0f));
            OverlayBaseUvs.Add(FVector2D(Column, Row));
            const bool bFoamCore =
                (Row == 1 || Row == 2) && (Column == 1 || Column == 2);
            OverlayBaseHydraulics.Add(FLinearColor(
                bFoamCore ? 0.95f : 0.0f, 0.55f, 0.85f, 1.0f));
            OverlayBaseDepths.Add(1.5f);
        }
    }
    TArray<FVector> OverlayVertices;
    TArray<int32> OverlayTriangles;
    TArray<FVector2D> OverlayUvs;
    TArray<FLinearColor> OverlayColors;
    int32 OverlayWidth = 0;
    int32 OverlayHeight = 0;
    TestTrue(
        TEXT("Refined aerated overlay geometry accepts an aligned wet grid"),
        BuildSouthForkRefinedWhitewaterOverlayGeometry(
            OverlayBaseVertices,
            OverlayBaseUvs,
            OverlayBaseHydraulics,
            OverlayBaseDepths,
            OverlayBaseWidth,
            OverlayBaseHeight,
            OverlayVertices,
            OverlayTriangles,
            OverlayUvs,
            OverlayColors,
            OverlayWidth,
            OverlayHeight));
    TestTrue(
        TEXT("Refined aerated overlay emits bounded whole quad pairs"),
        OverlayTriangles.Num() > 0 &&
            OverlayTriangles.Num() % 6 == 0 &&
            OverlayTriangles.Num() <=
                (OverlayWidth - 1) * (OverlayHeight - 1) * 6);
    for (int32 TriangleIndex = 0;
         TriangleIndex + 5 < OverlayTriangles.Num();
         TriangleIndex += 6)
    {
        const int32 I0 = OverlayTriangles[TriangleIndex];
        const int32 I1 = OverlayTriangles[TriangleIndex + 1];
        const int32 I2 = OverlayTriangles[TriangleIndex + 2];
        TestTrue(
            TEXT("Every admitted aerated cell contains both matching triangles"),
            I1 == I0 + 1 &&
                I2 == I0 + OverlayWidth &&
                OverlayTriangles[TriangleIndex + 3] == I1 &&
                OverlayTriangles[TriangleIndex + 4] == I2 + 1 &&
                OverlayTriangles[TriangleIndex + 5] == I2);
    }

    TArray<FLinearColor> CalmOverlayHydraulics;
    CalmOverlayHydraulics.Init(
        FLinearColor(0.0f, 0.55f, 0.85f, 1.0f),
        OverlayBaseWidth * OverlayBaseHeight);
    TArray<int32> CalmOverlayTriangles;
    TestTrue(
        TEXT("Refined calm overlay geometry accepts an aligned wet grid"),
        BuildSouthForkRefinedWhitewaterOverlayGeometry(
            OverlayBaseVertices,
            OverlayBaseUvs,
            CalmOverlayHydraulics,
            OverlayBaseDepths,
            OverlayBaseWidth,
            OverlayBaseHeight,
            OverlayVertices,
            CalmOverlayTriangles,
            OverlayUvs,
            OverlayColors,
            OverlayWidth,
            OverlayHeight));
    TestEqual(
        TEXT("Transparent padding cannot create geometry in calm water"),
        CalmOverlayTriangles.Num(),
        0);

    return !HasAnyErrors();
}

#endif
