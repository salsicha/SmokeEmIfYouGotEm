// P4 test: each generated river map loads a live cooked-field river window (or
// falls back to the dev tank if its fields are not cooked yet) and the raft
// rests on wet, finite water. Runs once per map that exists.

#include "AssetRegistry/AssetRegistryModule.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Misc/AutomationTest.h"
#include "RaftSimPhysicsBridgeSubsystem.h"
#include "RaftSimCrewAvatarActor.h"
#include "RaftSimRaftActor.h"
#include "RaftSimRockObstacleActor.h"
#include "RaftSimRiverWaterConfig.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "RaftSimWaterSurfaceActor.h"
#include "RaftSimWaterVfxActor.h"
#include "ProceduralMeshComponent.h"
#include "Tests/AutomationCommon.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_COMPLEX_AUTOMATION_TEST(
    FRaftSimRiverMapLoadsTest,
    "RaftSim.P4.RiverMapLoads",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext |
        EAutomationTestFlags::ProductFilter)

namespace
{

const TCHAR* GRiverMapPaths[] = {
    TEXT("/Game/RaftSim/Maps/L_Troublemaker"),
    TEXT("/Game/RaftSim/Maps/L_Hance"),
    TEXT("/Game/RaftSim/Maps/L_UpperHuacas"),
    TEXT("/Game/RaftSim/Maps/L_Terminator"),
    TEXT("/Game/RaftSim/Maps/L_LavaCanyon"),
    TEXT("/Game/RaftSim/Maps/L_Zambezi"),
};

UWorld* GetRiverTestWorld()
{
    for (const FWorldContext& Context : GEngine->GetWorldContexts())
    {
        if (Context.World() != nullptr &&
            (Context.WorldType == EWorldType::PIE || Context.WorldType == EWorldType::Game))
        {
            return Context.World();
        }
    }
    return nullptr;
}

bool MapExists(const FString& PackagePath)
{
    const FString FileName = FPackageName::LongPackageNameToFilename(
        PackagePath, FPackageName::GetMapPackageExtension());
    return FPaths::FileExists(FileName);
}

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(
    FRaftSimStartZambeziLaunchCommand, FAutomationTestBase*, Test);
bool FRaftSimStartZambeziLaunchCommand::Update()
{
    UWorld* World = GetRiverTestWorld();
    if (World == nullptr)
    {
        Test->AddError(TEXT("No world for Zambezi launch command"));
        return true;
    }
    for (TActorIterator<ARaftSimRaftActor> It(World); It; ++It)
    {
        if (It->GetActorLabel() == TEXT("RaftSim_Zambezi_PlayerRaft"))
        {
            Test->TestEqual(
                TEXT("Zambezi raft remains upright through initial settle"),
                static_cast<int32>(It->GetRaftMode()),
                static_cast<int32>(ERaftSimRaftMode::Upright));
            Test->TestEqual(
                TEXT("Zambezi initial settle keeps every person in the raft"),
                It->GetSwimmerCount(),
                0);
            It->IssueCrewCommand(ERaftSimCrewCommand::AllForward);
            return true;
        }
    }
    Test->AddError(TEXT("Zambezi launch command found no player raft"));
    return true;
}

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(
    FRaftSimAssertRiverMapCommand, FAutomationTestBase*, Test);
bool FRaftSimAssertRiverMapCommand::Update()
{
    UWorld* World = GetRiverTestWorld();
    if (World == nullptr)
    {
        Test->AddError(TEXT("No world for river map"));
        return true;
    }

    // A live water window must be configured (river window, or the dev-tank
    // fallback if this river's cooked fields are not present yet). Either way,
    // wet finite water the raft can float on.
    if (const UGameInstance* GI = World->GetGameInstance())
    {
        if (URaftSimPhysicsBridgeSubsystem* Bridge =
                GI->GetSubsystem<URaftSimPhysicsBridgeSubsystem>())
        {
            if (URaftSimWaterRuntimeAdapter* Water = Bridge->GetWaterRuntime())
            {
                Test->TestTrue(TEXT("a live water window is configured"), Water->HasLiveWindow());
                FRaftSimWaterLiveWindowStats Stats;
                if (Water->GetLiveWindowStats(Stats))
                {
                    Test->TestTrue(
                        FString::Printf(TEXT("window is wet (%.2f) and finite"), Stats.WetFraction),
                        Stats.WetFraction > 0.02f && !Stats.bHasNonFinite);
                }
            }
        }
    }

    bool bZambeziReferenceRun = false;
    bool bPacuareReferenceRun = false;
    bool bColoradoHanceReferenceRun = false;
    bool bChilkoLavaCanyonReferenceRun = false;
    bool bFutaleufuTerminatorReferenceRun = false;
    ARaftSimRaftActor* PlayerRaft = nullptr;
    if (TActorIterator<ARaftSimRaftActor> It(World); It)
    {
        PlayerRaft = *It;
        bZambeziReferenceRun = PlayerRaft->GetActorLabel() ==
            TEXT("RaftSim_Zambezi_PlayerRaft");
        bPacuareReferenceRun = PlayerRaft->GetActorLabel() ==
            TEXT("RaftSim_PacuareUpperHuacas_PlayerRaft");
        bColoradoHanceReferenceRun = PlayerRaft->GetActorLabel() ==
            TEXT("RaftSim_ColoradoHance_PlayerRaft");
        bChilkoLavaCanyonReferenceRun = PlayerRaft->GetActorLabel() ==
            TEXT("RaftSim_ChilkoLavaCanyon_PlayerRaft");
        bFutaleufuTerminatorReferenceRun = PlayerRaft->GetActorLabel() ==
            TEXT("RaftSim_FutaleufuTerminator_PlayerRaft");
        Test->TestTrue(
            FString::Printf(
                TEXT("raft rests within depth envelope (z=%.0f)"),
                PlayerRaft->GetActorLocation().Z),
            FMath::Abs(PlayerRaft->GetActorLocation().Z) < 20000.0f);
    }
    else
    {
        Test->AddError(TEXT("River map has no player raft"));
    }

    const bool bUsesSolverOwnedVisibleRiver =
        bPacuareReferenceRun || bColoradoHanceReferenceRun ||
        bChilkoLavaCanyonReferenceRun || bFutaleufuTerminatorReferenceRun;
    int32 LiveSurfaceActorCount = 0;
    for (TActorIterator<ARaftSimWaterSurfaceActor> It(World); It; ++It)
    {
        ++LiveSurfaceActorCount;
        Test->TestEqual(
            TEXT("live surface carrier follows the saved river ownership contract"),
            It->IsLiveSurfaceCarrierEnabled(),
            bUsesSolverOwnedVisibleRiver);
        if (bUsesSolverOwnedVisibleRiver)
        {
            Test->TestTrue(
                TEXT("solver-owned river has visible calm-water coverage"),
                It->GetCalmLiveSurfaceCoverage() >= 0.80f);
            Test->TestTrue(
                TEXT("solver-owned river has visible active-water coverage"),
                It->GetActiveLiveSurfaceCoverage() >=
                    It->GetCalmLiveSurfaceCoverage());
        }
        else
        {
            Test->TestEqual(
                TEXT("authored visible river keeps the live overlay transparent"),
                It->GetActiveLiveSurfaceCoverage(),
                0.0f);
        }
    }
    Test->TestEqual(
        TEXT("river map has exactly one live solver surface actor"),
        LiveSurfaceActorCount,
        1);

    if (bChilkoLavaCanyonReferenceRun || bFutaleufuTerminatorReferenceRun)
    {
        const FName RiverRunTag = bChilkoLavaCanyonReferenceRun
            ? FName(TEXT("RaftSimChilkoLavaCanyonRun"))
            : FName(TEXT("RaftSimFutaleufuTerminatorRun"));
        int32 OpaqueVegetationActorCount = 0;
        int32 OrganicGroundCoverActorCount = 0;
        for (TActorIterator<AActor> It(World); It; ++It)
        {
            if (!(*It)->Tags.Contains(TEXT("RaftSimOpaqueVolumetricVegetation")) ||
                !(*It)->Tags.Contains(RiverRunTag))
            {
                continue;
            }
            Test->TestTrue(
                TEXT("temperate vegetation is explicitly procedural infill"),
                (*It)->Tags.Contains(TEXT("RaftSimProceduralVegetationFallback")));
            Test->TestTrue(
                TEXT("temperate vegetation placement is slope screened"),
                (*It)->Tags.Contains(TEXT("RaftSimSlopeScreenedPlacement")));
            OrganicGroundCoverActorCount +=
                (*It)->Tags.Contains(TEXT("RaftSimOrganicBankGroundCover")) ? 1 : 0;
            ++OpaqueVegetationActorCount;
        }
        Test->TestEqual(
            TEXT("temperate river has four opaque volumetric vegetation forms"),
            OpaqueVegetationActorCount,
            4);
        Test->TestEqual(
            TEXT("temperate river has one organic ground-cover layer"),
            OrganicGroundCoverActorCount,
            1);
    }

    if (bZambeziReferenceRun)
    {
        Test->TestEqual(
            TEXT("Zambezi calm launch keeps the raft upright after all-forward"),
            static_cast<int32>(PlayerRaft->GetRaftMode()),
            static_cast<int32>(ERaftSimRaftMode::Upright));
        Test->TestEqual(
            TEXT("Zambezi calm launch keeps every person in the raft"),
            PlayerRaft->GetSwimmerCount(),
            0);
        Test->TestEqual(
            TEXT("Zambezi calm launch retains four paddlers and one guide"),
            PlayerRaft->GetCrewAvatarCount(),
            5);
        int32 AttachedCrewCount = 0;
        for (TActorIterator<ARaftSimCrewAvatarActor> It(World); It; ++It)
        {
            ARaftSimCrewAvatarActor* Avatar = *It;
            if (Avatar->GetOwner() != PlayerRaft)
            {
                continue;
            }
            Test->TestTrue(
                TEXT("Zambezi seated crew stays attached to the player raft"),
                Avatar->GetAttachParentActor() == PlayerRaft);
            Test->TestTrue(
                TEXT("Zambezi seated crew root stays within the raft envelope"),
                FVector::Dist(Avatar->GetActorLocation(), PlayerRaft->GetActorLocation()) <
                    300.0f);
            Test->TestTrue(
                TEXT("Zambezi seated crew visual transforms remain finite"),
                Avatar->HasFiniteVisualTransforms());
            ++AttachedCrewCount;
        }
        Test->TestEqual(
            TEXT("Zambezi has five attached live crew actors"),
            AttachedCrewCount,
            5);
        int32 ScenarioMarkerCount = 0;
        for (TActorIterator<AActor> It(World); It; ++It)
        {
            if ((*It)->Tags.Contains(TEXT("RaftSimScenarioMarker")) &&
                (*It)->Tags.Contains(TEXT("RaftSimZambeziRun")))
            {
                ++ScenarioMarkerCount;
            }
        }
        Test->TestEqual(
            TEXT("Zambezi reference run retains all 25 rapid markers"),
            ScenarioMarkerCount,
            25);
        int32 RuntimeWaterConfigCount = 0;
        for (TActorIterator<ARaftSimRiverWaterConfig> It(World); It; ++It)
        {
            if ((*It)->GetActorLabel() == TEXT("RaftSim_Zambezi_RuntimeWaterConfig"))
            {
                Test->TestFalse(
                    TEXT("Zambezi preserves globally stationed cooked hydraulics"),
                    (*It)->bRecenterHydraulicCrux);
                Test->TestTrue(
                    TEXT("Zambezi water config records global river-station authority"),
                    (*It)->Tags.Contains(TEXT("RaftSimGlobalRiverStationAuthority")));
                Test->TestTrue(
                    TEXT("Zambezi water config records the safe launch apron"),
                    (*It)->Tags.Contains(TEXT("RaftSimSafeLaunchApron")));
                ++RuntimeWaterConfigCount;
            }
        }
        Test->TestEqual(
            TEXT("Zambezi reference run has one procedural runtime water config"),
            RuntimeWaterConfigCount,
            1);
        int32 BreakingSiteCount = 0;
        if (TActorIterator<ARaftSimWaterSurfaceActor> It(World); It)
        {
            TArray<ARaftSimWaterSurfaceActor::FBreakingSite> BreakingSites;
            It->GetBreakingSites(BreakingSites);
            BreakingSiteCount = BreakingSites.Num();
            Test->TestTrue(
                FString::Printf(
                    TEXT("Zambezi exposes advected rapid foam on the separate masked sheet (%d vertices)"),
                    It->GetVisibleRapidFoamVertexCount()),
                It->GetVisibleRapidFoamVertexCount() > 0);
            Test->TestTrue(
                TEXT("Zambezi rapid-foam presentation is visible when solver foam is active"),
                It->IsRapidFoamMeshVisible());
        }
        Test->TestTrue(
            TEXT("Zambezi start apron activates solver-owned breaking water"),
            BreakingSiteCount > 0);
        if (TActorIterator<ARaftSimWaterVfxActor> It(World); It)
        {
            Test->TestTrue(
                TEXT("Zambezi uses the complete production Niagara water pool"),
                It->IsProductionNiagaraReady());
            Test->TestTrue(
                TEXT("Zambezi emits a camera-local rapid roller"),
                It->GetActiveRapidRollerNiagaraCount() > 0);
            Test->TestTrue(
                TEXT("Zambezi emits camera-local rapid aerosol"),
                It->GetActiveRapidAerosolNiagaraCount() > 0);
        }
        else
        {
            Test->AddError(TEXT("Zambezi did not spawn the live water VFX actor"));
        }
        int32 ConditionedVisualTerrainCount = 0;
        for (TActorIterator<AActor> It(World); It; ++It)
        {
            AActor* Actor = *It;
            if (!Actor->Tags.Contains(TEXT("RaftSimProceduralVisualMorphology")) ||
                !Actor->Tags.Contains(TEXT("RaftSimBatokaWorldAlignedTerrain")))
            {
                continue;
            }
            const UProceduralMeshComponent* Mesh =
                Actor->FindComponentByClass<UProceduralMeshComponent>();
            Test->TestNotNull(TEXT("conditioned Batoka tile has a procedural mesh"), Mesh);
            if (!Mesh)
            {
                continue;
            }
            Test->TestEqual(
                TEXT("conditioned Batoka tile is render-only"),
                Mesh->GetCollisionEnabled(),
                ECollisionEnabled::NoCollision);
            const UMaterialInterface* Material = Mesh->GetMaterial(0);
            Test->TestNotNull(TEXT("conditioned Batoka tile has a material"), Material);
            if (Material)
            {
                Test->TestTrue(
                    TEXT("conditioned Batoka tile uses the world-aligned material"),
                    Material->GetName().Contains(TEXT("BatokaV12_WorldAligned")));
            }
            ++ConditionedVisualTerrainCount;
        }
        Test->TestEqual(
            TEXT("Zambezi reference run has four conditioned visual-terrain tiles"),
            ConditionedVisualTerrainCount,
            4);

        int32 AdaptiveNearFieldTerrainCount = 0;
        int32 ZambeziAtmosphereActorCount = 0;
        int32 AtmosphereSunCount = 0;
        int32 CapturedSkyFillCount = 0;
        int32 DrySeasonSkyCount = 0;
        int32 GorgeHazeCount = 0;
        for (TActorIterator<AActor> It(World); It; ++It)
        {
            AActor* Actor = *It;
            if (Actor->Tags.Contains(TEXT("RaftSimZambeziAdaptiveNearFieldTerrainV1")))
            {
                const UProceduralMeshComponent* Mesh =
                    Actor->FindComponentByClass<UProceduralMeshComponent>();
                Test->TestNotNull(TEXT("adaptive Zambezi bank has a procedural mesh"), Mesh);
                if (Mesh)
                {
                    Test->TestEqual(
                        TEXT("adaptive Zambezi bank is render-only"),
                        Mesh->GetCollisionEnabled(),
                        ECollisionEnabled::NoCollision);
                    Test->TestFalse(
                        TEXT("adaptive Zambezi bank suppresses coarse self-shadow wedges"),
                        Mesh->CastShadow);
                    Test->TestNotNull(
                        TEXT("adaptive Zambezi bank has a source-conditioned material"),
                        Mesh->GetMaterial(0));
                }
                Test->TestTrue(
                    TEXT("adaptive Zambezi bank declares source-conditioned authority"),
                    Actor->Tags.Contains(TEXT("RaftSimSourceConditionedTerrain")));
                Test->TestTrue(
                    TEXT("adaptive Zambezi bank declares bounded procedural infill"),
                    Actor->Tags.Contains(TEXT("RaftSimProceduralInfill")));
                Test->TestTrue(
                    TEXT("adaptive Zambezi bank protects the dry shoreline"),
                    Actor->Tags.Contains(TEXT("RaftSimProtectedDryShoreline")));
                Test->TestTrue(
                    TEXT("adaptive Zambezi bank cannot replace Landscape collision"),
                    Actor->Tags.Contains(TEXT("RaftSimNonCollisionRenderSurface")));
                Test->TestTrue(
                    TEXT("adaptive Zambezi bank records its self-shadow policy"),
                    Actor->Tags.Contains(TEXT("RaftSimNearFieldSelfShadowSuppressed")));
                ++AdaptiveNearFieldTerrainCount;
            }

            if (!Actor->Tags.Contains(TEXT("RaftSimZambeziAtmosphereV1")))
            {
                continue;
            }
            ++ZambeziAtmosphereActorCount;
            AtmosphereSunCount +=
                Actor->Tags.Contains(TEXT("RaftSimAtmosphereSunLight")) ? 1 : 0;
            CapturedSkyFillCount +=
                Actor->Tags.Contains(TEXT("RaftSimCapturedGorgeSkyFill")) ? 1 : 0;
            DrySeasonSkyCount +=
                Actor->Tags.Contains(TEXT("RaftSimSourceAwareDrySeasonSky")) ? 1 : 0;
            GorgeHazeCount +=
                Actor->Tags.Contains(TEXT("RaftSimVolumetricGorgeHaze")) ? 1 : 0;
        }
        Test->TestEqual(
            TEXT("Zambezi reference run has two adaptive near-field banks"),
            AdaptiveNearFieldTerrainCount,
            2);
        Test->TestEqual(
            TEXT("Zambezi reference run has a four-actor atmosphere contract"),
            ZambeziAtmosphereActorCount,
            4);
        Test->TestEqual(TEXT("Zambezi links one atmosphere sun"), AtmosphereSunCount, 1);
        Test->TestEqual(TEXT("Zambezi captures one gorge sky fill"), CapturedSkyFillCount, 1);
        Test->TestEqual(TEXT("Zambezi has one dry-season sky"), DrySeasonSkyCount, 1);
        Test->TestEqual(TEXT("Zambezi has one volumetric gorge haze"), GorgeHazeCount, 1);
        return true;
    }

    if (bPacuareReferenceRun)
    {
        Test->TestTrue(
            TEXT("Pacuare player raft is marked reference-runnable"),
            PlayerRaft->Tags.Contains(TEXT("RaftSimReferenceRunnable")));
        Test->TestTrue(
            TEXT("Pacuare launch keeps the raft upright"),
            PlayerRaft->GetRaftMode() == ERaftSimRaftMode::Upright);
        Test->TestEqual(
            TEXT("Pacuare launch keeps every person in the raft"),
            PlayerRaft->GetSwimmerCount(),
            0);

        int32 RuntimeWaterConfigCount = 0;
        for (TActorIterator<ARaftSimRiverWaterConfig> It(World); It; ++It)
        {
            if ((*It)->GetActorLabel() !=
                TEXT("RaftSim_PacuareUpperHuacas_RuntimeWaterConfig"))
            {
                continue;
            }
            Test->TestEqual(
                TEXT("Pacuare loads the Upper Huacas cooked package"),
                (*It)->CookedFieldsDir,
                FString(TEXT("physics/data/real_world/pacuare_river_costa_rica/"
                             "scenario_upper_huacas/cooked_flow_fields")));
            Test->TestEqual(
                TEXT("Pacuare loads the rain-fed runnable planning band"),
                (*It)->FlowBand,
                FName(TEXT("rainfed_runnable_planning")));
            Test->TestFalse(
                TEXT("Pacuare preserves source station/lateral coordinates"),
                (*It)->bRecenterHydraulicCrux);
            Test->TestEqual(
                TEXT("Pacuare binds the local-world vertical datum map"),
                (*It)->CoordinateMapPath,
                FString(TEXT("physics/data/real_world/pacuare_river_costa_rica/"
                             "terrain/upper_huacas_visual/"
                             "upper_huacas_runtime_coordinate_map.json")));
            Test->TestTrue(
                TEXT("Pacuare Landscape owns runtime terrain"),
                (*It)->bMapProvidesTerrain);
            ++RuntimeWaterConfigCount;
        }
        Test->TestEqual(
            TEXT("Pacuare reference run has one runtime water config"),
            RuntimeWaterConfigCount,
            1);

        int32 CaptureOnlyWaterCount = 0;
        int32 SolverFieldFoamCount = 0;
        for (TActorIterator<AActor> It(World); It; ++It)
        {
            if (!(*It)->Tags.Contains(TEXT("RaftSimCaptureOnlyStaticWater")))
            {
                continue;
            }
            Test->TestTrue(
                TEXT("Pacuare authored capture ribbon is hidden during play"),
                (*It)->IsHidden());
            Test->TestTrue(
                TEXT("Pacuare runtime solver owns gameplay water rendering"),
                (*It)->Tags.Contains(TEXT("RaftSimLiveSolverWaterOwnsRuntimeRendering")));
            if ((*It)->Tags.Contains(TEXT("RaftSimSolverFieldFoam")))
            {
                Test->TestTrue(
                    TEXT("Pacuare authored foam is identified as solver-field visualization"),
                    (*It)->Tags.Contains(
                        TEXT("RaftSimPacuareUpperHuacasSolverVisualization")));
                ++SolverFieldFoamCount;
            }
            ++CaptureOnlyWaterCount;
        }
        Test->TestEqual(
            TEXT("Pacuare has capture-only static water and foam surfaces"),
            CaptureOnlyWaterCount,
            2);
        Test->TestEqual(
            TEXT("Pacuare has one cooked-field-derived capture foam surface"),
            SolverFieldFoamCount,
            1);
        return true;
    }

    if (bColoradoHanceReferenceRun)
    {
        Test->TestTrue(
            TEXT("Colorado Hance player raft is marked reference-runnable"),
            PlayerRaft->Tags.Contains(TEXT("RaftSimReferenceRunnable")));
        Test->TestTrue(
            TEXT("Colorado Hance launch keeps the raft upright"),
            PlayerRaft->GetRaftMode() == ERaftSimRaftMode::Upright);
        Test->TestEqual(
            TEXT("Colorado Hance launch keeps every person in the raft"),
            PlayerRaft->GetSwimmerCount(),
            0);

        int32 RuntimeWaterConfigCount = 0;
        for (TActorIterator<ARaftSimRiverWaterConfig> It(World); It; ++It)
        {
            if ((*It)->GetActorLabel() !=
                TEXT("RaftSim_ColoradoHance_RuntimeWaterConfig"))
            {
                continue;
            }
            Test->TestEqual(
                TEXT("Colorado Hance loads the Hance cooked package"),
                (*It)->CookedFieldsDir,
                FString(TEXT("physics/data/real_world/"
                             "colorado_river_grand_canyon_rowing/"
                             "scenario_hance/cooked_flow_fields")));
            Test->TestEqual(
                TEXT("Colorado Hance loads the moderate release planning band"),
                (*It)->FlowBand,
                FName(TEXT("moderate_release_planning")));
            Test->TestFalse(
                TEXT("Colorado Hance preserves source station/lateral coordinates"),
                (*It)->bRecenterHydraulicCrux);
            Test->TestEqual(
                TEXT("Colorado Hance binds the local-world vertical datum map"),
                (*It)->CoordinateMapPath,
                FString(TEXT("physics/data/real_world/"
                             "colorado_river_grand_canyon_rowing/terrain/"
                             "hance_visual/hance_runtime_coordinate_map.json")));
            Test->TestTrue(
                TEXT("Colorado Hance Landscape owns runtime terrain"),
                (*It)->bMapProvidesTerrain);
            ++RuntimeWaterConfigCount;
        }
        Test->TestEqual(
            TEXT("Colorado Hance reference run has one runtime water config"),
            RuntimeWaterConfigCount,
            1);

        int32 CaptureOnlyWaterCount = 0;
        int32 SolverFieldFoamCount = 0;
        for (TActorIterator<AActor> It(World); It; ++It)
        {
            if (!(*It)->Tags.Contains(TEXT("RaftSimCaptureOnlyStaticWater")))
            {
                continue;
            }
            Test->TestTrue(
                TEXT("Colorado Hance authored capture water is hidden during play"),
                (*It)->IsHidden());
            Test->TestTrue(
                TEXT("Colorado Hance runtime solver owns gameplay water rendering"),
                (*It)->Tags.Contains(
                    TEXT("RaftSimLiveSolverWaterOwnsRuntimeRendering")));
            if ((*It)->Tags.Contains(TEXT("RaftSimSolverFieldFoam")))
            {
                Test->TestTrue(
                    TEXT("Colorado Hance foam is identified as solver-field visualization"),
                    (*It)->Tags.Contains(
                        TEXT("RaftSimColoradoHanceSolverVisualization")));
                ++SolverFieldFoamCount;
            }
            ++CaptureOnlyWaterCount;
        }
        Test->TestEqual(
            TEXT("Colorado Hance has capture-only static water and foam surfaces"),
            CaptureOnlyWaterCount,
            2);
        Test->TestEqual(
            TEXT("Colorado Hance has one cooked-field-derived capture foam surface"),
            SolverFieldFoamCount,
            1);
        return true;
    }

    if (bFutaleufuTerminatorReferenceRun)
    {
        Test->TestTrue(
            TEXT("Futaleufu Terminator player raft is marked reference-runnable"),
            PlayerRaft->Tags.Contains(TEXT("RaftSimReferenceRunnable")));
        Test->TestTrue(
            TEXT("Futaleufu Terminator launch keeps the raft upright"),
            PlayerRaft->GetRaftMode() == ERaftSimRaftMode::Upright);
        Test->TestEqual(
            TEXT("Futaleufu Terminator launch keeps every person in the raft"),
            PlayerRaft->GetSwimmerCount(),
            0);

        int32 RuntimeWaterConfigCount = 0;
        for (TActorIterator<ARaftSimRiverWaterConfig> It(World); It; ++It)
        {
            if ((*It)->GetActorLabel() !=
                TEXT("RaftSim_FutaleufuTerminator_RuntimeWaterConfig"))
            {
                continue;
            }
            Test->TestEqual(
                TEXT("Futaleufu loads the Terminator cooked package"),
                (*It)->CookedFieldsDir,
                FString(TEXT("physics/data/real_world/futaleufu_river_chile/"
                             "scenario_terminator/cooked_flow_fields")));
            Test->TestEqual(
                TEXT("Futaleufu loads the median runnable band"),
                (*It)->FlowBand,
                FName(TEXT("median_runnable")));
            Test->TestFalse(
                TEXT("Futaleufu preserves source station/lateral coordinates"),
                (*It)->bRecenterHydraulicCrux);
            Test->TestEqual(
                TEXT("Futaleufu binds the local-world vertical datum map"),
                (*It)->CoordinateMapPath,
                FString(TEXT("physics/data/real_world/futaleufu_river_chile/terrain/"
                             "terminator_visual/"
                             "terminator_runtime_coordinate_map.json")));
            Test->TestTrue(
                TEXT("Futaleufu Landscape owns runtime terrain"),
                (*It)->bMapProvidesTerrain);
            Test->TestTrue(
                TEXT("Futaleufu solver owns the visible gameplay river"),
                (*It)->bLiveSolverOwnsRuntimeRendering);
            Test->TestTrue(
                TEXT("Futaleufu visible carrier has complete calm-water coverage"),
                (*It)->LiveSurfaceCalmCoverage >= 0.80f);
            Test->TestTrue(
                TEXT("Futaleufu live sky reflection stays restrained"),
                FMath::IsNearlyEqual(
                    (*It)->LiveSkyReflectionStrength, 0.34f, 0.001f));
            Test->TestTrue(
                TEXT("Futaleufu live carrier keeps moving micro-normal response"),
                FMath::IsNearlyEqual(
                    (*It)->LiveRippleStrength, 0.30f, 0.001f));
            Test->TestTrue(
                TEXT("Futaleufu solver foam remains optically legible"),
                FMath::IsNearlyEqual(
                    (*It)->LiveFoamIntensity, 0.68f, 0.001f));
            ++RuntimeWaterConfigCount;
        }
        Test->TestEqual(
            TEXT("Futaleufu Terminator reference run has one runtime water config"),
            RuntimeWaterConfigCount,
            1);

        int32 CaptureOnlyWaterCount = 0;
        int32 SolverFieldFoamCount = 0;
        for (TActorIterator<AActor> It(World); It; ++It)
        {
            if (!(*It)->Tags.Contains(TEXT("RaftSimCaptureOnlyStaticWater")))
            {
                continue;
            }
            Test->TestTrue(
                TEXT("Futaleufu authored capture water is hidden during play"),
                (*It)->IsHidden());
            Test->TestTrue(
                TEXT("Futaleufu runtime solver owns gameplay water rendering"),
                (*It)->Tags.Contains(
                    TEXT("RaftSimLiveSolverWaterOwnsRuntimeRendering")));
            if (!(*It)->Tags.Contains(TEXT("RaftSimSolverFieldFoam")))
            {
                Test->TestTrue(
                    TEXT("Futaleufu capture ribbon uses its isolated Default Lit water"),
                    (*It)->Tags.Contains(TEXT("RaftSimFutaleufuDefaultLitWater")));
                Test->TestTrue(
                    TEXT("Futaleufu capture ribbon records CPU cooked-field color authority"),
                    (*It)->Tags.Contains(TEXT("RaftSimCpuAuthoredCookedFieldColor")));
            }
            if ((*It)->Tags.Contains(TEXT("RaftSimSolverFieldFoam")))
            {
                Test->TestTrue(
                    TEXT("Futaleufu foam is identified as solver-field visualization"),
                    (*It)->Tags.Contains(
                        TEXT("RaftSimFutaleufuTerminatorSolverVisualization")));
                ++SolverFieldFoamCount;
            }
            ++CaptureOnlyWaterCount;
        }
        Test->TestEqual(
            TEXT("Futaleufu has capture-only static water and foam surfaces"),
            CaptureOnlyWaterCount,
            2);
        Test->TestEqual(
            TEXT("Futaleufu has one cooked-field-derived capture foam surface"),
            SolverFieldFoamCount,
            1);

        int32 InterpretedD4RockCount = 0;
        for (TActorIterator<ARaftSimRockObstacleActor> It(World); It; ++It)
        {
            if ((*It)->Tags.Contains(TEXT("RaftSimInterpretedC3Obstacle")) &&
                (*It)->Tags.Contains(TEXT("RaftSimReviewGatedGeometry")) &&
                (*It)->GetContactRadiusM() >= 0.1f)
            {
                ++InterpretedD4RockCount;
            }
        }
        Test->TestEqual(
            TEXT("Futaleufu retains one review-gated interpreted D4 contact"),
            InterpretedD4RockCount,
            1);
        return true;
    }

    if (bChilkoLavaCanyonReferenceRun)
    {
        Test->TestTrue(
            TEXT("Chilko Lava Canyon player raft is marked reference-runnable"),
            PlayerRaft->Tags.Contains(TEXT("RaftSimReferenceRunnable")));
        Test->TestTrue(
            TEXT("Chilko Lava Canyon launch keeps the raft upright"),
            PlayerRaft->GetRaftMode() == ERaftSimRaftMode::Upright);
        Test->TestEqual(
            TEXT("Chilko Lava Canyon launch keeps every person in the raft"),
            PlayerRaft->GetSwimmerCount(),
            0);

        int32 RuntimeWaterConfigCount = 0;
        for (TActorIterator<ARaftSimRiverWaterConfig> It(World); It; ++It)
        {
            if ((*It)->GetActorLabel() !=
                TEXT("RaftSim_ChilkoLavaCanyon_RuntimeWaterConfig"))
            {
                continue;
            }
            Test->TestEqual(
                TEXT("Chilko loads the Lava Canyon cooked package"),
                (*It)->CookedFieldsDir,
                FString(TEXT("physics/data/real_world/chilko_river_lava_canyon/"
                             "scenario_lava_canyon/cooked_flow_fields")));
            Test->TestEqual(
                TEXT("Chilko loads the median runnable band"),
                (*It)->FlowBand,
                FName(TEXT("median_runnable")));
            Test->TestFalse(
                TEXT("Chilko preserves source station/lateral coordinates"),
                (*It)->bRecenterHydraulicCrux);
            Test->TestEqual(
                TEXT("Chilko binds the local-world vertical datum map"),
                (*It)->CoordinateMapPath,
                FString(TEXT("physics/data/real_world/chilko_river_lava_canyon/"
                             "terrain/lava_canyon_visual/"
                             "lava_canyon_runtime_coordinate_map.json")));
            Test->TestTrue(
                TEXT("Chilko Landscape owns runtime terrain"),
                (*It)->bMapProvidesTerrain);
            Test->TestTrue(
                TEXT("Chilko solver owns the visible gameplay river"),
                (*It)->bLiveSolverOwnsRuntimeRendering);
            Test->TestTrue(
                TEXT("Chilko visible carrier has complete calm-water coverage"),
                (*It)->LiveSurfaceCalmCoverage >= 0.80f);
            Test->TestTrue(
                TEXT("Chilko live sky reflection stays restrained"),
                FMath::IsNearlyEqual(
                    (*It)->LiveSkyReflectionStrength, 0.38f, 0.001f));
            Test->TestTrue(
                TEXT("Chilko live carrier keeps moving micro-normal response"),
                FMath::IsNearlyEqual(
                    (*It)->LiveRippleStrength, 0.32f, 0.001f));
            Test->TestTrue(
                TEXT("Chilko solver foam remains optically legible"),
                FMath::IsNearlyEqual(
                    (*It)->LiveFoamIntensity, 0.72f, 0.001f));
            ++RuntimeWaterConfigCount;
        }
        Test->TestEqual(
            TEXT("Chilko Lava Canyon reference run has one runtime water config"),
            RuntimeWaterConfigCount,
            1);

        int32 CaptureOnlyWaterCount = 0;
        int32 SolverFieldFoamCount = 0;
        for (TActorIterator<AActor> It(World); It; ++It)
        {
            if (!(*It)->Tags.Contains(TEXT("RaftSimCaptureOnlyStaticWater")))
            {
                continue;
            }
            Test->TestTrue(
                TEXT("Chilko authored capture water is hidden during play"),
                (*It)->IsHidden());
            if (!(*It)->Tags.Contains(TEXT("RaftSimSolverFieldFoam")))
            {
                Test->TestTrue(
                    TEXT("Chilko capture ribbon uses its isolated Default Lit water"),
                    (*It)->Tags.Contains(TEXT("RaftSimChilkoDefaultLitWater")));
                Test->TestTrue(
                    TEXT("Chilko capture ribbon records CPU cooked-field color authority"),
                    (*It)->Tags.Contains(TEXT("RaftSimCpuAuthoredCookedFieldColor")));
            }
            if ((*It)->Tags.Contains(TEXT("RaftSimSolverFieldFoam")))
            {
                Test->TestTrue(
                    TEXT("Chilko foam is identified as solver-field visualization"),
                    (*It)->Tags.Contains(
                        TEXT("RaftSimChilkoLavaCanyonSolverVisualization")));
                ++SolverFieldFoamCount;
            }
            ++CaptureOnlyWaterCount;
        }
        Test->TestEqual(
            TEXT("Chilko has capture-only static water and foam surfaces"),
            CaptureOnlyWaterCount,
            2);
        Test->TestEqual(
            TEXT("Chilko has one cooked-field-derived capture foam surface"),
            SolverFieldFoamCount,
            1);

        int32 InterpretedD4RockCount = 0;
        for (TActorIterator<ARaftSimRockObstacleActor> It(World); It; ++It)
        {
            if ((*It)->Tags.Contains(TEXT("RaftSimInterpretedC3Obstacle")) &&
                (*It)->Tags.Contains(TEXT("RaftSimReviewGatedGeometry")) &&
                (*It)->GetContactRadiusM() >= 0.1f)
            {
                ++InterpretedD4RockCount;
            }
        }
        Test->TestEqual(
            TEXT("Chilko retains four review-gated interpreted D4 contacts"),
            InterpretedD4RockCount,
            4);
        return true;
    }

    int32 AuthoritativeRockCount = 0;
    for (TActorIterator<ARaftSimRockObstacleActor> It(World); It; ++It)
    {
        if ((*It)->GetContactRadiusM() >= 0.1f)
        {
            ++AuthoritativeRockCount;
        }
    }
    Test->TestEqual(
        TEXT("signature rapid has four serialized D4 rock obstacles"),
        AuthoritativeRockCount,
        4);
    return true;
}

} // namespace

void FRaftSimRiverMapLoadsTest::GetTests(
    TArray<FString>& OutBeautifiedNames, TArray<FString>& OutTestCommands) const
{
    for (const TCHAR* MapPath : GRiverMapPaths)
    {
        if (MapExists(MapPath))
        {
            OutBeautifiedNames.Add(FPackageName::GetShortName(MapPath));
            OutTestCommands.Add(MapPath);
        }
    }
}

bool FRaftSimRiverMapLoadsTest::RunTest(const FString& MapPath)
{
    AutomationOpenMap(MapPath);
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(1.0f));
    if (MapPath.Contains(TEXT("Zambezi")))
    {
        ADD_LATENT_AUTOMATION_COMMAND(FRaftSimStartZambeziLaunchCommand(this));
    }
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(3.0f));
    ADD_LATENT_AUTOMATION_COMMAND(FRaftSimAssertRiverMapCommand(this));
    return true;
}

#endif // WITH_AUTOMATION_TESTS
