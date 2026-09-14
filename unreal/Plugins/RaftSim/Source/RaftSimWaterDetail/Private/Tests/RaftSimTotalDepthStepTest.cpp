#include "Misc/AutomationTest.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/FileHelper.h"
#include "Serialization/MemoryReader.h"
#include "RaftSimTotalDepthStepGPU.h"
#include "RenderGraphUtils.h"
#include "RenderingThread.h"
#include "RHIGPUReadback.h"
#include <limits>

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FTotalDepthStepTest,"RaftSim.WaterDetail.TotalDepthStepGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FTotalDepthStepTest::RunTest(const FString&)
{
    if(GUsingNullRHI){AddError(TEXT("Actual GPU required"));return false;}
    FString Path,Error;TArray<uint8> Bytes;
    if(!FParse::Value(FCommandLine::Get(),TEXT("RaftSimStepFixture="),Path) || !FFileHelper::LoadFileToArray(Bytes,*Path))
    {AddError(TEXT("Generate export_total_depth_step_fixtures.py and pass -RaftSimStepFixture=<binary>"));return false;}
    FMemoryReader Reader(Bytes,true);uint32 Magic=0,Version=0,Count=0;Reader<<Magic<<Version<<Count;
    if(Magic!=0x52535354u || (Version!=1 && Version!=2 && Version!=3) || Count<8 || Count>32){AddError(TEXT("Invalid step fixture header"));return false;}
    struct FCase{FIntPoint Size;bool Periodic,SecondOrder;float Dx,Dt,B1,B2;TArray<float> Bed;TArray<FVector4f> State,Expected;};
    TArray<FCase> Cases;
    for(uint32 K=0;K<Count;++K)
    {
        uint32 X=0,Y=0,P=0,O=0;float Dx=0,Dt=0,B1=0,B2=0;Reader<<X<<Y<<P<<O<<Dx<<Dt<<B1<<B2;
        if(X<1 || Y<1 || X>512 || Y>512 || P>1 || O>1 || !FMath::IsFinite(Dx) || Dx<=0 || !FMath::IsFinite(Dt) || Dt<=0)
        {AddError(TEXT("Invalid step fixture dimensions"));return false;}
        auto& C=Cases.AddDefaulted_GetRef();C.Size=FIntPoint(X,Y);C.Periodic=P!=0;C.SecondOrder=O!=0;C.Dx=Dx;C.Dt=Dt;C.B1=B1;C.B2=B2;
        auto Read=[&](auto& A){A.SetNumUninitialized(X*Y);int64 N=sizeof(A[0])*int64(X)*Y;
            if(Reader.Tell()+N>Reader.TotalSize()){Reader.SetError();return;}Reader.Serialize(A.GetData(),N);};
        Read(C.Bed);Read(C.State);Read(C.Expected);if(Reader.IsError()){AddError(TEXT("Truncated step fixture"));return false;}
    }
    if(Reader.Tell()!=Reader.TotalSize()){AddError(TEXT("Trailing step fixture bytes"));return false;}
    bool Passed=true;TArray<FString> Records;
    ENQUEUE_RENDER_COMMAND(TotalDepthStepVerification)([&](FRHICommandListImmediate& Cmd)
    {
        for(int32 Index=0;Index<Cases.Num()+9;++Index)
        {
            const int32 Fault=Index-Cases.Num();const bool Extra=Fault>=0;
            const auto& C=Cases[Extra?((Fault==4 || Fault==6 || Fault==8)?0:5):Index];const int32 N=C.State.Num();
            TArray<float> Fraction,BadFraction;Fraction.Init(1.f,N);BadFraction.Init(std::numeric_limits<float>::quiet_NaN(),N);
            TArray<FVector4f> Progress;Progress.Add(FVector4f(1048576.f,0,.004f,C.Dt));
            if(Fault==2){Progress[0].Z=0;Progress[0].W=0;}
            if(Fault==3)Progress[0].W=1e-12f;
            if(Fault==4)Progress[0].Z=FMath::Pow(2.f,-40.f);
            if(Fault==5){Progress[0].X=3e38f;Progress[0].Y=3e38f;}
            if(Fault==6){Progress[0].Z=.1f;Progress[0].W=1.f;}
            FRDGBuilder Graph(Cmd);auto S=CreateStructuredBuffer(Graph,TEXT("StepTest.State"),C.State);
            auto B=CreateStructuredBuffer(Graph,TEXT("StepTest.Bed"),C.Bed);auto Clock=CreateStructuredBuffer(Graph,TEXT("StepTest.Progress"),Progress);
            auto F=CreateStructuredBuffer(Graph,TEXT("StepTest.Fraction"),Fraction);auto BadF=CreateStructuredBuffer(Graph,TEXT("StepTest.BadFraction"),BadFraction);
            int32 Calls=0;
            auto SelectFraction=[&](FRDGBuilder& G,FRDGBufferRef,const FRaftSimTotalDepthTransportResult& FV)
            {
                ++Calls;
                // Explicit test-only faults: exercise publication guards,
                // not altered production equations or physical references.
                if(Fault==7 && Calls==2)AddClearUAVPass(G,G.CreateUAV(FV.CFL),0u);
                if(Fault==8 && Calls==2)AddClearUAVFloatPass(G,G.CreateUAV(FV.HydroRate),-1e9f);
                return (Fault==0 && Calls==1) || (Fault==1 && Calls==2)?BadF:F;
            };
            auto R=RaftSimTryTotalDepthStepGPU(Graph,S,B,Clock,C.Size,C.Dx,C.Periodic,C.SecondOrder,SelectFraction,Error,{},nullptr,{},Version==2,Version==3);
            if(!R.State || Calls!=2){Passed=false;Graph.Execute();return;}
            FRHIGPUBufferReadback StateRead(TEXT("StepTest.StateRead")),ClockRead(TEXT("StepTest.ClockRead")),
                InfoRead(TEXT("StepTest.InfoRead")),DiagRead(TEXT("StepTest.DiagRead"));
            AddEnqueueCopyPass(Graph,&StateRead,R.State,N*16);AddEnqueueCopyPass(Graph,&ClockRead,R.Progress,16);
            AddEnqueueCopyPass(Graph,&InfoRead,R.Info,16);AddEnqueueCopyPass(Graph,&DiagRead,R.Diagnostics,16);
            Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle();
            const auto* A=static_cast<const FVector4f*>(StateRead.Lock(N*16));const auto* Next=static_cast<const FVector4f*>(ClockRead.Lock(16));
            const auto* Info=static_cast<const FVector4f*>(InfoRead.Lock(16));const auto* D=static_cast<const uint32*>(DiagRead.Lock(16));
            if(!A || !Next || !Info || !D){Passed=false;return;}
            const bool ExpectedAccept=!Extra || Fault==4 || Fault==6;Passed &= D[3]==uint32(ExpectedAccept);
            double MaxError=0;
            if(ExpectedAccept)
            {
                Passed &= D[0]==0 && D[1]==0 && D[2]==0 && Info->X>0;
                const float ExpectedDt=Fault==4?Progress[0].Z:Fault==6?1.f/120.f:C.Dt;
                Passed &= Info->X==ExpectedDt && Info->Y==ExpectedDt;
                Passed &= FMath::Abs((double(Next->X)+Next->Y)-(double(Progress[0].X)+Progress[0].Y+ExpectedDt))<1e-9;
                Passed &= Next->Z==(ExpectedDt==Progress[0].Z?0:Progress[0].Z-ExpectedDt);
                const auto& Expected=Extra?C.State:C.Expected;
                for(int32 K=0;K<4;++K)
                {
                    double E2=0,N2=0;
                    for(int32 I=0;I<N;++I)
                    {
                        const double E=double(A[I][K])-Expected[I][K];E2+=E*E;N2+=double(Expected[I][K])*Expected[I][K];
                        MaxError=FMath::Max(MaxError,FMath::Abs(E));Passed &= FMath::IsFinite(A[I][K]);
                    }
                    const double Relative=N2>0?FMath::Sqrt(E2/N2):FMath::Sqrt(E2);
                    Passed &= Relative<2e-5;
                    Records.Add(FString::Printf(TEXT("step case%d component%d relative%.9g reference-norm%.9g error-norm%.9g"),Index,K,Relative,FMath::Sqrt(N2),FMath::Sqrt(E2)));
                }
                Passed &= MaxError<1e-4;
                double FoamBefore=0,FoamAfter=0;
                for(int32 I=0;I<N;++I){Passed &= A[I].X>=0 && A[I].W>=0;FoamBefore+=C.State[I].W;FoamAfter+=A[I].W;}
                Passed &= FMath::Abs(FoamAfter-FoamBefore)<=2e-6*FoamBefore; // exact zero when no foam exists
                if(!Extra && (Index==2 || Index==3))
                    for(int32 I=0;I<N;++I)Passed &= A[I].Z==0 && C.Expected[I].Z==0;
                if(!Extra && (Index==0 || Index==1))Passed &= FMemory::Memcmp(A,C.State.GetData(),N*16)==0;
            }
            else
            {
                Passed &= FMemory::Memcmp(A,C.State.GetData(),N*16)==0 && Info->X==0;
                Passed &= Next->X==Progress[0].X && Next->Y==Progress[0].Y && Next->Z==Progress[0].Z;
                if(Fault==0)Passed &= D[0]!=0 && Next->W==0;
                if(Fault==1)Passed &= D[1]!=0 && Next->W==.5f*Info->Y;
                if(Fault==2)Passed &= (D[0]|D[1]|D[2])==0 && Next->W==0;
                if(Fault==3 || Fault==5)Passed &= ((D[0]|D[2])&16u)!=0 && Next->W==0;
                if(Fault==7)Passed &= (D[1]&4u)!=0 && Next->W==.5f*Info->Y;
                if(Fault==8)Passed &= (D[2]&8u)!=0 && Next->W==.5f*Info->Y;
            }
            Records.Add(FString::Printf(TEXT("step case%d fault%d accepted%u bits%u/%u/%u dt%.9g next%.9g state error%.9g time %.9g+%.9g"),
                Index,Fault,D[3],D[0],D[1],D[2],Info->X,Next->W,MaxError,Next->X,Next->Y));
            StateRead.Unlock();ClockRead.Unlock();InfoRead.Unlock();DiagRead.Unlock();
        }
    });
    FlushRenderingCommands();TestTrue(TEXT("GPU SSP-RK2 matches CPU and rejected trials preserve state and compensated clock"),Passed);
    for(const auto& R:Records)AddInfo(R);if(!Error.IsEmpty())AddError(Error);return !HasAnyErrors();
}
#endif
