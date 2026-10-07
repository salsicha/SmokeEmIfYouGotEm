#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "Misc/Paths.h"
#include "HAL/FileManager.h"
#include "RaftSimWaterRuntimeAdapter.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimPresentationBoundsTest,
    "RaftSim.Continuous.PresentationSourceBounds",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimPresentationBoundsTest::RunTest(const FString&)
{
    auto* Water = NewObject<URaftSimWaterRuntimeAdapter>();
    FBox2D Bounds;
    TestFalse(TEXT("unloaded source has no fabricated bounds"), Water->GetCurvedPresentationBaselineBoundsM(Bounds));
    TestFalse(TEXT("unloaded bounds invalid"), bool(Bounds.bIsValid));
    const FString Path = FPaths::Combine(FPaths::ProjectSavedDir(),
        TEXT("Automation"), TEXT("presentation-bounds-") + FGuid::NewGuid().ToString() + TEXT(".bin"));
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Path), true);
    ON_SCOPE_EXIT { IFileManager::Get().Delete(*Path); };
    {
        TUniquePtr<FArchive> Writer(IFileManager::Get().CreateFileWriter(*Path));
        if (!TestTrue(TEXT("unique fixture writer"), Writer.IsValid())) return false;
        uint32 Magic = 0x52534246u, Version = 1;
        int32 Width = 3, Rows = 3;
        float Origin = -4.f, Spacing = 2.f;
        TArray<float> Stations{1001.f, 1004.f, 1009.f}, Heights, Energy;
        TArray<uint8> Wet;
        Heights.Init(700.f, 9); Energy.Init(.1f, 9); Wet.Init(1, 9);
        *Writer << Magic << Version << Width << Rows << Origin << Spacing;
        *Writer << Stations << Heights << Energy << Wet;
    }
    if (!TestTrue(TEXT("production baseline loader"), Water->LoadPresentationBaselineFieldFromFile(Path))) return false;
    TestTrue(TEXT("loaded source exposes own coverage"), Water->GetCurvedPresentationBaselineBoundsM(Bounds));
    TestEqual(TEXT("nonzero irregular station minimum"), Bounds.Min, FVector2D(1001., -4.));
    TestEqual(TEXT("station and lateral maximum"), Bounds.Max, FVector2D(1009., 0.));
    for (const FVector2D P : {Bounds.Min, Bounds.Max, FVector2D(1003., -1.)})
    {
        FRaftSimWaterSample Sample;
        TestTrue(TEXT("included source nodes still sample"), Water->SamplePresentationBaselineFieldAtRiverCoordinates(P, Sample));
    }
    for (const FVector2D P : {FVector2D(1000., -2.), FVector2D(1010., -2.),
            FVector2D(1004., -5.), FVector2D(1004., 1.), FVector2D(450000., -2.)})
    {
        FRaftSimWaterSample Sample;
        TestFalse(TEXT("outside source cannot produce water even on a longer route"),
            Water->SamplePresentationBaselineFieldAtRiverCoordinates(P, Sample));
    }
    return true;
}
#endif
