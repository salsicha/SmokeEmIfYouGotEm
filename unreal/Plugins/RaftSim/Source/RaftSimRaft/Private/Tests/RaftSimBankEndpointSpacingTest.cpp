#include "RaftSimWaterShoreline.h"
#include "RaftSimWaterBankContour.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimBankEndpointSpacingTest,
    "RaftSim.M4.BankEndpointSpacing",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimBankEndpointSpacingTest::RunTest(const FString&)
{
    using namespace RaftSimWaterShoreline;
    // Same-call cached values and submitted triangle from v22 contact report
    // bff4c53b8ad86c0003b40036862ae8c0e8e6aeb3a2e238e5e70ab0ff4dd2b74f.
    const TArray<float> Bed={8.45587158203125f,8.711944580078125f,
        8.397781372070312f,8.534469604492188f};
    const TArray<float> H={.061720576137304306f,0.f,
        .16925844550132751f,.17600621283054352f};
    const TArray<uint8> Wet={1,0,1,1},Available={1,1,1,1};
    const FVector2D Probe(.9013296732491654,.12234552688732947);
    double B[4],D[4];for(int32 I=0;I<4;++I){B[I]=Bed[I];D[I]=H[I];}
    TestTrue(TEXT("captured point has negative reconstructed depth, not a film"),
        RaftSimWaterBankContour::SignedDepth(B,D,Probe)<-.044);

    TArray<FProcMeshVertex> Captured;Captured.SetNum(3);
    Captured[0].Position=FVector(1.,.5041379432518625,8.710422257356859);
    Captured[1].Position=FVector(.6710989108305512,.05793331661516277,8.704395527018899);
    Captured[2].Position=FVector(1.,.0082758865046344,8.710422257356859);
    const TArray<uint32> CapturedIndices={0,1,2};FVector Hit;
    TestTrue(TEXT("retained submitted triangle reproduces dry coverage"),
        Sample(Probe,0,3,Captured,CapturedIndices,Hit));

    for(bool Compact:{false,true})for(double Sign:{-1.,1.})for(double Angle:{0.,.37})
    {
        const auto World=[&](FVector2D P,double Z){
            return FVector(-542700.+100.*(FMath::Cos(Angle)*P.X-FMath::Sin(Angle)*P.Y),
                Sign*(360200.+100.*(FMath::Sin(Angle)*P.X+FMath::Cos(Angle)*P.Y)),Z*100.);};
        TArray<FProcMeshVertex> Source;Source.SetNum(4);
        for(int32 I=0;I<4;++I){Source[I].Position=World(FVector2D(I%2,I/2),Bed[I]+H[I]);Source[I].Normal=FVector::UpVector;}
        TArray<FProcMeshVertex> V;TArray<uint32> T;TArray<FCurvedBank> Banks;
        if(!TestTrue(TEXT("captured cell builds with balanced rays"),
            Build(2,2,MoveTemp(Source),Wet,Available,H,Bed,V,T,nullptr,nullptr,Compact,true,true,&Banks)))return false;
        const FVector Query=World(Probe,0.);
        TestFalse(TEXT("new submitted geometry excludes captured dry probe"),
            Sample(FVector2D(Query.X,Query.Y),0,T.Num(),V,T,Hit));
        if(!TestEqual(TEXT("one bank with unchanged segment count"),Banks.Num(),1))return false;
        TestEqual(TEXT("no blanket subdivision increase"),Banks[0].Segments,16);
        for(const auto& P:Banks[0].Points)
            TestTrue(TEXT("each generated node stays on original zero-depth contour"),
                FMath::Abs(RaftSimWaterBankContour::SignedDepth(B,D,P))<1.e-8);
    }
    // Rescaling either endpoint changes its distance but not its direction.
    // Exercise tiny positive distances without a GetSafeNormal epsilon cutoff.
    const FVector2D Origin(1.,0.),A(.24,0.),C(1.,.008);
    for(double Scale:{1.,1.e-6,1.e-12})for(int32 I=1;I<16;++I)
    {
        const FVector2D P=RaftSimWaterBankContour::Point(B,D,1,A,C,double(I)/16);
        const FVector2D Q=RaftSimWaterBankContour::Point(B,D,1,
            Origin+(A-Origin)*Scale,C,double(I)/16);
        const FVector2D R=RaftSimWaterBankContour::Point(B,D,1,
            A,Origin+(C-Origin)*Scale,double(I)/16);
        TestTrue(TEXT("rays independent of endpoint distance"),
            P.Equals(Q,1.e-10) && P.Equals(R,1.e-10));
    }
    // This is not a certificate for every chord interior or two-wet-corner
    // banks. Those retained failures remain separate reconstruction work.
    return !HasAnyErrors();
}
#endif
