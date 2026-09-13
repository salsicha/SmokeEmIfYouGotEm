#include "RaftSimShorelineCrests.h"
#include "RaftSimWaterVertexCopy.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "ProfilingDebugging/CsvProfiler.h"

CSV_DEFINE_CATEGORY(RaftSimCrests,true);

namespace
{
uint64 EdgeKey(int32 A,int32 B)
{ return (uint64(FMath::Min(A,B))<<32)|uint32(FMath::Max(A,B)); }

FProcMeshVertex Midpoint(const FProcMeshVertex& A,const FProcMeshVertex& B)
{
    FProcMeshVertex V;
    V.Position=(A.Position+B.Position)*.5;
    V.Normal=(A.Normal+B.Normal).GetSafeNormal();
    V.Color=((A.Color.ReinterpretAsLinear()+B.Color.ReinterpretAsLinear())*.5f).ToFColor(false);
    V.UV0=(A.UV0+B.UV0)*.5; V.UV1=(A.UV1+B.UV1)*.5;
    V.UV2=(A.UV2+B.UV2)*.5; V.UV3=(A.UV3+B.UV3)*.5;
    V.Tangent=FProcMeshTangent((A.Tangent.TangentX+B.Tangent.TangentX).GetSafeNormal(),A.Tangent.bFlipTangentY);
    return V;
}
}

void FRaftSimShorelineCrests::Reset()
{
    CachedXY.Reset(); CachedIndices.Reset(); CachedProfile.Reset();
    CachedCoarse.Reset(); CachedShore.Reset(); CorrectionHistory.Reset();
    TargetCorrectionsCm.Reset(); RenderedCorrectionsCm.Reset();
    FineProfileCm.Reset();
}

