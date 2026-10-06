#include "Misc/AutomationTest.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "../RaftSimNonlinearEvolutionGPU.h"
#include "../RaftSimWindowSourceTransition.h"
#include <limits>

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_COMPLEX_AUTOMATION_TEST(FNonlinearEvolutionOwnerTest,"RaftSim.WaterDetail.NonlinearEvolutionOwnerGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
void FNonlinearEvolutionOwnerTest::GetTests(TArray<FString>& Names,TArray<FString>& Commands) const
{
    // Independent automation frames recycle transient D3D descriptors between
    // stress cases. Preserve every configuration/assertion; do not silence the
    // descriptor exhaustion warning from piling all cases in one frame.
    for(int32 Clock:{0,1,2})for(int32 Slots:{1,4,8,16})for(int32 RunAhead:{0,2})
    {
        Names.Add(FString::Printf(TEXT("Clock%d.Slots%d.RunAhead%d"),Clock,Slots,RunAhead));
        Commands.Add(FString::Printf(TEXT("%d_%d_%d"),Clock,Slots,RunAhead));
    }
    Names.Add(TEXT("WindowTransactions"));Commands.Add(TEXT("transactions"));
    Names.Add(TEXT("InitialMove"));Commands.Add(TEXT("initial_move"));
}
bool FNonlinearEvolutionOwnerTest::RunTest(const FString& Parameters)
{
    if(GUsingNullRHI){AddError(TEXT("Actual GPU required"));return false;}
    const bool Continuous=FParse::Param(FCommandLine::Get(),TEXT("RaftSimContinuousShorelineTest"));
    const bool Unscaled=FParse::Param(FCommandLine::Get(),TEXT("RaftSimUnscaledShorelineTest"));
    if(Continuous && Unscaled){AddError(TEXT("Choose one shoreline model"));return false;}
    AddInfo(FString::Printf(TEXT("immutable shoreline continuous%d unscaled%d"),Continuous,Unscaled));
    TArray<FVector4f> HUV,Geometry;TArray<float> FaceVelocity;
    HUV.Init(FVector4f(1,.25f,.125f,0),67*67);Geometry.Init(FVector4f(0,1,1,1),67*67);
    for(int32 I=0;I<512;++I)FaceVelocity.Add(I<256?.25f:.125f);
    FString Error;auto A=FRaftSimTotalDepthSource::Build(HUV,Geometry,FaceVelocity,FVector2f(123,-456),3.125,1,Error);
    if(!A){AddError(Error);return false;}
    auto Make=[&](uint64 Revision,double Seconds,float InteriorDepth)
    {
        auto R=MakeShared<FRaftSimTotalDepthSource,ESPMode::ThreadSafe>(*A);
        R->Revision=Revision;R->SampleSeconds=Seconds;
        for(auto& S:R->State)S=FVector4f(InteriorDepth,.25f*InteriorDepth,.125f*InteriorDepth,0);
        return R;
    };
    auto B=Make(2,3.140625,3),C=Make(3,3.15625,7);
    bool Passed=true;TArray<FString> Records;
    ENQUEUE_RENDER_COMMAND(NonlinearEvolutionOwnerVerification)([&](FRHICommandListImmediate& Cmd)
    {
        FRaftSimNonlinearEvolutionGPU InvalidModel(4,2,true,true);
        Passed &= InvalidModel.HasFailed() && !InvalidModel.Observe(A,Error) && !InvalidModel.State;
        Error.Reset();
        if(Parameters==TEXT("initial_move"))
        {
            for(int32 Model:{0,1,2})
            {
                auto Closing=Make(2,A->SampleSeconds,1),Opening=Make(3,A->SampleSeconds,1);
                Opening->OriginMeters.X+=8;Opening->CoarseSampleOriginMeters.X+=8;Opening->ClosingWindowSource=Closing;
                auto Later=MakeShared<FRaftSimTotalDepthSource,ESPMode::ThreadSafe>(*Opening);
                Later->Revision=4;Later->SampleSeconds=B->SampleSeconds;Later->ClosingWindowSource.Reset();
                FRaftSimNonlinearEvolutionGPU Owner(4,2,Model==1,Model==2);
                bool OK=Owner.Observe(A,Error) && Owner.Observe(Opening,Error) && Owner.Observe(Later,Error);
                for(int32 I=0;OK && I<16 && Owner.CompletedIntervals<1;++I)
                {
                    OK=Owner.Pump(Cmd,4,Error);Cmd.SubmitAndBlockUntilGPUIdle();
                    if(OK)OK=Owner.Poll(Error);
                }
                OK &= Owner.CompletedMoves==1 && Owner.CompletedIntervals==1 && Owner.AcceptedTrials==2 &&
                    Owner.CompletedSeconds==Later->SampleSeconds && Owner.PendingObservations()==1 && !Owner.HasPendingReadback();
                if(OK && Owner.State)
                {
                    FRDGBuilder Graph(Cmd);FRHIGPUBufferReadback Read(TEXT("InitialMove.State"));
                    AddEnqueueCopyPass(Graph,&Read,Graph.RegisterExternalBuffer(Owner.State),16384*16);
                    Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle();const void* Data=Read.Lock(16384*16);
                    OK &= Data && FMemory::Memcmp(Data,A->State.GetData(),16384*16)==0;
                    if(Data)Read.Unlock();
                }
                else OK=false;
                Records.Add(FString::Printf(TEXT("initial-move model%d passed%d moves%llu intervals%llu accepted%llu error%s"),
                    Model,OK,Owner.CompletedMoves,Owner.CompletedIntervals,Owner.AcceptedTrials,*Error));
                Passed &= OK;
            }
            return;
        }
        for(int32 ClockCase:{0,1,2})for(int32 Slots:{1,4,8,16})for(int32 RunAhead:{0,2})
        {
            if(Parameters!=FString::Printf(TEXT("%d_%d_%d"),ClockCase,Slots,RunAhead))continue;
            const double NativeSpan=(ClockCase==2?8:4)*double(1.f/60.f);
            TSharedPtr<const FRaftSimTotalDepthSource,ESPMode::ThreadSafe> First=A,Second=B,Third=C;
            if(ClockCase!=0)
            {First=Make(1,NativeSpan,1);Second=Make(2,2*NativeSpan,3);Third=Make(3,3*NativeSpan,7);}
            FRaftSimNonlinearEvolutionGPU Owner(3,RunAhead,Continuous,Unscaled);
            Passed &= Owner.UsesContinuousShoreline()==Continuous && Owner.UsesUnscaledShoreline()==Unscaled;
            Passed &= Owner.Observe(First,Error) && Owner.Observe(First,Error) && Owner.PendingObservations()==1;
            Passed &= Owner.Pump(Cmd,Slots,Error) && !Owner.State && !Owner.HasPendingReadback();
            Passed &= Owner.Observe(Second,Error) && Owner.Observe(Third,Error) && Owner.PendingObservations()==3;
            for(int32 I=0;I<32 && Owner.CompletedIntervals<2;++I)
            {
                if(!Owner.Pump(Cmd,Slots,Error)){Passed=false;break;}
                for(int32 Extra=0;Extra<3;++Extra)
                    if(!Owner.Pump(Cmd,Slots,Error)){Passed=false;break;}
                // Blocking is only in this automation test. Production Pump and
                // Poll never wait for the GPU or retire an unconfirmed bracket.
                Cmd.SubmitAndBlockUntilGPUIdle();
                if(!Owner.Poll(Error)){Passed=false;break;}
            }
            Passed &= Owner.CompletedIntervals==2 && Owner.CompletedSeconds==Third->SampleSeconds &&
                Owner.PendingObservations()==1 && !Owner.HasPendingReadback() && Owner.AcceptedTrials==(ClockCase==0?4u:ClockCase==1?16u:32u);
            if(!Owner.State){Passed=false;continue;}
            auto Retained=Owner.State;const uint64 Graphs=Owner.DispatchedGraphs;
            Passed &= Owner.Pump(Cmd,Slots,Error) && Owner.State==Retained && Owner.DispatchedGraphs==Graphs;
            FRDGBuilder Graph(Cmd);FRHIGPUBufferReadback Read(TEXT("OwnerTest.State"));
            AddEnqueueCopyPass(Graph,&Read,Graph.RegisterExternalBuffer(Owner.State),128*128*16);
            Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle();
            const void* Data=Read.Lock(128*128*16);
            const bool Exact=Data && FMemory::Memcmp(Data,A->State.GetData(),128*128*16)==0;
            Passed &= Exact;if(Data)Read.Unlock();
            Records.Add(FString::Printf(TEXT("nonlinear owner clockcase%d slots%d runahead%d completed%llu accepted%llu graphs%llu continued%llu retained-initial-state-exact%d end%.17g; later mean depths3/7 ignored"),
                ClockCase,Slots,RunAhead,Owner.CompletedIntervals,Owner.AcceptedTrials,Owner.DispatchedGraphs,Owner.ContinuedGraphsWithoutReadback,Exact,Owner.CompletedSeconds));
        }
        if(Parameters!=TEXT("transactions")){Error.Reset();return;}
        for(int32 Case=0;Case<8;++Case)
        {
            FRaftSimNonlinearEvolutionGPU Owner(2,2,Continuous,Unscaled);Passed &= Owner.Observe(A,Error);
            auto Bad=Make(2,3.140625,1);
            if(Case==0)Bad->Revision=1;
            if(Case==1)Bad->SampleSeconds=A->SampleSeconds;
            if(Case==2)Bad->SampleSeconds=3;
            if(Case==3){Bad->OriginMeters.X+=1;Bad->CoarseSampleOriginMeters.X+=1;}
            if(Case==4){Bad->Bed[0]=1;Bad->Reference[0].X=1;}
            if(Case==5)Bad->ExteriorBed[0]=1;
            if(Case==6)Bad->State[0].X=-1;
            if(Case==7)Bad->SampleSeconds=A->SampleSeconds+.1;
            Passed &= !Owner.Observe(Bad,Error) && !Error.IsEmpty() && Owner.PendingObservations()==1 && Owner.HasFailed();
            Passed &= !Owner.Pump(Cmd,1,Error) && !Owner.State;
        }
        FRaftSimNonlinearEvolutionGPU Full(2,2,Continuous,Unscaled);
        Passed &= Full.Observe(A,Error) && Full.Observe(B,Error);
        Passed &= !Full.Observe(C,Error) && Full.PendingObservations()==2 && Full.HasFailed();
        FRaftSimNonlinearEvolutionGPU BadCapacity(1,2,Continuous,Unscaled);
        Passed &= !BadCapacity.Observe(A,Error) && BadCapacity.PendingObservations()==0;
        for(int32 BadBudget:{0,RaftSimMaxTotalDepthTrialsPerGraph+1})
        {
            FRaftSimNonlinearEvolutionGPU Owner(2,2,Continuous,Unscaled);
            Passed &= Owner.Observe(A,Error) && Owner.Observe(B,Error);
            Passed &= !Owner.Pump(Cmd,BadBudget,Error) && Owner.HasFailed() && !Owner.State && Owner.PendingObservations()==2;
        }
        for(const FIntPoint Offset:{FIntPoint(16,0),FIntPoint(-16,3),FIntPoint(0,17),FIntPoint(5,-17)})
        {
            auto Opening=Make(3,B->SampleSeconds,3);
            Opening->OriginMeters=A->OriginMeters+.5f*FVector2f(Offset);
            FRaftSimDetailSampleGrid Grid;Passed &= Grid.Register(Opening->OriginMeters);
            Opening->CoarseSampleOriginMeters=Grid.CoarseOriginMeters;Opening->ClosingWindowSource=B;
            FRaftSimNonlinearEvolutionGPU Owner(3,2,Continuous,Unscaled);
            Passed &= Owner.Observe(A,Error) && Owner.Observe(Opening,Error) && Owner.PendingObservations()==3;
            for(int32 I=0;I<12 && Owner.CompletedMoves==0;++I)
            {
                if(!Owner.Pump(Cmd,4,Error)){Passed=false;break;}
                Cmd.SubmitAndBlockUntilGPUIdle();if(!Owner.Poll(Error)){Passed=false;break;}
            }
            Passed &= Owner.CompletedIntervals==1 && Owner.CompletedMoves==1 && Owner.CompletedSeconds==B->SampleSeconds &&
                Owner.PendingObservations()==1 && !Owner.HasPendingReadback();
            if(!Owner.State || !Owner.WindowExchange){Passed=false;continue;}
            FRDGBuilder Graph(Cmd);FRHIGPUBufferReadback SR(TEXT("MoveTest.State")),ER(TEXT("MoveTest.Exchange"));
            AddEnqueueCopyPass(Graph,&SR,Graph.RegisterExternalBuffer(Owner.State),16384*16);
            AddEnqueueCopyPass(Graph,&ER,Graph.RegisterExternalBuffer(Owner.WindowExchange),16384*16);
            Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle();
            const auto* S=static_cast<const FVector4f*>(SR.Lock(16384*16));
            const auto* E=static_cast<const FVector4f*>(ER.Lock(16384*16));
            bool Exact=S && E;FVector4d Delta(0,0,0,0),Ledger(0,0,0,0);
            if(S && E)for(int32 Y=0;Y<128;++Y)for(int32 X=0;X<128;++X)
            {
                const int32 I=Y*128+X;const auto P=FIntPoint(X,Y)+Offset,Q=FIntPoint(X,Y)-Offset;
                const bool Retained=P.X>=0 && P.Y>=0 && P.X<128 && P.Y<128;
                const bool Departed=Q.X<0 || Q.Y<0 || Q.X>=128 || Q.Y>=128;
                const FVector4f Expected=Retained?A->State[P.Y*128+P.X]:Opening->State[I];
                const FVector4f Exchange=(Retained?FVector4f(0,0,0,0):Opening->State[I])-(Departed?A->State[I]:FVector4f(0,0,0,0));
                Exact &= S[I]==Expected && E[I]==Exchange;
                for(int32 K=0;K<4;++K){Delta[K]+=double(S[I][K])-A->State[I][K];Ledger[K]+=E[I][K];}
            }
            if(S)SR.Unlock();if(E)ER.Unlock();
            Passed &= Exact && Delta==Ledger;
            Records.Add(FString::Printf(TEXT("nonlinear move offset%d/%d exact%d completed%llu endpoint%.17g inventory_h%.9g; later mean only enters exposed cells"),
                Offset.X,Offset.Y,Exact,Owner.CompletedMoves,Owner.CompletedSeconds,Ledger.X*.25));
            for(int32 BadCase=0;BadCase<4;++BadCase)
            {
                auto Bad=MakeShared<FRaftSimTotalDepthSource,ESPMode::ThreadSafe>(*Opening);
                if(BadCase==0)Bad->ClosingWindowSource.Reset();
                if(BadCase==1)Bad->SampleSeconds+=.015625;
                if(BadCase==2){const int32 X=FMath::Max(0,-Offset.X),Y=FMath::Max(0,-Offset.Y);Bad->State[Y*128+X].X+=1;}
                if(BadCase==3){Bad->OriginMeters.X+=.25f;}
                FRaftSimNonlinearEvolutionGPU Rejected(3,2,Continuous,Unscaled);Passed &= Rejected.Observe(A,Error);
                Passed &= !Rejected.Observe(Bad,Error) && Rejected.PendingObservations()==1 && !Rejected.State;
            }
            FRaftSimNonlinearEvolutionGPU FullMove(2,2,Continuous,Unscaled);Passed &= FullMove.Observe(A,Error);
            Passed &= !FullMove.Observe(Opening,Error) && FullMove.PendingObservations()==1;
        }
        {
            auto Closing=Make(2,B->SampleSeconds,1);
            auto Opening=Make(3,B->SampleSeconds,1);
            Opening->OriginMeters.X+=8;Opening->CoarseSampleOriginMeters.X+=8;Opening->ClosingWindowSource=Closing;
            auto Later=MakeShared<FRaftSimTotalDepthSource,ESPMode::ThreadSafe>(*Opening);
            Later->Revision=4;Later->SampleSeconds=C->SampleSeconds;Later->ClosingWindowSource.Reset();
            auto Returning=Make(5,C->SampleSeconds,1);Returning->ClosingWindowSource=Later;
            FRaftSimNonlinearEvolutionGPU Owner(5,2,Continuous,Unscaled);
            Passed &= Owner.Observe(A,Error) && Owner.Observe(Opening,Error) && Owner.Observe(Returning,Error);
            for(int32 I=0;I<16 && Owner.CompletedMoves<2;++I)
            {
                if(!Owner.Pump(Cmd,4,Error)){Passed=false;break;}
                Cmd.SubmitAndBlockUntilGPUIdle();if(!Owner.Poll(Error)){Passed=false;break;}
            }
            Passed &= Owner.CompletedIntervals==2 && Owner.CompletedMoves==2 && Owner.CompletedSeconds==C->SampleSeconds &&
                Owner.PendingObservations()==1 && !Owner.HasPendingReadback() && Owner.StateOriginMeters==A->OriginMeters;
            if(!Owner.State || !Owner.WindowExchange)Passed=false;
            else
            {
                FRDGBuilder Graph(Cmd);FRHIGPUBufferReadback SR(TEXT("ReturnMove.State")),ER(TEXT("ReturnMove.Exchange"));
                AddEnqueueCopyPass(Graph,&SR,Graph.RegisterExternalBuffer(Owner.State),16384*16);
                AddEnqueueCopyPass(Graph,&ER,Graph.RegisterExternalBuffer(Owner.WindowExchange),16384*16);
                Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle();
                const void* S=SR.Lock(16384*16);const auto* E=static_cast<const FVector4f*>(ER.Lock(16384*16));
                bool Exact=S && E && FMemory::Memcmp(S,A->State.GetData(),16384*16)==0;
                if(E)for(int32 I=0;I<16384;++I)Exact &= E[I]==FVector4f(0,0,0,0);
                if(S)SR.Unlock();if(E)ER.Unlock();Passed &= Exact;
                Records.Add(FString::Printf(TEXT("two nonlinear moves with two evolved intervals: state/inventory exact%d endpoint%.17g; temporal boundary ownership resumes on new grid"),Exact,Owner.CompletedSeconds));
            }
        }
        Error.Reset();
    });
    FlushRenderingCommands();for(const auto& R:Records)AddInfo(R);
    TestTrue(TEXT("Immutable observations survive async GPU consumption without interior resets, dropped intervals or extrapolation"),Passed);
    if(!Error.IsEmpty())AddError(Error);return !HasAnyErrors();
}
#endif
