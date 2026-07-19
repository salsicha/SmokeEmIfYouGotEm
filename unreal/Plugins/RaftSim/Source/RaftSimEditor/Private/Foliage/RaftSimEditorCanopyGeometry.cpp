#include "Environment/RaftSimEditorEnvironmentInternal.h"

namespace RaftSimEditorEnvironment
{
void BuildFutaleufuCoiguePrototypeGeometry(
    const FFutaleufuCoigueCrownForm& Form,
    TArray<FVector>& TrunkVertices,
    TArray<int32>& TrunkTriangles,
    TArray<FVector>& TrunkNormals,
    TArray<FVector2D>& TrunkUVs,
    TArray<FVector>& BranchletVertices,
    TArray<int32>& BranchletTriangles,
    TArray<FVector>& BranchletNormals,
    TArray<FVector2D>& BranchletUVs,
    TArray<FVector>& LeafVertices,
    TArray<int32>& LeafTriangles,
    TArray<FVector>& LeafNormals,
    TArray<FVector2D>& LeafUVs,
    TArray<FVector>& FarLeafVertices,
    TArray<int32>& FarLeafTriangles,
    TArray<FVector>& FarLeafNormals,
    TArray<FVector2D>& FarLeafUVs,
    FVector& OutCloseupCamera,
    FVector& OutCloseupTarget,
    FFutaleufuCoigueRoutingMetrics& OutRoutingMetrics)
{
    OutRoutingMetrics = FFutaleufuCoigueRoutingMetrics();
    const float TrunkTopZ = 2920.0f * Form.TrunkHeightScale;
    auto TrunkLeanAtZ = [&Form, TrunkTopZ](float Z)
    {
        const float T = FMath::Clamp(Z / FMath::Max(TrunkTopZ, 1.0f), 0.0f, 1.0f);
        return FVector(Form.TrunkLeanTopCm.X * T, Form.TrunkLeanTopCm.Y * T, 0.0f);
    };
    OutCloseupCamera = FVector(1110.0f, -330.0f, 1210.0f * Form.TrunkHeightScale);
    OutCloseupTarget = FVector(760.0f, -5.0f, 1150.0f * Form.TrunkHeightScale);
    const float LowerTrunkZ = 1150.0f * Form.TrunkHeightScale;
    AppendNativeCanopyTaperedSegment(
        FVector(0.0f, 0.0f, 0.0f), TrunkLeanAtZ(LowerTrunkZ) + FVector(0.0f, 0.0f, LowerTrunkZ),
        105.0f * Form.TrunkRadiusScale, 76.0f * Form.TrunkRadiusScale, 18,
        TrunkVertices, TrunkTriangles, TrunkNormals, TrunkUVs);
    const float MidTrunkStartZ = 1080.0f * Form.TrunkHeightScale;
    const float MidTrunkEndZ = 2180.0f * Form.TrunkHeightScale;
    AppendNativeCanopyTaperedSegment(
        TrunkLeanAtZ(MidTrunkStartZ) + FVector(0.0f, 0.0f, MidTrunkStartZ),
        TrunkLeanAtZ(MidTrunkEndZ) + FVector(18.0f, -12.0f, MidTrunkEndZ),
        80.0f * Form.TrunkRadiusScale, 38.0f * Form.TrunkRadiusScale, 16,
        TrunkVertices, TrunkTriangles, TrunkNormals, TrunkUVs);
    const float UpperTrunkStartZ = 2110.0f * Form.TrunkHeightScale;
    AppendNativeCanopyTaperedSegment(
        TrunkLeanAtZ(UpperTrunkStartZ) + FVector(18.0f, -12.0f, UpperTrunkStartZ),
        TrunkLeanAtZ(TrunkTopZ) + FVector(-18.0f, 16.0f, TrunkTopZ),
        40.0f * Form.TrunkRadiusScale, 9.0f * Form.TrunkRadiusScale, 12,
        TrunkVertices, TrunkTriangles, TrunkNormals, TrunkUVs);

    for (int32 RootIndex = 0; RootIndex < 7; ++RootIndex)
    {
        const float Angle = 2.0f * PI * static_cast<float>(RootIndex) / 7.0f + 0.21f;
        const FVector End(
            FMath::Cos(Angle) * (185.0f + 20.0f * (RootIndex % 3)),
            FMath::Sin(Angle) * (185.0f + 20.0f * (RootIndex % 3)),
            4.0f);
        AppendNativeCanopyTaperedSegment(
            FVector(0.0f, 0.0f, 72.0f * Form.TrunkHeightScale), End,
            42.0f * Form.TrunkRadiusScale, 8.0f * Form.TrunkRadiusScale, 10,
            TrunkVertices, TrunkTriangles, TrunkNormals, TrunkUVs);
    }

    struct FNativeCanopyLeafSpray
    {
        FVector Center;
        FVector Direction;
        float Scale = 1.0f;
        bool bNearDetail = true;
    };
    TArray<FNativeCanopyLeafSpray> LeafSprays;
    auto AddLeafSpray = [&LeafSprays](
                            const FVector& Center,
                            const FVector& Direction,
                            float Scale)
    {
        FNativeCanopyLeafSpray Spray;
        Spray.Center = Center;
        Spray.Direction = Direction.GetSafeNormal();
        Spray.Scale = Scale;
        LeafSprays.Add(Spray);
    };
    auto AddFarLeafSpray = [&LeafSprays](
                               const FVector& Center,
                               const FVector& Direction,
                               float Scale)
    {
        FNativeCanopyLeafSpray Spray;
        Spray.Center = Center;
        Spray.Direction = Direction.GetSafeNormal();
        Spray.Scale = Scale;
        Spray.bNearDetail = false;
        LeafSprays.Add(Spray);
    };
    auto EvaluateSuppressedSectorScale = [&Form](float AngleDegrees)
    {
        if (Form.SuppressedSectorHalfWidthDegrees <= KINDA_SMALL_NUMBER)
        {
            return 1.0f;
        }
        const float SectorDistance = FMath::Abs(FMath::FindDeltaAngleDegrees(
            AngleDegrees, Form.SuppressedSectorCenterDegrees));
        if (SectorDistance >= Form.SuppressedSectorHalfWidthDegrees)
        {
            return 1.0f;
        }
        const float EdgeT = SectorDistance / Form.SuppressedSectorHalfWidthDegrees;
        return FMath::Lerp(
            Form.SuppressedSectorLengthScale,
            1.0f,
            EdgeT * EdgeT * (3.0f - 2.0f * EdgeT));
    };
    const int32 MainBranchCount = Form.MainBranchCount;
    for (int32 BranchIndex = 0; BranchIndex < MainBranchCount; ++BranchIndex)
    {
        const float HeightNoise = FMath::Abs(FMath::Frac(
            FMath::Sin(static_cast<float>(BranchIndex + 17 + Form.SeedOffset) * 12.9898f) * 43758.5453f));
        const float BranchT = static_cast<float>(BranchIndex) / static_cast<float>(MainBranchCount - 1);
        const float StartZ =
            Form.CrownBaseZCm + BranchT * Form.CrownSpanZCm + (HeightNoise - 0.5f) * 238.0f;
        const float Angle = FMath::DegreesToRadians(
            FMath::Fmod(
                static_cast<float>(BranchIndex + Form.SeedOffset) * 137.50776f +
                    (HeightNoise - 0.5f) * 31.0f * Form.AsymmetryScale,
                360.0f));
        const float AngleDegrees = FMath::RadiansToDegrees(Angle);
        const float SuppressedSectorScale = EvaluateSuppressedSectorScale(AngleDegrees);
        const bool bInCrownGap =
            Form.CrownGapCenterT >= 0.0f &&
            FMath::Abs(BranchT - Form.CrownGapCenterT) < Form.CrownGapHalfWidthT;
        const bool bStormDamaged =
            Form.DamageModulo > 0 &&
            (BranchIndex + Form.SeedOffset) % Form.DamageModulo == Form.DamageRemainder;
        const float StructuralLengthScale = FMath::Clamp(
            SuppressedSectorScale *
                (bInCrownGap ? Form.CrownGapLengthScale : 1.0f) *
                (bStormDamaged ? Form.DamagedBranchLengthScale : 1.0f),
            0.16f,
            1.0f);
        const float CrownProfile = FMath::Sin(PI * FMath::Clamp(BranchT, 0.0f, 1.0f));
        const float SideBias = (BranchIndex % 5 == 0) ? 1.13f : ((BranchIndex % 7 == 0) ? 0.88f : 1.0f);
        const float Length =
            (610.0f + CrownProfile * 390.0f +
             (HeightNoise - 0.5f) * 148.0f * Form.AsymmetryScale) *
            SideBias * Form.CrownWidthScale * StructuralLengthScale;
        const FVector Start = TrunkLeanAtZ(StartZ) + FVector(
            8.0f * FMath::Sin(Angle * 2.0f), 8.0f * FMath::Cos(Angle), StartZ);
        const FVector Horizontal(FMath::Cos(Angle), FMath::Sin(Angle), 0.0f);
        const FVector Side(-Horizontal.Y, Horizontal.X, 0.0f);
        const float LateralBend = (HeightNoise - 0.5f) * 112.0f * Form.AsymmetryScale;
        const FVector Mid =
            Start + Horizontal * Length * 0.53f + Side * LateralBend +
            FVector(0.0f, 0.0f, Length * 0.11f * Form.BranchUpliftScale);
        const FVector End = Start + Horizontal * Length + FVector(
            Side.X * LateralBend * 0.42f,
            Side.Y * LateralBend * 0.42f,
            Length * FMath::Lerp(0.13f, 0.42f, BranchT) * Form.BranchUpliftScale);
        const float BaseRadius = FMath::Lerp(37.0f, 16.0f, BranchT);
        AppendNativeCanopyTaperedSegment(
            Start, Mid, BaseRadius, BaseRadius * 0.58f, 12,
            TrunkVertices, TrunkTriangles, TrunkNormals, TrunkUVs);
        AppendNativeCanopyTaperedSegment(
            Mid - Horizontal * 12.0f, End, BaseRadius * 0.62f, 7.0f, 10,
            TrunkVertices, TrunkTriangles, TrunkNormals, TrunkUVs);

        const FVector BranchDirection = (End - Mid).GetSafeNormal();
        const float FirstTipLength = bStormDamaged ? 24.0f : 60.0f;
        const float SecondTipLength = bStormDamaged ? 18.0f : 72.0f;
        const float FirstTipRise = bStormDamaged ? -7.0f : 18.0f;
        const float SecondTipRise = bStormDamaged ? -11.0f : 28.0f;
        const FVector BranchTipMid =
            End + BranchDirection * FirstTipLength + FVector::UpVector * FirstTipRise;
        const FVector BranchTipEnd =
            BranchTipMid + BranchDirection * SecondTipLength + FVector::UpVector * SecondTipRise;
        AppendNativeCanopyTaperedSegment(
            End, BranchTipMid, 7.0f, 3.2f, 8,
            TrunkVertices, TrunkTriangles, TrunkNormals, TrunkUVs);
        AppendNativeCanopyTaperedSegment(
            BranchTipMid, BranchTipEnd, 3.2f, 0.8f, 6,
            TrunkVertices, TrunkTriangles, TrunkNormals, TrunkUVs);
        const int32 MainSprayCount = bStormDamaged ? 1 : (bInCrownGap ? 2 : 3);
        for (int32 MainSprayIndex = 0; MainSprayIndex < MainSprayCount; ++MainSprayIndex)
        {
            const float SprayT = MainSprayCount == 1
                ? 0.48f
                : FMath::Lerp(0.28f, 0.88f, static_cast<float>(MainSprayIndex) / (MainSprayCount - 1));
            AddLeafSpray(
                FMath::Lerp(Mid, End, SprayT),
                BranchDirection,
                FMath::Lerp(1.06f, 0.88f, SprayT));
        }

        const int32 TwigCount = bStormDamaged ? 1 : (bInCrownGap ? 2 : 3);
        for (int32 TwigIndex = 0; TwigIndex < TwigCount; ++TwigIndex)
        {
            const float TwigT = 0.36f + TwigIndex * 0.21f;
            const FVector TwigStart = FMath::Lerp(Mid, End, TwigT);
            const float SideSign = ((BranchIndex + TwigIndex) % 2 == 0) ? 1.0f : -1.0f;
            const FVector TwigEnd = TwigStart +
                Side * SideSign * FMath::Lerp(165.0f, 225.0f, BranchT) * Form.CrownWidthScale +
                Horizontal * 92.0f * Form.CrownWidthScale +
                FVector(0.0f, 0.0f, (58.0f + TwigIndex * 21.0f) * Form.BranchUpliftScale);
            AppendNativeCanopyTaperedSegment(
                TwigStart, TwigEnd, 10.0f, 3.2f, 8,
                BranchletVertices, BranchletTriangles, BranchletNormals, BranchletUVs);
            const FVector TwigDirection = (TwigEnd - TwigStart).GetSafeNormal();
            const FVector TwigCollarMid = TwigEnd + TwigDirection * 20.0f + FVector::UpVector * 3.0f;
            const FVector TwigCollarEnd = TwigCollarMid + TwigDirection * 28.0f + FVector::UpVector * 4.0f;
            AppendNativeCanopyTaperedSegment(
                TwigEnd, TwigCollarMid, 3.2f, 1.4f, 6,
                BranchletVertices, BranchletTriangles, BranchletNormals, BranchletUVs);
            AppendNativeCanopyTaperedSegment(
                TwigCollarMid, TwigCollarEnd, 1.4f, 0.72f, 5,
                BranchletVertices, BranchletTriangles, BranchletNormals, BranchletUVs);
            AddLeafSpray(FMath::Lerp(TwigStart, TwigEnd, 0.58f), TwigDirection, 0.86f);
            AddLeafSpray(TwigCollarEnd + TwigDirection * 12.0f, TwigDirection, 0.80f);
        }
    }
    constexpr int32 CrownAnchorCount = 24;
    for (int32 CrownIndex = 0; CrownIndex < CrownAnchorCount; ++CrownIndex)
    {
        const float Angle = 2.0f * PI * CrownIndex / static_cast<float>(CrownAnchorCount);
        const float DirectionScale = EvaluateSuppressedSectorScale(FMath::RadiansToDegrees(Angle));
        const float CrownZ =
            Form.CrownBaseZCm + Form.CrownSpanZCm * 0.93f + 22.0f * CrownIndex;
        const FVector CrownDirection(
            FMath::Cos(Angle),
            FMath::Sin(Angle),
            0.34f + 0.05f * (CrownIndex % 3));
        AddFarLeafSpray(
            TrunkLeanAtZ(CrownZ) + FVector(
                FMath::Cos(Angle) * (175.0f + 48.0f * (CrownIndex % 5)) *
                    Form.CrownWidthScale * DirectionScale,
                FMath::Sin(Angle) * (175.0f + 48.0f * (CrownIndex % 5)) *
                    Form.CrownWidthScale * DirectionScale,
                CrownZ),
            CrownDirection,
            0.84f * FMath::Lerp(0.72f, 1.0f, DirectionScale));
    }

    auto Noise01 = [](int32 Seed)
    {
        return FMath::Abs(FMath::Frac(
            FMath::Sin(static_cast<float>(Seed) * 12.9898f + 0.917f) * 43758.5453f));
    };
    const int32 FarCrownVolumeAnchorCount = Form.FarCrownVolumeAnchorCount;
    for (int32 CrownIndex = 0; CrownIndex < FarCrownVolumeAnchorCount; ++CrownIndex)
    {
        const int32 Seed = 7103 + Form.SeedOffset * 37 + CrownIndex * 293;
        const float HeightT =
            (static_cast<float>(CrownIndex) + 0.5f) / static_cast<float>(FarCrownVolumeAnchorCount);
        const float Angle =
            FMath::DegreesToRadians(FMath::Fmod(CrownIndex * 137.50776f + Noise01(Seed) * 47.0f, 360.0f));
        const float DirectionScale = EvaluateSuppressedSectorScale(FMath::RadiansToDegrees(Angle));
        const bool bInCrownGap =
            Form.CrownGapCenterT >= 0.0f &&
            FMath::Abs(HeightT - Form.CrownGapCenterT) < Form.CrownGapHalfWidthT;
        const float GapScale = bInCrownGap ? Form.CrownGapLengthScale : 1.0f;
        const float CrownProfile = 0.36f + 0.64f * FMath::Sin(PI * HeightT);
        const float Radius =
            CrownProfile * FMath::Lerp(80.0f, 1060.0f, FMath::Pow(Noise01(Seed + 1), 0.72f)) *
            Form.CrownWidthScale * DirectionScale * GapScale;
        const float CenterZ =
            Form.CrownBaseZCm + 130.0f + HeightT * (Form.CrownSpanZCm + 210.0f) +
            (Noise01(Seed + 4) - 0.5f) * 118.0f;
        const FVector Center = TrunkLeanAtZ(CenterZ) + FVector(
            FMath::Cos(Angle) * Radius *
                FMath::Lerp(0.82f, 1.10f, Noise01(Seed + 2)) * Form.AsymmetryScale,
            FMath::Sin(Angle) * Radius * FMath::Lerp(0.82f, 1.10f, Noise01(Seed + 3)),
            CenterZ);
        AddFarLeafSpray(
            Center,
            FVector(FMath::Cos(Angle), FMath::Sin(Angle), FMath::Lerp(0.12f, 0.46f, HeightT)),
            FMath::Lerp(1.08f, 0.82f, HeightT) *
                FMath::Lerp(0.66f, 1.0f, DirectionScale * GapScale));
    }
    TArray<TPair<FVector, FVector>> AuthoredNearBranchletSegments;
    TArray<TPair<FVector, FVector>> AuthoredNearTertiarySegments;
    for (int32 SprayIndex = 0; SprayIndex < LeafSprays.Num(); ++SprayIndex)
    {
        const FNativeCanopyLeafSpray& Spray = LeafSprays[SprayIndex];
        const FVector Direction = Spray.Direction.IsNearlyZero() ? FVector::ForwardVector : Spray.Direction;
        FVector BaseUp = (FVector::UpVector - Direction * FVector::DotProduct(FVector::UpVector, Direction)).GetSafeNormal();
        if (BaseUp.IsNearlyZero())
        {
            BaseUp = FVector::RightVector;
        }
        const FVector BaseNormal = FVector::CrossProduct(Direction, BaseUp).GetSafeNormal();
        if (Spray.bNearDetail)
        {
        const FVector ParentShootStart = Spray.Center - Direction * 12.0f;
        const FVector ParentShootMid = Spray.Center + Direction * 16.0f + BaseUp * 2.5f;
        const FVector ParentShootEnd = Spray.Center + Direction * 44.0f + BaseUp * 5.0f;
        AppendNativeCanopyTaperedSegment(
            ParentShootStart, ParentShootMid, 0.74f, 0.46f, 6,
            BranchletVertices, BranchletTriangles, BranchletNormals, BranchletUVs);
        AppendNativeCanopyTaperedSegment(
            ParentShootMid, ParentShootEnd, 0.48f, 0.20f, 5,
            BranchletVertices, BranchletTriangles, BranchletNormals, BranchletUVs);
        for (int32 BranchletIndex = 0;
             BranchletIndex < FutaleufuCoigueBranchletsPerParentShoot;
             ++BranchletIndex)
        {
            const int32 BranchletSeed =
                Form.SeedOffset * 100003 + SprayIndex * 4099 + BranchletIndex * 307;
            const float BranchletAngle =
                static_cast<float>(BranchletIndex) * 2.39996323f +
                (Noise01(BranchletSeed + 1) - 0.5f) * 0.36f;
            const float BaseParentT = 0.08f +
                static_cast<float>(BranchletIndex) *
                    (0.84f / static_cast<float>(FutaleufuCoigueBranchletsPerParentShoot - 1));
            const float BranchletLength =
                FMath::Lerp(24.0f, 40.0f, Noise01(BranchletSeed + 4)) * Spray.Scale;
            const float CandidateOffsetsDegrees[] = {0.0f, 28.0f, -28.0f, 52.0f, -52.0f};
            const float CandidateAttachmentOffsets[] = {0.0f, 0.03f, -0.03f, 0.06f, -0.06f};
            constexpr float RequiredBranchletClearanceCm = 1.2f;
            FVector BranchletStart =
                FMath::Lerp(ParentShootStart, ParentShootEnd, BaseParentT);
            FVector Radial = FVector::ZeroVector;
            FVector BranchletDirection = FVector::ZeroVector;
            FVector BranchletMid = FVector::ZeroVector;
            FVector BranchletEnd = FVector::ZeroVector;
            float SelectedClearance = -1.0f;
            int32 SelectedCandidateIndex = 0;
            bool bBranchletRouteFound = false;
            int32 CandidateOrdinal = 0;
            for (int32 AttachmentIndex = 0;
                 AttachmentIndex < UE_ARRAY_COUNT(CandidateAttachmentOffsets) && !bBranchletRouteFound;
                 ++AttachmentIndex)
            {
                const float CandidateParentT = FMath::Clamp(
                    BaseParentT + CandidateAttachmentOffsets[AttachmentIndex], 0.04f, 0.96f);
                const FVector CandidateStart =
                    FMath::Lerp(ParentShootStart, ParentShootEnd, CandidateParentT);
                for (int32 CandidateIndex = 0;
                     CandidateIndex < UE_ARRAY_COUNT(CandidateOffsetsDegrees);
                     ++CandidateIndex, ++CandidateOrdinal)
                {
                    const float CandidateAngle = BranchletAngle +
                        FMath::DegreesToRadians(CandidateOffsetsDegrees[CandidateIndex]);
                    const FVector CandidateRadial =
                        BaseNormal * FMath::Cos(CandidateAngle) + BaseUp * FMath::Sin(CandidateAngle);
                    const FVector CandidateDirection =
                        (Direction * 0.48f + CandidateRadial * 0.84f + FVector::UpVector * 0.18f).GetSafeNormal();
                    const FVector CandidateMid =
                        CandidateStart + CandidateDirection * BranchletLength * 0.52f +
                        BaseUp * ((Noise01(BranchletSeed + 5) - 0.5f) * 7.0f);
                    const FVector CandidateEnd =
                        CandidateStart + CandidateDirection * BranchletLength +
                        BaseNormal * ((Noise01(BranchletSeed + 6) - 0.5f) * 9.0f);
                    float CandidateClearance = TNumericLimits<float>::Max();
                    const FVector CandidateCenter = (CandidateStart + CandidateEnd) * 0.5f;
                    for (const TPair<FVector, FVector>& Segment : AuthoredNearBranchletSegments)
                    {
                        if (FVector::DistSquared(
                                CandidateCenter,
                                (Segment.Key + Segment.Value) * 0.5f) > FMath::Square(100.0f))
                        {
                            continue;
                        }
                        CandidateClearance = FMath::Min(
                            CandidateClearance,
                            NativeCanopySegmentDistance(
                                CandidateStart, CandidateEnd, Segment.Key, Segment.Value));
                    }
                    if (CandidateClearance > SelectedClearance)
                    {
                        SelectedClearance = CandidateClearance;
                        SelectedCandidateIndex = CandidateOrdinal;
                        BranchletStart = CandidateStart;
                        Radial = CandidateRadial;
                        BranchletDirection = CandidateDirection;
                        BranchletMid = CandidateMid;
                        BranchletEnd = CandidateEnd;
                    }
                    if (AuthoredNearBranchletSegments.IsEmpty() ||
                        CandidateClearance >= RequiredBranchletClearanceCm)
                    {
                        SelectedCandidateIndex = CandidateOrdinal;
                        SelectedClearance = CandidateClearance;
                        BranchletStart = CandidateStart;
                        Radial = CandidateRadial;
                        BranchletDirection = CandidateDirection;
                        BranchletMid = CandidateMid;
                        BranchletEnd = CandidateEnd;
                        bBranchletRouteFound = true;
                        break;
                    }
                }
            }
            if (!AuthoredNearBranchletSegments.IsEmpty())
            {
                OutRoutingMetrics.MinNearBranchletClearanceCm = FMath::Min(
                    OutRoutingMetrics.MinNearBranchletClearanceCm,
                    SelectedClearance);
                OutRoutingMetrics.ReroutedBranchletCount += SelectedCandidateIndex > 0 ? 1 : 0;
                OutRoutingMetrics.UnresolvedBranchletClearanceCount +=
                    SelectedClearance < RequiredBranchletClearanceCm ? 1 : 0;
            }
            AuthoredNearBranchletSegments.Emplace(BranchletStart, BranchletEnd);
            if (SprayIndex == 89 && BranchletIndex == 0)
            {
                OutCloseupTarget = FMath::Lerp(BranchletStart, BranchletEnd, 0.58f);
                FVector Outward(Spray.Center.X, Spray.Center.Y, 0.0f);
                Outward = Outward.GetSafeNormal();
                if (Outward.IsNearlyZero())
                {
                    Outward = BaseNormal;
                }
                FVector Tangent = FVector::CrossProduct(FVector::UpVector, Outward).GetSafeNormal();
                if (Tangent.IsNearlyZero())
                {
                    Tangent = BaseNormal;
                }
                OutCloseupCamera =
                    OutCloseupTarget + Tangent * 118.0f + Outward * 16.0f + FVector::UpVector * 22.0f;
            }
            AppendNativeCanopyTaperedSegment(
                BranchletStart, BranchletMid, 0.42f, 0.20f, 5,
                BranchletVertices, BranchletTriangles, BranchletNormals, BranchletUVs);
            AppendNativeCanopyTaperedSegment(
                BranchletMid, BranchletEnd, 0.22f, 0.08f, 4,
                BranchletVertices, BranchletTriangles, BranchletNormals, BranchletUVs);

            TArray<TPair<FVector, FVector>> LeafAttachmentAxes;
            for (int32 LeafIndex = 0; LeafIndex < FutaleufuCoigueMainLeavesPerBranchlet; ++LeafIndex)
            {
                const float LeafT = 0.10f +
                    static_cast<float>(LeafIndex) *
                        (0.82f / static_cast<float>(FutaleufuCoigueMainLeavesPerBranchlet - 1));
                const FVector Attachment =
                    LeafT < 0.52f
                    ? FMath::Lerp(BranchletStart, BranchletMid, LeafT / 0.52f)
                    : FMath::Lerp(BranchletMid, BranchletEnd, (LeafT - 0.52f) / 0.48f);
                const float SideSign = (LeafIndex % 2 == 0) ? 1.0f : -1.0f;
                const FVector LeafAxis =
                    (BranchletDirection * 0.34f + Radial * SideSign * 0.88f + BaseUp * 0.24f).GetSafeNormal();
                LeafAttachmentAxes.Emplace(Attachment, LeafAxis);
            }
            for (int32 TertiaryIndex = 0;
                 TertiaryIndex < FutaleufuCoigueTertiaryBranchesPerBranchlet;
                 ++TertiaryIndex)
            {
                const float BaseTertiaryT =
                    0.30f + static_cast<float>(TertiaryIndex) * 0.23f;
                const float SideSign = TertiaryIndex % 2 == 0 ? -1.0f : 1.0f;
                const FVector BaseTertiaryDirection =
                    (BranchletDirection * 0.54f + Radial * SideSign * 0.76f +
                     BaseUp * (0.14f + TertiaryIndex * 0.04f)).GetSafeNormal();
                const float TertiaryLength =
                    FMath::Lerp(10.0f, 18.0f, Noise01(BranchletSeed + 20 + TertiaryIndex));
                const float TertiaryCandidateOffsetsDegrees[] = {0.0f, 32.0f, -32.0f, 58.0f, -58.0f};
                const float TertiaryAttachmentOffsets[] = {
                    0.0f, 0.025f, -0.025f, 0.05f, -0.05f, 0.075f, -0.075f, 0.10f, -0.10f};
                constexpr float RequiredTertiaryClearanceCm = 0.6f;
                FVector TertiaryStart =
                    FMath::Lerp(BranchletStart, BranchletEnd, BaseTertiaryT);
                FVector TertiaryDirection = BaseTertiaryDirection;
                FVector TertiaryEnd = TertiaryStart + TertiaryDirection * TertiaryLength;
                float SelectedTertiaryClearance = -1.0f;
                int32 SelectedTertiaryCandidateIndex = 0;
                bool bTertiaryRouteFound = false;
                int32 TertiaryCandidateOrdinal = 0;
                for (int32 AttachmentIndex = 0;
                     AttachmentIndex < UE_ARRAY_COUNT(TertiaryAttachmentOffsets) && !bTertiaryRouteFound;
                     ++AttachmentIndex)
                {
                    const float CandidateTertiaryT = FMath::Clamp(
                        BaseTertiaryT + TertiaryAttachmentOffsets[AttachmentIndex], 0.12f, 0.90f);
                    const FVector CandidateStart =
                        FMath::Lerp(BranchletStart, BranchletEnd, CandidateTertiaryT);
                    for (int32 CandidateIndex = 0;
                         CandidateIndex < UE_ARRAY_COUNT(TertiaryCandidateOffsetsDegrees);
                         ++CandidateIndex, ++TertiaryCandidateOrdinal)
                    {
                        const FVector CandidateDirection = BaseTertiaryDirection.RotateAngleAxis(
                            TertiaryCandidateOffsetsDegrees[CandidateIndex], BranchletDirection).GetSafeNormal();
                        const FVector CandidateEnd = CandidateStart + CandidateDirection * TertiaryLength;
                        float CandidateClearance = TNumericLimits<float>::Max();
                        const FVector CandidateCenter = (CandidateStart + CandidateEnd) * 0.5f;
                        for (const TPair<FVector, FVector>& Segment : AuthoredNearTertiarySegments)
                        {
                            if (FVector::DistSquared(
                                    CandidateCenter,
                                    (Segment.Key + Segment.Value) * 0.5f) > FMath::Square(50.0f))
                            {
                                continue;
                            }
                            CandidateClearance = FMath::Min(
                                CandidateClearance,
                                NativeCanopySegmentDistance(
                                    CandidateStart, CandidateEnd, Segment.Key, Segment.Value));
                        }
                        if (CandidateClearance > SelectedTertiaryClearance)
                        {
                            SelectedTertiaryClearance = CandidateClearance;
                            SelectedTertiaryCandidateIndex = TertiaryCandidateOrdinal;
                            TertiaryStart = CandidateStart;
                            TertiaryDirection = CandidateDirection;
                            TertiaryEnd = CandidateEnd;
                        }
                        if (AuthoredNearTertiarySegments.IsEmpty() ||
                            CandidateClearance >= RequiredTertiaryClearanceCm)
                        {
                            SelectedTertiaryCandidateIndex = TertiaryCandidateOrdinal;
                            SelectedTertiaryClearance = CandidateClearance;
                            TertiaryStart = CandidateStart;
                            TertiaryDirection = CandidateDirection;
                            TertiaryEnd = CandidateEnd;
                            bTertiaryRouteFound = true;
                            break;
                        }
                    }
                }
                if (!AuthoredNearTertiarySegments.IsEmpty())
                {
                    OutRoutingMetrics.MinNearTertiaryClearanceCm = FMath::Min(
                        OutRoutingMetrics.MinNearTertiaryClearanceCm,
                        SelectedTertiaryClearance);
                    OutRoutingMetrics.ReroutedTertiaryCount +=
                        SelectedTertiaryCandidateIndex > 0 ? 1 : 0;
                    OutRoutingMetrics.UnresolvedTertiaryClearanceCount +=
                        SelectedTertiaryClearance < RequiredTertiaryClearanceCm ? 1 : 0;
                }
                AuthoredNearTertiarySegments.Emplace(TertiaryStart, TertiaryEnd);
                AppendNativeCanopyTaperedSegment(
                    TertiaryStart, TertiaryEnd, 0.16f, 0.045f, 3,
                    BranchletVertices, BranchletTriangles, BranchletNormals, BranchletUVs);
                for (int32 LeafIndex = 0;
                     LeafIndex < FutaleufuCoigueLeavesPerTertiaryBranch;
                     ++LeafIndex)
                {
                    const float LeafT = 0.22f +
                        static_cast<float>(LeafIndex) *
                            (0.68f / static_cast<float>(FutaleufuCoigueLeavesPerTertiaryBranch - 1));
                    const float LeafSideSign = (LeafIndex % 2 == 0) ? 1.0f : -1.0f;
                    const FVector Attachment = FMath::Lerp(TertiaryStart, TertiaryEnd, LeafT);
                    const FVector LeafAxis =
                        (TertiaryDirection * 0.38f + Radial * LeafSideSign * 0.78f + BaseUp * 0.28f).GetSafeNormal();
                    LeafAttachmentAxes.Emplace(Attachment, LeafAxis);
                }
            }

            for (int32 LeafIndex = 0; LeafIndex < LeafAttachmentAxes.Num(); ++LeafIndex)
            {
                const int32 Seed = BranchletSeed * 17 + LeafIndex * 131;
                const FVector Attachment = LeafAttachmentAxes[LeafIndex].Key;
                const FVector LeafAxis = LeafAttachmentAxes[LeafIndex].Value;
                const float PetioleLength = FMath::Lerp(0.8f, 2.2f, Noise01(Seed + 1));
                const FVector PetioleEnd = Attachment + LeafAxis * PetioleLength;
                AppendNativeCanopyTaperedSegment(
                    Attachment, PetioleEnd, 0.075f, 0.025f, 3,
                    BranchletVertices, BranchletTriangles, BranchletNormals, BranchletUVs);
                const float LeafWidth = FMath::Lerp(2.8f, 4.2f, Noise01(Seed + 2));
                const float LeafHeight = FMath::Lerp(4.0f, 5.8f, Noise01(Seed + 3));
                FVector CardRight = FVector::CrossProduct(LeafAxis, Direction).GetSafeNormal();
                if (CardRight.IsNearlyZero())
                {
                    CardRight = BaseNormal;
                }
                const FVector CardCenter = PetioleEnd + LeafAxis * LeafHeight * 0.48f;
                AppendNativeCanopyLeafCard(
                    CardCenter,
                    CardRight,
                    LeafAxis,
                    LeafWidth,
                    LeafHeight,
                    Seed % 12,
                    LeafVertices,
                    LeafTriangles,
                    LeafNormals,
                    LeafUVs);
            }
        }
        }

        for (int32 ClusterIndex = 0; ClusterIndex < 24; ++ClusterIndex)
        {
            const int32 ClusterSeed =
                Form.SeedOffset * 130003 + SprayIndex * 3253 + ClusterIndex * 211 + 31;
            const float ClusterAngle = Noise01(ClusterSeed + 1) * 2.0f * PI;
            const float ClusterRadius = ClusterIndex == 0
                ? 0.0f
                : FMath::Lerp(28.0f, 64.0f, Noise01(ClusterSeed + 2));
            const FVector ClusterRadial =
                BaseUp * FMath::Cos(ClusterAngle) + BaseNormal * FMath::Sin(ClusterAngle);
            const FVector ClusterCenter =
                Spray.Center + ClusterRadial * ClusterRadius +
                Direction * (Noise01(ClusterSeed + 3) * 2.0f - 1.0f) * 82.0f;
            for (int32 CardIndex = 0; CardIndex < 6; ++CardIndex)
            {
                const int32 Seed = ClusterSeed * 13 + CardIndex * 79;
                const FVector CardRight =
                    (Direction + BaseNormal * (Noise01(Seed + 1) * 0.80f - 0.40f) +
                     BaseUp * (Noise01(Seed + 2) * 0.32f - 0.16f)).GetSafeNormal();
                const FVector CardUp =
                    BaseUp.RotateAngleAxis(Noise01(Seed + 3) * 170.0f, CardRight).GetSafeNormal();
                AppendNativeCanopyLeafCard(
                    ClusterCenter + BaseNormal * (Noise01(Seed + 4) * 34.0f - 17.0f),
                    CardRight,
                    CardUp,
                    FMath::Lerp(44.0f, 80.0f, Noise01(Seed + 5)) * Spray.Scale,
                    FMath::Lerp(36.0f, 60.0f, Noise01(Seed + 6)) * Spray.Scale,
                    12 + (Seed % 4),
                    FarLeafVertices,
                    FarLeafTriangles,
                    FarLeafNormals,
                    FarLeafUVs);
            }
        }
    }
    if (OutRoutingMetrics.MinNearBranchletClearanceCm == TNumericLimits<float>::Max())
    {
        OutRoutingMetrics.MinNearBranchletClearanceCm = 0.0f;
    }
    if (OutRoutingMetrics.MinNearTertiaryClearanceCm == TNumericLimits<float>::Max())
    {
        OutRoutingMetrics.MinNearTertiaryClearanceCm = 0.0f;
    }
}

                                      
 
               
                        
                       
                      
                         
                           
                             
                               
                               
                                 
                              
                           
                                                     
                                               
                                                  
                                             
                                  
                                    
                                     
                           
                              
                                          
  

void AppendFutaleufuCordilleraCypressOpaqueScaleLeafCluster(
    const FVector& Base,
    const FVector& Direction,
    float WidthCm,
    float LengthCm,
    float FoldCm,
    float RollDegrees,
    TArray<FVector>& Vertices,
    TArray<int32>& Triangles,
    TArray<FVector>& Normals,
    TArray<FVector2D>& UVs)
{
    const FVector Axis = Direction.GetSafeNormal();
    if (Axis.IsNearlyZero() || WidthCm < 1.0f || LengthCm < 1.0f)
    {
        return;
    }
    FVector Right = FVector::CrossProduct(Axis, FVector::UpVector).GetSafeNormal();
    if (Right.IsNearlyZero())
    {
        Right = FVector::RightVector;
    }
    Right = Right.RotateAngleAxis(RollDegrees, Axis).GetSafeNormal();
    const FVector FoldNormal = FVector::CrossProduct(Axis, Right).GetSafeNormal();
    const int32 BaseIndex = Vertices.Num();
    Vertices.Add(Base);
    UVs.Add(FVector2D(0.5f, 1.0f));
    const FVector LobeDirections[] = {
        Axis,
        (Axis * 0.88f + Right * 0.36f + FoldNormal * 0.10f).GetSafeNormal(),
        (Axis * 0.86f - Right * 0.38f - FoldNormal * 0.08f).GetSafeNormal()};
    const float LobeLengthScales[] = {1.0f, 0.78f, 0.84f};
    const float LobeHalfWidthScales[] = {0.30f, 0.24f, 0.24f};
    for (int32 LobeIndex = 0; LobeIndex < 3; ++LobeIndex)
    {
        const FVector LobeDirection = LobeDirections[LobeIndex];
        FVector LobeRight = FVector::CrossProduct(LobeDirection, FoldNormal).GetSafeNormal();
        if (LobeRight.IsNearlyZero())
        {
            LobeRight = Right;
        }
        const float LobeLength = LengthCm * LobeLengthScales[LobeIndex];
        const float HalfWidth = WidthCm * LobeHalfWidthScales[LobeIndex];
        const FVector Shoulder = Base + LobeDirection * LobeLength * 0.48f;
        const FVector FoldOffset = FoldNormal * FoldCm * (LobeIndex == 0 ? 1.0f : -0.55f);
        const int32 LobeBaseIndex = Vertices.Num();
        Vertices.Append({
            Shoulder - LobeRight * HalfWidth - FoldOffset,
            Base + LobeDirection * LobeLength,
            Shoulder + LobeRight * HalfWidth - FoldOffset});
        UVs.Append({
            FVector2D(0.0f, 0.55f),
            FVector2D(0.5f, 0.0f),
            FVector2D(1.0f, 0.55f)});
        Triangles.Append({
            BaseIndex, LobeBaseIndex, LobeBaseIndex + 1,
            BaseIndex, LobeBaseIndex + 1, LobeBaseIndex + 2});
    }

    TArray<FVector> ClusterNormals;
    ClusterNormals.Init(FVector::ZeroVector, 10);
    for (int32 TriangleIndex = 0; TriangleIndex < 6; ++TriangleIndex)
    {
        const int32 TriangleOffset = Triangles.Num() - 18 + TriangleIndex * 3;
        const int32 A = Triangles[TriangleOffset] - BaseIndex;
        const int32 B = Triangles[TriangleOffset + 1] - BaseIndex;
        const int32 C = Triangles[TriangleOffset + 2] - BaseIndex;
        const FVector FaceNormal = FVector::CrossProduct(
            Vertices[BaseIndex + B] - Vertices[BaseIndex + A],
            Vertices[BaseIndex + C] - Vertices[BaseIndex + A]).GetSafeNormal();
        ClusterNormals[A] += FaceNormal;
        ClusterNormals[B] += FaceNormal;
        ClusterNormals[C] += FaceNormal;
    }
    for (const FVector& ClusterNormal : ClusterNormals)
    {
        Normals.Add(ClusterNormal.GetSafeNormal());
    }
}

void AppendFutaleufuCordilleraCypressVolumetricScaleLeafCluster(
    const FVector& Base,
    const FVector& Direction,
    float WidthCm,
    float LengthCm,
    int32 Seed,
    TArray<FVector>& WoodyVertices,
    TArray<int32>& WoodyTriangles,
    TArray<FVector>& WoodyNormals,
    TArray<FVector2D>& WoodyUVs,
    TArray<FVector>& FoliageVertices,
    TArray<int32>& FoliageTriangles,
    TArray<FVector>& FoliageNormals,
    TArray<FVector2D>& FoliageUVs)
{
    const FVector Axis = Direction.GetSafeNormal();
    if (Axis.IsNearlyZero() || WidthCm < 1.0f || LengthCm < 1.0f)
    {
        return;
    }
    auto Noise01 = [Seed](int32 Offset)
    {
        return FMath::Abs(FMath::Frac(
            FMath::Sin(static_cast<float>(Seed + Offset) * 12.9898f + 78.233f) *
            43758.5453f));
    };
    FVector BasisA = FVector::CrossProduct(Axis, FVector::UpVector).GetSafeNormal();
    if (BasisA.IsNearlyZero())
    {
        BasisA = FVector::RightVector;
    }
    const FVector BasisB = FVector::CrossProduct(Axis, BasisA).GetSafeNormal();
    const FVector CentralEnd = Base + Axis * LengthCm * 0.64f;
    AppendNativeCanopyTaperedSegment(
        Base,
        CentralEnd,
        2.8f,
        0.9f,
        6,
        WoodyVertices,
        WoodyTriangles,
        WoodyNormals,
        WoodyUVs);

    for (int32 ShootIndex = 0; ShootIndex < 4; ++ShootIndex)
    {
        const float Angle =
            2.0f * PI * static_cast<float>(ShootIndex) / 4.0f +
            (Noise01(ShootIndex * 17 + 1) - 0.5f) * 0.52f;
        const FVector Radial =
            (BasisA * FMath::Cos(Angle) + BasisB * FMath::Sin(Angle)).GetSafeNormal();
        const float AttachT = 0.20f + ShootIndex * 0.15f;
        const FVector ShootBase = FMath::Lerp(Base, CentralEnd, AttachT);
        const FVector ShootDirection = (
            Axis * FMath::Lerp(0.48f, 0.66f, Noise01(ShootIndex * 19 + 3)) +
            Radial * FMath::Lerp(0.68f, 0.86f, Noise01(ShootIndex * 19 + 5)) +
            FVector::UpVector * ((Noise01(ShootIndex * 19 + 7) - 0.42f) * 0.28f))
                                                   .GetSafeNormal();
        const float ShootLength = LengthCm * FMath::Lerp(
            0.30f, 0.44f, Noise01(ShootIndex * 23 + 9));
        const FVector ShootEnd = ShootBase + ShootDirection * ShootLength;
        AppendNativeCanopyTaperedSegment(
            ShootBase,
            ShootEnd,
            1.5f,
            0.42f,
            6,
            WoodyVertices,
            WoodyTriangles,
            WoodyNormals,
            WoodyUVs);

        for (int32 LobeIndex = 0; LobeIndex < 2; ++LobeIndex)
        {
            const float LobeT = 0.34f + LobeIndex * 0.38f;
            const float SideSign = (ShootIndex + LobeIndex) % 2 == 0 ? 1.0f : -1.0f;
            const FVector LobeBase = FMath::Lerp(ShootBase, ShootEnd, LobeT);
            const FVector LobeDirection = (
                ShootDirection * 0.76f +
                Radial * SideSign * FMath::Lerp(
                    0.22f, 0.40f, Noise01(ShootIndex * 29 + LobeIndex * 7 + 11)) +
                BasisB * ((Noise01(ShootIndex * 31 + LobeIndex * 11 + 13) - 0.5f) * 0.32f))
                                                      .GetSafeNormal();
            const float LobeLength = LengthCm * FMath::Lerp(
                0.28f, 0.44f, Noise01(ShootIndex * 37 + LobeIndex * 13 + 17));
            const FVector LobeMid = LobeBase + LobeDirection * LobeLength * 0.46f;
            const FVector LobeEnd = LobeBase + LobeDirection * LobeLength;
            const float LobeRadius = WidthCm * FMath::Lerp(
                0.16f, 0.24f, Noise01(ShootIndex * 41 + LobeIndex * 17 + 19));
            AppendNativeCanopyTaperedSegment(
                LobeBase,
                LobeMid,
                LobeRadius * 0.48f,
                LobeRadius,
                8,
                FoliageVertices,
                FoliageTriangles,
                FoliageNormals,
                FoliageUVs);
            AppendNativeCanopyTaperedSegment(
                LobeMid,
                LobeEnd,
                LobeRadius,
                LobeRadius * 0.18f,
                8,
                FoliageVertices,
                FoliageTriangles,
                FoliageNormals,
                FoliageUVs);
        }
    }
}

void BuildFutaleufuCordilleraCypressGeometry(
    const FFutaleufuCordilleraCypressForm& Form,
    bool bOpaqueNearGeometry,
    bool bVolumetricNearGeometry,
    TArray<FVector>& WoodyVertices,
    TArray<int32>& WoodyTriangles,
    TArray<FVector>& WoodyNormals,
    TArray<FVector2D>& WoodyUVs,
    TArray<FVector>& NearSprayVertices,
    TArray<int32>& NearSprayTriangles,
    TArray<FVector>& NearSprayNormals,
    TArray<FVector2D>& NearSprayUVs,
    TArray<FVector>& SprayVertices,
    TArray<int32>& SprayTriangles,
    TArray<FVector>& SprayNormals,
    TArray<FVector2D>& SprayUVs,
    FVector& OutCloseupCamera,
    FVector& OutCloseupTarget)
{
    WoodyVertices.Reset();
    WoodyTriangles.Reset();
    WoodyNormals.Reset();
    WoodyUVs.Reset();
    NearSprayVertices.Reset();
    NearSprayTriangles.Reset();
    NearSprayNormals.Reset();
    NearSprayUVs.Reset();
    SprayVertices.Reset();
    SprayTriangles.Reset();
    SprayNormals.Reset();
    SprayUVs.Reset();

    auto Noise01 = [](int32 Seed)
    {
        return FMath::Abs(FMath::Frac(
            FMath::Sin(static_cast<float>(Seed) * 12.9898f + 78.233f) * 43758.5453f));
    };
    auto LeanAtZ = [&Form](float Z)
    {
        const float T = FMath::Clamp(Z / FMath::Max(Form.HeightCm, 1.0f), 0.0f, 1.0f);
        return FVector(Form.TrunkLeanTopCm.X * T, Form.TrunkLeanTopCm.Y * T, 0.0f);
    };
    auto SectorScale = [&Form](float AngleDegrees)
    {
        if (Form.SuppressedSectorHalfWidthDegrees <= KINDA_SMALL_NUMBER)
        {
            return 1.0f;
        }
        const float Distance = FMath::Abs(FMath::FindDeltaAngleDegrees(
            AngleDegrees, Form.SuppressedSectorCenterDegrees));
        if (Distance >= Form.SuppressedSectorHalfWidthDegrees)
        {
            return 1.0f;
        }
        const float EdgeT = Distance / Form.SuppressedSectorHalfWidthDegrees;
        return FMath::Lerp(
            Form.SuppressedSectorLengthScale,
            1.0f,
            EdgeT * EdgeT * (3.0f - 2.0f * EdgeT));
    };

    const int32 TrunkSegmentCount = 5;
    for (int32 SegmentIndex = 0; SegmentIndex < TrunkSegmentCount; ++SegmentIndex)
    {
        const float T0 = static_cast<float>(SegmentIndex) / TrunkSegmentCount;
        const float T1 = static_cast<float>(SegmentIndex + 1) / TrunkSegmentCount;
        const float Z0 = Form.HeightCm * T0;
        const float Z1 = Form.HeightCm * T1;
        const float Radius0 = FMath::Lerp(Form.BaseRadiusCm, 5.0f, FMath::Pow(T0, 0.78f));
        const float Radius1 = FMath::Lerp(Form.BaseRadiusCm, 5.0f, FMath::Pow(T1, 0.78f));
        const FVector WindCrook(
            (Noise01(Form.SeedOffset + SegmentIndex * 31) - 0.5f) * 22.0f * T1,
            (Noise01(Form.SeedOffset + SegmentIndex * 47) - 0.5f) * 22.0f * T1,
            0.0f);
        AppendNativeCanopyTaperedSegment(
            LeanAtZ(Z0) + FVector(0.0f, 0.0f, Z0),
            LeanAtZ(Z1) + WindCrook + FVector(0.0f, 0.0f, Z1),
            Radius0,
            Radius1,
            SegmentIndex < 2 ? 16 : 12,
            WoodyVertices,
            WoodyTriangles,
            WoodyNormals,
            WoodyUVs);
    }
    for (int32 RootIndex = 0; RootIndex < 6; ++RootIndex)
    {
        const float Angle = 2.0f * PI * RootIndex / 6.0f + Form.SeedOffset * 0.001f;
        AppendNativeCanopyTaperedSegment(
            FVector(0.0f, 0.0f, 40.0f),
            FVector(FMath::Cos(Angle) * 145.0f, FMath::Sin(Angle) * 145.0f, 3.0f),
            Form.BaseRadiusCm * 0.42f,
            6.0f,
            9,
            WoodyVertices,
            WoodyTriangles,
            WoodyNormals,
            WoodyUVs);
    }

    auto AddSpray = [&](const FVector& Center,
                        const FVector& Direction,
                        float WidthCm,
                        float LengthCm,
                        int32 AtlasTile,
                        float RollDegrees)
    {
        const FVector SprayDirection = Direction.GetSafeNormal();
        FVector CardRight = FVector::CrossProduct(SprayDirection, FVector::UpVector).GetSafeNormal();
        if (CardRight.IsNearlyZero())
        {
            CardRight = FVector::RightVector;
        }
        CardRight = CardRight.RotateAngleAxis(RollDegrees, SprayDirection).GetSafeNormal();
        AppendNativeCanopyLeafCard(
            Center,
            CardRight,
            SprayDirection,
            WidthCm,
            LengthCm,
            AtlasTile,
            SprayVertices,
            SprayTriangles,
            SprayNormals,
            SprayUVs);
    };
    auto AddNearSpray = [&](const FVector& Base,
                            const FVector& Direction,
                            float WidthCm,
                            float LengthCm,
                            int32 AtlasTile,
                            float RollDegrees)
    {
        const FVector SprayDirection = Direction.GetSafeNormal();
        FVector CardRight = FVector::CrossProduct(SprayDirection, FVector::UpVector).GetSafeNormal();
        if (CardRight.IsNearlyZero())
        {
            CardRight = FVector::RightVector;
        }
        CardRight = CardRight.RotateAngleAxis(RollDegrees, SprayDirection).GetSafeNormal();
        AppendNativeCanopyLeafCard(
            Base + SprayDirection * LengthCm * 0.5f,
            CardRight,
            SprayDirection,
            WidthCm,
            LengthCm,
            AtlasTile,
            NearSprayVertices,
            NearSprayTriangles,
            NearSprayNormals,
            NearSprayUVs);
    };
    auto AddTerminalCluster = [&](const FVector& Center,
                                  const FVector& Direction,
                                  float WidthCm,
                                  float LengthCm,
                                  int32 Seed)
    {
        const FVector Axis = Direction.GetSafeNormal();
        FVector AxisA = FVector::CrossProduct(Axis, FVector::UpVector).GetSafeNormal();
        if (AxisA.IsNearlyZero())
        {
            AxisA = FVector::RightVector;
        }
        const FVector AxisB = FVector::CrossProduct(Axis, AxisA).GetSafeNormal();
        const float NearBranchSystemSamplingProbability = bVolumetricNearGeometry
            ? 0.50f
            : (bOpaqueNearGeometry ? 0.11f : 0.34f);
        if (Noise01(Seed + 997) < NearBranchSystemSamplingProbability)
        {
            const float FrondRollDegrees =
                (Noise01(Seed + 2) - 0.5f) * 34.0f;
            if (bVolumetricNearGeometry)
            {
                AppendFutaleufuCordilleraCypressVolumetricScaleLeafCluster(
                    Center,
                    Axis,
                    WidthCm,
                    LengthCm,
                    Seed,
                    WoodyVertices,
                    WoodyTriangles,
                    WoodyNormals,
                    WoodyUVs,
                    NearSprayVertices,
                    NearSprayTriangles,
                    NearSprayNormals,
                    NearSprayUVs);
            }
            else if (bOpaqueNearGeometry)
            {
                AppendFutaleufuCordilleraCypressOpaqueScaleLeafCluster(
                    Center,
                    Axis,
                    WidthCm * FMath::Lerp(1.34f, 1.56f, Noise01(Seed + 4)),
                    LengthCm * FMath::Lerp(1.28f, 1.46f, Noise01(Seed + 6)),
                    WidthCm * FMath::Lerp(0.10f, 0.16f, Noise01(Seed + 8)),
                    FrondRollDegrees,
                    NearSprayVertices,
                    NearSprayTriangles,
                    NearSprayNormals,
                    NearSprayUVs);
            }
            else
            {
                const FVector FrondStart = Center - Axis * LengthCm * 0.47f;
                AddNearSpray(
                    FrondStart,
                    Axis,
                    WidthCm * FMath::Lerp(1.52f, 1.78f, Noise01(Seed + 4)),
                    LengthCm * FMath::Lerp(1.36f, 1.58f, Noise01(Seed + 6)),
                    Seed,
                    FrondRollDegrees);
            }
        }
        constexpr int32 ShootCount = 5;
        for (int32 ShootIndex = 0; ShootIndex < ShootCount; ++ShootIndex)
        {
            const float Angle =
                2.0f * PI * static_cast<float>(ShootIndex) / ShootCount +
                (Noise01(Seed + ShootIndex * 29) - 0.5f) * 0.42f;
            const FVector Radial =
                (AxisA * FMath::Cos(Angle) + AxisB * FMath::Sin(Angle)).GetSafeNormal();
            const FVector ShootStart =
                Center - Axis * LengthCm * FMath::Lerp(
                    0.18f, 0.27f, Noise01(Seed + ShootIndex * 31 + 3)) +
                Radial * WidthCm * FMath::Lerp(
                    0.015f, 0.075f, Noise01(Seed + ShootIndex * 31 + 5));
            const FVector ShootDirection = (
                Axis * FMath::Lerp(0.68f, 0.80f, Noise01(Seed + ShootIndex * 31 + 7)) +
                Radial * FMath::Lerp(0.42f, 0.62f, Noise01(Seed + ShootIndex * 31 + 11)) +
                FVector::UpVector *
                    ((Noise01(Seed + ShootIndex * 31 + 13) - 0.5f) * 0.18f))
                                                     .GetSafeNormal();
            const float ShootLength = LengthCm * FMath::Lerp(
                0.27f, 0.40f, Noise01(Seed + ShootIndex * 31 + 17));
            const FVector ShootEnd = ShootStart + ShootDirection * ShootLength;
            if (ShootIndex == 0 || ShootIndex == 2 || ShootIndex == 4)
            {
                const FVector SprayDirection = (
                    ShootDirection * 0.82f +
                    Radial * (ShootIndex == 2 ? -0.18f : 0.24f) +
                    AxisB * ((Noise01(Seed + ShootIndex * 41) - 0.5f) * 0.22f))
                                                        .GetSafeNormal();
                const float Scale = FMath::Lerp(
                    0.86f,
                    1.12f,
                    Noise01(Seed + ShootIndex * 43 + 19));
                AddSpray(
                    FMath::Lerp(ShootStart, ShootEnd, 0.76f),
                    SprayDirection,
                    WidthCm * 0.86f * Scale,
                    LengthCm * 0.90f * Scale,
                    Seed + ShootIndex * 5,
                    FMath::RadiansToDegrees(Angle) +
                        (Noise01(Seed + ShootIndex * 47 + 23) - 0.5f) * 76.0f);
            }
        }
    };

    OutCloseupTarget = FVector(0.0f, 0.0f, Form.CrownBaseCm + 240.0f);
    OutCloseupCamera = OutCloseupTarget + FVector(520.0f, -420.0f, 90.0f);
    const float CrownSpan = FMath::Max(Form.HeightCm - Form.CrownBaseCm - 70.0f, 100.0f);
    for (int32 BranchIndex = 0; BranchIndex < Form.BranchCount; ++BranchIndex)
    {
        const float BranchT = (static_cast<float>(BranchIndex) + 0.35f) /
            static_cast<float>(Form.BranchCount);
        const int32 Seed = Form.SeedOffset + BranchIndex * 193;
        const float StartZ = Form.CrownBaseCm + CrownSpan * BranchT +
            (Noise01(Seed + 1) - 0.5f) * 260.0f;
        const float AngleDegrees = FMath::Fmod(
            static_cast<float>(Form.SeedOffset) * 0.37f +
                static_cast<float>(BranchIndex) * 137.50776f +
                (Noise01(Seed + 2) - 0.5f) * 28.0f * Form.Asymmetry,
            360.0f);
        const float Angle = FMath::DegreesToRadians(AngleDegrees);
        const FVector Horizontal(FMath::Cos(Angle), FMath::Sin(Angle), 0.0f);
        const FVector Side(-Horizontal.Y, Horizontal.X, 0.0f);
        const bool bInGap = Form.CrownGapCenterT >= 0.0f &&
            FMath::Abs(BranchT - Form.CrownGapCenterT) < Form.CrownGapHalfWidthT;
        const bool bDamaged = Form.DamageModulo > 0 &&
            (BranchIndex + Form.SeedOffset) % Form.DamageModulo == Form.DamageRemainder;
        const float LengthScale = FMath::Clamp(
            SectorScale(AngleDegrees) *
                (bInGap ? Form.CrownGapLengthScale : 1.0f) *
                (bDamaged ? Form.DamagedBranchLengthScale : 1.0f),
            0.16f,
            1.0f);
        const float CrownProfile = FMath::Pow(1.0f - BranchT, 0.62f);
        const float BranchLength = Form.CrownRadiusCm *
            (0.22f + CrownProfile * 0.78f) *
            FMath::Lerp(0.80f, 1.14f, Noise01(Seed + 3)) * LengthScale;
        const FVector Start = LeanAtZ(StartZ) + Horizontal * 12.0f + FVector(0.0f, 0.0f, StartZ);
        const float SideBend = (Noise01(Seed + 4) - 0.5f) * 58.0f * Form.Asymmetry;
        const FVector Mid = Start + Horizontal * BranchLength * 0.55f + Side * SideBend +
            FVector::UpVector * BranchLength * (0.04f + BranchT * 0.11f) * Form.BranchUplift;
        const FVector End = Start + Horizontal * BranchLength + Side * SideBend * 0.45f +
            FVector::UpVector * BranchLength * (0.10f + BranchT * 0.34f) * Form.BranchUplift;
        const float BaseRadius = FMath::Lerp(18.0f, 5.0f, BranchT) *
            FMath::Clamp(Form.BaseRadiusCm / 72.0f, 0.55f, 1.25f);
        const FVector CollarEnd = FMath::Lerp(Start, Mid, 0.18f);
        AppendNativeCanopyTaperedSegment(
            Start, CollarEnd, BaseRadius * 1.28f, BaseRadius * 0.82f, 10,
            WoodyVertices, WoodyTriangles, WoodyNormals, WoodyUVs);
        AppendNativeCanopyTaperedSegment(
            FMath::Lerp(Start, Mid, 0.12f), Mid, BaseRadius * 0.88f, BaseRadius * 0.58f, 9,
            WoodyVertices, WoodyTriangles, WoodyNormals, WoodyUVs);
        AppendNativeCanopyTaperedSegment(
            Mid, End, BaseRadius * 0.62f, bDamaged ? 2.4f : 1.1f, 7,
            WoodyVertices, WoodyTriangles, WoodyNormals, WoodyUVs);

        const FVector MainDirection = (End - Mid).GetSafeNormal();
        const int32 MainSprayCount = bDamaged ? 6 : (bInGap ? 9 : 13);
        for (int32 SprayIndex = 0; SprayIndex < MainSprayCount; ++SprayIndex)
        {
            const float SprayT = FMath::Lerp(
                0.12f,
                0.93f,
                MainSprayCount == 1
                    ? 0.5f
                    : static_cast<float>(SprayIndex) / (MainSprayCount - 1));
            const FVector SprayCenter =
                SprayT < 0.50f
                    ? FMath::Lerp(Start, Mid, SprayT * 2.0f)
                    : FMath::Lerp(Mid, End, (SprayT - 0.50f) * 2.0f);
            const float SprayScale = FMath::Lerp(1.0f, 0.66f, SprayT) *
                FMath::Lerp(0.88f, 1.12f, Noise01(Seed + 20 + SprayIndex));
            AddTerminalCluster(
                SprayCenter,
                MainDirection,
                102.0f * SprayScale,
                176.0f * SprayScale,
                Seed + SprayIndex * 3);
        }

        const int32 SecondaryCount = bDamaged ? 3 : 6;
        for (int32 SecondaryIndex = 0; SecondaryIndex < SecondaryCount; ++SecondaryIndex)
        {
            const float SecondaryT = 0.24f + SecondaryIndex * 0.145f;
            const float SideSign = (BranchIndex + SecondaryIndex) % 2 == 0 ? 1.0f : -1.0f;
            const FVector SecondaryStart = FMath::Lerp(Mid, End, SecondaryT);
            const FVector SecondaryDirection = (
                MainDirection * 0.46f + Side * SideSign * 0.82f + FVector::UpVector * 0.12f)
                                                    .GetSafeNormal();
            const float SecondaryLength = BranchLength *
                FMath::Lerp(0.15f, 0.22f, Noise01(Seed + 40 + SecondaryIndex));
            const FVector SecondaryEnd = SecondaryStart + SecondaryDirection * SecondaryLength;
            AppendNativeCanopyTaperedSegment(
                SecondaryStart, SecondaryEnd, 3.0f, 0.40f, 6,
                WoodyVertices, WoodyTriangles, WoodyNormals, WoodyUVs);
            for (int32 SecondarySprayIndex = 0; SecondarySprayIndex < 3; ++SecondarySprayIndex)
            {
                const float SecondarySprayT = 0.40f + SecondarySprayIndex * 0.25f;
                AddTerminalCluster(
                    FMath::Lerp(SecondaryStart, SecondaryEnd, SecondarySprayT),
                    SecondaryDirection,
                    FMath::Lerp(78.0f, 104.0f, Noise01(Seed + 50 + SecondaryIndex * 7 + SecondarySprayIndex)),
                    FMath::Lerp(124.0f, 164.0f, Noise01(Seed + 60 + SecondaryIndex * 7 + SecondarySprayIndex)),
                    Seed + SecondaryIndex * 11 + SecondarySprayIndex * 5 + 11);
            }

            const FVector SecondarySide =
                FVector::CrossProduct(SecondaryDirection, FVector::UpVector).GetSafeNormal();
            for (int32 TertiaryIndex = 0; TertiaryIndex < 3; ++TertiaryIndex)
            {
                const float TertiaryT = 0.30f + TertiaryIndex * 0.22f;
                const float TertiarySign =
                    (BranchIndex + SecondaryIndex + TertiaryIndex) % 2 == 0 ? 1.0f : -1.0f;
                const FVector TertiaryStart =
                    FMath::Lerp(SecondaryStart, SecondaryEnd, TertiaryT);
                const FVector TertiaryDirection = (
                    SecondaryDirection * 0.54f +
                    SecondarySide * TertiarySign * 0.76f +
                    FVector::UpVector * (0.12f + TertiaryIndex * 0.04f))
                                                        .GetSafeNormal();
                const float TertiaryLength = FMath::Lerp(
                    38.0f,
                    68.0f,
                    Noise01(Seed + 90 + SecondaryIndex * 13 + TertiaryIndex));
                const FVector TertiaryEnd = TertiaryStart + TertiaryDirection * TertiaryLength;
                AppendNativeCanopyTaperedSegment(
                    TertiaryStart,
                    TertiaryEnd,
                    0.95f,
                    0.12f,
                    5,
                    WoodyVertices,
                    WoodyTriangles,
                    WoodyNormals,
                    WoodyUVs);
                AddTerminalCluster(
                    FMath::Lerp(TertiaryStart, TertiaryEnd, 0.70f),
                    TertiaryDirection,
                    FMath::Lerp(62.0f, 82.0f, Noise01(Seed + 110 + TertiaryIndex)),
                    FMath::Lerp(94.0f, 128.0f, Noise01(Seed + 120 + TertiaryIndex)),
                    Seed + SecondaryIndex * 17 + TertiaryIndex * 7 + 29);
            }
        }

        const int32 InteriorShootCount = bDamaged ? 2 : 5;
        for (int32 InteriorIndex = 0; InteriorIndex < InteriorShootCount; ++InteriorIndex)
        {
            const float InteriorT = 0.26f + InteriorIndex * 0.13f;
            const float InteriorSign = InteriorIndex % 2 == 0 ? 1.0f : -1.0f;
            const FVector InteriorStart = FMath::Lerp(Start, End, InteriorT);
            const FVector InteriorDirection = (
                MainDirection * 0.52f + Side * InteriorSign * 0.56f +
                FVector::UpVector * FMath::Lerp(0.20f, 0.46f, BranchT))
                                                    .GetSafeNormal();
            const float InteriorLength = FMath::Lerp(
                46.0f,
                84.0f,
                Noise01(Seed + 140 + InteriorIndex));
            const FVector InteriorEnd = InteriorStart + InteriorDirection * InteriorLength;
            AppendNativeCanopyTaperedSegment(
                InteriorStart,
                InteriorEnd,
                1.15f,
                0.16f,
                5,
                WoodyVertices,
                WoodyTriangles,
                WoodyNormals,
                WoodyUVs);
            AddTerminalCluster(
                FMath::Lerp(InteriorStart, InteriorEnd, 0.68f),
                InteriorDirection,
                FMath::Lerp(68.0f, 92.0f, Noise01(Seed + 150 + InteriorIndex)),
                FMath::Lerp(108.0f, 148.0f, Noise01(Seed + 160 + InteriorIndex)),
                Seed + InteriorIndex * 19 + 53);
        }

        if (BranchT < 0.72f && BranchIndex % 2 == 0)
        {
            const FVector InnerDirection = (
                MainDirection * 0.46f +
                Side * ((BranchIndex % 4 == 0) ? 0.38f : -0.38f) +
                FVector::UpVector * FMath::Lerp(0.48f, 0.72f, BranchT))
                                                    .GetSafeNormal();
            AddTerminalCluster(
                FMath::Lerp(Start, Mid, 0.26f),
                InnerDirection,
                FMath::Lerp(72.0f, 94.0f, Noise01(Seed + 173)),
                FMath::Lerp(118.0f, 154.0f, Noise01(Seed + 179)),
                Seed + 181);
        }

        if (BranchIndex == FMath::Clamp(Form.BranchCount / 5, 0, Form.BranchCount - 1))
        {
            OutCloseupTarget = FMath::Lerp(Mid, End, 0.80f);
            OutCloseupCamera = OutCloseupTarget + Side * 320.0f + Horizontal * 140.0f +
                FVector::UpVector * 100.0f;
        }
    }

    for (int32 LeaderIndex = 0; LeaderIndex < 14; ++LeaderIndex)
    {
        const float Angle = 2.0f * PI * LeaderIndex / 14.0f;
        const float T = static_cast<float>(LeaderIndex) / 13.0f;
        const FVector Radial(FMath::Cos(Angle), FMath::Sin(Angle), 0.0f);
        const FVector Direction = (FVector::UpVector * 0.84f + Radial * 0.54f).GetSafeNormal();
        const FVector Center = LeanAtZ(Form.HeightCm * (0.78f + T * 0.18f)) +
            FVector(0.0f, 0.0f, Form.HeightCm * (0.78f + T * 0.18f)) +
            Radial * Form.CrownRadiusCm * FMath::Lerp(0.24f, 0.05f, T);
        if (bOpaqueNearGeometry)
        {
            const FVector LeaderRoot = LeanAtZ(Form.HeightCm * (0.76f + T * 0.17f)) +
                FVector(0.0f, 0.0f, Form.HeightCm * (0.76f + T * 0.17f));
            AppendNativeCanopyTaperedSegment(
                LeaderRoot,
                Center,
                FMath::Lerp(2.4f, 0.9f, T),
                0.35f,
                5,
                WoodyVertices,
                WoodyTriangles,
                WoodyNormals,
                WoodyUVs);
        }
        AddTerminalCluster(
            Center,
            Direction,
            FMath::Lerp(108.0f, 68.0f, T),
            FMath::Lerp(188.0f, 118.0f, T),
            Form.SeedOffset + LeaderIndex * 13);
    }
}

void BuildReducedNativeCanopyCardGeometry(
    const TArray<FVector>& SourceVertices,
    const TArray<int32>& SourceTriangles,
    const TArray<FVector>& SourceNormals,
    const TArray<FVector2D>& SourceUVs,
    int32 CardStride,
    float CardScale,
    TArray<FVector>& OutVertices,
    TArray<int32>& OutTriangles,
    TArray<FVector>& OutNormals,
    TArray<FVector2D>& OutUVs)
{
    check(CardStride > 0);
    check(SourceVertices.Num() % 4 == 0);
    check(SourceTriangles.Num() % 6 == 0);
    check(SourceNormals.Num() == SourceVertices.Num());
    check(SourceUVs.Num() == SourceVertices.Num());
    const int32 SourceCardCount = SourceVertices.Num() / 4;
    OutVertices.Reset();
    OutTriangles.Reset();
    OutNormals.Reset();
    OutUVs.Reset();
    OutVertices.Reserve(FMath::DivideAndRoundUp(SourceCardCount, CardStride) * 4);
    OutTriangles.Reserve(FMath::DivideAndRoundUp(SourceCardCount, CardStride) * 6);
    for (int32 SourceCardIndex = 0;
         SourceCardIndex < SourceCardCount;
         SourceCardIndex += CardStride)
    {
        const int32 SourceVertexStart = SourceCardIndex * 4;
        const FVector Center =
            (SourceVertices[SourceVertexStart] + SourceVertices[SourceVertexStart + 1] +
             SourceVertices[SourceVertexStart + 2] + SourceVertices[SourceVertexStart + 3]) * 0.25f;
        const int32 OutputVertexStart = OutVertices.Num();
        for (int32 Corner = 0; Corner < 4; ++Corner)
        {
            const int32 SourceVertexIndex = SourceVertexStart + Corner;
            OutVertices.Add(
                Center + (SourceVertices[SourceVertexIndex] - Center) * CardScale);
            OutNormals.Add(SourceNormals[SourceVertexIndex]);
            OutUVs.Add(SourceUVs[SourceVertexIndex]);
        }
        OutTriangles.Append({
            OutputVertexStart,
            OutputVertexStart + 2,
            OutputVertexStart + 1,
            OutputVertexStart,
            OutputVertexStart + 3,
            OutputVertexStart + 2});
    }
}

UStaticMesh* ConvertNativeCanopyProceduralActorToStaticMesh(
    AActor* Actor,
    const FString& PackagePath,
    UMaterialInterface* Material,
    bool bEnableNanite,
    ENaniteShapePreservation ShapePreservation,
    FString& OutSummary)
{
    const FString AssetName = FPackageName::GetLongPackageAssetName(PackagePath);
    const FString ObjectPath = FString::Printf(TEXT("%s.%s"), *PackagePath, *AssetName);
    UStaticMesh* ExistingMesh = LoadObject<UStaticMesh>(nullptr, *ObjectPath);
    UProceduralMeshComponent* Component = Actor ? Actor->FindComponentByClass<UProceduralMeshComponent>() : nullptr;
    if (!Component)
    {
        OutSummary += FString::Printf(TEXT("No procedural component available for %s.\n"), *PackagePath);
        return nullptr;
    }
    FMeshDescription MeshDescription = BuildMeshDescription(Component);
    if (MeshDescription.Polygons().Num() == 0)
    {
        OutSummary += FString::Printf(TEXT("Native-canopy mesh description is empty for %s.\n"), *PackagePath);
        return nullptr;
    }
    UPackage* Package = ExistingMesh ? ExistingMesh->GetOutermost() : CreatePackage(*PackagePath);
    UStaticMesh* Mesh = ExistingMesh ? ExistingMesh : (Package
        ? NewObject<UStaticMesh>(Package, *AssetName, RF_Public | RF_Standalone | RF_Transactional)
        : nullptr);
    if (!Mesh)
    {
        OutSummary += FString::Printf(TEXT("Failed to allocate native-canopy static mesh %s.\n"), *PackagePath);
        return nullptr;
    }
    Mesh->Modify();
    if (!ExistingMesh)
    {
        Mesh->InitResources();
    }
    Mesh->SetLightingGuid();
    Mesh->SetNumSourceModels(1);
    FStaticMeshSourceModel& SourceModel = Mesh->GetSourceModel(0);
    SourceModel.BuildSettings.bRecomputeNormals = false;
    SourceModel.BuildSettings.bRecomputeTangents = true;
    SourceModel.BuildSettings.bRemoveDegenerates = true;
    SourceModel.BuildSettings.bUseHighPrecisionTangentBasis = false;
    SourceModel.BuildSettings.bUseFullPrecisionUVs = false;
    SourceModel.BuildSettings.bGenerateLightmapUVs = true;
    SourceModel.BuildSettings.SrcLightmapIndex = 0;
    SourceModel.BuildSettings.DstLightmapIndex = 1;
    Mesh->CreateMeshDescription(0, MoveTemp(MeshDescription));
    Mesh->CommitMeshDescription(0);
    TArray<UMaterialInterface*> SectionMaterials;
    for (int32 SectionIndex = 0; SectionIndex < Component->GetNumSections(); ++SectionIndex)
    {
        UMaterialInterface* SectionMaterial = Component->GetMaterial(SectionIndex);
        if (!SectionMaterial)
        {
            SectionMaterial = Material
                ? Material
                : UMaterial::GetDefaultMaterial(MD_Surface);
        }
        SectionMaterials.AddUnique(SectionMaterial);
    }
    if (SectionMaterials.IsEmpty())
    {
        SectionMaterials.Add(
            Material ? Material : UMaterial::GetDefaultMaterial(MD_Surface));
    }
    Mesh->GetStaticMaterials().Empty();
    for (UMaterialInterface* SectionMaterial : SectionMaterials)
    {
        Mesh->GetStaticMaterials().Add(FStaticMaterial(SectionMaterial));
    }
    Mesh->SetImportVersion(EImportStaticMeshVersion::LastVersion);
    Mesh->SetLightMapCoordinateIndex(1);
    Mesh->GetNaniteSettings().bEnabled = bEnableNanite;
    Mesh->GetNaniteSettings().ShapePreservation = ShapePreservation;
    if (bEnableNanite &&
        Component->GetCollisionEnabled() != ECollisionEnabled::NoCollision)
    {
        // A collision-bearing Nanite mesh must keep a full fallback mesh:
        // Chaos complex collision reads the fallback, not Nanite clusters.
        // Reducing it with the automatic heuristic visibly decouples rocks,
        // rafts, and people from the authored terrain surface.
        Mesh->GetNaniteSettings().GenerateFallback = ENaniteGenerateFallback::Enabled;
        Mesh->GetNaniteSettings().FallbackTarget =
            ENaniteFallbackTarget::PercentTriangles;
        Mesh->GetNaniteSettings().FallbackPercentTriangles = 1.0f;
    }
    Mesh->Build(false);
    Mesh->PostEditChange();
    Mesh->MarkPackageDirty();
    if (!ExistingMesh)
    {
        FAssetRegistryModule::AssetCreated(Mesh);
    }
    FAssetCompilingManager::Get().FinishAllCompilation();

    const FString Filename =
        FPackageName::LongPackageNameToFilename(PackagePath, FPackageName::GetAssetPackageExtension());
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    if (!UPackage::SavePackage(Mesh->GetOutermost(), Mesh, *Filename, SaveArgs))
    {
        OutSummary += FString::Printf(TEXT("Failed to save native-canopy mesh %s.\n"), *ObjectPath);
        return nullptr;
    }
    OutSummary += FString::Printf(
        TEXT("Saved native-canopy mesh %s (Nanite %s, shape preservation %s, %d vertices, %d triangles).\n"),
        *ObjectPath,
        bEnableNanite ? TEXT("enabled") : TEXT("disabled"),
        ShapePreservation == ENaniteShapePreservation::PreserveArea ? TEXT("PreserveArea") : TEXT("None"),
        Mesh->GetNumVertices(0),
        Mesh->GetNumTriangles(0));
    return Mesh;
}

AActor* AddPreviewIrregularRockActor(
    UWorld* World,
    const FString& Label,
    const FVector& BaseLocation,
    float YawDegrees,
    const FVector& Scale,
    const FLinearColor& Color,
    int32 Seed)
{
    if (!World)
    {
        return nullptr;
    }

    constexpr int32 RingCount = 8;
    constexpr int32 SegmentCount = 20;
    const float YawRadians = FMath::DegreesToRadians(YawDegrees);
    const float CosYaw = FMath::Cos(YawRadians);
    const float SinYaw = FMath::Sin(YawRadians);
    const FVector Radii(
        FMath::Max(4.0f, Scale.X * 100.0f),
        FMath::Max(4.0f, Scale.Y * 100.0f),
        FMath::Max(3.0f, Scale.Z * 100.0f));

    TArray<FVector> Vertices;
    TArray<FVector2D> UVs;
    TArray<FLinearColor> VertexColors;
    TArray<int32> Triangles;
    Vertices.Reserve(RingCount * SegmentCount + 2);
    UVs.Reserve(RingCount * SegmentCount + 2);
    VertexColors.Reserve(RingCount * SegmentCount + 2);
    Triangles.Reserve(RingCount * SegmentCount * 6);

    for (int32 RingIndex = 0; RingIndex < RingCount; ++RingIndex)
    {
        const float V = static_cast<float>(RingIndex) / static_cast<float>(RingCount);
        const float AngleFromBase = V * HALF_PI;
        const float RingRadius = FMath::Cos(AngleFromBase);
        const float Height = FMath::Sin(AngleFromBase);
        for (int32 SegmentIndex = 0; SegmentIndex < SegmentCount; ++SegmentIndex)
        {
            const float U = static_cast<float>(SegmentIndex) / static_cast<float>(SegmentCount);
            const float Angle = U * 2.0f * PI;
            const float Noise =
                0.82f +
                0.20f * FMath::Sin(static_cast<float>(Seed) * 0.37f + static_cast<float>(RingIndex) * 1.19f + static_cast<float>(SegmentIndex) * 0.73f) +
                0.10f * FMath::Sin(static_cast<float>(Seed) * 0.11f - static_cast<float>(RingIndex) * 0.61f + static_cast<float>(SegmentIndex) * 1.47f);
            const float LocalX = FMath::Cos(Angle) * RingRadius * Radii.X * Noise;
            const float LocalY = FMath::Sin(Angle) * RingRadius * Radii.Y *
                (0.92f + 0.10f * FMath::Sin(static_cast<float>(Seed + SegmentIndex) * 0.53f));
            const float LocalZ = Height * Radii.Z *
                (0.88f + 0.10f * FMath::Sin(static_cast<float>(Seed) * 0.23f + static_cast<float>(SegmentIndex) * 0.91f));
            Vertices.Add(FVector(
                BaseLocation.X + LocalX * CosYaw - LocalY * SinYaw,
                BaseLocation.Y + LocalX * SinYaw + LocalY * CosYaw,
                BaseLocation.Z + LocalZ));
            UVs.Add(FVector2D(U, V));
            VertexColors.Add(ScalePreviewColor(Color, 0.58f + 0.10f * Noise + 0.03f * Height));
        }
    }

    const int32 TopIndex = Vertices.Num();
    Vertices.Add(FVector(BaseLocation.X, BaseLocation.Y, BaseLocation.Z + Radii.Z * 1.04f));
    UVs.Add(FVector2D(0.5f, 1.0f));
    VertexColors.Add(ScalePreviewColor(Color, 0.74f));

    const int32 BottomIndex = Vertices.Num();
    Vertices.Add(BaseLocation);
    UVs.Add(FVector2D(0.5f, 0.0f));
    VertexColors.Add(ScalePreviewColor(Color, 0.46f));

    for (int32 RingIndex = 0; RingIndex < RingCount - 1; ++RingIndex)
    {
        const int32 CurrentRing = RingIndex * SegmentCount;
        const int32 NextRing = (RingIndex + 1) * SegmentCount;
        for (int32 SegmentIndex = 0; SegmentIndex < SegmentCount; ++SegmentIndex)
        {
            const int32 NextSegment = (SegmentIndex + 1) % SegmentCount;
            const int32 A = CurrentRing + SegmentIndex;
            const int32 B = CurrentRing + NextSegment;
            const int32 C = NextRing + SegmentIndex;
            const int32 D = NextRing + NextSegment;
            Triangles.Add(A);
            Triangles.Add(C);
            Triangles.Add(B);
            Triangles.Add(B);
            Triangles.Add(C);
            Triangles.Add(D);
        }
    }

    const int32 LastRing = (RingCount - 1) * SegmentCount;
    for (int32 SegmentIndex = 0; SegmentIndex < SegmentCount; ++SegmentIndex)
    {
        const int32 NextSegment = (SegmentIndex + 1) % SegmentCount;
        Triangles.Add(LastRing + SegmentIndex);
        Triangles.Add(TopIndex);
        Triangles.Add(LastRing + NextSegment);

        Triangles.Add(BottomIndex);
        Triangles.Add(NextSegment);
        Triangles.Add(SegmentIndex);
    }

    const TArray<FVector> Normals = ComputePreviewMeshNormals(Vertices, Triangles);
    return AddPreviewProceduralMeshActor(
        World,
        Label,
        Vertices,
        Triangles,
        Normals,
        UVs,
        Color,
        LoadOrCreatePreviewVertexColorMaterial(),
        &VertexColors);
}

AActor* AddPreviewProceduralLeafClusterActor(
    UWorld* World,
    const FString& Label,
    const FVector& BaseLocation,
    float YawDegrees,
    const FVector& Scale,
    const FLinearColor& Color,
    int32 Seed,
    bool bRainforest)
{
    if (!World)
    {
        return nullptr;
    }

    constexpr int32 RingCount = 5;
    constexpr int32 SegmentCount = 8;
    const float YawRadians = FMath::DegreesToRadians(YawDegrees);
    const float CosYaw = FMath::Cos(YawRadians);
    const float SinYaw = FMath::Sin(YawRadians);
    const float FirstPartyProceduralCanopyBlobDemotion = bRainforest ? 0.72f : 0.82f;
    const FVector Radii(
        FMath::Max(8.0f, Scale.X * 100.0f * FirstPartyProceduralCanopyBlobDemotion),
        FMath::Max(8.0f, Scale.Y * 100.0f * FirstPartyProceduralCanopyBlobDemotion),
        FMath::Max(6.0f, Scale.Z * 100.0f * (bRainforest ? 0.86f : 0.90f)));

    TArray<FVector> Vertices;
    TArray<FVector2D> UVs;
    TArray<FLinearColor> VertexColors;
    TArray<int32> Triangles;
    Vertices.Reserve(RingCount * SegmentCount + 2);
    UVs.Reserve(RingCount * SegmentCount + 2);
    VertexColors.Reserve(RingCount * SegmentCount + 2);
    Triangles.Reserve(RingCount * SegmentCount * 6);

    for (int32 RingIndex = 0; RingIndex < RingCount; ++RingIndex)
    {
        const float RingT = static_cast<float>(RingIndex) / static_cast<float>(RingCount - 1);
        const float LocalZUnit = FMath::Lerp(-0.58f, 0.72f, RingT);
        const float RingRadius = FMath::Sqrt(FMath::Max(0.0f, 1.0f - LocalZUnit * LocalZUnit));
        for (int32 SegmentIndex = 0; SegmentIndex < SegmentCount; ++SegmentIndex)
        {
            const float SegmentT = static_cast<float>(SegmentIndex) / static_cast<float>(SegmentCount);
            const float Angle = SegmentT * 2.0f * PI;
            const float LobeNoise =
                0.72f +
                0.22f * FMath::Sin(static_cast<float>(Seed) * 0.31f + static_cast<float>(RingIndex) * 1.13f + static_cast<float>(SegmentIndex) * 0.91f) +
                0.18f * FMath::Sin(static_cast<float>(Seed) * 0.17f - static_cast<float>(RingIndex) * 0.47f + static_cast<float>(SegmentIndex) * 1.61f);
            const float LeafGap =
                0.90f + 0.12f * FMath::Sin(static_cast<float>(SegmentIndex) * (bRainforest ? 2.31f : 1.73f) + static_cast<float>(Seed) * 0.07f);
            const float LocalX = FMath::Cos(Angle) * RingRadius * Radii.X * LobeNoise;
            const float LocalY = FMath::Sin(Angle) * RingRadius * Radii.Y * LeafGap;
            const float LocalZ = LocalZUnit * Radii.Z *
                (0.86f + 0.14f * FMath::Sin(static_cast<float>(Seed) * 0.19f + static_cast<float>(SegmentIndex) * 0.67f));
            Vertices.Add(FVector(
                BaseLocation.X + LocalX * CosYaw - LocalY * SinYaw,
                BaseLocation.Y + LocalX * SinYaw + LocalY * CosYaw,
                BaseLocation.Z + LocalZ));
            UVs.Add(FVector2D(SegmentT, RingT));
            const float HeightTint = 0.82f + 0.16f * RingT;
            const float LeafTint = 0.82f + 0.12f * LobeNoise + (bRainforest ? 0.04f : 0.0f);
            VertexColors.Add(ScalePreviewColor(Color, HeightTint * LeafTint * (bRainforest ? 0.86f : 0.90f)));
        }
    }

    const int32 TopIndex = Vertices.Num();
    Vertices.Add(FVector(BaseLocation.X, BaseLocation.Y, BaseLocation.Z + Radii.Z * 0.86f));
    UVs.Add(FVector2D(0.5f, 1.0f));
    VertexColors.Add(ScalePreviewColor(Color, bRainforest ? 0.90f : 0.88f));

    const int32 BottomIndex = Vertices.Num();
    Vertices.Add(FVector(BaseLocation.X, BaseLocation.Y, BaseLocation.Z - Radii.Z * 0.56f));
    UVs.Add(FVector2D(0.5f, 0.0f));
    VertexColors.Add(ScalePreviewColor(Color, 0.58f));

    for (int32 RingIndex = 0; RingIndex < RingCount - 1; ++RingIndex)
    {
        const int32 CurrentRing = RingIndex * SegmentCount;
        const int32 NextRing = (RingIndex + 1) * SegmentCount;
        for (int32 SegmentIndex = 0; SegmentIndex < SegmentCount; ++SegmentIndex)
        {
            const int32 NextSegment = (SegmentIndex + 1) % SegmentCount;
            const int32 A = CurrentRing + SegmentIndex;
            const int32 B = CurrentRing + NextSegment;
            const int32 C = NextRing + SegmentIndex;
            const int32 D = NextRing + NextSegment;
            Triangles.Add(A);
            Triangles.Add(C);
            Triangles.Add(B);
            Triangles.Add(B);
            Triangles.Add(C);
            Triangles.Add(D);
        }
    }

    const int32 FirstRing = 0;
    const int32 LastRing = (RingCount - 1) * SegmentCount;
    for (int32 SegmentIndex = 0; SegmentIndex < SegmentCount; ++SegmentIndex)
    {
        const int32 NextSegment = (SegmentIndex + 1) % SegmentCount;
        Triangles.Add(LastRing + SegmentIndex);
        Triangles.Add(TopIndex);
        Triangles.Add(LastRing + NextSegment);

        Triangles.Add(BottomIndex);
        Triangles.Add(FirstRing + NextSegment);
        Triangles.Add(FirstRing + SegmentIndex);
    }

    const TArray<FVector> Normals = ComputePreviewMeshNormals(Vertices, Triangles);
    return AddPreviewProceduralMeshActor(
        World,
        Label,
        Vertices,
        Triangles,
        Normals,
        UVs,
        Color,
        LoadOrCreatePreviewVertexColorMaterial(),
        &VertexColors);
}

AActor* AddPreviewOrganicLeafSprayActor(
    UWorld* World,
    const FString& Label,
    const FVector& BaseLocation,
    float YawDegrees,
    const FVector& Scale,
    const FLinearColor& Color,
    int32 Seed,
    bool bRainforest)
{
    if (!World)
    {
        return nullptr;
    }

    const int32 LeafCount = bRainforest ? 18 : 12;
    const float YawRadians = FMath::DegreesToRadians(YawDegrees);
    const FVector BaseForward(FMath::Cos(YawRadians), FMath::Sin(YawRadians), 0.0f);
    const FVector BaseRight(-FMath::Sin(YawRadians), FMath::Cos(YawRadians), 0.0f);
    const FVector Up(0.0f, 0.0f, 1.0f);
    const FVector Radii(
        FMath::Max(16.0f, Scale.X * 100.0f),
        FMath::Max(12.0f, Scale.Y * 100.0f),
        FMath::Max(10.0f, Scale.Z * 100.0f));
    const float FoliageCardSilhouetteDemotion = bRainforest ? 0.62f : 0.70f;
    const float LeafCardWidthScale = bRainforest ? 0.54f : 0.62f;

    TArray<FVector> Vertices;
    TArray<FVector2D> UVs;
    TArray<FLinearColor> VertexColors;
    TArray<int32> Triangles;
    Vertices.Reserve(LeafCount * 4);
    UVs.Reserve(LeafCount * 4);
    VertexColors.Reserve(LeafCount * 4);
    Triangles.Reserve(LeafCount * 6);

    for (int32 LeafIndex = 0; LeafIndex < LeafCount; ++LeafIndex)
    {
        const float LeafT = static_cast<float>(LeafIndex) / static_cast<float>(FMath::Max(1, LeafCount - 1));
        const float Angle = YawRadians + static_cast<float>(LeafIndex) * (bRainforest ? 2.399f : 2.117f) +
            static_cast<float>(Seed) * 0.013f;
        const float RadialT = FMath::Sqrt(FMath::Frac(0.211f + 0.618034f * static_cast<float>(LeafIndex)));
        const float VerticalT = FMath::Sin(static_cast<float>(Seed) * 0.071f + static_cast<float>(LeafIndex) * 1.317f);
        const FVector RadialDir(FMath::Cos(Angle), FMath::Sin(Angle), 0.0f);
        const FVector TangentDir = (RadialDir * (0.78f + 0.12f * FMath::Sin(LeafT * PI)) +
            Up * (bRainforest ? 0.34f : 0.22f) * FMath::Sin(Angle * 1.7f + static_cast<float>(Seed) * 0.031f)).GetSafeNormal();
        const FVector WidthDir = FVector::CrossProduct(TangentDir, Up).GetSafeNormal();
        const FVector FallbackWidthDir =
            (BaseRight * (0.72f + 0.18f * FMath::Sin(Angle)) + BaseForward * 0.18f).GetSafeNormal();
        const FVector LeafWidthDir = WidthDir.IsNearlyZero() ? FallbackWidthDir : WidthDir;

        const FVector LeafCenter = BaseLocation +
            RadialDir * (Radii.X * RadialT * (0.28f + 0.44f * FMath::Abs(FMath::Sin(Angle * 0.73f)))) +
            BaseRight * (Radii.Y * 0.20f * FMath::Sin(static_cast<float>(LeafIndex) * 1.91f + static_cast<float>(Seed) * 0.017f)) +
            Up * (Radii.Z * (0.14f + 0.52f * LeafT + 0.18f * VerticalT));
        const float LeafLength = Radii.X * (bRainforest ? 0.20f : 0.15f) * FoliageCardSilhouetteDemotion *
            (0.62f + 0.26f * FMath::Abs(FMath::Sin(static_cast<float>(LeafIndex) * 0.83f + static_cast<float>(Seed) * 0.029f)));
        const float LeafWidth = Radii.Y * (bRainforest ? 0.050f : 0.040f) * LeafCardWidthScale *
            (0.78f + 0.18f * FMath::Abs(FMath::Cos(static_cast<float>(LeafIndex) * 1.23f)));
        const float TipLift = Radii.Z * (bRainforest ? 0.030f : 0.020f) *
            FMath::Sin(static_cast<float>(LeafIndex) * 0.61f + static_cast<float>(Seed) * 0.043f);

        const int32 BaseVertexIndex = Vertices.Num();
        Vertices.Add(LeafCenter - TangentDir * LeafLength - LeafWidthDir * LeafWidth);
        Vertices.Add(LeafCenter - TangentDir * LeafLength * 0.30f + LeafWidthDir * LeafWidth * 0.82f + Up * TipLift);
        Vertices.Add(LeafCenter + TangentDir * LeafLength + LeafWidthDir * LeafWidth * 0.34f + Up * TipLift * 1.4f);
        Vertices.Add(LeafCenter + TangentDir * LeafLength * 0.22f - LeafWidthDir * LeafWidth * 0.92f);
        UVs.Add(FVector2D(0.0f, 0.0f));
        UVs.Add(FVector2D(0.0f, 1.0f));
        UVs.Add(FVector2D(1.0f, 1.0f));
        UVs.Add(FVector2D(1.0f, 0.0f));

        const float LeafShade = 0.76f + 0.20f * LeafT +
            0.10f * FMath::Sin(static_cast<float>(Seed) * 0.037f + static_cast<float>(LeafIndex) * 0.97f);
        const FLinearColor InnerLeafColor = ScalePreviewColor(Color, LeafShade * (bRainforest ? 0.92f : 0.88f));
        const FLinearColor OuterLeafColor = ScalePreviewColor(Color, LeafShade * (bRainforest ? 0.92f : 0.90f));
        VertexColors.Add(InnerLeafColor);
        VertexColors.Add(OuterLeafColor);
        VertexColors.Add(ScalePreviewColor(OuterLeafColor, 0.96f));
        VertexColors.Add(ScalePreviewColor(InnerLeafColor, 0.90f));

        Triangles.Add(BaseVertexIndex);
        Triangles.Add(BaseVertexIndex + 1);
        Triangles.Add(BaseVertexIndex + 2);
        Triangles.Add(BaseVertexIndex);
        Triangles.Add(BaseVertexIndex + 2);
        Triangles.Add(BaseVertexIndex + 3);
    }

    const TArray<FVector> Normals = ComputePreviewMeshNormals(Vertices, Triangles);
    AActor* Actor = AddPreviewProceduralMeshActor(
        World,
        Label,
        Vertices,
        Triangles,
        Normals,
        UVs,
        Color,
        LoadOrCreatePreviewVertexColorMaterial(),
        &VertexColors);
    if (Actor)
    {
        TArray<UProceduralMeshComponent*> MeshComponents;
        Actor->GetComponents<UProceduralMeshComponent>(MeshComponents);
        for (UProceduralMeshComponent* MeshComponent : MeshComponents)
        {
            if (MeshComponent)
            {
                MeshComponent->SetCollisionEnabled(ECollisionEnabled::NoCollision);
            }
        }
    }
    return Actor;
}

AActor* AddPreviewOrganicBranchFrondActor(
    UWorld* World,
    const FString& Label,
    const FVector& BaseLocation,
    float YawDegrees,
    const FVector& Scale,
    const FLinearColor& Color,
    int32 Seed,
    bool bRainforest,
    bool bUnderstory)
{
    if (!World)
    {
        return nullptr;
    }

    const float YawRadians = FMath::DegreesToRadians(YawDegrees);
    const FVector BaseForward(FMath::Cos(YawRadians), FMath::Sin(YawRadians), 0.0f);
    const FVector BaseRight(-FMath::Sin(YawRadians), FMath::Cos(YawRadians), 0.0f);
    const FVector Up(0.0f, 0.0f, 1.0f);
    const FVector Radii(
        FMath::Max(18.0f, Scale.X * 100.0f),
        FMath::Max(14.0f, Scale.Y * 100.0f),
        FMath::Max(12.0f, Scale.Z * 100.0f));
    const int32 BranchCount = bRainforest ? (bUnderstory ? 7 : 9) : (bUnderstory ? 5 : 7);
    const int32 LeavesPerBranch = bRainforest ? (bUnderstory ? 6 : 8) : (bUnderstory ? 4 : 6);

    TArray<FVector> Vertices;
    TArray<FVector2D> UVs;
    TArray<FLinearColor> VertexColors;
    TArray<int32> Triangles;
    Vertices.Reserve(BranchCount * (LeavesPerBranch * 4 + 8));
    UVs.Reserve(BranchCount * (LeavesPerBranch * 4 + 8));
    VertexColors.Reserve(BranchCount * (LeavesPerBranch * 4 + 8));
    Triangles.Reserve(BranchCount * (LeavesPerBranch * 6 + 12));

    auto AddQuad = [&Vertices, &UVs, &VertexColors, &Triangles](
                       const FVector& A,
                       const FVector& B,
                       const FVector& C,
                       const FVector& D,
                       const FLinearColor& ColorA,
                       const FLinearColor& ColorB)
    {
        const int32 BaseVertexIndex = Vertices.Num();
        Vertices.Add(A);
        Vertices.Add(B);
        Vertices.Add(C);
        Vertices.Add(D);
        UVs.Add(FVector2D(0.0f, 0.0f));
        UVs.Add(FVector2D(0.0f, 1.0f));
        UVs.Add(FVector2D(1.0f, 1.0f));
        UVs.Add(FVector2D(1.0f, 0.0f));
        VertexColors.Add(ColorA);
        VertexColors.Add(ColorA);
        VertexColors.Add(ColorB);
        VertexColors.Add(ColorB);
        Triangles.Add(BaseVertexIndex);
        Triangles.Add(BaseVertexIndex + 1);
        Triangles.Add(BaseVertexIndex + 2);
        Triangles.Add(BaseVertexIndex);
        Triangles.Add(BaseVertexIndex + 2);
        Triangles.Add(BaseVertexIndex + 3);
    };

    const FLinearColor BranchColor = ScalePreviewColor(
        bRainforest ? FLinearColor(0.018f, 0.020f, 0.014f) : FLinearColor(0.115f, 0.072f, 0.038f),
        bUnderstory ? 0.82f : 0.92f);
    for (int32 BranchIndex = 0; BranchIndex < BranchCount; ++BranchIndex)
    {
        const float BranchT = static_cast<float>(BranchIndex) / static_cast<float>(FMath::Max(1, BranchCount - 1));
        const float Angle = YawRadians +
            (BranchT - 0.5f) * (bRainforest ? 2.8f : 2.2f) +
            FMath::Sin(static_cast<float>(Seed) * 0.023f + static_cast<float>(BranchIndex) * 1.71f) * 0.48f;
        const FVector RadialDir(FMath::Cos(Angle), FMath::Sin(Angle), 0.0f);
        const FVector BranchDir = (RadialDir * (bRainforest ? 0.78f : 0.86f) +
                                   Up * (bRainforest ? (bUnderstory ? 0.34f : 0.48f) : (bUnderstory ? 0.25f : 0.36f)))
                                      .GetSafeNormal();
        const FVector WidthDirRaw = FVector::CrossProduct(BranchDir, Up).GetSafeNormal();
        const FVector WidthDir = WidthDirRaw.IsNearlyZero() ? BaseRight : WidthDirRaw;
        const float BranchLength = Radii.X * (bRainforest ? 0.72f : 0.56f) *
            (0.78f + 0.18f * FMath::Abs(FMath::Sin(static_cast<float>(Seed) * 0.031f + static_cast<float>(BranchIndex) * 0.83f)));
        const FVector BranchBase = BaseLocation +
            BaseRight * (Radii.Y * 0.20f * FMath::Sin(static_cast<float>(BranchIndex) * 1.19f + static_cast<float>(Seed) * 0.017f)) +
            Up * (Radii.Z * (bUnderstory ? 0.08f : 0.16f) * FMath::Sin(static_cast<float>(BranchIndex) * 0.67f));
        const float BranchHalfWidth = FMath::Max(1.8f, Radii.Y * (bRainforest ? 0.010f : 0.012f));

        const FVector BranchMid = BranchBase + BranchDir * (BranchLength * 0.52f) +
            Up * (Radii.Z * 0.10f * FMath::Sin(static_cast<float>(BranchIndex) * 1.37f));
        const FVector BranchTip = BranchBase + BranchDir * BranchLength +
            RadialDir * (Radii.Y * 0.10f * FMath::Sin(static_cast<float>(Seed) * 0.011f + static_cast<float>(BranchIndex))) +
            Up * (Radii.Z * (bRainforest ? 0.12f : 0.07f));
        AddQuad(
            BranchBase - WidthDir * BranchHalfWidth,
            BranchBase + WidthDir * BranchHalfWidth,
            BranchMid + WidthDir * BranchHalfWidth * 0.70f,
            BranchMid - WidthDir * BranchHalfWidth * 0.70f,
            BranchColor,
            ScalePreviewColor(BranchColor, 0.78f));
        AddQuad(
            BranchMid - WidthDir * BranchHalfWidth * 0.70f,
            BranchMid + WidthDir * BranchHalfWidth * 0.70f,
            BranchTip + WidthDir * BranchHalfWidth * 0.36f,
            BranchTip - WidthDir * BranchHalfWidth * 0.36f,
            ScalePreviewColor(BranchColor, 0.82f),
            ScalePreviewColor(BranchColor, 0.58f));

        for (int32 LeafIndex = 0; LeafIndex < LeavesPerBranch; ++LeafIndex)
        {
            const float LeafT = (static_cast<float>(LeafIndex) + 1.0f) / static_cast<float>(LeavesPerBranch + 1);
            const float SideSign = (LeafIndex % 2 == 0) ? -1.0f : 1.0f;
            const FVector LeafForward = (BranchDir * 0.72f + RadialDir * (0.22f * SideSign) + Up * (bRainforest ? 0.10f : 0.06f)).GetSafeNormal();
            const FVector LeafWidthDirRaw = FVector::CrossProduct(LeafForward, Up).GetSafeNormal();
            const FVector LeafWidthDir = LeafWidthDirRaw.IsNearlyZero() ? WidthDir : LeafWidthDirRaw;
            const float LeafNoise =
                0.72f +
                0.18f * FMath::Sin(static_cast<float>(Seed) * 0.037f + static_cast<float>(LeafIndex) * 1.27f) +
                0.12f * FMath::Sin(static_cast<float>(BranchIndex) * 1.09f + static_cast<float>(LeafIndex) * 0.73f);
            const FVector LeafCenter = BranchBase +
                BranchDir * (BranchLength * LeafT) +
                WidthDir * (SideSign * Radii.Y * (bRainforest ? 0.055f : 0.045f) * (0.8f + LeafT)) +
                Up * (Radii.Z * 0.045f * FMath::Sin(static_cast<float>(LeafIndex) * 1.53f + static_cast<float>(Seed) * 0.019f));
            const float LeafLength = Radii.X * (bRainforest ? 0.075f : 0.058f) *
                (0.72f + 0.22f * FMath::Abs(LeafNoise));
            const float LeafHalfWidth = Radii.Y * (bRainforest ? 0.024f : 0.020f) *
                (0.66f + 0.18f * FMath::Abs(FMath::Cos(static_cast<float>(LeafIndex) * 0.91f)));
            const float Shade = 0.70f + 0.22f * LeafT + 0.08f * FMath::Sin(static_cast<float>(Seed) * 0.041f + static_cast<float>(LeafIndex) * 0.61f);
            const FLinearColor LeafBaseColor = ScalePreviewColor(Color, Shade * (bRainforest ? 0.78f : 0.76f));
            const FLinearColor LeafTipColor = ScalePreviewColor(Color, Shade * (bRainforest ? 0.94f : 0.88f));
            AddQuad(
                LeafCenter - LeafForward * LeafLength * 0.70f,
                LeafCenter + LeafWidthDir * LeafHalfWidth,
                LeafCenter + LeafForward * LeafLength + Up * (LeafLength * 0.12f),
                LeafCenter - LeafWidthDir * LeafHalfWidth,
                LeafBaseColor,
                LeafTipColor);
        }
    }

    const TArray<FVector> Normals = ComputePreviewMeshNormals(Vertices, Triangles);
    AActor* Actor = AddPreviewProceduralMeshActor(
        World,
        Label,
        Vertices,
        Triangles,
        Normals,
        UVs,
        Color,
        LoadOrCreatePreviewVertexColorMaterial(),
        &VertexColors);
    if (Actor)
    {
        TArray<UProceduralMeshComponent*> MeshComponents;
        Actor->GetComponents<UProceduralMeshComponent>(MeshComponents);
        for (UProceduralMeshComponent* MeshComponent : MeshComponents)
        {
            if (MeshComponent)
            {
                MeshComponent->SetCollisionEnabled(ECollisionEnabled::NoCollision);
            }
        }
    }
    return Actor;
}

AActor* AddPreviewFineTwigCanopyLaceActor(
    UWorld* World,
    const FString& Label,
    const FVector& BaseLocation,
    float YawDegrees,
    const FVector& Scale,
    const FLinearColor& Color,
    int32 Seed,
    bool bRainforest)
{
    if (!World)
    {
        return nullptr;
    }

    const float YawRadians = FMath::DegreesToRadians(YawDegrees);
    const FVector BaseForward(FMath::Cos(YawRadians), FMath::Sin(YawRadians), 0.0f);
    const FVector BaseRight(-FMath::Sin(YawRadians), FMath::Cos(YawRadians), 0.0f);
    const FVector Up(0.0f, 0.0f, 1.0f);
    const FVector Radii(
        FMath::Max(20.0f, Scale.X * 100.0f),
        FMath::Max(16.0f, Scale.Y * 100.0f),
        FMath::Max(14.0f, Scale.Z * 100.0f));
    const int32 TwigCount = bRainforest ? 20 : 14;
    const int32 LeafletsPerTwig = bRainforest ? 5 : 4;

    TArray<FVector> Vertices;
    TArray<FVector2D> UVs;
    TArray<FLinearColor> VertexColors;
    TArray<int32> Triangles;
    Vertices.Reserve(TwigCount * (LeafletsPerTwig + 2) * 4);
    UVs.Reserve(TwigCount * (LeafletsPerTwig + 2) * 4);
    VertexColors.Reserve(TwigCount * (LeafletsPerTwig + 2) * 4);
    Triangles.Reserve(TwigCount * (LeafletsPerTwig + 2) * 6);

    auto AddQuad = [&Vertices, &UVs, &VertexColors, &Triangles](
                       const FVector& A,
                       const FVector& B,
                       const FVector& C,
                       const FVector& D,
                       const FLinearColor& ColorA,
                       const FLinearColor& ColorB)
    {
        const int32 BaseVertexIndex = Vertices.Num();
        Vertices.Add(A);
        Vertices.Add(B);
        Vertices.Add(C);
        Vertices.Add(D);
        UVs.Add(FVector2D(0.0f, 0.0f));
        UVs.Add(FVector2D(0.0f, 1.0f));
        UVs.Add(FVector2D(1.0f, 1.0f));
        UVs.Add(FVector2D(1.0f, 0.0f));
        VertexColors.Add(ColorA);
        VertexColors.Add(ColorA);
        VertexColors.Add(ColorB);
        VertexColors.Add(ColorB);
        Triangles.Add(BaseVertexIndex);
        Triangles.Add(BaseVertexIndex + 1);
        Triangles.Add(BaseVertexIndex + 2);
        Triangles.Add(BaseVertexIndex);
        Triangles.Add(BaseVertexIndex + 2);
        Triangles.Add(BaseVertexIndex + 3);
    };

    const FLinearColor TwigColor = bRainforest
        ? FLinearColor(0.014f, 0.020f, 0.012f)
        : FLinearColor(0.075f, 0.052f, 0.030f);
    for (int32 TwigIndex = 0; TwigIndex < TwigCount; ++TwigIndex)
    {
        const float TwigT = static_cast<float>(TwigIndex) / static_cast<float>(FMath::Max(1, TwigCount - 1));
        const float Angle = YawRadians + static_cast<float>(TwigIndex) * (bRainforest ? 2.033f : 2.417f) +
            static_cast<float>(Seed) * 0.019f;
        const FVector RadialDir(FMath::Cos(Angle), FMath::Sin(Angle), 0.0f);
        const FVector SweepDir = (RadialDir * (0.70f + 0.10f * FMath::Sin(TwigT * PI)) +
                                  BaseForward * (0.10f * FMath::Sin(static_cast<float>(TwigIndex) * 0.91f)) +
                                  Up * (bRainforest ? 0.42f : 0.30f))
                                     .GetSafeNormal();
        const FVector WidthDirRaw = FVector::CrossProduct(SweepDir, Up).GetSafeNormal();
        const FVector WidthDir = WidthDirRaw.IsNearlyZero() ? BaseRight : WidthDirRaw;
        const float RadiusT = FMath::Sqrt(FMath::Frac(0.173f + 0.618034f * static_cast<float>(TwigIndex)));
        const FVector TwigRoot = BaseLocation +
            RadialDir * (Radii.X * RadiusT * 0.18f) +
            BaseRight * (Radii.Y * 0.18f * FMath::Sin(static_cast<float>(Seed) * 0.011f + static_cast<float>(TwigIndex) * 1.73f)) +
            Up * (Radii.Z * (0.10f + 0.28f * TwigT));
        const float TwigLength = Radii.X * (bRainforest ? 0.46f : 0.36f) *
            (0.72f + 0.18f * FMath::Abs(FMath::Sin(static_cast<float>(Seed) * 0.023f + static_cast<float>(TwigIndex) * 0.79f)));
        const float TwigHalfWidth = FMath::Max(0.85f, Radii.Y * (bRainforest ? 0.0045f : 0.0055f));
        const FVector TwigMid = TwigRoot + SweepDir * (TwigLength * 0.56f) +
            Up * (Radii.Z * 0.045f * FMath::Sin(static_cast<float>(TwigIndex) * 1.37f));
        const FVector TwigTip = TwigRoot + SweepDir * TwigLength +
            RadialDir * (Radii.Y * 0.08f * FMath::Sin(static_cast<float>(Seed) * 0.017f + static_cast<float>(TwigIndex))) +
            Up * (Radii.Z * (bRainforest ? 0.070f : 0.045f));

        AddQuad(
            TwigRoot - WidthDir * TwigHalfWidth,
            TwigRoot + WidthDir * TwigHalfWidth,
            TwigMid + WidthDir * TwigHalfWidth * 0.58f,
            TwigMid - WidthDir * TwigHalfWidth * 0.58f,
            ScalePreviewColor(TwigColor, 0.90f),
            ScalePreviewColor(TwigColor, 0.68f));
        AddQuad(
            TwigMid - WidthDir * TwigHalfWidth * 0.58f,
            TwigMid + WidthDir * TwigHalfWidth * 0.58f,
            TwigTip + WidthDir * TwigHalfWidth * 0.22f,
            TwigTip - WidthDir * TwigHalfWidth * 0.22f,
            ScalePreviewColor(TwigColor, 0.74f),
            ScalePreviewColor(TwigColor, 0.50f));

        for (int32 LeafletIndex = 0; LeafletIndex < LeafletsPerTwig; ++LeafletIndex)
        {
            const float LeafT = (static_cast<float>(LeafletIndex) + 1.0f) / static_cast<float>(LeafletsPerTwig + 1);
            const float SideSign = (LeafletIndex % 2 == 0) ? -1.0f : 1.0f;
            const FVector LeafForward = (SweepDir * 0.68f + RadialDir * (0.24f * SideSign) + Up * (bRainforest ? 0.12f : 0.06f)).GetSafeNormal();
            const FVector LeafWidthDirRaw = FVector::CrossProduct(LeafForward, Up).GetSafeNormal();
            const FVector LeafWidthDir = LeafWidthDirRaw.IsNearlyZero() ? WidthDir : LeafWidthDirRaw;
            const FVector LeafCenter = TwigRoot +
                SweepDir * (TwigLength * LeafT) +
                WidthDir * (SideSign * Radii.Y * (bRainforest ? 0.030f : 0.024f) * (0.70f + LeafT)) +
                Up * (Radii.Z * 0.030f * FMath::Sin(static_cast<float>(LeafletIndex) * 1.41f + static_cast<float>(Seed) * 0.031f));
            const float LeafLength = Radii.X * (bRainforest ? 0.036f : 0.028f) *
                (0.70f + 0.16f * FMath::Abs(FMath::Sin(static_cast<float>(TwigIndex) * 0.83f + static_cast<float>(LeafletIndex))));
            const float LeafHalfWidth = Radii.Y * (bRainforest ? 0.012f : 0.009f) *
                (0.68f + 0.14f * FMath::Abs(FMath::Cos(static_cast<float>(LeafletIndex) * 0.91f + static_cast<float>(Seed) * 0.013f)));
            const float LeafShade = 0.64f + 0.22f * LeafT +
                0.08f * FMath::Sin(static_cast<float>(Seed) * 0.037f + static_cast<float>(TwigIndex) * 0.53f + static_cast<float>(LeafletIndex));
            const FLinearColor LeafBaseColor = ScalePreviewColor(Color, LeafShade * (bRainforest ? 0.74f : 0.70f));
            const FLinearColor LeafTipColor = ScalePreviewColor(Color, LeafShade * (bRainforest ? 0.92f : 0.84f));
            AddQuad(
                LeafCenter - LeafForward * LeafLength * 0.72f,
                LeafCenter + LeafWidthDir * LeafHalfWidth,
                LeafCenter + LeafForward * LeafLength + Up * (LeafLength * 0.10f),
                LeafCenter - LeafWidthDir * LeafHalfWidth,
                LeafBaseColor,
                LeafTipColor);
        }
    }

    const TArray<FVector> Normals = ComputePreviewMeshNormals(Vertices, Triangles);
    AActor* Actor = AddPreviewProceduralMeshActor(
        World,
        Label,
        Vertices,
        Triangles,
        Normals,
        UVs,
        Color,
        LoadOrCreatePreviewVertexColorMaterial(),
        &VertexColors);
    if (Actor)
    {
        TArray<UProceduralMeshComponent*> MeshComponents;
        Actor->GetComponents<UProceduralMeshComponent>(MeshComponents);
        for (UProceduralMeshComponent* MeshComponent : MeshComponents)
        {
            if (MeshComponent)
            {
                MeshComponent->SetCollisionEnabled(ECollisionEnabled::NoCollision);
            }
        }
    }
    return Actor;
}

void AddPreviewFoliageCrownDepthAndLeafletBreakupDetail(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview,
    const FRaftSimPreviewImage* WaterMask,
    const FRaftSimPreviewImage* VegetationMask)
{
    if (!World)
    {
        return;
    }

    const bool bRainforest = Spec.bHasWaterfalls;
    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const float RemainingBlockyFoliageProxyCull = 0.38f;
    const int32 CrownCount = Spec.bDesertCanyon ? 10 : (bRainforest ? 32 : 20);
    const int32 ShadowQuadsPerCrown = 1;
    const int32 LeafletsPerCrown = Spec.bDesertCanyon ? 3 : (bRainforest ? 7 : 5);
    const float NearBankOffset = Spec.bDesertCanyon ? 1120.0f : (bRainforest ? 700.0f : 720.0f);
    const float FarBankOffset = Spec.bDesertCanyon ? 2200.0f : (bRainforest ? 1680.0f : 1260.0f);
    const float FoliageCardSilhouetteDemotion =
        (Spec.bDesertCanyon ? 0.66f : (bRainforest ? 0.42f : 0.48f)) * RemainingBlockyFoliageProxyCull;
    const float FirstPartyProceduralCanopyBlobDemotion =
        Spec.bDesertCanyon ? 0.64f : (bRainforest ? 0.48f : 0.54f);
    const FVector Up(0.0f, 0.0f, 1.0f);

    TArray<FVector> Vertices;
    TArray<FVector2D> UVs;
    TArray<FLinearColor> VertexColors;
    TArray<int32> Triangles;
    Vertices.Reserve(CrownCount * (ShadowQuadsPerCrown + LeafletsPerCrown) * 4);
    UVs.Reserve(CrownCount * (ShadowQuadsPerCrown + LeafletsPerCrown) * 4);
    VertexColors.Reserve(CrownCount * (ShadowQuadsPerCrown + LeafletsPerCrown) * 4);
    Triangles.Reserve(CrownCount * (ShadowQuadsPerCrown + LeafletsPerCrown) * 6);

    auto AddQuad = [&Vertices, &UVs, &VertexColors, &Triangles](
                       const FVector& A,
                       const FVector& B,
                       const FVector& C,
                       const FVector& D,
                       const FLinearColor& ColorA,
                       const FLinearColor& ColorB)
    {
        const int32 BaseVertexIndex = Vertices.Num();
        Vertices.Add(A);
        Vertices.Add(B);
        Vertices.Add(C);
        Vertices.Add(D);
        UVs.Add(FVector2D(0.0f, 0.0f));
        UVs.Add(FVector2D(0.0f, 1.0f));
        UVs.Add(FVector2D(1.0f, 1.0f));
        UVs.Add(FVector2D(1.0f, 0.0f));
        VertexColors.Add(ColorA);
        VertexColors.Add(ScalePreviewColor(ColorA, 0.94f));
        VertexColors.Add(ColorB);
        VertexColors.Add(ScalePreviewColor(ColorB, 0.90f));
        Triangles.Add(BaseVertexIndex);
        Triangles.Add(BaseVertexIndex + 1);
        Triangles.Add(BaseVertexIndex + 2);
        Triangles.Add(BaseVertexIndex);
        Triangles.Add(BaseVertexIndex + 2);
        Triangles.Add(BaseVertexIndex + 3);
    };

    for (int32 CrownIndex = 0; CrownIndex < CrownCount; ++CrownIndex)
    {
        const float T = static_cast<float>(CrownIndex) / static_cast<float>(FMath::Max(1, CrownCount - 1));
        const float Phase = static_cast<float>(CrownIndex) * 1.237f;
        const float Side = (CrownIndex % 2 == 0) ? -1.0f : 1.0f;
        const float BaseX = FMath::Lerp(2700.0f, 26050.0f, T) +
            220.0f * FMath::Sin(Phase * 1.09f) +
            90.0f * FMath::Sin(Phase * 0.41f);
        const float OffsetWave = FMath::Pow(
            FMath::Abs(FMath::Sin(Phase * (Spec.bDesertCanyon ? 0.58f : 0.63f))),
            Spec.bDesertCanyon ? 0.72f : 0.48f);
        const float BaseOffset = ActiveRiverHalfWidth + NearBankOffset + FarBankOffset * OffsetWave;

        float X = BaseX;
        float SignedOffset = Side * BaseOffset;
        float BestScore = -1000.0f;
        for (int32 CandidateIndex = 0; CandidateIndex < 6; ++CandidateIndex)
        {
            const float CandidateX = BaseX + 185.0f * FMath::Sin(Phase + static_cast<float>(CandidateIndex) * 0.93f);
            const float CandidateOffset = FMath::Max(
                ActiveRiverHalfWidth + NearBankOffset * 0.70f,
                BaseOffset + 215.0f * FMath::Sin(Phase * 0.46f + static_cast<float>(CandidateIndex) * 1.17f));
            const float CandidateY = GetPreviewRiverCenterY(Spec, CandidateX) + Side * CandidateOffset;
            const float WaterT = SamplePreviewMaskAtWorld(Spec, WaterMask, CandidateX, CandidateY);
            const float VegetationT = SamplePreviewMaskAtWorld(Spec, VegetationMask, CandidateX, CandidateY);
            const float BankPreference =
                1.0f - FMath::Clamp(
                    FMath::Abs(CandidateOffset - (ActiveRiverHalfWidth + NearBankOffset + FarBankOffset * 0.34f)) /
                        FMath::Max(1.0f, FarBankOffset),
                    0.0f,
                    1.0f);
            const float Score = Spec.bDesertCanyon
                ? BankPreference * 0.82f + (1.0f - WaterT) * 0.44f + (1.0f - VegetationT) * 0.08f
                : BankPreference * 0.58f + VegetationT * (bRainforest ? 1.44f : 1.02f) - WaterT * 0.58f;
            if (Score > BestScore)
            {
                BestScore = Score;
                X = CandidateX;
                SignedOffset = Side * CandidateOffset;
            }
        }

        if (X < 3150.0f && FMath::Abs(SignedOffset) < ActiveRiverHalfWidth + 1060.0f)
        {
            continue;
        }

        const float Y = GetPreviewRiverCenterY(Spec, X) + SignedOffset;
        const float TerrainZ = GetPreviewTerrainHeightCm(Spec, X, Y, TerrainRelief, HeightfieldPreview);
        const float VegetationT = SamplePreviewMaskAtWorld(Spec, VegetationMask, X, Y);
        const float WaterT = SamplePreviewMaskAtWorld(Spec, WaterMask, X, Y);
        const float YawDegrees = static_cast<float>((CrownIndex * 47) % 360);
        const float YawRadians = FMath::DegreesToRadians(YawDegrees);
        const FVector BaseForward(FMath::Cos(YawRadians), FMath::Sin(YawRadians), 0.0f);
        const FVector BaseRight(-FMath::Sin(YawRadians), FMath::Cos(YawRadians), 0.0f);
        const FVector CrownCenter(
            X,
            Y,
            TerrainZ + (Spec.bDesertCanyon ? 82.0f : (bRainforest ? 350.0f : 214.0f)) +
                18.0f * FMath::Sin(Phase));
        const float CrownRadiusX = (Spec.bDesertCanyon ? 70.0f : (bRainforest ? 210.0f : 138.0f)) * FirstPartyProceduralCanopyBlobDemotion;
        const float CrownRadiusY = (Spec.bDesertCanyon ? 42.0f : (bRainforest ? 148.0f : 96.0f)) * FirstPartyProceduralCanopyBlobDemotion;
        const float CrownRadiusZ = (Spec.bDesertCanyon ? 42.0f : (bRainforest ? 145.0f : 86.0f)) * (Spec.bDesertCanyon ? 0.88f : (bRainforest ? 0.78f : 0.82f));
        const FLinearColor CanopyLow = Spec.bDesertCanyon
            ? FLinearColor(0.19f, 0.20f, 0.10f)
            : (bRainforest ? FLinearColor(0.014f, 0.070f, 0.024f) : FLinearColor(0.070f, 0.150f, 0.045f));
        const FLinearColor CanopyHigh = Spec.bDesertCanyon
            ? FLinearColor(0.38f, 0.35f, 0.18f)
            : (bRainforest ? FLinearColor(0.070f, 0.245f, 0.060f) : FLinearColor(0.165f, 0.280f, 0.080f));
        const FLinearColor CrownBaseColor = ScalePreviewColor(
            FMath::Lerp(CanopyLow, FMath::Lerp(Spec.FoliageColor, CanopyHigh, 0.50f), 0.48f + VegetationT * 0.30f),
            0.78f + 0.06f * static_cast<float>(CrownIndex % 5) - WaterT * 0.05f);
        const FLinearColor CrownShadowColor = Spec.bDesertCanyon
            ? ScalePreviewColor(FLinearColor(0.090f, 0.090f, 0.050f), 0.78f)
            : ScalePreviewColor(
                  bRainforest ? FLinearColor(0.008f, 0.025f, 0.012f) : FLinearColor(0.030f, 0.055f, 0.022f),
                  0.86f);

        for (int32 ShadowIndex = 0; ShadowIndex < ShadowQuadsPerCrown; ++ShadowIndex)
        {
            const float ShadowT =
                (static_cast<float>(ShadowIndex) + 1.0f) / static_cast<float>(ShadowQuadsPerCrown + 1);
            const float Angle = YawRadians +
                (ShadowT - 0.5f) * (bRainforest ? 2.20f : 1.65f) +
                0.35f * FMath::Sin(Phase + static_cast<float>(ShadowIndex));
            const FVector RadialDir(FMath::Cos(Angle), FMath::Sin(Angle), 0.0f);
            const FVector WidthDir = (BaseRight * 0.68f + RadialDir * 0.32f).GetSafeNormal();
            const FVector ShadowCenter = CrownCenter +
                RadialDir * (CrownRadiusX * (0.10f + 0.18f * ShadowT)) -
                BaseForward * (CrownRadiusY * 0.10f) -
                Up * (CrownRadiusZ * (0.18f + 0.08f * FMath::Sin(Phase)));
            const float ShadowWidth =
                CrownRadiusY * (Spec.bDesertCanyon ? 0.36f : (bRainforest ? 0.58f : 0.50f)) * FoliageCardSilhouetteDemotion;
            const float ShadowHeight =
                CrownRadiusZ * (Spec.bDesertCanyon ? 0.50f : (bRainforest ? 0.64f : 0.58f)) * FoliageCardSilhouetteDemotion;
            AddQuad(
                ShadowCenter - WidthDir * ShadowWidth - Up * ShadowHeight * 0.48f,
                ShadowCenter + WidthDir * ShadowWidth - Up * ShadowHeight * 0.40f,
                ShadowCenter + WidthDir * ShadowWidth * 0.78f + Up * ShadowHeight * 0.48f,
                ShadowCenter - WidthDir * ShadowWidth * 0.72f + Up * ShadowHeight * 0.42f,
                ScalePreviewColor(CrownShadowColor, 0.74f + ShadowT * 0.08f),
                ScalePreviewColor(CrownBaseColor, 0.54f + ShadowT * 0.10f));
        }

        for (int32 LeafletIndex = 0; LeafletIndex < LeafletsPerCrown; ++LeafletIndex)
        {
            const float LeafT = static_cast<float>(LeafletIndex) / static_cast<float>(FMath::Max(1, LeafletsPerCrown - 1));
            const float Angle = YawRadians +
                static_cast<float>(LeafletIndex) * (bRainforest ? 2.399f : 2.117f) +
                static_cast<float>(CrownIndex) * 0.037f;
            const float RadialT = FMath::Sqrt(FMath::Frac(0.257f + 0.618034f * static_cast<float>(LeafletIndex)));
            const FVector RadialDir(FMath::Cos(Angle), FMath::Sin(Angle), 0.0f);
            const FVector LeafForward =
                (RadialDir * (0.78f + 0.10f * FMath::Sin(LeafT * PI)) +
                 BaseForward * (0.12f * FMath::Sin(Phase + static_cast<float>(LeafletIndex) * 0.77f)) +
                 Up * (Spec.bDesertCanyon ? 0.08f : (bRainforest ? 0.30f : 0.20f)))
                    .GetSafeNormal();
            const FVector LeafWidthDirRaw = FVector::CrossProduct(LeafForward, Up).GetSafeNormal();
            const FVector LeafWidthDir = LeafWidthDirRaw.IsNearlyZero() ? BaseRight : LeafWidthDirRaw;
            const FVector LeafCenter = CrownCenter +
                RadialDir * (CrownRadiusX * (0.22f + 0.58f * RadialT)) +
                BaseRight * (CrownRadiusY * 0.16f * FMath::Sin(Phase * 0.73f + static_cast<float>(LeafletIndex) * 1.31f)) +
                Up * (CrownRadiusZ * (-0.18f + 0.70f * LeafT + 0.12f * FMath::Sin(Angle)));
            const float LeafLength = CrownRadiusX * (Spec.bDesertCanyon ? 0.16f : (bRainforest ? 0.12f : 0.11f)) *
                FoliageCardSilhouetteDemotion *
                (0.70f + 0.20f * FMath::Abs(FMath::Sin(Phase + static_cast<float>(LeafletIndex) * 0.91f)));
            const float LeafHalfWidth = CrownRadiusY * (Spec.bDesertCanyon ? 0.038f : (bRainforest ? 0.026f : 0.030f)) *
                (Spec.bDesertCanyon ? 0.72f : (bRainforest ? 0.52f : 0.58f)) *
                (0.70f + 0.16f * FMath::Abs(FMath::Cos(Angle * 0.73f)));
            const float Shade = 0.66f + 0.24f * LeafT +
                0.08f * FMath::Sin(Phase * 0.91f + static_cast<float>(LeafletIndex) * 0.83f);
            const FLinearColor LeafBaseColor = ScalePreviewColor(CrownBaseColor, Shade * (bRainforest ? 0.74f : 0.78f));
            const FLinearColor LeafTipColor = ScalePreviewColor(CrownBaseColor, Shade * (bRainforest ? 0.88f : 0.86f));
            AddQuad(
                LeafCenter - LeafForward * LeafLength * 0.74f,
                LeafCenter + LeafWidthDir * LeafHalfWidth,
                LeafCenter + LeafForward * LeafLength + Up * (LeafLength * (bRainforest ? 0.16f : 0.10f)),
                LeafCenter - LeafWidthDir * LeafHalfWidth,
                LeafBaseColor,
                LeafTipColor);
        }
    }

    if (Vertices.IsEmpty() || Triangles.IsEmpty())
    {
        return;
    }

    const TArray<FVector> Normals = ComputePreviewMeshNormals(Vertices, Triangles);
    AActor* Actor = AddPreviewProceduralMeshActor(
        World,
        FString::Printf(TEXT("RaftSim_FoliageCrownDepthAndLeafletBreakup_%s"), *Spec.RiverId),
        Vertices,
        Triangles,
        Normals,
        UVs,
        Spec.FoliageColor,
        LoadOrCreatePreviewVertexColorMaterial(),
        &VertexColors);
    if (Actor)
    {
        TArray<UProceduralMeshComponent*> MeshComponents;
        Actor->GetComponents<UProceduralMeshComponent>(MeshComponents);
        for (UProceduralMeshComponent* MeshComponent : MeshComponents)
        {
            if (MeshComponent)
            {
                MeshComponent->SetCollisionEnabled(ECollisionEnabled::NoCollision);
            }
        }
    }
}

void AddPreviewBoulderSurfaceFacet(
    UWorld* World,
    const FString& Label,
    const FVector& Center,
    const FVector& LongAxis,
    const FVector& ShortAxis,
    const FLinearColor& InnerColor,
    const FLinearColor& OuterColor)
{
    if (!World)
    {
        return;
    }

    TArray<FVector> Vertices;
    Vertices.Add(Center - LongAxis - ShortAxis * 0.70f);
    Vertices.Add(Center - LongAxis * 0.35f + ShortAxis);
    Vertices.Add(Center + LongAxis + ShortAxis * 0.62f);
    Vertices.Add(Center + LongAxis * 0.48f - ShortAxis);

    TArray<int32> Triangles = {0, 1, 2, 0, 2, 3};
    TArray<FVector> Normals = ComputePreviewMeshNormals(Vertices, Triangles);
    TArray<FVector2D> UVs = {
        FVector2D(0.0f, 0.0f),
        FVector2D(0.0f, 1.0f),
        FVector2D(1.0f, 1.0f),
        FVector2D(1.0f, 0.0f)};
    TArray<FLinearColor> VertexColors = {
        ScalePreviewColor(InnerColor, 0.88f),
        ScalePreviewColor(OuterColor, 0.96f),
        ScalePreviewColor(OuterColor, 1.08f),
        ScalePreviewColor(InnerColor, 1.02f)};

    AActor* Actor = AddPreviewProceduralMeshActor(
        World,
        Label,
        Vertices,
        Triangles,
        Normals,
        UVs,
        InnerColor,
        LoadOrCreatePreviewVertexColorMaterial(),
        &VertexColors);
    if (Actor)
    {
        TArray<UProceduralMeshComponent*> MeshComponents;
        Actor->GetComponents<UProceduralMeshComponent>(MeshComponents);
        for (UProceduralMeshComponent* MeshComponent : MeshComponents)
        {
            if (MeshComponent)
            {
                MeshComponent->SetCollisionEnabled(ECollisionEnabled::NoCollision);
            }
        }
    }
}

void AddPreviewBoulderSurfaceVariationDetail(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FVector& BaseLocation,
    float YawDegrees,
    const FVector& Scale,
    int32 BoulderIndex,
    float WaterMaskT,
    float VegetationMaskT,
    bool bNearCameraReviewBoulder)
{
    if (!World)
    {
        return;
    }

    const float YawRadians = FMath::DegreesToRadians(YawDegrees);
    const FVector Forward(FMath::Cos(YawRadians), FMath::Sin(YawRadians), 0.0f);
    const FVector Right(-FMath::Sin(YawRadians), FMath::Cos(YawRadians), 0.0f);
    const float RadiusX = FMath::Max(18.0f, Scale.X * 100.0f);
    const float RadiusY = FMath::Max(12.0f, Scale.Y * 100.0f);
    const float RadiusZ = FMath::Max(8.0f, Scale.Z * 100.0f);
    const float Wetness = FMath::Clamp(0.22f + WaterMaskT * 0.62f, 0.0f, 0.86f);
    const float MossSediment = FMath::Clamp((Spec.bHasWaterfalls ? 0.28f : 0.08f) + VegetationMaskT * 0.48f, 0.0f, 0.70f);
    const float NearCameraFacetScale = bNearCameraReviewBoulder ? (Spec.bDesertCanyon ? 0.58f : 0.48f) : 1.0f;

    const FLinearColor WetFacet = FMath::Lerp(
        ScalePreviewColor(Spec.RockColor, Spec.bDesertCanyon ? 0.44f : 0.34f),
        ScalePreviewColor(Spec.WaterColor, Spec.bDesertCanyon ? 0.38f : 0.30f),
        Spec.bDesertCanyon ? 0.22f : 0.44f);
    const FLinearColor WetHighlight = Spec.bDesertCanyon
        ? FLinearColor(0.42f, 0.36f, 0.25f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.08f, 0.22f, 0.17f) : FLinearColor(0.34f, 0.38f, 0.31f));
    const FLinearColor Abrasion = Spec.bDesertCanyon
        ? FLinearColor(0.68f, 0.52f, 0.33f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.17f, 0.19f, 0.16f) : FLinearColor(0.48f, 0.46f, 0.38f));
    const FLinearColor TopHighlight = Spec.bDesertCanyon
        ? FLinearColor(0.66f, 0.52f, 0.34f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.16f, 0.20f, 0.15f) : FLinearColor(0.48f, 0.47f, 0.38f));
    const FLinearColor MossOrSediment = Spec.bDesertCanyon
        ? FLinearColor(0.42f, 0.30f, 0.16f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.035f, 0.16f, 0.055f) : FLinearColor(0.18f, 0.25f, 0.11f));
    const FLinearColor CreviceShadow = Spec.bDesertCanyon
        ? FLinearColor(0.15f, 0.10f, 0.065f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.010f, 0.028f, 0.020f) : FLinearColor(0.10f, 0.10f, 0.080f));

    const FVector UpLift(0.0f, 0.0f, 1.0f);
    const FVector WetCenter = BaseLocation +
        Forward * (RadiusX * (0.12f + 0.10f * FMath::Sin(static_cast<float>(BoulderIndex)))) -
        Right * (RadiusY * (0.60f + 0.12f * FMath::Cos(static_cast<float>(BoulderIndex) * 0.71f))) +
        UpLift * (RadiusZ * (0.26f + Wetness * 0.24f) + 4.0f);
    AddPreviewBoulderSurfaceFacet(
        World,
        FString::Printf(TEXT("RaftSim_BoulderWetSheenFacet_%02d_%s"), BoulderIndex, *Spec.RiverId),
        WetCenter,
        Forward * (RadiusX * (0.22f + 0.10f * Wetness)),
        (Right * (RadiusY * 0.10f) + UpLift * (RadiusZ * 0.035f)),
        WetFacet,
        ScalePreviewColor(FMath::Lerp(WetFacet, WetHighlight, 0.36f + Wetness * 0.28f), NearCameraFacetScale));

    const FVector AbrasionCenter = BaseLocation +
        Forward * (RadiusX * (0.10f + 0.22f * FMath::Sin(static_cast<float>(BoulderIndex) * 0.57f))) +
        Right * (RadiusY * (0.42f + 0.10f * FMath::Sin(static_cast<float>(BoulderIndex) * 1.11f))) +
        UpLift * (RadiusZ * 0.58f + 8.0f);
    AddPreviewBoulderSurfaceFacet(
        World,
        FString::Printf(TEXT("RaftSim_BoulderAbrasionFacet_%02d_%s"), BoulderIndex, *Spec.RiverId),
        AbrasionCenter,
        (Forward * (RadiusX * 0.18f) + UpLift * (RadiusZ * 0.045f)),
        Right * (RadiusY * 0.10f),
        FMath::Lerp(ScalePreviewColor(Spec.RockColor, 0.64f), Abrasion, 0.38f),
        ScalePreviewColor(Abrasion, NearCameraFacetScale));

    const FVector TopCenter = BaseLocation +
        Forward * (RadiusX * (0.02f + 0.16f * FMath::Sin(static_cast<float>(BoulderIndex) * 0.41f))) +
        Right * (RadiusY * (0.04f + 0.12f * FMath::Cos(static_cast<float>(BoulderIndex) * 0.73f))) +
        UpLift * (RadiusZ * 0.96f + 10.0f);
    AddPreviewBoulderSurfaceFacet(
        World,
        FString::Printf(TEXT("RaftSim_BoulderTopHighlightFacet_%02d_%s"), BoulderIndex, *Spec.RiverId),
        TopCenter,
        Forward * (RadiusX * 0.34f),
        Right * (RadiusY * 0.18f),
        ScalePreviewColor(FMath::Lerp(Abrasion, TopHighlight, 0.28f), NearCameraFacetScale),
        ScalePreviewColor(TopHighlight, bNearCameraReviewBoulder ? NearCameraFacetScale * 0.82f : 1.0f));

    const FVector MossCenter = BaseLocation -
        Forward * (RadiusX * (0.18f + 0.06f * FMath::Cos(static_cast<float>(BoulderIndex) * 0.63f))) +
        Right * (RadiusY * (0.18f - 0.34f * FMath::Sin(static_cast<float>(BoulderIndex) * 0.83f))) +
        UpLift * (RadiusZ * (0.36f + MossSediment * 0.30f) + 5.0f);
    AddPreviewBoulderSurfaceFacet(
        World,
        FString::Printf(TEXT("RaftSim_BoulderMossSedimentFacet_%02d_%s"), BoulderIndex, *Spec.RiverId),
        MossCenter,
        Forward * (RadiusX * (0.15f + MossSediment * 0.08f)),
        (Right * (RadiusY * 0.12f) + UpLift * (RadiusZ * 0.030f)),
        FMath::Lerp(ScalePreviewColor(Spec.RockColor, 0.40f), MossOrSediment, MossSediment),
        MossOrSediment);

    const FVector CreviceCenter = BaseLocation -
        Forward * (RadiusX * (0.06f + 0.14f * FMath::Sin(static_cast<float>(BoulderIndex) * 0.49f))) -
        Right * (RadiusY * (0.34f + 0.10f * FMath::Cos(static_cast<float>(BoulderIndex) * 1.17f))) +
        UpLift * (RadiusZ * (0.30f + Wetness * 0.12f) + 3.0f);
    AddPreviewBoulderSurfaceFacet(
        World,
        FString::Printf(TEXT("RaftSim_BoulderCreviceShadowFacet_%02d_%s"), BoulderIndex, *Spec.RiverId),
        CreviceCenter,
        Forward * (RadiusX * (0.18f + 0.05f * Wetness)),
        (Right * (RadiusY * 0.075f) + UpLift * (RadiusZ * 0.020f)),
        CreviceShadow,
        FMath::Lerp(CreviceShadow, ScalePreviewColor(Spec.RockColor, 0.30f), 0.28f));
}
} // namespace RaftSimEditorEnvironment
