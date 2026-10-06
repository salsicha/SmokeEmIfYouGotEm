#include "Misc/AutomationTest.h"
#include "RaftSimCoordinateMap.h"
#include <cmath>
#include <limits>

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCoordinateMapTest,"RaftSim.M4.ExactCoordinateMap",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimCoordinateMapTest::RunTest(const FString&)
{
    TRaftSimCoordinateMap<int32> Fast;TMap<FVector2D,int32> Reference;
    TArray<FVector2D> Points;
    for(int32 Y=0;Y<96;++Y)for(int32 X=0;X<96;++X)
    {
        const FVector2D P(-545000.+X*12.5,-360000.+Y*12.5);
        Points.Add(P);
        Points.Emplace(std::nextafter(P.X,0.),P.Y);
        Points.Emplace(P.X,std::nextafter(P.Y,0.));
    }
    Points.Emplace(std::numeric_limits<double>::denorm_min(),1.);
    Points.Emplace(-std::numeric_limits<double>::denorm_min(),1.);
    for(int32 I=0;I<Points.Num();++I){Fast.Add(Points[I],I);Reference.Add(Points[I],I);}
    TestEqual(TEXT("all distinct full-precision keys retained"),Fast.Num(),Points.Num());
    for(int32 I=0;I<Points.Num();++I)
    {
        const auto* Value=Fast.Find(Points[I]);
        if(!Value || *Value!=Reference.FindChecked(Points[I])){AddError(TEXT("exact coordinate lookup differs"));return false;}
        if(I%7==0){Fast.Add(Points[I],-I);Reference.Add(Points[I],-I);}
    }
    for(int32 I=0;I<Points.Num();++I)
        if(Fast.FindChecked(Points[I])!=Reference.FindChecked(Points[I])){AddError(TEXT("last-writer semantics differ"));return false;}
    const int32 Before=Fast.Num();Fast.Add(FVector2D(0.,-0.),42);Fast.Add(FVector2D(-0.,0.),71);
    TestEqual(TEXT("equal signed zero keys share a slot"),Fast.Num(),Before+1);
    TestEqual(TEXT("signed zero retains last writer"),Fast.FindChecked(FVector2D(0.,0.)),71);
    TestEqual(TEXT("signed zero has equal hashes"),TRaftSimCoordinateKeyFuncs<int32>::GetKeyHash(FVector2D(0.,-0.)),
        TRaftSimCoordinateKeyFuncs<int32>::GetKeyHash(FVector2D(-0.,0.)));
    Fast.Reset();TestEqual(TEXT("reset removes prior values"),Fast.Num(),0);
    TestFalse(TEXT("reset cannot serve stale coordinates"),Fast.Contains(Points[0]));
    return true;
}
#endif
