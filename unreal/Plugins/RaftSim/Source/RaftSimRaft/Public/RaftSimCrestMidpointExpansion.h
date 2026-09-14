#pragma once
#include "CoreMinimal.h"
#include "Async/ParallelFor.h"
#include "ProceduralMeshComponent.h"

// Scheduling only: each dependency band reads fully completed parent bands.
// Keep exact parent order and the original attribute arithmetic within a node.
class FRaftSimCrestMidpointExpansion
{
    int32 CachedSourceCount=INDEX_NONE;
    TArray<FIntPoint> CachedParents,Bands;
public:
    void Reset(){CachedSourceCount=INDEX_NONE;CachedParents.Reset();Bands.Reset();}
    int32 BandCount() const{return Bands.Num();}
    static FProcMeshVertex Midpoint(const FProcMeshVertex& A,const FProcMeshVertex& B)
    {
        FProcMeshVertex V;
        V.Position=(A.Position+B.Position)*.5;
        V.Normal=(A.Normal+B.Normal).GetSafeNormal();
        V.Color=((A.Color.ReinterpretAsLinear()+B.Color.ReinterpretAsLinear())*.5f).ToFColor(false);
        V.UV0=(A.UV0+B.UV0)*.5;V.UV1=(A.UV1+B.UV1)*.5;
        V.UV2=(A.UV2+B.UV2)*.5;V.UV3=(A.UV3+B.UV3)*.5;
        V.Tangent=FProcMeshTangent((A.Tangent.TangentX+B.Tangent.TangentX).GetSafeNormal(),A.Tangent.bFlipTangentY);
        return V;
    }
    static bool EqualAttributes(const FProcMeshVertex& A,const FProcMeshVertex& B)
    {
        // Compare every attribute bit, excluding unobservable struct padding.
        const auto Same=[](const auto& X,const auto& Y){return FMemory::Memcmp(&X,&Y,sizeof(X))==0;};
        return Same(A.Position,B.Position)&&Same(A.Normal,B.Normal)&&Same(A.Color,B.Color)&&
            Same(A.UV0,B.UV0)&&Same(A.UV1,B.UV1)&&Same(A.UV2,B.UV2)&&Same(A.UV3,B.UV3)&&
            Same(A.Tangent.TangentX,B.Tangent.TangentX)&&Same(A.Tangent.bFlipTangentY,B.Tangent.bFlipTangentY);
    }
    bool Expand(TArray<FProcMeshVertex>& Vertices,int32 SourceCount,const TArray<FIntPoint>& Parents)
    {
        if(SourceCount<0 || int64(SourceCount)+Parents.Num()!=Vertices.Num())return false;
        if(CachedSourceCount!=SourceCount || CachedParents!=Parents)
        {
            TArray<FIntPoint> NewBands;
            int32 Begin=0;
            while(Begin<Parents.Num())
            {
                const int32 Available=SourceCount+Begin;
                int32 End=Begin;
                while(End<Parents.Num())
                {
                    const auto P=Parents[End];
                    if(P.X<0 || P.Y<0)return false;
                    if(P.X>=Available || P.Y>=Available)break;
                    ++End;
                }
                if(End==Begin)return false; // Cyclic/forward parent, never guess.
                NewBands.Emplace(Begin,End);Begin=End;
            }
            CachedSourceCount=SourceCount;CachedParents=Parents;Bands=MoveTemp(NewBands);
        }
        for(const auto Band:Bands)
        {
            ParallelFor(TEXT("RaftSimCrestMidpoints"),Band.Y-Band.X,128,[&](int32 Offset)
            {
                const int32 I=Band.X+Offset;const auto P=Parents[I];
                Vertices[SourceCount+I]=Midpoint(Vertices[P.X],Vertices[P.Y]);
            }); // Joins before any child band can read these vertices.
        }
        return true;
    }
};
