#include "Misc/AutomationTest.h"
#include "RaftSimBreakingCandidateGate.h"
#include "RaftSimWaterFlowFrame.h"
#include <limits>
#include <cmath>

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimBreakingCandidateGateTest,
    "RaftSim.Water.BreakingCandidateGate",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimBreakingCandidateGateTest::RunTest(const FString&)
{
    const float Values[]={-1.f,0.f,std::nextafter(.94f,0.f),.94f,std::nextafter(.94f,1.f),2.f,
        std::numeric_limits<float>::infinity(),-std::numeric_limits<float>::infinity(),
        std::numeric_limits<float>::quiet_NaN()};
    int32 Compared=0,Skipped=0;bool Exact=true;
    for(bool Cartesian:{false,true})for(int32 Stride:{1,3,7})
    for(int32 Mask=0;Mask<8;++Mask)for(float Froude:Values)
    for(int32 Index=0;Index<63;++Index)for(FVector2D Velocity:{FVector2D(0.,0.),FVector2D(1.,0.),FVector2D(-2.,3.),FVector2D(1.,-4.)})
    {
        const auto Wet=[&](int32 I)->uint8 {return ((I+Mask)%3)==0?0:1;};
        const auto Direction=Cartesian?RaftSimWaterFlowFrame::Direction(Velocity):FVector2D(1.,0.);
        const int32 Up=Cartesian?RaftSimWaterFlowFrame::OffsetIndex(Index,9,7,Direction,-Stride):Index-Stride;
        // Non-Cartesian production starts at X >= Stride.
        if(!Cartesian && Index%9<Stride)continue;
        const bool Original=Up!=INDEX_NONE && Wet(Index)!=0 && Wet(Up)!=0 && !(Froude>.94f);
        const bool Early=RaftSimBreakingCandidateGate::RejectCurrent(Wet(Index),Froude);
        const bool Candidate=!Early && Up!=INDEX_NONE && Wet(Up)!=0;
        Exact &= Original==Candidate;++Compared;Skipped+=Early;
    }
    TestTrue(TEXT("Original survivor decisions including dry/upstream boundaries/NaN match"),Exact);
    TestTrue(TEXT("Direction work is actually skipped"),Skipped>0 && Skipped<Compared);
    AddInfo(FString::Printf(TEXT("Compared=%d early_rejections=%d"),Compared,Skipped));
    return true;
}
#endif
