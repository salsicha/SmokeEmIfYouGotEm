#include "Misc/AutomationTest.h"
#include "RaftSimDetailWaterGPU.h"
#include "RaftSimDetailEntrainment.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "RHIGPUReadback.h"
#include "RHICommandList.h"
#include "RenderingThread.h"
#include "HAL/PlatformProcess.h"

#if WITH_AUTOMATION_TESTS
namespace
{
bool ReadDetailFixture(const FRaftSimDetailWaterGrid& Grid,const TArray<FVector4f>& Flow,
    const TArray<FVector4f>& Initial,int32 Steps,TArray<FVector4f>& Result,FString& Error,bool bSplitBatch=false)
{
    auto Simulation=MakeShared<FRaftSimDetailWaterGPU,ESPMode::ThreadSafe>();
    auto Readback=MakeShared<FRHIGPUBufferReadback,ESPMode::ThreadSafe>(TEXT("RaftSimDetailFixture"));
    bool bAdvanced=false;
    ENQUEUE_RENDER_COMMAND(RaftSimDetailFixture)([&](FRHICommandListImmediate& Cmd)
    {
        bAdvanced=bSplitBatch ?
            Simulation->Advance(Cmd,Grid,Flow,Steps/2,&Initial,nullptr,Error) &&
            Simulation->Advance(Cmd,Grid,Flow,Steps-Steps/2,nullptr,&Readback.Get(),Error) :
            Simulation->Advance(Cmd,Grid,Flow,Steps,&Initial,&Readback.Get(),Error);
    });
    FlushRenderingCommands();
    if (!bAdvanced)return false;
    const double Deadline=FPlatformTime::Seconds()+10;
    while (!Readback->IsReady() && FPlatformTime::Seconds()<Deadline)FPlatformProcess::Sleep(0.01f);
    if (!Readback->IsReady()) { Error=TEXT("GPU readback timed out");return false; }
    ENQUEUE_RENDER_COMMAND(RaftSimDetailFixtureRead)([&](FRHICommandListImmediate& Cmd)
    {
        const void* Data=Readback->Lock(Initial.Num()*sizeof(FVector4f));
        Result.SetNumUninitialized(Initial.Num());FMemory::Memcpy(Result.GetData(),Data,Initial.Num()*sizeof(FVector4f));
        Readback->Unlock();Simulation->Reset();
    });
    FlushRenderingCommands();
    return true;
}
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimDetailWaterValidationTest,
    "RaftSim.WaterDetail.InputAndCFLValidation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)
bool FRaftSimDetailWaterValidationTest::RunTest(const FString&)
{
    FRaftSimDetailWaterGrid Grid;Grid.Size=FIntPoint(16,16);
    TArray<FVector4f> Flow;Flow.Init(FVector4f(2,2,0,0),256);
    FString Error;
    TestTrue(TEXT("valid flow and two-dimensional CFL"),Grid.Validate(Flow,Error));
    Grid.StepSeconds=1;
    TestFalse(TEXT("unstable timestep rejected instead of clamping water"),Grid.Validate(Flow,Error));
    Grid.StepSeconds=1.0f/120;
    Flow[0].X=-1;
    TestFalse(TEXT("negative background depth rejected"),Grid.Validate(Flow,Error));
    Flow[0]=FVector4f(2,2,0,2);
    TestFalse(TEXT("invalid source rejected"),Grid.Validate(Flow,Error));
    Flow[0]=FVector4f(2,2,0,0);
    Grid.TurbulentHeadMeters=-0.01f;
    TestFalse(TEXT("negative pressure forcing rejected"),Grid.Validate(Flow,Error));
    Grid.TurbulentHeadMeters=0.11f;
    TestFalse(TEXT("unbounded pressure forcing rejected"),Grid.Validate(Flow,Error));
    Grid.TurbulentHeadMeters=0.06f;
    TestTrue(TEXT("review pressure forcing valid"),Grid.Validate(Flow,Error));
    Flow.Pop();
    TestFalse(TEXT("incomplete input rejected"),Grid.Validate(Flow,Error));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimDetailWaterGPUTest,
    "RaftSim.WaterDetail.PersistentTransportGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)
bool FRaftSimDetailWaterGPUTest::RunTest(const FString&)
{
    if (GUsingNullRHI || GMaxRHIFeatureLevel<ERHIFeatureLevel::SM5)
    { AddError(TEXT("Real SM5+ GPU required; NullRHI is not simulation evidence"));return false; }
    FRaftSimDetailWaterGrid Grid;Grid.Size=FIntPoint(64,64);Grid.bPeriodic=true;
    Grid.MomentumDampingPerSecond=0;Grid.FoamDecayPerSecond=0;Grid.FoamSourcePerSecond=0;
    TArray<FVector4f> Flow,Initial,Result;
    Flow.Init(FVector4f(1,2,0,0),4096);Initial.Init(FVector4f(0,0,0,0),4096);
    double InitialFoam=0,InitialWeightedX=0,InitialHeight=0;
    for (int32 Y=0;Y<64;++Y)for (int32 X=0;X<64;++X)
    {
        const float R2=FMath::Square((X-20)*0.5f)+FMath::Square((Y-32)*0.5f);
        const float Gaussian=R2<9 ? FMath::Exp(-R2/2) : 0;
        Initial[Y*64+X]=FVector4f(0.02f*Gaussian,0,0,Gaussian);
        InitialFoam+=Gaussian;InitialWeightedX+=Gaussian*X*0.5;InitialHeight+=0.02f*Gaussian;
    }
    auto Simulation=MakeShared<FRaftSimDetailWaterGPU,ESPMode::ThreadSafe>();
    auto Readback=MakeShared<FRHIGPUBufferReadback,ESPMode::ThreadSafe>(TEXT("RaftSimDetailRegression"));
    bool bAdvance=false,bRefusedReset=false,bRefusedRescale=false,bRefusedMove=false,bRefusedMode=false;FString Error;uint64 StepCount=0;
    // Two separate render graphs exercise persistence, not one transient batch.
    ENQUEUE_RENDER_COMMAND(RaftSimDetailTransport)([&](FRHICommandListImmediate& Cmd)
    {
        bAdvance=Simulation->Advance(Cmd,Grid,Flow,60,&Initial,nullptr,Error) &&
            Simulation->Advance(Cmd,Grid,Flow,60,nullptr,&Readback.Get(),Error);
        bRefusedReset=!Simulation->Advance(Cmd,Grid,Flow,1,&Initial,nullptr,Error);
        auto Rescaled=Grid;Rescaled.CellMeters*=2;
        bRefusedRescale=!Simulation->Advance(Cmd,Rescaled,Flow,1,nullptr,nullptr,Error);
        auto Moved=Grid;Moved.OriginMeters.X+=0.5f;
        bRefusedMove=!Simulation->Advance(Cmd,Moved,Flow,1,nullptr,nullptr,Error);
        auto ChangedMode=Grid;ChangedMode.bSecondOrder=true;
        bRefusedMode=!Simulation->Advance(Cmd,ChangedMode,Flow,1,nullptr,nullptr,Error);
        StepCount=Simulation->GetStepCount();
    });
    FlushRenderingCommands();
    TestTrue(TEXT("persistent GPU dispatch succeeds"),bAdvance);
    TestTrue(TEXT("implicit reseed rejected"),bRefusedReset);
    TestTrue(TEXT("implicit spatial rescaling rejected"),bRefusedRescale);
    TestTrue(TEXT("implicit world-window jump rejected"),bRefusedMove);
    TestTrue(TEXT("implicit transport-mode change rejected"),bRefusedMode);
    TestEqual(TEXT("persistent step counter"),StepCount,uint64(120));
    if (!bAdvance) { AddError(Error);return false; }
    const double Deadline=FPlatformTime::Seconds()+10;
    while (!Readback->IsReady() && FPlatformTime::Seconds()<Deadline)FPlatformProcess::Sleep(0.01f);
    if (!Readback->IsReady()) { AddError(TEXT("GPU readback timed out"));return false; }
    ENQUEUE_RENDER_COMMAND(RaftSimDetailReadback)([&](FRHICommandListImmediate& Cmd)
    {
        const void* Data=Readback->Lock(Initial.Num()*sizeof(FVector4f));
        Result.SetNumUninitialized(Initial.Num());FMemory::Memcpy(Result.GetData(),Data,Initial.Num()*sizeof(FVector4f));
        Readback->Unlock();Simulation->Reset();
    });
    FlushRenderingCommands();
    double Foam=0,WeightedX=0,Height=0;float MinimumFoam=1,MaximumHeight=0;bool bFinite=true;
    for (int32 I=0;I<Result.Num();++I)
    {
        const FVector4f& S=Result[I];
        bFinite &= FMath::IsFinite(S.X)&&FMath::IsFinite(S.Y)&&FMath::IsFinite(S.Z)&&FMath::IsFinite(S.W);
        Foam+=S.W;WeightedX+=S.W*(I%64)*0.5;Height+=S.X;
        MinimumFoam=FMath::Min(MinimumFoam,S.W);MaximumHeight=FMath::Max(MaximumHeight,FMath::Abs(S.X));
    }
    TestTrue(TEXT("GPU state remains finite"),bFinite);
    TestTrue(TEXT("transport conserves foam mass"),FMath::Abs(Foam-InitialFoam)<1.e-4);
    TestTrue(TEXT("closed wave transport conserves height integral"),FMath::Abs(Height-InitialHeight)<1.e-5);
    TestTrue(TEXT("foam follows 2 m/s mean current, not gravity-wave speed"),FMath::Abs(WeightedX/Foam-InitialWeightedX/InitialFoam-2)<0.002);
    TestTrue(TEXT("upwind foam remains nonnegative"),MinimumFoam>=-1.e-7f);
    TestTrue(TEXT("initial crest propagates without growth"),MaximumHeight<0.02f && MaximumHeight>0.001f);
    AddInfo(FString::Printf(TEXT("GPU: foam mass error %.9g, height integral error %.9g, mean foam travel %.6f m"),
        Foam-InitialFoam,Height-InitialHeight,WeightedX/Foam-InitialWeightedX/InitialFoam));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimDetailWaterShoreGPUTest,
    "RaftSim.WaterDetail.UnevenDepthAndDryShoreGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)
bool FRaftSimDetailWaterShoreGPUTest::RunTest(const FString&)
{
    if (GUsingNullRHI || GMaxRHIFeatureLevel<ERHIFeatureLevel::SM5)
    { AddError(TEXT("Real SM5+ GPU required"));return false; }
    FRaftSimDetailWaterGrid Grid;Grid.Size=FIntPoint(48,32);
    Grid.MomentumDampingPerSecond=0;Grid.FoamDecayPerSecond=0.3f;Grid.FoamSourcePerSecond=0.8f;
    TArray<FVector4f> Flow,Initial,Result;
    Flow.Init(FVector4f(0,0,0,0),48*32);Initial.Init(FVector4f(0,0,0,0),48*32);
    // Uneven depth, a slanted dry shore and a dry island. A spatially constant
    // 2 cm surface perturbation is at rest, even across bathymetric steps.
    for (int32 Y=0;Y<32;++Y)for (int32 X=0;X<48;++X)
        if (Y>4+X/9 && Y<28 && !(X>22 && X<27 && Y>13 && Y<20))
        {
            Flow[Y*48+X]=FVector4f(0.4f+0.03f*X+0.2f*(Y%3),0,0,0.6f);
            Initial[Y*48+X]=FVector4f(0.02f,0,0,0.4f);
        }
    FString Error;
    if (!TestTrue(TEXT("uneven-depth GPU fixture dispatches"),ReadDetailFixture(Grid,Flow,Initial,120,Result,Error)))
    { AddError(Error);return false; }
    float MaximumMomentum=0,MaximumHeightError=0,MaximumDryState=0,MaximumFoamError=0;
    const float ExpectedFoam=0.4f*FMath::Exp(-0.3f)+0.8f*0.6f*(1-FMath::Exp(-0.3f))/0.3f;
    for (int32 I=0;I<Result.Num();++I)
    {
        const FVector4f& S=Result[I];
        if (Flow[I].X>0.01f)
        {
            MaximumMomentum=FMath::Max(MaximumMomentum,FMath::Max(FMath::Abs(S.Y),FMath::Abs(S.Z)));
            MaximumHeightError=FMath::Max(MaximumHeightError,FMath::Abs(S.X-0.02f));
            MaximumFoamError=FMath::Max(MaximumFoamError,FMath::Abs(S.W-ExpectedFoam));
        }
        else MaximumDryState=FMath::Max(MaximumDryState,FMath::Max(FMath::Max(FMath::Abs(S.X),FMath::Abs(S.Y)),FMath::Max(FMath::Abs(S.Z),FMath::Abs(S.W))));
    }
    TestTrue(TEXT("no artificial current at depth steps"),MaximumMomentum<1.e-6f);
    TestTrue(TEXT("constant surface offset stays level"),MaximumHeightError<1.e-6f);
    TestEqual(TEXT("no water detail or foam on dry land"),MaximumDryState,0.0f);
    TestTrue(TEXT("foam source and decay follow the analytic solution"),MaximumFoamError<1.e-5f);
    AddInfo(FString::Printf(TEXT("GPU shore: momentum %.9g, height error %.9g, dry state %.9g, foam error %.9g"),
        MaximumMomentum,MaximumHeightError,MaximumDryState,MaximumFoamError));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimDetailWaterCapturedFlowGPUTest,
    "RaftSim.WaterDetail.RegisteredRockFlowGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)
bool FRaftSimDetailWaterCapturedFlowGPUTest::RunTest(const FString&)
{
    if (GUsingNullRHI || GMaxRHIFeatureLevel<ERHIFeatureLevel::SM5)
    { AddError(TEXT("Real SM5+ GPU required"));return false; }
    const FString Directory=TEXT("tmp/south-fork-survey-hydraulics/1m-mixed-inlet-registered-rock-xy-20260907/engine_review");
    URaftSimWaterRuntimeAdapter* Adapter=NewObject<URaftSimWaterRuntimeAdapter>();
    FRaftSimWaterRuntimeConfig Config;Config.bRequireAcceptedReportManifest=false;Config.bEnableDeterministicCapture=false;
    Adapter->Configure(Config);
    if (!TestTrue(TEXT("registered rock coordinate map loads"),Adapter->ConfigureRiverCoordinateMap(Directory/TEXT("coordinate_map.json"))) ||
        !TestTrue(TEXT("registered rock mean flow loads"),Adapter->ConfigureRiverWindow(Directory,TEXT("median_runnable"),
            FVector2D::ZeroVector,FVector2D(273,273),0.041f,false)))return false;
    FRaftSimDetailWaterGrid Grid;Grid.Size=FIntPoint(64,64);Grid.CellMeters=1;
    TArray<FVector4f> Flow,Initial,Result;Flow.SetNumZeroed(4096);Initial.SetNumZeroed(4096);
    const FVector Downstream(-0.9299998355760436,0.36755993501540923,0);
    const FVector Left(-Downstream.Y,Downstream.X,0);
    int32 Missing=0,Wet=0;float MaxBackgroundSpeed=0,MaxCachedFieldError=0;
    for (int32 Y=0;Y<64;++Y)for (int32 X=0;X<64;++X)
    {
        FVector Position;FRaftSimWaterSample Sample;
        if (!Adapter->RiverToWorldPosition(FVector2D(X-32,Y-32),228,Position) ||
            !Adapter->SampleWaterAtWorldPosition(Position,Sample)) { ++Missing;continue; }
        FVector2D Coordinates;FVector Tangent,Normal;FRaftSimWaterSample Field;
        if (!Adapter->WorldToRiverCoordinates(Position,Coordinates,Tangent,Normal) ||
            !Adapter->SampleWaterFieldAtRiverCoordinates(Coordinates,Field)) { ++Missing;continue; }
        const FVector CachedVelocity=Tangent*Field.VelocityMetersPerSecond.X+Normal*Field.VelocityMetersPerSecond.Y;
        MaxCachedFieldError=FMath::Max(MaxCachedFieldError,FMath::Max(FMath::Abs(Field.DepthMeters-Sample.DepthMeters),
            float((CachedVelocity-Sample.VelocityMetersPerSecond).Size())));
        if (Field.bWet!=Sample.bWet)++Missing;
        if (!Sample.bWet || Sample.DepthMeters<=0.01f)continue;
        ++Wet;
        const float U=FVector::DotProduct(Sample.VelocityMetersPerSecond,Downstream);
        const float V=FVector::DotProduct(Sample.VelocityMetersPerSecond,Left);
        const float Speed=FMath::Sqrt(U*U+V*V);MaxBackgroundSpeed=FMath::Max(MaxBackgroundSpeed,Speed);
        const float Fr=Speed/FMath::Sqrt(9.81f*Sample.DepthMeters);
        Flow[Y*64+X]=FVector4f(Sample.DepthMeters,U,V,FMath::Clamp((Fr-0.65f)/0.7f,0.0f,1.0f));
        Initial[Y*64+X]=FVector4f(0.005f*FMath::Sin(0.5f*X)*FMath::Sin(0.4f*Y)*FMath::Min(1.0f,Sample.DepthMeters/0.2f),0,0,0);
    }
    TestEqual(TEXT("complete mapped background sampling"),Missing,0);
    TestTrue(TEXT("cached coordinate/basis field sampling preserves live depth and velocity"),MaxCachedFieldError<1.e-6f);
    TestTrue(TEXT("fixture contains both captured banks and active current"),Wet>500 && Wet<4096 && MaxBackgroundSpeed>1);
    FString Error;
    if (!TestTrue(TEXT("captured flow GPU dispatches"),ReadDetailFixture(Grid,Flow,Initial,240,Result,Error)))
    { AddError(Error);return false; }
    bool bFinite=true;float MaxHeight=0,MaxFoam=0,MinFoam=0,DryState=0;
    for (int32 I=0;I<Result.Num();++I)
    {
        const FVector4f& S=Result[I];
        bFinite &= FMath::IsFinite(S.X)&&FMath::IsFinite(S.Y)&&FMath::IsFinite(S.Z)&&FMath::IsFinite(S.W);
        MaxHeight=FMath::Max(MaxHeight,FMath::Abs(S.X));MaxFoam=FMath::Max(MaxFoam,S.W);MinFoam=FMath::Min(MinFoam,S.W);
        if (Flow[I].X<=0.01f)DryState=FMath::Max(DryState,FMath::Max(FMath::Max(FMath::Abs(S.X),FMath::Abs(S.Y)),FMath::Max(FMath::Abs(S.Z),FMath::Abs(S.W))));
    }
    TestTrue(TEXT("captured-flow detail stays finite"),bFinite);
    TestTrue(TEXT("small perturbations remain below five centimetres"),MaxHeight<0.05f);
    TestEqual(TEXT("no GPU water or foam on captured dry cells"),DryState,0.0f);
    TestTrue(TEXT("current produces finite nonnegative transported aeration"),MinFoam>=-1.e-6f && MaxFoam>0.01f && MaxFoam<4);
    AddInfo(FString::Printf(TEXT("Captured flow GPU: wet %d/4096, background speed %.6f, max detail height %.9g m, foam [%.9g,%.9g]"),
        Wet,MaxBackgroundSpeed,MaxHeight,MinFoam,MaxFoam));
    AddInfo(TEXT("Frozen registered-rock mean flow and synthetic 5mm perturbation for two seconds; not continuous runtime coupling or visual acceptance."));
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimDetailWaterForcedGPUTest,
    "RaftSim.WaterDetail.PressureExcitationGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)
bool FRaftSimDetailWaterForcedGPUTest::RunTest(const FString&)
{
    if (GUsingNullRHI || GMaxRHIFeatureLevel<ERHIFeatureLevel::SM5)
    { AddError(TEXT("Real SM5+ GPU required"));return false; }
    FRaftSimDetailWaterGrid Grid;Grid.Size=FIntPoint(48,32);Grid.TurbulentHeadMeters=0.06f;
    Grid.OriginMeters=FVector2f(-12,-8);
    TArray<FVector4f> Flow,Initial,Whole,Split,Inactive;
    Flow.SetNumZeroed(48*32);Initial.SetNumZeroed(48*32);
    for (int32 Y=0;Y<32;++Y)for (int32 X=0;X<48;++X)
        if (Y>3+X/12 && Y<28)Flow[Y*48+X]=FVector4f(0.7f+X*0.02f,0.4f,0,0.8f);
    FString Error;
    if (!ReadDetailFixture(Grid,Flow,Initial,240,Whole,Error) ||
        !ReadDetailFixture(Grid,Flow,Initial,240,Split,Error,true))
    { AddError(Error);return false; }
    float MaxHeight=0,MaxDifference=0,Dry=0;bool bFinite=true;
    for (int32 I=0;I<Whole.Num();++I)
    {
        const FVector4f& S=Whole[I];
        for (int32 C=0;C<4;++C)
        {
            bFinite &= FMath::IsFinite(S[C]);
            MaxDifference=FMath::Max(MaxDifference,FMath::Abs(S[C]-Split[I][C]));
            if (Flow[I].X<=0.01f)Dry=FMath::Max(Dry,FMath::Abs(S[C]));
        }
        MaxHeight=FMath::Max(MaxHeight,FMath::Abs(S.X));
    }
    TestTrue(TEXT("pressure forcing produces finite actual surface relief"),bFinite && MaxHeight>0.001f && MaxHeight<0.1f);
    TestTrue(TEXT("forcing clock independent of render-graph batch boundaries"),MaxDifference<1.e-6f);
    TestEqual(TEXT("pressure forcing cannot create water on dry land"),Dry,0.0f);
    for (FVector4f& F:Flow)F.W=0;
    if (!ReadDetailFixture(Grid,Flow,Initial,240,Inactive,Error)) { AddError(Error);return false; }
    float Quiet=0;
    for (const FVector4f& S:Inactive)for (int32 C=0;C<4;++C)Quiet=FMath::Max(Quiet,FMath::Abs(S[C]));
    TestEqual(TEXT("no unforced lake turbulence"),Quiet,0.0f);
    AddInfo(FString::Printf(TEXT("Pressure excitation: max height %.9g m, batch error %.9g, dry state %.9g"),MaxHeight,MaxDifference,Dry));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimDetailWaterResolveGPUTest,
    "RaftSim.WaterDetail.SurfaceTextureResolveGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)
bool FRaftSimDetailWaterResolveGPUTest::RunTest(const FString&)
{
    if (GUsingNullRHI || GMaxRHIFeatureLevel<ERHIFeatureLevel::SM5)
    { AddError(TEXT("Real SM5+ GPU required"));return false; }
    FRaftSimDetailWaterGrid Grid;Grid.Size=FIntPoint(32,32);Grid.FoamDecayPerSecond=0;Grid.FoamSourcePerSecond=0;
    TArray<FVector4f> Flow,Initial,Resolved;
    Flow.SetNumZeroed(1024);Initial.SetNumZeroed(1024);
    for (int32 Y=0;Y<32;++Y)for (int32 X=0;X<32;++X)
        if (Y>3+X/12 && !(X>14 && X<18 && Y>14 && Y<18))
        {
            Flow[Y*32+X]=FVector4f(0.04f+X*0.02f,0,0,0);
            Initial[Y*32+X]=FVector4f(0.02f,0,0,0.4f);
        }
    auto Simulation=MakeShared<FRaftSimDetailWaterGPU,ESPMode::ThreadSafe>();
    auto Readback=MakeShared<FRHIGPUTextureReadback,ESPMode::ThreadSafe>(TEXT("RaftSimDetailResolveFixture"));
    FTextureRHIRef Texture;FString Error;bool bResolved=false,bRejectEmpty=false;
    ENQUEUE_RENDER_COMMAND(RaftSimDetailResolveFixture)([&](FRHICommandListImmediate& Cmd)
    {
        const auto Desc=FRHITextureCreateDesc::Create2D(TEXT("DetailResolveTest"),Grid.Size,PF_A32B32G32R32F)
            .SetFlags(ETextureCreateFlags::ShaderResource|ETextureCreateFlags::UAV)
            .SetInitialState(ERHIAccess::UAVCompute);
        Texture=Cmd.CreateTexture(Desc);
        bRejectEmpty=!Simulation->Resolve(Cmd,Texture,Error);
        bResolved=Simulation->Advance(Cmd,Grid,Flow,1,&Initial,nullptr,Error) && Simulation->Resolve(Cmd,Texture,Error);
        if (bResolved)
        {
            Cmd.Transition(FRHITransitionInfo(Texture,ERHIAccess::SRVMask,ERHIAccess::CopySrc));
            Readback->EnqueueCopy(Cmd,Texture);
        }
    });
    FlushRenderingCommands();
    TestTrue(TEXT("cannot resolve uninitialized state"),bRejectEmpty);
    if (!TestTrue(TEXT("GPU surface texture resolves"),bResolved)) { AddError(Error);return false; }
    const double Deadline=FPlatformTime::Seconds()+10;
    while (!Readback->IsReady() && FPlatformTime::Seconds()<Deadline)FPlatformProcess::Sleep(0.01f);
    if (!Readback->IsReady()) { AddError(TEXT("GPU texture readback timed out"));return false; }
    ENQUEUE_RENDER_COMMAND(RaftSimDetailResolveRead)([&](FRHICommandListImmediate& Cmd)
    {
        int32 RowPitch=0;const auto* Data=static_cast<const FVector4f*>(Readback->Lock(RowPitch));
        Resolved.SetNumUninitialized(1024);
        for (int32 Y=0;Y<32;++Y)FMemory::Memcpy(Resolved.GetData()+Y*32,Data+Y*RowPitch,32*sizeof(FVector4f));
        Readback->Unlock();Simulation->Reset();Texture.SafeRelease();
    });
    FlushRenderingCommands();
    const auto Smooth=[](float A,float B,float V) { const float T=FMath::Clamp((V-A)/(B-A),0.0f,1.0f);return T*T*(3-2*T); };
    const auto Weight=[&](int32 X,int32 Y)
    { return Smooth(0,4,FMath::Min(FMath::Min(X,Y),FMath::Min(31-X,31-Y))*0.5f)*Smooth(0.02f,0.4f,Flow[Y*32+X].X); };
    const auto Height=[&](int32 X,int32 Y) { return 0.02f*Weight(FMath::Clamp(X,0,31),FMath::Clamp(Y,0,31)); };
    float MaxError=0,DryState=0;bool bFinite=true;
    for (int32 Y=0;Y<32;++Y)for (int32 X=0;X<32;++X)
    {
        const float W=Weight(X,Y);FVector4f Expected(0,0,0,0);
        if (W>0)Expected=FVector4f(Height(X,Y),Height(X+1,Y)-Height(X-1,Y),Height(X,Y+1)-Height(X,Y-1),W*(1-FMath::Exp(-0.4f)));
        const FVector4f& S=Resolved[Y*32+X];
        for (int32 C=0;C<4;++C)
        {
            bFinite &= FMath::IsFinite(S[C]);MaxError=FMath::Max(MaxError,FMath::Abs(S[C]-Expected[C]));
            if (W==0)DryState=FMath::Max(DryState,FMath::Abs(S[C]));
        }
    }
    TestTrue(TEXT("height, tapered slopes and foam conversion match independently computed CPU values"),bFinite && MaxError<1.e-6f);
    TestEqual(TEXT("resolved dry land and window boundary exactly zero"),DryState,0.0f);
    AddInfo(FString::Printf(TEXT("Surface texture resolve: maximum RGBA error %.9g, dry/edge output %.9g"),MaxError,DryState));
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimDetailWaterEntrainmentTest,
    "RaftSim.WaterDetail.BreakingSourceLocalization",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)
bool FRaftSimDetailWaterEntrainmentTest::RunTest(const FString&)
{
    const FIntPoint Size(32,32);TArray<FVector4f> Uniform,Jump,Rotated;
    Uniform.SetNumZeroed(1024);Jump.SetNumZeroed(1024);Rotated.SetNumZeroed(1024);
    for (int32 Y=0;Y<32;++Y)for (int32 X=0;X<32;++X)
        if (Y>4+X/10 && Y<28 && !(X>13 && X<17 && Y>14 && Y<18))
        {
            Uniform[Y*32+X]=FVector4f(0.5f,4,0,0);
            const float U=4-FMath::Clamp((X-12)*0.5f,0.0f,3.0f);
            Jump[Y*32+X]=FVector4f(0.5f,U,0,0);
            Rotated[X*32+(31-Y)]=FVector4f(0.5f,0,U,0);
        }
    FRaftSimDetailEntrainment::Build(Size,0.5f,Uniform);
    FRaftSimDetailEntrainment::Build(Size,0.5f,Jump);
    FRaftSimDetailEntrainment::Build(Size,0.5f,Rotated);
    float MaxUniform=0,MaxJump=0,MaxDry=0,MaxRotationError=0,MaxOutside=0;
    for (int32 Y=0;Y<32;++Y)for (int32 X=0;X<32;++X)
    {
        const int32 I=Y*32+X;
        MaxUniform=FMath::Max(MaxUniform,Uniform[I].W);MaxJump=FMath::Max(MaxJump,Jump[I].W);
        MaxRotationError=FMath::Max(MaxRotationError,FMath::Abs(Jump[I].W-Rotated[X*32+31-Y].W));
        if (Jump[I].X==0)MaxDry=FMath::Max(MaxDry,Jump[I].W);
        if (X<12 || X>18)MaxOutside=FMath::Max(MaxOutside,Jump[I].W);
    }
    TestEqual(TEXT("uniform fast current emits no blanket foam, including along dry shore/island"),MaxUniform,0.0f);
    TestTrue(TEXT("decelerating transition produces entrainment"),MaxJump>0.5f && MaxJump<=1);
    TestEqual(TEXT("source restricted to transition, not downstream calm runout"),MaxOutside,0.0f);
    TestEqual(TEXT("dry source exactly zero"),MaxDry,0.0f);
    TestTrue(TEXT("source independent of channel orientation"),MaxRotationError<1.e-6f);
    AddInfo(FString::Printf(TEXT("Breaking source: uniform %.9g, transition %.9g, dry %.9g, rotation error %.9g"),MaxUniform,MaxJump,MaxDry,MaxRotationError));
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimDetailSecondOrderTest,
    "RaftSim.WaterDetail.LimitedSecondOrderGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)
bool FRaftSimDetailSecondOrderTest::RunTest(const FString&)
{
    if (GUsingNullRHI || GMaxRHIFeatureLevel<ERHIFeatureLevel::SM5)
    { AddError(TEXT("Real SM5+ GPU required"));return false; }
    FRaftSimDetailWaterGrid Grid;Grid.Size=FIntPoint(64,32);Grid.bPeriodic=true;
    Grid.MomentumDampingPerSecond=0;Grid.FoamDecayPerSecond=0;Grid.FoamSourcePerSecond=0;
    const double WaveSpeed=FMath::Sqrt(9.81),K=2*PI/8.0;
    TArray<FVector4f> Flow,Initial,First,Second,Split;
    Flow.Init(FVector4f(1,2,0,0),2048);Initial.SetNumUninitialized(2048);
    double InitialFoam=0,InitialWeightedX=0;
    for (int32 Y=0;Y<32;++Y)for (int32 X=0;X<64;++X)
    {
        const double Eta=0.02*FMath::Sin(K*X*0.5)*FMath::Sin(K*0.25)/(K*0.25);
        const float Foam=FMath::Abs(X-20)<8 ? FMath::Exp(-FMath::Square((X-20)*0.5f)/2) : 0;
        Initial[Y*64+X]=FVector4f(Eta,WaveSpeed*Eta,0,Foam);
        InitialFoam+=Foam;InitialWeightedX+=Foam*X*0.5;
    }
    FString Error;
    if (!ReadDetailFixture(Grid,Flow,Initial,120,First,Error)) { AddError(Error);return false; }
    Grid.bSecondOrder=true;
    if (!ReadDetailFixture(Grid,Flow,Initial,120,Second,Error) ||
        !ReadDetailFixture(Grid,Flow,Initial,120,Split,Error,true)) { AddError(Error);return false; }
    double FirstError=0,SecondError=0,Foam=0,WeightedX=0,Height=0,MaxAmplitude=0,MinFoam=1,MaxBatchError=0;
    for (int32 I=0;I<Second.Num();++I)
    {
        const auto S=Second[I];const double X=(I%64)*0.5;
        const double Expected=0.02*FMath::Sin(K*(X-(2+WaveSpeed)*120*double(Grid.StepSeconds)))*FMath::Sin(K*0.25)/(K*0.25);
        FirstError+=FMath::Square(First[I].X-Expected);SecondError+=FMath::Square(S.X-Expected);
        Foam+=S.W;WeightedX+=S.W*X;Height+=S.X;MinFoam=FMath::Min(MinFoam,double(S.W));
        MaxAmplitude=FMath::Max(MaxAmplitude,FMath::Abs(double(S.X)));
        for (int32 C=0;C<4;++C)
        {
            if (!FMath::IsFinite(S[C])) { AddError(TEXT("Nonfinite limited state"));return false; }
            MaxBatchError=FMath::Max(MaxBatchError,double(FMath::Abs(S[C]-Split[I][C])));
        }
    }
    FirstError=FMath::Sqrt(FirstError/Second.Num());SecondError=FMath::Sqrt(SecondError/Second.Num());
    TestTrue(TEXT("less than 65 percent of first-order wave RMS error at SAME grid, time and amplitude"),SecondError<0.65*FirstError);
    TestTrue(TEXT("no artificial wave amplitude growth"),MaxAmplitude<=0.020001);
    TestTrue(TEXT("conservative limited foam transport"),FMath::Abs(Foam-InitialFoam)<0.001);
    TestTrue(TEXT("foam follows mean flow, not wave phase"),FMath::Abs(WeightedX/Foam-InitialWeightedX/InitialFoam-2)<0.002);
    TestTrue(TEXT("no negative density or height-integral drift"),MinFoam>=-1.e-7 && FMath::Abs(Height)<1.e-4);
    TestEqual(TEXT("stage clock/state survive render graph boundaries"),MaxBatchError,0.0);

    // Uneven rest plus dry island checks pressure/source balancing with both
    // stages. No foam or water is allowed to leak into dry cells.
    Grid.bPeriodic=false;Grid.FoamDecayPerSecond=0.3f;Grid.FoamSourcePerSecond=0.8f;
    for (int32 Y=0;Y<32;++Y)for (int32 X=0;X<64;++X)
    {
        const int32 I=Y*64+X;
        const bool Wet=Y>3+X/15 && Y<29 && !(X>22 && X<28 && Y>12 && Y<20);
        Flow[I]=Wet ? FVector4f(0.4f+0.01f*X+0.2f*(Y%3),0,0,0.6f) : FVector4f(0,0,0,0);
        Initial[I]=Wet ? FVector4f(0.02f,0,0,0.4f) : FVector4f(0,0,0,0);
    }
    if (!ReadDetailFixture(Grid,Flow,Initial,120,Second,Error)) { AddError(Error);return false; }
    const float ExpectedFoam=0.4f*FMath::Exp(-0.3f)+0.8f*0.6f*(1-FMath::Exp(-0.3f))/0.3f;
    double MaxRestError=0,MaxDry=0,MaxSourceError=0;
    for (int32 I=0;I<Second.Num();++I)
    {
        const auto S=Second[I];
        if (Flow[I].X>0.01f)
        {
            MaxRestError=FMath::Max(MaxRestError,double(FMath::Max3(FMath::Abs(S.X-0.02f),FMath::Abs(S.Y),FMath::Abs(S.Z))));
            MaxSourceError=FMath::Max(MaxSourceError,double(FMath::Abs(S.W-ExpectedFoam)));
        }
        else for (int32 C=0;C<4;++C)MaxDry=FMath::Max(MaxDry,double(FMath::Abs(S[C])));
    }
    TestTrue(TEXT("uneven constant offset at rest"),MaxRestError<1.e-6);
    TestEqual(TEXT("dry land remains empty"),MaxDry,0.0);
    TestTrue(TEXT("source/decay applied once per full step"),MaxSourceError<1.e-5);
    Grid.TurbulentHeadMeters=0.06f;
    if (!ReadDetailFixture(Grid,Flow,Initial,120,Second,Error) ||
        !ReadDetailFixture(Grid,Flow,Initial,120,Split,Error,true)) { AddError(Error);return false; }
    double ForcedBatchError=0,ForcedHeight=0;
    for (int32 I=0;I<Second.Num();++I)
    {
        if (Flow[I].X>0.01f)ForcedHeight=FMath::Max(ForcedHeight,double(FMath::Abs(Second[I].X-0.02f)));
        for (int32 C=0;C<4;++C)
        {
            if (!FMath::IsFinite(Second[I][C])) { AddError(TEXT("Nonfinite forced RK2 state"));return false; }
            ForcedBatchError=FMath::Max(ForcedBatchError,double(FMath::Abs(Second[I][C]-Split[I][C])));
            if (Flow[I].X<=0.01f)MaxDry=FMath::Max(MaxDry,double(FMath::Abs(Second[I][C])));
        }
    }
    TestEqual(TEXT("time-dependent pressure forcing has the same stage clock across batches"),ForcedBatchError,0.0);
    TestTrue(TEXT("bounded nonzero pressure response without a height clamp"),ForcedHeight>0.001 && ForcedHeight<0.1);
    TestEqual(TEXT("forced dry shore remains empty"),MaxDry,0.0);
    AddInfo(FString::Printf(TEXT("Limited RK2: RMS first %.9g second %.9g m, amplitude %.9g m; foam mass error %.9g, travel %.9g m, batch %.9g; rest %.9g dry %.9g source %.9g"),
        FirstError,SecondError,MaxAmplitude,Foam-InitialFoam,WeightedX/Foam-InitialWeightedX/InitialFoam,MaxBatchError,MaxRestError,MaxDry,MaxSourceError));
    AddInfo(FString::Printf(TEXT("Forced RK2: batch error %.9g, maximum height response %.9g m"),ForcedBatchError,ForcedHeight));
    return true;
}
#endif
