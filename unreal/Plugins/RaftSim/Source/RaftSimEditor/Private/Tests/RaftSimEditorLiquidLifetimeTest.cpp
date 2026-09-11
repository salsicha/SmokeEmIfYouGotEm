#include "Misc/AutomationTest.h"
#include "RaftSimLiquidLifetime.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLiquidLifetimeTest,"RaftSim.Editor.LiquidLifetime",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FLiquidLifetimeTest::RunTest(const FString&)
{
    const FGuid A=FGuid::NewGuid(),B=FGuid::NewGuid();FString Error;
    const TArray<FRaftSimLiquidBirthPlan> Initial={{0,3,0,true},{1,2,0,true}};
    const TArray<FRaftSimLiquidBirthPlan> Next={{0,0,0,false},{1,1,0,false}};
    for(int32 Mode=0;Mode<7;++Mode)
    {
        FRaftSimLiquidLifetime Life;FRaftSimLiquidTickToken First,Second;
        TestTrue(TEXT("Fresh generation"),Life.Initialize(A,2,Error));
        TestTrue(TEXT("Native initial reset/births"),Life.BeginStep(1,Initial,First,Error));
        TestTrue(TEXT("First tick closes"),Life.EndStep(First,Error));
        TestTrue(TEXT("Next native births"),Life.BeginStep(2,Next,Second,Error));
        TestEqual(TEXT("Birth totals persist"),Life.GetBirths()[1],uint64(3));
        if(Mode==0)
        {
            TestTrue(TEXT("One transfer claim"),Life.ClaimTransfer(Second,Error));
            TestTrue(TEXT("Transfer tick ends"),Life.EndStep(Second,Error));
            FRaftSimLiquidLifetime Restart;FRaftSimLiquidTickToken New;
            TestTrue(TEXT("Fresh native generation can restart at sequence zero"),Restart.Initialize(B,2,Error)&&Restart.BeginStep(1,Initial,New,Error));
            TestTrue(TEXT("Generation identity distinguishes reused birth words"),New.Generation!=First.Generation);
            continue;
        }
        if(Mode==1) { auto Stale=Second;Stale.Generation=B;TestFalse(TEXT("Stale generation rejected"),Life.ClaimTransfer(Stale,Error)); }
        if(Mode==2) { Life.ClaimTransfer(Second,Error);TestFalse(TEXT("Duplicate transfer rejected"),Life.ClaimTransfer(Second,Error)); }
        if(Mode==3) { Life.EndStep(Second,Error);TestFalse(TEXT("Closed tick rejected"),Life.ClaimTransfer(Second,Error)); }
        if(Mode==4) { Life.EndStep(Second,Error);TestFalse(TEXT("Skipped tick rejected"),Life.BeginStep(4,Next,Second,Error)); }
        if(Mode==5) { Life.EndStep(Second,Error);TestFalse(TEXT("Uncoordinated native reset rejected"),Life.BeginStep(3,Initial,Second,Error)); }
        if(Mode==6) { auto Stale=Second;Stale.TransferEpoch=0;TestFalse(TEXT("Wrong acquire epoch rejected"),Life.ClaimTransfer(Stale,Error)); }
        TestTrue(TEXT("Generation remains fail-closed"),Life.IsFailed());
        TestFalse(TEXT("Failed coordinator cannot be reinitialized"),Life.Initialize(B,2,Error));
    }
    // Reach wrap boundary without billions of loop iterations. No narrowing of
    // cumulative birth counts is permitted, even though particle IDs are uint32.
    FRaftSimLiquidLifetime Limit;FRaftSimLiquidTickToken T;
    TestTrue(TEXT("Counter boundary generation"),Limit.Initialize(A,2,Error));
    TArray<FRaftSimLiquidBirthPlan> Huge={{0,MAX_uint32,1,true},{1,0,0,true}};
    TestTrue(TEXT("Every uint32 identity bit pattern allowed"),Limit.BeginStep(1,Huge,T,Error));
    TestEqual(TEXT("Full unsigned namespace retained"),Limit.GetBirths()[0],uint64(MAX_uint32)+1);
    Limit.EndStep(T,Error);Huge={{0,1,0,false},{1,0,0,false}};
    TestFalse(TEXT("Next birth cannot alias sequence zero"),Limit.BeginStep(2,Huge,T,Error));
    TestEqual(TEXT("Rejected plan leaves birth count unchanged"),Limit.GetBirths()[0],uint64(MAX_uint32)+1);
    FRaftSimLiquidLifetime Duplicate;Duplicate.Initialize(B,2,Error);
    Huge={{0,0,0,true},{0,0,0,true}};
    TestFalse(TEXT("Duplicate owner cannot hide missing reset participant"),Duplicate.BeginStep(1,Huge,T,Error));
    return !HasAnyErrors();
}
