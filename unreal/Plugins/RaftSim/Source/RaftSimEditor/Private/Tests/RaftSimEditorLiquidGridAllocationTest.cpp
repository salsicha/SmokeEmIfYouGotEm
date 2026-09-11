#include "Misc/AutomationTest.h"
#include "../Materials/RaftSimLiquidGridAllocation.h"
#include "UObject/StrongObjectPtr.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLiquidIndependentAllocationTest,
    "RaftSim.Editor.LiquidIndependentAllocation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLiquidIndependentAllocationTest::RunTest(const FString&)
{
    auto* Source=LoadObject<UNiagaraSystem>(nullptr,TEXT("/Game/RaftSim/VFX/Water/LiquidBodyReview/NS_SouthForkLiquidTerrainReview.NS_SouthForkLiquidTerrainReview"));
    if (!TestNotNull(TEXT("Saved source fixture"),Source)) return false;
    FString Error;
    TestFalse(TEXT("Saved source cannot be modified"),RaftSimInstallLiquidGridAllocation(Source,FIntVector(68,36,24),FVector3f(3400,2700,800),Error));
    TStrongObjectPtr<UNiagaraSystem> Candidate(DuplicateObject<UNiagaraSystem>(Source,GetTransientPackage()));
    TestFalse(TEXT("Whole-domain allocation cannot bypass cap"),RaftSimInstallLiquidGridAllocation(Candidate.Get(),FIntVector(496,166,24),FVector3f(24800,8300,800),Error));
    TestFalse(TEXT("Odd X cannot use native half-X dispatch"),RaftSimInstallLiquidGridAllocation(Candidate.Get(),FIntVector(65,36,24),FVector3f(3250,2700,800),Error));
    TestTrue(TEXT("Final pair keeps exact extent and cell count"),RaftSimInstallLiquidGridAllocation(Candidate.Get(),FIntVector(66,36,24),FVector3f(3300,2700,800),Error));
    if (!TestTrue(TEXT("Exact XYZ mode installed"),RaftSimInstallLiquidGridAllocation(Candidate.Get(),FIntVector(68,36,24),FVector3f(3400,2700,800),Error)))
    { AddError(Error);return false; }
    const auto Extent=Candidate->GetExposedParameters().GetParameterValue<FVector3f>(
        FNiagaraVariable(FNiagaraTypeDefinition::GetVec3Def(),TEXT("User.World Grid Extents")));
    TestEqual(TEXT("No isotropic extent rounding"),Extent,FVector3f(3400,2700,800));
    TestTrue(TEXT("Repeat configuration uses owned independent mode"),RaftSimInstallLiquidGridAllocation(Candidate.Get(),FIntVector(68,36,24),Extent,Error));
    return true;
}
