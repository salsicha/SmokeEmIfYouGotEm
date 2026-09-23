#pragma once
#include "RaftSimWaterRuntimeAdapter.h"
#include "RaftSimWaterFlowFrame.h"
#include "RaftSimPhysicalBreakingSample.h"
#include "RaftSimPreparedPhysicalBreakingSample.h"

// Immutable broad phase for the SAME continuous crest function. No height
// interpolation, quantization, profile-history reuse or site-order changes.
// Only physical sites have finite support suitable for this index. Unsupported
// inputs retain the full evaluator, including the legacy branch.
template<int32 TileSizeMeters=8>
class TRaftSimIndexedBreakingProfile
{
    static_assert(TileSizeMeters>0);
    using FSite=URaftSimWaterRuntimeAdapter::FSupportBreakingSite;
    static constexpr double TileMeters=double(TileSizeMeters);
    TArray<FSite> Sites;
    TMap<FIntPoint,TArray<FSite>> Tiles;
    // Immutable direct lookup of exactly the same ordered site subsets.
    // A bounded rectangular table avoids hashing every refinement sample.
    // Own the copied subsets: normal copy/move cannot leave dangling pointers.
    TArray<TArray<FSite>> DenseTiles;
    using FPreparedSite=RaftSimPreparedPhysicalBreakingSample::FSite;
    TMap<FIntPoint,TArray<FPreparedSite>> PreparedTiles;
    TArray<TArray<FPreparedSite>> PreparedDenseTiles;
    bool bPrepared=false;
    FIntPoint DenseOrigin=FIntPoint::ZeroValue,DenseSize=FIntPoint::ZeroValue;
    float Lift,Spacing,GlobalCap=0;
    bool bIndexed=false;
    static bool Tile(const FVector2D& P,FIntPoint& Out)
    {
        if (P.ContainsNaN() || FMath::Abs(P.X)>1.e8 || FMath::Abs(P.Y)>1.e8) return false;
        Out=FIntPoint(FMath::FloorToInt(P.X/TileMeters),FMath::FloorToInt(P.Y/TileMeters));
        return true;
    }
public:
    TRaftSimIndexedBreakingProfile(TConstArrayView<FSite> Input,float InLift,float InSpacing)
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
        if (!Tiles.IsEmpty())
        {
            FIntPoint Low(MAX_int32,MAX_int32),High(MIN_int32,MIN_int32);
            for (const auto& Entry:Tiles)
            {
                Low.X=FMath::Min(Low.X,Entry.Key.X);Low.Y=FMath::Min(Low.Y,Entry.Key.Y);
                High.X=FMath::Max(High.X,Entry.Key.X);High.Y=FMath::Max(High.Y,Entry.Key.Y);
            }
            const int64 Width=int64(High.X)-Low.X+1,Height=int64(High.Y)-Low.Y+1;
            // Widely separated sites keep the existing sparse hash path.
            if (Width*Height<=65536)
            {
                DenseOrigin=Low;DenseSize=FIntPoint(int32(Width),int32(Height));
                DenseTiles.SetNum(int32(Width*Height));
                for (const auto& Entry:Tiles)
                    DenseTiles[(Entry.Key.Y-Low.Y)*DenseSize.X+Entry.Key.X-Low.X]=Entry.Value;
            }
        }
    }
    bool IsIndexed() const { return bIndexed; }
    int32 TileCount() const { return Tiles.Num(); }
    int32 DenseTileCount() const { return DenseTiles.Num(); }
    // Explicit trial preparation. Ordinary indexes allocate no prepared tables.
    void PreparePhysicalConstants()
    {
        if(bPrepared || !bIndexed)return;
        const auto Prepare=[](const TArray<FSite>& In,TArray<FPreparedSite>& Out)
        {Out.Reserve(In.Num());for(const auto& S:In)Out.Emplace(S);};
        if(!DenseTiles.IsEmpty())
        {
            PreparedDenseTiles.SetNum(DenseTiles.Num());
            for(int32 I=0;I<DenseTiles.Num();++I)Prepare(DenseTiles[I],PreparedDenseTiles[I]);
        }
        else for(const auto& Entry:Tiles)Prepare(Entry.Value,PreparedTiles.Add(Entry.Key));
        bPrepared=true;
    }
    float SamplePrepared(const FVector2D& P,float* Foam=nullptr) const
    {
        FIntPoint Key;
        if(!bPrepared || !Tile(P,Key))return Sample(P,Foam);
        const TArray<FPreparedSite>* Found=nullptr;
        if(!PreparedDenseTiles.IsEmpty())
        {
            const int32 X=Key.X-DenseOrigin.X,Y=Key.Y-DenseOrigin.Y;
            if(X>=0 && Y>=0 && X<DenseSize.X && Y<DenseSize.Y)Found=&PreparedDenseTiles[Y*DenseSize.X+X];
        }
        else Found=PreparedTiles.Find(Key);
        const TConstArrayView<FPreparedSite> Local=Found ? TConstArrayView<FPreparedSite>(*Found) : TConstArrayView<FPreparedSite>();
        return Foam ? RaftSimPreparedPhysicalBreakingSample::Evaluate<true>(P,Local,GlobalCap,Foam)
                    : RaftSimPreparedPhysicalBreakingSample::Evaluate<false>(P,Local,GlobalCap,nullptr);
    }
    float Sample(const FVector2D& P,float* Foam=nullptr,bool bDense=true) const
    { return SampleWithEmptyTileSkip(P,Foam,bDense,false); }
    float SamplePhysicalInline(const FVector2D& P,float* Foam=nullptr) const
    {
        FIntPoint Key;
        if(!bIndexed || !Tile(P,Key))
            return URaftSimWaterRuntimeAdapter::ComputeCoupledBreakingReliefMeters(P,Sites,Lift,Spacing,Foam);
        const TArray<FSite>* Found=nullptr;
        if(!DenseTiles.IsEmpty())
        {
            const int32 X=Key.X-DenseOrigin.X,Y=Key.Y-DenseOrigin.Y;
            if(X>=0 && Y>=0 && X<DenseSize.X && Y<DenseSize.Y)
                Found=&DenseTiles[Y*DenseSize.X+X];
        }
        else Found=Tiles.Find(Key);
        const TConstArrayView<FSite> Local=Found ? TConstArrayView<FSite>(*Found) : TConstArrayView<FSite>();
        return Foam ? RaftSimPhysicalBreakingSample::Evaluate<true>(P,Local,GlobalCap,Foam)
                    : RaftSimPhysicalBreakingSample::Evaluate<false>(P,Local,GlobalCap,nullptr);
    }
    float SampleWithEmptyTileSkip(const FVector2D& P,float* Foam,bool bDense,bool bSkipEmpty) const
    {
        FIntPoint Key;
        if (!bIndexed || !Tile(P,Key))
            return URaftSimWaterRuntimeAdapter::ComputeCoupledBreakingReliefMeters(P,Sites,Lift,Spacing,Foam);
        const TArray<FSite>* Found=nullptr;
        if (bDense && !DenseTiles.IsEmpty())
        {
            const int32 X=Key.X-DenseOrigin.X,Y=Key.Y-DenseOrigin.Y;
            if (X>=0 && Y>=0 && X<DenseSize.X && Y<DenseSize.Y)
                Found=&DenseTiles[Y*DenseSize.X+X];
        }
        else Found=Tiles.Find(Key);
        const TConstArrayView<FSite> Local=Found ? TConstArrayView<FSite>(*Found) : TConstArrayView<FSite>();
        // A validated physical index has a finite nonnegative global cap.
        // No local sites means Total=0 and Foam=0, regardless of that cap.
        // Unsupported/invalid queries took the original full path above.
        if(bSkipEmpty && Local.IsEmpty())
        {
            if(Foam)*Foam=0.f;
            return 0.f;
        }
        return URaftSimWaterRuntimeAdapter::ComputeCoupledBreakingReliefMeters(P,Local,Lift,Spacing,Foam,GlobalCap);
    }
};

// The ordinary qualified index remains 8 m. A finer broad phase is opt-in;
// both variants call the SAME evaluator in original site order with its full cap.
using FRaftSimIndexedBreakingProfile=TRaftSimIndexedBreakingProfile<8>;
using FRaftSimFineIndexedBreakingProfile=TRaftSimIndexedBreakingProfile<2>;
