#include "Misc/AutomationTest.h"
#include "RaftSimPressureResidualGPU.h"
#include "RenderGraphUtils.h"
#include "RenderingThread.h"
#include "RHIGPUReadback.h"
#include <limits>

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FPressureResidualTest,"RaftSim.WaterDetail.PressureResidualQualificationGPU",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FPressureResidualTest::RunTest(const FString&)
{
    if(GUsingNullRHI){AddError(TEXT("Actual GPU required"));return false;}
    bool Passed=true;TArray<FString> Records;FString Error;
    ENQUEUE_RENDER_COMMAND(PressureResidualQualification)([&](FRHICommandListImmediate& Cmd)
    {
        for(int32 Case=0;Case<17;++Case)
        {
            const float Scale=Case==0?1.f:Case==1?1e-30f:Case==2?1e30f:Case==3?1e-40f:1.f;
            TArray<FVector4f> B,R;B.Init(FVector4f(Scale,-Scale,Scale,Scale),257);
            R.Init(FVector4f(Scale*1e-5f,-Scale*1e-5f,Scale*1e-4f,Scale*1e-4f),257);
            uint32 Expected=2;bool Bad=false;
            if(Case==3){B.Init(FVector4f(Scale,Scale,Scale,Scale),257);R.Init(FVector4f(0,0,Scale,Scale),257);}
            if(Case==4){B.Init(FVector4f(0,0,0,0),257);R.Init(FVector4f(0,0,0,0),257);Expected=0;}
            if(Case==5){B.Init(FVector4f(0,0,0,0),257);R.Init(FVector4f(1e-40f,0,0,0),257);Expected=1;}
            if(Case==6){R[256].X=std::numeric_limits<float>::quiet_NaN();Bad=true;}
            if(Case==7){B[256].X=std::numeric_limits<float>::infinity();Bad=true;}
            TArray<FVector2f> Geometry;Geometry.Init(FVector2f(1,0),257);
            if(Case>=8)
            {
                B.Init(FVector4f(1,1,1,1),257);R.Init(FVector4f(0,0,0,0),257);Expected=0;
                if(Case==8 || Case==9)
                {B[0]=FVector4f(1e20f,1e20f,1e20f,1e20f);Geometry[0].X=1.401298464324817e-45f;
                    R[256].X=Case==8?.001f:.0001f;Expected=Case==8?4u:0u;}
                if(Case==10 || Case==11)
                {const float S=Case==10?1e-30f:1e30f;B.Init(FVector4f(S,S,S,S),257);
                    R.Init(FVector4f(S*1e-4f,0,0,0),257);Expected=5;
                    Geometry.Init(FVector2f(Case==10?1.401298464324817e-45f:1e38f,0),257);}
                if(Case==12){uint32 Bits=0x80000001u;FMemory::Memcpy(&Geometry[256].X,&Bits,4);Bad=true;}
                if(Case==13){Geometry[256].X=std::numeric_limits<float>::quiet_NaN();Bad=true;}
                if(Case==14)Geometry.Init(FVector2f(0,0),257);
                if(Case==15)
                {B.Init(FVector4f(0,0,0,0),257);R[256].X=1.401298464324817e-45f;
                    Geometry.Init(FVector2f(1.401298464324817e-45f,0),257);Expected=5;}
                if(Case==16){R[0].X=.001f;Geometry[0].X=1.401298464324817e-45f;Expected=1;}
            }
            FRDGBuilder Graph(Cmd);auto RB=CreateStructuredBuffer(Graph,TEXT("ResidualTest.RHS"),B);
            auto RR=CreateStructuredBuffer(Graph,TEXT("ResidualTest.Residual"),R);
            auto G=Case>=8?CreateStructuredBuffer(Graph,TEXT("ResidualTest.Geometry"),Geometry):nullptr;
            if(Case==8)
            {Passed &= !RaftSimCheckPressureResidualGPU(Graph,RB,RR,FIntPoint(257,1),Error,RB).Diagnostics && !Error.IsEmpty();}
            auto Check=RaftSimCheckPressureResidualGPU(Graph,RB,RR,FIntPoint(257,1),Error,G);
            if(!Check.Diagnostics){Passed=false;Graph.Execute();return;}
            FRHIGPUBufferReadback Read(TEXT("ResidualTest.Flags"));AddEnqueueCopyPass(Graph,&Read,Check.Diagnostics,16);
            Graph.Execute();Cmd.SubmitAndBlockUntilGPUIdle();const auto* D=static_cast<const uint32*>(Read.Lock(16));
            if(!D){Passed=false;return;}Passed &= Bad?D[0]>0:(D[0]==0 && D[1]==Expected);
            Records.Add(FString::Printf(TEXT("residual case%d invalid%u failed-poles%u expected%u"),Case,D[0],D[1],Expected));Read.Unlock();
        }
    });
    FlushRenderingCommands();TestTrue(TEXT("true residual qualification handles both poles, overflow, subnormal and nonfinite inputs"),Passed);
    for(const auto& R:Records)AddInfo(R);if(!Error.IsEmpty())AddError(Error);return !HasAnyErrors();
}
#endif
