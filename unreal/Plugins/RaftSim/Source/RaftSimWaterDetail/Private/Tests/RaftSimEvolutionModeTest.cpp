#include "Misc/AutomationTest.h"
#include "RaftSimTotalDepthAdvanceGPU.h"
#include "RenderGraphUtils.h"
#include "RenderingThread.h"
#include "RHIGPUReadback.h"

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEvolutionModeTest,"RaftSim.WaterDetail.EvolutionModeGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FEvolutionModeTest::RunTest(const FString&)
{
    if(GUsingNullRHI){AddError(TEXT("Actual GPU required"));return false;}
    bool Passed=true;FString Error;
    ENQUEUE_RENDER_COMMAND(EvolutionModeVerification)([&](FRHICommandListImmediate& Cmd)
    {
        const FIntPoint Size(7,5);const int32 N=Size.X*Size.Y;
        TArray<FVector4f> Initial;TArray<float> Bed,Fraction;
        for(int32 I=0;I<N;++I)Initial.Add(FVector4f(1+.03125f*(I%7),.125f,.0625f,.015625f));
        Bed.Init(0,N);Fraction.Init(1,N);
        for(int32 Model:{0,1,2})for(int32 Other:{0,1,2})for(bool Completed:{false,true})
        {
            if(Model==Other)continue;
            const bool Continuous=Model==1,Unscaled=Model==2;
            FRDGBuilder Graph(Cmd);
            auto S=CreateStructuredBuffer(Graph,TEXT("Mode.State"),Initial);
            auto B=CreateStructuredBuffer(Graph,TEXT("Mode.Bed"),Bed);
            auto F=CreateStructuredBuffer(Graph,TEXT("Mode.Fraction"),Fraction);
            TArray<FVector4f> Clock={FVector4f(3,0,Completed?.00390625f:.015625f,.00390625f)};
            auto P=CreateStructuredBuffer(Graph,TEXT("Mode.Clock"),Clock);
            auto Select=[&](FRDGBuilder&,FRDGBufferRef,const FRaftSimTotalDepthTransportResult&){return F;};
            auto Before=RaftSimAdvanceTotalDepthGPU(Graph,S,B,P,nullptr,nullptr,Size,.5f,true,true,
                1,16,Select,Error,{},nullptr,true,{},Continuous,Unscaled);
            if(!Before.State){Passed=false;Graph.Execute();continue;}
            auto Refused=RaftSimAdvanceTotalDepthGPU(Graph,Before.State,B,Before.Progress,Before.Summary,Before.Diagnostics,
                Size,.5f,true,true,1,16,Select,Error,{},nullptr,true,{},Other==1,Other==2);
            if(!Refused.State){Passed=false;Graph.Execute();continue;}
            auto Latched=RaftSimAdvanceTotalDepthGPU(Graph,Refused.State,B,Refused.Progress,Refused.Summary,Refused.Diagnostics,
                Size,.5f,true,true,1,16,Select,Error,{},nullptr,true,{},Continuous,Unscaled);
            if(!Latched.State){Passed=false;Graph.Execute();continue;}
            FRHIGPUBufferReadback S0(TEXT("Mode.S0")),S1(TEXT("Mode.S1")),S2(TEXT("Mode.S2"));
            FRHIGPUBufferReadback P0(TEXT("Mode.P0")),P1(TEXT("Mode.P1")),P2(TEXT("Mode.P2"));
            FRHIGPUBufferReadback C0(TEXT("Mode.C0")),C1(TEXT("Mode.C1")),C2(TEXT("Mode.C2"));
            FRHIGPUBufferReadback D1(TEXT("Mode.D1")),D2(TEXT("Mode.D2"));
            AddEnqueueCopyPass(Graph,&S0,Before.State,N*16);AddEnqueueCopyPass(Graph,&S1,Refused.State,N*16);AddEnqueueCopyPass(Graph,&S2,Latched.State,N*16);
            AddEnqueueCopyPass(Graph,&P0,Before.Progress,16);AddEnqueueCopyPass(Graph,&P1,Refused.Progress,16);AddEnqueueCopyPass(Graph,&P2,Latched.Progress,16);
            AddEnqueueCopyPass(Graph,&C0,Before.Summary,16);AddEnqueueCopyPass(Graph,&C1,Refused.Summary,16);AddEnqueueCopyPass(Graph,&C2,Latched.Summary,16);
            AddEnqueueCopyPass(Graph,&D1,Refused.Diagnostics,16);AddEnqueueCopyPass(Graph,&D2,Latched.Diagnostics,16);
            Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle();
            auto Check=[&]()
            {
                const void* A=S0.Lock(N*16),*V=S1.Lock(N*16),*W=S2.Lock(N*16);
                const auto* Q0=static_cast<const FVector4f*>(P0.Lock(16));
                const auto* Q1=static_cast<const FVector4f*>(P1.Lock(16));
                const auto* Q2=static_cast<const FVector4f*>(P2.Lock(16));
                const auto* T0=static_cast<const uint32*>(C0.Lock(16));
                const auto* T1=static_cast<const uint32*>(C1.Lock(16));
                const auto* T2=static_cast<const uint32*>(C2.Lock(16));
                const auto* E1=static_cast<const uint32*>(D1.Lock(16));
                const auto* E2=static_cast<const uint32*>(D2.Lock(16));
                bool OK=A && V && W && Q0 && Q1 && Q2 && T0 && T1 && T2 && E1 && E2;
                if(OK)OK=FMemory::Memcmp(A,V,N*16)==0 && FMemory::Memcmp(A,W,N*16)==0 &&
                    FMemory::Memcmp(Q0,Q1,12)==0 && FMemory::Memcmp(Q1,Q2,16)==0 && Q1->W==0 &&
                    T0[0]==1 && T0[1]==1 && T0[2]==(Completed?1u:0u) &&
                    T1[0]==T0[0] && T1[1]==T0[1] && T1[2]==2 && T1[3]==RaftSimTotalDepthEvolutionMode(false,Continuous,Unscaled) &&
                    FMemory::Memcmp(T1,T2,16)==0 && E1[0]==0 && E1[1]==0 && E1[2]==32 && E1[3]==0 &&
                    FMemory::Memcmp(E1,E2,16)==0;
                if(A)S0.Unlock();if(V)S1.Unlock();if(W)S2.Unlock();
                if(Q0)P0.Unlock();if(Q1)P1.Unlock();if(Q2)P2.Unlock();
                if(T0)C0.Unlock();if(T1)C1.Unlock();if(T2)C2.Unlock();
                if(E1)D1.Unlock();if(E2)D2.Unlock();return OK;
            };
            Passed &= Check();
        }
    });
    FlushRenderingCommands();
    TestTrue(TEXT("All six ordered model switches reject pending/completed intervals, preserve state/time/counters and latch failure"),Passed);
    if(!Error.IsEmpty())AddError(Error);return !HasAnyErrors();
}
#endif
