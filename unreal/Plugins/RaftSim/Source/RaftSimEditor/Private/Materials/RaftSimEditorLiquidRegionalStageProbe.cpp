#include "RaftSimLiquidRegionalState.h"
#include "RaftSimLiquidStageInterface.h"
#include "RaftSimLiquidHaloGPU.h"
#include "RaftSimLiquidTransferGPU.h"
#include "RaftSimLiquidRegionalContact.h"
#include "RaftSimLiquidRegionalProjection.h"
#include "RaftSimLiquidParentExterior.h"
#include "RaftSimLiquidFaceBedProfile.h"
#include "RaftSimLiquidStageJournal.h"
#include "RaftSimLiquidDataset.h"
#include "NiagaraDataInterfaceGrid3DCollection.h"
#include "RenderGraphBuilder.h"
#include "NiagaraComponent.h"
#include "NiagaraSystem.h"
#include "NiagaraScript.h"
#include "NiagaraEmitterInstance.h"
#include "NiagaraEmitterHandle.h"
#include "NiagaraSystemInstanceController.h"
#include "NiagaraComputeExecutionContext.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "HAL/IConsoleManager.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/ScopeExit.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Serialization/JsonSerializer.h"
#include "RenderingThread.h"
#include "UObject/StrongObjectPtr.h"
#include "RenderTargetPool.h"
#include "RHICommandList.h"
#include "RenderGraphUtils.h"
#include "RHIGPUReadback.h"
#include "RaftSimLiquidNativeTransferAudit.h"
#include "RaftSimLiquidProjectionPacket.h"
#include "RaftSimLiquidAdvectionPacket.h"
#include "RaftSimLiquidInterfaceRuntime.h"
#include "RaftSimLiquidParticleAssemblyAudit.h"
#include "RaftSimLiquidNativeParticleHandoff.h"
#include "NiagaraDataInterfaceArrayImpl.h"

BEGIN_SHADER_PARAMETER_STRUCT(FRaftSimRegionalMarkerCopy,)
    RDG_TEXTURE_ACCESS(Texture,ERHIAccess::CopySrc)
END_SHADER_PARAMETER_STRUCT()

struct FRaftSimRegionalProbeGraph
{
    FRaftSimLiquidHaloPlan Halo;
    FRaftSimLiquidTransferPlan Transfer;
    FRaftSimLiquidInterfaceGraph Interface;
};
RDG_REGISTER_BLACKBOARD_STRUCT(FRaftSimRegionalProbeGraph);

namespace
{
struct FMarkerSlice
{
    int32 Owner=0,Z=0;
    TUniquePtr<FRHIGPUTextureReadback> Readback;
};
struct FStageProbe
{
    FRaftSimLiquidDataset Dataset;
    UWorld* World=nullptr;
    TArray<TStrongObjectPtr<UNiagaraComponent>> Components;
    TArray<uint64> Systems;
    TArray<FNiagaraComputeExecutionContext*> Contexts;
    TArray<FNiagaraDataInterfaceProxyNeighborQuery*> Neighbors;
    uint32 NeighborViewRefreshes=0;
    TArray<FNiagaraDataInterfaceProxyGrid3DCollectionProxy*> Pressure;
    TArray<FNiagaraDataInterfaceProxyGrid3DCollectionProxy*> Boundary;
    TArray<FNiagaraDataInterfaceProxyGrid3DCollectionProxy*> RawTransfer,Velocity,Support;
    TArray<FIntVector> Sizes;
    TArray<int32> RegionIds;
    TArray<FRaftSimLiquidHaloColumn> Copies;
    TArray<TSharedPtr<FJsonValue>> Groups;
    FRaftSimLiquidStageJournal Journal;
    FDelegateHandle Handle,SurfaceHandle;
    uint32 Incomplete=0,Misaligned=0,Complete=0,PressureGroups=0,FirstGroups=0;
    uint32 Exchanges=0;
    uint32 BoundaryExchanges=0;
    uint32 AdvectionVelocityExchanges=0;
    FString ExchangeError;
    bool ContactInstalled=false;
    bool ProjectionInstalled=false;
    TArray<double> PressureOmegas;
    bool BoundaryExchange=false;
    bool ParentExterior=false;
    bool TransferEnabled=false;
    uint32 TransferReductions=0;
    bool PacketRequested=false,PacketCaptured=false;
    bool ProjectionPacketRequested=false;
    TArray<FRaftSimLiquidProjectionPacket> ProjectionPackets;
    bool AdvectionPacketRequested=false;
    TArray<FRaftSimLiquidAdvectionPacket> AdvectionPackets;
    TArray<FIntVector> AdvectionMatrixOffsets;
    bool InterfaceRequested=false;
    FRaftSimLiquidInterfaceRuntime Interface;
    int32 PacketStep=1;
    int32 PacketPerOwner=1;
    double PacketSpeed=1;
    bool RouteRequested=false;
    bool AssemblyRequested=false;
    bool HandlesRequested=false;
    bool HandoffRequested=false;
    bool RetirementRequested=false;
    bool CompactHandoff=false;
    bool DenseRequested=false;
    bool FixedSourceSeed=false;
    int32 SourceSeed=0;
    TArray<int32> BoundSourceSeeds;
    TArray<FVector3f> BoundSourceScales;
    int32 FullAuditStep=0;
    bool ExactExitBed=false;
    TRefCountPtr<FRDGPooledBuffer> FirstExitRejection;
    TArray<uint32> RegionalReservations;
    TArray<double> PreparedSpawnRates;
    RaftSimLiquidParentExterior::FProfile RetirementProfile;
    bool EmptyReceiver=false;
    bool EmissionRequested=false,EmissionActivated=false;
    uint32 EmissionStartStep=0;
    uint32 Reservation=16;
    bool ReservationReady=false;
    IConsoleVariable* EarlyFreeVariable=nullptr;
    int32 PreviousEarlyFree=0;
    FDelegateHandle ReservationHandle;
    int32 HandoffCount=1;
    TArray<FRaftSimNativeParticleHandoff> Handoffs;
    FRaftSimLiquidLifetime Lifetime;
    FRaftSimLiquidTickToken TickToken;
    FRaftSimNativeAssemblySample Assembly;
    TArray<FIntRect> RouteRegions;
    FIntPoint RouteParentCells;
    FVector RouteLower,RouteAxisX,RouteAxisY;
    FVector2D RouteSpacing;
    FNiagaraGpuComputeDispatchInterface* Dispatch=nullptr;
    TArray<FRaftSimNativeTransferSample> Packet;
    bool MarkerRequested=false,MarkerSeeded=false,MarkerCaptured=false;
    TArray<FMarkerSlice> MarkerSlices;
};
TSharedPtr<FStageProbe,ESPMode::ThreadSafe> Probe;

TSharedPtr<FJsonObject> ReadProbeJson(const FString& Path)
{
    FString Text;TSharedPtr<FJsonObject> J;
    if (FFileHelper::LoadFileToString(Text,*Path)) FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),J);
    return J;
}
void StopProbe()
{
    if (!Probe) return;
    auto State=Probe;
    ENQUEUE_RENDER_COMMAND(RaftSimStopRegionalStageProbe)([State](FRHICommandListImmediate&)
    {
        URaftSimLiquidStageInterface::PostGroupEvent().Remove(State->Handle);State->Handle.Reset();
        URaftSimLiquidStageInterface::SurfaceBindingEvent().Remove(State->SurfaceHandle);State->SurfaceHandle.Reset();
        if (State->Dispatch && State->ReservationHandle.IsValid())
            State->Dispatch->GetOnPreInitViewsEvent().Remove(State->ReservationHandle);
        State->ReservationHandle.Reset();
    });
    FlushRenderingCommands();
    for (auto& C:State->Components) if (C.IsValid())
    { C->DeactivateImmediate();if (auto* Actor=C->GetOwner()) Actor->Destroy(); }
    if (State->EarlyFreeVariable)
    {
        State->EarlyFreeVariable->SetWithCurrentPriority(State->PreviousEarlyFree);
        State->EarlyFreeVariable=nullptr;
    }
    State->Components.Empty();Probe.Reset();
}
FDelegateHandle ProbeCleanup=FWorldDelegates::OnWorldCleanup.AddLambda([](UWorld* World,bool,bool)
{ if (Probe && Probe->World==World) StopProbe(); });

