#include "RaftSimRaftActor.h"
#include "RaftSimRaftMesh.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "ProfilingDebugging/CsvProfiler.h"

CSV_DEFINE_CATEGORY(RaftSimHull,true);

void ARaftSimRaftActor::ConfigureSharedHullGeometryReview()
{
#if !UE_BUILD_SHIPPING
    if(!FParse::Param(FCommandLine::Get(),TEXT("RaftSimSharedHullReview")) &&
       !FParse::Param(FCommandLine::Get(),TEXT("RaftSimFullHullGroundReview")))return;
    bSharedHullGeometryReview=true;
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
    if(!RaftAdapter->SetHullGeometryProvider(
        [WeakThis](const TArray<FRaftSimFlexVisualSegmentState>& Segments,FRaftSimHullGeometry& Out)
        {auto* Self=WeakThis.Get();return Self && Self->PrepareSharedHullGeometry(Segments,Out);},
        [WeakThis](){if(auto* Self=WeakThis.Get())Self->CommitSharedHullGeometry();}))
    {
        UE_LOG(LogTemp,Error,TEXT("Shared hull review source initialization failed; raft disabled"));
        SetActorTickEnabled(false);return;
    }
    const auto& Hull=RaftAdapter->GetHullGeometry();
    UE_LOG(LogTemp,Display,TEXT("Shared hull fixed-step source ready: vertices=%d triangles=%d sections=%d; original indexed surface, no full-surface contact promotion"),
        Hull.VerticesM.Num(),Hull.Faces.Num(),Hull.Sections.Num());
#endif
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
    RaftSimRaftMesh::DeformProductionRaftRestMesh(ProductionRaftRestSections,TubeRadiusM,SharedHullPublishedSegments,
        SharedHullPublishedCondition,ProductionRaftDeformedSections,&ProductionRaftDeformationCache);
    const auto& Hull=RaftAdapter->GetHullGeometry();
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
    for(int32 S=0;S<ProductionRaftDeformedSections.Num();++S)
    {
        const auto& Section=ProductionRaftDeformedSections[S];
        RaftVisual->UpdateMeshSection_LinearColor(S,Section.Vertices,Section.Normals,NoUVs,NoColors,Section.Tangents);
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
    if(LastLoggedHullRevision==0 || Revision>=LastLoggedHullRevision+1200)
    {
        UE_LOG(LogTemp,Display,TEXT("Shared hull/render verified: revision=%llu vertices=%d triangles=%d max_error_m=%.17g prepares=%llu prepare_mean_ms=%.6f prepare_max_ms=%.6f"),
            Revision,Hull.VerticesM.Num(),Hull.Faces.Num(),MaximumErrorM,SharedHullPrepareCount,
            SharedHullPrepareTotalMs/double(SharedHullPrepareCount),SharedHullPrepareMaximumMs);
        LastLoggedHullRevision=Revision;
    }
    LastRenderedHullRevision=Revision;
}
