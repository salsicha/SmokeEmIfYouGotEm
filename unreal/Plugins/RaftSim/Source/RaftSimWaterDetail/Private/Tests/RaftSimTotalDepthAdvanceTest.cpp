#include "Misc/AutomationTest.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "RaftSimTotalDepthAdvanceGPU.h"
#include "RenderGraphUtils.h"
#include "RenderingThread.h"
#include "RHIGPUReadback.h"
#include <limits>

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_COMPLEX_AUTOMATION_TEST(FTotalDepthAdvanceTest,"RaftSim.WaterDetail.TotalDepthAdvanceGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
void FTotalDepthAdvanceTest::GetTests(TArray<FString>& Names,TArray<FString>& Commands) const
{
    // Each stress case gets a new automation frame so transient descriptors
    // recycle. Keep every assertion, including the original direct control.
    for(int32 Case=0;Case<8;++Case)
    {Names.Add(FString::Printf(TEXT("Case%d"),Case));Commands.Add(FString::FromInt(Case));}
    Names.Add(TEXT("InvalidDescriptors"));Commands.Add(TEXT("descriptors"));
}
bool FTotalDepthAdvanceTest::RunTest(const FString& Parameters)
{
    if(GUsingNullRHI){AddError(TEXT("Actual GPU required"));return false;}
    const bool Continuous=FParse::Param(FCommandLine::Get(),TEXT("RaftSimContinuousShorelineTest"));
    const bool Unscaled=FParse::Param(FCommandLine::Get(),TEXT("RaftSimUnscaledShorelineTest"));
    if(Continuous && Unscaled){AddError(TEXT("Choose one shoreline model"));return false;}
    AddInfo(FString::Printf(TEXT("immutable continuous shoreline model%d"),Continuous));
    bool Passed=true;FString Error;TArray<FString> Records;
    ENQUEUE_RENDER_COMMAND(TotalDepthAdvanceVerification)([&](FRHICommandListImmediate& Cmd)
    {
        const FIntPoint Size(17,13);const int32 N=Size.X*Size.Y;
        TArray<FVector4f> Initial;TArray<float> Bed,Fraction,BadFraction;
        Bed.Init(0,N);Fraction.Init(1,N);BadFraction.Init(std::numeric_limits<float>::quiet_NaN(),N);
        for(int32 I=0;I<N;++I){float H=1.f+.1f*FMath::Sin(float(I%Size.X));Initial.Add(FVector4f(H,.2f*H,.1f*H,.125f));}
        struct FResult{TArray<FVector4f> State;FVector4f Progress=FVector4f(0,0,0,0);uint32 Summary[4]{},Diagnostics[4]{};};
        for(int32 Case=0;Case<8;++Case)
        {
            if(Parameters!=FString::FromInt(Case))continue;
            TArray<FVector4f> InitialProgress;InitialProgress.Add(FVector4f(1048576.f,0,(Case==0 || Case==6)?.02f:.004f,.004f));
            if(Case==3){InitialProgress[0].Z=.02f;InitialProgress[0].W=.001f;}
            if(Case==4){InitialProgress[0].Z=0;InitialProgress[0].W=0;}
            if(Case==7)InitialProgress[0].Z=-1;
            const int32 Limit=Case==3?1:Case==5?3:16;
            auto Run=[&](int32 Batch,FResult& Result,bool Cull=true)
            {
                TRefCountPtr<FRDGPooledBuffer> State,Progress,Summary,Diagnostics;int32 Calls=0;
                // At least four scheduled slots, split across graph lifetimes or batched.
                // Then another graph tests that terminal status really latches.
                const int32 ScheduledGraphs=FMath::DivideAndRoundUp(4,Batch);
                for(int32 GraphIndex=0;GraphIndex<ScheduledGraphs+1;++GraphIndex)
                {
                    FRDGBuilder Graph(Cmd);const bool Last=GraphIndex==ScheduledGraphs;
                    auto S=State?Graph.RegisterExternalBuffer(State):CreateStructuredBuffer(Graph,TEXT("AdvanceTest.InitialState"),Initial);
                    auto P=Progress?Graph.RegisterExternalBuffer(Progress):CreateStructuredBuffer(Graph,TEXT("AdvanceTest.InitialProgress"),InitialProgress);
                    auto B=CreateStructuredBuffer(Graph,TEXT("AdvanceTest.Bed"),Bed);
                    auto F=CreateStructuredBuffer(Graph,TEXT("AdvanceTest.Fraction"),Fraction);
                    auto Bad=CreateStructuredBuffer(Graph,TEXT("AdvanceTest.BadFraction"),BadFraction);
                    auto SelectFraction=[&](FRDGBuilder&,FRDGBufferRef,const FRaftSimTotalDepthTransportResult&)
                    {
                        ++Calls;
                        const bool Fault=(Case==1 && Calls==2) || (Case==2 && Calls==1) ||
                            (Case==5 && Calls%2==0) || (Case==6 && Calls==3);
                        return Fault?Bad:F;
                    };
                    auto R=RaftSimAdvanceTotalDepthGPU(Graph,S,B,P,
                        Summary?Graph.RegisterExternalBuffer(Summary):nullptr,
                        Diagnostics?Graph.RegisterExternalBuffer(Diagnostics):nullptr,
                        Size,.5f,true,true,Last?1:Batch,Limit,SelectFraction,Error,{},nullptr,Cull,{},Continuous,Unscaled);
                    if(!R.State){Passed=false;Graph.Execute();return;}
                    FRHIGPUBufferReadback SR(TEXT("AdvanceTest.StateRead")),PR(TEXT("AdvanceTest.ProgressRead")),
                        CR(TEXT("AdvanceTest.SummaryRead")),DR(TEXT("AdvanceTest.DiagnosticsRead"));
                    if(Last)
                    {
                        AddEnqueueCopyPass(Graph,&SR,R.State,N*16);AddEnqueueCopyPass(Graph,&PR,R.Progress,16);
                        AddEnqueueCopyPass(Graph,&CR,R.Summary,16);AddEnqueueCopyPass(Graph,&DR,R.Diagnostics,16);
                    }
                    Graph.QueueBufferExtraction(R.State,&State);Graph.QueueBufferExtraction(R.Progress,&Progress);
                    Graph.QueueBufferExtraction(R.Summary,&Summary);Graph.QueueBufferExtraction(R.Diagnostics,&Diagnostics);
                    Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle();
                    if(Last)
                    {
                        const void* A=SR.Lock(N*16);const void* Clock=PR.Lock(16);const void* Counts=CR.Lock(16);const void* Flags=DR.Lock(16);
                        if(!A || !Clock || !Counts || !Flags){Passed=false;return;}
                        Result.State.SetNumUninitialized(N);FMemory::Memcpy(Result.State.GetData(),A,N*16);
                        FMemory::Memcpy(&Result.Progress,Clock,16);FMemory::Memcpy(Result.Summary,Counts,16);FMemory::Memcpy(Result.Diagnostics,Flags,16);
                        SR.Unlock();PR.Unlock();CR.Unlock();DR.Unlock();
                    }
                }
            };
            FResult Split{},Batch{},Direct{};Run(1,Split);Run(4,Batch);Run(4,Direct,false);
            if(Split.State.Num()!=N || Batch.State.Num()!=N || Direct.State.Num()!=N){Passed=false;return;}
            const bool DirectExact=FMemory::Memcmp(Direct.State.GetData(),Batch.State.GetData(),N*16)==0 &&
                FMemory::Memcmp(&Direct.Progress,&Batch.Progress,16)==0 &&
                FMemory::Memcmp(Direct.Summary,Batch.Summary,16)==0 && FMemory::Memcmp(Direct.Diagnostics,Batch.Diagnostics,16)==0;
            Passed &= DirectExact;
            Records.Add(FString::Printf(TEXT("advance case%d indirect/direct four-record exact%d"),Case,DirectExact));
            Passed &= FMemory::Memcmp(Split.State.GetData(),Batch.State.GetData(),N*16)==0 &&
                FMemory::Memcmp(&Split.Progress,&Batch.Progress,16)==0 &&
                FMemory::Memcmp(Split.Summary,Batch.Summary,16)==0 && FMemory::Memcmp(Split.Diagnostics,Batch.Diagnostics,16)==0;
            FResult Wide{};Run(RaftSimMaxTotalDepthTrialsPerGraph,Wide);
            const bool WideExact=Wide.State.Num()==N && FMemory::Memcmp(Split.State.GetData(),Wide.State.GetData(),N*16)==0 &&
                FMemory::Memcmp(&Split.Progress,&Wide.Progress,16)==0 &&
                FMemory::Memcmp(Split.Summary,Wide.Summary,16)==0 && FMemory::Memcmp(Split.Diagnostics,Wide.Diagnostics,16)==0;
            Passed &= WideExact;
            Records.Add(FString::Printf(TEXT("advance case%d sixteen-slot state/clock/counters/rejection exact%d"),Case,WideExact));
            const uint32 ExpectedTrials[]={3,3,1,1,0,3,2,1};
            const uint32 ExpectedAccepted[]={3,2,0,1,0,0,1,0};
            const uint32 ExpectedStatus[]={1,1,2,4,1,4,2,2};
            Passed &= Split.Summary[0]==ExpectedTrials[Case] && Split.Summary[1]==ExpectedAccepted[Case] &&
                Split.Summary[2]==ExpectedStatus[Case] && Split.Summary[3]==RaftSimTotalDepthEvolutionMode(false,Continuous,Unscaled);
            if(ExpectedAccepted[Case]==0)
            {
                Passed &= FMemory::Memcmp(Split.State.GetData(),Initial.GetData(),N*16)==0;
                Passed &= Split.Progress.X==InitialProgress[0].X && Split.Progress.Y==InitialProgress[0].Y && Split.Progress.Z==InitialProgress[0].Z;
            }
            else
            {
                double V0=0,V1=0,Change=0,F0=0,F1=0,FChange=0;
                for(int32 I=0;I<N;++I)
                {
                    const auto& A=Split.State[I];V0+=Initial[I].X;V1+=A.X;Change+=FMath::Abs(A.X-Initial[I].X);
                    Passed &= FMath::IsFinite(A.X) && FMath::IsFinite(A.Y) && FMath::IsFinite(A.Z) && FMath::IsFinite(A.W) && A.X>=0 && A.W>=0;
                    F0+=Initial[I].W;F1+=A.W;FChange+=FMath::Abs(A.W-Initial[I].W);
                }
                Passed &= Change>0 && FMath::Abs(V1-V0)<1e-5*V0;
                Passed &= FChange>0 && FMath::Abs(F1-F0)<2e-6*F0;
                const double Elapsed=double(Split.Progress.X)-InitialProgress[0].X+Split.Progress.Y;
                const double ExpectedElapsed=Case==0?.02f:Case==3?.001f:.004f;
                Passed &= FMath::Abs(Elapsed-ExpectedElapsed)<1e-8;
            }
            if(ExpectedStatus[Case]==1)Passed &= Split.Progress.Z==0;
            if(Case==2 || Case==6)Passed &= Split.Diagnostics[0]!=0 && Split.Diagnostics[3]==0 && Split.Progress.W==0;
            if(Case==5)Passed &= Split.Diagnostics[1]!=0 && Split.Diagnostics[3]==0 && Split.Progress.W==.0005f;
            if(Case==7)Passed &= (Split.Diagnostics[0]&16u)!=0;
            Records.Add(FString::Printf(TEXT("advance case%d trials%u accepted%u status%u clock %.9g+%.9g remaining%.9g proposed%.9g diagnostics%u/%u/%u/%u"),
                Case,Split.Summary[0],Split.Summary[1],Split.Summary[2],Split.Progress.X,Split.Progress.Y,Split.Progress.Z,Split.Progress.W,
                Split.Diagnostics[0],Split.Diagnostics[1],Split.Diagnostics[2],Split.Diagnostics[3]));
        }
        if(Parameters!=TEXT("descriptors")){Error.Reset();return;}
        // Invalid host descriptors/budgets fail before scheduling trials.
        FRDGBuilder InvalidGraph(Cmd);auto S=CreateStructuredBuffer(InvalidGraph,TEXT("AdvanceTest.InvalidState"),Initial);
        auto B=CreateStructuredBuffer(InvalidGraph,TEXT("AdvanceTest.InvalidBed"),Bed);
        TArray<FVector4f> Clock;Clock.Add(FVector4f(0,0,.004f,.004f));
        auto P=CreateStructuredBuffer(InvalidGraph,TEXT("AdvanceTest.InvalidProgress"),Clock);
        auto F=CreateStructuredBuffer(InvalidGraph,TEXT("AdvanceTest.InvalidFraction"),Fraction);
        int32 Calls=0;auto Callback=[&](FRDGBuilder&,FRDGBufferRef,const FRaftSimTotalDepthTransportResult&){++Calls;return F;};
        for(int32 Budget:{0,RaftSimMaxTotalDepthTrialsPerGraph+1})
        {FString E;Passed &= !RaftSimAdvanceTotalDepthGPU(InvalidGraph,S,B,P,nullptr,nullptr,Size,.5f,true,true,Budget,16,Callback,E).State && !E.IsEmpty();}
        for(int32 Limit:{0,4097})
        {FString E;Passed &= !RaftSimAdvanceTotalDepthGPU(InvalidGraph,S,B,P,nullptr,nullptr,Size,.5f,true,true,1,Limit,Callback,E).State && !E.IsEmpty();}
        {FString E;Passed &= !RaftSimAdvanceTotalDepthGPU(InvalidGraph,S,B,P,F,nullptr,Size,.5f,true,true,1,16,Callback,E).State && !E.IsEmpty();}
        for(FIntPoint BadSize:{FIntPoint(0,13),FIntPoint(17,-1),FIntPoint(513,13),FIntPoint(17,514)})
        {FString E;Passed &= !RaftSimAdvanceTotalDepthGPU(InvalidGraph,S,B,P,nullptr,nullptr,BadSize,.5f,true,true,1,16,Callback,E).State && !E.IsEmpty();}
        {FString E;Passed &= !RaftSimAdvanceTotalDepthGPU(InvalidGraph,B,B,P,nullptr,nullptr,Size,.5f,true,true,1,16,Callback,E).State && !E.IsEmpty();}
        {FString E;Passed &= !RaftSimAdvanceTotalDepthGPU(InvalidGraph,S,S,P,nullptr,nullptr,Size,.5f,true,true,1,16,Callback,E).State && !E.IsEmpty();}
        Passed &= Calls==0;InvalidGraph.Execute();
    });
    FlushRenderingCommands();TestTrue(TEXT("Bounded GPU advance is graph-partition invariant, preserves rejected state and latches terminal status"),Passed);
    for(const auto& R:Records)AddInfo(R);if(!Error.IsEmpty())AddError(Error);return !HasAnyErrors();
}
#endif
