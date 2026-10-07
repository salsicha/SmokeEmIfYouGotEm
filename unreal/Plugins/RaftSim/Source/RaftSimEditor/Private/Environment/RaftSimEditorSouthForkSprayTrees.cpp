#include "Environment/RaftSimEditorEnvironmentInternal.h"

namespace RaftSimEditorEnvironment
{
UStaticMesh* CreateSouthForkSprayTreeMesh(
    UWorld* World,
    const FString& PackagePath,
    const FSouthForkSprayTreeForm& Form,
    UMaterialInterface* BarkMaterial,
    UMaterialInterface* LeafMaterial,
    int32 LeafAtlasTileCount,
    FString& OutSummary)
{
    if (!World || !BarkMaterial || !LeafMaterial || LeafAtlasTileCount <= 0 ||
        Form.StemCount <= 0 || Form.BranchLevels <= 0 || Form.BranchesPerLevel <= 0)
    {
        return nullptr;
    }
    float TargetBaseZ = 0.0f;
    float TargetTopZ = Form.HeightCm;
    const FString AssetName = FPackageName::GetLongPackageAssetName(PackagePath);
    if (const UStaticMesh* Existing = LoadObject<UStaticMesh>(
            nullptr, *FString::Printf(TEXT("%s.%s"), *PackagePath, *AssetName)))
    {
        const FBox Bounds = Existing->GetBoundingBox();
        TargetBaseZ = static_cast<float>(Bounds.Min.Z);
        TargetTopZ = static_cast<float>(Bounds.Max.Z);
    }

    auto Noise01 = [&Form](int32 Seed)
    {
        const float Value = FMath::Sin(
            static_cast<float>(Seed + Form.SeedSalt * 4099 + 911) * 12.9898f + 0.431f) *
            43758.5453f;
        return FMath::Abs(FMath::Frac(Value));
    };
    auto RandomUnit = [&Noise01](int32 Seed)
    {
        const float Z = 2.0f * Noise01(Seed) - 1.0f;
        const float Azimuth = 2.0f * PI * Noise01(Seed + 1);
        const float Ring = FMath::Sqrt(FMath::Max(0.0f, 1.0f - Z * Z));
        return FVector(Ring * FMath::Cos(Azimuth), Ring * FMath::Sin(Azimuth), Z);
    };
    TArray<FVector> BarkVertices;
    TArray<int32> BarkTriangles;
    TArray<FVector> BarkNormals;
    TArray<FVector2D> BarkUvs;
    TArray<FVector> LeafVertices;
    TArray<int32> LeafTriangles;
    TArray<FVector> LeafNormals;
    TArray<FVector2D> LeafUvs;

    // Stems: one straight pine bole, or a clump of alder stems leaning a
    // little apart from a shared base.
    struct FStem
    {
        FVector Base;
        FVector Top;
    };
    TArray<FStem> Stems;
    for (int32 StemIndex = 0; StemIndex < Form.StemCount; ++StemIndex)
    {
        const float Azimuth = 2.0f * PI *
            (StemIndex + 0.37f * Noise01(StemIndex * 17 + 3)) / Form.StemCount;
        const FVector Outward(FMath::Cos(Azimuth), FMath::Sin(Azimuth), 0.0f);
        const bool bClump = Form.StemCount > 1;
        const FVector Base = bClump ? Outward * Form.StemBaseRadiusCm * 1.4f : FVector::ZeroVector;
        const float Splay = FMath::DegreesToRadians(bClump
            ? Form.StemSplayDegrees * FMath::Lerp(0.6f, 1.2f, Noise01(StemIndex * 19 + 5))
            : 0.0f);
        const float StemHeight = Form.HeightCm * Form.StemTopFraction *
            (StemIndex == 0 ? 1.0f : FMath::Lerp(0.82f, 0.95f, Noise01(StemIndex * 23 + 7)));
        const FVector Top = Base +
            (FVector::UpVector * FMath::Cos(Splay) + Outward * FMath::Sin(Splay)) * StemHeight;
        const float BaseRadius = Form.StemBaseRadiusCm * (StemIndex == 0 ? 1.0f : 0.8f);
        FVector Previous = Base;
        float PreviousRadius = BaseRadius;
        for (int32 Piece = 1; Piece <= 3; ++Piece)
        {
            const float T = Piece / 3.0f;
            FVector Point = FMath::Lerp(Base, Top, T);
            if (Piece < 3)
            {
                Point += FVector(
                    FMath::Lerp(-1.0f, 1.0f, Noise01(StemIndex * 29 + Piece * 3)),
                    FMath::Lerp(-1.0f, 1.0f, Noise01(StemIndex * 31 + Piece * 5)),
                    0.0f) * Form.WidthCm * 0.012f;
            }
            const float Radius = FMath::Lerp(BaseRadius, BaseRadius * 0.16f, T);
            AppendNativeCanopyTaperedSegment(
                Previous, Point, PreviousRadius, Radius, 10,
                BarkVertices, BarkTriangles, BarkNormals, BarkUvs);
            Previous = Point;
            PreviousRadius = Radius;
        }
        Stems.Add({Base, Top});
    }

    // Branches from the crown base up, in levels round the stems; each branch
    // end and its side twigs are the terminals that carry sprays.
    struct FTerminal
    {
        FVector Start;
        FVector End;
        int32 Seed;
    };
    TArray<FTerminal> Terminals;
    const float HalfWidth = Form.WidthCm * 0.5f;
    int32 BranchIndex = 0;
    for (int32 Level = 0; Level < Form.BranchLevels; ++Level)
    {
        for (int32 LevelBranch = 0; LevelBranch < Form.BranchesPerLevel; ++LevelBranch, ++BranchIndex)
        {
            const int32 Seed = Form.SeedSalt * 10000 + BranchIndex * 97;
            const FStem& Stem = Stems[BranchIndex % Stems.Num()];
            const float U = FMath::Clamp(
                (Level + FMath::Lerp(0.15f, 0.85f, Noise01(Seed + 1))) / Form.BranchLevels, 0.0f, 1.0f);
            const float CrownBaseZ = Form.HeightCm * Form.CrownBaseFraction;
            const float StemBaseZ = static_cast<float>(Stem.Base.Z);
            const float StemTopZ = static_cast<float>(Stem.Top.Z);
            const float Height = FMath::Lerp(CrownBaseZ, StemTopZ * 0.98f, U);
            const FVector Origin = FMath::Lerp(
                Stem.Base, Stem.Top,
                FMath::Clamp((Height - StemBaseZ) / FMath::Max(1.0f, StemTopZ - StemBaseZ), 0.0f, 1.0f));
            const float Azimuth = FMath::DegreesToRadians(
                BranchIndex * 137.50776f + FMath::Lerp(-14.0f, 14.0f, Noise01(Seed + 2)));
            // Ponderosa narrows to a point; alder is widest a little below
            // mid-crown.
            const float Profile = Form.bConicalCrown
                ? FMath::Lerp(1.0f, 0.10f, FMath::Pow(U, 0.9f))
                : FMath::Max(0.22f, FMath::Sqrt(FMath::Max(0.0f, 1.0f - FMath::Square((U - 0.42f) / 0.62f))));
            const float Length = HalfWidth * Profile * FMath::Lerp(0.82f, 1.05f, Noise01(Seed + 3));
            const float Pitch = FMath::DegreesToRadians(
                FMath::Lerp(Form.BranchPitchBaseDegrees, Form.BranchPitchTopDegrees, U) +
                FMath::Lerp(-6.0f, 6.0f, Noise01(Seed + 4)));
            const FVector Direction(
                FMath::Cos(Azimuth) * FMath::Cos(Pitch),
                FMath::Sin(Azimuth) * FMath::Cos(Pitch),
                FMath::Sin(Pitch));
            const float Droop = Form.bConicalCrown ? 0.07f : 0.02f;
            const FVector Mid = Origin + Direction * Length * 0.5f - FVector::UpVector * Length * Droop;
            const FVector End = Origin + Direction * Length - FVector::UpVector * Length * Droop * 0.6f;
            const float RootRadius = FMath::Clamp(Length * 0.022f, 2.0f, 9.0f);
            AppendNativeCanopyTaperedSegment(
                Origin, Mid, RootRadius, RootRadius * 0.55f, 7,
                BarkVertices, BarkTriangles, BarkNormals, BarkUvs);
            AppendNativeCanopyTaperedSegment(
                Mid, End, RootRadius * 0.55f, 0.8f, 6,
                BarkVertices, BarkTriangles, BarkNormals, BarkUvs);
            Terminals.Add({Mid, End, Seed + 11});
            for (int32 Twig = 0; Twig < Form.TwigsPerBranch; ++Twig)
            {
                const int32 TwigSeed = Seed + 31 + Twig * 13;
                const float Along = FMath::Lerp(0.45f, 0.9f, (Twig + 0.5f) / Form.TwigsPerBranch);
                const FVector TwigStart = Along < 0.5f
                    ? FMath::Lerp(Origin, Mid, Along * 2.0f)
                    : FMath::Lerp(Mid, End, Along * 2.0f - 1.0f);
                const float TwigAzimuth = Azimuth + FMath::DegreesToRadians(
                    (Twig % 2 == 0 ? 1.0f : -1.0f) * FMath::Lerp(25.0f, 45.0f, Noise01(TwigSeed)));
                const float TwigPitch = Pitch + FMath::DegreesToRadians(Form.bConicalCrown ? 4.0f : 15.0f);
                const FVector TwigDirection(
                    FMath::Cos(TwigAzimuth) * FMath::Cos(TwigPitch),
                    FMath::Sin(TwigAzimuth) * FMath::Cos(TwigPitch),
                    FMath::Sin(TwigPitch));
                const FVector TwigEnd = TwigStart +
                    TwigDirection * Length * FMath::Lerp(0.22f, 0.34f, Noise01(TwigSeed + 1));
                AppendNativeCanopyTaperedSegment(
                    TwigStart, TwigEnd, 1.6f, 0.6f, 5,
                    BarkVertices, BarkTriangles, BarkNormals, BarkUvs);
                Terminals.Add({TwigStart, TwigEnd, TwigSeed + 7});
            }
        }
    }

    FBox TipBounds(ForceInit);
    for (const FTerminal& Terminal : Terminals)
    {
        TipBounds += Terminal.End;
    }
    FVector CrownCenter = TipBounds.GetCenter();
    CrownCenter.Z -= 0.15f * TipBounds.GetExtent().Z;
    const FVector CrownRadii = TipBounds.GetExtent() + FVector(80.0f);
    const FVector CrownRadiiSquared = CrownRadii * CrownRadii;
    for (int32 TerminalIndex = 0; TerminalIndex < Terminals.Num(); ++TerminalIndex)
    {
        const FTerminal& Terminal = Terminals[TerminalIndex];
        const FVector Along = (Terminal.End - Terminal.Start).GetSafeNormal();
        const float TwigLength = FVector::Distance(Terminal.Start, Terminal.End);
        for (int32 SprayIndex = 0; SprayIndex < Form.SpraysPerTerminal; ++SprayIndex)
        {
            const int32 Seed = Terminal.Seed + 7919 + SprayIndex * 131;
            const float SprayHeight = FMath::Lerp(Form.SprayHeightMinCm, Form.SprayHeightMaxCm, Noise01(Seed + 1));
            const float SprayWidth = FMath::Lerp(Form.SprayWidthMinCm, Form.SprayWidthMaxCm, Noise01(Seed + 2));
            const FVector Center =
                FMath::Lerp(Terminal.Start, Terminal.End, FMath::Lerp(0.3f, 1.0f, Noise01(Seed + 6))) +
                Along * TwigLength * 0.2f * Noise01(Seed + 7) +
                RandomUnit(Seed + 3) * FMath::Lerp(10.0f, 35.0f, Noise01(Seed + 8)) +
                FVector::UpVector * 0.25f * SprayHeight;
            const FVector Outward = ((Center - CrownCenter) / CrownRadiiSquared).GetSafeNormal();
            FVector Facing = (Outward * 0.55f + RandomUnit(Seed + 11) * 0.85f).GetSafeNormal();
            if (FVector::DotProduct(Facing, Outward) < 0.0f)
            {
                Facing = -Facing;
            }
            FVector SprayUp = FVector::UpVector * 0.7f + Along * 0.5f;
            SprayUp -= Facing * FVector::DotProduct(SprayUp, Facing);
            if (SprayUp.SizeSquared() < 1.0e-4f)
            {
                SprayUp = Along - Facing * FVector::DotProduct(Along, Facing);
            }
            SprayUp = SprayUp.GetSafeNormal().RotateAngleAxis(
                FMath::Lerp(-30.0f, 30.0f, Noise01(Seed + 13)), Facing);
            const int32 FirstVertex = LeafVertices.Num();
            AppendNativeCanopyLeafCard(
                Center,
                FVector::CrossProduct(SprayUp, Facing),
                SprayUp,
                SprayWidth,
                SprayHeight,
                (TerminalIndex * 7 + SprayIndex * 5) % LeafAtlasTileCount,
                LeafVertices,
                LeafTriangles,
                LeafNormals,
                LeafUvs);
            for (int32 Vertex = FirstVertex; Vertex < LeafVertices.Num(); ++Vertex)
            {
                const FVector Crown = ((LeafVertices[Vertex] - CrownCenter) / CrownRadiiSquared).GetSafeNormal();
                LeafNormals[Vertex] = (LeafNormals[Vertex] * 0.45f + Crown * 0.55f).GetSafeNormal();
            }
        }
    }

    // Map the new tree's base and top onto the placed package's.
    float BuiltBaseZ = TNumericLimits<float>::Max();
    float BuiltTopZ = -TNumericLimits<float>::Max();
    for (const TArray<FVector>* Positions : {&LeafVertices, &BarkVertices})
    {
        for (const FVector& Vertex : *Positions)
        {
            BuiltBaseZ = FMath::Min(BuiltBaseZ, static_cast<float>(Vertex.Z));
            BuiltTopZ = FMath::Max(BuiltTopZ, static_cast<float>(Vertex.Z));
        }
    }
    const float HeightScale = (TargetTopZ - TargetBaseZ) / FMath::Max(1.0f, BuiltTopZ - BuiltBaseZ);
    for (TArray<FVector>* Positions : {&LeafVertices, &BarkVertices})
    {
        for (FVector& Vertex : *Positions)
        {
            Vertex.Z = TargetBaseZ + (Vertex.Z - BuiltBaseZ) * HeightScale;
        }
    }
    for (TArray<FVector>* Normals : {&LeafNormals, &BarkNormals})
    {
        for (FVector& Normal : *Normals)
        {
            Normal = FVector(Normal.X, Normal.Y, Normal.Z / HeightScale).GetSafeNormal();
        }
    }

    AActor* TemporaryActor = AddPreviewTwoSectionProceduralMeshActor(
        World,
        FString::Printf(TEXT("SouthFork%sSprayTree_BuildSource"), Form.Token),
        BarkVertices, BarkTriangles, BarkNormals, BarkUvs, BarkMaterial,
        LeafVertices, LeafTriangles, LeafNormals, LeafUvs, LeafMaterial);
    UStaticMesh* Mesh = ConvertNativeCanopyProceduralActorToStaticMesh(
        TemporaryActor,
        PackagePath,
        LeafMaterial,
        /*bEnableNanite=*/false,
        ENaniteShapePreservation::None,
        OutSummary);
    if (TemporaryActor)
    {
        TemporaryActor->Destroy();
    }
    if (!Mesh)
    {
        return nullptr;
    }
    OutSummary += FString::Printf(
        TEXT("Created South Fork %s spray tree %s: stems=%d terminals=%d leaf_sprays=%d "
             "leaf_triangles=%d bark_triangles=%d top_z=%.1f base_z=%.1f height_scale=%.4f.\n"),
        Form.Token,
        *PackagePath,
        Form.StemCount,
        Terminals.Num(),
        Terminals.Num() * Form.SpraysPerTerminal,
        LeafTriangles.Num() / 3,
        BarkTriangles.Num() / 3,
        TargetTopZ,
        TargetBaseZ,
        HeightScale);
    return Mesh;
}
} // namespace RaftSimEditorEnvironment
