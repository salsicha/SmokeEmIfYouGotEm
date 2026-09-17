#pragma once
#include "CoreMinimal.h"
#include "Async/ParallelFor.h"
#include "RaftSimCoordinateMap.h"
#include "RaftSimFlatCoordinateMap.h"
#include "RaftSimCrestCornerSamples.h"
#include "RaftSimCrestRegionIndex.h"
#include "RaftSimEdgeMap.h"
#include "RaftSimIndexedEdgeMap.h"
#include "RaftSimBoundCoordinateMemo.h"

// Conforming red/green triangle refinement. Midpoints retain parent indices so
// every render attribute uses the same piecewise-linear hydraulic authority;
// no new solver query, second surface or independent stage is introduced.
struct FRaftSimSurfaceRefinement
{
    struct FProfileMemoSample { float Value=0; uint64 Epoch=0; };
    TArray<FIntPoint> MidpointParents;
    TArray<int32> Triangles;
    // Final triangles retain their original cell owner, including green
    // transition triangles. Used by the clipped carrier's exact anchor lookup.
    TArray<int32> TriangleOrigins;
    int32 SourceVertexCount=0;

    // Only combinatorial assembly is cached. Every build still evaluates its
    // current coordinates/profile and makes every selection decision anew.
    uint64 TopologyBuildCount=0,TopologyReuseCount=0;
    // Opt-in diagnostic only; these do not control selection or topology.
    bool bMeasureStages=false;
    // Scheduling only. Each batch owns its memo, and every build advances the
    // profile epoch even when the grouping changes. Selection remains exact.
    int32 ParallelBatchSize=128;
    bool bIndexedRegions=false; // Candidate until actual paired timing qualifies it.
    bool bFlatCoordinateMemo=false; // Candidate: exact keys, unchanged profile epochs.
    bool bStrongEdgeHash=false; // Candidate until exact actual-input timing qualifies it.
    bool bIndexedEdges=false; // Shoreline enables the qualified indexed lookup.
    bool bRetainTopologyStorage=false; // Reuse capacity, never stale selection/profile values.
    bool bLevelLocalMemos=false; // Candidate: retain coordinate slots separately per level.
    bool bInlineSelection=false; // Candidate: typed predicate, identical evaluations.
    bool bBoundCoordinateMemo=false; // Candidate: exact per-triangle lookup bindings.
    // Optional conservative width of a range containing the current profile
    // on a box. Only skips selection when every error test is provably below
    // the SAME tolerance. It never changes a sampled or published height.
    TFunction<float(const FBox2D&)> HeightRangeWidthCm;
    double InputSeconds=0,SelectionSeconds=0,AssemblySeconds=0;
    uint64 ParallelContextsCreated=0,ParallelContextsDestroyed=0;
    uint64 SharedCornerSamples=0,SharedCornerReads=0;
    double GetRetainedMemoAllocatedBytes() const
    {
        uint64 Bytes=RetainedParallelValues.GetAllocatedSize()+RetainedFastParallelValues.GetAllocatedSize();
        for(const auto& Context:RetainedParallelValues)Bytes+=Context.GetAllocatedSize();
        for(const auto& Context:RetainedFastParallelValues)Bytes+=Context.GetAllocatedSize();
        for(const auto& Level:RetainedLevelFastValues)
        {
            Bytes+=Level.GetAllocatedSize();
            for(const auto& Context:Level)Bytes+=Context.GetAllocatedSize();
        }
        Bytes+=RetainedFlatParallelValues.GetAllocatedSize();
        for(const auto& Context:RetainedFlatParallelValues)Bytes+=Context.GetAllocatedSize();
        Bytes+=RetainedBoundValues.GetAllocatedSize();
        for(const auto& Context:RetainedBoundValues)Bytes+=Context.GetAllocatedSize();
        // Diagnostic numeric value for CSV/JSON. Exact for any feasible
        // process allocation (<2^53 bytes); never controls cache ownership.
        return double(Bytes);
    }
    void InvalidateTopologyCache() { CachedRootTriangles.Reset(); CachedLevels.Reset(); CachedRootPointCount=0; }

    bool Build(const TArray<FVector2D>& Coordinates,const TArray<int32>& SourceTriangles,
        const FBox2D& Window,int32 Levels,const FBox2D* FinalLevelWindow=nullptr)
    {
        return BuildSelected(Coordinates,SourceTriangles,Levels,
            [&](const FVector2D& A,const FVector2D& B,const FVector2D& C,int32 Level,int32,int32)
            {
                FBox2D Bounds(ForceInit); Bounds+=A; Bounds+=B; Bounds+=C;
                return Bounds.Intersect(FinalLevelWindow && Level==Levels-1 ? *FinalLevelWindow : Window);
            });
    }

