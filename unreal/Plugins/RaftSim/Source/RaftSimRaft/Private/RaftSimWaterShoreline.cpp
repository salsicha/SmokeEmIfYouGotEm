#include "RaftSimWaterShoreline.h"
#include "RaftSimWaterVertexCopy.h"

namespace
{
bool ValidInput(int32 Nx, int32 Ny, TConstArrayView<FProcMeshVertex> Source,
    TConstArrayView<uint8> Wet, TConstArrayView<uint8> Available,
    TConstArrayView<float> DepthM, TConstArrayView<float> BedM)
{
    const int64 Count=int64(Nx)*Ny;
    if (Nx<2 || Ny<2 || Count>MAX_int32/12 || Source.Num()!=Count || Wet.Num()!=Count ||
        Available.Num()!=Count || DepthM.Num()!=Count || BedM.Num()!=Count) return false;
    for (int32 I=0; I<Count; ++I)
        if (Source[I].Position.ContainsNaN() || Source[I].Normal.ContainsNaN() ||
            !FMath::IsFinite(DepthM[I]) || DepthM[I]<0 || !FMath::IsFinite(BedM[I]) ||
            (Wet[I] && DepthM[I]<=0)) return false;
    return true;
}
double Crossing(int32 W, int32 D, TConstArrayView<float> DepthM, TConstArrayView<float> BedM)
{
    const double DryRise=double(BedM[D])-(double(BedM[W])+DepthM[W]);
    return DryRise>0 ? DepthM[W]/(DepthM[W]+DryRise) : .5;
}
void WriteEdge(const RaftSimWaterShoreline::FEdge& Edge, TArray<FProcMeshVertex>& Vertices)
{
    const auto& W=Vertices[Edge.WetVertex];
    const auto& D=Vertices[Edge.DryVertex];
    auto& V=Vertices[Edge.Node];
    V=W;
    V.Position=FMath::Lerp(W.Position,D.Position,Edge.Crossing);
    V.Position.Z=W.Position.Z;
    V.UV0=FMath::Lerp(W.UV0,D.UV0,Edge.Crossing);
}
int8 TriangleOrientation(uint32 A, uint32 B, uint32 C, const TArray<FProcMeshVertex>& Vertices)
{
    const FVector Cross=FVector::CrossProduct(Vertices[B].Position-Vertices[A].Position,
        Vertices[C].Position-Vertices[A].Position);
    return FMath::Abs(Cross.Z)<=1.e-8 ? 0 : Cross.Z<0 ? -1 : 1;
}
}

