#include "Misc/AutomationTest.h"
#include "RaftSimWaterInterpolation.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimWaterInterpolationTest,"RaftSim.M4.WaterInterpolation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimWaterInterpolationTest::RunTest(const FString&)
{
    for(int32 N:{0,1,1023,1024,1025,50625})
    {
        TArray<FVector> P,Normal,RP,RN,SP,SN;
        TArray<FLinearColor> C,RC,SC;
        TArray<FVector2D> F,W,RF,RW,SF,SW;
        P.SetNum(N);Normal.SetNum(N);C.SetNum(N);F.SetNum(N);W.SetNum(N);
        RP.Init(FVector(3,-7,19),N);RN.Init(FVector::ZeroVector,N);
        RC.Init(FLinearColor(.1f,.7f,.3f,.9f),N);
        RF.Init(FVector2D(2,-3),N);RW.Init(FVector2D(-4,1),N);
        SP=RP;SN=RN;SC=RC;SF=RF;SW=RW;
        for(int32 Frame=0;Frame<16;++Frame)
        {
            const float Alpha=Frame==0 ? 0.f : (Frame==1 ? 1.f : 1.f-FMath::Exp(-16.f*(Frame+1)/1000.f));
            for(int32 I=0;I<N;++I)
            {
                P[I]=FVector(68920000.+I*.13,-429600000.+I*.19,Frame*.3);
                Normal[I]=I%3==0 ? FVector::ZeroVector : FVector(I%7-3,Frame-8,1).GetSafeNormal();
                C[I]=FLinearColor((I%17)/16.f,Frame*.1f,.31f,.75f);
                F[I]=FVector2D(I*.07,Frame*-.17);W[I]=FVector2D(Frame*.03,I*-.01);
            }
            // Independent original expressions, not a second call to Advance.
            for(int32 I=0;I<N;++I)
            {
                RP[I]=FMath::Lerp(RP[I],P[I],Alpha);
                RN[I]=FMath::Lerp(RN[I],Normal[I],Alpha).GetSafeNormal();
                RC[I]=FMath::Lerp(RC[I],C[I],Alpha);
                RF[I]=FMath::Lerp(RF[I],F[I],Alpha);
                RW[I]=FMath::Lerp(RW[I],W[I],Alpha);
            }
            if(!TestTrue(TEXT("valid parallel history"),RaftSimWaterInterpolation::Advance(
                P,Normal,C,F,W,Alpha,SP,SN,SC,SF,SW,true))) return false;
            const auto Exact=[](const auto& A,const auto& B)
            {return A.Num()==B.Num() && (!A.Num() || !FMemory::Memcmp(A.GetData(),B.GetData(),A.Num()*sizeof(A[0])));};
            if(!TestTrue(TEXT("all evolving histories bit exact"),Exact(RP,SP) && Exact(RN,SN) &&
                Exact(RC,SC) && Exact(RF,SF) && Exact(RW,SW)))return false;
        }
        const auto Before=SP;
        SW.Add(FVector2D::ZeroVector);
        TestFalse(TEXT("mismatched history rejected before mutation"),RaftSimWaterInterpolation::Advance(
            P,Normal,C,F,W,.5f,SP,SN,SC,SF,SW,true));
        TestTrue(TEXT("rejected update leaves positions unchanged"),Before==SP);
    }
    return true;
}
#endif