FAutoConsoleCommandWithWorldAndArgs StageProbe(TEXT("RaftSim.LiquidRegionalStageProbe"),
    TEXT("start [all] | stop new-report.json. Unsaved scheduler/exchange probe; optional four-particle transfer snapshot, never fluid acceptance."),
    FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args,UWorld* World)
    {
        if ((Args.Num()==1 || (Args.Num()==2 && Args[1]==TEXT("all"))) && Args[0]==TEXT("start") && !Probe)
        {
            using namespace RaftSimLiquidRegionalState;
            const FString Base=FPaths::ProjectDir()/TEXT("../tmp");
            FString DatasetKey=TEXT("core-v1"),Error;FRaftSimLiquidDataset Dataset;
            FParse::Value(FCommandLine::Get(),TEXT("RaftSimRegionalDataset="),DatasetKey);
            if(!FRaftSimLiquidDataset::Load(Base,DatasetKey,Dataset,Error))
            { UE_LOG(LogTemp,Error,TEXT("Stage probe dataset: %s"),*Error);return; }
            const FString Directory=Dataset.Regions;
            const auto Manifest=ReadProbeJson(Directory/TEXT("manifest.json"));
            const auto Boundary=ReadProbeJson(Dataset.Parent/TEXT("grid_boundary_profile.json"));
            FParent Parent;
            if (!DecodeParent(Manifest,Boundary,Parent,Error)) { UE_LOG(LogTemp,Error,TEXT("Stage probe parent: %s"),*Error);return; }
            auto* Source=LoadObject<UNiagaraSystem>(nullptr,TEXT("/Game/RaftSim/VFX/Water/LiquidBodyReview/NS_SouthForkLiquidTerrainReview.NS_SouthForkLiquidTerrainReview"));
            if (!Source) return;
            auto State=MakeShared<FStageProbe,ESPMode::ThreadSafe>();State->World=World;State->Dataset=Dataset;
            State->ContactInstalled=FParse::Param(FCommandLine::Get(),TEXT("RaftSimRegionalContact"));
            State->ProjectionInstalled=FParse::Param(FCommandLine::Get(),TEXT("RaftSimRegionalProjection"));
            State->BoundaryExchange=FParse::Param(FCommandLine::Get(),TEXT("RaftSimRegionalBoundaryExchange"));
            if (State->BoundaryExchange && !State->ProjectionInstalled)
            { UE_LOG(LogTemp,Error,TEXT("Shared boundary exchange requires regional contact/projection"));return; }
            State->MarkerRequested=FParse::Param(FCommandLine::Get(),TEXT("RaftSimRegionalPressureMarker"));
            if (State->MarkerRequested && !State->ProjectionInstalled)
            { UE_LOG(LogTemp,Error,TEXT("Pressure marker requires regional projection"));return; }
            if (State->ProjectionInstalled && !State->ContactInstalled)
            { UE_LOG(LogTemp,Error,TEXT("Regional projection probe requires canonical contact"));return; }
            State->ParentExterior=FParse::Param(FCommandLine::Get(),TEXT("RaftSimRegionalParentExterior"));
            State->TransferEnabled=FParse::Param(FCommandLine::Get(),TEXT("RaftSimRegionalTransfer"));
            State->PacketRequested=FParse::Param(FCommandLine::Get(),TEXT("RaftSimRegionalTransferPacket"));
            State->ProjectionPacketRequested=FParse::Param(FCommandLine::Get(),TEXT("RaftSimRegionalProjectionPacket"));
            if(State->ProjectionPacketRequested && (!State->PacketRequested || !State->TransferEnabled || !State->BoundaryExchange || !State->ProjectionInstalled))
            { UE_LOG(LogTemp,Error,TEXT("Same-step projection packet requires transfer packet and exchanged regional projection"));return; }
            State->RouteRequested=FParse::Param(FCommandLine::Get(),TEXT("RaftSimRegionalParticleRoutes"));
            State->AdvectionPacketRequested=FParse::Param(FCommandLine::Get(),TEXT("RaftSimRegionalAdvectionPacket"));
            if(FParse::Param(FCommandLine::Get(),TEXT("RaftSimRegionalCompatibleTransport")) && !State->AdvectionPacketRequested)
            { UE_LOG(LogTemp,Error,TEXT("Compatible transport requires paired native advection validation"));return; }
            if(State->AdvectionPacketRequested && (!State->ProjectionPacketRequested || !State->RouteRequested || !State->ParentExterior))
            { UE_LOG(LogTemp,Error,TEXT("Advection packet requires paired projection, particle routes and parent contact outputs"));return; }
            State->AssemblyRequested=FParse::Param(FCommandLine::Get(),TEXT("RaftSimRegionalParticleAssembly"));
            State->HandlesRequested=FParse::Param(FCommandLine::Get(),TEXT("RaftSimRegionalParticleHandles"));
            State->HandoffRequested=FParse::Param(FCommandLine::Get(),TEXT("RaftSimRegionalParticleHandoff"));
            State->RetirementRequested=FParse::Param(FCommandLine::Get(),TEXT("RaftSimRegionalParticleRetirement"));
            State->CompactHandoff=FParse::Param(FCommandLine::Get(),TEXT("RaftSimRegionalCompactHandoff"));
            State->DenseRequested=FParse::Param(FCommandLine::Get(),TEXT("RaftSimRegionalDense"));
            State->InterfaceRequested=FParse::Param(FCommandLine::Get(),TEXT("RaftSimRegionalInterfaceTransport"));
            State->Interface.PressureCoupled=FParse::Param(FCommandLine::Get(),TEXT("RaftSimRegionalInterfacePressure"));
            State->Interface.CompactTransport=FParse::Param(FCommandLine::Get(),TEXT("RaftSimRegionalUnifiedTransport"));
            State->Interface.HighOrder=FParse::Param(FCommandLine::Get(),TEXT("RaftSimRegionalHighOrderInterface"));
            if(State->Interface.HighOrder && !State->Interface.CompactTransport)
            { UE_LOG(LogTemp,Error,TEXT("High-order interface requires current unified native transport"));return; }
            if(State->Interface.CompactTransport && (!State->InterfaceRequested || !State->Interface.PressureCoupled ||
                !State->AdvectionPacketRequested || !FParse::Param(FCommandLine::Get(),TEXT("RaftSimRegionalCompatibleTransport"))))
            { UE_LOG(LogTemp,Error,TEXT("Unified transport requires coupled interface, compatible particles and paired motion capture"));return; }
            if(State->Interface.PressureCoupled && !State->InterfaceRequested)
            { UE_LOG(LogTemp,Error,TEXT("Current surface pressure requires continuous interface transport"));return; }
            if(State->InterfaceRequested && (!State->DenseRequested || !State->ProjectionPacketRequested || !State->ParentExterior))
            { UE_LOG(LogTemp,Error,TEXT("Live interface requires dense native flow, paired projection and parent exterior"));return; }
            State->FixedSourceSeed=FParse::Value(FCommandLine::Get(),TEXT("RaftSimRegionalSourceSeed="),State->SourceSeed);
            if(State->FixedSourceSeed && (!State->DenseRequested || State->SourceSeed<0 || State->SourceSeed>1000000))
            { UE_LOG(LogTemp,Error,TEXT("Fixed-source diagnostic seed requires dense mode and 0..1000000"));return; }
            if(State->CompactHandoff && !State->HandoffRequested)
            { UE_LOG(LogTemp,Error,TEXT("Compact telemetry requires native handoff"));return; }
            if(State->RetirementRequested && !State->HandoffRequested)
            { UE_LOG(LogTemp,Error,TEXT("Native retirement requires full-state handoff and an exit ledger"));return; }
            State->EmptyReceiver=FParse::Param(FCommandLine::Get(),TEXT("RaftSimRegionalEmptyReceiver"));
            State->EmissionRequested=FParse::Param(FCommandLine::Get(),TEXT("RaftSimRegionalEmission"));
            if (State->EmissionRequested && (!State->HandoffRequested || !State->EmptyReceiver))
            { UE_LOG(LogTemp,Error,TEXT("Emission replay requires handoff and an initially empty receiver"));return; }
            if (State->EmissionRequested) State->Reservation=64;
            if(State->DenseRequested && (!State->PacketRequested || !State->HandoffRequested || !State->RetirementRequested ||
                !State->CompactHandoff || !State->ParentExterior || State->EmptyReceiver || State->EmissionRequested || Args.Num()!=2))
            { UE_LOG(LogTemp,Error,TEXT("Dense water requires all physical owners, compact handoff, native exits and parent forcing; no authored corner/source fixtures"));return; }
            if (State->EmptyReceiver && !State->HandoffRequested)
            { UE_LOG(LogTemp,Error,TEXT("Empty receiver requires native handoff"));return; }
            FParse::Value(FCommandLine::Get(),TEXT("RaftSimRegionalHandoffCount="),State->HandoffCount);
            // Dense history is 304 bytes/commit plus a bounded lossless stage
            // journal. Full dense payloads remain limited to one diagnostic step.
            const int32 MaxCommits=State->DenseRequested?3598:(State->RetirementRequested?10:8);
            if (State->HandoffCount<1 || State->HandoffCount>MaxCommits || (!State->HandoffRequested && State->HandoffCount!=1))
            { UE_LOG(LogTemp,Error,TEXT("Native handoff replay exceeds its mode-specific retained history budget"));return; }
            // Extraction retains pointers into these objects until graph execution.
            // Allocate the entire history once; never relocate pending snapshots.
            State->Handoffs.SetNum(State->HandoffCount);
            FParse::Value(FCommandLine::Get(),TEXT("RaftSimRegionalFullAuditStep="),State->FullAuditStep);
            if (State->FullAuditStep && (!State->DenseRequested || State->FullAuditStep<2 || State->FullAuditStep>State->HandoffCount+1))
            { UE_LOG(LogTemp,Error,TEXT("One full diagnostic step must be inside the dense compact handoff interval"));return; }
            if (State->HandoffRequested && (!State->RouteRequested || State->AssemblyRequested || State->HandlesRequested))
            { UE_LOG(LogTemp,Error,TEXT("Live handoff requires routing; standalone assembly/handle captures must be off"));return; }
            if (State->HandlesRequested && !State->AssemblyRequested)
            { UE_LOG(LogTemp,Error,TEXT("Persistent handle preparation requires native receiving assembly"));return; }
            if (State->AssemblyRequested && !State->RouteRequested)
            { UE_LOG(LogTemp,Error,TEXT("Receiving assembly requires native particle routing"));return; }
            FParse::Value(FCommandLine::Get(),TEXT("RaftSimRegionalTransferPacketSpeed="),State->PacketSpeed);
            if (!FMath::IsFinite(State->PacketSpeed) || State->PacketSpeed<1 || State->PacketSpeed>8 ||
                (!State->PacketRequested && (State->RouteRequested || State->PacketSpeed!=1)))
            { UE_LOG(LogTemp,Error,TEXT("Particle routing/speed probe requires a bounded native packet"));return; }
            State->RouteParentCells=FIntPoint(Parent.Cells.X,Parent.Cells.Y);
            State->RouteLower=FCanonicalFrame::WorldPosition(Parent.Frame.AxisX*(Parent.Lower.X*100)+Parent.Frame.AxisY*(Parent.Lower.Y*100)+FVector(0,0,Parent.Frame.Origin.Z));
            State->RouteAxisX=FCanonicalFrame::WorldVector(Parent.Frame.AxisX);State->RouteAxisY=FCanonicalFrame::WorldVector(Parent.Frame.AxisY);
            State->RouteSpacing=FVector2D(Parent.Spacing.X,Parent.Spacing.Y);
            FParse::Value(FCommandLine::Get(),TEXT("RaftSimRegionalTransferPacketStep="),State->PacketStep);
            FParse::Value(FCommandLine::Get(),TEXT("RaftSimRegionalTransferPacketPerOwner="),State->PacketPerOwner);
            if (State->PacketPerOwner<1 || State->PacketPerOwner>4 || (!State->PacketRequested && State->PacketPerOwner!=1))
            { UE_LOG(LogTemp,Error,TEXT("Native corner packet requires 1..4 particles per selected owner"));return; }
            if (State->PacketStep<1 || State->PacketStep>(State->DenseRequested?3600:12) || (!State->PacketRequested && State->PacketStep!=1))
            { UE_LOG(LogTemp,Error,TEXT("Packet step exceeds the bounded native replay (3600 dense, 12 small)"));return; }
            // A continuous outlet replay commits every completed advection up to
            // the retained next-step P2G snapshot. Its repeated before/after
            // history proves subsequent native motion without disabling handoff
            // for a final moving frame, which would strand new source particles.
            if(State->RetirementRequested && (State->HandoffCount<3 || State->PacketStep!=State->HandoffCount+2))
            { UE_LOG(LogTemp,Error,TEXT("Outlet replay requires at least 3 commits through the step preceding retained P2G"));return; }
            if (State->HandoffRequested && !State->RetirementRequested && State->PacketStep<State->HandoffCount+3)
            { UE_LOG(LogTemp,Error,TEXT("Live handoff must observe completed native motion after the final commit"));return; }
            if (State->PacketRequested && (!State->TransferEnabled || (State->ParentExterior && !State->DenseRequested) || State->MarkerRequested))
            { UE_LOG(LogTemp,Error,TEXT("Native packet requires transfer and no exterior forcing/synthetic pressure marker"));return; }
            if (State->PacketRequested) State->Dispatch=FNiagaraGpuComputeDispatchInterface::Get(World);
            if (State->TransferEnabled && (!State->BoundaryExchange || Args.Num()!=2))
            { UE_LOG(LogTemp,Error,TEXT("Regional transfer requires all canonical contact/projection/boundary owners"));return; }
            if (State->ParentExterior && (!State->BoundaryExchange || State->MarkerRequested || Args.Num()!=2))
            { UE_LOG(LogTemp,Error,TEXT("Parent exterior requires all regional boundary owners and no synthetic pressure marker"));return; }
            RaftSimLiquidParentExterior::FProfile Exterior;
            if (State->ParentExterior || State->RetirementRequested)
            {
                TArray<FState> All;
                for (int32 Id=0;Id<12;++Id)
                {
                    FState R;
                    if (!Decode(ReadProbeJson(Directory/FString::Printf(TEXT("region-%03d.json"),Id)),Parent,R,Error))
                    { UE_LOG(LogTemp,Error,TEXT("Exterior owner: %s"),*Error);return; }
                    All.Add(MoveTemp(R));
                }
                if (!RaftSimLiquidParentExterior::FProfile::Build(Parent,All,
                    ReadProbeJson(Dataset.Parent/TEXT("grid_vector_boundary_profile.json")),Exterior,Error))
                { UE_LOG(LogTemp,Error,TEXT("Exterior table: %s"),*Error);return; }
                if(State->DenseRequested)
                {
                    const auto Geometry=ReadProbeJson(Dataset.Geometry/TEXT("manifest.json"));
                    FString MeshHash;FRaftSimLiquidFaceBed Bed;
                    if(!Geometry || !Geometry->TryGetStringField(TEXT("original_mesh_sha256"),MeshHash) ||
                        !RaftSimLiquidFaceBedProfile::Decode(ReadProbeJson(Dataset.FaceBed),Parent,
                            Dataset.Mesh,Dataset.Parent/TEXT("grid_vector_boundary_profile.json"),MeshHash,Bed,Error))
                    { UE_LOG(LogTemp,Error,TEXT("Exact outlet bed: %s"),*Error);return; }
                    Exterior.SetExactBed(MoveTemp(Bed));State->ExactExitBed=true;
                }
                if(State->RetirementRequested) State->RetirementProfile=Exterior;
            }
            bool Started=false;Probe=State;
            ON_SCOPE_EXIT { if (!Started) StopProbe(); };
            if (State->HandoffRequested)
            {
                // Honor manual preallocation on empty emitters too. This is a
                // bounded probe override, restored on stop/failure; it is not a
                // global production memory policy. Never resize a live buffer.
                State->EarlyFreeVariable=IConsoleManager::Get().FindConsoleVariable(TEXT("fx.NiagaraBatcher.FreeBufferEarly"));
                if (!State->EarlyFreeVariable) return;
                State->PreviousEarlyFree=State->EarlyFreeVariable->GetInt();
                State->EarlyFreeVariable->SetWithCurrentPriority(0);
            }
            // Retain actual regional grid dimensions and canonical actor
            // frames, but explicitly clear ALL water and inlet sources. No
            // mismatched legacy contact can be mistaken for a working river.
            TArray<FState> Regions;
            for (int32 Id=Args.Num()==2?0:10;Id<12;++Id)
            {
                FState R;
                if (!Decode(ReadProbeJson(Directory/FString::Printf(TEXT("region-%03d.json"),Id)),Parent,R,Error))
                { UE_LOG(LogTemp,Error,TEXT("Stage probe region: %s"),*Error);return; }
                State->RouteRegions.Add(FIntRect(R.FirstCell,R.FirstCell+FIntPoint(R.Cells.X,R.Cells.Y)));
                State->PreparedSpawnRates.Add(R.SpawnRate);
                // Explicit bounded reserve, not an assertion about live count.
                // Overflow fails the SAME atomic commit gate; never truncate
                // imports to fit a receiving CPU dispatch or native buffer.
                State->RegionalReservations.Add(State->DenseRequested?
                    FMath::Min(230000u,uint32(FMath::CeilToInt(R.Positions.Num()*1.5))+4096u):State->Reservation);
                if(!State->DenseRequested)
                {
                // A bounded diagnostic packet at a FOUR-REGION corner. Use
                // actual wet-prior seed positions/IDs, with explicitly authored
                // test velocities, and no continuous emission or handoff claim.
                TArray<FVector> PacketPositions;TArray<int32> PacketIds;
                const bool OutletPacket=State->RetirementRequested && Id==7;
                if(OutletPacket)
                {
                    // Real prepared wet seeds 30..70cm inside the EAST parent
                    // face, not fabricated positions or a regional cut. Speed
                    // below is explicit diagnostic forcing, not calibrated Q.
                    TArray<TPair<double,int32>> Candidates;
                    const auto& Rows=State->RetirementProfile.Packed();
                    for(int32 I=0;I<R.Positions.Num();++I)
                    {
                        const auto P=R.Positions[I];const double S=FVector::DotProduct(P,Parent.Frame.AxisX);
                        const double T=FVector::DotProduct(P,Parent.Frame.AxisY);
                        const double Distance=Parent.Lower.X*100+Parent.Cells.X*Parent.Spacing.X-S;
                        const int32 Column=FMath::FloorToInt((T-Parent.Lower.Y*100)/Parent.Spacing.Y);
                        if(Column<0 || Column>=Parent.Cells.Y || Distance<30 || Distance>70) continue;
                        const auto Row=Rows[8+Parent.Cells.Y+Column];
                        if(Row.Z>=0 || P.Z<=Row.X+35 || P.Z>=Row.Y-5) continue;
                        const double Score=Distance*Distance+FMath::Square(.05*T)+.01*FMath::Square(P.Z-Row.Y);
                        Candidates.Emplace(Score,I);
                    }
                    Candidates.Sort([](const auto& A,const auto& B){return A.Key==B.Key?A.Value<B.Value:A.Key<B.Key;});
                    if(Candidates.Num()<State->PacketPerOwner) { UE_LOG(LogTemp,Error,TEXT("Missing wet outlet seeds near approved parent east face"));return; }
                    for(int32 I=0;I<State->PacketPerOwner;++I)
                    { PacketPositions.Add(R.Positions[Candidates[I].Value]);PacketIds.Add(R.SeedIds[Candidates[I].Value]); }
                }
                else if (State->PacketRequested && !(State->EmptyReceiver && Id==0) && (R.FirstCell.X==128 || R.FirstCell.X+R.Cells.X==128) &&
                    (R.FirstCell.Y==64 || R.FirstCell.Y+R.Cells.Y==64))
                {
                    const FVector Corner=FVector(0,0,Parent.Frame.Origin.Z)+Parent.Frame.AxisX*(Parent.Lower.X*100+128*Parent.Spacing.X)+
                        Parent.Frame.AxisY*(Parent.Lower.Y*100+64*Parent.Spacing.Y);
                    TArray<TPair<double,int32>> Candidates;
                    for (int32 I=0;I<R.Positions.Num();++I)
                    {
                        const FVector D=R.Positions[I]-Corner;
                        const double Score=D.X*D.X+D.Y*D.Y+0.001*FMath::Square(D.Z-400.);
                        if (Score<=625.) Candidates.Emplace(Score,I);
                    }
                    Candidates.Sort([](const auto& A,const auto& B){return A.Key==B.Key?A.Value<B.Value:A.Key<B.Key;});
                    if (Candidates.Num()<State->PacketPerOwner) { UE_LOG(LogTemp,Error,TEXT("Insufficient nearby wet seeds for corner packet"));return; }
                    for (int32 I=0;I<State->PacketPerOwner;++I)
                    { PacketPositions.Add(R.Positions[Candidates[I].Value]);PacketIds.Add(R.SeedIds[Candidates[I].Value]); }
                }
                R.Positions.Reset();R.Velocities.Reset();R.SeedIds.Reset();R.SourceIds.Reset();
                R.SourcePositions.Reset();R.SourceVelocities.Reset();R.SourceWeights.Reset();R.Inflow=R.SpawnRate=0;
                for (int32 I=0;I<PacketIds.Num();++I)
                {
                    R.Positions.Add(PacketPositions[I]);
                    R.Velocities.Add(OutletPacket?Parent.Frame.AxisX*(100*State->PacketSpeed):State->PacketSpeed*FVector(100+20*Id+3*I,-35+17*Id-2*I,0));
                    R.SeedIds.Add(PacketIds[I]);
                }
                if (State->EmissionRequested && Id==1)
                {
                    // Explicit test source at a real wet seed, not calibrated Q.
                    // Start at zero rate; activate only after native initial birth.
                    R.SourcePositions.Add(R.Positions[0]);R.SourceVelocities.Add(R.Velocities[0]);
                    R.SourceIds.Add(R.SeedIds[0]);R.SourceWeights.Add(1.);
                }
                }
                else
                {
                    // Retain EVERY original seed, velocity and source array.
                    // Initial filling is separate from measured-rate inlet
                    // activation after the first native reset has completed.
                    R.SpawnRate=0;
                }
                auto* System=DuplicateObject<UNiagaraSystem>(Source,GetTransientPackage(),
                    MakeUniqueObjectName(GetTransientPackage(),UNiagaraSystem::StaticClass(),
                        FName(*FString::Printf(TEXT("LiquidRegionalStageProbe_%d"),Id))));
                if (!InstallArrays(System,R,Error)) { UE_LOG(LogTemp,Error,TEXT("Stage probe arrays: %s"),*Error);return; }
                if(State->FixedSourceSeed)
                {
                    int32 Changed=0;
                    for(auto& H:System->GetEmitterHandles()) if(H.GetName()==TEXT("Grid3D_FLIP_FluidControl_Emitter"))
                        if(auto* E=H.GetInstance().GetEmitterData())
                        {
                            E->bDeterminism=true;E->RandomSeed=State->SourceSeed+Id*7919;
                            State->BoundSourceSeeds.Add(E->RandomSeed);++Changed;
                        }
                    if(Changed!=1) { UE_LOG(LogTemp,Error,TEXT("Expected one native source emitter for explicit diagnostic seed"));return; }
                }
                if (State->HandoffRequested)
                    for (auto& H:System->GetEmitterHandles()) if (H.GetName()==TEXT("Grid3D_FLIP_FluidControl_Emitter"))
                        if (auto* E=H.GetInstance().GetEmitterData())
                        { E->AllocationMode=EParticleAllocationMode::ManualEstimate;
                          E->PreAllocationCount=State->DenseRequested?State->RegionalReservations.Last()+2048:State->Reservation*2; }
                if (State->EmissionRequested)
                    System->GetExposedParameters().SetParameterValue<FVector3f>(FVector3f::ZeroVector,
                        FNiagaraVariable(FNiagaraTypeDefinition::GetVec3Def(),TEXT("User.Inlet Scale")));
                const FVector3f SourceScale=System->GetExposedParameters().GetParameterValue<FVector3f>(
                    FNiagaraVariable(FNiagaraTypeDefinition::GetVec3Def(),TEXT("User.Inlet Scale")));
                State->BoundSourceScales.Add(SourceScale);
                if(State->DenseRequested && SourceScale!=FVector3f::ZeroVector)
                { UE_LOG(LogTemp,Error,TEXT("Dense source positions must not receive unregistered spatial jitter"));return; }
                if (State->ContactInstalled && !RaftSimInstallRegionalLiquidContact(System,R,
                    ReadProbeJson(Dataset.Geometry/
                        FString::Printf(TEXT("region-%03d-contact.json"),Id)),Error,State->ParentExterior?&Exterior:nullptr))
                { UE_LOG(LogTemp,Error,TEXT("Stage probe canonical contact: %s"),*Error);return; }
                if (State->ProjectionInstalled && !RaftSimInstallRegionalLiquidProjection(System,Parent,R,Error,State->Interface.PressureCoupled))
                { UE_LOG(LogTemp,Error,TEXT("Stage probe regional projection: %s"),*Error);return; }
                if(State->ProjectionInstalled)
                {
                    RaftSimLiquidRegionalProjection::FLayout Layout;
                    if(!RaftSimLiquidRegionalProjection::Build(Parent,R,Layout,Error)) return;
                    State->PressureOmegas.Add(Layout.PressureOmega());
                }
                System->RequestCompile(true);System->WaitForCompilationComplete(false,false);System->WaitForCompilationComplete(true,false);
                if (!System->IsReadyToRun()) { UE_LOG(LogTemp,Error,TEXT("Stage probe compile failed"));return; }
                if ((State->ParentExterior || State->PacketRequested) && Id==4)
                {
                    FString Label;
                    if (FParse::Value(FCommandLine::Get(),TEXT("RaftSimRegionalStageLabel="),Label) &&
                        !Label.Contains(TEXT("/")) && !Label.Contains(TEXT("\\")) && !Label.Contains(TEXT("..")))
                    {
                        const FString Dump=FPaths::ProjectDir()/TEXT("../docs/reconstruction-review-2026-09-07")/Label/TEXT("region-004-native.hlsl");
                        for (const auto& H:System->GetEmitterHandles()) if (H.GetIsEnabled()) if (const auto* E=H.GetInstance().GetEmitterData())
                        {
                            TArray<UNiagaraScript*> Scripts;E->GetScripts(Scripts,false);
                            for (const auto* S:Scripts) if (S->GetUsage()==ENiagaraScriptUsage::ParticleGPUComputeScript && !FPaths::FileExists(Dump))
                                FFileHelper::SaveStringToFile(S->GetVMExecutableData().LastHlslTranslationGPU,*Dump);
                        }
                    }
                }
                FActorSpawnParameters Spawn;Spawn.ObjectFlags|=RF_Transient;
                auto* Actor=World->SpawnActor<AActor>(AActor::StaticClass(),FTransform::Identity,Spawn);
                Actor->SetActorLabel(FString::Printf(TEXT("LiquidRegionalStageProbe_%d"),Id));
                auto* Component=NewObject<UNiagaraComponent>(Actor);Component->SetAutoActivate(false);
                if(State->FixedSourceSeed) Component->SetRandomSeedOffset(0);
                Actor->SetRootComponent(Component);Actor->AddInstanceComponent(Component);
                Component->SetAsset(System);Component->RegisterComponent();
                Actor->SetActorLocationAndRotation(FCanonicalFrame::WorldPosition(R.Frame.Origin),
                    FRotationMatrix::MakeFromXZ(R.Frame.WorldAxisX(),FVector::UpVector).ToQuat());
                Component->SetTickBehavior(ENiagaraTickBehavior::UseComponentTickGroup);
                Component->Activate(true);Component->SetComponentTickEnabled(false);
                auto Controller=Component->GetSystemInstanceController();
                if (!Controller) { Actor->Destroy();return; }
                FNiagaraComputeExecutionContext* Context=nullptr;
                for (const auto& E:Controller->GetSystemInstance_Unsafe()->GetEmitters())
                    if (E->GetEmitterHandle().GetName()==TEXT("Grid3D_FLIP_FluidControl_Emitter")) Context=E->GetGPUContext();
                if (!Context) { Actor->Destroy();return; }
                if(State->AdvectionPacketRequested)
                {
                    FIntVector Offsets;
                    Offsets.X=Context->CombinedParamStore.IndexOf(FNiagaraVariable(FNiagaraTypeDefinition::GetMatrix4Def(),TEXT("Grid3D_FLIP_FluidControl_Emitter.WorldToUnit")));
                    Offsets.Y=Context->CombinedParamStore.IndexOf(FNiagaraVariable(FNiagaraTypeDefinition::GetMatrix4Def(),TEXT("Grid3D_FLIP_FluidControl_Emitter.LocalToWorld")));
                    Offsets.Z=Context->CombinedParamStore.IndexOf(FNiagaraVariable(FNiagaraTypeDefinition::GetMatrix4Def(),TEXT("Grid3D_FLIP_FluidControl_Emitter.UnitToWorld")));
                    if(Offsets.GetMin()<0 || Offsets.GetMax()+int32(sizeof(FMatrix44f))>Context->CombinedParamStore.GetParameterDataArray().Num())
                    { UE_LOG(LogTemp,Error,TEXT("Native advection matrix layout unavailable: %d/%d/%d"),Offsets.X,Offsets.Y,Offsets.Z);return; }
                    State->AdvectionMatrixOffsets.Add(Offsets);
                }
                if(State->InterfaceRequested)
                {
                    const int32 Offset=Context->CombinedParamStore.IndexOf(FNiagaraVariable(FNiagaraTypeDefinition::GetFloatDef(),TEXT("Grid3D_FLIP_FluidControl_Emitter.DeltaTime")));
                    // ExternalCBufferLayoutSize is populated in the first emitter
                    // Tick, not Activate. Validate the initialized source layout
                    // here; the callback bounds-checks the immutable tick bytes.
                    if(Offset<0 || Offset+4>Context->CombinedParamStore.GetParameterDataArray().Num())
                    {
                        UE_LOG(LogTemp,Error,TEXT("Native Emitter.DeltaTime source layout unavailable (offset=%d, bytes=%d)"),Offset,Context->CombinedParamStore.GetParameterDataArray().Num());
                        for(const auto& V:Context->CombinedParamStore.ReadParameterVariables())
                            if(V.GetName().ToString().Contains(TEXT("DeltaTime"))) UE_LOG(LogTemp,Display,TEXT("Tick parameter %s"),*V.GetName().ToString());
                        return;
                    }
                    State->Interface.DeltaOffsets.Add(Offset);
                }
                if (State->PacketRequested)
                {
                    auto& Sample=State->Packet.AddDefaulted_GetRef();Sample.RegionId=R.Id;Sample.ExpectedCount=R.Positions.Num();
                    Sample.InitialSeedIds=R.SeedIds;
                    Sample.Cells=R.ComputationalCells;Sample.Origin=FCanonicalFrame::WorldPosition(R.Frame.Origin);
                    Sample.AxisX=R.Frame.WorldAxisX();Sample.AxisY=R.Frame.WorldAxisY();Sample.Extent=R.Extent;Sample.Volume=R.ParticleVolume;
                    int32 Found=0,IdentityFound=0;
                    for (const auto& V:Context->MainDataSet->GetVariables())
                    {
                        if(V.GetName()==TEXT("RiverSourceIndex"))
                        {
                            const auto* Layout=Context->MainDataSet->GetVariableLayout(V);
                            if(!Layout || Layout->GetNumInt32Components()!=1) return;
                            Sample.SourceIndexOffset=Layout->GetInt32ComponentStart();
                        }
                        const FName InletNames[]={TEXT("RiverInletRawPosition"),TEXT("RiverInletRawVelocity"),TEXT("RiverInletFace")};
                        for(int32 I=0;I<3;++I) if(V.GetName()==InletNames[I])
                        {
                            const auto* Layout=Context->MainDataSet->GetVariableLayout(V);
                            if(!Layout || Layout->GetNumFloatComponents()!=(I==2?1u:3u)) return;
                            Sample.InletOffsets[I]=Layout->GetFloatComponentStart();
                        }
                        if (V.GetName()==TEXT("Position") || V.GetName()==TEXT("Velocity") || V.GetName()==TEXT("RiverStepStartPosition"))
                        {
                            if (V.GetType()!=FNiagaraTypeDefinition::GetPositionDef() && V.GetType()!=FNiagaraTypeDefinition::GetVec3Def()) return;
                            const uint32 Offset=Context->MainDataSet->GetVariableLayout(V)->GetFloatComponentStart();
                            if (V.GetName()==TEXT("Position")) Sample.PositionOffset=Offset;
                            else if (V.GetName()==TEXT("Velocity")) Sample.VelocityOffset=Offset;
                            else Sample.StepStartOffset=Offset;
                            ++Found;
                        }
                        const FName IdentityNames[]={TEXT("RiverBirthOwner"),TEXT("RiverBirthSequence"),TEXT("UniqueID"),TEXT("ID")};
                        for (int32 I=0;I<4;++I) if (V.GetName()==IdentityNames[I])
                        {
                            const auto* Layout=Context->MainDataSet->GetVariableLayout(V);
                            if (!Layout || (I<3 && V.GetType()!=FNiagaraTypeDefinition::GetIntDef()) ||
                                Layout->GetNumInt32Components()!=(I==3?2u:1u)) return;
                            Sample.IdentityOffsets[I]=Layout->GetInt32ComponentStart();++IdentityFound;
                        }
                    }
                    if (Found!=3) { UE_LOG(LogTemp,Error,TEXT("Full-precision native packet position/velocity/pre-advection attributes missing"));return; }
                    if(State->ParentExterior && Sample.InletOffsets.GetMin()<0)
                    { UE_LOG(LogTemp,Error,TEXT("Physical inlet advection evidence missing"));return; }
                    if (IdentityFound!=4) { UE_LOG(LogTemp,Error,TEXT("Native integer birth/engine particle identities missing"));return; }
                    FNiagaraDataInterfaceProxyNeighborQuery* Neighbor=nullptr;
                    for (auto* DI:Context->GetDataInterfaces()) if (auto* N=Cast<UNiagaraDataInterfaceNeighborQuery>(DI))
                    {
                        if (Neighbor) { UE_LOG(LogTemp,Error,TEXT("Ambiguous native neighbor interface"));return; }
                        Neighbor=static_cast<FNiagaraDataInterfaceProxyNeighborQuery*>(N->GetProxy());
                    }
                    if (!Neighbor) return;
                    State->Neighbors.Add(Neighbor);
                    if (State->DenseRequested && R.Id==4)
                    {
                        Sample.NeighborProxy=Neighbor;Sample.NeighborSystem=Controller->GetSystemInstanceID();
                    }
                }
                State->Components.Emplace(Component);State->Systems.Add(Controller->GetSystemInstanceID());State->Contexts.Add(Context);
                FNiagaraDataInterfaceProxyGrid3DCollectionProxy* Pressure=nullptr;
                FNiagaraDataInterfaceProxyGrid3DCollectionProxy* BoundaryGrid=nullptr;
                FNiagaraDataInterfaceProxyGrid3DCollectionProxy* RawGrid=nullptr;
                FNiagaraDataInterfaceProxyGrid3DCollectionProxy* VelocityGrid=nullptr;
                FNiagaraDataInterfaceProxyGrid3DCollectionProxy* SupportGrid=nullptr;
                for (auto* DI:Context->GetDataInterfaces())
                    if (auto* Grid=Cast<UNiagaraDataInterfaceGrid3DCollection>(DI))
                    {
                        const auto* const* Found=Grid->GetSystemInstancesToProxyData_GT().Find(Controller->GetSystemInstanceID());
                        if (!Found || !*Found || (*Found)->Vars.Num()!=1) continue;
                        if (State->TransferEnabled)
                        {
                            const FName Name=(*Found)->Vars[0].GetName();
                            auto** Target=Name==TEXT("Momentum_Volume")?&RawGrid:Name==TEXT("Velocity")?&VelocityGrid:Name==TEXT("SimFloat")?&SupportGrid:nullptr;
                            if (Target)
                            {
                                const auto Format=(*Found)->PixelFormat.Get(PF_Unknown);
                                const bool FormatOK=Name==TEXT("Momentum_Volume")?Format==PF_A32B32G32R32F:
                                    Name==TEXT("Velocity")?Format==PF_FloatRGBA:(Format==PF_R16F || Format==PF_R32_FLOAT);
                                if (*Target || !FormatOK || (*Found)->Offsets.Num()!=1 || (*Found)->Offsets[0]!=0 ||
                                    (*Found)->NumTiles!=FIntVector(1,1,1) ||
                                    (Name==TEXT("Momentum_Volume") && (*Found)->NumCells!=R.ComputationalCells))
                                { UE_LOG(LogTemp,Error,TEXT("Invalid or ambiguous raw/velocity/support grid %s format%d cells%s duplicate%d"),
                                    *Name.ToString(),int32(Format),*(*Found)->NumCells.ToString(),*Target!=nullptr);return; }
                                // Native grids receive XYZ through SetNumCells
                                // during initialization. Check actual RT sizes
                                // after that stage, just like pressure/boundary.
                                *Target=static_cast<FNiagaraDataInterfaceProxyGrid3DCollectionProxy*>(Grid->GetProxy());
                            }
                        }
                        if ((*Found)->Vars[0].GetName()==TEXT("SolidVelocity_Boundary"))
                        {
                            if (BoundaryGrid || (*Found)->Offsets.Num()!=1 || (*Found)->Offsets[0]!=0 ||
                                (*Found)->NumTiles!=FIntVector(1,1,1) || (*Found)->PixelFormat.Get(PF_Unknown)!=PF_FloatRGBA)
                            { UE_LOG(LogTemp,Error,TEXT("Ambiguous regional boundary interface"));return; }
                            BoundaryGrid=static_cast<FNiagaraDataInterfaceProxyGrid3DCollectionProxy*>(Grid->GetProxy());
                        }
                        if ((*Found)->Vars[0].GetName()!=TEXT("Pressure")) continue;
                        // Niagara calls single-attribute untiled R32F storage
                        // "UseRGBATexture" too. Validate actual packing/format,
                        // not that misleading boolean.
                        if (Pressure || (*Found)->Offsets.Num()!=1 || (*Found)->Offsets[0]!=0 ||
                            (*Found)->NumTiles!=FIntVector(1,1,1) || (*Found)->PixelFormat.Get(PF_Unknown)!=PF_R32_FLOAT)
                        { UE_LOG(LogTemp,Error,TEXT("Ambiguous or tiled regional pressure interface"));return; }
                        Pressure=static_cast<FNiagaraDataInterfaceProxyGrid3DCollectionProxy*>(Grid->GetProxy());
                    }
                if (!Pressure) { UE_LOG(LogTemp,Error,TEXT("Regional native pressure interface missing"));return; }
                if (State->ContactInstalled && !BoundaryGrid) { UE_LOG(LogTemp,Error,TEXT("Regional native boundary interface missing"));return; }
                State->Boundary.Add(BoundaryGrid);
                if (State->TransferEnabled && (!RawGrid || !VelocityGrid || !SupportGrid))
                {
                    UE_LOG(LogTemp,Error,TEXT("Native transfer interfaces missing: raw%d velocity%d support%d"),RawGrid!=nullptr,VelocityGrid!=nullptr,SupportGrid!=nullptr);
                    for (auto* DI:Context->GetDataInterfaces()) if (auto* Grid=Cast<UNiagaraDataInterfaceGrid3DCollection>(DI))
                    {
                        const auto* const* Found=Grid->GetSystemInstancesToProxyData_GT().Find(Controller->GetSystemInstanceID());
                        FString Names;if (Found && *Found) for (const auto& V:(*Found)->Vars) Names+=V.GetName().ToString()+TEXT(";");
                        UE_LOG(LogTemp,Display,TEXT("Transfer grid %s found%d vars[%s]"),*Grid->GetPathName(),Found && *Found,*Names);
                    }
                    return;
                }
                State->RawTransfer.Add(RawGrid);State->Velocity.Add(VelocityGrid);State->Support.Add(SupportGrid);
                State->Pressure.Add(Pressure);State->Sizes.Add(R.ComputationalCells);State->RegionIds.Add(R.Id);Regions.Add(MoveTemp(R));
            }
            // Map every shared halo column directly to its physical owner,
            // including diagonal owners. This probe still contains NO water.
            for (int32 D=0;D<Regions.Num();++D) for (int32 S=0;S<Regions.Num();++S)
            {
                if (D==S) continue;
                const auto& Dest=Regions[D];const auto& SourceRegion=Regions[S];
                for (int32 Y=0;Y<Dest.ComputationalCells.Y;++Y) for (int32 X=0;X<Dest.ComputationalCells.X;++X)
                {
                    if (X>=2 && Y>=2 && X<Dest.Cells.X+2 && Y<Dest.Cells.Y+2) continue;
                    const FIntPoint Global=Dest.FirstCell+FIntPoint(X-2,Y-2),Local=Global-SourceRegion.FirstCell;
                    if (Local.X<0 || Local.Y<0 || Local.X>=SourceRegion.Cells.X || Local.Y>=SourceRegion.Cells.Y) continue;
                    State->Copies.Add({S,D,FIntPoint(Local.X+2,SourceRegion.ComputationalCells.Y-3-Local.Y),
                        FIntPoint(X,Dest.ComputationalCells.Y-1-Y)});
                }
            }
            if(State->HandoffRequested)
            {
                if(!State->Lifetime.Initialize(FGuid::NewGuid(),State->Systems.Num(),Error))
                { UE_LOG(LogTemp,Error,TEXT("Liquid generation: %s"),*Error);return; }
                for(auto& Sample:State->Packet) Sample.Generation=State->Lifetime.GetGeneration();
            }
            if(State->ProjectionPacketRequested)
            {
                State->ProjectionPackets.SetNum(State->Systems.Num());
                for(auto& Packet:State->ProjectionPackets) Packet.AdvectionRequested=State->AdvectionPacketRequested;
            }
            if(State->AdvectionPacketRequested) State->AdvectionPackets.SetNum(State->Systems.Num());
            if(State->InterfaceRequested && !State->Interface.Load(Base/TEXT("south-fork-liquid-interface-20260911"),Dataset,State->Sizes,State->PacketStep,Error))
            { UE_LOG(LogTemp,Error,TEXT("Initial live interface: %s"),*Error);return; }
            ENQUEUE_RENDER_COMMAND(RaftSimStartRegionalStageProbe)([State](FRHICommandListImmediate& Cmd)
            {
                if(State->InterfaceRequested) State->Interface.Initialize(Cmd);
                if(State->Interface.PressureCoupled)
                    State->SurfaceHandle=URaftSimLiquidStageInterface::SurfaceBindingEvent().AddLambda(
                        [State](FRDGBuilder& Graph,uint64 SystemId,FRDGTextureRef& Texture)
                        {
                            const int32 I=State->Systems.IndexOfByKey(SystemId);
                            if(I==INDEX_NONE) return;
                            auto& Local=Graph.Blackboard.GetOrCreate<FRaftSimRegionalProbeGraph>().Interface;
                            if(State->Interface.Bind(Graph,Local,State->ExchangeError)) Texture=Local.Current[I];
                            else if(State->ExchangeError.IsEmpty()) State->ExchangeError=TEXT("Current pressure interface unavailable");
                        });
                if (State->HandoffRequested)
                    State->ReservationHandle=State->Dispatch->GetOnPreInitViewsEvent().AddLambda([State](FRDGBuilder&)
                    {
                        if (!State->FirstGroups || !State->ExchangeError.IsEmpty()) return;
                        State->ReservationReady=false;
                        bool AllAllocated=true;
                        for (int32 Owner=0;Owner<State->Contexts.Num();++Owner)
                        {
                            auto* C=State->Contexts[Owner];
                            auto* D=C->MainDataSet->GetCurrentData();
                            if (!D || !D->GetNumInstancesAllocated()) { AllAllocated=false;continue; }
                            const uint32 Reserve=State->RegionalReservations[Owner];
                            if (D->GetNumInstancesAllocated()<Reserve || D->GetGPUInstanceCountBufferOffset()==INDEX_NONE)
                            {
                                State->ExchangeError=FString::Printf(TEXT("Native incoming reservation missing: owner%d capacity%u countOffset%u CPU%u"),
                                    Owner,D->GetNumInstancesAllocated(),D->GetGPUInstanceCountBufferOffset(),C->GetCurrentNumInstances());return;
                            }
                            // Bounded global upper count, not a per-owner live claim.
                            // Emission mode allows one birth/step for at most 12
                            // measured steps in addition to <=16 initial particles.
                            C->EmitterInstanceReadback.GPUCountOffset=INDEX_NONE;
                            C->SetCurrentNumInstances(Reserve);
                        }
                        State->ReservationReady=AllAllocated;
                    });
                State->Handle=URaftSimLiquidStageInterface::PostGroupEvent().AddLambda(
                    [State](FRDGBuilder& Graph,uint32 Ordinal,TConstArrayView<FRaftSimLiquidCompletedStage> Stages)
                    {
                        TArray<FRaftSimLiquidCompletedStage> Relevant;TSet<int32> Seen;
                        for (const auto& Stage:Stages)
                            for (int32 I=0;I<State->Systems.Num();++I)
                                if (Stage.SystemId==State->Systems[I] && Stage.Context==State->Contexts[I])
                                { Relevant.Add(Stage);Seen.Add(I); }
                        if (Relevant.IsEmpty()) return;
                        // Niagara restores its counter to SRV|CopySrc after the
                        // last dispatch GROUP, which is not necessarily the last
                        // stage of this system's tick. Query the actual batch
                        // state and restore it before engine readback/free work.
                        const auto CounterState=State->PacketRequested?
                            FNiagaraDataInterfaceArrayImplInternal::GetCountBufferRHIAccess(*State->Dispatch):ERHIAccess::UAVCompute;
                        auto* CounterUav=State->PacketRequested?State->Dispatch->GetGPUInstanceCounterManager().GetInstanceCountBuffer().UAV.GetReference():nullptr;
                        if (CounterState!=ERHIAccess::UAVCompute)
                            Graph.AddPass(RDG_EVENT_NAME("Regional Native Counter Access Begin"),ERDGPassFlags::None,
                                [CounterUav,CounterState](FRHICommandList& Cmd)
                                { Cmd.Transition(FRHITransitionInfo(CounterUav,CounterState,ERHIAccess::UAVCompute)); });
                        ON_SCOPE_EXIT
                        {
                            if (CounterState!=ERHIAccess::UAVCompute)
                                Graph.AddPass(RDG_EVENT_NAME("Regional Native Counter Access End"),ERDGPassFlags::None,
                                    [CounterUav,CounterState](FRHICommandList& Cmd)
                                    { Cmd.Transition(FRHITransitionInfo(CounterUav,ERHIAccess::UAVCompute,CounterState)); });
                        };
                        const bool Full=Relevant.Num()==State->Systems.Num() && Seen.Num()==State->Systems.Num();
                        bool Aligned=Full;
                        for (const auto& S:Relevant)
                        {
                            const auto& A=Relevant[0];
                            Aligned &= S.StageName==A.StageName && S.StageIndex==A.StageIndex && S.Iteration==A.Iteration &&
                                S.Iterations==A.Iterations && S.Loop==A.Loop && S.Loops==A.Loops && S.First==A.First && S.Last==A.Last && S.Reset==A.Reset;
                        }
                        State->Incomplete+=!Full;State->Misaligned+=Full && !Aligned;State->Complete+=Aligned;
                        State->PressureGroups+=Aligned && Relevant[0].StageName.ToString().Contains(TEXT("Pressure"));
                        State->FirstGroups+=Aligned && Relevant[0].First;
                        if(State->InterfaceRequested && Aligned && Relevant[0].First && State->ExchangeError.IsEmpty())
                        {
                            if(State->FirstGroups==1 && Relevant[0].Reset && !State->Interface.InitialResetObserved)
                                State->Interface.InitialResetObserved=true;
                            else if(Relevant[0].Reset || !State->Interface.InitialResetObserved)
                                State->ExchangeError=TEXT("Interface requires exactly one initial native reset");
                        }
                        if (State->PacketRequested && Aligned && Relevant[0].First && State->ExchangeError.IsEmpty())
                        {
                            // Native slot storage can grow during Spawn/Update.
                            // UE's pooled buffer Initialize replaces storage but
                            // retains cached SRV/UAVs within the same RDG graph.
                            // Drop only cached views before the complete
                            // post-spawn insertion; do not clear particle/grid
                            // data or change counts. Existing passes retain their
                            // original RDG resource references.
                            for (int32 I=0;I<State->Neighbors.Num();++I)
                            {
                                auto* N=State->Neighbors[I]->SystemInstancesToProxyData_RT.Find(State->Systems[I]);
                                if (!N) { State->ExchangeError=TEXT("Native neighbor refresh state missing");break; }
                                N->CellIdBuffer.EndGraphUsage();N->ParticleIdIndexBuffer.EndGraphUsage();
                                N->AcquireTagBuffer.EndGraphUsage();N->CellCountBuffer.EndGraphUsage();
                                N->CellOffsetBuffer.EndGraphUsage();N->ParticleListBuffer.EndGraphUsage();
                                N->AcquireTagListBuffer.EndGraphUsage();
                            }
                            if (State->ExchangeError.IsEmpty()) ++State->NeighborViewRefreshes;
                        }
                        if(State->HandoffRequested && Aligned && Relevant[0].First && State->ExchangeError.IsEmpty())
                        {
                            TArray<FRaftSimLiquidBirthPlan> Plans;
                            for(const auto& S:Relevant)
                                Plans.Add({uint32(State->Systems.Find(S.SystemId)),S.RateSpawns,S.EventSpawns,S.Reset});
                            State->Lifetime.BeginStep(State->FirstGroups,Plans,State->TickToken,State->ExchangeError);
                        }
                        if (Aligned && State->TransferEnabled && Relevant[0].StageName==TEXT("Neighbor Grid Rasterize Particles") && State->ExchangeError.IsEmpty())
                        {
                            auto& Plan=Graph.Blackboard.GetOrCreate<FRaftSimRegionalProbeGraph>().Transfer;
                            if (!Plan.Groups) Plan=RaftSimBuildLiquidTransferPlan(Graph,State->Sizes,State->Copies,State->ExchangeError);
                            TArray<FRDGTextureRef> Raw,Velocity,Support,Totals;
                            auto Gather=[&](const auto& Proxies,TArray<FRDGTextureRef>& Textures)
                            {
                                for (int32 I=0;I<Proxies.Num();++I)
                                {
                                    auto* Data=Proxies[I]->SystemInstancesToProxyData_RT.Find(State->Systems[I]);
                                    if (!Data || !Data->CurrentData || !Data->CurrentData->IsValid() ||
                                        Data->NumCells!=State->Sizes[I] || Data->NumTiles!=FIntVector(1,1,1))
                                    { State->ExchangeError=TEXT("Current same-step native P2G grid unavailable");return false; }
                                    Textures.Add(Data->CurrentData->GetOrCreateTexture(Graph));
                                }
                                return true;
                            };
                            if (Gather(State->RawTransfer,Raw) && Gather(State->Velocity,Velocity) && Gather(State->Support,Support) &&
                                RaftSimReduceLiquidTransfer(Graph,Plan,Raw,Totals,State->ExchangeError))
                            {
                                for (int32 I=0;I<Totals.Num();++I)
                                    if (!RaftSimResolveLiquidTransfer(Graph,Totals[I],Velocity[I],Support[I],State->ExchangeError)) break;
                                if (State->PacketRequested && State->TransferReductions==0 && State->ExchangeError.IsEmpty())
                                    for (int32 I=0;I<Totals.Num();++I)
                                        if (!State->Packet[I].CaptureBirthIdentities(Graph,State->Contexts[I],State->Dispatch,State->ExchangeError)) break;
                                if (State->PacketRequested && !State->PacketCaptured && State->ExchangeError.IsEmpty() &&
                                    State->TransferReductions+1==uint32(State->PacketStep))
                                {
                                    FRaftSimLiquidParticleRoutePlan RoutePlan;
                                    TArray<FRaftSimLiquidParticleRoutePacket> Routes;Routes.SetNum(Totals.Num());
                                    if (State->RouteRequested)
                                    {
                                        RoutePlan=RaftSimBuildLiquidParticleRoutePlan(Graph,State->RouteParentCells,State->RouteRegions,
                                            State->RouteLower,State->RouteAxisX,State->RouteAxisY,State->RouteSpacing,State->ExchangeError);
                                        RoutePlan.ResidualOuterBoundary=FParse::Param(FCommandLine::Get(),TEXT("RaftSimRegionalResidualBoundary"));
                                    }
                                    for (int32 I=0;I<Totals.Num();++I)
                                        if (!State->ExchangeError.IsEmpty() || !State->Packet[I].Capture(Graph,State->Contexts[I],State->Dispatch,Raw[I],Totals[I],State->ExchangeError,
                                            State->RouteRequested?&RoutePlan:nullptr,State->AssemblyRequested?&Routes[I]:nullptr)) break;
                                    if (State->AssemblyRequested && State->ExchangeError.IsEmpty())
                                    {
                                        uint32 NativeTag=0;
                                        for (const auto* C:State->Contexts)
                                            NativeTag=FMath::Max(NativeTag,C->MainDataSet->GetCurrentData()->GetIDAcquireTag());
                                        State->Assembly.Capture(Graph,Routes,State->ExchangeError,
                                            State->HandlesRequested?State->Packet[0].IdentityOffsets.W:MAX_uint32,NativeTag);
                                    }
                                    State->PacketCaptured=State->ExchangeError.IsEmpty();
                                }
                                if (State->ExchangeError.IsEmpty()) ++State->TransferReductions;
                            }
                        }
                        if (Aligned && State->BoundaryExchange && Relevant[0].StageName==TEXT("Compute Boundary") && State->ExchangeError.IsEmpty())
                        {
                            auto& Plan=Graph.Blackboard.GetOrCreate<FRaftSimRegionalProbeGraph>().Halo;
                            if (!Plan.Columns) Plan=RaftSimBuildLiquidHaloPlan(Graph,State->Sizes,State->Copies,State->ExchangeError);
                            TArray<FRDGTextureRef> Grids;
                            for (int32 I=0;I<State->Boundary.Num();++I)
                            {
                                const auto* Data=State->Boundary[I]->SystemInstancesToProxyData_RT.Find(State->Systems[I]);
                                if (!Data || !Data->CurrentData || !Data->CurrentData->IsValid() ||
                                    Data->NumCells!=State->Sizes[I] || Data->NumTiles!=FIntVector(1,1,1))
                                { State->ExchangeError=TEXT("Current post-stage native boundary grid unavailable");break; }
                                Grids.Add(Data->CurrentData->GetOrCreateTexture(Graph));
                            }
                            // Imported type/solid velocity must be visible to
                            // the NEXT native extrapolation, divergence and
                            // pressure stages, not a later rendered frame.
                            if (State->ExchangeError.IsEmpty() && RaftSimExchangeLiquidBoundaryHalo(Graph,Plan,Grids,State->ExchangeError)) ++State->BoundaryExchanges;
                        }
                        auto CurrentPressure=[&](TArray<FRDGTextureRef>& Grids)
                        {
                            for (int32 I=0;I<State->Pressure.Num();++I)
                            {
                                auto* Data=State->Pressure[I]->SystemInstancesToProxyData_RT.Find(State->Systems[I]);
                                if (!Data || !Data->CurrentData || !Data->CurrentData->IsValid() ||
                                    Data->NumCells!=State->Sizes[I] || Data->NumTiles!=FIntVector(1,1,1))
                                { State->ExchangeError=TEXT("Current post-stage untiled pressure grid unavailable");return false; }
                                Grids.Add(Data->CurrentData->GetOrCreateTexture(Graph));
                            }
                            return true;
                        };
                        if (Aligned && State->MarkerRequested && !State->MarkerSeeded &&
                            Relevant[0].StageName==TEXT("Compute Divergence") && State->ExchangeError.IsEmpty())
                        {
                            // Diagnostic-only nonzero field. With ZERO water,
                            // visited non-shared cells must become zero. Other
                            // cells must retain this exact owner-specific marker.
                            TArray<FRDGTextureRef> Grids;
                            if (CurrentPressure(Grids))
                            {
                                for (int32 I=0;I<Grids.Num();++I)
                                    AddClearUAVPass(Graph,Graph.CreateUAV(Grids[I]),float(1000+State->RegionIds[I]));
                                State->MarkerSeeded=true;
                            }
                        }
                        if (Aligned && Relevant[0].StageName==TEXT("Solve Pressure") && State->ExchangeError.IsEmpty())
                        {
                            auto& Plan=Graph.Blackboard.GetOrCreate<FRaftSimRegionalProbeGraph>().Halo;
                            if (!Plan.Columns) Plan=RaftSimBuildLiquidHaloPlan(Graph,State->Sizes,State->Copies,State->ExchangeError);
                            TArray<FRDGTextureRef> Grids;
                            if (CurrentPressure(Grids) && State->MarkerSeeded && !State->MarkerCaptured)
                            {
                                if (Relevant[0].Iteration!=0) State->ExchangeError=TEXT("Marker missed first pressure color");
                                else for (int32 I=0;I<Grids.Num();++I) for (int32 Z=0;Z<State->Sizes[I].Z;++Z)
                                {
                                    auto& Slice=State->MarkerSlices.AddDefaulted_GetRef();Slice.Owner=I;Slice.Z=Z;
                                    Slice.Readback=MakeUnique<FRHIGPUTextureReadback>(TEXT("RegionalPressureFirstColor"));
                                    auto* Read=Slice.Readback.Get();auto* Parameters=Graph.AllocParameters<FRaftSimRegionalMarkerCopy>();
                                    Parameters->Texture=Grids[I];const auto Size=State->Sizes[I];
                                    Graph.AddPass(RDG_EVENT_NAME("RegionalPressureMarkerBeforeExchange"),Parameters,ERDGPassFlags::Readback,
                                        [Read,Texture=Grids[I],Size,Z](FRHICommandList& Cmd)
                                        { Read->EnqueueCopy(Cmd,Texture->GetRHI(),FIntVector(0,0,Z),0,FIntVector(Size.X,Size.Y,1)); });
                                }
                                State->MarkerCaptured=State->ExchangeError.IsEmpty();
                            }
                            if (State->ExchangeError.IsEmpty() && RaftSimExchangeLiquidPressureHalo(Graph,Plan,Grids,State->ExchangeError)) ++State->Exchanges;
                        }
                        if(Aligned && State->Interface.CompactTransport && Relevant[0].StageName==TEXT("Extrapolate Velocities Again") && State->ExchangeError.IsEmpty())
                        {
                            if(State->FirstGroups<2 || State->AdvectionVelocityExchanges!=State->FirstGroups-2)
                            { State->ExchangeError=TEXT("Shared transport velocity missed or repeated a native step");return; }
                            auto& Plan=Graph.Blackboard.GetOrCreate<FRaftSimRegionalProbeGraph>().Halo;
                            if(!Plan.Columns) Plan=RaftSimBuildLiquidHaloPlan(Graph,State->Sizes,State->Copies,State->ExchangeError);
                            TArray<FRDGTextureRef> Grids;
                            for(int32 I=0;I<State->Velocity.Num();++I)
                            {
                                auto* Data=State->Velocity[I]->SystemInstancesToProxyData_RT.Find(State->Systems[I]);
                                if(!Data || !Data->CurrentData || !Data->CurrentData->IsValid() ||
                                    Data->NumCells!=State->Sizes[I] || Data->NumTiles!=FIntVector(1,1,1))
                                { State->ExchangeError=TEXT("Current post-extrapolation owner velocity unavailable");break; }
                                Grids.Add(Data->CurrentData->GetOrCreateTexture(Graph));
                            }
                            // Must precede paired capture, surface transport and
                            // the following native FLIP/PIC particle stage.
                            if(State->ExchangeError.IsEmpty() && RaftSimExchangeLiquidVelocityHalo(Graph,Plan,Grids,State->ExchangeError))
                                ++State->AdvectionVelocityExchanges;
                        }
                        if(Aligned && State->ProjectionPacketRequested && State->FirstGroups==uint32(State->PacketStep) && State->ExchangeError.IsEmpty())
                        {
                            const auto& S=Relevant[0];
                            const bool Inputs=S.StageName==TEXT("Compute Divergence");
                            const bool Pressure=S.StageName==TEXT("Solve Pressure") && S.Iteration+1==S.Iterations && S.Loop+1==S.Loops;
                            const bool Projected=S.StageName==TEXT("Project Pressure");
                            const bool Advected=State->AdvectionPacketRequested && S.StageName==TEXT("Extrapolate Velocities Again");
                            if(Inputs || Pressure || Projected || Advected)
                            {
                                if(!State->PacketCaptured || State->TransferReductions!=State->FirstGroups)
                                    State->ExchangeError=TEXT("Projection packet is not paired with current native P2G");
                                for(int32 I=0;I<State->Systems.Num() && State->ExchangeError.IsEmpty();++I)
                                for(int32 F=Inputs?0:Pressure?3:Projected?4:5;F<(Inputs?3:Pressure?4:Projected?5:6);++F)
                                {
                                    auto* Proxy=F==0?State->Boundary[I]:(F==1 || F>=4)?State->Velocity[I]:F==2?State->Support[I]:State->Pressure[I];
                                    auto* Data=Proxy->SystemInstancesToProxyData_RT.Find(State->Systems[I]);
                                    if(!Data || !Data->CurrentData || !Data->CurrentData->IsValid() || Data->NumCells!=State->Sizes[I] || Data->NumTiles!=FIntVector(1,1,1))
                                    { State->ExchangeError=TEXT("Same-step projection source unavailable");break; }
                                    if(!State->ProjectionPackets[I].Capture(Graph,Data->CurrentData->GetOrCreateTexture(Graph),F,State->FirstGroups,State->ExchangeError)) break;
                                }
                            }
                        }
                        if(Aligned && State->AdvectionPacketRequested && State->FirstGroups==uint32(State->PacketStep) &&
                            Relevant[0].StageName==TEXT("FLIP / PIC force") && State->ExchangeError.IsEmpty())
                        {
                            for(int32 I=0;I<State->Systems.Num();++I)
                            {
                                const auto* S=Relevant.FindByPredicate([&](const auto& V){return V.SystemId==State->Systems[I];});
                                if(!S || !State->PacketCaptured || !State->AdvectionPackets[I].Capture(Graph,State->Contexts[I],
                                    State->Dispatch,State->Packet[I],State->FirstGroups,S->EngineDeltaSeconds,
                                    S->ExternalParameters,S->ExternalParameterBytes,State->AdvectionMatrixOffsets[I],State->ExchangeError)) break;
                            }
                        }
                        if(Aligned && State->InterfaceRequested && Relevant[0].StageName==State->Interface.TransportStage() &&
                            (State->Interface.PressureCoupled || State->FirstGroups<=uint32(State->PacketStep)) && State->ExchangeError.IsEmpty())
                        {
                            TArray<FRDGTextureRef> Flow,Boundary;float Dt=-1,EngineDt=-1;
                            if(State->TransferReductions!=State->FirstGroups)
                            { State->ExchangeError=TEXT("Interface update not paired with the current native transfer");return; }
                            for(int32 I=0;I<State->Systems.Num();++I)
                            {
                                const auto* S=Relevant.FindByPredicate([&](const auto& V){return V.SystemId==State->Systems[I];});
                                const int32 Offset=State->Interface.DeltaOffsets[I];float CurrentDt=-1;
                                if(!S || !S->ExternalParameters || uint32(Offset+4)>S->ExternalParameterBytes)
                                { State->ExchangeError=TEXT("Current native interface clock unavailable");break; }
                                FMemory::Memcpy(&CurrentDt,S->ExternalParameters+Offset,4);
                                if(I==0) { Dt=CurrentDt;EngineDt=S->EngineDeltaSeconds; }
                                if(!FMath::IsFinite(CurrentDt) || CurrentDt<0 || CurrentDt!=Dt || S->EngineDeltaSeconds!=EngineDt)
                                { State->ExchangeError=TEXT("Native interface clocks differ across physical owners");break; }
                                auto* Data=State->Velocity[I]->SystemInstancesToProxyData_RT.Find(State->Systems[I]);
                                if(!Data || !Data->CurrentData || !Data->CurrentData->IsValid() || Data->NumCells!=State->Sizes[I] || Data->NumTiles!=FIntVector(1,1,1))
                                { State->ExchangeError=TEXT("Current native interface velocity unavailable");break; }
                                Flow.Add(Data->CurrentData->GetOrCreateTexture(Graph));
                                if(State->Interface.HighOrder)
                                {
                                    auto* Solid=State->Boundary[I]->SystemInstancesToProxyData_RT.Find(State->Systems[I]);
                                    if(!Solid || !Solid->CurrentData || !Solid->CurrentData->IsValid() ||
                                        Solid->NumCells!=State->Sizes[I] || Solid->NumTiles!=FIntVector(1,1,1))
                                    { State->ExchangeError=TEXT("Same-step native high-order solid boundary unavailable");break; }
                                    Boundary.Add(Solid->CurrentData->GetOrCreateTexture(Graph));
                                }
                            }
                            auto& Resources=Graph.Blackboard.GetOrCreate<FRaftSimRegionalProbeGraph>();
                            if(State->ExchangeError.IsEmpty())
                            {
                                const auto Plan=RaftSimBuildLiquidHaloPlan(Graph,State->Sizes,State->Copies,State->ExchangeError);
                                if(Plan.Columns) State->Interface.Advance(Graph,Resources.Interface,Plan,Flow,Boundary,State->FirstGroups,Dt,EngineDt,State->ExchangeError);
                            }
                        }
                        if (Aligned && Relevant[0].Last && State->HandoffRequested && State->FirstGroups>=2 &&
                            State->FirstGroups<uint32(State->HandoffCount+2) && State->ExchangeError.IsEmpty())
                        {
                            if(!State->ReservationReady)
                            {
                                State->ExchangeError=TEXT("Native reset must complete before reserving the next transfer batch; incoming dispatch is not ready");
                                return;
                            }
                            auto Plan=RaftSimBuildLiquidParticleRoutePlan(Graph,State->RouteParentCells,State->RouteRegions,
                                State->RouteLower,State->RouteAxisX,State->RouteAxisY,State->RouteSpacing,State->ExchangeError);
                            Plan.ResidualOuterBoundary=FParse::Param(FCommandLine::Get(),TEXT("RaftSimRegionalResidualBoundary"));
                            for (const auto& P:State->Packet)
                                if (P.IdentityOffsets!=State->Packet[0].IdentityOffsets || P.PositionOffset!=State->Packet[0].PositionOffset ||
                                    P.StepStartOffset!=State->Packet[0].StepStartOffset)
                                    State->ExchangeError=TEXT("Native handoff particle layout differs across owners");
                            if (State->ExchangeError.IsEmpty())
                            {
                                auto& Handoff=State->Handoffs[State->FirstGroups-2];
                                Handoff.NativeStep=State->FirstGroups;
                                FRaftSimLiquidParticleExitPlan ExitPlan;TArray<float> Volumes;
                                if(State->RetirementRequested)
                                {
                                    ExitPlan=State->RetirementProfile.ExitPlan(Graph,Plan,State->ExchangeError);
                                    for(const auto& Packet:State->Packet) Volumes.Add(float(Packet.Volume));
                                    if(!ExitPlan.FaceRows) return;
                                    const bool InitializeTrace=!State->FirstExitRejection;
                                    if(InitializeTrace)
                                    {
                                        auto Desc=FRDGBufferDesc::CreateStructuredDesc(4,RaftSimLiquidExitTraceWords);Desc.Usage|=BUF_SourceCopy;
                                        State->FirstExitRejection=AllocatePooledBuffer(Desc,TEXT("LiquidExit.FirstRejectedParticle"));
                                    }
                                    ExitPlan.FirstRejectionTrace=Graph.RegisterExternalBuffer(State->FirstExitRejection);
                                    if(InitializeTrace) AddClearUAVPass(Graph,Graph.CreateUAV(ExitPlan.FirstRejectionTrace),0);
                                    ExitPlan.NativeStep=State->FirstGroups;
                                }
                                Handoff.Issue(Graph,State->Dispatch,State->Contexts,Plan,
                                    State->Packet[0].PositionOffset,State->Packet[0].IdentityOffsets.W,State->ExchangeError,
                                    State->Lifetime,State->TickToken,State->RetirementRequested?&ExitPlan:nullptr,State->Packet[0].StepStartOffset,Volumes,
                                    !State->CompactHandoff || State->FullAuditStep==int32(State->FirstGroups),
                                    State->DenseRequested?TConstArrayView<uint32>(State->RegionalReservations):TConstArrayView<uint32>());
                            }
                        }
                        if(State->HandoffRequested && Aligned && Relevant[0].Last && State->ExchangeError.IsEmpty())
                            State->Lifetime.EndStep(State->TickToken,State->ExchangeError);
                        if (!State->DenseRequested && State->Groups.Num()>=8192) return;
                        auto J=MakeShared<FJsonObject>();
                        if(State->HandoffRequested) J->SetStringField(TEXT("simulation_generation"),State->Lifetime.GetGeneration().ToString(EGuidFormats::DigitsWithHyphens));
                        J->SetBoolField(TEXT("complete"),Full);J->SetBoolField(TEXT("aligned"),Aligned);
                        TArray<TSharedPtr<FJsonValue>> Entries;
                        for (const auto& S:Relevant)
                        {
                            auto E=MakeShared<FJsonObject>();E->SetNumberField(TEXT("owner"),State->Systems.Find(S.SystemId));
                            E->SetStringField(TEXT("name"),S.StageName.ToString());E->SetNumberField(TEXT("stage"),S.StageIndex);
                            E->SetNumberField(TEXT("iteration"),S.Iteration);E->SetNumberField(TEXT("iterations"),S.Iterations);
                            E->SetNumberField(TEXT("loop"),S.Loop);E->SetNumberField(TEXT("loops"),S.Loops);
                            E->SetBoolField(TEXT("first"),S.First);E->SetBoolField(TEXT("reset"),S.Reset);
                            E->SetBoolField(TEXT("last"),S.Last);
                            E->SetNumberField(TEXT("native_rate_spawns"),S.RateSpawns);E->SetNumberField(TEXT("native_event_spawns"),S.EventSpawns);
                            Entries.Add(MakeShared<FJsonValueObject>(E));
                        }
                        J->SetArrayField(TEXT("entries"),Entries);
                        if(State->DenseRequested)
                        {
                            if(!State->Journal.Add(GFrameNumberRenderThread,Ordinal,J))
                                State->ExchangeError=TEXT("Lossless stage journal exceeded its retained evidence budget");
                        }
                        else
                        {
                            J->SetNumberField(TEXT("render_frame"),GFrameNumberRenderThread);J->SetNumberField(TEXT("graph_group"),Ordinal);
                            State->Groups.Add(MakeShared<FJsonValueObject>(J));
                        }
                    });
            });
            FlushRenderingCommands();Started=true;
            UE_LOG(LogTemp,Display,TEXT("%d-region %d-particle stage probe active; no full-flow/visual/performance acceptance"),Regions.Num(),State->PacketRequested?(4-int32(State->EmptyReceiver))*State->PacketPerOwner:0);
        }
        else if (Args.Num()==1 && Args[0]==TEXT("emit") && Probe && (Probe->EmissionRequested || Probe->DenseRequested) && !Probe->EmissionActivated)
        {
            FlushRenderingCommands();
            if (!Probe->FirstGroups || !Probe->ExchangeError.IsEmpty()) return;
            if(Probe->DenseRequested)
            {
                for(int32 I=0;I<Probe->Components.Num();++I)
                    Probe->Components[I]->SetVariableFloat(TEXT("User.Inlet Particle Rate"),float(Probe->PreparedSpawnRates[I]));
            }
            else
            {
                const int32 Owner=Probe->RegionIds.Find(1);
                if (Owner==INDEX_NONE || !Probe->Components[Owner].IsValid()) return;
                Probe->Components[Owner]->SetVariableFloat(TEXT("User.Inlet Particle Rate"),60.f);
            }
            Probe->EmissionStartStep=Probe->FirstGroups;Probe->EmissionActivated=true;
        }
        else if (Args.Num()==2 && Args[0]==TEXT("status") && Probe)
        {
            const FString Path=FPaths::ConvertRelativePathToFull(Args[1]);
            const FString Root=FPaths::ConvertRelativePathToFull(FPaths::ProjectDir()/TEXT("../docs/reconstruction-review-2026-09-07"));
            if (!FPaths::IsUnderDirectory(Path,Root) || FPaths::GetCleanFilename(Path)!=TEXT("live-status.json")) return;
            FlushRenderingCommands();
            auto J=MakeShared<FJsonObject>();
            J->SetBoolField(TEXT("packet_captured"),Probe->PacketCaptured);
            J->SetNumberField(TEXT("native_neighbor_view_refreshes"),Probe->NeighborViewRefreshes);
            J->SetNumberField(TEXT("native_steps"),Probe->FirstGroups);
            J->SetStringField(TEXT("error"),Probe->ExchangeError);
            FString Text;auto Writer=TJsonWriterFactory<>::Create(&Text);
            FJsonSerializer::Serialize(J,Writer);FFileHelper::SaveStringToFile(Text,*Path);
        }
        else if (Args.Num()==2 && Args[0]==TEXT("stop") && Probe)
        {
            const FString Path=FPaths::ConvertRelativePathToFull(Args[1]);
            const FString Root=FPaths::ConvertRelativePathToFull(FPaths::ProjectDir()/TEXT("../docs/reconstruction-review-2026-09-07"));
            if (!FPaths::IsUnderDirectory(Path,Root) || FPaths::FileExists(Path)) return;
            auto State=Probe;
            // capture_scene enqueues render work. Finish that work before
            // reading the RT-owned capture flag; otherwise a requested late
            // step can complete during readback after the GT skipped Save.
            FlushRenderingCommands();
            TArray<TSharedPtr<FJsonValue>> PacketRecords;bool PacketSaved=false;
            TSharedPtr<FJsonObject> AssemblyRecord;
            TSharedPtr<FJsonObject> HandoffRecord;
            TArray<TSharedPtr<FJsonValue>> HandoffHistory;
            TSharedPtr<FJsonObject> FirstExitRejectionRecord;
            TSharedPtr<FJsonObject> InterfaceRecord;
            if(State->InterfaceRequested)
            {
                ENQUEUE_RENDER_COMMAND(RaftSimInterfaceSave)([State,&InterfaceRecord,Directory=FPaths::GetPath(Path)](FRHICommandListImmediate& Cmd)
                {
                    FString SaveError;
                    if(!State->Interface.Save(Cmd,Directory,InterfaceRecord,SaveError) && State->ExchangeError.IsEmpty()) State->ExchangeError=SaveError;
                });
                FlushRenderingCommands();
            }
            if(State->FirstExitRejection)
            {
                ENQUEUE_RENDER_COMMAND(RaftSimFirstExitRejectionSave)([State,&FirstExitRejectionRecord](FRHICommandListImmediate& Cmd)
                {
                    constexpr uint32 Bytes=RaftSimLiquidExitTraceWords*4;
                    FRHIGPUBufferReadback Read(TEXT("LiquidExit.FirstRejectedParticleReadback"));
                    Cmd.Transition(FRHITransitionInfo(State->FirstExitRejection->GetRHI(),ERHIAccess::Unknown,ERHIAccess::CopySrc));
                    Read.EnqueueCopy(Cmd,State->FirstExitRejection->GetRHI(),Bytes);Cmd.SubmitAndBlockUntilGPUIdle();
                    const auto* Data=static_cast<const uint32*>(Read.Lock(Bytes));
                    if(!Data) { State->ExchangeError=TEXT("First exit rejection readback failed");return; }
                    TArray<TSharedPtr<FJsonValue>> Values;
                    for(uint32 I=0;I<RaftSimLiquidExitTraceWords;++I) Values.Add(MakeShared<FJsonValueNumber>(Data[I]));
                    Read.Unlock();FirstExitRejectionRecord=MakeShared<FJsonObject>();
                    FirstExitRejectionRecord->SetStringField(TEXT("schema"),TEXT("raftsim.liquid_exit_first_rejection.v1"));
                    FirstExitRejectionRecord->SetStringField(TEXT("simulation_generation"),State->Lifetime.GetGeneration().ToString(EGuidFormats::DigitsWithHyphens));
                    FirstExitRejectionRecord->SetNumberField(TEXT("retained_bytes"),Bytes);
                    FirstExitRejectionRecord->SetArrayField(TEXT("words"),Values);
                });
                FlushRenderingCommands();
            }
            if (State->PacketRequested && !State->PacketCaptured && State->ExchangeError.IsEmpty())
                State->ExchangeError=TEXT("Requested native P2G step has not completed at stop");
            if (State->PacketCaptured)
            {
                ENQUEUE_RENDER_COMMAND(RaftSimNativePacketSave)([State,&PacketRecords,&PacketSaved,&AssemblyRecord,&HandoffRecord,&HandoffHistory,Directory=FPaths::GetPath(Path)](FRHICommandListImmediate& Cmd)
                {
                    PacketSaved=true;
                    if (State->HandoffRequested)
                        for (int32 I=0;I<State->Handoffs.Num();++I)
                        {
                            const FString Subdir=I==0?TEXT(""):FString::Printf(TEXT("commit-%03d"),I+1);
                            const FString Target=Subdir.IsEmpty()?Directory:Directory/Subdir;
                            IFileManager::Get().MakeDirectory(*Target,true);
                            TSharedPtr<FJsonObject> Record;
                            if (!State->Handoffs[I].Save(Cmd,Target,Record,State->ExchangeError)) { PacketSaved=false;break; }
                            Record->SetStringField(TEXT("snapshot_directory"),Subdir);
                            if (I==0) HandoffRecord=Record;
                            HandoffHistory.Add(MakeShared<FJsonValueObject>(Record));
                        }
                    if (State->AssemblyRequested && !State->Assembly.Save(Cmd,Directory,AssemblyRecord,State->ExchangeError)) PacketSaved=false;
                    for (const auto& Sample:State->Packet)
                    {
                        TSharedPtr<FJsonObject> Record;
                        if (!Sample.Save(Cmd,Directory,Record,State->ExchangeError)) { PacketSaved=false;break; }
                        if(State->ProjectionPacketRequested && !State->ProjectionPackets[Sample.RegionId].Save(Cmd,Directory,Sample.RegionId,Sample.Cells,State->PacketStep,Record,State->ExchangeError))
                        { PacketSaved=false;break; }
                        if(State->AdvectionPacketRequested && !State->AdvectionPackets[Sample.RegionId].Save(Cmd,Directory,Sample.RegionId,State->PacketStep,Record,State->ExchangeError))
                        { PacketSaved=false;break; }
                        PacketRecords.Add(MakeShared<FJsonValueObject>(Record));
                    }
                });
                FlushRenderingCommands();
            }
            TArray<TArray<float>> OutletPressurePixels;bool OutletPressureValid=false;
            if (State->ParentExterior)
            {
                for (const auto Size:State->Sizes) OutletPressurePixels.AddDefaulted_GetRef().SetNumUninitialized(Size.X*Size.Y*Size.Z);
                ENQUEUE_RENDER_COMMAND(RaftSimRegionalOutletPressureReadback)([State,&OutletPressurePixels,&OutletPressureValid](FRHICommandListImmediate& Cmd)
                {
                    OutletPressureValid=true;
                    for (int32 I=0;I<State->Sizes.Num() && OutletPressureValid;++I)
                    {
                        const auto Size=State->Sizes[I];
                        const auto* Data=State->Pressure[I]->SystemInstancesToProxyData_RT.Find(State->Systems[I]);
                        if (!Data || !Data->CurrentData || !Data->CurrentData->IsValid() || Data->NumCells!=Size)
                        { OutletPressureValid=false;break; }
                        auto* T=Data->CurrentData->GetPooledTexture()->GetRHI();
                        if (T->GetDesc().Format!=PF_R32_FLOAT) { OutletPressureValid=false;break; }
                        Cmd.Transition(FRHITransitionInfo(T,ERHIAccess::Unknown,ERHIAccess::CopySrc));
                        for (int32 Z=0;Z<Size.Z;++Z)
                        {
                            FRHIGPUTextureReadback Read(TEXT("RegionalFinalOutletPressure"));
                            Read.EnqueueCopy(Cmd,T,FIntVector(0,0,Z),0,FIntVector(Size.X,Size.Y,1));
                            Cmd.SubmitAndBlockUntilGPUIdle();int32 Pitch=0;
                            const auto* Values=static_cast<const float*>(Read.Lock(Pitch));
                            if (!Values || Pitch<Size.X) { if (Values) Read.Unlock();OutletPressureValid=false;break; }
                            for (int32 Y=0;Y<Size.Y;++Y)
                                FMemory::Memcpy(OutletPressurePixels[I].GetData()+(Z*Size.Y+Y)*Size.X,Values+Y*Pitch,Size.X*sizeof(float));
                            Read.Unlock();
                        }
                    }
                });
                FlushRenderingCommands();
            }
            TArray<TArray<float>> MarkerPixels;bool MarkerValid=false;
            if (State->MarkerCaptured)
            {
                for (const auto Size:State->Sizes) MarkerPixels.AddDefaulted_GetRef().SetNumUninitialized(Size.X*Size.Y*Size.Z);
                ENQUEUE_RENDER_COMMAND(RaftSimRegionalMarkerReadback)([State,&MarkerPixels,&MarkerValid](FRHICommandListImmediate& Cmd)
                {
                    int32 ReadCount=0;MarkerValid=true;
                    for (const auto& Slice:State->MarkerSlices)
                    {
                        if (!Slice.Readback->IsReady()) { MarkerValid=false;break; }
                        const auto Size=State->Sizes[Slice.Owner];int32 Pitch=0;
                        const auto* Values=static_cast<const float*>(Slice.Readback->Lock(Pitch));
                        if (!Values || Pitch<Size.X) { if (Values) Slice.Readback->Unlock();MarkerValid=false;break; }
                        for (int32 Y=0;Y<Size.Y;++Y)
                            FMemory::Memcpy(MarkerPixels[Slice.Owner].GetData()+(Slice.Z*Size.Y+Y)*Size.X,Values+Y*Pitch,Size.X*sizeof(float));
                        Slice.Readback->Unlock();++ReadCount;
                    }
                    MarkerValid &= ReadCount==State->Sizes.Num()*State->Sizes[0].Z;
                });
                FlushRenderingCommands();
            }
            TArray<TArray<FFloat16Color>> BoundaryPixels;bool BoundaryReadbackValid=true;
            if (State->ContactInstalled)
            {
                BoundaryPixels.SetNum(State->Sizes.Num());
                ENQUEUE_RENDER_COMMAND(RaftSimRegionalBoundaryReadback)([State,&BoundaryPixels,&BoundaryReadbackValid](FRHICommandListImmediate& Cmd)
                {
                    for (int32 I=0;I<State->Sizes.Num();++I)
                    {
                        const auto S=State->Sizes[I];
                        const auto* Data=State->Boundary[I]->SystemInstancesToProxyData_RT.Find(State->Systems[I]);
                        if (!Data || !Data->CurrentData || !Data->CurrentData->IsValid() || Data->NumCells!=S)
                        { BoundaryReadbackValid=false;break; }
                        auto* T=Data->CurrentData->GetPooledTexture()->GetRHI();const auto& D=T->GetDesc();
                        if (D.Format!=PF_FloatRGBA || D.Extent!=FIntPoint(S.X,S.Y) || D.Depth!=S.Z)
                        { BoundaryReadbackValid=false;break; }
                        Cmd.Read3DSurfaceFloatData(T,FIntRect(0,0,S.X,S.Y),FIntPoint(0,S.Z),BoundaryPixels[I]);
                        if (BoundaryPixels[I].Num()!=S.X*S.Y*S.Z) { BoundaryReadbackValid=false;break; }
                    }
                });
                FlushRenderingCommands();
            }
            StopProbe();
            auto J=MakeShared<FJsonObject>();J->SetArrayField(TEXT("groups"),State->Groups);
            J->SetObjectField(TEXT("native_dataset"),State->Dataset.Evidence);
            if(State->DenseRequested) J->SetObjectField(TEXT("stage_journal"),State->Journal.Json());
            TArray<TSharedPtr<FJsonValue>> OutletPressureFiles;
            if (OutletPressureValid)
                for (int32 I=0;I<OutletPressurePixels.Num();++I)
                {
                    const FString Name=FString::Printf(TEXT("pressure-final-%03d.r32f"),State->RegionIds[I]);
                    const FString File=FPaths::GetPath(Path)/Name;
                    TArray<uint8> Bytes;Bytes.Append(reinterpret_cast<const uint8*>(OutletPressurePixels[I].GetData()),OutletPressurePixels[I].Num()*sizeof(float));
                    if (FPaths::FileExists(File) || !FFileHelper::SaveArrayToFile(Bytes,*File)) { OutletPressureValid=false;break; }
                    auto P=MakeShared<FJsonObject>();P->SetNumberField(TEXT("region_id"),State->RegionIds[I]);P->SetStringField(TEXT("file"),Name);
                    P->SetNumberField(TEXT("voxel_count"),OutletPressurePixels[I].Num());OutletPressureFiles.Add(MakeShared<FJsonValueObject>(P));
                }
            J->SetBoolField(TEXT("outlet_pressure_readback_valid"),OutletPressureValid && OutletPressureFiles.Num()==State->Sizes.Num());
            J->SetArrayField(TEXT("outlet_pressure_readbacks"),OutletPressureFiles);
            TArray<TSharedPtr<FJsonValue>> MarkerFiles;
            if (MarkerValid)
                for (int32 I=0;I<MarkerPixels.Num();++I)
                {
                    const FString Name=FString::Printf(TEXT("pressure-first-color-%03d.r32f"),State->RegionIds[I]);
                    const FString File=FPaths::GetPath(Path)/Name;
                    TArray<uint8> Bytes;Bytes.Append(reinterpret_cast<const uint8*>(MarkerPixels[I].GetData()),MarkerPixels[I].Num()*sizeof(float));
                    if (FPaths::FileExists(File) || !FFileHelper::SaveArrayToFile(Bytes,*File)) { MarkerValid=false;break; }
                    auto P=MakeShared<FJsonObject>();P->SetNumberField(TEXT("region_id"),State->RegionIds[I]);P->SetStringField(TEXT("file"),Name);
                    P->SetNumberField(TEXT("voxel_count"),MarkerPixels[I].Num());MarkerFiles.Add(MakeShared<FJsonValueObject>(P));
                }
            J->SetBoolField(TEXT("nonzero_pressure_marker_requested"),State->MarkerRequested);
            J->SetBoolField(TEXT("nonzero_pressure_marker_seeded"),State->MarkerSeeded);
            J->SetBoolField(TEXT("nonzero_pressure_marker_readback_valid"),MarkerValid && MarkerFiles.Num()==State->Sizes.Num());
            J->SetArrayField(TEXT("pressure_marker_readbacks"),MarkerFiles);
            TArray<TSharedPtr<FJsonValue>> BoundaryFiles;
            if (State->ContactInstalled && BoundaryReadbackValid)
                for (int32 I=0;I<BoundaryPixels.Num();++I)
                {
                    const FString Name=FString::Printf(TEXT("boundary-%03d.rgba16f"),State->RegionIds[I]);
                    const FString File=FPaths::GetPath(Path)/Name;
                    TArray<uint8> Bytes;Bytes.Append(reinterpret_cast<const uint8*>(BoundaryPixels[I].GetData()),BoundaryPixels[I].Num()*sizeof(FFloat16Color));
                    if (FPaths::FileExists(File) || !FFileHelper::SaveArrayToFile(Bytes,*File)) { BoundaryReadbackValid=false;break; }
                    auto B=MakeShared<FJsonObject>();B->SetNumberField(TEXT("region_id"),State->RegionIds[I]);B->SetStringField(TEXT("file"),Name);
                    B->SetNumberField(TEXT("voxel_count"),BoundaryPixels[I].Num());BoundaryFiles.Add(MakeShared<FJsonValueObject>(B));
                }
            J->SetArrayField(TEXT("boundary_readbacks"),BoundaryFiles);
            J->SetBoolField(TEXT("boundary_readback_valid"),State->ContactInstalled && BoundaryReadbackValid && BoundaryFiles.Num()==State->Sizes.Num());
            J->SetNumberField(TEXT("complete_aligned_groups"),State->Complete);J->SetNumberField(TEXT("incomplete_groups"),State->Incomplete);
            J->SetNumberField(TEXT("misaligned_groups"),State->Misaligned);J->SetNumberField(TEXT("pressure_groups"),State->PressureGroups);
            J->SetNumberField(TEXT("first_stage_groups"),State->FirstGroups);J->SetBoolField(TEXT("zero_water"),!State->PacketRequested);
            J->SetBoolField(TEXT("native_transfer_packet_requested"),State->PacketRequested);
            J->SetNumberField(TEXT("native_transfer_packet_step"),State->PacketStep);
            J->SetBoolField(TEXT("native_projection_packet_requested"),State->ProjectionPacketRequested);
            J->SetBoolField(TEXT("native_advection_packet_requested"),State->AdvectionPacketRequested);
            J->SetBoolField(TEXT("native_compatible_transport_requested"),FParse::Param(FCommandLine::Get(),TEXT("RaftSimRegionalCompatibleTransport")));
            J->SetBoolField(TEXT("native_unified_transport_requested"),State->Interface.CompactTransport);
            J->SetBoolField(TEXT("native_high_order_interface_requested"),State->Interface.HighOrder);
            J->SetBoolField(TEXT("native_advection_velocity_halo_exchange"),State->Interface.CompactTransport);
            J->SetNumberField(TEXT("advection_velocity_halo_dispatches"),State->AdvectionVelocityExchanges);
            J->SetBoolField(TEXT("native_interface_transport_requested"),State->InterfaceRequested);
            if(InterfaceRecord) J->SetObjectField(TEXT("native_interface_transport"),InterfaceRecord);
            J->SetNumberField(TEXT("native_transfer_packet_per_owner"),State->PacketPerOwner);
            J->SetNumberField(TEXT("native_transfer_packet_speed"),State->PacketSpeed);
            J->SetBoolField(TEXT("native_particle_routes_requested"),State->RouteRequested);
            J->SetBoolField(TEXT("native_particle_assembly_requested"),State->AssemblyRequested);
            J->SetBoolField(TEXT("native_particle_handles_requested"),State->HandlesRequested);
            J->SetBoolField(TEXT("native_particle_handoff_requested"),State->HandoffRequested);
            J->SetStringField(TEXT("simulation_generation"),State->Lifetime.GetGeneration().ToString(EGuidFormats::DigitsWithHyphens));
            J->SetBoolField(TEXT("native_lifetime_failed"),State->Lifetime.IsFailed());
            J->SetNumberField(TEXT("native_lifetime_steps"),State->Lifetime.GetStep());
            TArray<TSharedPtr<FJsonValue>> LifetimeBirths;
            for(uint64 Count:State->Lifetime.GetBirths()) LifetimeBirths.Add(MakeShared<FJsonValueNumber>(double(Count)));
            J->SetArrayField(TEXT("native_lifetime_births"),LifetimeBirths);
            J->SetBoolField(TEXT("native_particle_retirement_requested"),State->RetirementRequested);
            J->SetBoolField(TEXT("native_compact_handoff_requested"),State->CompactHandoff);
            J->SetBoolField(TEXT("native_dense_requested"),State->DenseRequested);
            J->SetBoolField(TEXT("native_fixed_source_seed_requested"),State->FixedSourceSeed);
            J->SetBoolField(TEXT("native_stratified_source_requested"),FParse::Param(FCommandLine::Get(),TEXT("RaftSimRegionalStratifiedSource")));
            J->SetNumberField(TEXT("native_source_seed"),State->SourceSeed);
            TArray<TSharedPtr<FJsonValue>> SourceSeeds;
            for(int32 Seed:State->BoundSourceSeeds) SourceSeeds.Add(MakeShared<FJsonValueNumber>(Seed));
            J->SetArrayField(TEXT("native_bound_source_seeds"),SourceSeeds);
            J->SetStringField(TEXT("native_inlet_model"),TEXT("normal-relaxation-v1"));
            J->SetStringField(TEXT("native_physical_frame_model"),FParse::Param(FCommandLine::Get(),TEXT("RaftSimRegionalResidualBoundary"))?
                TEXT("double-float-residual-outer-v2"):TEXT("double-float-demote-v1"));
            J->SetStringField(TEXT("native_prescribed_normal_rounding"),TEXT("inward-representable-v1"));
            TArray<TSharedPtr<FJsonValue>> SourceScales;
            for(const FVector3f& Scale:State->BoundSourceScales)
            {
                TArray<TSharedPtr<FJsonValue>> XYZ;
                XYZ.Add(MakeShared<FJsonValueNumber>(Scale.X));XYZ.Add(MakeShared<FJsonValueNumber>(Scale.Y));
                XYZ.Add(MakeShared<FJsonValueNumber>(Scale.Z));SourceScales.Add(MakeShared<FJsonValueArray>(XYZ));
            }
            J->SetArrayField(TEXT("native_bound_source_scales"),SourceScales);
            J->SetNumberField(TEXT("native_full_diagnostic_step"),State->FullAuditStep);
            J->SetBoolField(TEXT("native_exact_exit_bed"),State->ExactExitBed);
            J->SetNumberField(TEXT("native_neighbor_view_refreshes"),State->NeighborViewRefreshes);
            TArray<TSharedPtr<FJsonValue>> SpawnRates,Reservations;
            for(double Rate:State->PreparedSpawnRates) SpawnRates.Add(MakeShared<FJsonValueNumber>(Rate));
            for(uint32 Limit:State->RegionalReservations) Reservations.Add(MakeShared<FJsonValueNumber>(Limit));
            J->SetArrayField(TEXT("prepared_spawn_rates"),SpawnRates);
            J->SetArrayField(TEXT("native_dispatch_reservations"),Reservations);
            J->SetBoolField(TEXT("native_empty_receiver_requested"),State->EmptyReceiver);
            J->SetBoolField(TEXT("native_emission_requested"),State->EmissionRequested);
            J->SetBoolField(TEXT("native_emission_activated"),State->EmissionActivated);
            J->SetNumberField(TEXT("native_emission_start_step"),State->EmissionStartStep);
            J->SetNumberField(TEXT("native_emission_rate"),State->EmissionRequested?60:0);
            if (HandoffRecord) J->SetObjectField(TEXT("native_particle_handoff"),HandoffRecord);
            J->SetNumberField(TEXT("native_particle_handoff_count"),State->HandoffCount);
            if (State->HandoffRequested) J->SetArrayField(TEXT("native_particle_handoff_history"),HandoffHistory);
            if(FirstExitRejectionRecord) J->SetObjectField(TEXT("first_exit_rejection"),FirstExitRejectionRecord);
            if (AssemblyRecord) J->SetObjectField(TEXT("native_particle_assembly"),AssemblyRecord);
            J->SetBoolField(TEXT("native_transfer_packet_saved"),PacketSaved && PacketRecords.Num()==State->Sizes.Num());
            J->SetArrayField(TEXT("native_transfer_packet"),PacketRecords);
            J->SetBoolField(TEXT("shared_pressure_or_particle_transfer_verified"),false);
            J->SetNumberField(TEXT("pressure_halo_dispatches"),State->Exchanges);
            J->SetNumberField(TEXT("region_count"),State->Sizes.Num());
            J->SetBoolField(TEXT("canonical_regional_contact_installed"),State->ContactInstalled);
            J->SetBoolField(TEXT("regional_compatible_projection_installed"),State->ProjectionInstalled);
            if(State->ProjectionInstalled)
            {
                J->SetStringField(TEXT("pressure_relaxation_model"),TEXT("parent-anisotropic-parity-box-v1"));
                TArray<TSharedPtr<FJsonValue>> Omegas;
                for(double Omega:State->PressureOmegas) Omegas.Add(MakeShared<FJsonValueNumber>(Omega));
                J->SetArrayField(TEXT("pressure_relaxation_omegas"),Omegas);
            }
            J->SetBoolField(TEXT("shared_boundary_exchange_enabled"),State->BoundaryExchange);
            J->SetNumberField(TEXT("boundary_halo_dispatches"),State->BoundaryExchanges);
            J->SetBoolField(TEXT("conservative_transfer_enabled"),State->TransferEnabled);
            J->SetNumberField(TEXT("raw_transfer_reductions"),State->TransferReductions);
            J->SetBoolField(TEXT("parent_exterior_forcing_installed"),State->ParentExterior);
            TArray<TSharedPtr<FJsonValue>> RegionIds,Columns;
            for (const int32 Id:State->RegionIds) RegionIds.Add(MakeShared<FJsonValueNumber>(Id));
            for (const auto& C:State->Copies)
            {
                TArray<TSharedPtr<FJsonValue>> Row;
                for (const int32 V:{State->RegionIds[C.SourceOwner],State->RegionIds[C.DestinationOwner],
                    C.Source.X,C.Source.Y,C.Destination.X,C.Destination.Y}) Row.Add(MakeShared<FJsonValueNumber>(V));
                Columns.Add(MakeShared<FJsonValueArray>(Row));
            }
            J->SetArrayField(TEXT("region_ids"),RegionIds);J->SetArrayField(TEXT("halo_columns_niagara"),Columns);
            J->SetNumberField(TEXT("shared_columns"),State->Copies.Num());
            J->SetStringField(TEXT("exchange_error"),State->ExchangeError);
            const uint32 RetainedGroups=State->DenseRequested?State->Journal.Records.Num():State->Groups.Num();
            J->SetBoolField(TEXT("records_truncated"),State->Journal.Failed || State->Complete+State->Incomplete+State->Misaligned!=RetainedGroups);
            J->SetBoolField(TEXT("empty_regional_exchange_dispatched"),State->Exchanges>0 && State->ExchangeError.IsEmpty());
            J->SetBoolField(TEXT("scheduler_alignment_observed"),State->Complete>0 && State->PressureGroups>0 && State->Incomplete==0 && State->Misaligned==0);
            FString Text;FJsonSerializer::Serialize(J,TJsonWriterFactory<>::Create(&Text));FFileHelper::SaveStringToFile(Text,*Path);
            StopProbe();
        }
    }));
}
