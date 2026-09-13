#pragma once
#include "CoreMinimal.h"
#include "Async/ParallelFor.h"

// Conforming red/green triangle refinement. Midpoints retain parent indices so
// every render attribute uses the same piecewise-linear hydraulic authority;
// no new solver query, second surface or independent stage is introduced.
struct FRaftSimSurfaceRefinement
{
    TArray<FIntPoint> MidpointParents;
    TArray<int32> Triangles;
    // Final triangles retain their original cell owner, including green
    // transition triangles. Used by the clipped carrier's exact anchor lookup.
    TArray<int32> TriangleOrigins;
    int32 SourceVertexCount=0;

    // Only combinatorial assembly is cached. Every build still evaluates its
    // current coordinates/profile and makes every selection decision anew.
    uint64 TopologyBuildCount=0,TopologyReuseCount=0;
    void InvalidateTopologyCache() { CachedRootTriangles.Reset(); CachedLevels.Reset(); CachedRootPointCount=0; }

    bool Build(const TArray<FVector2D>& Coordinates,const TArray<int32>& SourceTriangles,
        const FBox2D& Window,int32 Levels,const FBox2D* FinalLevelWindow=nullptr)
    {
        return BuildSelected(Coordinates,SourceTriangles,Levels,
            [&](const FVector2D& A,const FVector2D& B,const FVector2D& C,int32 Level,int32)
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
    // have one owner per parallel batch. Final topology order stays serial/exact.
    bool BuildAdaptive(const TArray<FVector2D>& Coordinates,const TArray<int32>& SourceTriangles,
        TFunctionRef<float(const FVector2D&)> HeightCm,int32 Levels,float ToleranceCm,
        TConstArrayView<FBox2D> NonzeroRegions={},TMap<FVector2D,float>* ProfileValues=nullptr,
        bool bParallel=false,bool bMemoizeParallel=false,
        const FBox2D* DetailWindow=nullptr,float DetailSpanCm=0)
    {
        if (!FMath::IsFinite(ToleranceCm) || ToleranceCm<=0) return false;
        TMap<FVector2D,float> LocalValues;
        TArray<TMap<FVector2D,float>> ParallelValues;
        TMap<FVector2D,float>& Values=ProfileValues ? *ProfileValues : LocalValues;
        const auto Value=[&](const FVector2D& P,int32 Context)
        {
            if (bParallel && !bMemoizeParallel) return HeightCm(P);
            auto& Memo=bParallel ? ParallelValues[Context] : Values;
            if (const float* Found=Memo.Find(P)) return *Found;
            const float V=HeightCm(P); Memo.Add(P,V); return V;
        };
        return BuildSelected(Coordinates,SourceTriangles,Levels,
            [&](const FVector2D& A,const FVector2D& B,const FVector2D& C,int32,int32 Context)
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
                    for (const auto& Region:NonzeroRegions) if (Bounds.Intersect(Region)) { Intersects=true; break; }
                    if (!Intersects) return false; // The supplied profile is exactly zero here.
                }
                const float VA=Value(A,Context), VB=Value(B,Context), VC=Value(C,Context);
                for (int32 U=0; U<=4; ++U) for (int32 V=0; V<=4-U; ++V)
                {
                    if ((U==0 && V==0) || U==4 || V==4) continue;
                    const double BWeight=U*.25, CWeight=V*.25, AWeight=1.-BWeight-CWeight;
                    if (FMath::Abs(Value(A*AWeight+B*BWeight+C*CWeight,Context)-
                        (VA*AWeight+VB*BWeight+VC*CWeight))>ToleranceCm) return true;
                }
                return false;
            },bParallel,[&](int32 Contexts)
            {
                // Resize only after the previous level has joined. Values
                // remain valid across levels within this exact profile build.
                // No table or coordinate survives into a changed profile.
                if (bMemoizeParallel) ParallelValues.SetNum(Contexts);
            });
    }

private:
    struct FTopologyLevel
    {
        TArray<uint8> Selection;
        TArray<FIntPoint> Parents;
        TArray<int32> Triangles,Origins;
    };
    TArray<int32> CachedRootTriangles;
    TArray<FTopologyLevel> CachedLevels;
    int32 CachedRootPointCount=0;

    bool BuildSelected(const TArray<FVector2D>& Coordinates,const TArray<int32>& SourceTriangles,
        int32 Levels,TFunctionRef<bool(const FVector2D&,const FVector2D&,const FVector2D&,int32,int32)> Select,
        bool bParallel=false,TFunction<void(int32)> PrepareParallel={})
    {
        MidpointParents.Reset();Triangles.Reset();TriangleOrigins.Reset();SourceVertexCount=Coordinates.Num();
        if (Coordinates.IsEmpty() || SourceTriangles.Num()%3 || Levels<0 || Levels>3)return false;
        for (int32 I:SourceTriangles)if (!Coordinates.IsValidIndex(I))return false;
        bool SamePrefix=CachedRootPointCount==Coordinates.Num() && CachedRootTriangles==SourceTriangles;
        if (!SamePrefix) CachedLevels.Reset();
        CachedRootTriangles=SourceTriangles; CachedRootPointCount=Coordinates.Num();
        CachedLevels.SetNum(Levels);
        TArray<FVector2D> Points=Coordinates;Triangles=SourceTriangles;
        for (int32 I=0; I<SourceTriangles.Num()/3; ++I) TriangleOrigins.Add(I);
        const auto Key=[](int32 A,int32 B) { return (uint64(FMath::Min(A,B))<<32)|uint32(FMath::Max(A,B)); };
        for (int32 Level=0;Level<Levels;++Level)
        {
            TArray<uint8> Selection;
            Selection.SetNumUninitialized(Triangles.Num()/3);
            if (bParallel)
            {
                constexpr int32 BatchSize=128;
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
                            Points[Triangles[T*3+2]],Level,Batch) ? 1 : 0;
                },EParallelForFlags::Unbalanced);
            }
            else for (int32 T=0;T<Selection.Num();++T)
                Selection[T]=Select(Points[Triangles[T*3]],Points[Triangles[T*3+1]],
                    Points[Triangles[T*3+2]],Level,0) ? 1 : 0;
            auto& Cached=CachedLevels[Level];
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
                if (Cached.Parents.IsEmpty()) break;
                continue;
            }
            const int32 FirstParent=MidpointParents.Num();
            ++TopologyBuildCount;
            Cached.Selection=MoveTemp(Selection);
            TMap<uint64,int32> Midpoints;
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
                break;
            }
            TArray<int32> Next;Next.Reserve(Triangles.Num()*4);
            TArray<int32> NextOrigins; NextOrigins.Reserve(Triangles.Num()*4/3);
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
            Triangles=MoveTemp(Next);
            TriangleOrigins=MoveTemp(NextOrigins);
            Cached.Triangles=Triangles; Cached.Origins=TriangleOrigins;
        }
        return true;
    }

public:
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
