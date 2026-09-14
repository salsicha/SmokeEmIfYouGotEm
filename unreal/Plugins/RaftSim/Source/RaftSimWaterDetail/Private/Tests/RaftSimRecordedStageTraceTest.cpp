#include "Misc/AutomationTest.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "RaftSimBreakingFrontGPU.h"
#include "RaftSimTemporalBoundaryGPU.h"
#include "RaftSimTotalDepthStateGPU.h"
#include "RenderGraphUtils.h"
#include "RenderingThread.h"
#include "RHIGPUReadback.h"

#if WITH_DEV_AUTOMATION_TESTS && WITH_UNREAL_DEVELOPER_TOOLS
// Keep this optional capture diagnostic aligned with the module's Json dependency.
#include "Serialization/JsonSerializer.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRecordedStageTraceTest,"RaftSim.Diagnostics.NonlinearRecordedStages",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRecordedStageTraceTest::RunTest(const FString&)
{
    FString Input,Prefix,Json;
    if(GUsingNullRHI || !FParse::Value(FCommandLine::Get(),TEXT("RaftSimRecordedOwnerAudit="),Input) ||
        !FParse::Value(FCommandLine::Get(),TEXT("RaftSimRecordedStagePrefix="),Prefix) ||
        FPaths::FileExists(Prefix+TEXT(".bin")) || FPaths::FileExists(Prefix+TEXT(".json")) || !FFileHelper::LoadFileToString(Json,*Input))
    {AddError(TEXT("Actual GPU, recorded owner audit and fresh stage output prefix required"));return false;}
    TSharedPtr<FJsonObject> Root;auto Reader=TJsonReaderFactory<>::Create(Json);
    if(!FJsonSerializer::Deserialize(Reader,Root) || !Root || Root->GetStringField(TEXT("schema"))!=TEXT("raftsim.live_nonlinear_owner_audit.v1"))
    {AddError(TEXT("Invalid recorded owner source"));return false;}
    FString Limiter=TEXT("binary");Root->TryGetStringField(TEXT("shoreline_limiter"),Limiter);
    const bool Continuous=Limiter==TEXT("continuous");
    const bool Unscaled=Limiter==TEXT("unscaled");
    const auto& Summary=Root->GetArrayField(TEXT("summary"));
    if((Limiter!=TEXT("binary") && !Continuous && !Unscaled) || Summary.Num()!=4 || Summary[3]->AsNumber()!=(Unscaled?5:Continuous?3:1))
    {AddError(TEXT("Captured model does not match persisted evolution mode"));return false;}
    // Reproducing a retained failure is a separate, explicit diagnostic. Never
    // shorten its source interval to the stalled clock or reset the failed dt.
    const bool CaptureRetainedFailure=FParse::Param(FCommandLine::Get(),TEXT("RaftSimRecordedRetainedFailure"));
    const bool SourceFailed=Summary[2]->AsNumber()==2;
    if(CaptureRetainedFailure!=SourceFailed || (!SourceFailed && Summary[2]->AsNumber()!=1))
    {AddError(TEXT("Completed history or explicitly requested retained failure required"));return false;}
    const auto& ExpectedDiagnostics=Root->GetArrayField(TEXT("diagnostics"));
    if(ExpectedDiagnostics.Num()!=4 || (SourceFailed && (Summary[0]->AsNumber()<1 || Summary[0]->AsNumber()>4096)))
    {AddError(TEXT("Invalid retained failure diagnostics or bounded trial count"));return false;}
    struct FObservation{TArray<FVector4f> State,Exterior;TArray<FVector2f> Reference;TArray<float> Bed,ExteriorBed,Face;double Time=0;FVector2f Origin=FVector2f::ZeroVector;};
    TArray<FObservation> Sources;const auto& Raw=Root->GetArrayField(TEXT("observations"));
    if(Raw.Num()<2 || Raw.Num()>256){AddError(TEXT("Invalid bounded source count"));return false;}
    const auto& EndClock=Root->GetArrayField(TEXT("progress"));
    if(EndClock.Num()!=4){AddError(TEXT("Invalid captured owner clock"));return false;}
    const double Target=EndClock[0]->AsNumber()+EndClock[1]->AsNumber();
    const FVector4f ExpectedClock(float(EndClock[0]->AsNumber()),float(EndClock[1]->AsNumber()),
        float(EndClock[2]->AsNumber()),float(EndClock[3]->AsNumber()));
    if(SourceFailed && (ExpectedClock.Z<=0 || ExpectedClock.W!=0))
    {AddError(TEXT("Retained failure requires the original incomplete interval and latched zero dt"));return false;}
    const int32 ExpectedMoves=Root->GetIntegerField(TEXT("completed_moves"));
    if(ExpectedMoves<0 || ExpectedMoves>32){AddError(TEXT("Invalid recorded move count"));return false;}
    double CaptureBegin=0,CaptureEnd=TNumericLimits<double>::Max();
    const bool CapturePolynomials=FParse::Param(FCommandLine::Get(),TEXT("RaftSimRecordedPolynomials"));
    const bool CaptureEndpoints=FParse::Param(FCommandLine::Get(),TEXT("RaftSimRecordedEndpoints"));
    FParse::Value(FCommandLine::Get(),TEXT("RaftSimRecordedCaptureBegin="),CaptureBegin);
    FParse::Value(FCommandLine::Get(),TEXT("RaftSimRecordedCaptureEnd="),CaptureEnd);
    if(!FMath::IsFinite(Target) || !FMath::IsFinite(CaptureBegin) || !FMath::IsFinite(CaptureEnd) || CaptureBegin<0 || CaptureEnd<=CaptureBegin)
    {AddError(TEXT("Invalid bounded capture time range"));return false;}
    constexpr int32 N=128*128,NB=512;bool Valid=true;
    auto ReadValues=[&](const TSharedPtr<FJsonObject>& O,const TCHAR* Key,auto& A,int32 Count,int32 Components)
    {
        const auto& Values=O->GetArrayField(Key);if(Values.Num()!=Count*Components){Valid=false;return;}
        A.SetNumUninitialized(Count);auto* Data=reinterpret_cast<float*>(A.GetData());
        for(int32 I=0;I<Values.Num();++I){Data[I]=float(Values[I]->AsNumber());Valid &= FMath::IsFinite(Data[I]);}
    };
    for(const auto& Value:Raw)
    {
        // Include equal-time closing/opening observations at the target, plus
        // its right bracket if present. Never evolve beyond the captured clock.
        if(Sources.Num() && Sources.Last().Time>Target)break;
        const auto O=Value->AsObject();FObservation A;A.Time=O->GetNumberField(TEXT("native_seconds"));
        Valid &= O->GetIntegerField(TEXT("nx"))==128 && O->GetIntegerField(TEXT("ny"))==128 && O->GetNumberField(TEXT("cell_meters"))==.5;
        A.Origin=FVector2f(float(O->GetNumberField(TEXT("origin_x"))),float(O->GetNumberField(TEXT("origin_y"))));
        Valid &= FMath::IsFinite(A.Time) && !A.Origin.ContainsNaN();
        ReadValues(O,TEXT("state"),A.State,N,4);ReadValues(O,TEXT("bed"),A.Bed,N,1);
        if(O->HasField(TEXT("reference")))ReadValues(O,TEXT("reference"),A.Reference,N,2);
        ReadValues(O,TEXT("exterior_state"),A.Exterior,NB,4);ReadValues(O,TEXT("exterior_bed"),A.ExteriorBed,NB,1);
        ReadValues(O,TEXT("face_normal_velocity"),A.Face,NB,1);
        if(Sources.Num() && Valid)
        {
            const auto& Last=Sources.Last();
            if(A.Origin==Last.Origin)Valid &= A.Time>Last.Time && A.Bed==Last.Bed && A.ExteriorBed==Last.ExteriorBed;
            else
            {
                const FVector2f Shift=(A.Origin-Last.Origin)/.5f;
                const FIntPoint Offset(FMath::TruncToInt(Shift.X),FMath::TruncToInt(Shift.Y));
                Valid &= A.Time==Last.Time && Shift==FVector2f(Offset) &&
                    FMath::Abs(Offset.X)<128 && FMath::Abs(Offset.Y)<128 && A.Reference.Num()==N && Last.Reference.Num()==N;
                if(Valid)for(int32 Y=0;Y<128;++Y)for(int32 X=0;X<128;++X)
                {
                    const FIntPoint P=FIntPoint(X,Y)+Offset;
                    if(P.X<0 || P.Y<0 || P.X>=128 || P.Y>=128)continue;
                    const int32 New=Y*128+X,Old=P.Y*128+P.X;
                    Valid &= A.State[New]==Last.State[Old] && A.Bed[New]==Last.Bed[Old] && A.Reference[New]==Last.Reference[Old];
                }
            }
        }
        Sources.Add(MoveTemp(A));
    }
    TArray<FVector4f> Expected;ReadValues(Root,TEXT("state"),Expected,N,4);
    if(!Valid || Sources.Num()<2 || Sources[0].Time>Target || Sources.Last().Time<Target)
    {AddError(TEXT("Invalid recorded arrays, exact moving overlap or target bracket"));return false;}
    bool Passed=true;FString Error;TArray<uint8> Bytes;TArray<TSharedPtr<FJsonValue>> Records;
    double End=Sources[0].Time;bool FinalExact=false,RetainedFailureExact=false;
    int32 EvolutionTrials=0,ReplayMoves=0;
    ENQUEUE_RENDER_COMMAND(RecordedNonlinearStages)([&](FRHICommandListImmediate& Cmd)
    {
        TRefCountPtr<FRDGPooledBuffer> State;FVector4f Clock(float(End),float(End-double(float(End))),0,0);
        for(int32 Interval=0;Interval+1<Sources.Num() && (End<Target || ReplayMoves<ExpectedMoves);++Interval)
        {
            const auto& A=Sources[Interval];const auto& B=Sources[Interval+1];
            if(A.Origin!=B.Origin)
            {
                if(!State || End!=A.Time || A.Time!=B.Time || Clock.Z!=0 || ReplayMoves>=ExpectedMoves)
                {Error=TEXT("Recorded move does not follow a completed old-window interval");Passed=false;return;}
                FRDGBuilder Graph(Cmd);const FVector2f Shift=(B.Origin-A.Origin)/.5f;
                auto R=RaftSimTransferTotalDepthStateGPU(Graph,Graph.RegisterExternalBuffer(State),
                    CreateStructuredBuffer(Graph,TEXT("Recorded.EnteringState"),B.State),
                    CreateStructuredBuffer(Graph,TEXT("Recorded.EnteringReference"),B.Reference),
                    FIntPoint(128,128),FIntPoint(int32(Shift.X),int32(Shift.Y)),.5f,Error);
                if(!R.State){Passed=false;Graph.Execute();return;}
                FRHIGPUBufferReadback DRead(TEXT("Recorded.MoveDiagnostics")),SRead(TEXT("Recorded.MoveState"));
                AddEnqueueCopyPass(Graph,&DRead,R.Diagnostics,16);AddEnqueueCopyPass(Graph,&SRead,R.State,N*16);
                Graph.QueueBufferExtraction(R.State,&State);Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle();
                const auto* D=static_cast<const uint32*>(DRead.Lock(16));const void* Data=SRead.Lock(N*16);
                const uint32 Overlap=(128-FMath::Abs(int32(Shift.X)))*(128-FMath::Abs(int32(Shift.Y)));
                Passed &= D && Data && D[0]==0 && D[1]==0 && D[2]==Overlap && D[3]==N-Overlap;
                FinalExact=Data && FMemory::Memcmp(Data,Expected.GetData(),N*16)==0;
                if(D)DRead.Unlock();if(Data)SRead.Unlock();if(!Passed)return;
                ++ReplayMoves;continue;
            }
            const bool FailureInterval=SourceFailed && A.Time<=Target && Target<B.Time;
            const double Stop=FailureInterval?B.Time:FMath::Min(B.Time,Target);
            Clock.Z=float(Stop-A.Time);Clock.W=FMath::Min(1.f/120.f,Clock.Z);
            uint32 AcceptedTrials=0;
            for(int32 Trial=0;Trial<4096 && Clock.Z>0;++Trial)
            {
                const double Begin=double(Clock.X)+Clock.Y;
                // Endpoint-only diagnostics still evolve EVERY original trial
                // and move. Only readback retention is sampled; state, source,
                // timestep, counters and the final-live equality gate are not.
                const bool CaptureStages=Begin>=CaptureBegin && Begin<CaptureEnd && (!CaptureEndpoints || Trial==0);
                if(CaptureStages && Records.Num()>=(CapturePolynomials?64:128)){Error=TEXT("Recorded trace memory budget exhausted; capture incomplete");Passed=false;return;}
                FRDGBuilder Graph(Cmd);
                auto Upload=[&](const auto& V,const TCHAR* Name){return CreateStructuredBuffer(Graph,Name,MakeArrayView(V));};
                auto S=State?Graph.RegisterExternalBuffer(State):Upload(A.State,TEXT("Recorded.Initial"));
                TArray<FVector4f> Clocks={Clock};auto P=Upload(Clocks,TEXT("Recorded.Clock"));
                auto Bed=Upload(A.Bed,TEXT("Recorded.Bed")),EB=Upload(A.ExteriorBed,TEXT("Recorded.ExteriorBed"));
                FRaftSimTemporalBoundaryEndpoint First{Upload(A.Exterior,TEXT("Recorded.First")),EB,Upload(A.Face,TEXT("Recorded.FirstFace")),A.Time};
                FRaftSimTemporalBoundaryEndpoint Second{Upload(B.Exterior,TEXT("Recorded.Second")),EB,Upload(B.Face,TEXT("Recorded.SecondFace")),B.Time};
                struct FStage{FRDGBufferRef Input=nullptr,Fraction=nullptr;FRaftSimTotalDepthTransportResult FV;};
                FStage Stages[2];int32 StageIndex=0;
                auto Select=[&](FRDGBuilder& G,FRDGBufferRef InputState,const FRaftSimTotalDepthTransportResult& FV)
                {
                    auto& Stage=Stages[StageIndex++];Stage.Input=InputState;Stage.FV=FV;
                    Stage.Fraction=RaftSimClassifyBreakingFrontGPU(G,FV.Geometry,FV.HydroRate,FV.Pairs,FIntPoint(128,128),.5f,false,Error).Fraction;
                    return Stage.Fraction;
                };
                FRaftSimTotalDepthBoundaryProvider Provider=[&](FRDGBuilder& G,FRDGBufferRef,FRDGBufferRef C,FRDGBufferRef Info)
                {return RaftSimSampleTemporalBoundaryGPU(G,First,Second,C,Info,FIntPoint(128,128),Error).Input;};
                auto R=RaftSimTryTotalDepthStepGPU(Graph,S,Bed,P,FIntPoint(128,128),.5f,false,true,Select,Error,Provider,nullptr,Stop,Continuous,Unscaled);
                if(!R.State || StageIndex!=2){Passed=false;Graph.Execute();return;}
                TArray<TUniquePtr<FRHIGPUBufferReadback>> Reads;TArray<uint32> Sizes;
                auto Capture=[&](FRDGBufferRef Buffer,uint32 Length)
                {
                    auto& Read=Reads.Add_GetRef(MakeUnique<FRHIGPUBufferReadback>(TEXT("Recorded.Stage")));
                    AddEnqueueCopyPass(Graph,Read.Get(),Buffer,Length);Sizes.Add(Length);
                };
                if(CaptureStages)for(int32 K=0;K<2;++K)
                {
                    Capture(Stages[K].Input,N*16);Capture(Stages[K].FV.HydroRate,N*16);Capture(Stages[K].FV.Geometry,N*8);
                    Capture(Stages[K].FV.Pairs,N*4);Capture(Stages[K].Fraction,N*4);
                    Capture(K==0?R.FirstPressureForce:R.SecondPressureForce,N*8);
                    if(CapturePolynomials)
                    {
                        Capture(Stages[K].FV.RawX,N*16);Capture(Stages[K].FV.RawY,N*16);
                        Capture(Stages[K].FV.SlopeX,N*16);Capture(Stages[K].FV.SlopeY,N*16);
                    }
                }
                const int32 FinalIndex=Reads.Num();
                Capture(R.State,N*16);Capture(R.Progress,16);Capture(R.Info,16);Capture(R.Diagnostics,16);
                Graph.QueueBufferExtraction(R.State,&State);Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle();
                const int64 Offset=Bytes.Num();uint32 Flags[4]{};FVector4f Info(0,0,0,0);++EvolutionTrials;
                for(int32 K=0;K<Reads.Num();++K)
                {
                    const void* Data=Reads[K]->Lock(Sizes[K]);if(!Data){Passed=false;return;}
                    if(CaptureStages){const int32 At=Bytes.AddUninitialized(Sizes[K]);FMemory::Memcpy(Bytes.GetData()+At,Data,Sizes[K]);}
                    if(K==FinalIndex+1)FMemory::Memcpy(&Clock,Data,16);if(K==FinalIndex+2)FMemory::Memcpy(&Info,Data,16);
                    if(K==FinalIndex+3)FMemory::Memcpy(Flags,Data,16);
                    if(K==FinalIndex)FinalExact=FMemory::Memcmp(Data,Expected.GetData(),N*16)==0;
                    Reads[K]->Unlock();
                }
                End=double(Clock.X)+Clock.Y;
                AcceptedTrials+=Flags[3];
                if(CaptureStages)
                {
                auto Record=MakeShared<FJsonObject>();Record->SetNumberField(TEXT("interval"),Interval);Record->SetNumberField(TEXT("trial"),Trial);
                Record->SetNumberField(TEXT("byte_offset"),Offset);Record->SetNumberField(TEXT("begin"),Begin);Record->SetNumberField(TEXT("end"),End);
                Record->SetNumberField(TEXT("accepted_dt"),Info.X);Record->SetNumberField(TEXT("attempted_dt"),Info.Y);
                Record->SetNumberField(TEXT("accepted"),Flags[3]);Records.Add(MakeShared<FJsonValueObject>(Record));
                }
                if(Clock.W==0 && Clock.Z>0)
                {
                    RetainedFailureExact=FailureInterval && End==Target && Clock==ExpectedClock && FinalExact &&
                        Trial+1==Summary[0]->AsNumber() && AcceptedTrials==Summary[1]->AsNumber();
                    for(int32 K=0;K<4;++K)RetainedFailureExact &= Flags[K]==ExpectedDiagnostics[K]->AsNumber();
                    Passed &= RetainedFailureExact;
                    if(!RetainedFailureExact)Error=TEXT("Replay failure differs from retained state, clock, trial counters or diagnostics");
                    return;
                }
                if(FailureInterval && (End>Target || Trial+1>=Summary[0]->AsNumber()))
                {Error=TEXT("Replay passed the retained failure clock or trial bound without reproducing it");Passed=false;return;}
            }
            if(Clock.Z!=0){Passed=false;return;}
        }
    });
    FlushRenderingCommands();Passed &= End==Target && FinalExact && Records.Num()>0 && ReplayMoves==ExpectedMoves &&
        (!SourceFailed || RetainedFailureExact);
    auto Report=MakeShared<FJsonObject>();Report->SetStringField(TEXT("schema"),CapturePolynomials?TEXT("raftsim.recorded_nonlinear_stages.v2"):TEXT("raftsim.recorded_nonlinear_stages.v1"));
    Report->SetStringField(TEXT("source"),Input);Report->SetStringField(TEXT("binary"),Prefix+TEXT(".bin"));
    Report->SetStringField(TEXT("shoreline_limiter"),Limiter);
    Report->SetStringField(TEXT("layout"),TEXT("Two stages each: input float4[N], hydro_rate float4[N], geometry float2[N], pairs uint[N], fraction float[N], pressure_force float2[N]; then final_state float4[N], progress float4, info float4, diagnostics uint4. N=128*128, little-endian."));
    if(CapturePolynomials)Report->SetStringField(TEXT("layout"),TEXT("Two stages each: input float4[N], hydro_rate float4[N], geometry float2[N], pairs uint[N], fraction float[N], pressure_force float2[N], raw_x float4[N], raw_y float4[N], slope_x float4[N], slope_y float4[N]; then final_state float4[N], progress float4, info float4, diagnostics uint4. N=128*128, little-endian."));
    Report->SetBoolField(TEXT("final_state_exact_to_live"),FinalExact);Report->SetBoolField(TEXT("completed"),Passed);
    Report->SetBoolField(TEXT("source_evolution_failed"),SourceFailed);
    Report->SetBoolField(TEXT("retained_failure_exact"),RetainedFailureExact);
    Report->SetNumberField(TEXT("end_seconds"),End);Report->SetArrayField(TEXT("trials"),Records);
    Report->SetNumberField(TEXT("evolution_trials"),EvolutionTrials);
    Report->SetNumberField(TEXT("replayed_moves"),ReplayMoves);
    Report->SetBoolField(TEXT("endpoint_captures_only"),CaptureEndpoints);
    Report->SetNumberField(TEXT("capture_begin_seconds"),CaptureBegin);Report->SetNumberField(TEXT("capture_end_seconds"),CaptureEnd);
    FString Output;auto Writer=TJsonWriterFactory<>::Create(&Output);FJsonSerializer::Serialize(Report,Writer);
    Passed &= FFileHelper::SaveArrayToFile(Bytes,*(Prefix+TEXT(".bin"))) && FFileHelper::SaveStringToFile(Output,*(Prefix+TEXT(".json")));
    AddInfo(FString::Printf(TEXT("Recorded %d trials, %d bytes, final live state exact%d, end%.17g"),Records.Num(),Bytes.Num(),FinalExact,End));
    TestTrue(TEXT("Recorded-stage replay reproduces actual live GPU final state without changing source or solver"),Passed);
    if(!Error.IsEmpty())AddError(Error);return !HasAnyErrors();
}
#endif
