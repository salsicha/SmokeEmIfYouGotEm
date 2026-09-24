#include "Misc/AutomationTest.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/FileHelper.h"
#include "GlobalShader.h"
#include "ShaderParameterStruct.h"
#include "RenderGraphUtils.h"
#include "RenderingThread.h"
#include "RHIGPUReadback.h"

#if WITH_DEV_AUTOMATION_TESTS && WITH_UNREAL_DEVELOPER_TOOLS
class FRaftSimRepresentedFloatTestCS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FRaftSimRepresentedFloatTestCS);
    SHADER_USE_PARAMETER_STRUCT(FRaftSimRepresentedFloatTestCS,FGlobalShader);
    class FPortable : SHADER_PERMUTATION_BOOL("RAFTSIM_ARITHMETIC_PORTABLE");
    using FPermutationDomain=TShaderPermutationDomain<FPortable>;
    BEGIN_SHADER_PARAMETER_STRUCT(FParameters,)
        SHADER_PARAMETER(uint32,Count)
        SHADER_PARAMETER(uint32,RK2)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,Input)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint4>,Output)
    END_SHADER_PARAMETER_STRUCT()
    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& P)
    {return IsFeatureLevelSupported(P.Platform,ERHIFeatureLevel::SM5) &&
        (FPermutationDomain(P.PermutationId).Get<FPortable>() ||
         (IsD3DPlatform(P.Platform) && IsFeatureLevelSupported(P.Platform,ERHIFeatureLevel::SM6)));}
};
IMPLEMENT_GLOBAL_SHADER(FRaftSimRepresentedFloatTestCS,"/Plugin/RaftSimWaterDetail/Private/RaftSimRepresentedFloatTest.usf","MainCS",SF_Compute);

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRepresentedFloatTest,"RaftSim.WaterDetail.RepresentedFloatArithmeticGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRepresentedFloatTest::RunTest(const FString&)
{
    FString Path;TArray<uint8> Bytes;
    if(GUsingNullRHI || GMaxRHIFeatureLevel<ERHIFeatureLevel::SM5 ||
        !FParse::Value(FCommandLine::Get(),TEXT("RaftSimRepresentedFloatFixture="),Path) ||
        !FFileHelper::LoadFileToArray(Bytes,*Path) || Bytes.Num()<12)
    {AddError(TEXT("Actual GPU and represented-float fixture required"));return false;}
    uint32 Header[3];FMemory::Memcpy(Header,Bytes.GetData(),12);
    const uint32 Operation=Header[1]-1;const bool bFace=Operation==4 || Operation==8;
    const uint32 Stride=bFace?96:Operation==0?16:20;
    const uint32 InputVectors=bFace?4:1,ExpectedComponents=bFace?8:1,OutputComponents=bFace?8:4;
    if(Header[0]!=0x52534650 || Header[1]<1 || Header[1]>11 || Header[2]<32 || Header[2]>65536 || Bytes.Num()!=12+Stride*Header[2])
    {AddError(TEXT("Invalid bounded arithmetic fixture"));return false;}
    TArray<FVector4f> Input;Input.SetNumUninitialized(Header[2]*InputVectors);TArray<uint32> ExpectedBits;ExpectedBits.SetNumUninitialized(Header[2]*ExpectedComponents);
    for(uint32 I=0;I<Header[2];++I)
    {FMemory::Memcpy(&Input[I*InputVectors],Bytes.GetData()+12+Stride*I,16*InputVectors);FMemory::Memcpy(&ExpectedBits[I*ExpectedComponents],Bytes.GetData()+12+Stride*I+Stride-4*ExpectedComponents,4*ExpectedComponents);}
    const bool bDoubleRequested=FParse::Param(FCommandLine::Get(),TEXT("RaftSimDoubleArithmeticControl"));
    if(bDoubleRequested && (Operation!=0 || !IsD3DPlatform(GMaxRHIShaderPlatform) || GMaxRHIFeatureLevel<ERHIFeatureLevel::SM6))
    {AddError(TEXT("FP64 control requires Euler fixtures and a capable D3D SM6 device; portable arithmetic does not"));return false;}
    uint32 WrongEuler=0,WrongRoundtrip=0,WrongLegacyAdd=0,OrdinaryDifferences=0,CompletedBackends=0;TArray<FString> Details;
    ENQUEUE_RENDER_COMMAND(RepresentedFloatArithmetic)([&](FRHICommandListImmediate& Cmd)
    {
        const bool bDoubleControl=bDoubleRequested;
        for(int32 Backend=0;Backend<(bDoubleControl?2:1);++Backend)
        {
        const bool bPortable=Backend==0;
        FRDGBuilder Graph(Cmd);auto In=CreateStructuredBuffer(Graph,TEXT("RepresentedFloat.Input"),Input);
        auto Desc=FRDGBufferDesc::CreateStructuredDesc(16,Header[2]*OutputComponents/4);Desc.Usage|=BUF_SourceCopy;
        auto Out=Graph.CreateBuffer(Desc,TEXT("RepresentedFloat.Output"));
        auto* P=Graph.AllocParameters<FRaftSimRepresentedFloatTestCS::FParameters>();
        P->Count=Header[2];P->RK2=Operation;P->Input=Graph.CreateSRV(In);P->Output=Graph.CreateUAV(Out);
        FRaftSimRepresentedFloatTestCS::FPermutationDomain Perm;Perm.Set<FRaftSimRepresentedFloatTestCS::FPortable>(bPortable);
        TShaderMapRef<FRaftSimRepresentedFloatTestCS> Shader(GetGlobalShaderMap(GMaxRHIFeatureLevel),Perm);ClearUnusedGraphResources(Shader,P);
        FComputeShaderUtils::AddPass(Graph,RDG_EVENT_NAME("RaftSim Represented Float Test"),Shader,P,FIntVector(FMath::DivideAndRoundUp(Header[2],256u),1,1));
        FRHIGPUBufferReadback Read(TEXT("RepresentedFloat.Read"));AddEnqueueCopyPass(Graph,&Read,Out,4*OutputComponents*Header[2]);
        Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle();const auto* Values=static_cast<const uint32*>(Read.Lock(4*OutputComponents*Header[2]));
        if(!Values)return;++CompletedBackends;
        for(uint32 I=0;I<Header[2];++I)
        {
            if(bFace)
            {
                for(uint32 K=0;K<8;++K)
                {
                    const uint32 E=ExpectedBits[8*I+K],V=Values[8*I+K];WrongEuler+=E!=V;
                    if(E!=V && Details.Num()<16)Details.Add(FString::Printf(TEXT("exact face case%u component%u expected%08x actual%08x"),I,K,E,V));
                }
                continue;
            }
            uint32 Expected=ExpectedBits[I],Initial;FMemory::Memcpy(&Initial,&Input[I].X,4);
            bool Wrong=Values[4*I]!=Expected;
            WrongEuler+=Wrong;WrongRoundtrip+=Values[4*I+1]!=Initial;if(Operation==0)OrdinaryDifferences+=Values[4*I+2]!=Expected;
            if(Operation==9)WrongLegacyAdd+=Values[4*I+2]!=Expected;
            if((Wrong || I<2) && Details.Num()<16)
                Details.Add(FString::Printf(TEXT("%s case%d expected%08x represented%08x"),bPortable?TEXT("integer"):TEXT("double"),I,Expected,Values[4*I]));
        }
        Read.Unlock();
        }
    });
    FlushRenderingCommands();TestEqual(TEXT("Read every requested arithmetic backend"),CompletedBackends,bDoubleRequested?2u:1u);
    TestEqual(TEXT("Exact rational arithmetic / admissibility reference"),WrongEuler,0u);
    TestEqual(TEXT("Transported input / double roundtrip bits exact"),WrongRoundtrip,0u);
    TestEqual(TEXT("Original wide-accumulator addition also matches the rational oracle"),WrongLegacyAdd,0u);
    AddInfo(FString::Printf(TEXT("%u cases operation%u; combined errors%u, input/roundtrip errors%u, ordinary differences%u; portable backend always tested; not full solver qualification"),Header[2],Operation,WrongEuler,WrongRoundtrip,OrdinaryDifferences));
    for(const auto& Detail:Details)AddInfo(Detail);
    return !HasAnyErrors();
}
#endif
