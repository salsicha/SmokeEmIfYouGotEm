#include "Misc/AutomationTest.h"
#include "RaftSimTotalDepthIntervalGPU.h"
#include "RenderGraphUtils.h"
#include "RenderingThread.h"
#include "RHIGPUReadback.h"
#include <limits>
#include <cmath>

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FTotalDepthIntervalTest,"RaftSim.WaterDetail.TotalDepthIntervalGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FTotalDepthIntervalTest::RunTest(const FString&)
{
    if(GUsingNullRHI){AddError(TEXT("Actual GPU required"));return false;}
    bool Passed=true;TArray<FString> Records;
    ENQUEUE_RENDER_COMMAND(TotalDepthIntervalVerification)([&](FRHICommandListImmediate& Cmd)
    {
        const FIntPoint Size(3,2);const int32 N=6,NB=10;
        TArray<FVector4f> Initial,Ledger;
        for(int32 I=0;I<N;++I)Initial.Add(FVector4f(1+.125f*I,.25f,-.125f,.0625f*I));
        for(int32 I=0;I<NB;++I)Ledger.Add(FVector4f(.125f*I,-.25f*I,.5f*I,.0625f*I));
        for(int32 Model:{0,1,2})for(int32 Case=0;Case<22;++Case)
        {
            const bool Continuous=Model==1,Unscaled=Model==2;
            FRDGBuilder Graph(Cmd);FString Error;
            auto Upload=[&](const auto& A,const TCHAR* Name){return CreateStructuredBuffer(Graph,Name,MakeArrayView(A));};
            TArray<FVector4f> Clock={FVector4f(3,.125f,0,0)};
            TArray<uint32> Counts={7,5,1,1},Flags={0,0,0,1};
            double Start=3.125;
            // Valid open/closed, noncanonical and very long clocks; failures
            // cover unfinished/failed transactions, mismatched instant/mode,
            // corrupted counters/flags, and a one-float-ULP low-word difference.
            if(Case==1)Counts[3]=0;
            if(Case==2){Clock[0].X=100000000;Start=100000000.125;}
            if(Case==3){Counts[2]=0;Clock[0].Z=.001f;}
            if(Case==4)Counts[2]=2;
            if(Case==5)Counts[2]=4;
            if(Case==6)Start+=.0625;
            if(Case==7)Flags[0]=1;
            if(Case==8)Clock[0].X=std::numeric_limits<float>::quiet_NaN();
            if(Case==9)Counts[3]=0;
            if(Case==10)Counts[1]=8;
            if(Case==11)Flags[3]=2;
            if(Case==12)Clock[0].Y=std::nextafter(Clock[0].Y,1.f);
            if(Case==13){Clock[0].X=3.125f;Clock[0].Y=0;}
            if(Case==14)Clock[0].W=-.001f;
            if(Case==15)Counts[0]=4097;
            if(Case==16)Flags[3]=0;
            if(Case==17){Counts[1]=0;Flags[3]=0;}
            if(Case==18){Counts[0]=0;Counts[1]=0;Flags[3]=0;}
            if(Case==19)Clock[0].W=.1f;
            Counts[3]|=RaftSimTotalDepthEvolutionMode(false,Continuous,Unscaled);
            // Both other models must be refused at the next interval.
            if(Case>=20)Counts[3]=(Counts[3]&1u)|RaftSimTotalDepthEvolutionMode(false,(Model+Case-19)%3==1,(Model+Case-19)%3==2);
            FRaftSimTotalDepthAdvanceResult P;
            P.State=Upload(Initial,TEXT("IntervalTest.State"));P.Progress=Upload(Clock,TEXT("IntervalTest.Clock"));
            P.Summary=Upload(Counts,TEXT("IntervalTest.Summary"));P.Diagnostics=Upload(Flags,TEXT("IntervalTest.Diagnostics"));
            if(Case!=1)P.BoundaryVolume=Upload(Ledger,TEXT("IntervalTest.Ledger"));
            auto R=RaftSimBeginNextTotalDepthIntervalGPU(Graph,P,Size,Start,Start+.015625,Error,Continuous,Unscaled);
            if(!R.Progress || !Error.IsEmpty()){Passed=false;Graph.Execute();continue;}
            Passed &= R.State==P.State && R.BoundaryVolume==P.BoundaryVolume;
            FRHIGPUBufferReadback PR(TEXT("IntervalTest.PR")),SR(TEXT("IntervalTest.SR")),DR(TEXT("IntervalTest.DR"));
            AddEnqueueCopyPass(Graph,&PR,R.Progress,16);AddEnqueueCopyPass(Graph,&SR,R.Summary,16);AddEnqueueCopyPass(Graph,&DR,R.Diagnostics,16);
            Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle();
            auto* CP=static_cast<const FVector4f*>(PR.Lock(16));auto* CS=static_cast<const uint32*>(SR.Lock(16));
            auto* CD=static_cast<const uint32*>(DR.Lock(16));
            if(!CP || !CS || !CD){Passed=false;continue;}
            const bool Valid=Case<3 || Case==13 || Case==18;
            bool OK=FMemory::Memcmp(CP,&Clock[0],8)==0;
            if(Valid)
                OK &= CP->Z==.015625f && CP->W==1.f/120.f && CS[0]==0 && CS[1]==0 && CS[2]==0 && CS[3]==Counts[3] &&
                    (CD[0]|CD[1]|CD[2]|CD[3])==0;
            else
                OK &= FMemory::Memcmp(CP,&Clock[0],16)==0 && CS[0]==Counts[0] && CS[1]==Counts[1] && CS[2]==2 &&
                    CS[3]==Counts[3] && CD[0]==Flags[0] && CD[1]==Flags[1] && CD[2]==(Flags[2]|64u) && CD[3]==0;
            Passed &= OK;Records.Add(FString::Printf(TEXT("interval case%d expected-admit%d passed%d status%u flags%u"),Case,Valid,OK,CS[2],CD[2]));
            PR.Unlock();SR.Unlock();DR.Unlock();
        }
        FRDGBuilder Graph(Cmd);FString Error;
        TArray<FVector4f> Clock={FVector4f(0,0,0,0)};TArray<uint32> Counts={1,1,1,0},Flags={0,0,0,1};
        FRaftSimTotalDepthAdvanceResult P;
        P.State=CreateStructuredBuffer(Graph,TEXT("IntervalTest.InvalidState"),Initial);
        P.Progress=CreateStructuredBuffer(Graph,TEXT("IntervalTest.InvalidClock"),Clock);
        P.Summary=CreateStructuredBuffer(Graph,TEXT("IntervalTest.InvalidSummary"),Counts);
        P.Diagnostics=CreateStructuredBuffer(Graph,TEXT("IntervalTest.InvalidDiagnostics"),Flags);
        for(double End:{0.,-1.,.1,std::numeric_limits<double>::infinity()})
            Passed &= !RaftSimBeginNextTotalDepthIntervalGPU(Graph,P,Size,0,End,Error).State && !Error.IsEmpty();
        auto Incomplete=P;Incomplete.Diagnostics=nullptr;
        Passed &= !RaftSimBeginNextTotalDepthIntervalGPU(Graph,Incomplete,Size,0,.125,Error).State && !Error.IsEmpty();
        Passed &= !RaftSimBeginNextTotalDepthIntervalGPU(Graph,P,FIntPoint(513,2),0,.125,Error).State && !Error.IsEmpty();
        Graph.Execute();
    });
    FlushRenderingCommands();
    for(const auto& R:Records)AddInfo(R);
    TestTrue(TEXT("Consecutive interval admits only complete exact-time records and never resets interior or ledger"),Passed);
    return !HasAnyErrors();
}
#endif
