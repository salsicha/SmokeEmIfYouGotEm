#include "Misc/AutomationTest.h"
#include "RaftSimLiquidParticleExitGPU.h"
#include "RenderGraphUtils.h"
#include "RenderingThread.h"
#include "RHIGPUReadback.h"
#include "Containers/ResourceArray.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLiquidRetirementTest,"RaftSim.Editor.LiquidParticleRetirementGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FLiquidRetirementTest::RunTest(const FString&)
{
    if(GUsingNullRHI || GMaxRHIFeatureLevel<ERHIFeatureLevel::SM5) { AddError(TEXT("Actual GPU required"));return false; }
    bool Passed=false;
    ENQUEUE_RENDER_COMMAND(RaftSimLiquidRetirementTest)([&](FRHICommandListImmediate& Cmd)
    {
        constexpr uint32 Capacity=3,NF=6,NI=4,Components=NF+NI,IDCapacity=4,Sentinel=0x13579bdf;
        // Mixed survivor/exit; all exit; forbidden face; corrupt count;
        // corrupt per-particle evidence caught after preflight.
        for(uint32 Mode=0;Mode<5;++Mode)
        {
            FRDGBuilder Graph(Cmd);FString Error;
            const TArray<FIntRect> Regions={{0,0,4,4},{4,0,8,4}};
            auto Routing=RaftSimBuildLiquidParticleRoutePlan(Graph,{8,4},Regions,FVector::ZeroVector,
                FVector::XAxisVector,FVector::YAxisVector,{50,50},Error);
            TArray<FVector3f> Rows;Rows.Init({0,100,-100},24);if(Mode==2) Rows[0].Z=100;
            auto Plan=RaftSimBuildLiquidParticleExitPlan(Graph,Routing,200,Rows,Error);
            TArray<FRaftSimLiquidParticleRoutePacket> Sources;
            TArray<FRaftSimLiquidParticleExitCandidates> Exits;
            TArray<TArray<uint32>> Inputs;
            TArray<TArray<FUintVector4>> InputRoutes;
            for(uint32 S=0;S<2;++S)
            {
                auto& W=Inputs.AddDefaulted_GetRef();W.Init(0,Capacity*Components);
                auto& Routes=InputRoutes.AddDefaulted_GetRef();TArray<uint32> Counts;Counts.Init(0,5);Counts[4]=Capacity;
                for(uint32 I=0;I<Capacity;++I)
                {
                    const bool Exit=Mode==1 || I==0;
                    const FVector3f A(Exit?(S?390:10):I==1?(S?300:100):(S?210:190),25+50*I,50);
                    const FVector3f B(Exit?(S?410:-10):I==1?A.X:(S?190:210),A.Y,A.Z);
                    for(uint32 C=0;C<3;++C)
                    {
                        const float End=B[C],Start=A[C];FMemory::Memcpy(&W[C*Capacity+I],&End,4);
                        FMemory::Memcpy(&W[(3+C)*Capacity+I],&Start,4);
                    }
                    W[NF*Capacity+I]=S;W[(NF+1)*Capacity+I]=I;W[(NF+2)*Capacity+I]=42;
                    W[(NF+3)*Capacity+I]=16777217+S*100+I;
                    const uint32 D=Exit?MAX_uint32:uint32(B.X>=200);
                    Routes.Emplace(D,S,I,Exit?2:1);++Counts[Exit?2:D];
                }
                FRaftSimLiquidParticleRoutePacket P;P.Capacity=Capacity;P.FloatComponents=NF;P.IntComponents=NI;
                P.Words=CreateStructuredBuffer(Graph,TEXT("Retirement.SourceWords"),TConstArrayView<uint32>(W));
                P.Routes=CreateStructuredBuffer(Graph,TEXT("Retirement.SourceRoutes"),TConstArrayView<FUintVector4>(Routes));
                P.Counts=CreateStructuredBuffer(Graph,TEXT("Retirement.SourceCounts"),TConstArrayView<uint32>(Counts));
                Sources.Add(P);
                auto E=RaftSimClassifyLiquidParticleExits(Graph,Plan,P,S,0,3,S?.02f:.01f,Error);
                if(!E.Records) { Graph.Execute();return; }
                if(Mode==3 && S==0)
                {
                    // Valid-shaped but dishonest totals must not bypass the GPU gate.
                    const TArray<uint32> Bad={2,1,0,0,0,0,0,4};
                    E.Counts=CreateStructuredBuffer(Graph,TEXT("Retirement.BadExitCounts"),TConstArrayView<uint32>(Bad));
                }
                if(Mode==4 && S==0)
                {
                    uint32 T;const float Half=.5f;FMemory::Memcpy(&T,&Half,4);
                    const TArray<FUintVector4> Bad={{2,0,0,T},{2,0,1,T},{1,MAX_uint32,MAX_uint32,0}};
                    E.Records=CreateStructuredBuffer(Graph,TEXT("Retirement.BadExitRecords"),TConstArrayView<FUintVector4>(Bad));
                }
                Exits.Add(E);
            }
            const TArray<uint32> Caps={Capacity,Capacity},IDs={IDCapacity,IDCapacity};
            auto Wrong=Exits;Wrong[0].SourceWords=Sources[1].Words;
            if(RaftSimAssembleLiquidParticleDestinations(Graph,Sources,Caps,Error,Wrong).Words)
            { Graph.Execute();return; }
            auto A=RaftSimAssembleLiquidParticleDestinations(Graph,Sources,Caps,Error,Exits);
            if(!A.Words || A.ExitParticleVolumesM3!=TArray<float>({.01f,.02f})) { Graph.Execute();return; }
            auto H=RaftSimPrepareLiquidParticleHandles(Graph,A,IDs,1,2,1,42,Error);
            if(!H.Handles) { Graph.Execute();return; }
            FRWBuffer NativeF[2],NativeI[2],NativeIDs[2],NativeCounts;
            TResourceArray<uint32> Initial;Initial.Init(Sentinel,2);
            NativeCounts.Initialize(Cmd,TEXT("Retirement.NativeCounts"),4,2,PF_R32_UINT,ERHIAccess::UAVCompute,BUF_Static|BUF_SourceCopy,&Initial);
            TArray<FRaftSimLiquidNativeParticleTarget> Targets;
            for(uint32 S=0;S<2;++S)
            {
                Initial.Init(Sentinel,Capacity*NF);
                NativeF[S].Initialize(Cmd,TEXT("Retirement.NativeFloats"),4,Initial.Num(),PF_R32_FLOAT,ERHIAccess::SRVMask,BUF_Static|BUF_SourceCopy,&Initial);
                Initial.Init(Sentinel,Capacity*NI);
                NativeI[S].Initialize(Cmd,TEXT("Retirement.NativeIntegers"),4,Initial.Num(),PF_R32_SINT,ERHIAccess::SRVMask,BUF_Static|BUF_SourceCopy,&Initial);
                Initial.Init(Sentinel,IDCapacity);
                NativeIDs[S].Initialize(Cmd,TEXT("Retirement.NativeIDs"),4,IDCapacity,PF_R32_SINT,ERHIAccess::SRVCompute,BUF_Static|BUF_SourceCopy,&Initial);
                auto& T=Targets.AddDefaulted_GetRef();T.Capacity=Capacity;T.FloatStride=Capacity;T.IntStride=Capacity;T.IDCapacity=IDCapacity;T.CountOffset=S;
                T.Floats=NativeF[S].UAV;T.Integers=NativeI[S].UAV;T.IDToIndex=NativeIDs[S].UAV;T.NativeCounts=NativeCounts.UAV;
            }
            if(!RaftSimCommitLiquidParticleAssembly(Graph,A,H,Targets,1,2,Error)) { Graph.Execute();return; }
            TArray<TRefCountPtr<FRDGPooledBuffer>> Saved;Saved.SetNum(11);
            const FRDGBufferRef Buffers[]={A.Words,A.References,A.Counts,A.Control,A.ExitWords,A.ExitReferences,A.ExitRecords,A.ExitCounts,H.Handles,H.IDToIndex,H.FreeCounts};
            for(int32 I=0;I<11;++I) Graph.QueueBufferExtraction(Buffers[I],&Saved[I]);
            Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle();
            auto Read=[&](FRHIBuffer* Buffer,uint32 Bytes,TArray<uint32>& Out)
            {
                FRHIGPUBufferReadback R(TEXT("Retirement.Read"));Cmd.Transition(FRHITransitionInfo(Buffer,ERHIAccess::Unknown,ERHIAccess::CopySrc));
                R.EnqueueCopy(Cmd,Buffer,Bytes);Cmd.SubmitAndBlockUntilGPUIdle();const auto* P=static_cast<const uint32*>(R.Lock(Bytes));
                if(!P) return false;Out.Append(P,Bytes/4);R.Unlock();return true;
            };
            TArray<TArray<uint32>> Values;Values.SetNum(11);
            for(int32 I=0;I<11;++I) if(!Read(Saved[I]->GetRHI(),Saved[I]->GetSize(),Values[I])) return;
            const bool Valid=Mode<2;
            if(Values[3][0]!=uint32(Valid) || Values[3][2]!=6 || Values[3][3]!=(Mode==1?6u:2u) ||
                (Valid?Values[3][1]!=0:(Values[3][1]&64)==0)) return;
            TArray<uint32> Counter;if(!Read(NativeCounts.Buffer,NativeCounts.NumBytes,Counter)) return;
            TSet<uint32> Seen;uint32 Retired=0,Kept=0;
            for(uint32 S=0;S<2;++S)
            {
                TArray<uint32> F,I,Lookup;
                if(!Read(NativeF[S].Buffer,NativeF[S].NumBytes,F) || !Read(NativeI[S].Buffer,NativeI[S].NumBytes,I) ||
                    !Read(NativeIDs[S].Buffer,NativeIDs[S].NumBytes,Lookup)) return;
                if(!Valid)
                {
                    if(Counter[S]!=Sentinel) return;
                    for(const auto* V:{&F,&I,&Lookup}) for(auto Word:*V) if(Word!=Sentinel) return;
                    continue;
                }
                const uint32 N=Values[2][S],E=Values[7][S*5+4];Kept+=N;Retired+=E;
                if(N!=(Mode==1?0u:2u) || E!=(Mode==1?3u:1u) || Counter[S]!=N || Values[10][S]!=IDCapacity-N) return;
                for(uint32 Face=0;Face<4;++Face) if(Values[7][S*5+Face]!=(Face==S?E:0)) return;
                for(uint32 J=0;J<IDCapacity;++J) if(Lookup[J]!=Values[9][S*IDCapacity+J]) return;
                for(uint32 Phase=0;Phase<2;++Phase) for(uint32 J=0;J<(Phase?E:N);++J)
                {
                    const uint32 Slot=S*Capacity+J;const auto& Refs=Values[Phase?5:1];const auto& Payload=Values[Phase?4:0];
                    const uint32 Owner=Refs[2*Slot],Index=Refs[2*Slot+1];
                    if(Owner>=2 || Index>=Capacity || Seen.Contains(Owner*Capacity+Index)) return;Seen.Add(Owner*Capacity+Index);
                    const auto Route=InputRoutes[Owner][Index];
                    if(Phase?(Owner!=S || Route.W!=2):(Route.X!=S || Route.W!=1)) return;
                    for(uint32 C=0;C<Components;++C) if(Payload[C*6+Slot]!=Inputs[Owner][C*Capacity+Index]) return;
                    if(Phase)
                    { if(Values[6][4*Slot]!=2 || Values[6][4*Slot+1]!=S) return; }
                    else
                    {
                        for(uint32 C=0;C<NF;++C) if(F[C*Capacity+J]!=Payload[C*6+Slot]) return;
                        for(uint32 C=0;C<NI;++C)
                        {
                            const uint32 Expected=C==1?Values[8][2*Slot]:C==2?Values[8][2*Slot+1]:Payload[(NF+C)*6+Slot];
                            if(I[C*Capacity+J]!=Expected) return;
                        }
                    }
                }
            }
            if(Valid && (Seen.Num()!=6 || Kept+Retired!=6)) return;
        }
        Passed=true;
    });
    FlushRenderingCommands();TestTrue(TEXT("Exact survivor/exit partition, all-exit empty native owners, identities/handles/free lists and atomic unchanged sinks on rejected or corrupt evidence"),Passed);
    return Passed;
}
