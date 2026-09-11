#pragma once
#include "RaftSimLiquidParticleRoutingGPU.h"

// Read-only classification against PHYSICAL parent faces. Caller supplies rows
// from the validated exterior profile: west/east (NY each), south/north (NX).
// Each row is (absolute bed Z cm, stage Z cm, inward normal speed cm/s).
// Only a wet outgoing pressure-stage row (normal speed < 0) permits retirement.
struct FRaftSimLiquidFaceBed
{
    TArray<FVector2f> Knots; // tangent cm, absolute bed Z cm
    FIntVector4 Offsets=FIntVector4(0,0,0,0),Counts=FIntVector4(0,0,0,0);
};
struct FRaftSimLiquidParticleExitPlan
{
    FRaftSimLiquidParticleRoutePlan Routing;
    FRDGBufferRef FaceRows=nullptr;
    float HeightCm=0;
    FRDGBufferRef BedKnots=nullptr;
    FIntVector4 BedOffsets=FIntVector4(0,0,0,0),BedCounts=FIntVector4(0,0,0,0);
};
RAFTSIMWATERDETAIL_API FRaftSimLiquidParticleExitPlan RaftSimBuildLiquidParticleExitPlan(
    FRDGBuilder& Graph,const FRaftSimLiquidParticleRoutePlan& Routing,float HeightCm,
    TConstArrayView<FVector3f> BedStageNormalSpeed,FString& Error,
    const FRaftSimLiquidFaceBed* ExactBed=nullptr);

// Records uint4: status, face, profile row, float32 crossing fraction bits.
// Status: 0 unused, 1 remains inside, 2 approved outlet candidate,
// 4 forbidden/ambiguous exterior crossing, 8 invalid segment/route.
// Counts: inside, west/east/south/north approved, rejected, invalid, source live.
// All original native words remain in the source packet. This function does NOT
// delete particles or authorize a partial commit; an atomic exit ledger is still
// required together with the destination assembly and survivor transaction.
RAFTSIMWATERDETAIL_API FRaftSimLiquidParticleExitCandidates RaftSimClassifyLiquidParticleExits(
    FRDGBuilder& Graph,const FRaftSimLiquidParticleExitPlan& Plan,
    const FRaftSimLiquidParticleRoutePacket& Packet,uint32 SourceOwner,
    uint32 PositionOffset,uint32 StepStartOffset,float ParticleVolumeM3,FString& Error);
