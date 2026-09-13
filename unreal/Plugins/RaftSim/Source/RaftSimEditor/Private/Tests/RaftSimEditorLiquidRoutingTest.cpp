#include "Misc/AutomationTest.h"
#include "RaftSimLiquidParticleRoutingGPU.h"
#include "RaftSimLiquidParticleExitGPU.h"
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
    constexpr uint32 Capacity=10,Stride=16,Floats=5,Ints=3;
    TResourceArray<uint32> FloatWords,IntWords;
    FloatWords.SetAllowCPUAccess(true);IntWords.SetAllowCPUAccess(true);
    FloatWords.SetNumZeroed(Stride*Floats);IntWords.SetNumZeroed(Stride*Ints);
    const FVector3f Positions[Capacity]={{25,25,0},{225,25,0},{25,4075,0},{225,4075,0},
        {-1,50,0},{400,8100,10},{0,0,0},{200,4050,0},
        {25,8100.00048828125f,0},{25,8099.99951171875f,0}};
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
        const uint32 Live[3]={9,0,12};TResourceArray<uint32> Counts;Counts.Append(Live,3);
        NativeCounts.Initialize(Cmd,TEXT("RouteNativeCounts"),4,3,PF_R32_UINT,ERHIAccess::UAVCompute,BUF_Static,&Counts);
        FRDGBuilder Graph(Cmd);FString Error;
        const TArray<FIntRect> Regions={{0,0,4,81},{4,0,8,81},{0,81,4,162},{4,81,8,162}};
        auto Plan=RaftSimBuildLiquidParticleRoutePlan(Graph,{8,162},Regions,FVector::ZeroVector,
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
        if (RaftSimBuildLiquidParticleRoutePlan(Graph,{8,162},BadRegions,FVector::ZeroVector,
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
            const uint32 ExpectedOwners[Capacity]={0,1,2,3,MAX_uint32,3,MAX_uint32,3,MAX_uint32,2};
            for (uint32 I=0;I<Capacity;++I)
            {
                const bool Active=I<Live[C];
                for(uint32 A=0;A<Floats+Ints;++A)
                {
                    const uint32 Expected=Active?(A<Floats?FloatWords[A*Stride+I]:IntWords[(A-Floats)*Stride+I]):0;
                    Exact &= Out[A*Capacity+I]==Expected;
                }
                const uint32 Status=!Active?0:(I==4 || I==8)?2:I==6?4:1;
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

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLiquidRotatedFrameTest,"RaftSim.Editor.LiquidRotatedPhysicalFrameGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FLiquidRotatedFrameTest::RunTest(const FString&)
{
    if(GUsingNullRHI || GMaxRHIFeatureLevel<ERHIFeatureLevel::SM5)
    { AddError(TEXT("Actual GPU required for rotated physical-frame regression"));return false; }
    bool AllPassed=true;
    for(bool Residual:{false,true})
    {
    // Exact captured float inputs, not the slightly different survey double frame.
    const FVector3f Lower(12080.8720703125f,312.3059387207031f,350.f);
    const FVector3f X(-0.929999828338623f,-0.36755993962287903f,0);
    const FVector3f Y(-0.36755993962287903f,0.929999828338623f,0);
    TArray<FVector3f> Points={{-12066.3134765625f,-5790.4296875f,647.559814453125f},
        {-12066.314453125f,-5790.42822265625f,647.55767822265625f},
        {-13401.5703125f,-2411.96533203125f,493.69671630859375f},
        {-13401.5693359375f,-2411.96533203125f,493.69671630859375f}};
    // Both sides of all four faces, at three tangential locations. The actual
    // float-stored point defines the expected result; no positional tolerance.
    for(int32 Face=0;Face<4;++Face) for(double T:{0.1,0.5,0.9}) for(double Offset:{-0.03,0.0,0.03})
    {
        FVector Local(24700*T,8300*T,100);
        Local[Face/2]=(Face%2 ? (Face<2 ? 24700.0:8300.0):0.0)+Offset;
        Points.Add(FVector3f(FVector(Lower)+FVector(X)*Local.X+FVector(Y)*Local.Y+FVector(0,0,Local.Z)));
    }
    const uint32 Capacity=Points.Num();
    TArray<uint32> Expected,ExpectedOwners;
    TResourceArray<uint32> Floats,Ints,Counts;
    Floats.SetNumZeroed(6*Capacity);Ints.SetNumZeroed(Capacity);Counts.Add(Capacity);
    for(uint32 I=0;I<Capacity;++I)
    {
        const FVector Delta=FVector(Points[I])-FVector(Lower);
        const double ExactA=FVector::DotProduct(Delta,FVector(X)),ExactB=FVector::DotProduct(Delta,FVector(Y));
        const double A=Residual?ExactA:static_cast<float>(ExactA);
        const double B=Residual?ExactB:static_cast<float>(ExactB);
        Expected.Add(A>=0 && A<=24700 && B>=0 && B<=8300 ? 1:2);
        ExpectedOwners.Add(Expected.Last()==1 ? (static_cast<float>(ExactA)<12350?0:1):MAX_uint32);
        for(uint32 C=0;C<3;++C) FMemory::Memcpy(&Floats[C*Capacity+I],&Points[I][C],4);
        const FVector3f Start=I==2?Points[I]-X:Points[I];
        for(uint32 C=0;C<3;++C) { const float Value=Start[C];FMemory::Memcpy(&Floats[(3+C)*Capacity+I],&Value,4); }
    }
    TestEqual(TEXT("Captured start is inside"),Expected[0],1u);
    TestEqual(TEXT("Captured endpoint is inside"),Expected[1],1u);
    TestEqual(TEXT("Tiny captured outward residual distinguishes the contracts"),Expected[2],Residual?2u:1u);
    TestEqual(TEXT("Adjacent representable point remains inside"),Expected[3],1u);
    bool Passed=false;
    ENQUEUE_RENDER_COMMAND(RaftSimRotatedPhysicalFrameTest)([&](FRHICommandListImmediate& Cmd)
    {
        FRWBuffer NativeFloats,NativeInts,NativeCounts;
        NativeFloats.Initialize(Cmd,TEXT("FrameFloats"),4,Floats.Num(),PF_R32_FLOAT,ERHIAccess::SRVCompute,BUF_Static,&Floats);
        NativeInts.Initialize(Cmd,TEXT("FrameInts"),4,Ints.Num(),PF_R32_SINT,ERHIAccess::SRVCompute,BUF_Static,&Ints);
        NativeCounts.Initialize(Cmd,TEXT("FrameCounts"),4,1,PF_R32_UINT,ERHIAccess::UAVCompute,BUF_Static,&Counts);
        FRDGBuilder Graph(Cmd);FString Error;
        const TArray<FIntRect> Regions={{0,0,247,166},{247,0,494,166}};
        // Production validates orthonormal doubles, then uploads float axes.
        // Normalizing here still rounds back to the exact captured GPU axes.
        auto Plan=RaftSimBuildLiquidParticleRoutePlan(Graph,{494,166},Regions,FVector(Lower),
            FVector(X).GetSafeNormal(),FVector(Y).GetSafeNormal(),{50,50},Error);
        Plan.ResidualOuterBoundary=Residual;
        if(!Plan.Bounds) { UE_LOG(LogTemp,Error,TEXT("Physical frame plan: %s"),*Error);Graph.Execute();return; }
        auto Packet=RaftSimStageLiquidParticleRoutes(Graph,Plan,0,NativeFloats.SRV,NativeInts.SRV,NativeCounts.UAV,
            0,Capacity,Capacity,6,1,0,0,Capacity,Error);
        if(!Packet.Routes || !Error.IsEmpty()) { UE_LOG(LogTemp,Error,TEXT("Physical frame packet: %s"),*Error);Graph.Execute();return; }
        TRefCountPtr<FRDGPooledBuffer> Routes;
        Graph.QueueBufferExtraction(Packet.Routes,&Routes);
        TArray<FVector3f> FaceRows;FaceRows.Init({350,1000,-100},2*(494+166));
        auto ExitPlan=RaftSimBuildLiquidParticleExitPlan(Graph,Plan,800,FaceRows,Error);
        auto Exit=RaftSimClassifyLiquidParticleExits(Graph,ExitPlan,Packet,0,0,3,1.f/48,Error);
        if(!Exit.Records || !Error.IsEmpty()) { Graph.Execute();return; }
        TRefCountPtr<FRDGPooledBuffer> ExitRecords;
        Graph.QueueBufferExtraction(Exit.Records,&ExitRecords);
        Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle();
        FRHIGPUBufferReadback Read(TEXT("RotatedPhysicalFrameRoutes"));
        Cmd.Transition(FRHITransitionInfo(Routes->GetRHI(),ERHIAccess::Unknown,ERHIAccess::CopySrc));
        Read.EnqueueCopy(Cmd,Routes->GetRHI(),Capacity*16);Cmd.SubmitAndBlockUntilGPUIdle();
        const auto* Data=static_cast<const FUintVector4*>(Read.Lock(Capacity*16));if(!Data) return;
        Passed=true;
        for(uint32 I=0;I<Capacity;++I)
        {
            const bool Match=Data[I].W==Expected[I] && Data[I].X==ExpectedOwners[I];
            if(!Match) UE_LOG(LogTemp,Error,TEXT("Physical frame residual%d point%u expected status%u owner%u got%u owner%u"),
                Residual,I,Expected[I],ExpectedOwners[I],Data[I].W,Data[I].X);
            Passed &= Match;
        }
        Read.Unlock();
        FRHIGPUBufferReadback ExitRead(TEXT("RotatedPhysicalFrameExits"));
        Cmd.Transition(FRHITransitionInfo(ExitRecords->GetRHI(),ERHIAccess::Unknown,ERHIAccess::CopySrc));
        ExitRead.EnqueueCopy(Cmd,ExitRecords->GetRHI(),Capacity*16);Cmd.SubmitAndBlockUntilGPUIdle();
        const auto* ExitData=static_cast<const FUintVector4*>(ExitRead.Lock(Capacity*16));
        if(!ExitData) { Passed=false;return; }
        Passed &= ExitData[2].X==(Residual?2u:1u);
        if(Residual)
        {
            float Fraction;FMemory::Memcpy(&Fraction,&ExitData[2].W,4);
            const FVector3f Start=Points[2]-X;
            const double A=FVector::DotProduct(FVector(Start)-FVector(Lower),FVector(X));
            const double B=FVector::DotProduct(FVector(Points[2])-FVector(Lower),FVector(X));
            const double ExactFraction=(24700-A)/(B-A);
            Passed &= ExitData[2].Y==1 && Fraction>0 && Fraction<=1 && FMath::Abs(Fraction-ExactFraction)<2e-7;
        }
        ExitRead.Unlock();
    });
    FlushRenderingCommands();
    TestTrue(TEXT("Captured false exit and true crossings on all four rotated physical faces"),Passed);
    AllPassed &= Passed;
    }
    return AllPassed;
}
