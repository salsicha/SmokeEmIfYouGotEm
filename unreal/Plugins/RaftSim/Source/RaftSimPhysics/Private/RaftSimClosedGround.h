#pragma once
#include "CoreMinimal.h"

// Topological classification only: original positions, faces and collision
// identities are never welded or changed. Exact-position seam aliases are used
// solely to find closed edge-connected source components.
class FRaftSimClosedGround
{
public:
    enum class ELocation : uint8 { Outside, Inside, Unresolved };
    void Build(TConstArrayView<FVector> Vertices,TConstArrayView<FIntVector> Faces);
    ELocation Classify(const FVector& Point,TConstArrayView<FVector> Vertices,
        TConstArrayView<FIntVector> Faces,bool bAccelerated=true) const;
    void AddEnclosedRepresentatives(const FBox& Bounds,TConstArrayView<FVector> Vertices,
        TArray<FVector>& Points) const;
    int32 ComponentCount() const { return ClosedComponents; }
private:
    struct FNode {FBox Bounds=FBox(ForceInit);int32 Left=INDEX_NONE,Right=INDEX_NONE,Begin=0,Count=0;};
    struct FComponent
    {
        TArray<int32> Faces;
        TArray<FNode> Nodes;
        FBox Bounds=FBox(ForceInit);
        int32 RepresentativeVertex=0;
        bool bClosed=false,bOriented=true;
    };
    int32 BuildNode(FComponent& Component,int32 Begin,int32 Count,
        TConstArrayView<FVector> Vertices,TConstArrayView<FIntVector> Faces);
    TOptional<int32> RayWinding(const FComponent& Component,const FVector& Point,
        TConstArrayView<FVector> Vertices,TConstArrayView<FIntVector> Faces) const;
    TArray<FComponent> Components;
    int32 ClosedComponents=0;
};
