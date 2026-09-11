#pragma once
#include "CoreMinimal.h"

// Conforming red/green triangle refinement. Midpoints retain parent indices so
// every render attribute uses the same piecewise-linear hydraulic authority;
// no new solver query, second surface or independent stage is introduced.
struct FRaftSimSurfaceRefinement
{
    TArray<FIntPoint> MidpointParents;
    TArray<int32> Triangles;
    int32 SourceVertexCount=0;

    bool Build(const TArray<FVector2D>& Coordinates,const TArray<int32>& SourceTriangles,
        const FBox2D& Window,int32 Levels)
    {
        MidpointParents.Reset();Triangles.Reset();SourceVertexCount=Coordinates.Num();
        if (Coordinates.IsEmpty() || SourceTriangles.Num()%3 || Levels<0 || Levels>3)return false;
        for (int32 I:SourceTriangles)if (!Coordinates.IsValidIndex(I))return false;
        TArray<FVector2D> Points=Coordinates;Triangles=SourceTriangles;
        const auto Key=[](int32 A,int32 B) { return (uint64(FMath::Min(A,B))<<32)|uint32(FMath::Max(A,B)); };
        for (int32 Level=0;Level<Levels;++Level)
        {
            TMap<uint64,int32> Midpoints;
            for (int32 I=0;I<Triangles.Num();I+=3)
            {
                const int32 A=Triangles[I],B=Triangles[I+1],C=Triangles[I+2];
                FBox2D Bounds(ForceInit);Bounds+=Points[A];Bounds+=Points[B];Bounds+=Points[C];
                if (!Bounds.Intersect(Window))continue;
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
            TArray<int32> Next;Next.Reserve(Triangles.Num()*4);
            const auto Add=[&](int32 A,int32 B,int32 C) { Next.Add(A);Next.Add(B);Next.Add(C); };
            for (int32 I=0;I<Triangles.Num();I+=3)
            {
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
        }
        return true;
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