static bool BuildClipped(int32 Nx, int32 Ny, TArray<FProcMeshVertex>&& Source,
    TConstArrayView<uint8> Wet, TConstArrayView<uint8> Available,
    TConstArrayView<float> DepthM, TConstArrayView<float> BedM,
    TArray<FProcMeshVertex>& OutVertices, TArray<uint32>& OutIndices, TArray<int32>* OutCellOffsets,
    TArray<RaftSimWaterShoreline::FEdge>* OutEdges, bool bPreserveUnusedNodes, bool bCompactEdges,
    TArray<RaftSimWaterShoreline::FBankTriangle>* OutBankTriangles = nullptr)
{
    // Both public entry points validate before any output/cache mutation.
    // Do not scan the entire source grid again on a cache miss.
    const int32 Count=Nx*Ny;
    const int32 HStart=Count, VStart=HStart+(Nx-1)*Ny;
    const int32 MaximumCount=VStart+Nx*(Ny-1);
    OutVertices.SetNum(bCompactEdges ? Count : MaximumCount);
    RaftSimWaterVertexCopy::Prefix(Source,OutVertices);
    // Unused nodes are inside the grid, not uninitialized or sunk miles below
    // it. They never enter the draw list or ray-tracing primitive list.
    // The owning cache already initialized its fixed reserve. On later
    // topology rebuilds every referenced edge is rewritten below; inactive
    // reserve vertices cannot affect the draw list, anchors or source bounds.
    // Do not rewrite two entire unused grids whenever a bank crossing moves.
    if (!bPreserveUnusedNodes)
        for (int32 I=Count; I<OutVertices.Num(); ++I) OutVertices[I]=OutVertices[0];
    OutIndices.Reset((Nx-1)*(Ny-1)*12);
    if (OutCellOffsets) OutCellOffsets->SetNumUninitialized((Nx-1)*(Ny-1)+1);
    if (OutEdges) OutEdges->Reset();
    if (OutBankTriangles) OutBankTriangles->Reset();
    TArray<uint8> Built;
    Built.Init(0, MaximumCount-Count);
    // Keep the original grid indices, but assign only encountered bank edges
    // a dense suffix for CPU crest work. Shared-edge identity is still its
    // canonical lattice slot, not a rounded coordinate or triangle-local node.
    TArray<int32> CompactNodes;
    if (bCompactEdges) CompactNodes.SetNumUninitialized(MaximumCount-Count);
    const auto Edge = [&](int32 A, int32 B) -> uint32
    {
        const int32 Min=FMath::Min(A,B), Max=FMath::Max(A,B);
        int32 Node;
        if (Max-Min==1) Node=HStart+(Min/Nx)*(Nx-1)+Min%Nx;
        else { check(Max-Min==Nx); Node=VStart+Min; }
        const int32 Slot=Node-Count;
        if (!Built[Slot])
        {
            Built[Slot]=1;
            if (bCompactEdges)
            {
                Node=OutVertices.AddDefaulted();
                CompactNodes[Slot]=Node;
            }
            const int32 W=Wet[A]?A:B, D=Wet[A]?B:A;
            // A rising dry bed intersects the wet cell's free surface exactly.
            // At a finite-volume advancing front with bed below that surface,
            // use the shared half-cell face: a dry cell supplies no water level.
            // This front convention is explicit, not inferred bathymetry.
            const RaftSimWaterShoreline::FEdge Result{W,D,Node,Crossing(W,D,DepthM,BedM)};
            WriteEdge(Result,OutVertices);
            if (OutEdges) OutEdges->Add(Result);
            // Flow, wake and optical channels come from actual water, never
            // from an absent dry sample or the dry vertex's reference height.
        }
        else if (bCompactEdges) Node=CompactNodes[Slot];
        return Node;
    };
    const auto Emit = [&](const uint32* Polygon, int32 N)
    {
        for (int32 I=1; I+1<N; ++I)
        {
            const int8 Orientation=TriangleOrientation(Polygon[0],Polygon[I],Polygon[I+1],OutVertices);
            // Retain omitted candidates too: a later bank move can turn a
            // degenerate triangle into a real triangle without changing masks.
            if (OutBankTriangles && (Polygon[0]>=uint32(Count) || Polygon[I]>=uint32(Count) || Polygon[I+1]>=uint32(Count)))
                OutBankTriangles->Add({Polygon[0],Polygon[I],Polygon[I+1],Orientation});
            if (!Orientation) continue;
            // Unreal's front face is clockwise when viewed from above. The
            // geographic Y reflection can reverse the source grid, so choose
            // winding from actual positions, not row/column order.
            OutIndices.Add(Polygon[0]);
            OutIndices.Add(Polygon[Orientation<0 ? I : I+1]);
            OutIndices.Add(Polygon[Orientation<0 ? I+1 : I]);
        }
    };
    for (int32 Y=0; Y<Ny-1; ++Y) for (int32 X=0; X<Nx-1; ++X)
    {
        const int32 A=Y*Nx+X, B=A+1, C=A+Nx, D=C+1;
        if (OutCellOffsets) (*OutCellOffsets)[Y*(Nx-1)+X]=OutIndices.Num();
        if (!Available[A] || !Available[B] || !Available[C] || !Available[D]) continue;
        const int32 V[4]={A,C,D,B};
        if (bool(Wet[A])==bool(Wet[D]) && bool(Wet[B])==bool(Wet[C]) && bool(Wet[A])!=bool(Wet[B]))
        {
            // Ambiguous diagonal wet corners stay disconnected. No measured
            // water at either dry corner supports inventing a joining channel.
            for (int32 I=0; I<4; ++I) if (Wet[V[I]])
            {
                const uint32 P[3]={uint32(V[I]),Edge(V[I],V[(I+1)%4]),Edge(V[(I+3)%4],V[I])};
                Emit(P,3);
            }
        }
        else
        {
            uint32 Polygon[8]; int32 N=0;
            for (int32 I=0; I<4; ++I)
            {
                const int32 P=V[I], Q=V[(I+1)%4];
                if (Wet[P]) Polygon[N++]=P;
                if (bool(Wet[P])!=bool(Wet[Q])) Polygon[N++]=Edge(P,Q);
            }
            Emit(Polygon,N);
        }
    }
    if (OutCellOffsets) OutCellOffsets->Last()=OutIndices.Num();
    return true;
}

bool RaftSimWaterShoreline::Build(int32 Nx, int32 Ny, TArray<FProcMeshVertex>&& Source,
    TConstArrayView<uint8> Wet, TConstArrayView<uint8> Available,
    TConstArrayView<float> DepthM, TConstArrayView<float> BedM,
    TArray<FProcMeshVertex>& OutVertices, TArray<uint32>& OutIndices,
    TArray<int32>* OutCellOffsets, TArray<FEdge>* OutEdges, bool bCompactEdges)
{
    if (!ValidInput(Nx,Ny,Source,Wet,Available,DepthM,BedM)) return false;
    return BuildClipped(Nx,Ny,MoveTemp(Source),Wet,Available,DepthM,BedM,
        OutVertices,OutIndices,OutCellOffsets,OutEdges,false,bCompactEdges);
}

void RaftSimWaterShoreline::FTopologyCache::Reset()
{
    CachedNx=CachedNy=CachedIndexCount=0;
    bCachedCompactEdges=false;
    XY.Reset(); WetMask.Reset(); AvailableMask.Reset(); Edges.Reset(); BankTriangles.Reset();
}

