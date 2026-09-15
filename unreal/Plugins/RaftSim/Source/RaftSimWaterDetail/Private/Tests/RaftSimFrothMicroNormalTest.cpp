#include "GlobalShader.h"
#include "ShaderParameterStruct.h"
#include "RenderGraphBuilder.h"
#include "RenderGraphUtils.h"
#include "RHIGPUReadback.h"
#include "RenderingThread.h"
#include "Misc/AutomationTest.h"
#include "HAL/PlatformProcess.h"

class FRaftSimFrothMicroNormalCS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FRaftSimFrothMicroNormalCS);
    SHADER_USE_PARAMETER_STRUCT(FRaftSimFrothMicroNormalCS,FGlobalShader);
    BEGIN_SHADER_PARAMETER_STRUCT(FParameters,)
        SHADER_PARAMETER(uint32,QueryCount)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,Queries)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,Contexts)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,Results)
    END_SHADER_PARAMETER_STRUCT()
    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& P)
    {return IsFeatureLevelSupported(P.Platform,ERHIFeatureLevel::SM5);}
};
IMPLEMENT_GLOBAL_SHADER(FRaftSimFrothMicroNormalCS,"/Plugin/RaftSimWaterDetail/Private/RaftSimFrothMicroNormalTest.usf","MainCS",SF_Compute);