    // Refine the actual physical profile wherever interpolation loses shape,
    // not an absolute rapid-origin box. Values are memoized only within this
    // exact build, or in an optional caller-owned cache whose values must be
    // discarded whenever the profile changes. Geometry changes alone may reuse
    // exact world-coordinate values; interpolation/selection is always rerun.
    // Parallel evaluation requires a pure, thread-safe HeightCm. It deliberately
    // bypasses the caller's mutable memo table; optional batch-local tables
    // have one owner per parallel batch. Retained tables keep coordinate slots
    // only: a new epoch forces current HeightCm evaluation on every build.
    // Final topology order stays serial/exact.
    bool BuildAdaptive(const TArray<FVector2D>& Coordinates,const TArray<int32>& SourceTriangles,
        TFunctionRef<float(const FVector2D&)> HeightCm,int32 Levels,float ToleranceCm,
        TConstArrayView<FBox2D> NonzeroRegions={},TMap<FVector2D,float>* ProfileValues=nullptr,
        bool bParallel=false,bool bMemoizeParallel=false,
        const FBox2D* DetailWindow=nullptr,float DetailSpanCm=0,bool bRetainParallelMemo=false,
        bool bFastCoordinateHash=true,bool bKeepParallelContexts=true,bool bShareCornerSamples=false)
    {
        if (!FMath::IsFinite(ToleranceCm) || ToleranceCm<=0) return false;
        TUniquePtr<FRaftSimCrestRegionIndex> RegionIndex;
        if(bIndexedRegions)RegionIndex=MakeUnique<FRaftSimCrestRegionIndex>(NonzeroRegions);
        ParallelContextsCreated=ParallelContextsDestroyed=0;
        SharedCornerSamples=SharedCornerReads=0;
        FRaftSimCrestCornerSamples Corners; // Never survives this profile build.
        const bool ShareCorners=bParallel && bShareCornerSamples;
        TMap<FVector2D,float> LocalValues;
        TArray<TMap<FVector2D,FProfileMemoSample>> LocalParallelValues;
        auto& ParallelValues=bRetainParallelMemo ? RetainedParallelValues : LocalParallelValues;
        TArray<TRaftSimCoordinateMap<FProfileMemoSample>> LocalFastParallelValues;
        auto& FastParallelValues=bRetainParallelMemo ? RetainedFastParallelValues : LocalFastParallelValues;
        TArray<TRaftSimCoordinateMap<FProfileMemoSample>> LocalLevelFastValues[3];
        TArray<FRaftSimBoundCoordinateMemo> LocalBoundValues;
        auto& BoundValues=bRetainParallelMemo ? RetainedBoundValues : LocalBoundValues;
        auto* ActiveFastParallelValues=&FastParallelValues;
        int32 MemoLevel=-1;
        TArray<TRaftSimFlatCoordinateMap<FProfileMemoSample>> LocalFlatParallelValues;
        auto& FlatParallelValues=bRetainParallelMemo ? RetainedFlatParallelValues : LocalFlatParallelValues;
        // Retain lookup slots, NEVER profile values across calls. XY can move,
        // profiles can change without a key, and callers can replace HeightCm.
        // Each batch owns its map; levels join before resizing or reusing it.
        if (++ProfileMemoEpoch==0)
        {
            RetainedParallelValues.Reset(); RetainedFastParallelValues.Reset(); RetainedFlatParallelValues.Reset();
            for(auto& Level:RetainedLevelFastValues)Level.Reset();
            RetainedBoundValues.Reset();
            ++ProfileMemoEpoch;
        }
        TMap<FVector2D,float>& Values=ProfileValues ? *ProfileValues : LocalValues;
        const auto MemoValue=[&](auto& Memo,const FVector2D& P)
        {
            if (auto* Found=Memo.Find(P))
            {
                if (Found->Epoch!=ProfileMemoEpoch)
                { Found->Value=HeightCm(P); Found->Epoch=ProfileMemoEpoch; }
                return Found->Value;
            }
            // Bound moving-window coordinate history. Clearing only repeats
            // exact evaluations; it cannot change selection or profile age.
            if (Memo.Num()>=4096) Memo.Reset();
            const float V=HeightCm(P); Memo.Add(P,{V,ProfileMemoEpoch}); return V;
        };
        const auto Value=[&](const FVector2D& P,int32 Context,int32 Binding)
        {
            if (bParallel && !bMemoizeParallel) return HeightCm(P);
            if (bParallel)
            {
                if(bBoundCoordinateMemo)
                    return BoundValues[Context].Value(P,Binding,ProfileMemoEpoch,HeightCm);
                if(bFlatCoordinateMemo)
                {
                    auto& Sample=FlatParallelValues[Context].FindOrAdd(P,4096);
                    if(Sample.Epoch!=ProfileMemoEpoch)
                    {Sample.Value=HeightCm(P);Sample.Epoch=ProfileMemoEpoch;}
                    return Sample.Value;
                }
                return bFastCoordinateHash ? MemoValue((*ActiveFastParallelValues)[Context],P) : MemoValue(ParallelValues[Context],P);
            }
            if (const float* Found=Values.Find(P)) return *Found;
            const float V=HeightCm(P); Values.Add(P,V); return V;
        };
        const auto Select=[&](const FVector2D& A,const FVector2D& B,const FVector2D& C,int32,int32 Context,int32 Triangle)
            {
                // A dynamic displacement field needs geometric samples even
                // where the immutable macro crest is flat. This selection
                // changes topology only, never invents profile heights.
                FBox2D Bounds(ForceInit); Bounds+=A; Bounds+=B; Bounds+=C;
                if (DetailWindow && DetailSpanCm>0 && Bounds.Intersect(*DetailWindow) &&
                    FMath::Max(Bounds.GetSize().X,Bounds.GetSize().Y)>DetailSpanCm) return true;
                if (!NonzeroRegions.IsEmpty())
                {
                    bool Intersects=false;
                    if(RegionIndex)Intersects=RegionIndex->Intersects(Bounds);
                    else for (const auto& Region:NonzeroRegions) if (Bounds.Intersect(Region)) { Intersects=true; break; }
                    if (!Intersects) return false; // The supplied profile is exactly zero here.
                }
                if(HeightRangeWidthCm)
                {
                    const float Width=HeightRangeWidthCm(Bounds);
                    // All quarter-triangle weights are nonnegative and sum
                    // to one. Profile values and their interpolation stay in
                    // the same range, hence their difference is <= its width.
                    if(FMath::IsFinite(Width) && Width>=0.f && Width<=ToleranceCm)return false;
                }
                // Each level keeps distinct triangle bindings, but exact
                // coordinate samples share ONE bounded table per worker.
                // Levels join before reuse, and all heights expire together.
                const int32 BindingBase=bBoundCoordinateMemo ? (MemoLevel*ParallelBatchSize+Triangle%ParallelBatchSize)*15 : 0;
                const float VA=ShareCorners ? Corners.Get(Triangle,0) : Value(A,Context,BindingBase);
                const float VB=ShareCorners ? Corners.Get(Triangle,1) : Value(B,Context,BindingBase+1);
                const float VC=ShareCorners ? Corners.Get(Triangle,2) : Value(C,Context,BindingBase+2);
                int32 SampleBinding=BindingBase+3;
                for (int32 U=0; U<=4; ++U) for (int32 V=0; V<=4-U; ++V)
                {
                    if ((U==0 && V==0) || U==4 || V==4) continue;
                    const double BWeight=U*.25, CWeight=V*.25, AWeight=1.-BWeight-CWeight;
                    if (FMath::Abs(Value(A*AWeight+B*BWeight+C*CWeight,Context,SampleBinding++)-
                        (VA*AWeight+VB*BWeight+VC*CWeight))>ToleranceCm) return true;
                }
                return false;
            };
        const TFunction<void(int32)> PrepareParallel=[&](int32 Contexts)
            {
                // Resize only after the previous level has joined. Values
                // remain valid across levels within this exact profile build.
                // No sampled height survives into another build's epoch.
                if (bMemoizeParallel)
                {
                    const auto Prepare=[&](auto& Tables)
                    {
                        const int32 Before=Tables.Num();
                        // A coarse level needs fewer workers than the previous
                        // frame's fine level. Preserve those inactive maps for
                        // later levels instead of destroying and recreating
                        // them every frame. Heights STILL use this build's epoch.
                        // Storage is bounded by peak context count and the
                        // existing4096-entry cap per map; no shared worker map.
                        const int32 Count=bRetainParallelMemo && bKeepParallelContexts ? FMath::Max(Before,Contexts) : Contexts;
                        Tables.SetNum(Count);
                        ParallelContextsCreated+=FMath::Max(Count-Before,0);
                        ParallelContextsDestroyed+=FMath::Max(Before-Count,0);
                    };
                    if (bBoundCoordinateMemo)
                    {
                        Prepare(BoundValues);
                        for(int32 I=0;I<Contexts;++I)BoundValues[I].Prepare(Levels*ParallelBatchSize*15);
                    }
                    else if (bFlatCoordinateMemo) Prepare(FlatParallelValues);
                    else if (bFastCoordinateHash) Prepare(*ActiveFastParallelValues);
                    else Prepare(ParallelValues);
                }
            };
        const TFunction<void(const TArray<FVector2D>&,const TArray<int32>&)> PrepareLevel=
            [&](const TArray<FVector2D>& Points,const TArray<int32>& CurrentTriangles)
            {
                ++MemoLevel;
                // A batch number refers to a different spatial strip at each
                // refinement level. Keep its coordinate slots level-local;
                // all sampled values still expire at this build's new epoch.
                if(bLevelLocalMemos)
                    ActiveFastParallelValues=bRetainParallelMemo ? &RetainedLevelFastValues[MemoLevel] : &LocalLevelFastValues[MemoLevel];
                if(!ShareCorners)return;
                Corners.Prepare(Points,CurrentTriangles,HeightCm,NonzeroRegions,DetailWindow,DetailSpanCm);
                SharedCornerSamples=Corners.SampleCount;SharedCornerReads=Corners.ReadCount;
            };
        if(bInlineSelection)
            return BuildSelected(Coordinates,SourceTriangles,Levels,Select,bParallel,PrepareParallel,PrepareLevel);
        // Retain the original erased-call path for independent same-build A/B.
        using FPredicate=TFunctionRef<bool(const FVector2D&,const FVector2D&,const FVector2D&,int32,int32,int32)>;
        return BuildSelected<FPredicate>(Coordinates,SourceTriangles,Levels,Select,bParallel,PrepareParallel,PrepareLevel);
    }

private:
    TArray<TMap<FVector2D,FProfileMemoSample>> RetainedParallelValues;
    TArray<TRaftSimCoordinateMap<FProfileMemoSample>> RetainedFastParallelValues;
    TArray<TRaftSimCoordinateMap<FProfileMemoSample>> RetainedLevelFastValues[3];
    TArray<TRaftSimFlatCoordinateMap<FProfileMemoSample>> RetainedFlatParallelValues;
    TArray<FRaftSimBoundCoordinateMemo> RetainedBoundValues;
    uint64 ProfileMemoEpoch=0;
    TArray<FVector2D> RetainedPoints;
    TArray<int32> RetainedNextTriangles,RetainedNextOrigins;
    struct FTopologyLevel
    {
        TArray<uint8> Selection;
        TArray<uint8> WorkingSelection;
        TArray<FIntPoint> Parents;
        TArray<int32> Triangles,Origins;
    };
    TArray<int32> CachedRootTriangles;
    TArray<FTopologyLevel> CachedLevels;
    int32 CachedRootPointCount=0;

