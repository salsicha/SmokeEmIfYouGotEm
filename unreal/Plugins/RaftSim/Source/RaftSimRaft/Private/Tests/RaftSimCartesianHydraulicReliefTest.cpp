#include "Misc/AutomationTest.h"
#include "RaftSimCartesianHydraulicRelief.h"
#include <limits>

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCartesianHydraulicReliefTest,
    "RaftSim.M4.CartesianHydraulicReliefScheduling",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimCartesianHydraulicReliefTest::RunTest(const FString&)
{
    constexpr int32 Nx=73,Ny=41,N=Nx*Ny;
    TArray<FRaftSimWaterSample> Samples;Samples.SetNum(N);
    TArray<float> Heights,Expected,Serial,Parallel;Heights.SetNum(N);
    TArray<uint8> Wet;Wet.Init(1,N);
    int64 Compared=0;int32 Nonzero=0;
    for(int32 Frame=0;Frame<12;++Frame)
    {
        for(int32 I=0;I<N;++I)
        {
            const int32 X=I%Nx,Y=I/Nx;
            Heights[I]=220.f+.2f*FMath::Sin(float(X)*.6f+Frame*.13f)+.1f*FMath::Cos(float(Y)*.7f);
            Samples[I].VelocityMetersPerSecond=FVector(2.*FMath::Cos(Frame*.7),2.*FMath::Sin(Frame*.7),0.);
            if(I%17==0)Samples[I].VelocityMetersPerSecond=FVector::ZeroVector;
            Samples[I].DepthMeters=.3f+float(I%23)*.1f;
            Wet[I]=Frame%3==0 || (X-35)*(X-35)+(Y-20)*(Y-20)>Frame*Frame;
        }
        if(Frame==10)Heights[N/2]=std::numeric_limits<float>::infinity();
        if(Frame==11)Wet.Init(0,N);
        const int32 Near=1+Frame%3,Far=2*Near;const float Scale=.7f;
        // Independent retained actor loop, not the helper's serial branch.
        Expected.Init(0.f,N);
        for(int32 Index=0;Index<N;++Index)
        {
            if(!Wet[Index])continue;
            const auto& Sample=Samples[Index];
            const FVector2D Direction=RaftSimWaterFlowFrame::Direction(FVector2D(
                Sample.VelocityMetersPerSecond.X,Sample.VelocityMetersPerSecond.Y));
            const FVector2D Position(Index%Nx,Index/Nx);
            float Values[4];bool Valid=true;int32 I=0;
            for(const int32 Offset:{-Far,-Near,Near,Far})
                Valid &= RaftSimWaterFlowFrame::SampleWetScalar(Heights,Wet,Nx,Ny,
                    Position+Direction*Offset,Values[I++]);
            if(!Valid)continue;
            Expected[Index]=URaftSimWaterRuntimeAdapter::ComputeCoupledHydraulicReliefMeters(
                Heights[Index],Values[0],Values[1],Values[2],Values[3],
                Sample.VelocityMetersPerSecond.Size2D(),Sample.DepthMeters)*Scale;
        }
        TestTrue(TEXT("serial input accepted"),RaftSimCartesianHydraulicRelief::Apply(Samples,Heights,Wet,Nx,Ny,Near,Far,Scale,Serial,false));
        TestTrue(TEXT("parallel input accepted"),RaftSimCartesianHydraulicRelief::Apply(Samples,Heights,Wet,Nx,Ny,Near,Far,Scale,Parallel,true));
        TestTrue(TEXT("all float bits match original loop, including dry/invalid samples"),
            FMemory::Memcmp(Expected.GetData(),Serial.GetData(),N*sizeof(float))==0 &&
            FMemory::Memcmp(Expected.GetData(),Parallel.GetData(),N*sizeof(float))==0);
        for(float Value:Expected)Nonzero+=Value!=0.f;
        Compared+=N;
    }
    TestTrue(TEXT("moving curved field exercises nonzero relief"),Nonzero>100);
    const auto Saved=Parallel;
    TestFalse(TEXT("invalid layout rejects"),RaftSimCartesianHydraulicRelief::Apply(Samples,Heights,Wet,Nx,Ny+1,1,2,1.f,Parallel,true));
    TestTrue(TEXT("rejection leaves output unchanged"),Parallel==Saved);
    AddInfo(FString::Printf(TEXT("%lld original-loop float comparisons over changing directions, holes, zero currents, boundaries and strides"),Compared));
    return !HasAnyErrors();
}
#endif
