#include "Misc/AutomationTest.h"
#include "RaftSimDetailWaterGPU.h"
#include "RHICommandList.h"
#include "RHIGPUReadback.h"
#include "RenderingThread.h"
#include "HAL/PlatformProcess.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimMacroSurfaceGPUTest,
    "RaftSim.WaterDetail.MacroTriangleInterpolationGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)
bool FRaftSimMacroSurfaceGPUTest::RunTest(const FString&)
{
    if (GUsingNullRHI || GMaxRHIFeatureLevel<ERHIFeatureLevel::SM5)
    { AddError(TEXT("Real SM5+ GPU required"));return false; }
    const FIntPoint Size(4,3);TArray<FVector4f> Data,Queries,Actual;
    for (int32 Band=0;Band<4;++Band)for (int32 Y=0;Y<3;++Y)for (int32 X=0;X<4;++X)
        Data.Add(FVector4f(100*Band+X*Y+X*X,0.1f*X+Y*Y,0.01f*(Band+X*Y),0.2f*Y+0.1f*X));
    for (int32 Band=0;Band<4;++Band)
    {
        for (int32 Y=0;Y<2;++Y)for (int32 X=0;X<3;++X)
            for (float Offset:{0.0f,0.25f,0.5f,0.75f,1.0f})Queries.Add(FVector4f(X+Offset,Y+Offset,Band,0));
        Queries.Add(FVector4f(-0.3f,-0.2f,Band,0));Queries.Add(FVector4f(3.5f,2.6f,Band,0));
    }
    auto Readback=MakeShared<FRHIGPUBufferReadback,ESPMode::ThreadSafe>(TEXT("RaftSimMacroTriangleTest"));
    FTextureRHIRef Texture;bool bSampled=false;FString Error;
    ENQUEUE_RENDER_COMMAND(RaftSimMacroTriangleTest)([&](FRHICommandListImmediate& Cmd)
    {
        const auto Desc=FRHITextureCreateDesc::Create2D(TEXT("MacroAtlasTest"),4,12,PF_A32B32G32R32F)
            .SetFlags(ETextureCreateFlags::ShaderResource).SetInitialState(ERHIAccess::CopyDest);
        Texture=Cmd.CreateTexture(Desc);
        Cmd.UpdateTexture2D(Texture,0,FUpdateTextureRegion2D(0,0,0,0,4,12),4*sizeof(FVector4f),reinterpret_cast<const uint8*>(Data.GetData()));
        Cmd.Transition(FRHITransitionInfo(Texture,ERHIAccess::CopyDest,ERHIAccess::SRVMask));
        bSampled=RaftSimValidateMacroSamplingGPU(Cmd,Texture,Size,Queries,&Readback.Get(),Error);
    });
    FlushRenderingCommands();
    if (!TestTrue(TEXT("atlas upload and shared material sampling dispatch"),bSampled)) { AddError(Error);return false; }
    const double Deadline=FPlatformTime::Seconds()+10;
    while (!Readback->IsReady() && FPlatformTime::Seconds()<Deadline)FPlatformProcess::Sleep(0.01f);
    if (!Readback->IsReady()) { AddError(TEXT("Macro GPU readback timeout"));return false; }
    ENQUEUE_RENDER_COMMAND(RaftSimMacroTriangleRead)([&](FRHICommandListImmediate&)
    {
        const void* Ptr=Readback->Lock(Queries.Num()*sizeof(FVector4f));Actual.SetNumUninitialized(Queries.Num());
        FMemory::Memcpy(Actual.GetData(),Ptr,Actual.Num()*sizeof(FVector4f));Readback->Unlock();Texture.SafeRelease();
    });
    FlushRenderingCommands();
    float MaxError=0,BilinearDifference=0;bool bFinite=true;
    for (int32 I=0;I<Queries.Num();++I)
    {
        const auto Q=Queries[I];const float PX=FMath::Clamp(Q.X,0.0f,3.0f),PY=FMath::Clamp(Q.Y,0.0f,2.0f);
        const int32 X=FMath::Min(2,FMath::FloorToInt(PX)),Y=FMath::Min(1,FMath::FloorToInt(PY)),Base=int32(Q.Z)*12+Y*4+X;
        const float U=PX-X,V=PY-Y;const auto A=Data[Base],B=Data[Base+1],C=Data[Base+4],D=Data[Base+5];
        const FVector4f Expected=U+V<=1 ? A+(B-A)*U+(C-A)*V : D+(C-D)*(1-U)+(B-D)*(1-V);
        const FVector4f Bilinear=FMath::Lerp(FMath::Lerp(A,B,U),FMath::Lerp(C,D,U),V);
        for (int32 K=0;K<4;++K)
        {
            bFinite &= FMath::IsFinite(Actual[I][K]);MaxError=FMath::Max(MaxError,FMath::Abs(Actual[I][K]-Expected[K]));
            BilinearDifference=FMath::Max(BilinearDifference,FMath::Abs(Bilinear[K]-Expected[K]));
        }
    }
    TestTrue(TEXT("all atlas bands and triangle halves match independent barycentric values"),bFinite && MaxError<1.e-5f);
    TestTrue(TEXT("nonplanar fixture rejects substitution of bilinear height"),BilinearDifference>0.1f);
    AddInfo(FString::Printf(TEXT("Macro triangle GPU: %d queries, max RGBA error %.9g; bilinear alternative differs by %.9g"),Queries.Num(),MaxError,BilinearDifference));
    return true;
}
#endif
