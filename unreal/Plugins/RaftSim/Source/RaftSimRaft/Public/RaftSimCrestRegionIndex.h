#pragma once
#include "CoreMinimal.h"

// Immutable exact broad phase for the existing OR of FBox2D::Intersect tests.
// No profile sampling, coordinate quantization or geometry-dependent tolerance.
class FRaftSimCrestRegionIndex
{
    struct FNode { FBox2D Bounds; int32 Left=INDEX_NONE,Right=INDEX_NONE,Region=INDEX_NONE; };
    TArray<FBox2D> Regions;
    TArray<int32> Order;
    TArray<FNode> Nodes;
    bool bIndexed=true;
    int32 BuildNode(int32 Begin,int32 End)
    {
        FBox2D Bounds(ForceInit);
        for(int32 I=Begin;I<End;++I) { Bounds+=Regions[Order[I]].Min;Bounds+=Regions[Order[I]].Max; }
        const int32 Node=Nodes.Add({Bounds});
        if(End-Begin==1) { Nodes[Node].Region=Order[Begin];return Node; }
        const int32 Axis=Bounds.GetSize().X>=Bounds.GetSize().Y ? 0 : 1;
        // Overflow-safe center is used ONLY for grouping, never for rejection.
        MakeArrayView(Order.GetData()+Begin,End-Begin).Sort([&](int32 A,int32 B)
        {
            const auto& X=Regions[A];const auto& Y=Regions[B];
            const double CX=X.Min[Axis]*.5+X.Max[Axis]*.5,CY=Y.Min[Axis]*.5+Y.Max[Axis]*.5;
            return CX<CY || (CX==CY && A<B);
        });
        const int32 Middle=Begin+(End-Begin)/2;
        const int32 Left=BuildNode(Begin,Middle),Right=BuildNode(Middle,End);
        Nodes[Node].Left=Left;Nodes[Node].Right=Right;return Node;
    }
    bool Query(int32 I,const FBox2D& Bounds) const
    {
        const auto& Node=Nodes[I];
        if(!Bounds.Intersect(Node.Bounds))return false;
        if(Node.Region!=INDEX_NONE)return Bounds.Intersect(Regions[Node.Region]);
        return Query(Node.Left,Bounds) || Query(Node.Right,Bounds);
    }
    static bool Regular(const FBox2D& B)
    {
        return B.bIsValid && !B.Min.ContainsNaN() && !B.Max.ContainsNaN() &&
            B.Min.X<=B.Max.X && B.Min.Y<=B.Max.Y;
    }
public:
    explicit FRaftSimCrestRegionIndex(TConstArrayView<FBox2D> Input)
    {
        Regions.Append(Input.GetData(),Input.Num());
        for(int32 I=0;I<Regions.Num();++I) { Order.Add(I);bIndexed&=Regular(Regions[I]); }
        if(bIndexed && !Regions.IsEmpty()) { Nodes.Reserve(2*Regions.Num()-1);BuildNode(0,Regions.Num()); }
    }
    bool Intersects(const FBox2D& Bounds) const
    {
        if(!bIndexed || !Regular(Bounds))
        {
            for(const auto& Region:Regions)if(Bounds.Intersect(Region))return true;
            return false;
        }
        return !Nodes.IsEmpty() && Query(0,Bounds);
    }
};
