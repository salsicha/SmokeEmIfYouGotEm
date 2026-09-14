#include "GlobalShader.h"
#include "ShaderParameterStruct.h"
#include "RenderGraphBuilder.h"
#include "RenderGraphUtils.h"
#include "RHIGPUReadback.h"
#include "RenderingThread.h"
#include "Misc/AutomationTest.h"
#include "HAL/PlatformProcess.h"

class FRaftSimIrregularFrothCS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FRaftSimIrregularFrothCS);
    SHADER_USE_PARAMETER_STRUCT(FRaftSimIrregularFrothCS,FGlobalShader);
    BEGIN_SHADER_PARAMETER_STRUCT(FParameters,)
        SHADER_PARAMETER(uint32,QueryCount)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,Queries)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,Contexts)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,Results)
    END_SHADER_PARAMETER_STRUCT()
    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& P)
    {return IsFeatureLevelSupported(P.Platform,ERHIFeatureLevel::SM5);}
};
IMPLEMENT_GLOBAL_SHADER(FRaftSimIrregularFrothCS,"/Plugin/RaftSimWaterDetail/Private/RaftSimIrregularFrothTest.usf","MainCS",SF_Compute);

#if WITH_AUTOMATION_TESTS
namespace
{
uint32 HashCell(int32 X,int32 Y,uint32 Salt)
{uint32 H=uint32(X)*1597334677u^uint32(Y)*3812015801u^Salt;H^=H>>16;H*=2246822519u;H^=H>>13;return H;}
double Smooth(double A,double B,double X)
{const double T=FMath::Clamp((X-A)/(B-A),0.,1.);return T*T*(3.-2.*T);}
double GridReference(FVector2f Position,double P,double Footprint)
{
    if(P<=0)return 0;if(P>=1)return 1;if(Footprint>=.75)return P;
    const int32 X=FMath::FloorToInt(Position.X),Y=FMath::FloorToInt(Position.Y);
    // Independent wider 5x5 neighborhood and double-distance reference verify
    // the shader's bounded 3x3 support, including translated cell boundaries.
    double D[25],O[25],Minimum=100.;int32 I=0;
    for(int32 J=-2;J<=2;++J)for(int32 K=-2;K<=2;++K,++I)
    {
        const uint32 H=HashCell(X+K,Y+J,0x6a09e667u);
        const double DX=K+.3+.4*((H&65535u)+.5)/65536.-(double(Position.X)-X);
        const double DY=J+.3+.4*((H>>16)+.5)/65536.-(double(Position.Y)-Y);
        D[I]=DX*DX+DY*DY;Minimum=FMath::Min(Minimum,D[I]);
        const double R=((HashCell(X+K,Y+J,0)&65535u)+.5)/65536.;
        const double Band=FMath::Min(.025,FMath::Min(P,1.-P));O[I]=1.-Smooth(P-Band,P+Band,R);
    }
    const double Border=FMath::Min(.25,FMath::Max(.025,.5*FMath::Max(Footprint,0.)));
    const double Span=2.*FMath::Sqrt(Minimum)*Border+Border*Border;
    double Total=0,Weights=0;
    for(I=0;I<25;++I){const double W=1.-Smooth(0,Span,D[I]-Minimum);Total+=W*O[I];Weights+=W;}
    return FMath::Lerp(Total/Weights,P,Smooth(.35,.75,Footprint));
}
// The shader declares these coordinate stages precise. Force independently
// represented float stages here too, rather than allowing /fp:fast to fuse
// the CPU reference's multiplication with the following addition/subtraction.
float RoundedProduct(float A,float B){volatile float V=A*B;return V;}
float RoundedSum(float A,float B){volatile float V=A+B;return V;}
FVector2f Backtrace(FVector2f P,FVector2f V,float Time)
{return FVector2f(RoundedSum(P.X,-RoundedProduct(V.X,Time)),RoundedSum(P.Y,-RoundedProduct(V.Y,Time)));}
FVector4f CoordinatesReference(FVector2f V)
{
    const float X=RoundedSum(RoundedProduct(.7986355f,V.X),RoundedProduct(.601815f,V.Y));
    const float Y=RoundedSum(RoundedProduct(-.601815f,V.X),RoundedProduct(.7986355f,V.Y));
    return FVector4f(RoundedProduct(V.X,4.5f),RoundedProduct(V.Y,4.5f),
        RoundedSum(RoundedProduct(X,17.f),17.13f),RoundedSum(RoundedProduct(Y,17.f),9.37f));
}
double PhaseReference(FVector2f V,double P,float Footprint)
{
    const FVector4f C=CoordinatesReference(V);
    return .7*GridReference(FVector2f(C.X,C.Y),P,Footprint*4.5f)+
        .3*GridReference(FVector2f(C.Z,C.W),P,Footprint*17.f);
}
double SampleReference(FVector4f Q,FVector4f C)
{
    const double P=1.-FMath::Exp(-double(FMath::Max(Q.X,0.f))*FMath::Max(Q.Y,0.f));
    const float A=C.Z-FMath::FloorToFloat(C.Z),B=A+.5f-FMath::FloorToFloat(A+.5f),W=1.f-FMath::Abs(2.f*A-1.f);
    const FVector2f World(Q.Z,Q.W),Velocity(C.X,C.Y);
    return FMath::Lerp(PhaseReference(Backtrace(World,Velocity,B),P,C.W),PhaseReference(Backtrace(World,Velocity,A),P,C.W),double(W));
}
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimIrregularFrothTest,"RaftSim.WaterDetail.IrregularFrothGPU",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimIrregularFrothTest::RunTest(const FString&)
{
    if(GUsingNullRHI || GMaxRHIFeatureLevel<ERHIFeatureLevel::SM5){AddError(TEXT("Real SM5 GPU required"));return false;}
    TArray<FVector4f> Queries,Contexts;
    const auto Add=[&](FVector4f Q,FVector4f C){Queries.Add(Q);Contexts.Add(C);};
    for(float Amount:{-1.f,0.f,.001f,.1f,1.f,5.f,10.f})for(float Density:{-1.f,0.f,3.f})
        for(float Time:{-.00001f,0.f,.00001f,.49999f,.5f,.50001f,.99999f,1.f,1.00001f})
            for(float Footprint:{0.f,.003f,.03f,.15f,.8f})
                Add(FVector4f(Amount,Density,-5.237f,7.419f),FVector4f(1.2f,.4f,Time,Footprint));
    const int32 MeanStart=Queries.Num();
    constexpr int32 PerMean=16384;constexpr float Probabilities[]={.02f,.12f,.5f,.88f,.98f};
    for(float P:Probabilities)for(int32 Y=0;Y<128;++Y)for(int32 X=0;X<128;++X)
        Add(FVector4f(-FMath::Loge(1.f-P)/3.f,3.f,X*2.31f-.7f,Y*2.19f-.9f),
            FVector4f(1.2f,.4f,.73f,((X+Y)%5)*.015f));
    const int32 LargeStart=Queries.Num();
    for(int32 I=0;I<512;++I)
        Add(FVector4f(.23f,3.f,-5450.f+I*.013f,3566.f+I*.021f),FVector4f(3.1f,-1.2f,.27f,.006f));
    auto Read=MakeShared<FRHIGPUBufferReadback,ESPMode::ThreadSafe>(TEXT("RaftSimIrregularFroth"));
    ENQUEUE_RENDER_COMMAND(RaftSimIrregularFrothTest)([&](FRHICommandListImmediate& Cmd)
    {
        FRDGBuilder Graph(Cmd);auto* P=Graph.AllocParameters<FRaftSimIrregularFrothCS::FParameters>();
        P->QueryCount=Queries.Num();P->Queries=Graph.CreateSRV(CreateStructuredBuffer(Graph,TEXT("IrregularFroth.Queries"),Queries));
        P->Contexts=Graph.CreateSRV(CreateStructuredBuffer(Graph,TEXT("IrregularFroth.Contexts"),Contexts));
        auto Output=Graph.CreateBuffer(FRDGBufferDesc::CreateStructuredDesc(sizeof(FVector4f),Queries.Num()*2),TEXT("IrregularFroth.Output"));
        P->Results=Graph.CreateUAV(Output);TShaderMapRef<FRaftSimIrregularFrothCS> Shader(GetGlobalShaderMap(GMaxRHIFeatureLevel));
        FComputeShaderUtils::AddPass(Graph,RDG_EVENT_NAME("Irregular froth qualification"),Shader,P,
            FIntVector(FMath::DivideAndRoundUp(Queries.Num(),64),1,1));
        AddEnqueueCopyPass(Graph,&Read.Get(),Output,Queries.Num()*2*sizeof(FVector4f));Graph.Execute();
    });
    FlushRenderingCommands();const double Deadline=FPlatformTime::Seconds()+5;
    while(!Read->IsReady() && FPlatformTime::Seconds()<Deadline)FPlatformProcess::Sleep(.001f);
    if(!TestTrue(TEXT("GPU readback completes"),Read->IsReady()))return false;
    bool Valid=false,Monotone=true;double GridError=0,SampleError=0,LargeError=0,CoordinateError=0,TemporalDelta=0,Means[5]={};
    float Lowest=1,Highest=0;int32 InvalidCount=0,WorstCoordinate=INDEX_NONE;FVector4f WorstGPU(0,0,0,0),WorstCPU(0,0,0,0);
    ENQUEUE_RENDER_COMMAND(RaftSimIrregularFrothCompare)([&](FRHICommandListImmediate&)
    {
        const auto* Results=static_cast<const FVector4f*>(Read->Lock(Queries.Num()*2*sizeof(FVector4f)));
        if(!Results)return;Valid=true;
        for(int32 I=0;I<Queries.Num();++I)
        {
            const auto Q=Queries[I],C=Contexts[I];
            const auto R=Results[I*2];
            for(int32 J=0;J<4;++J)
            {
                const bool InRange=FMath::IsFinite(R[J]) && R[J]>=0 && R[J]<=1;
                Valid&=InRange;InvalidCount+=!InRange;Lowest=FMath::Min(Lowest,R[J]);Highest=FMath::Max(Highest,R[J]);
            }
            Monotone&=R.W+1.e-6f>=R.X;
            if(Q.X<=0 || Q.Y<=0)Valid&=R.X==0 && R.Y==0;
            const float Phase=C.Z-FMath::FloorToFloat(C.Z);
            const auto Coordinate=CoordinatesReference(Backtrace(FVector2f(Q.Z,Q.W),FVector2f(C.X,C.Y),Phase));
            for(int32 J=0;J<4;++J)
            {
                const double Error=FMath::Abs(Coordinate[J]-Results[I*2+1][J]);
                if(Error>CoordinateError){CoordinateError=Error;WorstCoordinate=I;WorstCPU=Coordinate;WorstGPU=Results[I*2+1];}
            }
            const double P=1.-FMath::Exp(-double(FMath::Max(Q.X,0.f))*FMath::Max(Q.Y,0.f));
            if(I<MeanStart || I>=LargeStart || (I-MeanStart)%47==0)
            {
                const double GE=FMath::Abs(R.Y-GridReference(FVector2f(Q.Z,Q.W),P,C.W));
                GridError=FMath::Max(GridError,GE);
                const double SE=FMath::Abs(R.X-SampleReference(Q,C));
                if(I>=LargeStart)LargeError=FMath::Max(LargeError,SE);else SampleError=FMath::Max(SampleError,SE);
            }
            if(I<MeanStart)TemporalDelta=FMath::Max(TemporalDelta,double(FMath::Abs(R.Z-R.X)));
            if(I>=MeanStart && I<LargeStart)Means[(I-MeanStart)/PerMean]+=R.X/PerMean;
        }
        Read->Unlock();
    });
    FlushRenderingCommands();
    TestTrue(TEXT("finite bounded occupancy, zero source remains zero"),Valid);
    TestTrue(TEXT("adding density never reduces optical occupancy"),Monotone);
    TestTrue(TEXT("GPU transforms match independently rounded coordinate stages exactly"),CoordinateError==0.);
    TestTrue(TEXT("bounded 3x3 agrees with independent 5x5 grid"),GridError<.0003);
    TestTrue(TEXT("advected material agrees with CPU reference"),SampleError<.0003);
    TestTrue(TEXT("large world-coordinate material agrees with CPU reference"),LargeError<.0003);
    TestTrue(TEXT("committed phase wraps without a discontinuity"),TemporalDelta<.01);
    for(int32 I=0;I<5;++I)
    {
        TestTrue(TEXT("finite spatial coverage within existing .008 statistical tolerance"),FMath::Abs(Means[I]-Probabilities[I])<.008);
        AddInfo(FString::Printf(TEXT("Irregular froth mean target=%.6f measured=%.9f points=%d"),Probabilities[I],Means[I],PerMean));
    }
    AddInfo(FString::Printf(TEXT("Irregular froth range=[%.12g,%.12g] invalid=%d coordinate_error=%.12g worst_query=%d cpu=%s gpu=%s"),
        Lowest,Highest,InvalidCount,CoordinateError,WorstCoordinate,*WorstCPU.ToString(),*WorstGPU.ToString()));
    AddInfo(FString::Printf(TEXT("Irregular froth queries=%d grid_error=%.9g material_error=%.9g world_error=%.9g wrap_delta=%.9g; optical tests, not mass/visual/FPS acceptance"),
        Queries.Num(),GridError,SampleError,LargeError,TemporalDelta));return !HasAnyErrors();
}
#endif
