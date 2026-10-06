#include "Misc/AutomationTest.h"
#include "RaftSimLiquidParticleRoutingGPU.h"
#include "RenderGraphUtils.h"
#include "RenderingThread.h"
#include "RHIGPUReadback.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLiquidAssemblyTest,"RaftSim.Editor.LiquidParticleAssemblyGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FLiquidAssemblyTest::RunTest(const FString&)
{
    if(GUsingNullRHI || GMaxRHIFeatureLevel<ERHIFeatureLevel::SM5)
    { AddError(TEXT("Actual GPU required for destination particle assembly"));return false; }
    bool Passed=false;
    ENQUEUE_RENDER_COMMAND(RaftSimLiquidAssemblyTest)([&](FRHICommandListImmediate& Cmd)
    {
        for(uint32 Mode=0;Mode<8;++Mode)
        {
            const uint32 Owners=Mode==7?16:2,Capacity=4,Components=5;
            FRDGBuilder Graph(Cmd);FString Error;
            TArray<FRaftSimLiquidParticleRoutePacket> Sources;
            TArray<TArray<uint32>> Inputs;TArray<TArray<FUintVector4>> InputRoutes;
            TArray<uint32> Capacities;Capacities.Init(Capacity,Owners);
            if(Mode==1) Capacities[0]=3;
            uint32 TotalLive=0;
            for(uint32 S=0;S<Owners;++S)
            {
                const uint32 N=Mode==5 || (Mode==6 && S==1)?0:Mode==7?1:3;
                TotalLive+=N;
                auto& W=Inputs.AddDefaulted_GetRef();W.Init(0,Capacity*Components);
                auto& R=InputRoutes.AddDefaulted_GetRef();R.Init(FUintVector4(MAX_uint32,S,0,0),Capacity);
                TArray<uint32> C;C.Init(0,Owners+3);C[Owners+2]=N;
                for(uint32 I=0;I<N;++I)
                {
                    const uint32 D=Mode==7?(S+1)%Owners:S==0?(I<2?1:0):0;
                    R[I]=FUintVector4(D,S,I,1);++C[D];
                    // Include all bits, not float-rounded numerical comparisons.
                    for(uint32 A=0;A<Components;++A) W[A*Capacity+I]=0x80000000u+S*1000+A*100+I;
                }
                if((Mode==2 || Mode==3) && S==0)
                { --C[R[2].X];R[2].X=MAX_uint32;R[2].W=Mode==2?2:4;++C[Owners+(Mode==3?1:0)]; }
                if(Mode==4 && S==0) R[0].Y=1;
                FRaftSimLiquidParticleRoutePacket P;
                P.Capacity=Mode==6 && S==1?0:Capacity;P.FloatComponents=3;P.IntComponents=2;
                P.Words=CreateStructuredBuffer(Graph,TEXT("AssemblyTest.SourceWords"),TConstArrayView<uint32>(W));
                P.Routes=CreateStructuredBuffer(Graph,TEXT("AssemblyTest.SourceRoutes"),TConstArrayView<FUintVector4>(R));
                P.Counts=CreateStructuredBuffer(Graph,TEXT("AssemblyTest.SourceCounts"),TConstArrayView<uint32>(C));
                Sources.Add(P);
            }
            auto Assembly=RaftSimAssembleLiquidParticleDestinations(Graph,Sources,Capacities,Error);
            if(!Assembly.Words || !Error.IsEmpty()) { Graph.Execute();return; }
            TRefCountPtr<FRDGPooledBuffer> Words,Refs,Counts,Control;
            Graph.QueueBufferExtraction(Assembly.Words,&Words);Graph.QueueBufferExtraction(Assembly.References,&Refs);
            Graph.QueueBufferExtraction(Assembly.Counts,&Counts);Graph.QueueBufferExtraction(Assembly.Control,&Control);
            auto Invalid=Sources;Invalid[0].IntComponents=3;
            if(RaftSimAssembleLiquidParticleDestinations(Graph,Invalid,Capacities,Error).Words)
            { Graph.Execute();return; }
            Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle();
            FRHIGPUBufferReadback WRead(TEXT("AssemblyWords")),RRead(TEXT("AssemblyRefs")),CRead(TEXT("AssemblyCounts")),GRead(TEXT("AssemblyControl"));
            for(auto* B:{Words.GetReference(),Refs.GetReference(),Counts.GetReference(),Control.GetReference()})
                Cmd.Transition(FRHITransitionInfo(B->GetRHI(),ERHIAccess::Unknown,ERHIAccess::CopySrc));
            const uint32 Slots=Assembly.TotalCapacity;
            WRead.EnqueueCopy(Cmd,Words->GetRHI(),Slots*Components*4);RRead.EnqueueCopy(Cmd,Refs->GetRHI(),Slots*8);
            CRead.EnqueueCopy(Cmd,Counts->GetRHI(),Owners*4);GRead.EnqueueCopy(Cmd,Control->GetRHI(),16);
            Cmd.SubmitAndBlockUntilGPUIdle();
            const auto* W=static_cast<const uint32*>(WRead.Lock(Slots*Components*4));
            const auto* R=static_cast<const FUintVector2*>(RRead.Lock(Slots*8));
            const auto* C=static_cast<const uint32*>(CRead.Lock(Owners*4));
            const auto* G=static_cast<const uint32*>(GRead.Lock(16));
            if(!W || !R || !C || !G) return;
            const uint32 ErrorBits=Mode==1?4:Mode==2?2:Mode==3?1:Mode==4?8:0;
            bool Exact=G[0]==uint32(ErrorBits==0) && G[1]==ErrorBits && G[2]==TotalLive && G[3]==uint32(Mode==2);
            if(ErrorBits==0)
            {
                TSet<uint32> Seen;uint32 Offset=0;
                for(uint32 D=0;D<Owners;++D)
                {
                    uint32 ExpectedCount=0;
                    for(const auto& RR:InputRoutes) for(const auto& Route:RR) if(Route.W==1 && Route.X==D) ++ExpectedCount;
                    Exact &= C[D]==ExpectedCount && C[D]<=Capacities[D];
                    for(uint32 I=0;I<C[D] && I<Capacities[D];++I)
                    {
                        const auto Ref=R[Offset+I];
                        if(Ref.X>=Owners || Ref.Y>=Capacity) { Exact=false;continue; }
                        const uint32 Key=Ref.X*Capacity+Ref.Y;
                        Exact &= !Seen.Contains(Key);Seen.Add(Key);
                        Exact &= InputRoutes[Ref.X][Ref.Y].X==D && InputRoutes[Ref.X][Ref.Y].W==1;
                        for(uint32 A=0;A<Components;++A) Exact &= W[A*Slots+Offset+I]==Inputs[Ref.X][A*Capacity+Ref.Y];
                    }
                    Offset+=Capacities[D];
                }
                Exact &= uint32(Seen.Num())==TotalLive;
            }
            else if(Mode!=4) // Preflight failure must publish no payload at all.
            {
                for(uint32 I=0;I<Slots*Components;++I) Exact &= W[I]==0;
                for(uint32 D=0;D<Owners;++D) Exact &= C[D]==0;
            }
            WRead.Unlock();RRead.Unlock();CRead.Unlock();GRead.Unlock();if(!Exact) return;
        }
        Passed=true;
    });
    FlushRenderingCommands();
    TestTrue(TEXT("Lossless all-owner receiving buffers; transactional capacity/exterior/invalid rejection; corrupt route rejection; empty/unallocated owners and sixteen-owner exchange"),Passed);
    return Passed;
}
