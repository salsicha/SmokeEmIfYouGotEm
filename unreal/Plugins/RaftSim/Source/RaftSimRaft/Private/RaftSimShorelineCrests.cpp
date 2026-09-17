#include "RaftSimShorelineCrests.h"
#include "RaftSimWaterVertexCopy.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "ProfilingDebugging/CsvProfiler.h"
#include "RaftSimCrestLookupAudit.h"
#include "RaftSimCrestContextAudit.h"
#include "RaftSimCrestCornerAudit.h"
#include "RaftSimCrestBatchAudit.h"
#include "RaftSimCrestRegionAudit.h"
#include "RaftSimFlatMemoAudit.h"
#include "RaftSimCrestInlineAudit.h"
#include "RaftSimCrestEdgeHashAudit.h"
#include "RaftSimCrestLevelMemoAudit.h"
#include "RaftSimCrestRangeAudit.h"
#include "RaftSimCrestPreparedRangeAudit.h"
#include "RaftSimCrestBoundMemoAudit.h"
#include "RaftSimCrestTopologyPublish.h"

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
    CandidateCorrectionHistory.Reset();
    MidpointExpansion.Reset();
    ParallelNormals.Reset();
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
    static const bool bFreshMemos=FParse::Param(FCommandLine::Get(),TEXT("RaftSimFreshCrestMemos"));
    static const bool bMappedHistory=FParse::Param(FCommandLine::Get(),TEXT("RaftSimMappedCrestHistory"));
    static const bool bLegacyCoordinateHash=FParse::Param(FCommandLine::Get(),TEXT("RaftSimLegacyCrestCoordinateHash"));
    static const bool bResizeContexts=FParse::Param(FCommandLine::Get(),TEXT("RaftSimResizeCrestContexts"));
    // Actual-input paired measurements rejected this candidate as slower.
    static const bool bSharedCorners=FParse::Param(FCommandLine::Get(),TEXT("RaftSimSharedCrestCorners")) &&
        !FParse::Param(FCommandLine::Get(),TEXT("RaftSimRepeatedCrestCorners"));
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
    if(SameGeometry)RaftSimCrestBatchAudit::Unchanged();
    if(SameGeometry)RaftSimCrestRegionAudit::Unchanged();
    if(SameGeometry)RaftSimFlatMemoAudit::Unchanged();
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
            Refinement.bMeasureStages=bTiming;
            static const bool bIndexedRegions=FParse::Param(FCommandLine::Get(),TEXT("RaftSimIndexedCrestRegions"));
            Refinement.bIndexedRegions=bIndexedRegions;
            static const bool bFlatMemo=FParse::Param(FCommandLine::Get(),TEXT("RaftSimFlatCrestMemo"));
            Refinement.bFlatCoordinateMemo=bFlatMemo;
            static const bool bInlineSelection=FParse::Param(FCommandLine::Get(),TEXT("RaftSimInlineCrestSelection"));
            Refinement.bInlineSelection=bInlineSelection;
            static const bool bStrongEdgeHash=FParse::Param(FCommandLine::Get(),TEXT("RaftSimStrongCrestEdgeHash"));
            Refinement.bStrongEdgeHash=bStrongEdgeHash;
            static const bool bLevelLocalMemos=FParse::Param(FCommandLine::Get(),TEXT("RaftSimLevelLocalCrestMemos"));
            Refinement.bLevelLocalMemos=bLevelLocalMemos;
            static const bool bBoundMemo=FParse::Param(FCommandLine::Get(),TEXT("RaftSimBoundCrestMemo"));
            Refinement.bBoundCoordinateMemo=bBoundMemo;
            static const bool bRangeBound=!FParse::Param(FCommandLine::Get(),TEXT("RaftSimReferenceCrestRange"));
            // The corrected spatial index is exact and slightly faster in
            // both orders of two actual-input captures, including preparation.
            // Preserve the full reference scan as an independent control.
            static const bool bPreparedRange=!FParse::Param(FCommandLine::Get(),TEXT("RaftSimUnpreparedCrestRange"));
            Refinement.HeightRangeWidthCm=bRangeBound
                ? (bPreparedRange && Input.PreparedHeightRangeWidthAtWorldXYCm
                    ? Input.PreparedHeightRangeWidthAtWorldXYCm : Input.HeightRangeWidthAtWorldXYCm)
                : TFunction<float(const FBox2D&)>();
            const uint64 OldBuilds=Refinement.TopologyBuildCount,OldReuses=Refinement.TopologyReuseCount;
            if (!Refinement.BuildAdaptive(XY,Triangles,Input.HeightAtWorldXYCm,3,.5f,Input.NonzeroRegionsCm,nullptr,true,true,
                Input.DetailSpanCm>0 ? &Input.DetailWindowCm : nullptr,Input.DetailSpanCm,!bFreshMemos,!bLegacyCoordinateHash,!bResizeContexts,bSharedCorners)) return false;
            CSV_CUSTOM_STAT(RaftSimCrests,TopologyLevelsBuilt,int32(Refinement.TopologyBuildCount-OldBuilds),ECsvCustomStatOp::Accumulate);
            CSV_CUSTOM_STAT(RaftSimCrests,TopologyLevelsReused,int32(Refinement.TopologyReuseCount-OldReuses),ECsvCustomStatOp::Accumulate);
            CSV_CUSTOM_STAT(RaftSimCrests,MemoContextsCreated,int32(Refinement.ParallelContextsCreated),ECsvCustomStatOp::Accumulate);
            CSV_CUSTOM_STAT(RaftSimCrests,MemoContextsDestroyed,int32(Refinement.ParallelContextsDestroyed),ECsvCustomStatOp::Accumulate);
            CSV_CUSTOM_STAT(RaftSimCrests,MemoAllocatedBytes,Refinement.GetRetainedMemoAllocatedBytes(),ECsvCustomStatOp::Set);
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
        RaftSimCrestLookupAudit::Run(CachedXY,Triangles,Input);
        RaftSimCrestContextAudit::Run(CachedXY,Triangles,Input);
        RaftSimCrestCornerAudit::Run(CachedXY,Triangles,Input);
        RaftSimCrestBatchAudit::Run(CachedXY,Triangles,Input);
        RaftSimCrestRegionAudit::Run(CachedXY,Triangles,Input);
        RaftSimFlatMemoAudit::Run(CachedXY,Triangles,Input);
        RaftSimCrestInlineAudit::Run(CachedXY,Triangles,Input,Refinement);
        RaftSimCrestEdgeHashAudit::Run(CachedXY,Triangles,Input,Refinement);
        RaftSimCrestLevelMemoAudit::Run(CachedXY,Triangles,Input,Refinement);
        RaftSimCrestRangeAudit::Run(CachedXY,Triangles,Input,Refinement);
        RaftSimCrestPreparedRangeAudit::Run(CachedXY,Triangles,Input,Refinement);
        RaftSimCrestBoundMemoAudit::Run(CachedXY,Triangles,Input,Refinement);
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
    // Paired playable runs preserve exact attributes and improve both call orders.
    // Retain the original serial path for controlled regression comparisons.
    static const bool bParallelMidpoints=!FParse::Param(FCommandLine::Get(),TEXT("RaftSimSerialCrestMidpoints"));
    static const bool bMidpointAudit=FParse::Param(FCommandLine::Get(),TEXT("RaftSimCrestMidpointAudit"));
    const auto SerialMidpoints=[&](TArray<FProcMeshVertex>& Output)
    {
        for(int32 I=0;I<Refinement.MidpointParents.Num();++I)
        {const auto P=Refinement.MidpointParents[I];Output[Source.Num()+I]=Midpoint(Output[P.X],Output[P.Y]);}
    };
    if(bMidpointAudit && GFrameCounter>=100 && GFrameCounter<=250)
    {
        TArray<FProcMeshVertex> Candidate;Candidate.SetNumUninitialized(Count);
        RaftSimWaterVertexCopy::Prefix(Source,Candidate);
        double SerialMs=0,ParallelMs=0;bool Valid=true;
        const auto Serial=[&](){const double Start=FPlatformTime::Seconds();SerialMidpoints(Vertices);SerialMs=(FPlatformTime::Seconds()-Start)*1000.;};
        const auto Parallel=[&](){const double Start=FPlatformTime::Seconds();Valid=MidpointExpansion.Expand(Candidate,Source.Num(),Refinement.MidpointParents);ParallelMs=(FPlatformTime::Seconds()-Start)*1000.;};
        if(GFrameCounter%2){Parallel();Serial();}else{Serial();Parallel();}
        for(int32 I=0;Valid && I<Vertices.Num();++I)Valid=FRaftSimCrestMidpointExpansion::EqualAttributes(Vertices[I],Candidate[I]);
        if(!Valid){UE_LOG(LogTemp,Error,TEXT("CrestMidpointAudit mismatch frame=%llu"),GFrameCounter);return false;}
        UE_LOG(LogTemp,Display,TEXT("CrestMidpointAudit exact frame=%llu vertices=%d midpoints=%d bands=%d serial_ms=%.6f parallel_ms=%.6f parallel_first=%d"),
            GFrameCounter,Vertices.Num(),Refinement.MidpointParents.Num(),MidpointExpansion.BandCount(),SerialMs,ParallelMs,int32(GFrameCounter%2));
        if(bParallelMidpoints)Vertices=MoveTemp(Candidate);
    }
    else if(bParallelMidpoints)
    {if(!MidpointExpansion.Expand(Vertices,Source.Num(),Refinement.MidpointParents))return false;}
    else SerialMidpoints(Vertices);
    const float Alpha=FMath::Clamp(Input.BlendAlpha,0.f,1.f);
    static const bool bHistoryHashAudit=FParse::Param(FCommandLine::Get(),TEXT("RaftSimCrestHistoryHashAudit"));
    bool bDenseHistory=false;
    if(bHistoryHashAudit)
    {
        auto ReferenceVertices=Vertices;
        TArray<float> ReferenceRendered;
        double FastMs=0,LegacyMs=0;bool ReferenceDense=false;
        const auto Fast=[&]()
        {
            const double Begin=FPlatformTime::Seconds();
            ReferenceDense=CandidateCorrectionHistory.Apply(ReferenceVertices,Source.Num(),BoundaryMidpoints,
                TargetCorrectionsCm,Alpha,ReferenceRendered,!bMappedHistory);
            FastMs=(FPlatformTime::Seconds()-Begin)*1000.;
        };
        const auto Legacy=[&]()
        {
            const double Begin=FPlatformTime::Seconds();
            bDenseHistory=CorrectionHistory.Apply(Vertices,Source.Num(),BoundaryMidpoints,
                TargetCorrectionsCm,Alpha,RenderedCorrectionsCm,!bMappedHistory);
            LegacyMs=(FPlatformTime::Seconds()-Begin)*1000.;
        };
        if(GFrameCounter%2){Fast();Legacy();}else{Legacy();Fast();}
        const bool Exact=bDenseHistory==ReferenceDense && RenderedCorrectionsCm==ReferenceRendered &&
            FMemory::Memcmp(Vertices.GetData(),ReferenceVertices.GetData(),SIZE_T(Vertices.Num())*sizeof(FProcMeshVertex))==0;
        if(!Exact){UE_LOG(LogTemp,Error,TEXT("CrestHistoryHashAudit mismatch frame=%llu"),GFrameCounter);return false;}
        UE_LOG(LogTemp,Display,TEXT("CrestHistoryHashAudit exact frame=%llu vertices=%d dense=%d fast_ms=%.6f legacy_ms=%.6f fast_first=%d"),
            GFrameCounter,Vertices.Num(),bDenseHistory,FastMs,LegacyMs,int32(GFrameCounter%2));
    }
    else bDenseHistory=CorrectionHistory.Apply(Vertices,Source.Num(),BoundaryMidpoints,
        TargetCorrectionsCm,Alpha,RenderedCorrectionsCm,!bMappedHistory);
    CSV_CUSTOM_STAT(RaftSimCrests,DenseHistoryUpdates,int32(bDenseHistory),ECsvCustomStatOp::Accumulate);
    const double VerticesDone=bTiming ? FPlatformTime::Seconds() : 0.;
    // Sixty-four actual-game pairs preserve all bits and improve both call
    // orders. Keep the original publisher as an independent regression control.
    static const bool bPartitionedTopology=!FParse::Param(FCommandLine::Get(),TEXT("RaftSimReferenceCrestTopology"));
    static const bool bTopologyAudit=FParse::Param(FCommandLine::Get(),TEXT("RaftSimCrestTopologyPublishAudit"));
    if (bTopologyAudit && GFrameCounter>=120 && GFrameCounter<184)
    {
        TArray<uint32> CandidateIndices;
        // The caller supplies fresh indices but retains cell-offset storage.
        // Give both measured paths the same initialized output size.
        TArray<int32> CandidateOffsets=CellOffsets;
        double ReferenceMs=0.,CandidateMs=0.;
        const auto Reference=[&]() { const double Start=FPlatformTime::Seconds();
            RaftSimCrestTopologyPublish::Reference(Refinement.Triangles,Refinement.TriangleOrigins,SourceCellOffsets,Indices,CellOffsets);
            ReferenceMs=(FPlatformTime::Seconds()-Start)*1000.; };
        const auto Candidate=[&]() { const double Start=FPlatformTime::Seconds();
            RaftSimCrestTopologyPublish::Partitioned(Refinement.Triangles,Refinement.TriangleOrigins,SourceCellOffsets,CandidateIndices,CandidateOffsets);
            CandidateMs=(FPlatformTime::Seconds()-Start)*1000.; };
        if (GFrameCounter%2) { Candidate(); Reference(); } else { Reference(); Candidate(); }
        const bool Exact=Indices==CandidateIndices && CellOffsets==CandidateOffsets;
        UE_LOG(LogTemp,Display,TEXT("CrestTopologyPublishAudit frame=%llu exact=%d candidate_first=%d indices=%d cells=%d reference_ms=%.9f candidate_ms=%.9f"),
            GFrameCounter,Exact,int32(GFrameCounter%2),Indices.Num(),CellOffsets.Num(),ReferenceMs,CandidateMs);
        if (!Exact) return false;
        if (bPartitionedTopology) { Indices=MoveTemp(CandidateIndices); CellOffsets=MoveTemp(CandidateOffsets); }
    }
    else if (bPartitionedTopology)
        RaftSimCrestTopologyPublish::Partitioned(Refinement.Triangles,Refinement.TriangleOrigins,SourceCellOffsets,Indices,CellOffsets);
    else RaftSimCrestTopologyPublish::Reference(Refinement.Triangles,Refinement.TriangleOrigins,SourceCellOffsets,Indices,CellOffsets);
    const double TopologyDone=bTiming ? FPlatformTime::Seconds() : 0.;
    {
    CSV_SCOPED_TIMING_STAT(RaftSimCrests,Normals);
    // Same-input playable audit preserves every attribute and improves both
    // call orders including rebuild costs. Retain the original control path.
    static const bool bParallelNormals=!FParse::Param(FCommandLine::Get(),TEXT("RaftSimSerialCrestNormals"));
    static const bool bNormalsAudit=FParse::Param(FCommandLine::Get(),TEXT("RaftSimCrestNormalsAudit"));
    if(bNormalsAudit && GFrameCounter>=100 && GFrameCounter<=250)
    {
        TArray<FProcMeshVertex> Candidate=Vertices;
        double SerialMs=0.,ParallelMs=0.;bool Valid=true;
        const uint64 Builds=ParallelNormals.Builds;
        const auto Serial=[&](){const double Start=FPlatformTime::Seconds();FRaftSimCrestNormals::Reference(Vertices,Indices,Source.Num());SerialMs=(FPlatformTime::Seconds()-Start)*1000.;};
        const auto Parallel=[&](){const double Start=FPlatformTime::Seconds();Valid=ParallelNormals.Apply(Candidate,Indices,Source.Num());ParallelMs=(FPlatformTime::Seconds()-Start)*1000.;};
        if(GFrameCounter%2){Parallel();Serial();}else{Serial();Parallel();}
        for(int32 I=0;Valid && I<Vertices.Num();++I)Valid=FRaftSimCrestMidpointExpansion::EqualAttributes(Vertices[I],Candidate[I]);
        if(!Valid){UE_LOG(LogTemp,Error,TEXT("CrestNormalsAudit mismatch frame=%llu"),GFrameCounter);return false;}
        UE_LOG(LogTemp,Display,TEXT("CrestNormalsAudit exact frame=%llu vertices=%d triangles=%d rebuilt=%d serial_ms=%.6f parallel_ms=%.6f parallel_first=%d"),
            GFrameCounter,Vertices.Num(),Indices.Num()/3,int32(ParallelNormals.Builds!=Builds),SerialMs,ParallelMs,int32(GFrameCounter%2));
        if(bParallelNormals)Vertices=MoveTemp(Candidate);
    }
    else if(bParallelNormals)
    {if(!ParallelNormals.Apply(Vertices,Indices,Source.Num()))return false;}
    else FRaftSimCrestNormals::Reference(Vertices,Indices,Source.Num());
    }
    if (bTiming)
    {
        const double End=FPlatformTime::Seconds();
        UE_LOG(LogTemp,Display,TEXT("WaterCrestPerf frame=%llu rebuild=%d total_ms=%.4f selection_ms=%.4f targets_ms=%.4f vertices_ms=%.4f topology_ms=%.4f normals_ms=%.4f fine_vertices=%d xy_changed=%d indices_changed=%d profile_changed=%d coarse_changed=%d shore_changed=%d detail_changed=%d sample_ms=%.4f assembly_ms=%.4f refine_input_ms=%.4f"),
            GFrameCounter,SameGeometry ? 0 : 1,(End-Started)*1000.,SelectionMs,TargetsMs,
            (VerticesDone-Started)*1000.-SelectionMs-TargetsMs,(TopologyDone-VerticesDone)*1000.,
            (End-TopologyDone)*1000.,Refinement.MidpointParents.Num(),!SameXY,!SameIndices,!SameProfile,!SameCoarse,!SameShore,!SameDetail,
            SameGeometry ? 0 : Refinement.SelectionSeconds*1000.,SameGeometry ? 0 : Refinement.AssemblySeconds*1000.,
            SameGeometry ? 0 : Refinement.InputSeconds*1000.);
    }
    return true;
}
