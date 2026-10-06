#include "Misc/AutomationTest.h"
#include "../Materials/RaftSimLiquidDataset.h"
#include "../Materials/RaftSimLiquidRegionalState.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimLiquidDatasetTest,"RaftSim.Editor.LiquidDataset",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimLiquidDatasetTest::RunTest(const FString&)
{
    const FString Base=FPaths::ProjectDir()/TEXT("../tmp");FString Error;
    FRaftSimLiquidDataset Core,Buffer,Invalid;
    if(!TestTrue(TEXT("Original dataset files and provenance valid"),FRaftSimLiquidDataset::Load(Base,TEXT("core-v1"),Core,Error)))
    { AddError(Error);return false; }
    if(!TestTrue(TEXT("Reservoir dataset files and provenance valid"),FRaftSimLiquidDataset::Load(Base,TEXT("reservoir-v1"),Buffer,Error)))
    { AddError(Error);return false; }
    TestFalse(TEXT("Unknown key cannot silently select original input"),FRaftSimLiquidDataset::Load(Base,TEXT("unknown"),Invalid,Error));
    TestTrue(TEXT("Failed selection leaves no usable dataset"),Invalid.Parent.IsEmpty() && !Invalid.Evidence);
    TestNotEqual(TEXT("Candidate does not replace original directory"),Buffer.Parent,Core.Parent);
    TestNotEqual(TEXT("Captured state identity changes with dataset"),
        Buffer.Evidence->GetStringField(TEXT("ownership_manifest_sha256")),Core.Evidence->GetStringField(TEXT("ownership_manifest_sha256")));
    auto Corrupt=MakeShared<FJsonObject>();Corrupt->SetStringField(TEXT("manifest.json"),FString::ChrN(64,TEXT('0')));
    TestFalse(TEXT("Changed file hash rejected"),FRaftSimLiquidDataset::VerifyFiles(Buffer.Parent,Corrupt));
    Corrupt->Values.Reset();Corrupt->SetStringField(TEXT("../manifest.json"),FRaftSimLiquidDataset::Hash(Buffer.Parent/TEXT("manifest.json")));
    TestFalse(TEXT("Manifest path traversal rejected"),FRaftSimLiquidDataset::VerifyFiles(Buffer.Parent,Corrupt));
    RaftSimLiquidRegionalState::FParent Parent;
    TestTrue(TEXT("Selected buffer parent decodes"),RaftSimLiquidRegionalState::DecodeParent(
        FRaftSimLiquidDataset::Read(Buffer.Regions/TEXT("manifest.json")),
        FRaftSimLiquidDataset::Read(Buffer.Parent/TEXT("grid_boundary_profile.json")),Parent,Error));
    TestEqual(TEXT("Buffer includes original and exterior initial water"),Parent.Seeds,729724);
    TestEqual(TEXT("Actual selected outer width"),Parent.Cells.X,494);
    TestEqual(TEXT("Actual selected outer height"),Parent.Cells.Y,166);
    return true;
}
