#include "Misc/AutomationTest.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/MemoryReader.h"
#include "Serialization/JsonSerializer.h"
#include "RaftSimBreakingFrontGPU.h"
#include "RaftSimTemporalBoundaryGPU.h"
#include "RaftSimTotalDepthAdvanceGPU.h"
#include "RenderGraphUtils.h"
#include "RenderingThread.h"
#include "RHIGPUReadback.h"

#if WITH_DEV_AUTOMATION_TESTS && WITH_UNREAL_DEVELOPER_TOOLS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCapturedOwnerTrialTest,"RaftSim.Diagnostics.CapturedOwnerTrial",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCapturedOwnerTrialTest::RunTest(const FString&)
{
    FString Input,Prefix,Error;TArray<uint8> Bytes;
    if(GUsingNullRHI || !FParse::Value(FCommandLine::Get(),TEXT("RaftSimCapturedTrialInput="),Input) ||
        !FParse::Value(FCommandLine::Get(),TEXT("RaftSimCapturedTrialPrefix="),Prefix) ||
        FPaths::FileExists(Prefix+TEXT(".json")) || FPaths::FileExists(Prefix+TEXT(".bin")) ||
        !FFileHelper::LoadFileToArray(Bytes,*Input) || Bytes.Num()<36)
    {AddError(TEXT("Actual GPU, captured trial input and fresh output prefix required"));return false;}
    FMemoryReader Reader(Bytes,true);uint32 Magic=0,Version=0,X=0,Y=0;float Dx=0;double Begin=0,End=0;
    Reader<<Magic<<Version<<X<<Y<<Dx<<Begin<<End;
    if(Magic!=0x52535452 || (Version!=1 && Version!=2) || X!=128 || Y!=128 || Dx!=.5f || !FMath::IsFinite(Begin) || !FMath::IsFinite(End) || Begin>=End)
    {AddError(TEXT("Invalid captured trial header"));return false;}
    constexpr int32 N=128*128,NB=512;
    TArray<FVector4f> Clock,State,First,Second;TArray<float> Bed,EB,FaceA,FaceB;
    auto Read=[&](auto& A,int32 Count)
    {
        const int64 Length=sizeof(A[0])*int64(Count);
        if(Reader.Tell()+Length>Reader.TotalSize()){Reader.SetError();return;}
        A.SetNumUninitialized(Count);Reader.Serialize(A.GetData(),Length);
    };
    Read(Clock,1);Read(State,N);Read(Bed,N);Read(First,NB);Read(Second,NB);Read(EB,NB);Read(FaceA,NB);Read(FaceB,NB);
    TArray<uint32> RetainedSummary,RetainedDiagnostics;TArray<FVector4f> RetainedLedger;
    if(Version==2){Read(RetainedSummary,4);Read(RetainedDiagnostics,4);Read(RetainedLedger,NB);}
    if(Reader.IsError() || Reader.Tell()!=Reader.TotalSize() || Clock[0].ContainsNaN() || Clock[0].Z<=0 || Clock[0].W<=0 ||
        double(Clock[0].X)+Clock[0].Y<Begin || double(Clock[0].X)+Clock[0].Y>=End)
    {AddError(TEXT("Invalid captured arrays/clock"));return false;}
    TArray<uint8> Output;TArray<TSharedPtr<FJsonValue>> Fields;bool Passed=true,Accepted=false;
    ENQUEUE_RENDER_COMMAND(CapturedOwnerTrial)([&](FRHICommandListImmediate& Cmd)
    {
        FRDGBuilder Graph(Cmd);auto Upload=[&](const auto& A,const TCHAR* Name){return CreateStructuredBuffer(Graph,Name,MakeArrayView(A));};
        auto S=Upload(State,TEXT("CapturedTrial.State")),B=Upload(Bed,TEXT("CapturedTrial.Bed")),P=Upload(Clock,TEXT("CapturedTrial.Clock"));
        auto ExtBed=Upload(EB,TEXT("CapturedTrial.ExteriorBed"));
        FRaftSimTemporalBoundaryEndpoint A{Upload(First,TEXT("CapturedTrial.First")),ExtBed,Upload(FaceA,TEXT("CapturedTrial.FaceA")),Begin};
        FRaftSimTemporalBoundaryEndpoint Z{Upload(Second,TEXT("CapturedTrial.Second")),ExtBed,Upload(FaceB,TEXT("CapturedTrial.FaceB")),End};
        if(Version==2)
        {
            TRefCountPtr<FRDGPooledBuffer> KeepState,KeepClock,KeepSummary,KeepDiagnostics,KeepLedger;
            auto Advance=[&](FRDGBuilder& G,FRDGBufferRef InState,FRDGBufferRef InClock,FRDGBufferRef Summary,FRDGBufferRef Flags,FRDGBufferRef Ledger,
                const FRaftSimTemporalBoundaryEndpoint& Start,const FRaftSimTemporalBoundaryEndpoint& Stop,FRDGBufferRef InBed)
            {
                auto Select=[&](FRDGBuilder& Inner,FRDGBufferRef,const FRaftSimTotalDepthTransportResult& F)
                {return RaftSimClassifyBreakingFrontGPU(Inner,F.Geometry,F.HydroRate,F.Pairs,FIntPoint(128,128),Dx,false,Error).Fraction;};
                FRaftSimTotalDepthBoundaryProvider Provider=[&](FRDGBuilder& Inner,FRDGBufferRef,FRDGBufferRef C,FRDGBufferRef Info)
                {return RaftSimSampleTemporalBoundaryGPU(Inner,Start,Stop,C,Info,FIntPoint(128,128),Error).Input;};
                return RaftSimAdvanceTotalDepthGPU(G,InState,InBed,InClock,Summary,Flags,FIntPoint(128,128),Dx,false,true,8,4096,Select,Error,Provider,Ledger,true,End);
            };
            auto R=Advance(Graph,S,P,Upload(RetainedSummary,TEXT("CapturedInterval.Summary")),Upload(RetainedDiagnostics,TEXT("CapturedInterval.Diagnostics")),
                Upload(RetainedLedger,TEXT("CapturedInterval.Ledger")),A,Z,B);
            if(!R.State){Passed=false;Graph.Execute();return;}
            auto Extract=[&](FRDGBuilder& G,const FRaftSimTotalDepthAdvanceResult& Value)
            {G.QueueBufferExtraction(Value.State,&KeepState);G.QueueBufferExtraction(Value.Progress,&KeepClock);G.QueueBufferExtraction(Value.Summary,&KeepSummary);
                G.QueueBufferExtraction(Value.Diagnostics,&KeepDiagnostics);G.QueueBufferExtraction(Value.BoundaryVolume,&KeepLedger);};
            Extract(Graph,R);Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle();
            // Preserve all five actual records across graph lifetimes. These
            // additional16 slots do not reset the original432/37 counters,
            // the4096 total-trial limit, clock, state or cumulative ledger.
            for(int32 Batch=1;Batch<2;++Batch)
            {
                FRDGBuilder Next(Cmd);auto Put=[&](const auto& Value,const TCHAR* Name){return CreateStructuredBuffer(Next,Name,MakeArrayView(Value));};
                auto EBNext=Put(EB,TEXT("CapturedInterval.ExteriorBed"));
                FRaftSimTemporalBoundaryEndpoint Start{Put(First,TEXT("CapturedInterval.First")),EBNext,Put(FaceA,TEXT("CapturedInterval.FaceA")),Begin};
                FRaftSimTemporalBoundaryEndpoint Stop{Put(Second,TEXT("CapturedInterval.Second")),EBNext,Put(FaceB,TEXT("CapturedInterval.FaceB")),End};
                R=Advance(Next,Next.RegisterExternalBuffer(KeepState),Next.RegisterExternalBuffer(KeepClock),Next.RegisterExternalBuffer(KeepSummary),
                    Next.RegisterExternalBuffer(KeepDiagnostics),Next.RegisterExternalBuffer(KeepLedger),Start,Stop,Put(Bed,TEXT("CapturedInterval.Bed")));
                if(!R.State){Passed=false;Next.Execute();return;}
                Extract(Next,R);Next.Execute();Cmd.SubmitAndBlockUntilGPUIdle();
            }
            FRDGBuilder Final(Cmd);TArray<TUniquePtr<FRHIGPUBufferReadback>> Reads;
            TArray<uint32> Sizes;TArray<FString> Names;TArray<int32> Components;
            auto Capture=[&](FRDGBufferRef Buffer,const TCHAR* Name,uint32 Count,int32 C)
            {Reads.Add(MakeUnique<FRHIGPUBufferReadback>(TEXT("CapturedInterval.Read")));Sizes.Add(Count*C*4);Names.Add(Name);Components.Add(C);AddEnqueueCopyPass(Final,Reads.Last().Get(),Buffer,Sizes.Last());};
            Capture(Final.RegisterExternalBuffer(KeepState),TEXT("output_state"),N,4);
            Capture(Final.RegisterExternalBuffer(KeepClock),TEXT("progress"),1,4);
            Capture(Final.RegisterExternalBuffer(KeepSummary),TEXT("summary"),1,4);
            Capture(Final.RegisterExternalBuffer(KeepDiagnostics),TEXT("diagnostics"),1,4);
            Capture(Final.RegisterExternalBuffer(KeepLedger),TEXT("boundary_volume"),NB,4);
            Final.Execute();Cmd.SubmitAndBlockUntilGPUIdle();
            for(int32 I=0;I<Reads.Num();++I)
            {
                const void* Data=Reads[I]->Lock(Sizes[I]);if(!Data){Passed=false;return;}
                auto Field=MakeShared<FJsonObject>();Field->SetStringField(TEXT("name"),Names[I]);Field->SetNumberField(TEXT("byte_offset"),Output.Num());
                Field->SetNumberField(TEXT("bytes"),Sizes[I]);Field->SetNumberField(TEXT("components"),Components[I]);
                Field->SetStringField(TEXT("dtype"),I==2 || I==3?TEXT("uint32"):TEXT("float32"));Fields.Add(MakeShared<FJsonValueObject>(Field));
                const int32 At=Output.AddUninitialized(Sizes[I]);FMemory::Memcpy(Output.GetData()+At,Data,Sizes[I]);
                if(I==2)Accepted=static_cast<const uint32*>(Data)[2]==1;
                Reads[I]->Unlock();
            }
            return;
        }
        FRaftSimTotalDepthTransportResult FV[2];FRDGBufferRef Fractions[2]{};FRaftSimBreakingFrontResult Breaking[2];int32 StageIndex=0;
        auto Select=[&](FRDGBuilder& G,FRDGBufferRef,const FRaftSimTotalDepthTransportResult& F)
        {const int32 K=StageIndex++;FV[K]=F;Breaking[K]=RaftSimClassifyBreakingFrontGPU(G,F.Geometry,F.HydroRate,F.Pairs,FIntPoint(128,128),Dx,false,Error);Fractions[K]=Breaking[K].Fraction;return Fractions[K];};
        FRDGBufferRef BoundaryTraces[2]{};int32 BoundaryIndex=0;
        FRaftSimTotalDepthBoundaryProvider Provider=[&](FRDGBuilder& G,FRDGBufferRef,FRDGBufferRef C,FRDGBufferRef Info)
        {auto Input=RaftSimSampleTemporalBoundaryGPU(G,A,Z,C,Info,FIntPoint(128,128),Error).Input;
            BoundaryTraces[BoundaryIndex++]=Input.FaceVelocity;return Input;};
        auto R=RaftSimTryTotalDepthStepGPU(Graph,S,B,P,FIntPoint(128,128),Dx,false,true,Select,Error,Provider,nullptr,End);
        if(!R.State || StageIndex!=2){Passed=false;Graph.Execute();return;}
        TArray<TUniquePtr<FRHIGPUBufferReadback>> Reads;TArray<uint32> Sizes;TArray<FString> Names;TArray<int32> Components;
        auto Capture=[&](FRDGBufferRef Buffer,const FString& Name,uint32 Count,int32 C)
        {Reads.Add(MakeUnique<FRHIGPUBufferReadback>(TEXT("CapturedTrial.Read")));Sizes.Add(Count*C*4);Names.Add(Name);Components.Add(C);AddEnqueueCopyPass(Graph,Reads.Last().Get(),Buffer,Sizes.Last());};
        Capture(S,TEXT("input_state"),N,4);Capture(R.EulerState,TEXT("euler_state"),N,4);Capture(R.CandidateState,TEXT("candidate_state"),N,4);
        Capture(R.State,TEXT("output_state"),N,4);Capture(R.Progress,TEXT("progress"),1,4);Capture(R.Info,TEXT("info"),1,4);Capture(R.Diagnostics,TEXT("diagnostics"),1,4);
        for(int32 K=0;K<2;++K)
        {
            Capture(FV[K].HydroRate,FString::Printf(TEXT("rate%d"),K),N,4);
            Capture(FV[K].Velocity,FString::Printf(TEXT("velocity%d"),K),N,2);
            Capture(FV[K].Geometry,FString::Printf(TEXT("geometry%d"),K),N,2);
            Capture(FV[K].Pairs,FString::Printf(TEXT("pairs%d"),K),N,1);
            Capture(FV[K].PhysicalBedSlope,FString::Printf(TEXT("bed_slope%d"),K),N,2);
            Capture(BoundaryTraces[K],FString::Printf(TEXT("boundary_trace%d"),K),NB,2);
            Capture(Breaking[K].SurfaceJumps,FString::Printf(TEXT("surface_jumps%d"),K),N,2);
            Capture(Breaking[K].Diagnostics,FString::Printf(TEXT("breaking_diagnostics%d"),K),1,4);
            Capture(FV[K].RawX,FString::Printf(TEXT("raw_x%d"),K),N,4);
            Capture(FV[K].RawY,FString::Printf(TEXT("raw_y%d"),K),N,4);
            Capture(FV[K].SlopeX,FString::Printf(TEXT("slope_x%d"),K),N,4);
            Capture(FV[K].SlopeY,FString::Printf(TEXT("slope_y%d"),K),N,4);
            Capture(FV[K].CFL,FString::Printf(TEXT("cfl%d"),K),1,4);
            Capture(FV[K].Diagnostics,FString::Printf(TEXT("transport_diagnostics%d"),K),1,4);
            Capture(Fractions[K],FString::Printf(TEXT("fraction%d"),K),N,1);
            Capture(K==0?R.FirstPressureForce:R.SecondPressureForce,FString::Printf(TEXT("force%d"),K),N,2);
            const auto& Pressure=R.PressureStages[K];
            Capture(Pressure.Diagnostics,FString::Printf(TEXT("pressure_diagnostics%d"),K),1,4);
            Capture(Pressure.SolverDiagnostics,FString::Printf(TEXT("solver_diagnostics%d"),K),1,4);
            Capture(Pressure.RightHandSide,FString::Printf(TEXT("pressure_rhs%d"),K),N,4);
            Capture(Pressure.Correction,FString::Printf(TEXT("pressure_correction%d"),K),N,4);
            Capture(Pressure.Pressure,FString::Printf(TEXT("pressure%d"),K),N,4);
            Capture(Pressure.Residual,FString::Printf(TEXT("pressure_residual%d"),K),N,4);
        }
        Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle();
        for(int32 I=0;I<Reads.Num();++I)
        {
            const void* Data=Reads[I]->Lock(Sizes[I]);if(!Data){Passed=false;return;}
            auto Field=MakeShared<FJsonObject>();Field->SetStringField(TEXT("name"),Names[I]);Field->SetNumberField(TEXT("byte_offset"),Output.Num());
            Field->SetNumberField(TEXT("bytes"),Sizes[I]);Field->SetNumberField(TEXT("components"),Components[I]);
            Field->SetStringField(TEXT("dtype"),Names[I].Contains(TEXT("diagnostics")) || Names[I].StartsWith(TEXT("pairs"))?TEXT("uint32"):TEXT("float32"));Fields.Add(MakeShared<FJsonValueObject>(Field));
            const int32 At=Output.AddUninitialized(Sizes[I]);FMemory::Memcpy(Output.GetData()+At,Data,Sizes[I]);
            if(I==0)Passed &= FMemory::Memcmp(Data,State.GetData(),Sizes[I])==0;
            if(I==6)Accepted=static_cast<const uint32*>(Data)[3]!=0;
            Reads[I]->Unlock();
        }
    });
    FlushRenderingCommands();auto Report=MakeShared<FJsonObject>();
    Report->SetStringField(TEXT("schema"),Version==2?TEXT("raftsim.captured_owner_interval_diagnostic.v1"):TEXT("raftsim.captured_owner_trial_diagnostic.v1"));Report->SetStringField(TEXT("input"),Input);
    Report->SetStringField(TEXT("binary"),Prefix+TEXT(".bin"));Report->SetBoolField(TEXT("capture_completed"),Passed);
    Report->SetBoolField(TEXT("transaction_accepted"),Accepted);Report->SetBoolField(TEXT("scene_accepted"),false);Report->SetArrayField(TEXT("fields"),Fields);
    FString Json;auto Writer=TJsonWriterFactory<>::Create(&Json);FJsonSerializer::Serialize(Report,Writer);
    Passed &= FFileHelper::SaveArrayToFile(Output,*(Prefix+TEXT(".bin"))) && FFileHelper::SaveStringToFile(Json,*(Prefix+TEXT(".json")));
    TestTrue(TEXT("Captured actual retained-state trial without replacing source or state"),Passed);
    AddInfo(FString::Printf(TEXT("Captured %d bytes; actual transaction accepted%d (capture is not accuracy qualification)"),Output.Num(),Accepted));
    if(!Error.IsEmpty())AddError(Error);return !HasAnyErrors();
}
#endif