bool RaftSimWaterShoreline::FTopologyCache::Update(int32 Nx, int32 Ny,
    TArray<FProcMeshVertex>&& Source, TConstArrayView<uint8> Wet, TConstArrayView<uint8> Available,
    TConstArrayView<float> DepthM, TConstArrayView<float> BedM,
    TArray<FProcMeshVertex>& Vertices, TArray<uint32>& Indices, TArray<int32>& CellOffsets,
    bool& bTopologyRebuilt, bool bCompactEdges)
{
    bTopologyRebuilt=false;
    if (!ValidInput(Nx,Ny,Source,Wet,Available,DepthM,BedM)) return false;
    const int32 Count=Nx*Ny;
    bool bReuse=CachedNx==Nx && CachedNy==Ny && XY.Num()==Count && bCachedCompactEdges==bCompactEdges &&
        Vertices.Num()==Count+(bCompactEdges ? Edges.Num() : (Nx-1)*Ny+Nx*(Ny-1)) && Indices.Num()==CachedIndexCount &&
        CellOffsets.Num()==(Nx-1)*(Ny-1)+1;
    for (int32 I=0; bReuse && I<Count; ++I)
        bReuse=WetMask[I]==Wet[I] && AvailableMask[I]==Available[I] &&
            XY[I].X==Source[I].Position.X && XY[I].Y==Source[I].Position.Y;
    if (bReuse)
    {
        // Unreferenced reserve nodes need no per-frame work. Their previous
        // finite values cannot affect any triangle, anchor or active bounds.
        RaftSimWaterVertexCopy::Prefix(Source,Vertices);
        bool bCrossingChanged=false;
        for (auto& Edge : Edges)
        {
            const double NewCrossing=Crossing(Edge.WetVertex,Edge.DryVertex,DepthM,BedM);
            bCrossingChanged |= Edge.Crossing!=NewCrossing;
            Edge.Crossing=NewCrossing;
            WriteEdge(Edge,Vertices);
        }
        if (bCrossingChanged) for (const auto& Triangle : BankTriangles)
            if (Triangle.Orientation!=TriangleOrientation(Triangle.A,Triangle.B,Triangle.C,Vertices))
            { bReuse=false; break; }
        if (bReuse)
        {
            ++ReuseCount;
            return true;
        }
    }
    const bool bInitializedReserve=CachedNx==Nx && CachedNy==Ny &&
        Vertices.Num()==Count+(Nx-1)*Ny+Nx*(Ny-1);
    if (!BuildClipped(Nx,Ny,MoveTemp(Source),Wet,Available,DepthM,BedM,
        Vertices,Indices,&CellOffsets,&Edges,bInitializedReserve,bCompactEdges,&BankTriangles)) return false;
    CachedNx=Nx; CachedNy=Ny; CachedIndexCount=Indices.Num();
    bCachedCompactEdges=bCompactEdges;
    XY.SetNumUninitialized(Count); WetMask.SetNumUninitialized(Count); AvailableMask.SetNumUninitialized(Count);
    for (int32 I=0; I<Count; ++I)
    {
        XY[I]=FVector2D(Vertices[I].Position.X,Vertices[I].Position.Y);
        WetMask[I]=Wet[I]; AvailableMask[I]=Available[I];
    }
    bTopologyRebuilt=true;
    ++RebuildCount;
    return true;
}

bool RaftSimWaterShoreline::Sample(const FVector2D& PositionXY, int32 Begin, int32 End,
    TConstArrayView<FProcMeshVertex> Vertices, TConstArrayView<uint32> Indices, FVector& Position,
    FIntVector* Corners,FVector* Weights)
{
    Position=FVector::ZeroVector;
    if (Begin<0 || End<Begin || End>Indices.Num() || Begin%3 || End%3) return false;
    for (int32 I=Begin; I<End; I+=3)
    {
        if (Indices[I]>=uint32(Vertices.Num()) || Indices[I+1]>=uint32(Vertices.Num()) ||
            Indices[I+2]>=uint32(Vertices.Num())) return false;
        const auto& A=Vertices[Indices[I]];
        const auto& B=Vertices[Indices[I+1]];
        const auto& C=Vertices[Indices[I+2]];
        const FVector2D AXY(A.Position.X,A.Position.Y);
        const FVector2D AB=FVector2D(B.Position.X,B.Position.Y)-AXY;
        const FVector2D AC=FVector2D(C.Position.X,C.Position.Y)-AXY;
        const FVector2D AP=PositionXY-AXY;
        const double Det=AB.X*AC.Y-AB.Y*AC.X;
        if (FMath::Abs(Det)<1.e-20) continue;
        const double U=(AP.X*AC.Y-AP.Y*AC.X)/Det;
        const double V=(AB.X*AP.Y-AB.Y*AP.X)/Det;
        if (U>=-1.e-8 && V>=-1.e-8 && U+V<=1.+1.e-8)
        {
            Position=A.Position*(1.-U-V)+B.Position*U+C.Position*V;
            if (Corners) *Corners=FIntVector(Indices[I],Indices[I+1],Indices[I+2]);
            if (Weights) *Weights=FVector(1.-U-V,U,V);
            return !Position.ContainsNaN();
        }
    }
    return false;
}
