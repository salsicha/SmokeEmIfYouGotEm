#pragma once
#include "RaftSimWaterRuntimeAdapter.h"
#include "RaftSimWaterFlowFrame.h"

// Immutable broad phase for the SAME continuous crest function. No height
// interpolation, quantization, profile-history reuse or site-order changes.
// Only physical sites have finite support suitable for this index. Unsupported
// inputs retain the full evaluator, including the legacy branch.
class FRaftSimIndexedBreakingProfile
{
    using FSite=URaftSimWaterRuntimeAdapter::FSupportBreakingSite;
    static constexpr double TileMeters=8.;
    TArray<FSite> Sites;
    TMap<FIntPoint,TArray<FSite>> Tiles;
    float Lift,Spacing,GlobalCap=0;
    bool bIndexed=false;
    static bool Tile(const FVector2D& P,FIntPoint& Out)
    {
        if (P.ContainsNaN() || FMath::Abs(P.X)>1.e8 || FMath::Abs(P.Y)>1.e8) return false;
        Out=FIntPoint(FMath::FloorToInt(P.X/TileMeters),FMath::FloorToInt(P.Y/TileMeters));
        return true;
    }
public:
    FRaftSimIndexedBreakingProfile(TConstArrayView<FSite> Input,float InLift,float InSpacing)
        : Lift(InLift),Spacing(InSpacing)
    {
        Sites.Append(Input.GetData(),Input.Num());
        int32 Entries=0;
        for (const FSite& Site:Sites)
        {
            const double Norm=Site.FlowDirection.SizeSquared();
            if (!FMath::IsFinite(Site.PhysicalCrestHeightMeters) || Site.PhysicalCrestHeightMeters<0 ||
                !FMath::IsFinite(Site.PhysicalCrestLengthMeters) || Site.RiverCoordinatesMeters.ContainsNaN() ||
                !FMath::IsFinite(Norm) || Norm<.25 || Norm>4.) { Tiles.Reset(); return; }
            const float Length=FMath::Clamp(Site.PhysicalCrestLengthMeters,2.f,7.f);
            if (!Site.bLocalEnvelopeCap)
                GlobalCap=FMath::Max(GlobalCap,FMath::Clamp(Site.PhysicalCrestHeightMeters,0.f,1.2f));
            FBox2D Bounds(ForceInit);
            // Invert ToLocal even for a slightly non-unit supplied direction.
            // Padding covers the evaluator's double-to-float support checks.
            for (double D:{-3.*Length-.01,7.*Length+.01}) for (double A:{-12.01,12.01})
                Bounds+=Site.RiverCoordinatesMeters+RaftSimWaterFlowFrame::ToField(FVector2D(D,A),Site.FlowDirection)/Norm;
            FIntPoint Low,High;
            if (!Tile(Bounds.Min,Low) || !Tile(Bounds.Max,High)) { Tiles.Reset(); return; }
            const int64 Count=int64(High.X-Low.X+1)*(High.Y-Low.Y+1);
            if (Count>65536-Entries) { Tiles.Reset(); return; }
            Entries+=int32(Count);
            for (int32 Y=Low.Y;Y<=High.Y;++Y) for (int32 X=Low.X;X<=High.X;++X)
                Tiles.FindOrAdd(FIntPoint(X,Y)).Add(Site); // Original sum order.
        }
        bIndexed=true;
    }
    bool IsIndexed() const { return bIndexed; }
    int32 TileCount() const { return Tiles.Num(); }
    float Sample(const FVector2D& P,float* Foam=nullptr) const
    {
        FIntPoint Key;
        if (!bIndexed || !Tile(P,Key))
            return URaftSimWaterRuntimeAdapter::ComputeCoupledBreakingReliefMeters(P,Sites,Lift,Spacing,Foam);
        const auto* Found=Tiles.Find(Key);
        const TConstArrayView<FSite> Local=Found ? TConstArrayView<FSite>(*Found) : TConstArrayView<FSite>();
        return URaftSimWaterRuntimeAdapter::ComputeCoupledBreakingReliefMeters(P,Local,Lift,Spacing,Foam,GlobalCap);
    }
};
