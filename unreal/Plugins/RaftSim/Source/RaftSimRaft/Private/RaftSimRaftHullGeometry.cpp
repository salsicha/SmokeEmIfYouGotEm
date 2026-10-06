#include "RaftSimRaftActor.h"
#include "RaftSimRaftMesh.h"
#include "RaftSimHullPrepareCache.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "ProfilingDebugging/CsvProfiler.h"
#include "Async/ParallelFor.h"

CSV_DEFINE_CATEGORY(RaftSimHull,true);

#if !UE_BUILD_SHIPPING
bool ARaftSimRaftActor::BindIsolatedFeatureHull(URaftSimChronoRuntimeAdapter* Runtime)
{
    if(!Runtime || !bUsingProductionRaftRestMesh || GetActorScale3D()!=FVector::OneVector)
    {
        const FVector Scale=GetActorScale3D();
        UE_LOG(LogTemp,Error,TEXT("Isolated hull precondition: runtime=%d production=%d scale=(%.17g,%.17g,%.17g)"),
            int32(Runtime!=nullptr),int32(bUsingProductionRaftRestMesh),Scale.X,Scale.Y,Scale.Z);
        return false;
    }
    RaftAdapter=Runtime;LastRenderedHullRevision=0;LastLoggedHullRevision=0;
    SharedHullRenderedCache=MakeShared<RaftSimHullPrepareCache::FCache>();SharedHullShadingUploads=0;
    const TWeakObjectPtr<ARaftSimRaftActor> WeakThis(this);
    const auto SnapshotCache=MakeShared<RaftSimHullPrepareCache::FCache>();
    const bool bCacheExactShape=true;
    const bool bReferenceRestKey=FParse::Param(FCommandLine::Get(),TEXT("RaftSimReferenceRestKey"));
    // Actual same-input AND same-module scene controls measured byte-comparison
    // reuse slower than assignment. Keep original copies in normal play.
    const bool bReferenceSnapshotCopy=!FParse::Param(FCommandLine::Get(),TEXT("RaftSimExactSnapshotCopy")) ||
        FParse::Param(FCommandLine::Get(),TEXT("RaftSimReferenceSnapshotCopy"));
    const bool Bound=Runtime->SetHullGeometryProvider(
        [WeakThis,SnapshotCache,bCacheExactShape,bReferenceSnapshotCopy,bReferenceRestKey](const TArray<FRaftSimFlexVisualSegmentState>& Segments,FRaftSimHullGeometry& Out)
        {
            auto* Self=WeakThis.Get();if(!Self || !Self->RaftVisual || !Self->RaftAdapter)return false;
            const double Started=FPlatformTime::Seconds();
            const RaftSimRaftMesh::FRaftSimRaftVisualCondition C={Self->RaftAdapter->GetFlexiblePressureFraction(),
                Self->RaftAdapter->GetFlexibleFabricIntegrity(),Self->RaftCondition.PermanentCreaseAmplitudeM};
            const auto T=Self->RaftVisual->GetRelativeTransform();
            bool Cached=false;
            {
                CSV_SCOPED_TIMING_STAT(RaftSimHull,PreparedKeyValidation);
                Cached=bCacheExactShape && Self->bUsingProductionRaftRestMesh && Self->GetActorScale3D()==FVector::OneVector &&
                    SnapshotCache->Matches(Self->ProductionRaftRestSections,Self->TubeRadiusM,Segments,C,T,bReferenceRestKey);
            }
            const bool SealedKey=!bReferenceRestKey && SnapshotCache->HasSealedRestKey(Self->ProductionRaftRestSections);
            CSV_CUSTOM_STAT(RaftSimHull,RestKeySealedChecks,int32(SealedKey),ECsvCustomStatOp::Accumulate);
            CSV_CUSTOM_STAT(RaftSimHull,RestKeyReferenceChecks,int32(!SealedKey),ECsvCustomStatOp::Accumulate);
            CSV_CUSTOM_STAT(RaftSimHull,PreparedCacheHits,int32(Cached),ECsvCustomStatOp::Accumulate);
            CSV_CUSTOM_STAT(RaftSimHull,PreparedCacheMisses,int32(!Cached),ECsvCustomStatOp::Accumulate);
            if(Cached)
            {
                {
                    CSV_SCOPED_TIMING_STAT(RaftSimHull,PreparedSnapshotCopy);
                    Self->SharedHullPreparedSegments=Segments;Self->SharedHullPreparedCondition=C;
                    RaftSimHullPrepareCache::FCopyCounts Copies;
                    // Render sections reach ProductionRaftDeformedSections only via
                    // the commit swap, and every reader regenerates (and here
                    // re-validates) them first; topology/UVs are immutable. Only
                    // the physics hull must be copied on a hit.
                    static const bool bCopyPreparedSections=FParse::Param(FCommandLine::Get(),TEXT("RaftSimCopyCachedPreparedSections"));
                    if(bReferenceSnapshotCopy && !bCopyPreparedSections)
                    {Out=SnapshotCache->Hull;Copies.Assigned=3;}
                    else if(bReferenceSnapshotCopy)
                    {Self->SharedHullPreparedSections=SnapshotCache->Prepared;Out=SnapshotCache->Hull;Copies.Assigned=5*SnapshotCache->Prepared.Num()+3;}
                    else
                    {
                        RaftSimHullPrepareCache::CopyPreparedIfChanged(SnapshotCache->Prepared,Self->SharedHullPreparedSections,Copies);
                        RaftSimHullPrepareCache::CopyHullIfChanged(SnapshotCache->Hull,Out,Copies);
                    }
                    CSV_CUSTOM_STAT(RaftSimHull,PreparedArraysAssigned,Copies.Assigned,ECsvCustomStatOp::Accumulate);
                    CSV_CUSTOM_STAT(RaftSimHull,PreparedArraysRetained,Copies.Retained,ECsvCustomStatOp::Accumulate);
                }
                const double Ms=(FPlatformTime::Seconds()-Started)*1000.;++Self->SharedHullPrepareCount;
                Self->SharedHullPrepareTotalMs+=Ms;Self->SharedHullPrepareMaximumMs=FMath::Max(Self->SharedHullPrepareMaximumMs,Ms);
                // The adapter runs IsValid on this exact snapshot (Out is its
                // pending hull) immediately after we return; repeating the
                // full byte comparison here changed nothing but its cost.
                return true;
            }
            bool Valid=false;
            {
                CSV_SCOPED_TIMING_STAT(RaftSimHull,PreparedSnapshotDeformExport);
                Valid=Self->PrepareSharedHullGeometry(Segments,Out);
            }
            if(Valid && bCacheExactShape)
            {
                CSV_SCOPED_TIMING_STAT(RaftSimHull,PreparedSnapshotRemember);
                SnapshotCache->Remember(Self->ProductionRaftRestSections,Self->TubeRadiusM,Segments,C,T,Self->SharedHullPreparedSections,Out);
            }
            return Valid;
        },
        [WeakThis](){if(auto* Self=WeakThis.Get())Self->CommitSharedHullGeometry();});
    if(!Bound)UE_LOG(LogTemp,Error,TEXT("Isolated production hull export refused: rest_sections=%d visual=%d"),ProductionRaftRestSections ? ProductionRaftRestSections->GetSections().Num() : 0,int32(RaftVisual!=nullptr));
    return Bound;
}
void ARaftSimRaftActor::RefreshIsolatedFeatureHull(){UpdateSharedHullVisual();}
#endif