bool FRaftSimShorelineCrests::Update(const TArray<FProcMeshVertex>& Source,
    const TArray<uint32>& SourceIndices,const TArray<int32>& SourceCellOffsets,
    const TArray<float>& CoarseCrestCm,const TArray<float>& Shore,
    const FRaftSimShorelineCrestInput& Input,TArray<FProcMeshVertex>& Vertices,
    TArray<uint32>& Indices,TArray<int32>& CellOffsets)
{
    CSV_SCOPED_TIMING_STAT(RaftSimCrests,Update);
    if (Source.Num()!=CoarseCrestCm.Num() || Source.Num()!=Shore.Num() ||
        !Input.HeightAtWorldXYCm || SourceCellOffsets.IsEmpty()) return false;
    static const bool bTiming=FParse::Param(FCommandLine::Get(),TEXT("RaftSimWaterStageTimings"));
    const double Started=bTiming ? FPlatformTime::Seconds() : 0.;
    double SelectionMs=0., TargetsMs=0.;
    const bool SameIndices=CachedIndices==SourceIndices,SameProfile=CachedProfile==Input.ProfileKey;
    const bool SameCoarse=CachedCoarse==CoarseCrestCm,SameShore=CachedShore==Shore;
    const bool SameDetail=
        CachedDetailSpanCm==Input.DetailSpanCm &&
        (Input.DetailSpanCm<=0 || CachedDetailWindowCm==Input.DetailWindowCm);
    bool SameXY=CachedXY.Num()==Source.Num();
    for (int32 I=0; SameXY && I<Source.Num(); ++I)
        SameXY=CachedXY[I]==FVector2D(Source[I].Position.X,Source[I].Position.Y);
    const bool SameGeometry=SameXY && SameIndices && SameProfile && SameDetail;
    const bool SameTargets=SameGeometry && SameCoarse && SameShore;
    CSV_CUSTOM_STAT(RaftSimCrests,UpdateCalls,1,ECsvCustomStatOp::Accumulate);
    CSV_CUSTOM_STAT(RaftSimCrests,XYChanged,int32(!SameXY),ECsvCustomStatOp::Accumulate);
    CSV_CUSTOM_STAT(RaftSimCrests,IndicesChanged,int32(!SameIndices),ECsvCustomStatOp::Accumulate);
    CSV_CUSTOM_STAT(RaftSimCrests,ProfileChanged,int32(!SameProfile),ECsvCustomStatOp::Accumulate);
    CSV_CUSTOM_STAT(RaftSimCrests,CoarseChanged,int32(!SameCoarse),ECsvCustomStatOp::Accumulate);
    CSV_CUSTOM_STAT(RaftSimCrests,ShoreChanged,int32(!SameShore),ECsvCustomStatOp::Accumulate);
    CSV_CUSTOM_STAT(RaftSimCrests,DetailWindowChanged,int32(!SameDetail),ECsvCustomStatOp::Accumulate);
    if (!SameGeometry)
    {
        TArray<FVector2D> XY; XY.Reserve(Source.Num());
        for (const auto& V:Source) XY.Emplace(V.Position.X,V.Position.Y);
        TArray<int32> Triangles; Triangles.Reserve(SourceIndices.Num());
        for (uint32 I:SourceIndices) Triangles.Add(int32(I));
        // Half-centimeter selection leaves margin for the unchanged 2 cm
        // independent interior-sampling gate; three levels reach 12.5 cm.
        // The actor supplies an immutable captured support-site profile. Avoid
        // a shared hash table and evaluate independent triangles concurrently.
        const uint64 PreviousTopologyBuilds=Refinement.TopologyBuildCount;
        {
            CSV_SCOPED_TIMING_STAT(RaftSimCrests,Selection);
            const uint64 OldBuilds=Refinement.TopologyBuildCount,OldReuses=Refinement.TopologyReuseCount;
            if (!Refinement.BuildAdaptive(XY,Triangles,Input.HeightAtWorldXYCm,3,.5f,Input.NonzeroRegionsCm,nullptr,true,true,
                Input.DetailSpanCm>0 ? &Input.DetailWindowCm : nullptr,Input.DetailSpanCm)) return false;
            CSV_CUSTOM_STAT(RaftSimCrests,TopologyLevelsBuilt,int32(Refinement.TopologyBuildCount-OldBuilds),ECsvCustomStatOp::Accumulate);
            CSV_CUSTOM_STAT(RaftSimCrests,TopologyLevelsReused,int32(Refinement.TopologyReuseCount-OldReuses),ECsvCustomStatOp::Accumulate);
        }
        const double Selected=bTiming ? FPlatformTime::Seconds() : 0.;
        SelectionMs=(Selected-Started)*1000.;
        TArray<FVector2D> ExpandedXY; Refinement.Expand(XY,ExpandedXY);
        if (PreviousTopologyBuilds!=Refinement.TopologyBuildCount)
        {
            // Boundary membership is combinatorial too. Reusing ALL levels
            // guarantees identical root indices and ordered parents, even
            // when the shoreline's current coordinates have moved.
            TMap<uint64,int32> EdgeUses;
            for (int32 T=0; T<Triangles.Num(); T+=3) for (int32 E=0; E<3; ++E)
                ++EdgeUses.FindOrAdd(EdgeKey(Triangles[T+E],Triangles[T+(E+1)%3]));
            TSet<uint64> Boundary;
            for (const auto& E:EdgeUses) if (E.Value==1) Boundary.Add(E.Key);
            BoundaryMidpoints.Init(0,Refinement.MidpointParents.Num());
            for (int32 I=0; I<Refinement.MidpointParents.Num(); ++I)
            {
                const auto P=Refinement.MidpointParents[I]; const int32 Node=Source.Num()+I;
                const uint64 Key=EdgeKey(P.X,P.Y);
                if (Boundary.Contains(Key))
                {
                    BoundaryMidpoints[I]=1;
                    Boundary.Remove(Key); Boundary.Add(EdgeKey(P.X,Node)); Boundary.Add(EdgeKey(Node,P.Y));
                }
            }
        }
        FineProfileCm.Init(0,ExpandedXY.Num());
        // Same pure current profile used by parallel selection; each worker
        // owns one destination. No shared memo, averaging or stale heights.
        ParallelFor(Refinement.MidpointParents.Num(),[&](int32 I)
        {
            const int32 Node=Source.Num()+I;
            if (!BoundaryMidpoints[I])FineProfileCm[Node]=Input.HeightAtWorldXYCm(ExpandedXY[Node]);
        });
        CachedXY=MoveTemp(XY); CachedIndices=SourceIndices; CachedProfile=Input.ProfileKey;
        CachedDetailWindowCm=Input.DetailWindowCm;CachedDetailSpanCm=Input.DetailSpanCm;
        ++BuildCount;
        TargetsMs=bTiming ? (FPlatformTime::Seconds()-Selected)*1000. : 0.;
    }
    if (!SameTargets)
    {
        // Selection depends on XY/topology/the continuous profile, NOT the
        // current coarse-height subtraction or shore blend. Those can change
        // independently without rerunning expensive adaptive profile samples.
        const double TargetStarted=bTiming ? FPlatformTime::Seconds() : 0.;
        Refinement.Expand(CoarseCrestCm,ExpandedCoarseCrestCm);
        Refinement.Expand(Shore,ExpandedShore);
        TargetCorrectionsCm.Init(0,FineProfileCm.Num());
        for (int32 I=0;I<Refinement.MidpointParents.Num();++I)
        {
            const int32 Node=Source.Num()+I;
            if (!BoundaryMidpoints[I])
                TargetCorrectionsCm[Node]=FineProfileCm[Node]*ExpandedShore[Node]-ExpandedCoarseCrestCm[Node];
        }
        CachedCoarse=CoarseCrestCm;CachedShore=Shore;
        if (bTiming)TargetsMs+=(FPlatformTime::Seconds()-TargetStarted)*1000.;
    }
    const int32 Count=Source.Num()+Refinement.MidpointParents.Num();
    // Source prefix and every midpoint are completely assigned before use.
    Vertices.SetNumUninitialized(Count,EAllowShrinking::No);
    RaftSimWaterVertexCopy::Prefix(Source,Vertices);
    // Build the uncorrected parent interpolation first. Adding a correction
    // while constructing descendants would double-count parent crest relief.
    for (int32 I=0; I<Refinement.MidpointParents.Num(); ++I)
    {
        const auto P=Refinement.MidpointParents[I];
        Vertices[Source.Num()+I]=Midpoint(Vertices[P.X],Vertices[P.Y]);
    }
    const float Alpha=FMath::Clamp(Input.BlendAlpha,0.f,1.f);
    TMap<FVector2D,float> NextHistory;
    RenderedCorrectionsCm.Init(0,Count);
    for (int32 I=0; I<Refinement.MidpointParents.Num(); ++I)
    {
        const int32 Node=Source.Num()+I;
        auto& V=Vertices[Node]; const FVector2D XY(V.Position.X,V.Position.Y);
        const float* Previous=CorrectionHistory.Find(XY);
        const float Correction=BoundaryMidpoints[I] ? 0.f : FMath::Lerp(
            Previous ? *Previous : 0.f,TargetCorrectionsCm[Node],Alpha);
        V.Position.Z+=Correction; RenderedCorrectionsCm[Node]=Correction;
        NextHistory.Add(XY,Correction);
    }
    CorrectionHistory=MoveTemp(NextHistory); // Bounded to this current window.
    const double VerticesDone=bTiming ? FPlatformTime::Seconds() : 0.;
    Indices.Reset(Refinement.Triangles.Num());
    for (int32 I:Refinement.Triangles) Indices.Add(uint32(I));
    CellOffsets.SetNumUninitialized(SourceCellOffsets.Num());
    int32 Triangle=0;
    for (int32 Cell=0; Cell<SourceCellOffsets.Num(); ++Cell)
    {
        while (Triangle<Refinement.TriangleOrigins.Num() &&
            Refinement.TriangleOrigins[Triangle]<SourceCellOffsets[Cell]/3) ++Triangle;
        CellOffsets[Cell]=Triangle*3;
    }
    const double TopologyDone=bTiming ? FPlatformTime::Seconds() : 0.;
    TArray<FVector> Sums; Sums.Init(FVector::ZeroVector,Count);
    TArray<uint8> Touched; Touched.Init(0,Count);
    for (int32 T=0; T<Indices.Num(); T+=3)
    {
        const int32 A=Indices[T],B=Indices[T+1],C=Indices[T+2];
        const FVector N=FVector::CrossProduct(Vertices[C].Position-Vertices[A].Position,
            Vertices[B].Position-Vertices[A].Position);
        Sums[A]+=N; Sums[B]+=N; Sums[C]+=N;
        if (A>=Source.Num() || B>=Source.Num() || C>=Source.Num()) Touched[A]=Touched[B]=Touched[C]=1;
    }
    for (int32 I=0; I<Count; ++I) if (Touched[I] && !Sums[I].IsNearlyZero())
    {
        auto& V=Vertices[I]; V.Normal=Sums[I].GetSafeNormal();
        auto& T=V.Tangent.TangentX;
        T=(T-V.Normal*FVector::DotProduct(T,V.Normal)).GetSafeNormal();
    }
    if (bTiming)
    {
        const double End=FPlatformTime::Seconds();
        UE_LOG(LogTemp,Display,TEXT("WaterCrestPerf frame=%llu rebuild=%d total_ms=%.4f selection_ms=%.4f targets_ms=%.4f vertices_ms=%.4f topology_ms=%.4f normals_ms=%.4f fine_vertices=%d xy_changed=%d indices_changed=%d profile_changed=%d coarse_changed=%d shore_changed=%d detail_changed=%d"),
            GFrameCounter,SameGeometry ? 0 : 1,(End-Started)*1000.,SelectionMs,TargetsMs,
            (VerticesDone-Started)*1000.-SelectionMs-TargetsMs,(TopologyDone-VerticesDone)*1000.,
            (End-TopologyDone)*1000.,Refinement.MidpointParents.Num(),!SameXY,!SameIndices,!SameProfile,!SameCoarse,!SameShore,!SameDetail);
    }
    return true;
}