#if WITH_AUTOMATION_TESTS
namespace
{
uint32 HashMicro(int32 X,int32 Y,uint32 Salt)
{uint32 H=uint32(X)*1597334677u^uint32(Y)*3812015801u^Salt;H^=H>>16;H*=2246822519u;H^=H>>13;return H;}
// Independent wider neighborhood and finite derivative of the HEIGHT, not a
// copy of the shader's analytic gradient. The shader supports only 3x3 cells.
double HeightReference(FVector2D P)
{
    const int32 X=FMath::FloorToInt(P.X),Y=FMath::FloorToInt(P.Y);double Sum=0;
    for(int32 J=-2;J<=2;++J)for(int32 I=-2;I<=2;++I)
    {
        const uint32 H=HashMicro(X+I,Y+J,0x6a09e667u);
        const FVector2D Centre(X+I+.28+.44*((H&65535u)+.5)/65536.,Y+J+.28+.44*((H>>16)+.5)/65536.);
        const double R=.38+.22*((HashMicro(X+I,Y+J,0xbb67ae85u)&65535u)+.5)/65536.;
        const double T=FMath::Max(1.-(P-Centre).SizeSquared()/(R*R),0.);Sum+=T*T*T;
    }
    return Sum;
}
FVector2D SlopeReference(FVector2f P)
{
    constexpr double E=1.e-5;const FVector2D V(P);
    return FVector2D((HeightReference(V+FVector2D(E,0))-HeightReference(V-FVector2D(E,0)))/(2*E),
        (HeightReference(V+FVector2D(0,E))-HeightReference(V-FVector2D(0,E)))/(2*E));
}
float MicroProduct(float A,float B){volatile float V=A*B;return V;}
float MicroSum(float A,float B){volatile float V=A+B;return V;}
double Fade(double X)
{double T=FMath::Clamp((X-.35)/.5,0.,1.);return 1.-T*T*(3.-2.*T);}
FVector2D PhaseReference(FVector2f P,float Footprint)
{
    const FVector2f Coarse(MicroProduct(P.X,8),MicroProduct(P.Y,8));
    const FVector2f Fine(MicroSum(MicroProduct(P.X,22),17.13f),MicroSum(MicroProduct(P.Y,22),9.37f));
    return SlopeReference(Coarse)*(.008*8*Fade(Footprint*8))+SlopeReference(Fine)*(.002*22*Fade(Footprint*22));
}
FVector3f NormalReference(FVector4f Q,FVector4f C)
{
    const FVector3f Base=FVector3f(.12f,-.09f,1.f).GetSafeNormal();
    if(C.Z<=0)return Base;
    const float A=Q.Z-FMath::FloorToFloat(Q.Z),B=(A+.5f)-FMath::FloorToFloat(A+.5f);
    const auto Back=[&](float T){return FVector2f(MicroSum(Q.X,-MicroProduct(C.X,T)),MicroSum(Q.Y,-MicroProduct(C.Y,T)));};
    const FVector2D S=FMath::Lerp(PhaseReference(Back(B),Q.W),PhaseReference(Back(A),Q.W),double(1-FMath::Abs(2*A-1)))*FMath::Clamp(double(C.Z),0.,1.);
    return FVector3f(Base.X/Base.Z-S.X,Base.Y/Base.Z-S.Y,1).GetSafeNormal();
}
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimFrothMicroNormalTest,"RaftSim.WaterDetail.FrothMicroNormalGPU",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimFrothMicroNormalTest::RunTest(const FString&)
{
    if(GUsingNullRHI || GMaxRHIFeatureLevel<ERHIFeatureLevel::SM5){AddError(TEXT("Real SM5 GPU required"));return false;}
    TArray<FVector4f> Queries,Contexts;
    for(int32 I=0;I<96;++I)for(float Coverage:{0.f,.1f,.5f,1.f})for(float Footprint:{0.f,.006f,.04f,.2f})
    {
        const float X=I<48 ? -3.175f+I*.113f : -5430.f+I*.017f;
        const float Y=I<48 ? 4.215f-I*.071f : 3600.f-I*.023f;
        Queries.Emplace(X,Y,(I%17)*.0625f,Footprint);Contexts.Emplace(1.3f,-.47f,Coverage,0);
    }
    auto Read=MakeShared<FRHIGPUBufferReadback,ESPMode::ThreadSafe>(TEXT("RaftSimFrothMicroNormal"));
    ENQUEUE_RENDER_COMMAND(RaftSimFrothMicroNormalTest)([&](FRHICommandListImmediate& Cmd)
    {
        FRDGBuilder Graph(Cmd);auto* P=Graph.AllocParameters<FRaftSimFrothMicroNormalCS::FParameters>();
        P->QueryCount=Queries.Num();P->Queries=Graph.CreateSRV(CreateStructuredBuffer(Graph,TEXT("MicroNormal.Queries"),Queries));
        P->Contexts=Graph.CreateSRV(CreateStructuredBuffer(Graph,TEXT("MicroNormal.Contexts"),Contexts));
        auto Output=Graph.CreateBuffer(FRDGBufferDesc::CreateStructuredDesc(sizeof(FVector4f),Queries.Num()*2),TEXT("MicroNormal.Output"));
        P->Results=Graph.CreateUAV(Output);TShaderMapRef<FRaftSimFrothMicroNormalCS> Shader(GetGlobalShaderMap(GMaxRHIFeatureLevel));
        FComputeShaderUtils::AddPass(Graph,RDG_EVENT_NAME("Froth micro-normal qualification"),Shader,P,FIntVector(FMath::DivideAndRoundUp(Queries.Num(),64),1,1));
        AddEnqueueCopyPass(Graph,&Read.Get(),Output,Queries.Num()*2*sizeof(FVector4f));Graph.Execute();
    });
    FlushRenderingCommands();const double Deadline=FPlatformTime::Seconds()+5;
    while(!Read->IsReady() && FPlatformTime::Seconds()<Deadline)FPlatformProcess::Sleep(.001f);
    if(!TestTrue(TEXT("GPU readback completes"),Read->IsReady()))return false;
    bool Valid=false;double GridError=0,PhaseError=0,NormalError=0,UnitError=0,DryError=0;
    ENQUEUE_RENDER_COMMAND(RaftSimFrothMicroNormalCompare)([&](FRHICommandListImmediate&)
    {
        const auto* Result=static_cast<const FVector4f*>(Read->Lock(Queries.Num()*2*sizeof(FVector4f)));
        if(!Result)return;Valid=true;
        for(int32 I=0;I<Queries.Num();++I)
        {
            const auto Q=Queries[I],C=Contexts[I],R=Result[2*I],S=Result[2*I+1];
            const FVector3f N(R.X,R.Y,R.Z);const auto Expected=NormalReference(Q,C);
            Valid&=!N.ContainsNaN() && N.Z>0 && FMath::IsFinite(S.X) && FMath::IsFinite(S.Y);
            UnitError=FMath::Max(UnitError,FMath::Abs(double(N.SizeSquared())-1));
            NormalError=FMath::Max(NormalError,double((N-Expected).Size()));
            if(C.Z==0)DryError=FMath::Max(DryError,double((N-Expected).Size()));
            const auto G=SlopeReference(FVector2f(Q.X,Q.Y)),P=PhaseReference(FVector2f(Q.X,Q.Y),Q.W);
            GridError=FMath::Max(GridError,(G-FVector2D(S.X,S.Y)).Size());
            PhaseError=FMath::Max(PhaseError,(P-FVector2D(S.Z,S.W)).Size());
        }
        Read->Unlock();
    });FlushRenderingCommands();
    TestTrue(TEXT("finite upward unit normals"),Valid && UnitError<2.e-6);
    TestTrue(TEXT("zero coverage preserves base normal"),DryError<2.e-7);
    TestTrue(TEXT("analytic 3x3 slope agrees with independent 5x5 height derivative"),GridError<.0003);
    TestTrue(TEXT("filtered phases and large coordinates agree"),PhaseError<.0003);
    TestTrue(TEXT("advected covered normals agree with independent reference"),NormalError<.0003);
    AddInfo(FString::Printf(TEXT("Froth micro-normal queries=%d grid_error=%.9g phase_error=%.9g normal_error=%.9g unit_error=%.9g dry_error=%.9g; optical only, not visual acceptance"),
        Queries.Num(),GridError,PhaseError,NormalError,UnitError,DryError));return !HasAnyErrors();
}
#endif
