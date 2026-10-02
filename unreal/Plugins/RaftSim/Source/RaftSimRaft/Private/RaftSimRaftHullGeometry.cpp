#include "RaftSimRaftActor.h"
#include "RaftSimRaftMesh.h"
#include "RaftSimHullPrepareCache.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "ProfilingDebugging/CsvProfiler.h"

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
    const bool Bound=Runtime->SetHullGeometryProvider(
        [WeakThis,SnapshotCache,bCacheExactShape](const TArray<FRaftSimFlexVisualSegmentState>& Segments,FRaftSimHullGeometry& Out)
        {
            auto* Self=WeakThis.Get();if(!Self || !Self->RaftVisual || !Self->RaftAdapter)return false;
            const double Started=FPlatformTime::Seconds();
            const RaftSimRaftMesh::FRaftSimRaftVisualCondition C={Self->RaftAdapter->GetFlexiblePressureFraction(),
                Self->RaftAdapter->GetFlexibleFabricIntegrity(),Self->RaftCondition.PermanentCreaseAmplitudeM};
            const auto T=Self->RaftVisual->GetRelativeTransform();
            if(bCacheExactShape && Self->bUsingProductionRaftRestMesh && Self->GetActorScale3D()==FVector::OneVector &&
                SnapshotCache->Matches(Self->ProductionRaftRestSections,Self->TubeRadiusM,Segments,C,T))
            {
                Self->SharedHullPreparedSegments=Segments;Self->SharedHullPreparedCondition=C;
                Self->SharedHullPreparedSections=SnapshotCache->Prepared;Out=SnapshotCache->Hull;
                const double Ms=(FPlatformTime::Seconds()-Started)*1000.;++Self->SharedHullPrepareCount;
                Self->SharedHullPrepareTotalMs+=Ms;Self->SharedHullPrepareMaximumMs=FMath::Max(Self->SharedHullPrepareMaximumMs,Ms);
                return Out.IsValid();
            }
            const bool Valid=Self->PrepareSharedHullGeometry(Segments,Out);
            if(Valid && bCacheExactShape)SnapshotCache->Remember(Self->ProductionRaftRestSections,Self->TubeRadiusM,Segments,C,T,Self->SharedHullPreparedSections,Out);
            return Valid;
        },
        [WeakThis](){if(auto* Self=WeakThis.Get())Self->CommitSharedHullGeometry();});
    if(!Bound)UE_LOG(LogTemp,Error,TEXT("Isolated production hull export refused: rest_sections=%d visual=%d"),ProductionRaftRestSections.Num(),int32(RaftVisual!=nullptr));
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
    if(!RaftAdapter->SetHullGeometryProvider(
        [WeakThis,SnapshotCache](const TArray<FRaftSimFlexVisualSegmentState>& Segments,FRaftSimHullGeometry& Out)
        {
            auto* Self=WeakThis.Get();if(!Self || !Self->RaftAdapter || !Self->RaftVisual)return false;
            const RaftSimRaftMesh::FRaftSimRaftVisualCondition C={Self->RaftAdapter->GetFlexiblePressureFraction(),
                Self->RaftAdapter->GetFlexibleFabricIntegrity(),Self->RaftCondition.PermanentCreaseAmplitudeM};
            const auto T=Self->RaftVisual->GetRelativeTransform();
            if(SnapshotCache->Matches(Self->ProductionRaftRestSections,Self->TubeRadiusM,Segments,C,T))
            {
                Self->SharedHullPreparedSegments=Segments;Self->SharedHullPreparedCondition=C;
                Self->SharedHullPreparedSections=SnapshotCache->Prepared;Out=SnapshotCache->Hull;
                ++Self->SharedHullPrepareCount;return Out.IsValid();
            }
            const bool Valid=Self->PrepareSharedHullGeometry(Segments,Out);
            if(Valid)SnapshotCache->Remember(Self->ProductionRaftRestSections,Self->TubeRadiusM,Segments,C,T,Self->SharedHullPreparedSections,Out);
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
    RaftSimRaftMesh::DeformProductionRaftRestMesh(ProductionRaftRestSections,TubeRadiusM,SharedHullPreparedSegments,
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
    const bool Reuse=SharedHullRenderedCache && SharedHullRenderedCache->Matches(
        ProductionRaftRestSections,TubeRadiusM,SharedHullPublishedSegments,SharedHullPublishedCondition,Datum) &&
        SharedHullRenderedCache->Hull.VerticesM==Hull.VerticesM && SharedHullRenderedCache->Hull.Faces==Hull.Faces;
    if(Reuse)ProductionRaftDeformedSections=SharedHullRenderedCache->Prepared;
    else RaftSimRaftMesh::DeformProductionRaftRestMesh(ProductionRaftRestSections,TubeRadiusM,SharedHullPublishedSegments,
        SharedHullPublishedCondition,ProductionRaftDeformedSections,&ProductionRaftDeformationCache);
    CSV_CUSTOM_STAT(RaftSimHull,ShadingUploads,int32(!Reuse),ECsvCustomStatOp::Set);
    bool Valid=Hull.Sections.Num()==ProductionRaftDeformedSections.Num();
    double MaximumErrorM=0.;
    for(int32 S=0;Valid && S<Hull.Sections.Num();++S)
    {
        const auto& Section=ProductionRaftDeformedSections[S];const auto& Range=Hull.Sections[S];
        Valid=Range.VertexCount==Section.Vertices.Num() && Range.FaceCount*3==Section.Triangles.Num();
        for(int32 V=0;Valid && V<Range.VertexCount;++V)
        {
            const FVector RenderM=RaftVisual->GetRelativeTransform().TransformPosition(Section.Vertices[V])*.01;
            const double Error=(RenderM-Hull.VerticesM[Range.VertexStart+V]).Length();
            MaximumErrorM=FMath::Max(MaximumErrorM,Error);Valid=FMath::IsFinite(Error) && Error<=1.e-12;
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
