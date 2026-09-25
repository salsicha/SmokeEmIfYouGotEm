#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "Engine/World.h"
#include "Engine/Engine.h"
#include "Engine/LocalPlayer.h"
#include "GameFramework/PlayerController.h"
#include "EnhancedInputSubsystems.h"
#include "EnhancedPlayerInput.h"
#include "InputMappingContext.h"
#include "InputAction.h"
#include "RaftSimGuidePawn.h"
#include "UObject/UnrealType.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimInputContextIsolationTest,
    "RaftSim.Input.PawnContextIsolation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimInputContextIsolationTest::RunTest(const FString&)
{
    auto* Asset=LoadObject<UInputMappingContext>(nullptr,
        TEXT("/Game/RaftSim/Input/IMC_RaftSimDefault.IMC_RaftSimDefault"));
    if (!TestNotNull(TEXT("cooked mapping template"),Asset)) return false;
    const auto Before=Asset->GetMappings();
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    if (!TestNotNull(TEXT("game world"),World)) return false;
    ON_SCOPE_EXIT { World->DestroyWorld(false); World->RemoveFromRoot(); };
    auto* Property=FindFProperty<FObjectPropertyBase>(ARaftSimGuidePawn::StaticClass(),TEXT("DefaultMappingContext"));
    if (!TestNotNull(TEXT("reflected mapping ownership"),Property)) return false;
    ARaftSimGuidePawn* Pawns[2]={World->SpawnActor<ARaftSimGuidePawn>(),World->SpawnActor<ARaftSimGuidePawn>()};
    UInputMappingContext* Contexts[2]={};
    for(int32 I=0;I<2;++I)
    {
        if (!TestNotNull(TEXT("spawned pawn"),Pawns[I])) return false;
        // This isolated world has not initialized actors for play.
        if (!Pawns[I]->IsActorInitialized()) Pawns[I]->PostInitializeComponents();
        Contexts[I]=Cast<UInputMappingContext>(Property->GetObjectPropertyValue_InContainer(Pawns[I]));
        if (!TestNotNull(TEXT("private mapping context"),Contexts[I])) return false;
        TestTrue(TEXT("private context owned by pawn"),Contexts[I]!=Asset && Contexts[I]->GetOuter()==Pawns[I]);
        TestTrue(TEXT("private context transient"),Contexts[I]->HasAnyFlags(RF_Transient));
        TestTrue(TEXT("rescue bindings retained"),Pawns[I]->HasCompleteRescueInputBindings());
        TestTrue(TEXT("independent mouse look retained"),Pawns[I]->UsesIndependentMouseLook());
        bool Steer=false,Record=false;
        for(const auto& Mapping:Contexts[I]->GetMappings())
        {
            if(!Mapping.Action) continue;
            if(Mapping.Action->GetName()==TEXT("IA_GuideSteerRuntime"))
            {Steer=true;TestTrue(TEXT("steer action belongs to this pawn"),Mapping.Action->GetOuter()==Pawns[I]);}
            if(Mapping.Action->GetName()==TEXT("IA_ToggleRecordingRuntime"))
            {Record=true;TestTrue(TEXT("record action belongs to this pawn"),Mapping.Action->GetOuter()==Pawns[I]);}
        }
        TestTrue(TEXT("steering and recording retained"),Steer && Record);
    }
    TestTrue(TEXT("two pawns have distinct contexts"),Contexts[0]!=Contexts[1]);
    const auto SecondBefore=Contexts[1]->GetMappings();
    TestTrue(TEXT("runtime rebind succeeds"),Pawns[0]->ApplyRuntimeKeyBinding(TEXT("PaddleStroke"),EKeys::J));
    TestTrue(TEXT("other pawn unchanged by rebind"),Contexts[1]->GetMappings()==SecondBefore);
    TestTrue(TEXT("source asset unchanged by construction and rebind"),Asset->GetMappings()==Before);
    TestTrue(TEXT("new positive paddle key present"),Pawns[0]->HasPaddleStrokeKeyBinding(EKeys::J,false));
    TestTrue(TEXT("negative paddle key retained"),Pawns[0]->HasPaddleStrokeKeyBinding(EKeys::S,true));
    // Rebinding must not swap unrelated mappings across priority positions.
    auto* RebindMarker=NewObject<UInputAction>(Contexts[0]);
    Contexts[0]->MapKey(RebindMarker,EKeys::F10);
    Contexts[0]->MapKey(RebindMarker,EKeys::F11);
    for(const FKey& NextKey : {EKeys::K,EKeys::L,EKeys::J})
    {
        const auto Previous=Contexts[0]->GetMappings();
        const auto Retained=Previous.FilterByPredicate([](const FEnhancedActionKeyMapping& M)
        {
            // Only the positive keyboard paddle mapping is replaced.
            if(!M.Action || !M.Action->GetName().Contains(TEXT("PaddleStroke")) || M.Key.IsGamepadKey())return true;
            return M.Key==EKeys::S;
        });
        TestTrue(TEXT("repeated rebind succeeds"),Pawns[0]->ApplyRuntimeKeyBinding(TEXT("PaddleStroke"),NextKey));
        const auto& After=Contexts[0]->GetMappings();
        TestEqual(TEXT("one replacement mapping appended"),After.Num(),Retained.Num()+1);
        for(int32 I=0;I<Retained.Num() && I<After.Num();++I)
            TestTrue(TEXT("surviving mapping record and priority exact"),After[I]==Retained[I]);
        TestTrue(TEXT("new positive key dispatched by mapping"),Pawns[0]->HasPaddleStrokeKeyBinding(NextKey,false));
        TestTrue(TEXT("negative key retained after repeated rebind"),Pawns[0]->HasPaddleStrokeKeyBinding(EKeys::S,true));
    }
    TestTrue(TEXT("other pawn unchanged after repeated rebinds"),Contexts[1]->GetMappings()==SecondBefore);
    TestTrue(TEXT("source unchanged after repeated rebinds"),Asset->GetMappings()==Before);
    // Reproduce the stale cooked entries without editing the actual asset.
    auto* Legacy=DuplicateObject<UInputMappingContext>(Asset,GetTransientPackage());
    const FKey LegacyKeys[]={EKeys::RightMouseButton,EKeys::LeftMouseButton,EKeys::Gamepad_LeftTrigger,EKeys::F9};
    for(const FKey& Key:LegacyKeys) { Legacy->MapKey(nullptr,Key); Legacy->MapKey(nullptr,Key); }
    Legacy->MapKey(nullptr,EKeys::F8); // Unrelated missing action must remain visible.
    auto* MarkerAction=NewObject<UInputAction>(Legacy);
    Legacy->MapKey(MarkerAction,EKeys::F9);
    Legacy->MapKey(MarkerAction,EKeys::F10);
    Legacy->MapKey(MarkerAction,EKeys::F11);
    const auto LegacyBefore=Legacy->GetMappings();
    FActorSpawnParameters Deferred; Deferred.bDeferConstruction=true;
    auto* Repaired=World->SpawnActor<ARaftSimGuidePawn>(Deferred);
    if(!TestNotNull(TEXT("legacy-context pawn"),Repaired))return false;
    Property->SetObjectPropertyValue_InContainer(Repaired,Legacy);
    Repaired->FinishSpawning(FTransform::Identity);
    if(!Repaired->IsActorInitialized())Repaired->PostInitializeComponents();
    auto* RepairedContext=Cast<UInputMappingContext>(Property->GetObjectPropertyValue_InContainer(Repaired));
    if(!TestNotNull(TEXT("repaired private context"),RepairedContext))return false;
    for(const FKey& Key:LegacyKeys)
    {
        TestFalse(TEXT("all stale null duplicates removed for repaired key"),RepairedContext->GetMappings().ContainsByPredicate(
            [&Key](const FEnhancedActionKeyMapping& M){return M.Key==Key && !M.Action;}));
        TestTrue(TEXT("replacement action exists for repaired key"),RepairedContext->GetMappings().ContainsByPredicate(
            [&Key](const FEnhancedActionKeyMapping& M){return M.Key==Key && M.Action;}));
    }
    TestTrue(TEXT("unrelated unresolved mapping not silently discarded"),RepairedContext->GetMappings().ContainsByPredicate(
        [](const FEnhancedActionKeyMapping& M){return M.Key==EKeys::F8 && !M.Action;}));
    TestTrue(TEXT("legacy source unchanged by repair"),Legacy->GetMappings()==LegacyBefore);
    TArray<FKey> MarkerKeys;
    for(const auto& Mapping:RepairedContext->GetMappings())
        if(Mapping.Action && Mapping.Action->GetName()==MarkerAction->GetName())MarkerKeys.Add(Mapping.Key);
    TestTrue(TEXT("valid same-key binding and surviving priority order retained"),
        MarkerKeys==TArray<FKey>({EKeys::F9,EKeys::F10,EKeys::F11}));
    TestTrue(TEXT("repair retains rescue controls"),Repaired->HasCompleteRescueInputBindings());
    auto* Controller=World->SpawnActor<APlayerController>();
    if (!TestNotNull(TEXT("local controller"),Controller)) return false;
    auto* LocalPlayer=NewObject<ULocalPlayer>(GEngine);
    LocalPlayer->PlayerController=Controller;
    Controller->Player=LocalPlayer;
    Controller->PlayerInput=NewObject<UEnhancedPlayerInput>(Controller);
    auto* Subsystem=NewObject<UEnhancedInputLocalPlayerSubsystem>(LocalPlayer);
    for(int32 I=0;I<2;++I)
    {
        Subsystem->AddMappingContext(Contexts[I],0);
        Pawns[I]->RegisteredInputSubsystem=Subsystem;
        TestTrue(TEXT("context actually registered before teardown"),Subsystem->HasMappingContext(Contexts[I]));
    }
    TestNull(TEXT("teardown does not rely on possession"),Pawns[0]->GetController());
    Pawns[0]->EndPlay(EEndPlayReason::Destroyed);
    TestFalse(TEXT("destroyed pawn context removed"),Subsystem->HasMappingContext(Contexts[0]));
    TestTrue(TEXT("other pawn context retained"),Subsystem->HasMappingContext(Contexts[1]));
    TestFalse(TEXT("registration owner released"),Pawns[0]->RegisteredInputSubsystem.IsValid());
    Pawns[1]->EndPlay(EEndPlayReason::LevelTransition);
    TestFalse(TEXT("travel removes remaining context"),Subsystem->HasMappingContext(Contexts[1]));
    TestTrue(TEXT("source asset unchanged through teardown"),Asset->GetMappings()==Before);
    return !HasAnyErrors();
}
#endif
