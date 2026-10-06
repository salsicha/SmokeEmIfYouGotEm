#include "RaftSimGroundSourceRegistry.h"
#include "Misc/AutomationTest.h"
#include "Engine/StaticMeshActor.h"
#include "Misc/ScopeExit.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimStreamedGroundSourcesTest,
    "RaftSim.Physics.StreamedGroundSources",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimStreamedGroundSourcesTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Editor,false);
    if (!World) return false;
    ON_SCOPE_EXIT { World->DestroyWorld(false); World->RemoveFromRoot(); };
    FRaftSimGroundSourceRegistry Sources(World);
    Sources.RefreshIfDirty();
    TestEqual(TEXT("initial world has no captured mesh"),Sources.Meshes.Num(),0);
    const uint32 Initial=Sources.GetRefreshCount();
    for (int32 I=0; I<24; ++I) Sources.RefreshIfDirty();
    TestEqual(TEXT("support substeps do not rescan unchanged actor lists"),Sources.GetRefreshCount(),Initial);
    auto* Ground=World->SpawnActor<AStaticMeshActor>();
    if (!Ground) return false;
    Ground->Tags.Add(TEXT("RaftSimPhysicalGround"));
    Sources.RefreshIfDirty();
    TestTrue(TEXT("captured terrain spawned after initial binding is discovered"),
        Sources.Meshes.Num()==1 && Sources.Meshes[0].Get()==Ground->GetStaticMeshComponent());
    auto* Scenery=World->SpawnActor<AStaticMeshActor>();
    if (!Scenery) return false;
    Sources.RefreshIfDirty();
    TestEqual(TEXT("unmarked scenery does not become a physical bed"),Sources.Meshes.Num(),1);
    // Authored streaming actors can acquire their final components/tags after
    // spawn, then signal that their level has been added to the world.
    Scenery->GetStaticMeshComponent()->ComponentTags.Add(TEXT("RaftSimPhysicalGround"));
    // Exercise the bound callback without sending synthetic level lifecycle
    // events to unrelated editor systems (null-world removal is not benign).
    Sources.LevelChanged(World->PersistentLevel,World);
    Sources.RefreshIfDirty();
    TestEqual(TEXT("level addition discovers component-tagged captured terrain"),Sources.Meshes.Num(),2);
    const uint32 BeforeForeign=Sources.GetRefreshCount();
    Sources.LevelChanged(nullptr,nullptr);
    Sources.RefreshIfDirty();
    TestEqual(TEXT("another world's level events do not invalidate this cache"),Sources.GetRefreshCount(),BeforeForeign);
    Scenery->GetStaticMeshComponent()->ComponentTags.Remove(TEXT("RaftSimPhysicalGround"));
    Sources.LevelChanged(World->PersistentLevel,World);
    Sources.RefreshIfDirty();
    TestTrue(TEXT("level removal refresh drops retired contact membership"),
        Sources.Meshes.Num()==1 && Sources.Meshes[0].Get()==Ground->GetStaticMeshComponent());
    return true;
}
#endif
