#include "RaftSimCartesianEddyOwners.h"
#include "Misc/AutomationTest.h"
#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCartesianEddyOwnersTest,"RaftSim.P2.CartesianEddyOwners",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimCartesianEddyOwnersTest::RunTest(const FString&)
{
    constexpr int32 W=17,N=W*W;
    TArray<uint8> Wet,Available;Wet.Init(1,N);Available.Init(1,N);
    TArray<FVector2D> P;for(int32 Y=0;Y<W;++Y)for(int32 X=0;X<W;++X)P.Add(FVector2D(X-8,Y-8));
    for(int32 Y=7;Y<=9;++Y)for(int32 X=7;X<=9;++X)Wet[Y*W+X]=0;
    auto Islands=RaftSimCartesianEddyOwners::Find(Wet,Available,P,W,W,1.);
    TestEqual(TEXT("enclosed dry terrain island discovered"),Islands.Num(),1);
    if(Islands.Num()!=1)return false;
    TestTrue(TEXT("actual hydraulic-coordinate centroid"),Islands[0].Center.IsNearlyZero());
    TestEqual(TEXT("wet collar contains twelve real neighbors"),Islands[0].Collar.Num(),12);
    TestTrue(TEXT("radius explicitly inferred from existing area"),FMath::Abs(Islands[0].Radius-FMath::Sqrt(9./UE_DOUBLE_PI))<1.e-12);
    auto Anisotropic=P;
    for(auto& Point:Anisotropic){Point.X*=2.;Point.Y*=3.;}
    const auto CurvedGrid=RaftSimCartesianEddyOwners::Find(Wet,Available,Anisotropic,W,W,1.);
    TestEqual(TEXT("station/lateral topology shares discovery"),CurvedGrid.Num(),1);
    if(CurvedGrid.Num()==1)TestTrue(TEXT("non-square actual cell area owns inferred radius"),
        FMath::Abs(CurvedGrid[0].Radius-FMath::Sqrt(54./UE_DOUBLE_PI))<1.e-12);
    Available[7*W+6]=0;
    TestEqual(TEXT("unknown collar cannot become eddy geometry"),RaftSimCartesianEddyOwners::Find(Wet,Available,P,W,W,1.).Num(),0);
    Available[7*W+6]=1;for(int32 X=0;X<7;++X)Wet[8*W+X]=0;
    TestEqual(TEXT("bank-connected component excluded"),RaftSimCartesianEddyOwners::Find(Wet,Available,P,W,W,1.).Num(),0);
    return !HasAnyErrors();
}
#endif
