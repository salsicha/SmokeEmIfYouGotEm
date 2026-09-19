#pragma once

#include "CoreMinimal.h"
#include "ProceduralMeshComponent.h"
#include "RaftSimSurfaceRefinement.h"
#include "RaftSimCrestHistory.h"
#include "RaftSimIncrementalCrestHistory.h"
#include "RaftSimCrestMidpointExpansion.h"
#include "RaftSimCrestNormals.h"
#include "RaftSimCrestProfilePrefetch.h"

struct FRaftSimShorelineCrestInput
{
    TConstArrayView<float> SourceCrestCm;
    TConstArrayView<float> SourceShoreWeight;
    TArray<double> ProfileKey;
    TArray<FBox2D> NonzeroRegionsCm;
    TFunction<float(const FVector2D&)> HeightAtWorldXYCm;
    // Allocated only for the explicit actual-input empty-tile comparison.
    TFunction<float(const FVector2D&)> EmptyTileComparisonHeight[2];
    TFunction<float(const FBox2D&)> HeightRangeWidthAtWorldXYCm;
    TFunction<float(const FBox2D&)> PreparedHeightRangeWidthAtWorldXYCm;
    TFunction<float(const FBox2D&)> TightHeightRangeWidthAtWorldXYCm;
    double PreparedRangeConstructionMs=0.;
    float BlendAlpha=1.f;
    FBox2D DetailWindowCm=FBox2D(ForceInit);
    float DetailSpanCm=0;
};

// Refines only already-clipped wet triangles. Source vertices and boundary
// segments are immutable; added vertices recover the shared continuous crest.
class RAFTSIMRAFT_API FRaftSimShorelineCrests
{
public:
    bool Update(const TArray<FProcMeshVertex>& Source,const TArray<uint32>& SourceIndices,
        const TArray<int32>& SourceCellOffsets,const TArray<float>& CoarseCrestCm,
        const TArray<float>& Shore,const FRaftSimShorelineCrestInput& Input,
        TArray<FProcMeshVertex>& Vertices,TArray<uint32>& Indices,TArray<int32>& CellOffsets);
    void Reset();
    void PrefetchProfile(const FRaftSimShorelineCrestInput& Input);
    const TArray<float>& GetTargetCorrectionsCm() const { return TargetCorrectionsCm; }
    const TArray<float>& GetRenderedCorrectionsCm() const { return RenderedCorrectionsCm; }
    const TArray<float>& GetExpandedCoarseCrestCm() const { return ExpandedCoarseCrestCm; }
    const TArray<float>& GetExpandedShore() const { return ExpandedShore; }
    uint64 GetBuildCount() const { return BuildCount; }
private:
    FRaftSimSurfaceRefinement Refinement;
    FRaftSimCrestProfilePrefetch ProfilePrefetch;
    TArray<FVector2D> CachedXY;
    TArray<uint32> CachedIndices;
    TArray<double> CachedProfile;
    TArray<float> CachedCoarse,CachedShore;
    TArray<float> FineProfileCm;
    FBox2D CachedDetailWindowCm=FBox2D(ForceInit);
    float CachedDetailSpanCm=0;
    TArray<uint8> BoundaryMidpoints;
    TArray<float> TargetCorrectionsCm,RenderedCorrectionsCm,ExpandedCoarseCrestCm,ExpandedShore;
    FRaftSimCrestHistory CorrectionHistory;
    FRaftSimCrestHistory ParallelCorrectionHistory;
    TArray<float> ParallelHistoryRendered;
    // Allocated only by the explicit actual-input hash comparison audit.
    FRaftSimFastCrestHistory CandidateCorrectionHistory;
    FRaftSimIncrementalCrestHistory IncrementalCorrectionHistory;
    // Exact topology-only dependency schedule; no cached evolving attributes.
    FRaftSimCrestMidpointExpansion MidpointExpansion;
    FRaftSimCrestNormals ParallelNormals;
    uint64 BuildCount=0;
};