void ARaftSimRaftActor::ConfigureSharedHullGeometryReview()
{
    bSharedHullGeometryReview=true;
    SharedHullRenderedCache=MakeShared<RaftSimHullPrepareCache::FCache>();SharedHullShadingUploads=0;
    LastRenderedHullRevision=0;LastLoggedHullRevision=0;
    SharedHullPrepareCount=0;SharedHullPrepareTotalMs=0;SharedHullPrepareMaximumMs=0;
    SharedHullPreparedSections.Reset();
    SharedHullPreparedSegments.Reset();SharedHullPublishedSegments.Reset();
    if(!bUsingProductionRaftRestMesh || GetActorScale3D()!=FVector::OneVector)
    {
        UE_LOG(LogTemp,Error,TEXT("Shared hull review requires the original production mesh and unit actor scale; no proxy fallback"));
        SetActorTickEnabled(false);return;
    }
    TWeakObjectPtr<ARaftSimRaftActor> WeakThis(this);
    const auto SnapshotCache=MakeShared<RaftSimHullPrepareCache::FCache>();
    const bool bReferenceRestKey=FParse::Param(FCommandLine::Get(),TEXT("RaftSimReferenceRestKey"));
    const bool bReferenceSnapshotCopy=!FParse::Param(FCommandLine::Get(),TEXT("RaftSimExactSnapshotCopy")) ||
        FParse::Param(FCommandLine::Get(),TEXT("RaftSimReferenceSnapshotCopy"));
    if(!RaftAdapter->SetHullGeometryProvider(
        [WeakThis,SnapshotCache,bReferenceSnapshotCopy,bReferenceRestKey](const TArray<FRaftSimFlexVisualSegmentState>& Segments,FRaftSimHullGeometry& Out)
        {
            auto* Self=WeakThis.Get();if(!Self || !Self->RaftAdapter || !Self->RaftVisual)return false;
            const RaftSimRaftMesh::FRaftSimRaftVisualCondition C={Self->RaftAdapter->GetFlexiblePressureFraction(),
                Self->RaftAdapter->GetFlexibleFabricIntegrity(),Self->RaftCondition.PermanentCreaseAmplitudeM};
            const auto T=Self->RaftVisual->GetRelativeTransform();
            bool Cached=false;
            {
                CSV_SCOPED_TIMING_STAT(RaftSimHull,PreparedKeyValidation);
                Cached=SnapshotCache->Matches(Self->ProductionRaftRestSections,Self->TubeRadiusM,Segments,C,T,bReferenceRestKey);
            }
            const bool SealedKey=!bReferenceRestKey && SnapshotCache->HasSealedRestKey(Self->ProductionRaftRestSections);
            CSV_CUSTOM_STAT(RaftSimHull,RestKeySealedChecks,int32(SealedKey),ECsvCustomStatOp::Accumulate);
            CSV_CUSTOM_STAT(RaftSimHull,RestKeyReferenceChecks,int32(!SealedKey),ECsvCustomStatOp::Accumulate);
            CSV_CUSTOM_STAT(RaftSimHull,PreparedCacheHits,int32(Cached),ECsvCustomStatOp::Accumulate);
            CSV_CUSTOM_STAT(RaftSimHull,PreparedCacheMisses,int32(!Cached),ECsvCustomStatOp::Accumulate);
            if(Cached)
            {
                {
                    CSV_SCOPED_TIMING_STAT(RaftSimHull,PreparedSnapshotCopy);
                    Self->SharedHullPreparedSegments=Segments;Self->SharedHullPreparedCondition=C;
                    RaftSimHullPrepareCache::FCopyCounts Copies;
                    // Render sections reach ProductionRaftDeformedSections only via
                    // the commit swap, and every reader regenerates (and here
                    // re-validates) them first; topology/UVs are immutable. Only
                    // the physics hull must be copied on a hit.
                    static const bool bCopyPreparedSections=FParse::Param(FCommandLine::Get(),TEXT("RaftSimCopyCachedPreparedSections"));
                    if(bReferenceSnapshotCopy && !bCopyPreparedSections)
                    {Out=SnapshotCache->Hull;Copies.Assigned=3;}
                    else if(bReferenceSnapshotCopy)
                    {Self->SharedHullPreparedSections=SnapshotCache->Prepared;Out=SnapshotCache->Hull;Copies.Assigned=5*SnapshotCache->Prepared.Num()+3;}
                    else
                    {
                        RaftSimHullPrepareCache::CopyPreparedIfChanged(SnapshotCache->Prepared,Self->SharedHullPreparedSections,Copies);
                        RaftSimHullPrepareCache::CopyHullIfChanged(SnapshotCache->Hull,Out,Copies);
                    }
                    CSV_CUSTOM_STAT(RaftSimHull,PreparedArraysAssigned,Copies.Assigned,ECsvCustomStatOp::Accumulate);
                    CSV_CUSTOM_STAT(RaftSimHull,PreparedArraysRetained,Copies.Retained,ECsvCustomStatOp::Accumulate);
                }
                ++Self->SharedHullPrepareCount;
                // The adapter runs IsValid on this exact snapshot (Out is its
                // pending hull) immediately after we return; repeating the
                // full byte comparison here changed nothing but its cost.
                return true;
            }
            bool Valid=false;
            {
                CSV_SCOPED_TIMING_STAT(RaftSimHull,PreparedSnapshotDeformExport);
                Valid=Self->PrepareSharedHullGeometry(Segments,Out);
            }
            if(Valid)
            {
                CSV_SCOPED_TIMING_STAT(RaftSimHull,PreparedSnapshotRemember);
                SnapshotCache->Remember(Self->ProductionRaftRestSections,Self->TubeRadiusM,Segments,C,T,Self->SharedHullPreparedSections,Out);
            }
            return Valid;
        },
        [WeakThis](){if(auto* Self=WeakThis.Get())Self->CommitSharedHullGeometry();}))
    {
        UE_LOG(LogTemp,Error,TEXT("Shared hull review source initialization failed; raft disabled"));
        SetActorTickEnabled(false);return;
    }
    const auto& Hull=RaftAdapter->GetHullGeometry();
    UE_LOG(LogTemp,Display,TEXT("Shared hull fixed-step source ready: vertices=%d triangles=%d sections=%d; production original indexed collision/render surface"),
        Hull.VerticesM.Num(),Hull.Faces.Num(),Hull.Sections.Num());
}

