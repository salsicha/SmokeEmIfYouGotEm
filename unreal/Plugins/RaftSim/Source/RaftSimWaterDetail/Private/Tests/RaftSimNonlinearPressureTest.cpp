#include "Misc/AutomationTest.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/FileHelper.h"
#include "Serialization/MemoryReader.h"
#include "RaftSimNonlinearPressureGPU.h"
#include "RaftSimNonlinearAccelerationGPU.h"
#include "RaftSimTotalDepthTransportGPU.h"
#include "RenderGraphUtils.h"
#include "RenderingThread.h"
#include "RHIGPUReadback.h"
#include <limits>

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FNonlinearPressureTest,"RaftSim.WaterDetail.NonlinearPressureGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FNonlinearPressureTest::RunTest(const FString&)
{
    if(GUsingNullRHI || GMaxRHIFeatureLevel<ERHIFeatureLevel::SM5)
    { AddError(TEXT("Actual GPU required for full nonlinear pressure verification"));return false; }
    struct FCase
    {
        FIntPoint Size;bool Periodic;float Dx;
        TArray<FVector2f> Geometry,Slope,Force,Boundary;
        TArray<FVector4f> State,Rate,RHS,Correction,Pressure;
        TArray<float> Fraction;TArray<uint32> Pairs;
    };
    TArray<FCase> Cases;
    for(bool BoundaryFixture:{false,true})
    {
        FString File;TArray<uint8> Bytes;
        const TCHAR* Flag=BoundaryFixture?TEXT("RaftSimPrescribedPressureFixture="):TEXT("RaftSimNonlinearPressureFixture=");
        if(!FParse::Value(FCommandLine::Get(),Flag,File) || !FFileHelper::LoadFileToArray(Bytes,*File))
        { AddError(FString::Printf(TEXT("Missing reference fixture: -%s<binary>"),Flag));return false; }
        FMemoryReader Reader(Bytes,true);uint32 Magic=0,Version=0,Count=0;Reader<<Magic<<Version<<Count;
        if(Magic!=0x52535046u || Version!=(BoundaryFixture?2u:1u) || Count<5 || Count>64)
        { AddError(TEXT("Invalid nonlinear pressure reference fixture header"));return false; }
        for(uint32 Index=0;Index<Count;++Index)
        {
            uint32 NX=0,NY=0,Periodic=0;float Dx=0;Reader<<NX<<NY<<Periodic<<Dx;
            if(NX<1 || NY<1 || NX>512 || NY>512 || Periodic>1 || (BoundaryFixture && Periodic) || !FMath::IsFinite(Dx) || Dx<=0)
            { AddError(TEXT("Invalid fixture dimensions"));return false; }
            const int32 N=NX*NY;FCase& C=Cases.AddDefaulted_GetRef();C.Size=FIntPoint(NX,NY);C.Periodic=Periodic!=0;C.Dx=Dx;
            auto Read=[&](auto& Array,int32 Elements)
            { Array.SetNumUninitialized(Elements);const int64 Size=sizeof(Array[0])*int64(Elements);if(Reader.Tell()+Size>Reader.TotalSize()){Reader.SetError();return;}Reader.Serialize(Array.GetData(),Size); };
            Read(C.Geometry,N);Read(C.State,N);Read(C.Rate,N);Read(C.Slope,N);Read(C.Fraction,N);Read(C.Pairs,N);
            Read(C.RHS,N);Read(C.Correction,N);Read(C.Pressure,N);Read(C.Force,N);
            if(BoundaryFixture)Read(C.Boundary,2*(NX+NY));
            if(Reader.IsError()){AddError(TEXT("Truncated reference fixture"));return false;}
        }
        if(Reader.Tell()!=Reader.TotalSize()){AddError(TEXT("Unexpected fixture trailing bytes"));return false;}
    }
    bool Passed=true,Rejected=true;TArray<FString> Records;FString Error;
    ENQUEUE_RENDER_COMMAND(RaftSimNonlinearPressureTest)([&](FRHICommandListImmediate& Cmd)
    {
        for(bool Fused:{false,true})
        for(int32 Index=0;Index<Cases.Num()+6;++Index)
        {
            const bool BadState=Index==Cases.Num(),BadRate=Index==Cases.Num()+1,BadFraction=Index==Cases.Num()+2;
            const bool BadBoundary=Index==Cases.Num()+3,BadBoundaryRate=Index==Cases.Num()+4;
            const bool BadNegativeDepth=Index==Cases.Num()+5;
            FCase C=Cases[FMath::Min(Index,Cases.Num()-1)];const int32 N=C.Size.X*C.Size.Y;
            if(BadState)C.State.Last().X+=.5f;
            if(BadRate)C.Rate.Last().X=std::numeric_limits<float>::infinity();
            if(BadFraction)C.Fraction.Last()=-1;
            if(BadBoundary)C.Boundary.Last().X=std::numeric_limits<float>::quiet_NaN();
            if(BadBoundaryRate)C.Boundary.Last().Y=std::numeric_limits<float>::infinity();
            if(BadNegativeDepth)
            {uint32 Bits=0x80000001u;FMemory::Memcpy(&C.State.Last().X,&Bits,4);FMemory::Memcpy(&C.Geometry.Last().X,&Bits,4);}
            FRDGBuilder Graph(Cmd);
            auto Upload=[&](const auto& Array,const TCHAR* Name)
            { return CreateStructuredBuffer(Graph,Name,MakeArrayView(Array)); };
            auto State=Upload(C.State,TEXT("PressureTest.State")),Rate=Upload(C.Rate,TEXT("PressureTest.Rate"));
            auto Geometry=Upload(C.Geometry,TEXT("PressureTest.Geometry")),Pairs=Upload(C.Pairs,TEXT("PressureTest.Pairs"));
            auto Slope=Upload(C.Slope,TEXT("PressureTest.Slope")),Fraction=Upload(C.Fraction,TEXT("PressureTest.Fraction"));
            FRDGBufferRef Boundary=C.Boundary.IsEmpty()?nullptr:Upload(C.Boundary,TEXT("PressureTest.Boundary"));
            FRaftSimTotalDepthTransportResult Transport;
            bool UniformExterior=Boundary && Index<Cases.Num();
            for(int32 I=0;I<N && UniformExterior;++I)
                UniformExterior=C.State[I]==C.State[0] && C.Geometry[I].Y==0 && C.Rate[I]==FVector4f(0,0,0,0);
            for(int32 I=0;I<C.Boundary.Num() && UniformExterior;++I)
                UniformExterior=C.Boundary[I].Y==0 && C.Boundary[I].X==
                    (I<2*C.Size.Y?C.State[0].Y:C.State[0].Z)/C.State[0].X;
            if(UniformExterior)
            {
                // Compose the REAL exterior FV dispatch with pressure. No CPU
                // rate/graph/slope is substituted into these throughflow cases.
                TArray<float> Bed,ExteriorBed;Bed.Init(0,N);ExteriorBed.Init(0,C.Boundary.Num());
                TArray<FVector4f> ExteriorState;ExteriorState.Init(C.State[0],C.Boundary.Num());
                Transport=RaftSimTotalDepthTransportGPU(Graph,State,Upload(Bed,TEXT("PressureTest.Bed")),
                    C.Size,C.Dx,false,true,Error,Upload(ExteriorState,TEXT("PressureTest.ExteriorState")),
                    Upload(ExteriorBed,TEXT("PressureTest.ExteriorBed")));
                if(!Transport.HydroRate || !Error.IsEmpty()){Passed=false;Graph.Execute();return;}
                Rate=Transport.HydroRate;Geometry=Transport.Geometry;Pairs=Transport.Pairs;Slope=Transport.PhysicalBedSlope;
                Records.Add(FString::Printf(TEXT("case%d fused=%d pressure consumes actual exterior FV rate/geometry/graph/slope"),Index,Fused));
            }
            if(Index==0)
            {
                Rejected &= !RaftSimNonlinearPressureGPU(Graph,State,Rate,Geometry,Pairs,Slope,Fraction,C.Size,0,C.Periodic,Error).Force;
                Rejected &= !RaftSimNonlinearPressureGPU(Graph,State,Geometry,Geometry,Pairs,Slope,Fraction,C.Size,C.Dx,C.Periodic,Error).Force;
                Rejected &= !RaftSimNonlinearPressureGPU(Graph,State,Rate,Geometry,Pairs,Slope,nullptr,C.Size,C.Dx,C.Periodic,Error).Force;
            }
            if(Boundary && Index==Cases.Num()-1)
            {
                Rejected &= !RaftSimNonlinearPressureGPU(Graph,State,Rate,Geometry,Pairs,Slope,Fraction,C.Size,C.Dx,true,Error,Fused,Boundary).Force;
                Rejected &= !RaftSimNonlinearPressureGPU(Graph,State,Rate,Geometry,Pairs,Slope,Fraction,C.Size,C.Dx,false,Error,Fused,Slope).Force;
                TArray<float> WrongStride;WrongStride.Init(0,C.Boundary.Num());
                auto Bad=Upload(WrongStride,TEXT("PressureTest.WrongBoundaryStride"));
                Rejected &= !RaftSimNonlinearPressureGPU(Graph,State,Rate,Geometry,Pairs,Slope,Fraction,C.Size,C.Dx,false,Error,Fused,Bad).Force;
            }
            auto Result=RaftSimNonlinearPressureGPU(Graph,State,Rate,Geometry,Pairs,Slope,Fraction,C.Size,C.Dx,C.Periodic,Error,Fused,Boundary);
            if(!Result.Force || !Error.IsEmpty()){Passed=false;Graph.Execute();return;}
            FRenderQueryPoolRHIRef TimingPool;TArray<FRHIPooledRenderQuery> TimingQueries;
            TArray<TRefCountPtr<FRDGPooledBuffer>> KeepOutput,KeepResidual;
            TArray<int32> IntervalModes;
            if(!Fused && (Index==5 || Index==6) && GSupportsTimestampRenderQueries && FParse::Param(FCommandLine::Get(),TEXT("RaftSimPressureTiming")))
            {
                constexpr int32 Samples=16,Intervals=Samples*4;
                TimingPool=RHICreateRenderQueryPool(RQT_AbsoluteTime,Intervals*2);
                KeepOutput.SetNum(Intervals);KeepResidual.SetNum(Intervals);
                for(int32 I=0;I<Intervals*2;++I)TimingQueries.Add(TimingPool->AllocateQuery());
                for(int32 I=0;I<Intervals;++I)
                {
                    // Rotate the four full/operator x legacy/fused modes so no
                    // path always runs first. Use identical actual GPU RHSs.
                    const int32 Mode=(I%4+I/4)%4;
                    const bool OperatorOnly=Mode%2==0,TimedFused=Mode>=2;
                    IntervalModes.Add(Mode);
                    auto* Begin=TimingQueries[2*I].GetQuery();auto* End=TimingQueries[2*I+1].GetQuery();
                    Graph.AddPass(RDG_EVENT_NAME("PressureTest.TimestampBegin"),ERDGPassFlags::None,
                        [Begin](FRHICommandList& List){List.EndRenderQuery(Begin);});
                    FRDGBufferRef Output=nullptr,Residual=nullptr;
                    if(OperatorOnly)
                    {
                        auto Timed=RaftSimSolveNonlinearAccelerationGPU(Graph,Geometry,Pairs,Result.RightHandSide,C.Size,
                            C.Dx,FVector2f(.4052787713439809f,.03916567310046354f),C.Periodic,40,Error,Slope,true,Fraction,TimedFused);
                        Output=Timed.Solution;Residual=Timed.Residual;
                    }
                    else
                    {
                        auto Timed=RaftSimNonlinearPressureGPU(Graph,State,Rate,Geometry,Pairs,Slope,Fraction,C.Size,C.Dx,C.Periodic,Error,TimedFused);
                        Output=Timed.Force;Residual=Timed.Residual;
                    }
                    if(!Output || !Residual || !Error.IsEmpty()){Passed=false;Graph.Execute();return;}
                    // Both paths retain the solution-dependent output AND true
                    // residual. Neither includes uploads/readback or transport.
                    Graph.QueueBufferExtraction(Output,&KeepOutput[I]);Graph.QueueBufferExtraction(Residual,&KeepResidual[I]);
                    Graph.AddPass(RDG_EVENT_NAME("PressureTest.TimestampEnd"),ERDGPassFlags::None,
                        [End](FRHICommandList& List){List.EndRenderQuery(End);});
                }
            }
            FRHIGPUBufferReadback ForceRead(TEXT("PressureTest.ForceRead")),RHSRead(TEXT("PressureTest.RHSRead")),
                CorrectionRead(TEXT("PressureTest.CorrectionRead")),PressureRead(TEXT("PressureTest.PressureRead")),
                ResidualRead(TEXT("PressureTest.ResidualRead")),DiagRead(TEXT("PressureTest.DiagRead")),SolveRead(TEXT("PressureTest.SolveRead"));
            FRHIGPUBufferReadback TransportDiag(TEXT("PressureTest.TransportDiag")),TransportRate(TEXT("PressureTest.TransportRate"));
            if(UniformExterior)
            {
                AddEnqueueCopyPass(Graph,&TransportDiag,Transport.Diagnostics,16);
                AddEnqueueCopyPass(Graph,&TransportRate,Transport.HydroRate,N*16);
            }
            AddEnqueueCopyPass(Graph,&ForceRead,Result.Force,N*8);AddEnqueueCopyPass(Graph,&RHSRead,Result.RightHandSide,N*16);
            AddEnqueueCopyPass(Graph,&CorrectionRead,Result.Correction,N*16);AddEnqueueCopyPass(Graph,&PressureRead,Result.Pressure,N*16);
            AddEnqueueCopyPass(Graph,&ResidualRead,Result.Residual,N*16);AddEnqueueCopyPass(Graph,&DiagRead,Result.Diagnostics,16);
            AddEnqueueCopyPass(Graph,&SolveRead,Result.SolverDiagnostics,16);Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle();
            if(UniformExterior)
            {
                const auto* TD=static_cast<const uint32*>(TransportDiag.Lock(16));
                const auto* TR=static_cast<const float*>(TransportRate.Lock(N*16));
                if(!TD || !TR){Passed=false;return;}
                Passed &= TD[0]==0 && TD[1]==0;
                for(int32 I=0;I<N*4;++I)Passed &= TR[I]==0;
                TransportDiag.Unlock();TransportRate.Unlock();
            }
            for(int32 I=0;I<TimingQueries.Num()/2;++I)
            {
                uint64 Begin=0,End=0;
                if(RHIGetRenderQueryResult(TimingQueries[2*I].GetQuery(),Begin,true) &&
                    RHIGetRenderQueryResult(TimingQueries[2*I+1].GetQuery(),End,true) && End>=Begin)
                    Records.Add(FString::Printf(TEXT("GPU paired pressure case%d sample%d %s fused=%d %.6f ms (actual GPU RHS; true residual retained; no transport/RK/render; not FPS)"),Index,I/4,
                        IntervalModes[I]%2==0?TEXT("operator"):TEXT("full"),IntervalModes[I]>=2,(End-Begin)/1000.));
                else Records.Add(TEXT("Full pressure GPU timestamp unavailable"));
            }
            const auto* D=static_cast<const uint32*>(DiagRead.Lock(16));const auto* S=static_cast<const uint32*>(SolveRead.Lock(16));
            if(!D || !S){Passed=false;return;}
            if(BadState || BadRate || BadFraction || BadBoundary || BadBoundaryRate || BadNegativeDepth)Passed &= D[0]>0;
            else
            {
                Passed &= D[0]==0 && D[1]==0 && S[0]==0 && S[1]==0 && S[2]<=40 && S[3]<=40;
                auto Compare=[&](FRHIGPUBufferReadback& Read,const auto& Expected,const TCHAR* Name)
                {
                    const int32 Components=sizeof(Expected[0])/4;
                    const float* Actual=static_cast<const float*>(Read.Lock(N*Components*4));
                    const float* Ref=reinterpret_cast<const float*>(Expected.GetData());
                    if(!Actual){Passed=false;return;}
                    double Error2=0,Norm2=0,MaxError=0;
                    for(int32 I=0;I<N*Components;++I)
                    {
                        const double E=double(Actual[I])-Ref[I];Passed &= FMath::IsFinite(Actual[I]);
                        MaxError=FMath::Max(MaxError,FMath::Abs(E));Error2+=E*E;Norm2+=double(Ref[I])*Ref[I];
                    }
                    const double Relative=Norm2>0?FMath::Sqrt(Error2/Norm2):FMath::Sqrt(Error2);
                    Passed &= Relative<2e-5 && (FCString::Strcmp(Name,TEXT("Force"))!=0 || MaxError<1e-3);
                    Records.Add(FString::Printf(TEXT("case%d fused=%d %dx%d %s max error %.9g relative %.9g"),Index,Fused,C.Size.X,C.Size.Y,Name,MaxError,Relative));
                    Read.Unlock();
                };
                Compare(RHSRead,C.RHS,TEXT("RHS"));Compare(CorrectionRead,C.Correction,TEXT("Correction"));
                Compare(PressureRead,C.Pressure,TEXT("Pressure"));Compare(ForceRead,C.Force,TEXT("Force"));
                const float* R=static_cast<const float*>(ResidualRead.Lock(N*16));double Residual2=0,Norm2=0;
                if(!R){Passed=false;return;}
                for(int32 I=0;I<N*4;++I){Passed &= FMath::IsFinite(R[I]);Residual2+=double(R[I])*R[I];const double V=reinterpret_cast<const float*>(C.RHS.GetData())[I];Norm2+=V*V;}
                const double Relative=Norm2>0?FMath::Sqrt(Residual2/Norm2):FMath::Sqrt(Residual2);
                Passed &= Relative<2e-5;ResidualRead.Unlock();
                Records.Add(FString::Printf(TEXT("case%d fused=%d true residual %.9g iterations %u/%u diagnostics %u/%u/%u/%u"),Index,Fused,Relative,S[2],S[3],D[0],D[1],S[0],S[1]));
            }
            DiagRead.Unlock();SolveRead.Unlock();
        }
    });
    FlushRenderingCommands();TestTrue(TEXT("invalid pressure descriptors rejected"),Rejected);
    TestTrue(TEXT("full nonlinear GPU RHS, solve, reconstruction and force match independent CPU reference"),Passed);
    for(const auto& Record:Records)AddInfo(Record);if(!Error.IsEmpty())AddError(Error);
    return !HasAnyErrors();
}
#endif
