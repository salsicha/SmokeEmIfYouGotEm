#include "Misc/AutomationTest.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/FileHelper.h"
#include "Serialization/MemoryReader.h"
#include "RaftSimBreakingFrontGPU.h"
#include "RenderGraphUtils.h"
#include "RenderingThread.h"
#include "RHIGPUReadback.h"
#include <limits>

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FBreakingFrontTest,"RaftSim.WaterDetail.BreakingFrontGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FBreakingFrontTest::RunTest(const FString&)
{
    if(GUsingNullRHI){AddError(TEXT("Actual GPU required"));return false;}
    FString Path,Error;TArray<uint8> Bytes;
    if(!FParse::Value(FCommandLine::Get(),TEXT("RaftSimBreakingFrontFixture="),Path) || !FFileHelper::LoadFileToArray(Bytes,*Path))
    {AddError(TEXT("Export breaking-front fixtures and pass -RaftSimBreakingFrontFixture=<binary>"));return false;}
    if(Bytes.Num()<12){AddError(TEXT("Truncated breaking fixture"));return false;}
    FMemoryReader Reader(Bytes,true);uint32 Magic=0,Version=0,Count=0;Reader<<Magic<<Version<<Count;
    if(Magic!=0x52464252u || Version!=1 || Count<1 || Count>64){AddError(TEXT("Invalid breaking fixture header"));return false;}
    struct FCase
    {
        FIntPoint Size;uint32 Periodic=0,Fronts=0,Truncated=0,Subcell=0;float Dx=0,Dt=0;
        TArray<FVector2f> Geometry;TArray<FVector4f> Rate,State,ExpectedState;
        TArray<uint32> Pairs;TArray<float> Expected;
    };
    TArray<FCase> Cases;
    for(uint32 K=0;K<Count;++K)
    {
        auto& C=Cases.AddDefaulted_GetRef();uint32 X=0,Y=0;
        Reader<<X<<Y<<C.Periodic<<C.Dx<<C.Dt<<C.Fronts<<C.Truncated<<C.Subcell;
        if(Reader.IsError() || X<1 || Y<1 || X>512 || Y>512 || C.Periodic>1 ||
            !FMath::IsFinite(C.Dx) || C.Dx<=0 || !FMath::IsFinite(C.Dt) || C.Dt<0)
        {AddError(TEXT("Invalid breaking fixture dimensions"));return false;}
        C.Size=FIntPoint(X,Y);const int32 N=X*Y;
        auto Read=[&](auto& A)
        {
            const int64 Length=sizeof(A[0])*int64(N);
            if(Reader.IsError() || Reader.Tell()+Length>Reader.TotalSize()){Reader.SetError();return;}
            A.SetNumUninitialized(N);Reader.Serialize(A.GetData(),Length);
        };
        Read(C.Geometry);Read(C.Rate);Read(C.Pairs);Read(C.Expected);Read(C.State);
        if(C.Dt>0)Read(C.ExpectedState);
        if(Reader.IsError()){AddError(TEXT("Truncated breaking fixture arrays"));return false;}
    }
    if(Reader.Tell()!=Reader.TotalSize()){AddError(TEXT("Trailing breaking fixture bytes"));return false;}
    bool Passed=true;TArray<FString> Records;
    ENQUEUE_RENDER_COMMAND(BreakingFrontVerification)([&](FRHICommandListImmediate& Cmd)
    {
        for(int32 Index=0;Index<Cases.Num()+6;++Index)
        {
            const int32 Fault=Index-Cases.Num();FCase C=Cases[Fault>=0?0:Index];const int32 N=C.Size.X*C.Size.Y;
            if(Fault==0)C.Geometry[0].X=std::numeric_limits<float>::quiet_NaN();
            if(Fault==1)C.Geometry[0].X=-1;
            if(Fault==2)C.Rate[0].X=std::numeric_limits<float>::infinity();
            if(Fault==3)C.Pairs[0]|=4u;
            if(Fault==4)C.Geometry[0].X=0; // a connected dry endpoint is invalid
            if(Fault==5){uint32 NegativeSubnormal=0x80000001u;FMemory::Memcpy(&C.Geometry[0].X,&NegativeSubnormal,4);}
            FRDGBuilder Graph(Cmd);
            auto Upload=[&](const auto& A,const TCHAR* Name){return CreateStructuredBuffer(Graph,Name,MakeArrayView(A));};
            auto Geometry=Upload(C.Geometry,TEXT("BreakingTest.Geometry")),Rate=Upload(C.Rate,TEXT("BreakingTest.Rate"));
            auto Pairs=Upload(C.Pairs,TEXT("BreakingTest.Pairs"));
            if(Index==0)
            {
                const auto Bad=RaftSimClassifyBreakingFrontGPU(Graph,Geometry,Geometry,Pairs,C.Size,C.Dx,C.Periodic!=0,Error);
                Passed &= !Bad.Fraction && !Error.IsEmpty();Error.Reset();
            }
            auto R=RaftSimClassifyBreakingFrontGPU(Graph,Geometry,Rate,Pairs,C.Size,C.Dx,C.Periodic!=0,Error);
            if(!R.Fraction){Passed=false;Graph.Execute();return;}
            FRHIGPUBufferReadback FR(TEXT("BreakingTest.Fraction")),DR(TEXT("BreakingTest.Diagnostics"));
            AddEnqueueCopyPass(Graph,&FR,R.Fraction,N*4);AddEnqueueCopyPass(Graph,&DR,R.Diagnostics,16);
            FRaftSimTotalDepthStepResult Step;
            FRHIGPUBufferReadback SR(TEXT("BreakingTest.Step")),SD(TEXT("BreakingTest.StepDiagnostics")),PR(TEXT("BreakingTest.Progress"));
            if(Fault<0 && C.Dt>0)
            {
                TArray<float> Bed;for(const auto& G:C.Geometry)Bed.Add(G.Y);
                TArray<FVector4f> Progress={FVector4f(3,.125f,C.Dt,C.Dt)};
                Step=RaftSimTryHybridBreakingStepGPU(Graph,Upload(C.State,TEXT("BreakingTest.State")),
                    Upload(Bed,TEXT("BreakingTest.Bed")),Upload(Progress,TEXT("BreakingTest.Clock")),C.Size,C.Dx,C.Periodic!=0,true,Error);
                if(!Step.State){Passed=false;Graph.Execute();return;}
                AddEnqueueCopyPass(Graph,&SR,Step.State,N*16);AddEnqueueCopyPass(Graph,&SD,Step.Diagnostics,16);
                AddEnqueueCopyPass(Graph,&PR,Step.Progress,16);
            }
            Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle(); // diagnostic fixture only
            const auto* F=static_cast<const float*>(FR.Lock(N*4));const auto* D=static_cast<const uint32*>(DR.Lock(16));
            if(!F || !D){Passed=false;return;}
            double Maximum=0;
            if(Fault<0)
            {
                Passed &= D[0]==0 && D[1]==C.Fronts && D[2]==C.Truncated && D[3]==C.Subcell;
                for(int32 I=0;I<N;++I)
                {
                    Passed &= FMath::IsFinite(F[I]) && F[I]>=0 && F[I]<=1;
                    Maximum=FMath::Max(Maximum,FMath::Abs(double(F[I])-C.Expected[I]));
                }
                Passed &= Maximum<2e-5;
            }
            else
            {
                Passed &= D[0]!=0;
                int32 Finite=0;
                for(int32 I=0;I<N;++I){Passed &= !FMath::IsFinite(F[I]);Finite+=FMath::IsFinite(F[I]);}
                Records.Add(FString::Printf(TEXT("invalid classifier case%d finite outputs%d first%.9g"),Index,Finite,F[0]));
            }
            Records.Add(FString::Printf(TEXT("breaking case%d fault%d error%.9g flags%u fronts%u/%u truncated%u/%u subcell%u/%u"),
                Index,Fault,Maximum,D[0],D[1],C.Fronts,D[2],C.Truncated,D[3],C.Subcell));
            FR.Unlock();DR.Unlock();
            if(Step.State)
            {
                const auto* S=static_cast<const FVector4f*>(SR.Lock(N*16));const auto* Flags=static_cast<const uint32*>(SD.Lock(16));
                const auto* Clock=static_cast<const FVector4f*>(PR.Lock(16));
                if(!S || !Flags || !Clock){Passed=false;return;}
                Passed &= Flags[0]==0 && Flags[1]==0 && Flags[2]==0 && Flags[3]==1 && Clock->Z==0;
                Passed &= FMath::Abs(double(Clock->X)+Clock->Y-(3.125+double(C.Dt)))<1e-9;
                double MaxState=0;
                for(int32 Component=0;Component<4;++Component)
                {
                    double E2=0,N2=0;
                    for(int32 I=0;I<N;++I)
                    {
                        const double E=double(S[I][Component])-C.ExpectedState[I][Component];
                        E2+=E*E;N2+=double(C.ExpectedState[I][Component])*C.ExpectedState[I][Component];
                        MaxState=FMath::Max(MaxState,FMath::Abs(E));Passed &= FMath::IsFinite(S[I][Component]);
                    }
                    const double Relative=N2>0?FMath::Sqrt(E2/N2):FMath::Sqrt(E2);
                    Passed &= Relative<2e-5;
                    Records.Add(FString::Printf(TEXT("hybrid RK2 case%d component%d relative%.9g"),Index,Component,Relative));
                }
                Passed &= MaxState<1e-4;
                double WaterBefore=0,WaterAfter=0,FoamBefore=0,FoamAfter=0;
                for(int32 I=0;I<N;++I)
                {Passed &= S[I].X>=0 && S[I].W>=0;WaterBefore+=C.State[I].X;WaterAfter+=S[I].X;FoamBefore+=C.State[I].W;FoamAfter+=S[I].W;}
                Passed &= FMath::Abs(WaterAfter-WaterBefore)<=2e-6*WaterBefore && FMath::Abs(FoamAfter-FoamBefore)<=2e-6*FoamBefore;
                Records.Add(FString::Printf(TEXT("hybrid ledger case%d clock %.12g+%.12g remaining%.12g error%.12g water%.12g/%.12g foam%.12g/%.12g"),
                    Index,Clock->X,Clock->Y,Clock->Z,FMath::Abs(double(Clock->X)+Clock->Y-(3.125+double(C.Dt))),WaterBefore,WaterAfter,FoamBefore,FoamAfter));
                Records.Add(FString::Printf(TEXT("hybrid RK2 case%d flags%u/%u/%u/%u maximum state error%.9g"),Index,Flags[0],Flags[1],Flags[2],Flags[3],MaxState));
                SR.Unlock();SD.Unlock();PR.Unlock();
            }
        }
    });
    FlushRenderingCommands();TestTrue(TEXT("same-stage GPU fronts and nonlinear RK2 match independent CPU without invalid-input fallback"),Passed);
    for(const auto& Record:Records)AddInfo(Record);if(!Error.IsEmpty())AddError(Error);return !HasAnyErrors();
}
#endif