bool ARaftSimRaftActor::PrepareSharedHullGeometry(
    const TArray<FRaftSimFlexVisualSegmentState>& Segments,FRaftSimHullGeometry& Out)
{
    CSV_SCOPED_TIMING_STAT(RaftSimHull,Prepare);
    if(!RaftVisual || !RaftAdapter || !bUsingProductionRaftRestMesh || GetActorScale3D()!=FVector::OneVector)return false;
    const double Started=FPlatformTime::Seconds();
    // Physics' current condition, not the actor's later render-frame update.
    // Permanent crease remains authored condition input, sampled on this clock.
    SharedHullPreparedSegments=Segments;
    SharedHullPreparedCondition={RaftAdapter->GetFlexiblePressureFraction(),RaftAdapter->GetFlexibleFabricIntegrity(),RaftCondition.PermanentCreaseAmplitudeM};
    RaftSimRaftMesh::DeformProductionRaftRestMesh(ProductionRaftRestSections->GetSections(),TubeRadiusM,SharedHullPreparedSegments,
        SharedHullPreparedCondition,SharedHullPreparedSections,&ProductionRaftDeformationCache,false);
    const bool Valid=RaftSimRaftMesh::ExportHullGeometry(SharedHullPreparedSections,RaftVisual->GetRelativeTransform(),Out);
    const double Ms=(FPlatformTime::Seconds()-Started)*1000.;
    SharedHullPrepareTotalMs+=Ms;SharedHullPrepareMaximumMs=FMath::Max(SharedHullPrepareMaximumMs,Ms);++SharedHullPrepareCount;
    return Valid;
}

