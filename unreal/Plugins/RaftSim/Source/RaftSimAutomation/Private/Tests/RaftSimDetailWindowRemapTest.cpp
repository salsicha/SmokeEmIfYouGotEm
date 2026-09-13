#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "RaftSimDetailWaterGPU.h"
#include "RaftSimWaterTextureHistory.h"
#include "RHIGPUReadback.h"
#include "RHICommandList.h"
#include "RenderingThread.h"
#include "HAL/PlatformProcess.h"

#if WITH_AUTOMATION_TESTS
namespace
{
template<class T> bool ReadBuffer(FRHIGPUBufferReadback& Readback,int32 Count,TArray<T>& Values)
{
    const double Deadline=FPlatformTime::Seconds()+10;
    while (!Readback.IsReady() && FPlatformTime::Seconds()<Deadline)FPlatformProcess::Sleep(.01f);
    if (!Readback.IsReady())return false;
    ENQUEUE_RENDER_COMMAND(RaftSimRemapRead)([&](FRHICommandListImmediate&)
    {
        Values.SetNumUninitialized(Count);
        const void* Source=Readback.Lock(Count*sizeof(T));
        FMemory::Memcpy(Values.GetData(),Source,Count*sizeof(T));Readback.Unlock();
    });
    FlushRenderingCommands();return true;
}
bool Exact(const FVector4f& A,const FVector4f& B)
{ return A.X==B.X && A.Y==B.Y && A.Z==B.Z && A.W==B.W; }
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimDetailWindowRemapTest,
    "RaftSim.WaterDetail.ExactMovingWindowGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)
bool FRaftSimDetailWindowRemapTest::RunTest(const FString&)
{
    if (GUsingNullRHI || GMaxRHIFeatureLevel<ERHIFeatureLevel::SM5)
    { AddError(TEXT("A real SM5+ GPU is required for window transfer evidence"));return false; }
    constexpr int32 Nx=17,Ny=13,Count=Nx*Ny; // Non-square, partial dispatch groups.
    int32 CheckedCells=0,RetainedNonzero=0,Exposed=0,Dried=0;
    for (bool Activity:{false,true})for (bool SecondOrder:{false,true})
    {
        FRaftSimDetailWaterGrid Grid;Grid.Size=FIntPoint(Nx,Ny);Grid.CellMeters=.5f;
        Grid.OriginMeters=FVector2f(-5439.f,3606.f);
        Grid.bActivityMemory=Activity;Grid.bSecondOrder=SecondOrder;
        Grid.FoamDecayPerSecond=0;Grid.FoamSourcePerSecond=0;
        Grid.ActivityDecayPerSecond=0;Grid.ActivitySourcePerSecond=0;
        TArray<FVector4f> Flow,Initial,Before;TArray<float> InitialActivity,BeforeActivity;
        for (int32 I=0;I<Count;++I)
        {
            Flow.Add(FVector4f(1.f+(I%7)*.03f,.1f,-.2f,0));
            Initial.Add(FVector4f(.001f*(I%11),.002f*(I%13),-.003f*(I%17),1.f+I*.03f));
            InitialActivity.Add((I%23)/23.f);
        }
        auto Simulation=MakeShared<FRaftSimDetailWaterGPU,ESPMode::ThreadSafe>();
        ON_SCOPE_EXIT
        {
            ENQUEUE_RENDER_COMMAND(RaftSimRemapRelease)([Simulation](FRHICommandListImmediate&) { Simulation->Reset(); });
            FlushRenderingCommands();
        };
        auto Readback=MakeShared<FRHIGPUBufferReadback,ESPMode::ThreadSafe>(TEXT("RaftSimRemapBefore"));
        auto ActivityRead=MakeShared<FRHIGPUBufferReadback,ESPMode::ThreadSafe>(TEXT("RaftSimRemapActivityBefore"));
        bool Started=false,RefusedUninitialized=false;FString Error;
        ENQUEUE_RENDER_COMMAND(RaftSimRemapStart)([&](FRHICommandListImmediate& Cmd)
        {
            RefusedUninitialized=!Simulation->RemapWindow(Cmd,Grid,Flow,Error);
            Started=Simulation->Advance(Cmd,Grid,Flow,1,&Initial,&Readback.Get(),Error,
                Activity ? &InitialActivity : nullptr,Activity ? &ActivityRead.Get() : nullptr);
        });
        FlushRenderingCommands();
        TestTrue(TEXT("uninitialized remap is rejected"),RefusedUninitialized);
        if (!TestTrue(TEXT("seeded state advances on GPU"),Started)) { AddError(Error);return false; }
        if (!ReadBuffer(Readback.Get(),Count,Before) || (Activity && !ReadBuffer(ActivityRead.Get(),Count,BeforeActivity)))
        { AddError(TEXT("Initial GPU readback timeout"));return false; }
        const double InitialClock=Grid.StepSeconds;
        for (FIntPoint Shift:{FIntPoint(3,-2),FIntPoint(-4,1),FIntPoint(0,0),
                              FIntPoint(16,0),FIntPoint(-2,-12),FIntPoint(0,4)})
        {
            Grid.OriginMeters+=FVector2f(Shift.X*Grid.CellMeters,Shift.Y*Grid.CellMeters);
            TArray<FVector4f> Expected,After;TArray<float> ExpectedActivity,AfterActivity;
            for (int32 Y=0;Y<Ny;++Y)for (int32 X=0;X<Nx;++X)
            {
                const int32 I=Y*Nx+X,OldX=X+Shift.X,OldY=Y+Shift.Y;
                const bool Inside=OldX>=0 && OldX<Nx && OldY>=0 && OldY<Ny;
                // Include freshly dried, threshold-dry and newly wet cells.
                Flow[I]=FVector4f(I%29==0 ? .01f : I%19==0 ? 0.f : 1.f,.1f,-.2f,0);
                const bool Keep=Inside && Flow[I].X>.01f;
                Expected.Add(Keep ? Before[OldY*Nx+OldX] : FVector4f(0,0,0,0));
                if (Activity)ExpectedActivity.Add(Keep ? BeforeActivity[OldY*Nx+OldX] : 0.f);
                ++CheckedCells;Exposed+=!Inside;Dried+=Inside && !Keep;
                RetainedNonzero+=Keep && Expected.Last().W>1;
            }
            auto MovedRead=MakeShared<FRHIGPUBufferReadback,ESPMode::ThreadSafe>(TEXT("RaftSimRemapMoved"));
            auto MovedActivity=MakeShared<FRHIGPUBufferReadback,ESPMode::ThreadSafe>(TEXT("RaftSimRemapMovedActivity"));
            bool Moved=false,SameClock=false;
            ENQUEUE_RENDER_COMMAND(RaftSimRemapMove)([&](FRHICommandListImmediate& Cmd)
            {
                Moved=Simulation->RemapWindow(Cmd,Grid,Flow,Error,&MovedRead.Get(),Activity ? &MovedActivity.Get() : nullptr);
                SameClock=Simulation->GetStepCount()==1 && Simulation->GetSimulationSeconds()==InitialClock;
            });
            FlushRenderingCommands();
            if (!TestTrue(TEXT("explicit signed cell shift dispatches"),Moved)) { AddError(Error);return false; }
            TestTrue(TEXT("handoff never advances or resets simulation/forcing time"),SameClock);
            if (!ReadBuffer(MovedRead.Get(),Count,After) || (Activity && !ReadBuffer(MovedActivity.Get(),Count,AfterActivity)))
            { AddError(TEXT("Moved GPU readback timeout"));return false; }
            bool Same=true;
            for (int32 I=0;I<Count;++I)Same &= Exact(Expected[I],After[I]) &&
                (!Activity || ExpectedActivity[I]==AfterActivity[I]);
            TestTrue(TEXT("wet overlap is bit-exact; entering/dry state and activity are zero without wrapping"),Same);
            Before=MoveTemp(After);BeforeActivity=MoveTemp(AfterActivity);
        }
        bool InvalidRejected=true,Continued=false,ClockAdvanced=false;
        auto FinalRead=MakeShared<FRHIGPUBufferReadback,ESPMode::ThreadSafe>(TEXT("RaftSimRemapAfterRejection"));
        ENQUEUE_RENDER_COMMAND(RaftSimRemapInvalid)([&](FRHICommandListImmediate& Cmd)
        {
            auto Bad=Grid;Bad.OriginMeters.X+=.25f;
            InvalidRejected &= !Simulation->RemapWindow(Cmd,Bad,Flow,Error);
            Bad=Grid;Bad.OriginMeters.X+=Nx*Grid.CellMeters;
            InvalidRejected &= !Simulation->RemapWindow(Cmd,Bad,Flow,Error);
            Bad=Grid;Bad.OriginMeters.Y-=Ny*Grid.CellMeters;
            InvalidRejected &= !Simulation->RemapWindow(Cmd,Bad,Flow,Error);
            Bad=Grid;Bad.CellMeters*=2;
            InvalidRejected &= !Simulation->RemapWindow(Cmd,Bad,Flow,Error);
            Bad=Grid;Bad.Size.X++;
            InvalidRejected &= !Simulation->RemapWindow(Cmd,Bad,Flow,Error);
            Bad=Grid;Bad.bPeriodic=true;
            InvalidRejected &= !Simulation->RemapWindow(Cmd,Bad,Flow,Error);
            Bad=Grid;Bad.bSecondOrder=!SecondOrder;
            InvalidRejected &= !Simulation->RemapWindow(Cmd,Bad,Flow,Error);
            Bad=Grid;Bad.bActivityMemory=!Activity;
            InvalidRejected &= !Simulation->RemapWindow(Cmd,Bad,Flow,Error);
            Bad=Grid;Bad.StepSeconds=1;
            InvalidRejected &= !Simulation->RemapWindow(Cmd,Bad,Flow,Error);
            auto BadFlow=Flow;BadFlow[0].W=2;
            InvalidRejected &= !Simulation->RemapWindow(Cmd,Grid,BadFlow,Error);
            // Failed requests must leave the previous origin/state usable.
            InvalidRejected &= Simulation->RemapWindow(Cmd,Grid,Flow,Error,&FinalRead.Get());
            Continued=Simulation->Advance(Cmd,Grid,Flow,1,nullptr,nullptr,Error);
            ClockAdvanced=Simulation->GetStepCount()==2 && Simulation->GetSimulationSeconds()==2*InitialClock;
        });
        FlushRenderingCommands();
        TestTrue(TEXT("fractional/nonoverlap/resize/mode/CFL/input changes rejected before mutation"),InvalidRejected);
        TArray<FVector4f> Final;
        if (!ReadBuffer(FinalRead.Get(),Count,Final)) { AddError(TEXT("Final GPU readback timeout"));return false; }
        bool Same=true;for (int32 I=0;I<Count;++I)Same &= Exact(Before[I],Final[I]);
        TestTrue(TEXT("all rejected requests preserve retained state exactly"),Same);
        TestTrue(TEXT("normal evolution resumes at moved origin without reseed or lost clock"),Continued && ClockAdvanced);
    }
    TestTrue(TEXT("fixture exercises compressed foam, exposed cells and drying"),RetainedNonzero>0 && Exposed>0 && Dried>0);
    AddInfo(FString::Printf(TEXT("GPU remap checked %d cells; %d retained density>1, %d newly exposed, %d drying; four transport/activity mode combinations"),
        CheckedCells,RetainedNonzero,Exposed,Dried));
    return !HasAnyErrors();
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimRegisteredDetailHistoryTest,
    "RaftSim.WaterDetail.RegisteredMovingHistoryGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)
bool FRaftSimRegisteredDetailHistoryTest::RunTest(const FString&)
{
    if (GUsingNullRHI || GMaxRHIFeatureLevel<ERHIFeatureLevel::SM5)
    { AddError(TEXT("A real SM5+ GPU is required"));return false; }
    constexpr int32 Nx=17,Ny=13,Count=Nx*Ny;
    FRaftSimDetailWaterGrid Grid;Grid.Size=FIntPoint(Nx,Ny);Grid.CellMeters=.5f;
    Grid.OriginMeters=FVector2f(-5439.f,3606.f);Grid.FoamDecayPerSecond=0;Grid.FoamSourcePerSecond=0;
    TArray<FVector4f> Flow,Initial,Seeded;
    for (int32 I=0;I<Count;++I)
    { Flow.Add(FVector4f(1,0,0,0));Initial.Add(FVector4f(.003f*(I%9),0,0,.05f*(I%37))); }
    const FVector2f Origin=Grid.OriginMeters;
    const TArray<FVector4f> Queries={
        FVector4f(Origin.X+3.125f,Origin.Y+2.375f,0,0),
        FVector4f(Origin.X+4.5f,Origin.Y+3.25f,0,0),
        FVector4f(Origin.X+8.f,Origin.Y+6.f,0,0), // Last DATA centre, never metadata.
        FVector4f(Origin.X+9.f,Origin.Y+4.f,0,0), // Initially outside; later exposed.
        FVector4f(Origin.X-1.f,Origin.Y+1.f,0,0),
        FVector4f(Origin.X+3.f,Origin.Y-2.f,0,0),
        FVector4f(Origin.X+3.75f,Origin.Y+5.75f,0,0)};
    auto Simulation=MakeShared<FRaftSimDetailWaterGPU,ESPMode::ThreadSafe>();
    ON_SCOPE_EXIT
    {
        ENQUEUE_RENDER_COMMAND(RaftSimRegisteredDetailRelease)([Simulation](FRHICommandListImmediate&) { Simulation->Reset(); });
        FlushRenderingCommands();
    };
    auto SeedRead=MakeShared<FRHIGPUBufferReadback,ESPMode::ThreadSafe>(TEXT("RegisteredDetailSeed"));
    bool OK=false;FString Error;
    ENQUEUE_RENDER_COMMAND(RaftSimRegisteredDetailSeed)([&](FRHICommandListImmediate& Cmd)
    { OK=Simulation->Advance(Cmd,Grid,Flow,1,&Initial,&SeedRead.Get(),Error); });
    FlushRenderingCommands();
    if (!OK || !ReadBuffer(SeedRead.Get(),Count,Seeded)) { AddError(TEXT("Registered detail seeding/readback failed: ")+Error);return false; }
    // Independent CPU resolve and world interpolation from actual advanced GPU
    // state. Includes moving edge taper, current dry masks and outside queries.
    const auto Expected=[&](const TArray<FVector4f>& State,const TArray<FVector4f>& Mean,FVector2f At)
    {
        const auto H=[&](int32 X,int32 Y)
        {
            X=FMath::Clamp(X,0,Nx-1);Y=FMath::Clamp(Y,0,Ny-1);
            const float Edge=FMath::Min(FMath::Min(X,Y),FMath::Min(Nx-1-X,Ny-1-Y))*.5f;
            return State[Y*Nx+X].X*FMath::SmoothStep(0.f,4.f,Edge)*FMath::SmoothStep(.02f,.4f,Mean[Y*Nx+X].X);
        };
        TArray<FVector4f> Resolved,Values;Resolved.SetNum(Count);
        for (int32 Y=0;Y<Ny;++Y)for (int32 X=0;X<Nx;++X)
        {
            const int32 I=Y*Nx+X;
            const float Edge=FMath::Min(FMath::Min(X,Y),FMath::Min(Nx-1-X,Ny-1-Y))*.5f;
            const float Weight=FMath::SmoothStep(0.f,4.f,Edge)*FMath::SmoothStep(.02f,.4f,Mean[I].X);
            Resolved[I]=Weight<=0 ? FVector4f(0,0,0,0) : FVector4f(H(X,Y),H(X+1,Y)-H(X-1,Y),
                H(X,Y+1)-H(X,Y-1),(1-FMath::Exp(-FMath::Max(State[I].W,0.f)))*Weight);
        }
        for (const auto& Q:Queries)
        {
            const FVector2f P=(FVector2f(Q.X,Q.Y)-At)/.5f;
            if (P.X<0 || P.Y<0 || P.X>Nx-1 || P.Y>Ny-1) { Values.Add(FVector4f(0,0,0,0));continue; }
            const int32 X=FMath::Clamp(FMath::FloorToInt(P.X),0,Nx-2),Y=FMath::Clamp(FMath::FloorToInt(P.Y),0,Ny-2);
            Values.Add(FMath::Lerp(FMath::Lerp(Resolved[Y*Nx+X],Resolved[Y*Nx+X+1],P.X-X),
                FMath::Lerp(Resolved[(Y+1)*Nx+X],Resolved[(Y+1)*Nx+X+1],P.X-X),P.Y-Y));
        }
        return Values;
    };
    TArray<TArray<FVector4f>> References;
    References.Add(Expected(Seeded,Flow,Origin));
    auto MovedState=Seeded;auto MovedFlow=Flow;auto MovedGrid=Grid;
    for (FIntPoint Shift:{FIntPoint(3,-2),FIntPoint(1,1)})
    {
        TArray<FVector4f> Next;Next.Init(FVector4f(0,0,0,0),Count);
        MovedGrid.OriginMeters+=FVector2f(Shift.X*.5f,Shift.Y*.5f);
        MovedFlow[5*Nx+7].X=0;
        for (int32 Y=0;Y<Ny;++Y)for (int32 X=0;X<Nx;++X)
            if (X+Shift.X>=0 && X+Shift.X<Nx && Y+Shift.Y>=0 && Y+Shift.Y<Ny && MovedFlow[Y*Nx+X].X>.01f)
                Next[Y*Nx+X]=MovedState[(Y+Shift.Y)*Nx+X+Shift.X];
        MovedState=MoveTemp(Next);References.Add(Expected(MovedState,MovedFlow,MovedGrid.OriginMeters));
    }
    const auto WrongOrigin=Expected(Seeded,Flow,Origin+FVector2f(1.5f,-1.f));
    float OriginSensitivity=0;
    for (int32 I=0;I<Queries.Num();++I)for (int32 C=0;C<4;++C)
        OriginSensitivity=FMath::Max(OriginSensitivity,FMath::Abs(WrongOrigin[I][C]-References[0][I][C]));
    TestTrue(TEXT("fixture detects using the current origin for previous pixels"),OriginSensitivity>1.e-3f);
    TArray<TSharedPtr<FRHIGPUBufferReadback,ESPMode::ThreadSafe>> Reads;
    for (int32 I=0;I<6;++I)Reads.Add(MakeShared<FRHIGPUBufferReadback,ESPMode::ThreadSafe>(TEXT("RegisteredDetailHistory")));
    uint64 Captures=0;
    ENQUEUE_RENDER_COMMAND(RaftSimRegisteredDetailHistory)([&](FRHICommandListImmediate& Cmd)
    {
        const auto MakeTexture=[&]()
        {
            return Cmd.CreateTexture(FRHITextureCreateDesc::Create2D(TEXT("RegisteredDetailHistory"),Nx,Ny+1,PF_A32B32G32R32F)
                .SetFlags(ETextureCreateFlags::ShaderResource|ETextureCreateFlags::UAV).SetInitialState(ERHIAccess::SRVMask));
        };
        auto Current=MakeTexture(),Previous=MakeTexture();FRaftSimWaterTextureHistory History;
        OK=Simulation->Resolve(Cmd,Current,Error) && History.Start(Cmd,Current,Previous);
        OK &= RaftSimValidateRegisteredDetailSamplingGPU(Cmd,Previous,Queries,Reads[0].Get(),Error);
        auto At=Grid;auto NewFlow=Flow;NewFlow[5*Nx+7].X=0;
        At.OriginMeters+=FVector2f(1.5f,-1.f);
        OK &= Simulation->RemapWindow(Cmd,At,NewFlow,Error) && Simulation->Resolve(Cmd,Current,Error);
        OK &= RaftSimValidateRegisteredDetailSamplingGPU(Cmd,Previous,Queries,Reads[1].Get(),Error);
        OK &= RaftSimValidateRegisteredDetailSamplingGPU(Cmd,Current,Queries,Reads[2].Get(),Error);
        At.OriginMeters+=FVector2f(.5f,.5f);
        OK &= Simulation->RemapWindow(Cmd,At,NewFlow,Error) && Simulation->Resolve(Cmd,Current,Error);
        OK &= RaftSimValidateRegisteredDetailSamplingGPU(Cmd,Previous,Queries,Reads[3].Get(),Error);
        History.CaptureFrame(Cmd);
        OK &= RaftSimValidateRegisteredDetailSamplingGPU(Cmd,Previous,Queries,Reads[4].Get(),Error);
        History.CaptureFrame(Cmd);
        OK &= RaftSimValidateRegisteredDetailSamplingGPU(Cmd,Previous,Queries,Reads[5].Get(),Error);
        Captures=History.GetCapturedFrames();History.Stop();
    });
    FlushRenderingCommands();
    if (!TestTrue(TEXT("real remap/metadata resolve/history/sample dispatches succeed"),OK)) { AddError(Error);return false; }
    const int32 ReferenceIndex[]={0,0,1,0,2,2};float MaxError=0;bool Finite=true;
    for (int32 R=0;R<Reads.Num();++R)
    {
        TArray<FVector4f> Values;
        if (!ReadBuffer(*Reads[R].Get(),Queries.Num(),Values)) { AddError(TEXT("Registered history readback timeout"));return false; }
        for (int32 I=0;I<Values.Num();++I)for (int32 C=0;C<4;++C)
        {
            Finite &= FMath::IsFinite(Values[I][C]);
            MaxError=FMath::Max(MaxError,FMath::Abs(Values[I][C]-References[ReferenceIndex[R]][I][C]));
        }
    }
    TestEqual(TEXT("only rendered-frame captures update history"),Captures,uint64(2));
    TestTrue(TEXT("world samples use each texture's own origin across multiple/no updates and never filter metadata"),Finite && MaxError<1.e-6f);
    AddInfo(FString::Printf(TEXT("Registered GPU history: 42 world samples across six snapshots, max RGBA error %.9g; actual remap and resolved metadata"),MaxError));
    return !HasAnyErrors();
}
#endif
