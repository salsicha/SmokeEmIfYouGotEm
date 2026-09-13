#include "Misc/AutomationTest.h"
#if WITH_DEV_AUTOMATION_TESTS
// Global test shaders must register with this PostConfigInit module, before
// shader types initialize. The later-loading editor module only calls them.
#include "GlobalShader.h"
#include "RenderGraphUtils.h"
#include "ShaderParameterStruct.h"
#include "RenderingThread.h"
#include "RHIGPUReadback.h"
#include <cmath>

class FRaftSimPrescribedNormalTestCS:public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FRaftSimPrescribedNormalTestCS);
    SHADER_USE_PARAMETER_STRUCT(FRaftSimPrescribedNormalTestCS,FGlobalShader);
    BEGIN_SHADER_PARAMETER_STRUCT(FParameters,)
        SHADER_PARAMETER(uint32,Cases)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,Inputs)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,Results)
    END_SHADER_PARAMETER_STRUCT()
    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& P)
    { return IsFeatureLevelSupported(P.Platform,ERHIFeatureLevel::SM5); }
};
IMPLEMENT_GLOBAL_SHADER(FRaftSimPrescribedNormalTestCS,"/Plugin/RaftSimWaterDetail/Private/RaftSimLiquidPrescribedNormalTest.usf","MainCS",SF_Compute);

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLiquidPrescribedNormalTest,"RaftSim.Editor.LiquidPrescribedNormalGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FLiquidPrescribedNormalTest::RunTest(const FString&)
{
    if(GUsingNullRHI || GMaxRHIFeatureLevel<ERHIFeatureLevel::SM5)
    { AddError(TEXT("Actual GPU required for prescribed normal-position rounding"));return false; }
    TArray<FVector4f> Inputs;TArray<FVector3f> Expected;
    auto Add=[&](FVector3f Start,FVector3f Candidate,FVector3f Normal,float Travel)
    {
        const int32 Axis=FMath::Abs(Normal.X)>=FMath::Abs(Normal.Y)?0:1;
        const double Residual=FVector::DotProduct(FVector(Candidate)-FVector(Start),FVector(Normal))-Travel;
        FVector3f Corrected=Candidate;
        Corrected[Axis]=static_cast<float>(double(Candidate[Axis])-Residual/Normal[Axis]);
        if(FVector::DotProduct(FVector(Corrected)-FVector(Start),FVector(Normal))<Travel)
            Corrected[Axis]=std::nextafter(Corrected[Axis],Normal[Axis]>0?INFINITY:-INFINITY);
        Expected.Add(Corrected);
        Inputs.Append({FVector4f(Start,0),FVector4f(Candidate,0),FVector4f(Normal,0),FVector4f(Travel,0,0,0)});
    };
    const FVector3f CapturedNormal(.929999828338623f,.36755993962287903f,0);
    Add({-12066.3125f,-5790.435546875f,647.5684814453125f},
        {-12066.3134765625f,-5790.43408203125f,647.5401611328125f},CapturedNormal,0);
    // Both signs/quadrants, zero and nonzero prescribed flux, positions away
    // from and close to the world origin. Each candidate is already projected.
    for(FVector3f Normal:{CapturedNormal,-CapturedNormal,
        FVector3f(-CapturedNormal.Y,CapturedNormal.X,0),FVector3f(CapturedNormal.Y,-CapturedNormal.X,0)})
    for(float Scale:{-15000.f,-1.f,1.f,15000.f}) for(float Travel:{0.f,.001f,.05f,3.f})
    {
        FVector3f Start(Scale,Scale*.731f,650);
        FVector Tangent(-Normal.Y,Normal.X,0);
        FVector3f Candidate(FVector(Start)+Tangent*.037+FVector(Normal)*Travel/FVector(Normal).SizeSquared()+FVector(0,0,-.028));
        Add(Start,Candidate,Normal,Travel);
    }
    bool Passed=false;
    ENQUEUE_RENDER_COMMAND(RaftSimPrescribedNormalTest)([&](FRHICommandListImmediate& Cmd)
    {
        FRDGBuilder Graph(Cmd);
        auto In=CreateStructuredBuffer(Graph,TEXT("PrescribedNormal.Inputs"),TConstArrayView<FVector4f>(Inputs));
        auto Desc=FRDGBufferDesc::CreateStructuredDesc(16,Expected.Num());Desc.Usage|=BUF_SourceCopy;
        auto Out=Graph.CreateBuffer(Desc,TEXT("PrescribedNormal.Results"));
        auto* P=Graph.AllocParameters<FRaftSimPrescribedNormalTestCS::FParameters>();
        P->Cases=Expected.Num();P->Inputs=Graph.CreateSRV(In);P->Results=Graph.CreateUAV(Out);
        TShaderMapRef<FRaftSimPrescribedNormalTestCS> Shader(GetGlobalShaderMap(GMaxRHIFeatureLevel));
        FComputeShaderUtils::AddPass(Graph,RDG_EVENT_NAME("Prescribed Normal Position Test"),Shader,P,FIntVector(FMath::DivideAndRoundUp(Expected.Num(),64),1,1));
        TRefCountPtr<FRDGPooledBuffer> Result;Graph.QueueBufferExtraction(Out,&Result);
        Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle();
        FRHIGPUBufferReadback Read(TEXT("PrescribedNormal.Readback"));
        Cmd.Transition(FRHITransitionInfo(Result->GetRHI(),ERHIAccess::Unknown,ERHIAccess::CopySrc));
        Read.EnqueueCopy(Cmd,Result->GetRHI(),Expected.Num()*16);Cmd.SubmitAndBlockUntilGPUIdle();
        const auto* Data=static_cast<const FVector4f*>(Read.Lock(Expected.Num()*16));if(!Data) return;
        Passed=true;
        for(int32 I=0;I<Expected.Num();++I)
        {
            const FVector3f Actual(Data[I]);
            const bool Match=FMemory::Memcmp(&Actual,&Expected[I],12)==0;
            if(!Match) UE_LOG(LogTemp,Error,TEXT("Prescribed normal case%d expected%s got%s"),I,*Expected[I].ToString(),*Actual.ToString());
            Passed &= Match;
        }
        Read.Unlock();
    });
    FlushRenderingCommands();
    TestTrue(TEXT("Captured tangent drift and 64 signed/scale/flux cases round to independently computed inward-representable coordinates"),Passed);
    return Passed;
}
#endif