    template<typename TSelect>
    bool BuildSelected(const TArray<FVector2D>& Coordinates,const TArray<int32>& SourceTriangles,
        int32 Levels,TSelect Select,
        bool bParallel=false,TFunction<void(int32)> PrepareParallel={},
        TFunction<void(const TArray<FVector2D>&,const TArray<int32>&)> PrepareLevel={})
    {
        InputSeconds=SelectionSeconds=AssemblySeconds=0;
        const double InputStarted=bMeasureStages ? FPlatformTime::Seconds() : 0.;
        MidpointParents.Reset();Triangles.Reset();TriangleOrigins.Reset();SourceVertexCount=Coordinates.Num();
        if (Coordinates.IsEmpty() || SourceTriangles.Num()%3 || Levels<0 || Levels>3 ||
            ParallelBatchSize<1 || ParallelBatchSize>4096)return false;
        for (int32 I:SourceTriangles)if (!Coordinates.IsValidIndex(I))return false;
        bool SamePrefix=CachedRootPointCount==Coordinates.Num() && CachedRootTriangles==SourceTriangles;
        // A changed root still makes SamePrefix false for EVERY visited level.
        // Keeping allocation capacity must never authorize cached topology.
        if (!SamePrefix && !bRetainTopologyStorage) CachedLevels.Reset();
        CachedRootTriangles=SourceTriangles; CachedRootPointCount=Coordinates.Num();
        CachedLevels.SetNum(Levels);
        TArray<FVector2D> LocalPoints;
        auto& Points=bRetainTopologyStorage ? RetainedPoints : LocalPoints;
        Points=Coordinates;Triangles=SourceTriangles;
        for (int32 I=0; I<SourceTriangles.Num()/3; ++I) TriangleOrigins.Add(I);
        const auto Key=[](int32 A,int32 B) { return (uint64(FMath::Min(A,B))<<32)|uint32(FMath::Max(A,B)); };
        if(bMeasureStages)InputSeconds=FPlatformTime::Seconds()-InputStarted;
        for (int32 Level=0;Level<Levels;++Level)
        {
            const double SelectionStarted=bMeasureStages ? FPlatformTime::Seconds() : 0.;
            if(PrepareLevel)PrepareLevel(Points,Triangles);
            auto& Cached=CachedLevels[Level];
            TArray<uint8> LocalSelection;
            auto& Selection=bRetainTopologyStorage ? Cached.WorkingSelection : LocalSelection;
            Selection.SetNumUninitialized(Triangles.Num()/3);
            if (bParallel)
            {
                const int32 BatchSize=ParallelBatchSize;
                const int32 Batches=FMath::DivideAndRoundUp(Selection.Num(),BatchSize);
                if (PrepareParallel) PrepareParallel(Batches);
                // Selection only reads this level's immutable points/indices.
                // Wait for all workers before any midpoint insertion can move
                // their storage, then assemble in the original triangle order.
                ParallelFor(TEXT("RaftSimCrestSelection"),Batches,1,[&](int32 Batch)
                {
                    const int32 End=FMath::Min((Batch+1)*BatchSize,Selection.Num());
                    for (int32 T=Batch*BatchSize; T<End; ++T)
                        Selection[T]=Select(Points[Triangles[T*3]],Points[Triangles[T*3+1]],
                            Points[Triangles[T*3+2]],Level,Batch,T) ? 1 : 0;
                },EParallelForFlags::Unbalanced);
            }
            else for (int32 T=0;T<Selection.Num();++T)
                Selection[T]=Select(Points[Triangles[T*3]],Points[Triangles[T*3+1]],
                    Points[Triangles[T*3+2]],Level,0,T) ? 1 : 0;
            const double AssemblyStarted=bMeasureStages ? FPlatformTime::Seconds() : 0.;
            if(bMeasureStages)SelectionSeconds+=AssemblyStarted-SelectionStarted;
            SamePrefix=SamePrefix && Cached.Selection==Selection;
            if (SamePrefix)
            {
                // Parent indices depend only on the root topology and exact
                // selection masks, not XYZ or heights. Re-evaluate midpoints
                // from THIS build's coordinates, in the original order.
                for (const auto P:Cached.Parents) Points.Add((Points[P.X]+Points[P.Y])*.5);
                MidpointParents.Append(Cached.Parents);
                Triangles=Cached.Triangles; TriangleOrigins=Cached.Origins;
                ++TopologyReuseCount;
                if(bMeasureStages)AssemblySeconds+=FPlatformTime::Seconds()-AssemblyStarted;
                if (Cached.Parents.IsEmpty()) break;
                continue;
            }
            const int32 FirstParent=MidpointParents.Num();
            ++TopologyBuildCount;
            if(bRetainTopologyStorage)Swap(Cached.Selection,Selection);
            else Cached.Selection=MoveTemp(Selection);
            const auto Assemble=[&](auto& Midpoints)
            {
                for (int32 I=0;I<Triangles.Num();I+=3)
                {
                    const int32 A=Triangles[I],B=Triangles[I+1],C=Triangles[I+2];
                    if (!Cached.Selection[I/3])continue;
                    const int32 Corners[]={A,B,C};
                    for (int32 E=0;E<3;++E)
                    {
                        const int32 L=Corners[E],R=Corners[(E+1)%3];const uint64 K=Key(L,R);
                        if (!Midpoints.Contains(K))
                        {
                            const int32 NewIndex=Points.Num();
                            Points.Add((Points[L]+Points[R])*0.5);
                            MidpointParents.Add(FIntPoint(L,R));Midpoints.Add(K,NewIndex);
                        }
                    }
                }
                Cached.Parents.Reset();
                for (int32 I=FirstParent;I<MidpointParents.Num();++I) Cached.Parents.Add(MidpointParents[I]);
                if (Midpoints.IsEmpty())
                {
                    Cached.Triangles=Triangles; Cached.Origins=TriangleOrigins;
                    return false;
                }
                TArray<int32> LocalNext,LocalNextOrigins;
                auto& Next=bRetainTopologyStorage ? RetainedNextTriangles : LocalNext;
                auto& NextOrigins=bRetainTopologyStorage ? RetainedNextOrigins : LocalNextOrigins;
                Next.Reset();Next.Reserve(Triangles.Num()*4);
                NextOrigins.Reset();NextOrigins.Reserve(Triangles.Num()*4/3);
                int32 Origin=0;
                const auto Add=[&](int32 A,int32 B,int32 C)
                { Next.Add(A);Next.Add(B);Next.Add(C);NextOrigins.Add(Origin); };
                for (int32 I=0;I<Triangles.Num();I+=3)
                {
                    Origin=TriangleOrigins[I/3];
                    int32 V[]={Triangles[I],Triangles[I+1],Triangles[I+2]};int32 M[3],Count=0;
                    for (int32 E=0;E<3;++E)
                    {
                        const int32* Found=Midpoints.Find(Key(V[E],V[(E+1)%3]));M[E]=Found ? *Found : INDEX_NONE;
                        Count+=Found ? 1 : 0;
                    }
                    if (Count==0) { Add(V[0],V[1],V[2]);continue; }
                    if (Count==3)
                    {
                        Add(V[0],M[0],M[2]);Add(M[0],V[1],M[1]);Add(M[2],M[1],V[2]);Add(M[0],M[1],M[2]);continue;
                    }
                    // Rotate indices cyclically; preserve the parent's winding.
                    int32 Start=0;
                    if (Count==1)while (M[Start]==INDEX_NONE)++Start;
                    else while (M[Start]==INDEX_NONE || M[(Start+1)%3]==INDEX_NONE)++Start;
                    const int32 A=V[Start],B=V[(Start+1)%3],C=V[(Start+2)%3],AB=M[Start];
                    if (Count==1) { Add(A,AB,C);Add(AB,B,C); }
                    else { const int32 BC=M[(Start+1)%3];Add(B,BC,AB);Add(A,AB,C);Add(AB,BC,C); }
                }
                if(bRetainTopologyStorage){Swap(Triangles,Next);Swap(TriangleOrigins,NextOrigins);}
                else {Triangles=MoveTemp(Next);TriangleOrigins=MoveTemp(NextOrigins);}
                Cached.Triangles=Triangles; Cached.Origins=TriangleOrigins;
                return true;
            };
            bool HasMidpoints=false;
            if(bIndexedEdges)
            { FRaftSimIndexedEdgeMap Midpoints(Points.Num()); HasMidpoints=Assemble(Midpoints); }
            else if(bStrongEdgeHash)
            { TRaftSimEdgeMap<int32> Midpoints; HasMidpoints=Assemble(Midpoints); }
            else
            { TMap<uint64,int32> Midpoints; HasMidpoints=Assemble(Midpoints); }
            if(bMeasureStages)AssemblySeconds+=FPlatformTime::Seconds()-AssemblyStarted;
            if(!HasMidpoints)break;
        }
        return true;
    }

public:
    uint64 GetTopologyAllocatedBytes() const
    {
        uint64 Bytes=CachedRootTriangles.GetAllocatedSize()+CachedLevels.GetAllocatedSize()+
            RetainedPoints.GetAllocatedSize()+RetainedNextTriangles.GetAllocatedSize()+RetainedNextOrigins.GetAllocatedSize();
        for(const auto& L:CachedLevels)Bytes+=L.Selection.GetAllocatedSize()+L.WorkingSelection.GetAllocatedSize()+
            L.Parents.GetAllocatedSize()+L.Triangles.GetAllocatedSize()+L.Origins.GetAllocatedSize();
        return Bytes;
    }
    template<class T> void Expand(const TArray<T>& Source,TArray<T>& Output) const
    {
        check(Source.Num()==SourceVertexCount);
        Output.SetNumUninitialized(Source.Num()+MidpointParents.Num());
        for (int32 I=0;I<Source.Num();++I)Output[I]=Source[I];
        for (int32 I=0;I<MidpointParents.Num();++I)
        {
            const auto P=MidpointParents[I];
            Output[Source.Num()+I]=(Output[P.X]+Output[P.Y])*0.5f;
        }
    }
};
