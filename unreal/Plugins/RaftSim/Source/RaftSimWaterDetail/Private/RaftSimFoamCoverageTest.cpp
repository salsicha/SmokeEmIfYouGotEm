#include "GlobalShader.h"
#include "ShaderParameterStruct.h"
#include "RenderGraphBuilder.h"
#include "RenderGraphUtils.h"
#include "RHIGPUReadback.h"
#include "RenderingThread.h"
#include "Misc/AutomationTest.h"
#include "HAL/PlatformProcess.h"

class FRaftSimFoamCoverageCS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FRaftSimFoamCoverageCS);
    SHADER_USE_PARAMETER_STRUCT(FRaftSimFoamCoverageCS,FGlobalShader);
    BEGIN_SHADER_PARAMETER_STRUCT(FParameters,)
        SHADER_PARAMETER(uint32,QueryCount)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,Queries)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,Results)
    END_SHADER_PARAMETER_STRUCT()
    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& P)
    { return IsFeatureLevelSupported(P.Platform,ERHIFeatureLevel::SM5); }
};
IMPLEMENT_GLOBAL_SHADER(FRaftSimFoamCoverageCS,"/Plugin/RaftSimWaterDetail/Private/RaftSimFoamCoverageTest.usf","MainCS",SF_Compute);

