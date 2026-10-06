#include "Misc/AutomationTest.h"
#include "../Materials/RaftSimLiquidGraphHistory.h"
#include "../Materials/RaftSimLiquidReconstructionLayout.h"
#include "RaftSimLiquidFoamGPU.h"
#include "RenderGraphUtils.h"
#include "RenderingThread.h"
#include "RHIGPUReadback.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLiquidReconstructionLayoutTest,"RaftSim.Editor.LiquidReconstructionLayout",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FLiquidReconstructionLayoutTest::RunTest(const FString&)
{
    FRaftSimLiquidReconstructionLayout L;FString Error;
    TestEqual(TEXT("Legacy minimum unchanged"),L.MinimumMeters(),FVector3f(-11.15625f,-11.15625f,0));
    TestTrue(TEXT("Actual final region accepted"),L.Configure(FVector3f(110,38,24),FVector3f(5500,1900,800),Error));
    TestEqual(TEXT("Tail retains independent dimensions"),L.Render,FIntVector(220,76,48));
    TestEqual(TEXT("Physical rectangle excludes two-cell halo"),L.PhysicalHalfCm,FVector2f(2650,850));
    TestEqual(TEXT("Anisotropic spacing retained"),L.RenderSpacingCm(),FVector3f(25,25,800.f/48));
    for (const FVector3f Invalid:{FVector3f(111,38,24),FVector3f(110.5,38,24),FVector3f(494,166,24),FVector3f(4,38,24)})
        TestFalse(TEXT("No odd/truncated/oversized/empty physical layout"),L.Configure(Invalid,FVector3f(5500,1900,800),Error));
    TestEqual(TEXT("Invalid input cannot partially change valid layout"),L.Render,FIntVector(220,76,48));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLiquidReconstructionOwnersTest,"RaftSim.Editor.LiquidReconstructionOwnersGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FLiquidReconstructionOwnersTest::RunTest(const FString&)
{
    if (GUsingNullRHI || GMaxRHIFeatureLevel<ERHIFeatureLevel::SM5)
    { AddError(TEXT("Actual GPU required for independent history test"));return false; }
    bool Passed=false;FString Error;
    TArray<FFloat16Color> OutA,OutB,OutC;
    uint32 Status[4]={};
    ENQUEUE_RENDER_COMMAND(RaftSimOwnerHistoryTest)([&](FRHICommandListImmediate& Cmd)
    {
        auto Upload=[&](const TCHAR* Name,FIntVector Size,FLinearColor Value)
        {
            TArray<FFloat16Color> Data;Data.Init(FFloat16Color(Value),Size.X*Size.Y*Size.Z);
            auto T=Cmd.CreateTexture(FRHITextureCreateDesc::Create3D(Name,Size.X,Size.Y,Size.Z,PF_FloatRGBA)
                .SetFlags(TexCreate_ShaderResource).SetInitialState(ERHIAccess::CopyDest));
            Cmd.UpdateTexture3D(T,0,FUpdateTextureRegion3D(0,0,0,0,0,0,Size.X,Size.Y,Size.Z),
                Size.X*sizeof(FFloat16Color),Size.X*Size.Y*sizeof(FFloat16Color),reinterpret_cast<const uint8*>(Data.GetData()));
            Cmd.Transition(FRHITransitionInfo(T,ERHIAccess::CopyDest,ERHIAccess::SRVMask));return T;
        };
        const FIntVector A(12,8,8),B(8,12,8);
        auto CurrentA=Upload(TEXT("OwnerCurrentA"),A,FLinearColor(0,0,10,0));
        auto CurrentB=Upload(TEXT("OwnerCurrentB"),B,FLinearColor(0,0,20,0));
        auto HistoryA=Upload(TEXT("OwnerHistoryA"),A,FLinearColor(0,.8f,10,0));
        auto HistoryB=Upload(TEXT("OwnerHistoryB"),B,FLinearColor(0,.25,20,0));
        auto FlowA=Upload(TEXT("OwnerFlowA"),A/2,FLinearColor(0,0,0,0));
        auto FlowB=Upload(TEXT("OwnerFlowB"),B/2,FLinearColor(0,0,0,0));
        FRDGBuilder Graph(Cmd);
        auto Register=[&](FTextureRHIRef T,const TCHAR* Name){return Graph.RegisterExternalTexture(CreateRenderTarget(T,Name));};
        auto CA=Register(CurrentA,TEXT("OwnerCA")),CB=Register(CurrentB,TEXT("OwnerCB"));
        auto FA=Register(FlowA,TEXT("OwnerFA")),FB=Register(FlowB,TEXT("OwnerFB"));
        auto& Histories=Graph.Blackboard.GetOrCreate<FRaftSimLiquidGraphHistories>();
        auto& HA=Histories.ForOwner(100);auto& HB=Histories.ForOwner(200);
        const FVector4f Active(10,.1f,0,1),Paused(20,0,0,0),Reset(0,0,1,1);
        HA.Clock=CreateStructuredBuffer(Graph,TEXT("OwnerClockA"),TConstArrayView<FVector4f>(&Active,1));
        HB.Clock=CreateStructuredBuffer(Graph,TEXT("OwnerClockB"),TConstArrayView<FVector4f>(&Paused,1));
        HA.Foam=Register(HistoryA,TEXT("OwnerHA"));HB.Foam=Register(HistoryB,TEXT("OwnerHB"));
        for (uint64 Owner=300;Owner<600;++Owner) Histories.ForOwner(Owner);
        if (&HA!=&Histories.ForOwner(100) || &HB!=&Histories.ForOwner(200) || HA.Clock==HB.Clock || HA.Foam==HB.Foam)
        { Error=TEXT("Owners alias or references invalidated by registry growth");return; }
        auto Desc=FRDGBufferDesc::CreateStructuredDesc(4,4);Desc.Usage|=BUF_SourceCopy;
        auto Diagnostics=Graph.CreateBuffer(Desc,TEXT("OwnerDiagnostics"));AddClearUAVPass(Graph,Graph.CreateUAV(Diagnostics),0);
        auto Step=[&](uint64 Owner,FRDGTextureRef Current,FRDGTextureRef Flow,FVector3f Extent)
        {
            auto& H=Histories.ForOwner(Owner);
            auto R=RaftSimLiquidFoamGPU(Graph,Current,H.Foam,Flow,Flow,H.Clock,0,Extent,
                FVector2f(Extent.X*.5f,Extent.Y*.5f),0,.25f,Diagnostics,Error);
            if (R.Surface) { H.Foam=R.Surface;++H.SecondarySteps; }
            return R.Surface!=nullptr;
        };
        // Interleave two differently sized owners in ONE graph. A advances
        // twice, B is paused. A's second pass must read its pending first pass,
        // never B or the previous frame's extracted history.
        if (!Step(100,CA,FA,FVector3f(120,80,80)) || !Step(200,CB,FB,FVector3f(80,120,80)) ||
            !Step(100,CA,FA,FVector3f(120,80,80))) return;
        auto& HC=Histories.ForOwner(700);
        if (HC.Foam || HC.Clock || HC.SecondarySteps) { Error=TEXT("Fresh attachment inherited old state");return; }
        HC.Clock=CreateStructuredBuffer(Graph,TEXT("OwnerClockC"),TConstArrayView<FVector4f>(&Reset,1));
        if (!Step(700,CA,FA,FVector3f(120,80,80)) || HA.SecondarySteps!=2 || HB.SecondarySteps!=1) return;
        TRefCountPtr<IPooledRenderTarget> OA,OB,OC;
        Graph.QueueTextureExtraction(HA.Foam,&OA);Graph.QueueTextureExtraction(HB.Foam,&OB);Graph.QueueTextureExtraction(HC.Foam,&OC);
        FRHIGPUBufferReadback Read(TEXT("OwnerHistoryStatus"));AddEnqueueCopyPass(Graph,&Read,Diagnostics,sizeof(Status));
        Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle();
        FMemory::Memcpy(Status,Read.Lock(sizeof(Status)),sizeof(Status));Read.Unlock();
        Cmd.Read3DSurfaceFloatData(OA->GetRHI(),FIntRect(0,0,A.X,A.Y),FIntPoint(0,A.Z),OutA);
        Cmd.Read3DSurfaceFloatData(OB->GetRHI(),FIntRect(0,0,B.X,B.Y),FIntPoint(0,B.Z),OutB);
        Cmd.Read3DSurfaceFloatData(OC->GetRHI(),FIntRect(0,0,A.X,A.Y),FIntPoint(0,A.Z),OutC);
        // A new graph must not retain any RDG references, even for a still-live
        // owner. Cross-graph history is carried only by its extracted resource.
        FRDGBuilder Next(Cmd);
        const auto& Fresh=Next.Blackboard.GetOrCreate<FRaftSimLiquidGraphHistories>().ForOwner(100);
        Passed=!Fresh.Clock && !Fresh.Foam && Fresh.SecondarySteps==0;Next.Execute();
    });
    FlushRenderingCommands();
    if (!TestTrue(TEXT("Actual interleaved owner histories dispatched"),Passed)) { AddError(Error);return false; }
    if (!TestEqual(TEXT("Complete active owner readback"),OutA.Num(),768) ||
        !TestEqual(TEXT("Complete paused owner readback"),OutB.Num(),768) ||
        !TestEqual(TEXT("Complete reset owner readback"),OutC.Num(),768)) return false;
    TestTrue(TEXT("GPU diagnostics zero"),(Status[0]|Status[1]|Status[2]|Status[3])==0);
    float Expected=FFloat16(.8f).GetFloat();
    for (int32 I=0;I<2;++I) Expected=FFloat16(Expected*FMath::Exp(-.025f)).GetFloat();
    for (const auto& P:OutA) if (FMath::Abs(P.G.GetFloat()-Expected)>.0005f || P.B.GetFloat()!=10)
    { AddError(TEXT("Active owner lost same-graph history or metadata"));return false; }
    for (const auto& P:OutB) if (P.G.GetFloat()!=.25f || P.B.GetFloat()!=20)
    { AddError(TEXT("Paused owner contaminated by active owner"));return false; }
    for (const auto& P:OutC) if (P.G.GetFloat()!=0) { AddError(TEXT("Fresh attachment inherited foam"));return false; }
    return true;
}
