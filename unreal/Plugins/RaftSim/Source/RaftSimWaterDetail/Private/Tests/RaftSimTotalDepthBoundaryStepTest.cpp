#include "Misc/AutomationTest.h"
#include "RaftSimTotalDepthStepGPU.h"
#include "RenderGraphUtils.h"
#include "RenderingThread.h"
#include "RHIGPUReadback.h"
#include <limits>

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FTotalDepthBoundaryStepTest,"RaftSim.WaterDetail.TotalDepthBoundaryStepGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FTotalDepthBoundaryStepTest::RunTest(const FString&)
{
    if(GUsingNullRHI){AddError(TEXT("Actual GPU required"));return false;}
    bool Passed=true,RejectedDescriptors=true;FString Error;TArray<FString> Records;
    ENQUEUE_RENDER_COMMAND(TotalDepthBoundaryStepVerification)([&](FRHICommandListImmediate& Cmd)
    {
        for(int32 Case=0;Case<20;++Case)
        {
            const int32 Fault=Case-16;
            const FIntPoint Shapes[]={FIntPoint(13,9),FIntPoint(17,1),FIntPoint(1,19),FIntPoint(1,1)};
            const FIntPoint Size=Shapes[Case<16?Case/4:3];const int32 N=Size.X*Size.Y,NB=2*(Size.X+Size.Y);
            const FVector2f Directions[]={FVector2f(.75f,0),FVector2f(-.75f,0),FVector2f(0,.75f),FVector2f(0,-.75f)};
            const FVector2f U=Directions[Case%4];const FVector4f Uniform(1,U.X,U.Y,.25f);
            TArray<FVector4f> State,Ext,ClockData;State.Init(Uniform,N);Ext.Init(Uniform,NB);
            ClockData.Add(FVector4f(1048576.f,.03125f,.02f,1.f/128.f));
            TArray<float> Bed,ExtBed,Fraction;Bed.Init(0,N);ExtBed.Init(0,NB);Fraction.Init(1,N);
            TArray<FVector2f> Trace;for(int32 I=0;I<NB;++I)Trace.Add(FVector2f(I<2*Size.Y?U.X:U.Y,0));
            FRDGBuilder Graph(Cmd);
            auto Upload=[&](const auto& A,const TCHAR* Name){return CreateStructuredBuffer(Graph,Name,MakeArrayView(A));};
            auto S=Upload(State,TEXT("BoundaryStep.State")),B=Upload(Bed,TEXT("BoundaryStep.Bed"));
            auto Clock=Upload(ClockData,TEXT("BoundaryStep.Clock")),F=Upload(Fraction,TEXT("BoundaryStep.Fraction"));
            auto SelectFraction=[&](FRDGBuilder&,FRDGBufferRef,const FRaftSimTotalDepthTransportResult&){return F;};
            int32 Calls=0;FRDGBufferRef SecondInfo=nullptr;
            FRaftSimTotalDepthBoundaryProvider Provider=[&](FRDGBuilder&,FRDGBufferRef Stage,FRDGBufferRef Progress,FRDGBufferRef Info)
            {
                ++Calls;Passed &= Progress==Clock;
                Passed &= Calls==1?(Stage==S && Info==nullptr):(Stage!=S && Info!=nullptr);
                if(Calls==2)SecondInfo=Info;
                auto Ghost=Ext;auto Z=ExtBed;auto T=Trace;
                if((Fault==0 && Calls==1) || (Fault==1 && Calls==2))T.Last().Y=std::numeric_limits<float>::quiet_NaN();
                if(Fault==2 && Calls==2)Z.Last()=std::numeric_limits<float>::infinity();
                if(Fault==3 && Calls==2)Ghost.Last().X=-1;
                return FRaftSimTotalDepthBoundaryInput{Upload(Ghost,TEXT("BoundaryStep.Exterior")),
                    Upload(Z,TEXT("BoundaryStep.ExteriorBed")),Upload(T,TEXT("BoundaryStep.FaceTrace"))};
            };
            if(Case==0)
            {
                auto Invalid=RaftSimTryTotalDepthStepGPU(Graph,S,B,Clock,Size,.5f,true,true,SelectFraction,Error,Provider);
                RejectedDescriptors &= !Invalid.State && Calls==0 && !Error.IsEmpty();
                FRaftSimTotalDepthBoundaryProvider Partial=[&](FRDGBuilder&,FRDGBufferRef,FRDGBufferRef,FRDGBufferRef)
                {return FRaftSimTotalDepthBoundaryInput{Upload(Ext,TEXT("BoundaryStep.PartialExterior")),nullptr,nullptr};};
                Invalid=RaftSimTryTotalDepthStepGPU(Graph,S,B,Clock,Size,.5f,false,true,SelectFraction,Error,Partial);
                RejectedDescriptors &= !Invalid.State && !Error.IsEmpty();
            }
            auto R=RaftSimTryTotalDepthStepGPU(Graph,S,B,Clock,Size,.5f,false,true,SelectFraction,Error,Provider);
            if(!R.State || !R.BoundaryVolume || !Error.IsEmpty()){Passed=false;Graph.Execute();return;}
            Passed &= Calls==2 && SecondInfo==R.Info;
            FRHIGPUBufferReadback StateRead(TEXT("BoundaryStep.StateRead")),ClockRead(TEXT("BoundaryStep.ClockRead")),
                InfoRead(TEXT("BoundaryStep.InfoRead")),DiagRead(TEXT("BoundaryStep.DiagRead")),FluxRead(TEXT("BoundaryStep.FluxRead"));
            AddEnqueueCopyPass(Graph,&StateRead,R.State,N*16);AddEnqueueCopyPass(Graph,&ClockRead,R.Progress,16);
            AddEnqueueCopyPass(Graph,&InfoRead,R.Info,16);AddEnqueueCopyPass(Graph,&DiagRead,R.Diagnostics,16);
            AddEnqueueCopyPass(Graph,&FluxRead,R.BoundaryVolume,NB*16);Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle();
            const auto* A=static_cast<const FVector4f*>(StateRead.Lock(N*16));
            const auto* Next=static_cast<const FVector4f*>(ClockRead.Lock(16));
            const auto* Info=static_cast<const FVector4f*>(InfoRead.Lock(16));
            const auto* D=static_cast<const uint32*>(DiagRead.Lock(16));
            const auto* V=static_cast<const FVector4f*>(FluxRead.Lock(NB*16));
            if(!A || !Next || !Info || !D || !V){Passed=false;return;}
            Passed &= FMemory::Memcmp(A,State.GetData(),N*16)==0;
            if(Fault<0)
            {
                const float Dt=ClockData[0].W;
                Passed &= D[0]==0 && D[1]==0 && D[2]==0 && D[3]==1 && Info->X==Dt;
                Passed &= double(Next->X)+Next->Y==double(ClockData[0].X)+ClockData[0].Y+Dt;
                Passed &= Next->Z==ClockData[0].Z-Dt;
                for(int32 I=0;I<NB;++I)
                {
                    const float Water=Dt*(I<2*Size.Y?U.X:U.Y);
                    Passed &= V[I].X==Water && V[I].W==.25f*Water;
                    for(int32 K=0;K<4;++K)Passed &= FMath::IsFinite(V[I][K]);
                }
            }
            else
            {
                Passed &= D[3]==0 && Info->X==0 && Next->X==ClockData[0].X && Next->Y==ClockData[0].Y && Next->Z==ClockData[0].Z;
                if(Fault==0)Passed &= D[0]!=0 && Next->W==0;
                else Passed &= D[1]!=0 && Next->W==.5f*Info->Y;
                for(int32 I=0;I<NB;++I)Passed &= V[I]==FVector4f(0,0,0,0);
            }
            Records.Add(FString::Printf(TEXT("boundary step case%d %dx%d fault%d accepted%u bits%u/%u/%u dt%.9g callbacks%d; state exact; accepted-only water/foam ledger"),
                Case,Size.X,Size.Y,Fault,D[3],D[0],D[1],D[2],Info->X,Calls));
            StateRead.Unlock();ClockRead.Unlock();InfoRead.Unlock();DiagRead.Unlock();FluxRead.Unlock();
        }
    });
    FlushRenderingCommands();TestTrue(TEXT("stage boundary descriptors cannot silently become closed or periodic"),RejectedDescriptors);
    TestTrue(TEXT("GPU stage-boundary composition preserves uniform state, clock transactions and accepted-only boundary inventory"),Passed);
    for(const auto& R:Records)AddInfo(R);if(!Error.IsEmpty())AddError(Error);return !HasAnyErrors();
}
#endif
