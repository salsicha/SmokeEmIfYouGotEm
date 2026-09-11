#include "Misc/AutomationTest.h"
#include "RaftSimLiquidParticleRoutingGPU.h"
#include "RenderGraphUtils.h"
#include "RenderingThread.h"
#include "RHIGPUReadback.h"
#include "Containers/ResourceArray.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLiquidRoutingTest,"RaftSim.Editor.LiquidParticleRoutingGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FLiquidRoutingTest::RunTest(const FString&)
{
    if (GUsingNullRHI || GMaxRHIFeatureLevel<ERHIFeatureLevel::SM5)
    { AddError(TEXT("Actual GPU required for native particle routing"));return false; }
    constexpr uint32 Capacity=8,Stride=16,Floats=5,Ints=3;
    TResourceArray<uint32> FloatWords,IntWords;
    FloatWords.SetAllowCPUAccess(true);IntWords.SetAllowCPUAccess(true);
    FloatWords.SetNumZeroed(Stride*Floats);IntWords.SetNumZeroed(Stride*Ints);
    const FVector3f Positions[Capacity]={{25,25,0},{225,25,0},{25,225,0},{225,225,0},
        {-1,50,0},{400,400,10},{0,0,0},{200,200,0}};
    for (uint32 I=0;I<Capacity;++I)
    {
        FloatWords[I]=0x80000000u; // Signed zero and non-position NaN payload must survive unchanged.
        FloatWords[4*Stride+I]=0x7fc01234u+I;
        for (uint32 C=0;C<3;++C) { const float Value=Positions[I][C];FMemory::Memcpy(&FloatWords[(C+1)*Stride+I],&Value,4); }
        IntWords[I]=16777217u+I;IntWords[Stride+I]=0x80000000u+I;IntWords[2*Stride+I]=0xffffffffu-I;
    }
    FloatWords[Stride+6]=0x7fc01234u; // Invalid position, distinct from a valid particle with NaN auxiliary data.
    bool Passed=false;
    ENQUEUE_RENDER_COMMAND(RaftSimLiquidRoutingTest)([&](FRHICommandListImmediate& Cmd)
    {
        FRWBuffer NativeFloats,NativeInts,NativeCounts;
        NativeFloats.Initialize(Cmd,TEXT("RouteNativeFloats"),4,FloatWords.Num(),PF_R32_FLOAT,ERHIAccess::SRVCompute,BUF_Static,&FloatWords);
        NativeInts.Initialize(Cmd,TEXT("RouteNativeInts"),4,IntWords.Num(),PF_R32_SINT,ERHIAccess::SRVCompute,BUF_Static,&IntWords);
        const uint32 Live[3]={7,0,10};TResourceArray<uint32> Counts;Counts.Append(Live,3);
        NativeCounts.Initialize(Cmd,TEXT("RouteNativeCounts"),4,3,PF_R32_UINT,ERHIAccess::UAVCompute,BUF_Static,&Counts);
        FRDGBuilder Graph(Cmd);FString Error;
        const TArray<FIntRect> Regions={{0,0,4,4},{4,0,8,4},{0,4,4,8},{4,4,8,8}};
        auto Plan=RaftSimBuildLiquidParticleRoutePlan(Graph,{8,8},Regions,FVector::ZeroVector,
            FVector::XAxisVector,FVector::YAxisVector,{50,50},Error);
        if (!Plan.Bounds || !Error.IsEmpty()) { Graph.Execute();return; }
        TRefCountPtr<FRDGPooledBuffer> Words[3],Routes[3],Totals[3];
        for (uint32 C=0;C<3;++C)
        {
            auto Packet=RaftSimStageLiquidParticleRoutes(Graph,Plan,2,NativeFloats.SRV,NativeInts.SRV,NativeCounts.UAV,
                C,Stride,Stride,Floats,Ints,0,1,Capacity,Error);
            if (!Packet.Words || !Error.IsEmpty()) { Graph.Execute();return; }
            Graph.QueueBufferExtraction(Packet.Words,&Words[C]);Graph.QueueBufferExtraction(Packet.Routes,&Routes[C]);
            Graph.QueueBufferExtraction(Packet.Counts,&Totals[C]);
        }
        auto BadRegions=Regions;BadRegions[3]=Regions[0];
        if (RaftSimBuildLiquidParticleRoutePlan(Graph,{8,8},BadRegions,FVector::ZeroVector,
                FVector::XAxisVector,FVector::YAxisVector,{50,50},Error).Bounds ||
            RaftSimStageLiquidParticleRoutes(Graph,Plan,2,NativeFloats.SRV,NativeInts.SRV,NativeCounts.UAV,
                0,Stride,Stride,Floats,Ints,1,1,Capacity,Error).Words ||
            RaftSimStageLiquidParticleRoutes(Graph,Plan,2,NativeFloats.SRV,NativeInts.SRV,NativeCounts.UAV,
                0,Capacity-1,Stride,Floats,Ints,0,1,Capacity,Error).Words ||
            RaftSimStageLiquidParticleRoutes(Graph,Plan,2,NativeFloats.SRV,NativeInts.SRV,NativeCounts.UAV,
                0,Stride,Stride,Floats,Ints,0,3,Capacity,Error).Words)
        { Graph.Execute();return; }
        Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle();
        for (uint32 C=0;C<3;++C)
        {
            FRHIGPUBufferReadback W(TEXT("RouteWords")),R(TEXT("RouteDestinations")),T(TEXT("RouteTotals"));
            for (auto* B:{Words[C].GetReference(),Routes[C].GetReference(),Totals[C].GetReference()})
                Cmd.Transition(FRHITransitionInfo(B->GetRHI(),ERHIAccess::Unknown,ERHIAccess::CopySrc));
            W.EnqueueCopy(Cmd,Words[C]->GetRHI(),Capacity*(Floats+Ints)*4);
            R.EnqueueCopy(Cmd,Routes[C]->GetRHI(),Capacity*16);T.EnqueueCopy(Cmd,Totals[C]->GetRHI(),7*4);
            Cmd.SubmitAndBlockUntilGPUIdle();
            const auto* Out=static_cast<const uint32*>(W.Lock(Capacity*(Floats+Ints)*4));
            const auto* Dest=static_cast<const FUintVector4*>(R.Lock(Capacity*16));
            const auto* Sum=static_cast<const uint32*>(T.Lock(7*4));
            if (!Out || !Dest || !Sum) return;
            bool Exact=true;uint32 ExpectedCounts[7]={0,0,0,0,0,Live[C]>Capacity?Live[C]-Capacity:0,Live[C]};
            const uint32 ExpectedOwners[Capacity]={0,1,2,3,MAX_uint32,3,MAX_uint32,3};
            for (uint32 I=0;I<Capacity;++I)
            {
                const bool Active=I<Live[C];
                for(uint32 A=0;A<Floats+Ints;++A)
                {
                    const uint32 Expected=Active?(A<Floats?FloatWords[A*Stride+I]:IntWords[(A-Floats)*Stride+I]):0;
                    Exact &= Out[A*Capacity+I]==Expected;
                }
                const uint32 Status=!Active?0:I==4?2:I==6?4:1;
                const FUintVector4 Expected(Active?ExpectedOwners[I]:MAX_uint32,2,I,Status);
                Exact &= FMemory::Memcmp(&Dest[I],&Expected,16)==0;
                if(Active) ++ExpectedCounts[Status==1?ExpectedOwners[I]:Status==2?4:5];
            }
            Exact &= FMemory::Memcmp(Sum,ExpectedCounts,sizeof(ExpectedCounts))==0;
            W.Unlock();R.Unlock();T.Unlock();if(!Exact) return;
        }
        Passed=true;
    });
    FlushRenderingCommands();
    TestTrue(TEXT("Full native payload bits, physical ownership, exact outer edge, nonfinite/exterior records, empty/overflow accounting and rejected unsupported ABI"),Passed);
    return Passed;
}
