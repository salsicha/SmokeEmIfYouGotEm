#include "Misc/AutomationTest.h"
#include "RaftSimWaterSourcePacking.h"
#include <cmath>
#include <limits>

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimSourceColorTest,"RaftSim.M4.SourceColorQuantization",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimSourceColorTest::RunTest(const FString&)
{
    int64 Count=0;
    const auto Check=[&](const FLinearColor& C)
    {
        ++Count;
        if(C.ToFColor(false)!=RaftSimWaterSourcePacking::VectorColor(C))
        {AddError(FString::Printf(TEXT("Original engine byte quantization mismatch at case %lld"),Count));return false;}
        return true;
    };
    for(int32 I=0;I<256;++I)
    {
        const float V=(I-.5f)/255.f;
        for(float X:{std::nextafter(V,-std::numeric_limits<float>::infinity()),V,
                     std::nextafter(V,std::numeric_limits<float>::infinity())})
            for(int32 Lane=0;Lane<4;++Lane)
            {
                FLinearColor C(.137f,.291f,.783f,.619f);(&C.R)[Lane]=X;
                if(!Check(C))return false;
            }
    }
    const float Special[]={-std::numeric_limits<float>::infinity(),-1.f,-0.f,0.f,
        std::numeric_limits<float>::denorm_min(),1.f,2.f,std::numeric_limits<float>::infinity(),
        std::numeric_limits<float>::quiet_NaN(),std::numeric_limits<float>::signaling_NaN()};
    for(float V:Special)for(int32 Lane=0;Lane<4;++Lane)
    {FLinearColor C(.2f,.4f,.6f,.8f);(&C.R)[Lane]=V;if(!Check(C))return false;}
    // Uniform bit patterns include negative values, NaNs, infinities and
    // subnormals; a separate [0,1] distribution exercises optical values.
    uint32 State=0x715e093b;
    for(int32 I=0;I<250000;++I)
    {
        FLinearColor C,D;
        for(int32 Lane=0;Lane<4;++Lane)
        {
            State=1664525u*State+1013904223u;
            FMemory::Memcpy((&C.R)+Lane,&State,sizeof(float));
            (&D.R)[Lane]=float(State&0xffffffu)/float(0xffffffu);
        }
        if(!Check(C) || !Check(D))return false;
    }
    AddInfo(FString::Printf(TEXT("Exact engine quantization: %lld four-channel colors, half-byte neighbors, special values and deterministic bit patterns"),Count));
    return !HasAnyErrors();
}
#endif
