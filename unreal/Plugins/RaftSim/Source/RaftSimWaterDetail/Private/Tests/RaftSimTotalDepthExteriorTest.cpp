#include "Misc/AutomationTest.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/FileHelper.h"
#include "Serialization/MemoryReader.h"
#include "RaftSimTotalDepthTransportGPU.h"
#include "RenderGraphUtils.h"
#include "RenderingThread.h"
#include "RHIGPUReadback.h"
#include <limits>

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FTotalExteriorTest,"RaftSim.WaterDetail.TotalDepthExteriorTransportGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FTotalExteriorTest::RunTest(const FString&)
{
    if(GUsingNullRHI || GMaxRHIFeatureLevel<ERHIFeatureLevel::SM5)
    {AddError(TEXT("Actual GPU required for exterior transport"));return false;}
    FString Path,Error;TArray<uint8> Bytes;
    if(!FParse::Value(FCommandLine::Get(),TEXT("RaftSimExteriorFixture="),Path) || !FFileHelper::LoadFileToArray(Bytes,*Path))
    {AddError(TEXT("Generate export_total_depth_exterior_fixtures.py and pass -RaftSimExteriorFixture=<binary>"));return false;}
    FMemoryReader Reader(Bytes,true);uint32 Magic=0,Version=0,Count=0;Reader<<Magic<<Version<<Count;
    if(Magic!=0x52534558u || Version!=1 || (Count!=22 && Count!=24)){AddError(TEXT("Invalid exterior fixture header"));return false;}
    struct FCase
    {
        FIntPoint Size;bool SecondOrder;float Dx,CFL;
        TArray<float> Bed,ExteriorBed;TArray<FVector4f> State,ExteriorState,Rate,Flux;
        TArray<FVector2f> Slope;
    };
    TArray<FCase> Cases;
    for(uint32 K=0;K<Count;++K)
    {
        uint32 X=0,Y=0,Second=0;float Dx=0,CFL=0;Reader<<X<<Y<<Second<<Dx<<CFL;
        if(X<1 || Y<1 || X>512 || Y>512 || Second>1 || !FMath::IsFinite(Dx) || Dx<=0 || !(CFL>0))
        {AddError(TEXT("Invalid exterior fixture dimensions/CFL"));return false;}
        auto& C=Cases.AddDefaulted_GetRef();C.Size=FIntPoint(X,Y);C.SecondOrder=Second!=0;C.Dx=Dx;C.CFL=CFL;
        auto Read=[&](auto& A,uint32 N)
        {
            A.SetNumUninitialized(N);const int64 Length=sizeof(A[0])*int64(N);
            if(Reader.Tell()+Length>Reader.TotalSize()){Reader.SetError();return;}
            Reader.Serialize(A.GetData(),Length);
        };
        const uint32 N=X*Y,NB=2*(X+Y);
        Read(C.Bed,N);Read(C.State,N);Read(C.ExteriorState,NB);Read(C.ExteriorBed,NB);
        Read(C.Rate,N);Read(C.Flux,NB);Read(C.Slope,N);
        if(Reader.IsError()){AddError(TEXT("Truncated exterior fixture"));return false;}
    }
    if(Reader.Tell()!=Reader.TotalSize()){AddError(TEXT("Trailing exterior fixture bytes"));return false;}
    bool Passed=true,Rejected=true;TArray<FString> Records;
    ENQUEUE_RENDER_COMMAND(RaftSimTotalExteriorTest)([&](FRHICommandListImmediate& Cmd)
    {
        for(int32 Index=0;Index<Cases.Num()+6;++Index)
        {
            const bool Bad=Index>=Cases.Num();auto C=Cases[FMath::Min(Index,Cases.Num()-1)];
            const int32 N=C.State.Num(),NB=C.ExteriorState.Num();
            // Last ghost of a 1x1 domain: validation must cover more ghosts
            // than cells and cannot rely on one ghost per cell thread.
            auto& E=C.ExteriorState.Last();
            if(Index==Cases.Num())E.X=-1;
            if(Index==Cases.Num()+1){E.X=0;E.Y=1;}
            if(Index==Cases.Num()+2)E.W=-1;
            if(Index==Cases.Num()+3)E.Y=std::numeric_limits<float>::quiet_NaN();
            if(Index==Cases.Num()+4)C.ExteriorBed.Last()=std::numeric_limits<float>::infinity();
            if(Index==Cases.Num()+5){E.X=1e-30f;E.Y=1e30f;}
            FRDGBuilder Graph(Cmd);
            auto S=CreateStructuredBuffer(Graph,TEXT("ExteriorTest.State"),C.State);
            auto B=CreateStructuredBuffer(Graph,TEXT("ExteriorTest.Bed"),C.Bed);
            auto ES=CreateStructuredBuffer(Graph,TEXT("ExteriorTest.Ghost"),C.ExteriorState);
            auto EB=CreateStructuredBuffer(Graph,TEXT("ExteriorTest.GhostBed"),C.ExteriorBed);
            if(Index==0)
            {
                Rejected &= !RaftSimTotalDepthTransportGPU(Graph,S,B,C.Size,C.Dx,true,true,Error,ES,EB).HydroRate;
                Rejected &= !RaftSimTotalDepthTransportGPU(Graph,S,B,C.Size,C.Dx,false,true,Error,ES,nullptr).HydroRate;
                Rejected &= !RaftSimTotalDepthTransportGPU(Graph,S,B,C.Size,C.Dx,false,true,Error,nullptr,EB).HydroRate;
                Rejected &= !RaftSimTotalDepthTransportGPU(Graph,S,B,C.Size,C.Dx,false,true,Error,S,EB).HydroRate;
                Rejected &= !RaftSimTotalDepthTransportGPU(Graph,S,B,C.Size,C.Dx,false,true,Error,ES,ES).HydroRate;
            }
            auto R=RaftSimTotalDepthTransportGPU(Graph,S,B,C.Size,C.Dx,false,C.SecondOrder,Error,ES,EB);
            if(!R.HydroRate || !R.BoundaryFlux || !Error.IsEmpty()){Passed=false;Graph.Execute();return;}
            FRHIGPUBufferReadback RateRead(TEXT("ExteriorTest.Rate")),FluxRead(TEXT("ExteriorTest.Flux")),
                SlopeRead(TEXT("ExteriorTest.Slope")),CFLRead(TEXT("ExteriorTest.CFL")),DiagRead(TEXT("ExteriorTest.Diag"));
            AddEnqueueCopyPass(Graph,&RateRead,R.HydroRate,N*16);AddEnqueueCopyPass(Graph,&FluxRead,R.BoundaryFlux,NB*16);
            AddEnqueueCopyPass(Graph,&SlopeRead,R.PhysicalBedSlope,N*8);
            AddEnqueueCopyPass(Graph,&CFLRead,R.CFL,16);AddEnqueueCopyPass(Graph,&DiagRead,R.Diagnostics,16);
            Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle();
            const auto* D=static_cast<const uint32*>(DiagRead.Lock(16));
            const auto* Bound=static_cast<const float*>(CFLRead.Lock(16));
            if(!D || !Bound){Passed=false;return;}
            if(Bad){Passed &= D[0]>0 && Bound[2]==0;DiagRead.Unlock();CFLRead.Unlock();continue;}
            Passed &= D[0]==0 && D[1]==0;
            Passed &= FMath::IsFinite(C.CFL)?FMath::Abs(double(Bound[2])/C.CFL-1)<2e-5:Bound[2]==C.CFL;
            DiagRead.Unlock();CFLRead.Unlock();
            const float* A=static_cast<const float*>(RateRead.Lock(N*16));
            const float* F=static_cast<const float*>(FluxRead.Lock(NB*16));
            const float* P=static_cast<const float*>(SlopeRead.Lock(N*8));
            if(!A || !F || !P){Passed=false;return;}
            auto Compare=[&](const float* Actual,const auto& Expected,const TCHAR* Name)
            {
                const float* Values=reinterpret_cast<const float*>(Expected.GetData());
                const int32 Length=Expected.Num()*sizeof(Expected[0])/sizeof(float);
                double E2=0,V2=0,Max=0;
                for(int32 J=0;J<Length;++J)
                {
                    Passed &= FMath::IsFinite(Actual[J]);double Delta=double(Actual[J])-Values[J];
                    E2+=Delta*Delta;V2+=double(Values[J])*Values[J];Max=FMath::Max(Max,FMath::Abs(Delta));
                }
                const double Relative=V2>0?FMath::Sqrt(E2/V2):FMath::Sqrt(E2);
                Passed &= Relative<2e-5 && Max<1e-3;
                Records.Add(FString::Printf(TEXT("case%d %s max %.9g relative %.9g"),Index,Name,Max,Relative));
            };
            Compare(A,C.Rate,TEXT("rate"));Compare(F,C.Flux,TEXT("boundary flux"));Compare(P,C.Slope,TEXT("bed slope"));
            for(int32 K: {0,3})
            {
                double Sum=0,Magnitude=0;
                for(int32 J=0;J<N;++J){Sum+=double(A[4*J+K])*C.Dx*C.Dx;Magnitude+=FMath::Abs(double(A[4*J+K]))*C.Dx*C.Dx;}
                for(int32 J=0;J<NB;++J)
                {
                    const bool Low=J<C.Size.Y || (J>=2*C.Size.Y && J<2*C.Size.Y+C.Size.X);
                    Sum+=(Low?-1:1)*double(F[4*J+K])*C.Dx;Magnitude+=FMath::Abs(double(F[4*J+K]))*C.Dx;
                }
                Passed &= FMath::Abs(Sum)<=2e-6*Magnitude;
                Records.Add(FString::Printf(TEXT("case%d component%d exterior balance %.9g magnitude %.9g"),Index,K,Sum,Magnitude));
            }
            // Four uniform throughflows, hydrostatic stepped lake, dry domain.
            if(Index<12)for(int32 J=0;J<N*4;++J)Passed &= A[J]==0;
            RateRead.Unlock();FluxRead.Unlock();SlopeRead.Unlock();
        }
    });
    FlushRenderingCommands();TestTrue(TEXT("Invalid exterior descriptors rejected"),Rejected);
    TestTrue(TEXT("Exterior GPU transport matches CPU, conserves boundary flux, preserves rest and refuses invalid ghosts"),Passed);
    for(const auto& R:Records)AddInfo(R);if(!Error.IsEmpty())AddError(Error);return !HasAnyErrors();
}
#endif