void ARaftSimRaftActor::CommitSharedHullGeometry()
{
    // Called only when the adapter publishes the same successful body substep.
    // Reuse both buffers; failed prepares/contacts never replace visible geometry.
    Swap(ProductionRaftDeformedSections,SharedHullPreparedSections);
    Swap(SharedHullPublishedSegments,SharedHullPreparedSegments);
    SharedHullPublishedCondition=SharedHullPreparedCondition;
}

void ARaftSimRaftActor::UpdateSharedHullVisual()
{
    CSV_SCOPED_TIMING_STAT(RaftSimHull,Render);
    const uint64 Revision=RaftAdapter->GetHullGeometryRevision();
    if(Revision==0 || Revision==LastRenderedHullRevision)return;
    // Shading is needed once per rendered frame, not once per rigid substep.
    // Reconstruct it from the COMMITTED fixed-step inputs, never newer actor
    // condition or rejected D4 state. Exact vertex equality is checked below.
    const auto& Hull=RaftAdapter->GetHullGeometry();
    const auto Datum=RaftVisual->GetRelativeTransform();
    static const bool bReferenceRestKey=FParse::Param(FCommandLine::Get(),TEXT("RaftSimReferenceRestKey"));
    const bool Reuse=SharedHullRenderedCache && SharedHullRenderedCache->Matches(
        ProductionRaftRestSections,TubeRadiusM,SharedHullPublishedSegments,SharedHullPublishedCondition,Datum,bReferenceRestKey) &&
        SharedHullRenderedCache->Hull.VerticesM==Hull.VerticesM && SharedHullRenderedCache->Hull.Faces==Hull.Faces;
    if(Reuse)
    {
        static const bool bReferenceSnapshotCopy=!FParse::Param(FCommandLine::Get(),TEXT("RaftSimExactSnapshotCopy")) ||
            FParse::Param(FCommandLine::Get(),TEXT("RaftSimReferenceSnapshotCopy"));
        if(bReferenceSnapshotCopy)ProductionRaftDeformedSections=SharedHullRenderedCache->Prepared;
        else
        {
            RaftSimHullPrepareCache::FCopyCounts Copies;
            RaftSimHullPrepareCache::CopyPreparedIfChanged(SharedHullRenderedCache->Prepared,ProductionRaftDeformedSections,Copies);
        }
    }
    else RaftSimRaftMesh::DeformProductionRaftRestMesh(ProductionRaftRestSections->GetSections(),TubeRadiusM,SharedHullPublishedSegments,
        SharedHullPublishedCondition,ProductionRaftDeformedSections,&ProductionRaftDeformationCache);
    CSV_CUSTOM_STAT(RaftSimHull,ShadingUploads,int32(!Reuse),ECsvCustomStatOp::Set);
    bool Valid=Hull.Sections.Num()==ProductionRaftDeformedSections.Num();
    double MaximumErrorM=0.;
    for(int32 S=0;Valid && S<Hull.Sections.Num();++S)
    {
        const auto& Section=ProductionRaftDeformedSections[S];const auto& Range=Hull.Sections[S];
        Valid=Range.VertexCount==Section.Vertices.Num() && Range.FaceCount*3==Section.Triangles.Num();
        if(Valid)
        {
            // Every vertex is still checked with the same arithmetic; chunks
            // run in parallel and any failing vertex fails the revision.
            const FTransform VisualTransform=RaftVisual->GetRelativeTransform();
            constexpr int32 Chunk=2048;
            const int32 Chunks=FMath::DivideAndRoundUp(Range.VertexCount,Chunk);
            TArray<double,TInlineAllocator<32>> ChunkMaximum;ChunkMaximum.Init(0.,Chunks);
            TArray<uint8,TInlineAllocator<32>> ChunkValid;ChunkValid.Init(1,Chunks);
            ParallelFor(Chunks,[&](int32 C)
            {
                const int32 Last=FMath::Min(Range.VertexCount,(C+1)*Chunk);
                for(int32 V=C*Chunk;V<Last;++V)
                {
                    const FVector RenderM=VisualTransform.TransformPosition(Section.Vertices[V])*.01;
                    const double Error=(RenderM-Hull.VerticesM[Range.VertexStart+V]).Length();
                    ChunkMaximum[C]=FMath::Max(ChunkMaximum[C],Error);
                    if(!FMath::IsFinite(Error) || Error>1.e-12){ChunkValid[C]=0;return;}
                }
            },Chunks>1 ? EParallelForFlags::None : EParallelForFlags::ForceSingleThread);
            for(int32 C=0;C<Chunks;++C){MaximumErrorM=FMath::Max(MaximumErrorM,ChunkMaximum[C]);Valid&=ChunkValid[C]!=0;}
        }
        for(int32 F=0;Valid && F<Range.FaceCount;++F)
            Valid=Hull.Faces[Range.FaceStart+F]==FIntVector(Range.VertexStart+Section.Triangles[F*3],
                Range.VertexStart+Section.Triangles[F*3+1],Range.VertexStart+Section.Triangles[F*3+2]);
    }
    if(!Valid)
    {
        UE_LOG(LogTemp,Error,TEXT("Shared hull/render snapshot mismatch at revision %llu; max_error_m=%.17g"),Revision,MaximumErrorM);
        SetActorTickEnabled(false);return;
    }
    const TArray<FLinearColor> NoColors;const TArray<FVector2D> NoUVs;
    if(!Reuse){++CrewSupportGeometryRevision;++SharedHullShadingUploads;}
    for(int32 S=0;S<ProductionRaftDeformedSections.Num();++S)
    {
        const auto& Section=ProductionRaftDeformedSections[S];
        // Rigid actor motion needs no identical local-buffer reupload. Every
        // rest attribute, deformer input and exported face/vertex must match;
        // both published geometry and actual component buffers still undergo
        // the full equality checks on EVERY rendered revision below.
        if(!Reuse)RaftVisual->UpdateMeshSection_LinearColor(S,Section.Vertices,Section.Normals,NoUVs,NoColors,Section.Tangents);
        // Verify the component's actual submitted CPU buffers as well as the
        // producer input. This is not a GPU/WPO or rendered-pixel assertion.
        const auto* Submitted=RaftVisual->GetProcMeshSection(S);
        bool SubmittedMatches=Submitted && Submitted->ProcVertexBuffer.Num()==Section.Vertices.Num() &&
            Submitted->ProcIndexBuffer.Num()==Section.Triangles.Num();
        for(int32 V=0;SubmittedMatches && V<Section.Vertices.Num();++V)
            SubmittedMatches=Submitted->ProcVertexBuffer[V].Position==Section.Vertices[V];
        for(int32 I=0;SubmittedMatches && I<Section.Triangles.Num();++I)
            SubmittedMatches=Submitted->ProcIndexBuffer[I]==uint32(Section.Triangles[I]);
        if(!SubmittedMatches)
        {
            UE_LOG(LogTemp,Error,TEXT("Shared hull submitted component differs from committed source at revision %llu section=%d"),Revision,S);
            SetActorTickEnabled(false);return;
        }
    }
    if(!Reuse && SharedHullRenderedCache)SharedHullRenderedCache->Remember(ProductionRaftRestSections,TubeRadiusM,
        SharedHullPublishedSegments,SharedHullPublishedCondition,Datum,ProductionRaftDeformedSections,Hull);
    if(LastLoggedHullRevision==0 || Revision>=LastLoggedHullRevision+1200)
    {
        UE_LOG(LogTemp,Display,TEXT("Shared hull/render verified: revision=%llu vertices=%d triangles=%d max_error_m=%.17g prepares=%llu prepare_mean_ms=%.6f prepare_max_ms=%.6f"),
            Revision,Hull.VerticesM.Num(),Hull.Faces.Num(),MaximumErrorM,SharedHullPrepareCount,
            SharedHullPrepareTotalMs/double(SharedHullPrepareCount),SharedHullPrepareMaximumMs);
        LastLoggedHullRevision=Revision;
    }
    LastRenderedHullRevision=Revision;
}