#if WITH_AUTOMATION_TESTS
namespace
{
float TransitionReference(float F,float Footprint)
{
    const auto Integral=[](float T)
    { return T<=0 ? 0.f : T>=1 ? T-.5f : T*T*T*(1-.5f*T); };
    if(Footprint<=.0001f)return FMath::SmoothStep(.4f,.6f,F);
    return FMath::Clamp(.2f*(Integral((F+.5f*Footprint-.4f)/.2f)-
        Integral((F-.5f*Footprint-.4f)/.2f))/Footprint,0.f,1.f);
}
float CellGridReference(FVector2f Position,float P,float Footprint)
{
    const int32 X=FMath::FloorToInt(Position.X),Y=FMath::FloorToInt(Position.Y);
    auto Occupied=[P](int32 A,int32 B)
    {
        uint32 H=uint32(A)*1597334677u^uint32(B)*3812015801u;
        H^=H>>16;H*=2246822519u;H^=H>>13;
        const float R=(float(H&65535u)+.5f)/65536.f;
        const float Band=FMath::Min(.025f,FMath::Min(P,1.f-P));
        const float T=FMath::Clamp((R-(P-Band))/(2*Band),0.f,1.f);
        return 1.f-T*T*(3.f-2.f*T);
    };
    const float FX=TransitionReference(Position.X-X,Footprint),FY=TransitionReference(Position.Y-Y,Footprint);
    const float Value=FMath::Lerp(FMath::Lerp(Occupied(X,Y),Occupied(X+1,Y),FX),
        FMath::Lerp(Occupied(X,Y+1),Occupied(X+1,Y+1),FX),FY);
    return FMath::Lerp(Value,P,FMath::SmoothStep(.5f,1.25f,Footprint));
}
float CellReference(FVector2f Position,float P,float Footprint)
{
    if (P<=0)return 0;if (P>=1)return 1;
    auto Phase=[P,Footprint](FVector2f V)
    {
        const FVector2f Fine(.7986355f*V.X+.601815f*V.Y,-.601815f*V.X+.7986355f*V.Y);
        return .7f*CellGridReference(V*1.7f,P,Footprint*1.7f)+
            .3f*CellGridReference(Fine*6.5f+FVector2f(17.13f,9.37f),P,Footprint*6.5f);
    };
    return FMath::Lerp(Phase(Position-FVector2f(1.2f,.4f)*.23f),
        Phase(Position-FVector2f(1.2f,.4f)*.73f),.54f);
}
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimFoamCoverageTest,"RaftSim.WaterDetail.FoamCoverageOpticsGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimFoamCoverageTest::RunTest(const FString&)
{
    double IntegralError=0;
    for(float Footprint:{.03f,.1f,.5f,2.f})for(int32 J=0;J<=20;++J)
    {
        const float F=J*.05f;double Mean=0;
        for(int32 K=0;K<4096;++K)
        {
            const double X=F+Footprint*((K+.5)/4096.-.5);
            const double T=FMath::Clamp((X-.4)/.2,0.,1.);
            Mean+=T*T*(3.-2.*T)/4096.;
        }
        IntegralError=FMath::Max(IntegralError,FMath::Abs(Mean-TransitionReference(F,Footprint)));
    }
    TestTrue(TEXT("pixel-filtered transition matches independent quadrature"),IntegralError<1.e-5);
    TestEqual(TEXT("resolved foam border has no whole-cell grey ramp"),TransitionReference(.35f,0),0.f);
    TestEqual(TEXT("resolved foam interior reaches full occupancy"),TransitionReference(.65f,0),1.f);
    if (GUsingNullRHI || GMaxRHIFeatureLevel<ERHIFeatureLevel::SM5)
    { AddError(TEXT("Real SM5 GPU required"));return false; }
    TArray<FVector4f> Queries;
    for (float Amount:{0.f,.001f,.1f,1.f,5.f,10.f})for (float Density:{0.f,3.f})
        for (float A:{0.f,.1552058425604128f,.5f,1.f})for (float B:{0.f,.1552058425604128f,.5f,1.f})
            Queries.Add(FVector4f(Amount,Density,A,B));
    const int32 MeanStart=Queries.Num();
    for (int32 Y=0;Y<128;++Y)for (int32 X=0;X<128;++X)
        Queries.Add(FVector4f(-FMath::Loge(.88f)/3.f,3.f,X*2.31f-.7f,Y*2.19f-.9f));
    auto Read=MakeShared<FRHIGPUBufferReadback,ESPMode::ThreadSafe>(TEXT("RaftSimFoamCoverageParity"));
    ENQUEUE_RENDER_COMMAND(RaftSimFoamCoverageTest)([&](FRHICommandListImmediate& Cmd)
    {
        FRDGBuilder Graph(Cmd);auto* P=Graph.AllocParameters<FRaftSimFoamCoverageCS::FParameters>();
        P->QueryCount=Queries.Num();
        P->Queries=Graph.CreateSRV(CreateStructuredBuffer(Graph,TEXT("FoamOptics.Queries"),Queries));
        auto Results=Graph.CreateBuffer(FRDGBufferDesc::CreateStructuredDesc(sizeof(FVector4f),Queries.Num()),TEXT("FoamOptics.Results"));
        P->Results=Graph.CreateUAV(Results);
        TShaderMapRef<FRaftSimFoamCoverageCS> Shader(GetGlobalShaderMap(GMaxRHIFeatureLevel));
        FComputeShaderUtils::AddPass(Graph,RDG_EVENT_NAME("Foam Coverage Optics Test"),Shader,P,
            FIntVector(FMath::DivideAndRoundUp(Queries.Num(),64),1,1));
        AddEnqueueCopyPass(Graph,&Read.Get(),Results,Queries.Num()*sizeof(FVector4f));Graph.Execute();
    });
    FlushRenderingCommands();
    const double Deadline=FPlatformTime::Seconds()+5;
    while (!Read->IsReady() && FPlatformTime::Seconds()<Deadline)FPlatformProcess::Sleep(.001f);
    if (!TestTrue(TEXT("GPU optics readback completes"),Read->IsReady()))return false;
    bool Valid=false;double Error=0,MeanError=0,CellError=0,CellMean=0;
    ENQUEUE_RENDER_COMMAND(RaftSimFoamCoverageCompare)([&](FRHICommandListImmediate&)
    {
        const auto* Results=static_cast<const FVector4f*>(Read->Lock(Queries.Num()*sizeof(FVector4f)));
        if (!Results)return;Valid=true;
        constexpr double Mean=.1552058425604128;
        for (int32 I=0;I<Queries.Num();++I)
        {
            const auto Q=Queries[I];const double Coverage=1.-FMath::Exp(-double(Q.X)*Q.Y);
            const double Contrast=FMath::Min(Coverage/Mean,(1.-Coverage)/(1.-Mean));
            for (int32 C=0;C<3;++C)
            {
                const double Lace=FMath::Lerp(FMath::Clamp(double(Q.W),0.,1.),FMath::Clamp(double(Q.Z),0.,1.),C*.5);
                const double Expected=Coverage+Contrast*(Lace-Mean);
                Valid &= FMath::IsFinite(Results[I][C]) && Results[I][C]>=0 && Results[I][C]<=1;
                Error=FMath::Max(Error,FMath::Abs(Expected-Results[I][C]));
            }
            // Extremal Bernoulli lace with P(L=1)=Mean has exactly this mean.
            // End phases must preserve its expected coverage, even for density>1.
            if (Q.Z==0.f && Q.W==1.f)
                MeanError=FMath::Max(MeanError,FMath::Abs(Mean*Results[I].X+(1.-Mean)*Results[I].Z-Coverage));
            Valid &= FMath::IsFinite(Results[I].W) && Results[I].W>=0 && Results[I].W<=1;
            const float ExpectedCell=CellReference(FVector2f(Q.Z,Q.W),float(Coverage),(I%5)*.03f);
            CellError=FMath::Max(CellError,double(FMath::Abs(Results[I].W-ExpectedCell)));
            if (I>=MeanStart)CellMean+=Results[I].W/(Queries.Num()-MeanStart);
        }
        Read->Unlock();
    });
    FlushRenderingCommands();
    TestTrue(TEXT("same material helper is bounded and matches independent double reference"),Valid && Error<1.e-6);
    TestTrue(TEXT("phase endpoints preserve expected optical coverage"),MeanError<1.e-6);
    TestTrue(TEXT("advected clump shader matches independent CPU reference"),CellError<.0003);
    TestTrue(TEXT("finite spatial clump sample retains expected 12 percent coverage"),FMath::Abs(CellMean-.12)<.008);
    AddInfo(FString::Printf(TEXT("%d GPU optical queries, maximum reference error %.9g, expected coverage error %.9g; not liquid mass or visual acceptance"),Queries.Num(),Error,MeanError));
    AddInfo(FString::Printf(TEXT("Advected clumps: GPU/CPU error %.9g, 16384-point sampled coverage %.9g (target .12); finite statistical sample, not exact local-area conservation"),CellError,CellMean));
    AddInfo(FString::Printf(TEXT("Narrowed edge analytic pixel filter: maximum independent quadrature error %.9g; GPU queries use five pixel footprints"),IntegralError));
    return !HasAnyErrors();
}
#endif
