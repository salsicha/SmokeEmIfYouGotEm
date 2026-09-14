#include "Misc/AutomationTest.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/FileHelper.h"
#include "Serialization/MemoryReader.h"
#include "RaftSimTotalDepthTransportGPU.h"
#include "RaftSimNonlinearPressureGPU.h"
#include "RenderGraphUtils.h"
#include "RenderingThread.h"
#include "RHIGPUReadback.h"
#include <limits>

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FTotalTransportTest,"RaftSim.WaterDetail.TotalDepthTransportGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FTotalTransportTest::RunTest(const FString&)
{
    if(GUsingNullRHI || GMaxRHIFeatureLevel<ERHIFeatureLevel::SM5)
    {AddError(TEXT("Actual GPU required for total-depth transport"));return false;}
    FString Path,Error;TArray<uint8> Bytes;
    if(!FParse::Value(FCommandLine::Get(),TEXT("RaftSimTransportFixture="),Path) || !FFileHelper::LoadFileToArray(Bytes,*Path))
    {AddError(TEXT("Generate export_total_depth_transport_fixtures.py and pass -RaftSimTransportFixture=<binary>"));return false;}
    FMemoryReader Reader(Bytes,true);uint32 Magic=0,Version=0,Count=0;Reader<<Magic<<Version<<Count;
    if(Magic!=0x52534656u || (Version!=1 && Version!=2 && Version!=3) || Count<8 || Count>32){AddError(TEXT("Invalid transport fixture header"));return false;}
    struct FCase
    {
        FIntPoint Size;bool Periodic,SecondOrder;float Dx,CFL;
        TArray<float> Bed,Fraction;TArray<FVector4f> State,Rate;
        TArray<uint32> Pairs;TArray<FVector2f> Slope,Force;
    };
    TArray<FCase> Cases;
    for(uint32 K=0;K<Count;++K)
    {
        uint32 X=0,Y=0,Periodic=0,SecondOrder=0;float Dx=0,CFL=0;
        Reader<<X<<Y<<Periodic<<SecondOrder<<Dx<<CFL;
        if(X<1 || Y<1 || X>512 || Y>512 || Periodic>1 || SecondOrder>1 || !FMath::IsFinite(Dx) || Dx<=0 || !(CFL>0))
        {AddError(TEXT("Invalid transport fixture dimensions/CFL"));return false;}
        auto& C=Cases.AddDefaulted_GetRef();C.Size=FIntPoint(X,Y);C.Periodic=Periodic!=0;C.SecondOrder=SecondOrder!=0;C.Dx=Dx;C.CFL=CFL;
        auto Read=[&](auto& A){A.SetNumUninitialized(X*Y);const int64 N=sizeof(A[0])*int64(X)*Y;
            if(Reader.Tell()+N>Reader.TotalSize()){Reader.SetError();return;}Reader.Serialize(A.GetData(),N);};
        Read(C.Bed);Read(C.State);Read(C.Rate);Read(C.Pairs);Read(C.Slope);Read(C.Force);Read(C.Fraction);
        if(Reader.IsError()){AddError(TEXT("Truncated transport fixture"));return false;}
    }
    if(Reader.Tell()!=Reader.TotalSize()){AddError(TEXT("Trailing transport fixture bytes"));return false;}
    bool Passed=true,Rejected=true;TArray<FString> Records;
    ENQUEUE_RENDER_COMMAND(RaftSimTotalTransportTest)([&](FRHICommandListImmediate& Cmd)
    {
        for(int32 Index=0;Index<Cases.Num()+4;++Index)
        {
            const bool Bad=Index>=Cases.Num();auto C=Cases[FMath::Min(Index,Cases.Num()-1)];const int32 N=C.State.Num();
            if(Index==Cases.Num())C.State[3].X=-1;
            if(Index==Cases.Num()+1){C.State[3].X=0;C.State[3].Y=1;}
            if(Index==Cases.Num()+2)C.Bed[3]=std::numeric_limits<float>::infinity();
            if(Index==Cases.Num()+3)C.State[3].W=-1;
            FRDGBuilder Graph(Cmd);
            auto S=CreateStructuredBuffer(Graph,TEXT("TransportTest.State"),C.State);
            auto B=CreateStructuredBuffer(Graph,TEXT("TransportTest.Bed"),C.Bed);
            auto F=CreateStructuredBuffer(Graph,TEXT("TransportTest.Fraction"),C.Fraction);
            if(Index==0)
            {
                Rejected &= !RaftSimTotalDepthTransportGPU(Graph,S,B,C.Size,0,C.Periodic,C.SecondOrder,Error).HydroRate;
                Rejected &= !RaftSimTotalDepthTransportGPU(Graph,S,S,C.Size,C.Dx,C.Periodic,C.SecondOrder,Error).HydroRate;
                Rejected &= !RaftSimTotalDepthTransportGPU(Graph,S,B,C.Size,C.Dx,C.Periodic,C.SecondOrder,Error,nullptr,nullptr,true,true).HydroRate;
            }
            auto R=RaftSimTotalDepthTransportGPU(Graph,S,B,C.Size,C.Dx,C.Periodic,C.SecondOrder,Error,nullptr,nullptr,Version==2,Version==3);
            if(!R.HydroRate || !Error.IsEmpty()){Passed=false;Graph.Execute();return;}
            // Integrate the components with actual native transport outputs.
            // Never upload the CPU FV rate or graph as the GPU pressure input.
            auto P=RaftSimNonlinearPressureGPU(Graph,S,R.HydroRate,R.Geometry,R.Pairs,R.PhysicalBedSlope,F,C.Size,C.Dx,C.Periodic,Error);
            if(!P.Force || !Error.IsEmpty()){Passed=false;Graph.Execute();return;}
            FRHIGPUBufferReadback RateRead(TEXT("TransportTest.Rate")),GraphRead(TEXT("TransportTest.Graph")),
                SlopeRead(TEXT("TransportTest.Slope")),GeoRead(TEXT("TransportTest.Geometry")),CFLRead(TEXT("TransportTest.CFL")),
                DiagRead(TEXT("TransportTest.Diag")),ForceRead(TEXT("TransportTest.Force")),PressureDiagRead(TEXT("TransportTest.PressureDiag")),
                SolverRead(TEXT("TransportTest.SolverDiag")),ResidualRead(TEXT("TransportTest.Residual")),RHSRead(TEXT("TransportTest.RHS"));
            AddEnqueueCopyPass(Graph,&RateRead,R.HydroRate,N*16);AddEnqueueCopyPass(Graph,&GraphRead,R.Pairs,N*4);
            AddEnqueueCopyPass(Graph,&SlopeRead,R.PhysicalBedSlope,N*8);AddEnqueueCopyPass(Graph,&GeoRead,R.Geometry,N*8);
            AddEnqueueCopyPass(Graph,&CFLRead,R.CFL,16);AddEnqueueCopyPass(Graph,&DiagRead,R.Diagnostics,16);
            AddEnqueueCopyPass(Graph,&ForceRead,P.Force,N*8);AddEnqueueCopyPass(Graph,&PressureDiagRead,P.Diagnostics,16);
            AddEnqueueCopyPass(Graph,&SolverRead,P.SolverDiagnostics,16);AddEnqueueCopyPass(Graph,&ResidualRead,P.Residual,N*16);
            AddEnqueueCopyPass(Graph,&RHSRead,P.RightHandSide,N*16);
            Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle();
            const uint32* D=static_cast<const uint32*>(DiagRead.Lock(16));
            const float* Bound=static_cast<const float*>(CFLRead.Lock(16));
            if(!D || !Bound){Passed=false;return;}
            if(Bad){Passed &= D[0]>0 && Bound[2]==0;DiagRead.Unlock();CFLRead.Unlock();continue;}
            Passed &= D[0]==0 && D[1]==0;
            const double CFLError=FMath::IsFinite(C.CFL)?FMath::Abs(double(Bound[2])/C.CFL-1.):0;
            Passed &= CFLError<2e-5 && (FMath::IsFinite(C.CFL) || Bound[2]==C.CFL);
            Records.Add(FString::Printf(TEXT("case%d transport diagnostics %u/%u CFL %.9g relative error %.9g"),Index,D[0],D[1],Bound[2],CFLError));
            DiagRead.Unlock();CFLRead.Unlock();
            auto Compare=[&](FRHIGPUBufferReadback& Read,const auto& Expected,const TCHAR* Name)
            {
                const int32 Components=sizeof(Expected[0])/4;const float* A=static_cast<const float*>(Read.Lock(N*Components*4));
                const float* E=reinterpret_cast<const float*>(Expected.GetData());if(!A){Passed=false;return;}
                double Error2=0,Norm2=0,MaxError=0,MassRate=0,MassMagnitude=0;
                for(int32 I=0;I<N*Components;++I)
                {const double V=double(A[I])-E[I];Passed &= FMath::IsFinite(A[I]);Error2+=V*V;Norm2+=double(E[I])*E[I];MaxError=FMath::Max(MaxError,FMath::Abs(V));}
                const double Relative=Norm2>0?FMath::Sqrt(Error2/Norm2):FMath::Sqrt(Error2);
                Passed &= Relative<2e-5 && MaxError<1e-3;
                if(FCString::Strcmp(Name,TEXT("Rate"))==0)
                {
                    for(int32 I=0;I<N;++I){MassRate+=A[I*4];MassMagnitude+=FMath::Abs(double(A[I*4]));Passed &= A[I*4+3]==0;}
                    Passed &= FMath::Abs(MassRate)<=2e-6*MassMagnitude;
                    const bool ExactRest=!C.Rate.ContainsByPredicate([](const FVector4f& V){return V!=FVector4f(0,0,0,0);});
                    if(Index==0 || Index==1 || ExactRest)for(int32 I=0;I<N*4;++I)Passed &= A[I]==0;
                }
                Records.Add(FString::Printf(TEXT("case%d %s max error %.9g relative %.9g mass sum %.9g magnitude %.9g"),Index,Name,MaxError,Relative,MassRate,MassMagnitude));Read.Unlock();
            };
            Compare(RateRead,C.Rate,TEXT("Rate"));Compare(SlopeRead,C.Slope,TEXT("Slope"));Compare(ForceRead,C.Force,TEXT("CoupledForce"));
            const auto* G=static_cast<const uint32*>(GraphRead.Lock(N*4));const auto* Geo=static_cast<const FVector2f*>(GeoRead.Lock(N*8));
            if(!G || !Geo){Passed=false;return;}uint32 Mismatches=0;
            for(int32 I=0;I<N;++I){Mismatches+=G[I]!=C.Pairs[I];Passed &= Geo[I].X==C.State[I].X && Geo[I].Y==C.Bed[I];}
            Passed &= Mismatches==0;GraphRead.Unlock();GeoRead.Unlock();Records.Add(FString::Printf(TEXT("case%d graph mismatches %u"),Index,Mismatches));
            const auto* PD=static_cast<const uint32*>(PressureDiagRead.Lock(16));const auto* SD=static_cast<const uint32*>(SolverRead.Lock(16));
            const float* Res=static_cast<const float*>(ResidualRead.Lock(N*16));const float* RHS=static_cast<const float*>(RHSRead.Lock(N*16));
            if(!PD || !SD || !Res || !RHS){Passed=false;return;}
            Passed &= PD[0]==0 && PD[1]==0 && SD[0]==0 && SD[1]==0 && SD[2]<=40 && SD[3]<=40;
            double R2=0,B2=0;for(int32 I=0;I<N*4;++I){Passed &= FMath::IsFinite(Res[I]) && FMath::IsFinite(RHS[I]);R2+=double(Res[I])*Res[I];B2+=double(RHS[I])*RHS[I];}
            const double Relative=B2>0?FMath::Sqrt(R2/B2):FMath::Sqrt(R2);Passed &= Relative<2e-5;
            Records.Add(FString::Printf(TEXT("case%d coupled pressure true residual %.9g diagnostics %u/%u/%u/%u"),Index,Relative,PD[0],PD[1],SD[0],SD[1]));
            PressureDiagRead.Unlock();SolverRead.Unlock();ResidualRead.Unlock();RHSRead.Unlock();
        }
    });
    FlushRenderingCommands();TestTrue(TEXT("transport invalid descriptors rejected"),Rejected);
    TestTrue(TEXT("native transport and coupled pressure match CPU, preserve graph/CFL/resting lake and reject invalid state"),Passed);
    for(const auto& R:Records)AddInfo(R);if(!Error.IsEmpty())AddError(Error);return !HasAnyErrors();
}
#endif
