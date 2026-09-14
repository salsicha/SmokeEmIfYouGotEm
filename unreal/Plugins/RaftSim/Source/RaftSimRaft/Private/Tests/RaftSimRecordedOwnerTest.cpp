#include "Misc/AutomationTest.h"

#if WITH_DEV_AUTOMATION_TESTS && WITH_UNREAL_DEVELOPER_TOOLS
#include "../RaftSimNonlinearEvolutionAudit.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRecordedOwnerTest,"RaftSim.Diagnostics.ReplayedNonlinearOwner",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRecordedOwnerTest::RunTest(const FString&)
{
    FString Input,Output,Json,Error;
    if(GUsingNullRHI || !FParse::Value(FCommandLine::Get(),TEXT("RaftSimRecordedOwnerInput="),Input) ||
        !FParse::Value(FCommandLine::Get(),TEXT("RaftSimRecordedOwnerOutput="),Output) ||
        FPaths::FileExists(Output) || !FFileHelper::LoadFileToString(Json,*Input))
    {AddError(TEXT("Actual GPU, original source history and fresh output required"));return false;}
    TSharedPtr<FJsonObject> Root;auto Reader=TJsonReaderFactory<>::Create(Json);
    if(!FJsonSerializer::Deserialize(Reader,Root) || !Root ||
        Root->GetStringField(TEXT("schema"))!=TEXT("raftsim.live_nonlinear_owner_audit.v1"))
    {AddError(TEXT("Invalid source history"));return false;}
    const bool Continuous=FParse::Param(FCommandLine::Get(),TEXT("RaftSimContinuousShorelineTest"));
    const bool Unscaled=FParse::Param(FCommandLine::Get(),TEXT("RaftSimUnscaledShorelineTest"));
    if(Continuous && Unscaled){AddError(TEXT("Choose one shoreline model"));return false;}
    const auto& OriginalClock=Root->GetArrayField(TEXT("progress"));
    if(OriginalClock.Num()!=4 || OriginalClock[2]->AsNumber()!=0 || !Root->GetStringField(TEXT("failure")).IsEmpty())
    {AddError(TEXT("Replay requires a completed original history endpoint"));return false;}
    const double Target=OriginalClock[0]->AsNumber()+OriginalClock[1]->AsNumber();
    const uint64 Intervals=Root->GetIntegerField(TEXT("completed_intervals")),Moves=Root->GetIntegerField(TEXT("completed_moves"));
    const auto& Raw=Root->GetArrayField(TEXT("observations"));
    if(!FMath::IsFinite(Target) || Raw.Num()<2 || Raw.Num()>256 || Intervals<1 || Intervals>128 || Moves>32)
    {AddError(TEXT("Unbounded source history"));return false;}
    bool Passed=true;
    TArray<TSharedPtr<const FRaftSimTotalDepthSource,ESPMode::ThreadSafe>> Sources;
    auto Values=[&](const TSharedPtr<FJsonObject>& O,const TCHAR* Key,auto& A,int32 Count,int32 Components)
    {
        const auto& V=O->GetArrayField(Key);
        if(V.Num()!=Count*Components){Passed=false;return;}
        A.SetNumUninitialized(Count);float* P=reinterpret_cast<float*>(A.GetData());
        for(int32 I=0;I<V.Num();++I)
        {
            const double D=V[I]->AsNumber();P[I]=float(D);
            // Source packets were captured as FP32. Never silently requantize.
            Passed &= FMath::IsFinite(D) && double(P[I])==D;
        }
    };
    for(const auto& V:Raw)
    {
        const auto O=V->AsObject();const double Time=O->GetNumberField(TEXT("native_seconds"));
        if(Time>Target)break;
        auto S=MakeShared<FRaftSimTotalDepthSource,ESPMode::ThreadSafe>();
        S->Size=FIntPoint(O->GetIntegerField(TEXT("nx")),O->GetIntegerField(TEXT("ny")));
        S->CellMeters=float(O->GetNumberField(TEXT("cell_meters")));S->SampleSeconds=Time;
        S->Revision=O->GetIntegerField(TEXT("revision"));
        S->OriginMeters=FVector2f(float(O->GetNumberField(TEXT("origin_x"))),float(O->GetNumberField(TEXT("origin_y"))));
        FRaftSimDetailSampleGrid Grid;Passed &= Grid.Register(S->OriginMeters);S->CoarseSampleOriginMeters=Grid.CoarseOriginMeters;
        Values(O,TEXT("state"),S->State,16384,4);Values(O,TEXT("bed"),S->Bed,16384,1);
        Values(O,TEXT("reference"),S->Reference,16384,2);Values(O,TEXT("exterior_state"),S->ExteriorState,512,4);
        Values(O,TEXT("exterior_bed"),S->ExteriorBed,512,1);Values(O,TEXT("face_normal_velocity"),S->FaceNormalVelocity,512,1);
        if(Sources.Num() && Sources.Last()->OriginMeters!=S->OriginMeters)S->ClosingWindowSource=Sources.Last();
        Passed &= S->Validate(Error);Sources.Add(S);
    }
    if(!Passed || Sources.Num()<2 || Sources.Last()->SampleSeconds!=Target)
    {AddError(TEXT("Original exact source packets or endpoint invalid: ")+Error);return false;}
    TArray<FVector4f> State,Ledger,Clock,Exchange;TArray<uint32> Summary,Diagnostics;
    ENQUEUE_RENDER_COMMAND(RecordedPersistentOwner)([&](FRHICommandListImmediate& Cmd)
    {
        FRaftSimNonlinearEvolutionGPU Owner(4,2,Continuous,Unscaled);
        // Feed every captured packet unchanged. Blocking/draining is diagnostic
        // only: validates the real persistent owner, NOT sustained queue capacity.
        for(int32 Index=0;Index<Sources.Num();++Index)
        {
            const auto& S=Sources[Index];
            // The capture expands the original move packet into closing/opening
            // rows. Observe must receive their ORIGINAL atomic ownership bundle;
            // it enqueues the closing row itself before the entering row. Feeding
            // that closing row separately would incorrectly reuse its revision.
            if(Index+1<Sources.Num() && Sources[Index+1]->ClosingWindowSource==S)continue;
            if(!Owner.Observe(S,Error)){Passed=false;break;}
            for(int32 Graphs=0;(Owner.PendingObservations()>1 || Owner.HasPendingReadback()) && Graphs<4096;++Graphs)
            {
                if(!Owner.Pump(Cmd,16,Error)){Passed=false;break;}
                Cmd.SubmitAndBlockUntilGPUIdle();
                if(!Owner.Poll(Error)){Passed=false;break;}
            }
            if(!Passed || Owner.PendingObservations()>1 || Owner.HasPendingReadback())
            {Passed=false;break;}
        }
        Passed &= Owner.CompletedIntervals==Intervals && Owner.CompletedMoves==Moves && Owner.CompletedSeconds==Target &&
            !Owner.HasFailed() && !Owner.HasPendingReadback();
        const auto& Origin=Root->GetArrayField(TEXT("state_origin_meters"));
        Passed &= Origin.Num()==2 && Origin[0]->AsNumber()==Owner.StateOriginMeters.X && Origin[1]->AsNumber()==Owner.StateOriginMeters.Y;
        Root->SetNumberField(TEXT("completed_intervals"),Owner.CompletedIntervals);Root->SetNumberField(TEXT("completed_moves"),Owner.CompletedMoves);
        Root->SetNumberField(TEXT("completed_native_seconds"),Owner.CompletedSeconds);
        Root->SetNumberField(TEXT("accepted_trials_in_completed_intervals"),Owner.AcceptedTrials);
        Root->SetNumberField(TEXT("graphs"),Owner.DispatchedGraphs);
        Root->SetNumberField(TEXT("continued_graphs_without_readback"),Owner.ContinuedGraphsWithoutReadback);
        Root->SetNumberField(TEXT("retained_observations"),Owner.PendingObservations());
        Root->SetBoolField(TEXT("owner_readback_pending"),Owner.HasPendingReadback());
        Root->SetArrayField(TEXT("state_origin_meters"),FRaftSimNonlinearEvolutionAudit::Scalars({Owner.StateOriginMeters.X,Owner.StateOriginMeters.Y}));
        if(!Owner.State || !Owner.Progress || !Owner.BoundaryVolume || !Owner.Summary || !Owner.Diagnostics){Passed=false;return;}
        FRDGBuilder Graph(Cmd);
        FRHIGPUBufferReadback SR(TEXT("ReplayOwner.State")),LR(TEXT("ReplayOwner.Ledger")),PR(TEXT("ReplayOwner.Clock")),
            CR(TEXT("ReplayOwner.Summary")),DR(TEXT("ReplayOwner.Diagnostics")),ER(TEXT("ReplayOwner.Exchange"));
        AddEnqueueCopyPass(Graph,&SR,Graph.RegisterExternalBuffer(Owner.State),16384*16);
        AddEnqueueCopyPass(Graph,&LR,Graph.RegisterExternalBuffer(Owner.BoundaryVolume),512*16);
        AddEnqueueCopyPass(Graph,&PR,Graph.RegisterExternalBuffer(Owner.Progress),16);
        AddEnqueueCopyPass(Graph,&CR,Graph.RegisterExternalBuffer(Owner.Summary),16);
        AddEnqueueCopyPass(Graph,&DR,Graph.RegisterExternalBuffer(Owner.Diagnostics),16);
        if(Owner.WindowExchange)AddEnqueueCopyPass(Graph,&ER,Graph.RegisterExternalBuffer(Owner.WindowExchange),16384*16);
        Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle();
        auto Read=[&](FRHIGPUBufferReadback& R,auto& A,int32 Count)
        {
            const uint32 Bytes=Count*sizeof(A[0]);const void* P=R.Lock(Bytes);
            if(!P){Passed=false;return;}A.SetNumUninitialized(Count);FMemory::Memcpy(A.GetData(),P,Bytes);R.Unlock();
        };
        Read(SR,State,16384);Read(LR,Ledger,512);Read(PR,Clock,1);Read(CR,Summary,4);Read(DR,Diagnostics,4);
        if(Owner.WindowExchange)Read(ER,Exchange,16384);else Exchange.Init(FVector4f(0,0,0,0),16384);
    });
    FlushRenderingCommands();
    // Binary reruns must reproduce their original final state. The candidate's
    // different numerical trajectory instead requires an independent CPU audit.
    TArray<FVector4f> Original;Values(Root,TEXT("state"),Original,16384,4);
    const bool Exact=Original.Num()==State.Num() && FMemory::Memcmp(Original.GetData(),State.GetData(),State.Num()*16)==0;
    if(!Continuous && !Unscaled)Passed &= Exact;
    Root->SetBoolField(TEXT("final_state_exact_to_original"),Exact);
    Root->SetStringField(TEXT("source_history"),Input);Root->SetStringField(TEXT("shoreline_limiter"),Unscaled?TEXT("unscaled"):Continuous?TEXT("continuous"):TEXT("binary"));
    Root->SetStringField(TEXT("scope"),TEXT("Original immutable captured packets replayed through the persistent GPU owner, drained between observations. No interior resets. Not live capacity, independent accuracy, visuals or FPS acceptance."));
    Root->SetStringField(TEXT("failure"),Passed?TEXT(""):Error.IsEmpty()?TEXT("Recorded owner completion/identity check failed"):Error);
    Root->SetBoolField(TEXT("completed_requested_intervals"),Passed);Root->SetNumberField(TEXT("trials_per_graph"),16);
    Root->SetArrayField(TEXT("state"),FRaftSimNonlinearEvolutionAudit::Vectors(State));Root->SetArrayField(TEXT("progress"),FRaftSimNonlinearEvolutionAudit::Vectors(Clock));
    Root->SetArrayField(TEXT("cumulative_boundary_volume"),FRaftSimNonlinearEvolutionAudit::Vectors(Ledger));
    Root->SetArrayField(TEXT("window_exchange"),FRaftSimNonlinearEvolutionAudit::Vectors(Exchange));
    auto UInts=[](const TArray<uint32>& A){TArray<TSharedPtr<FJsonValue>> V;for(uint32 X:A)V.Add(MakeShared<FJsonValueNumber>(X));return V;};
    Root->SetArrayField(TEXT("summary"),UInts(Summary));Root->SetArrayField(TEXT("diagnostics"),UInts(Diagnostics));
    auto Writer=TJsonWriterFactory<>::Create(&Json);Json.Reset();
    Passed &= FJsonSerializer::Serialize(Root,Writer) && !FPaths::FileExists(Output) && FFileHelper::SaveStringToFile(Json,*Output);
    AddInfo(FString::Printf(TEXT("recorded persistent owner continuous%d unscaled%d original-final-exact%d output%s"),Continuous,Unscaled,Exact,*Output));
    TestTrue(TEXT("Persistent owner completes the original history and preserves immutable source observations"),Passed);
    if(!Error.IsEmpty())AddError(Error);return !HasAnyErrors();
}
#endif
