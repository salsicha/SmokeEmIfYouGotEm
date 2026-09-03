// P4 test: each generated river map loads a live cooked-field river window (or
// falls back to the dev tank if its fields are not cooked yet) and the raft
// rests on wet, finite water. Runs once per map that exists.

#include "AssetRegistry/AssetRegistryModule.h"
#include "Components/ExponentialHeightFogComponent.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Containers/Set.h"
#include "Engine/StaticMesh.h"
#include "Engine/Texture2D.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Materials/MaterialInterface.h"
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

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimSouthForkFullReachSupportParityTest,
    "RaftSim.P4.SouthForkFullReachSupportParity",
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
        if (It->GetActorLabelView() == TEXT("RaftSim_Zambezi_PlayerRaft"))
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
        bZambeziReferenceRun = PlayerRaft->GetActorLabelView() ==
            TEXT("RaftSim_Zambezi_PlayerRaft");
        bPacuareReferenceRun = PlayerRaft->GetActorLabelView() ==
            TEXT("RaftSim_PacuareUpperHuacas_PlayerRaft");
        bColoradoHanceReferenceRun = PlayerRaft->GetActorLabelView() ==
            TEXT("RaftSim_ColoradoHance_PlayerRaft");
        bChilkoLavaCanyonReferenceRun = PlayerRaft->GetActorLabelView() ==
            TEXT("RaftSim_ChilkoLavaCanyon_PlayerRaft");
        bFutaleufuTerminatorReferenceRun = PlayerRaft->GetActorLabelView() ==
            TEXT("RaftSim_FutaleufuTerminator_PlayerRaft");
        // Sanity envelope against falling through the world or launching
        // skyward. Rivers ride their real-world vertical datum, so the bound
        // must admit legitimate elevations: South Fork rests near z=32155
        // (321 m true elevation), which the former 20000 cm bound rejected
        // even with the raft floating correctly at its put-in (2026-08-13).
        Test->TestTrue(
            FString::Printf(
                TEXT("raft rests within depth envelope (z=%.0f)"),
                PlayerRaft->GetActorLocation().Z),
            FMath::Abs(PlayerRaft->GetActorLocation().Z) < 60000.0f);
    }
    else
    {
        Test->AddError(TEXT("River map has no player raft"));
    }

    if (PlayerRaft)
    {
        const UGameInstance* GI = World->GetGameInstance();
        URaftSimPhysicsBridgeSubsystem* Bridge = GI
            ? GI->GetSubsystem<URaftSimPhysicsBridgeSubsystem>()
            : nullptr;
        URaftSimWaterRuntimeAdapter* Water = Bridge
            ? Bridge->GetWaterRuntime()
            : nullptr;
        FRaftSimWaterSample CenterWater;
        if (Water &&
            Water->SampleRaftSupportSurfaceAtWorldPosition(
                PlayerRaft->GetActorLocation(), CenterWater) &&
            CenterWater.bWet)
        {
            const float DraftBelowSurfaceCm =
                CenterWater.SurfaceHeightMeters * 100.0f -
                PlayerRaft->GetActorLocation().Z;
            Test->TestTrue(
                FString::Printf(
                    TEXT("loaded raft center stays within 45 cm of visible support surface (draft %.1f cm)"),
                    DraftBelowSurfaceCm),
                DraftBelowSurfaceCm < 45.0f);
        }
        if (Water && bColoradoHanceReferenceRun)
        {
            Test->TestTrue(
                TEXT("Colorado Hance couples visible rapid relief into raft support"),
                Water->IsRaftSupportSurfaceEnabled());
            Test->TestTrue(
                TEXT("Colorado Hance support uses the unified-carrier smoothing strength"),
                FMath::IsNearlyEqual(
                    Water->GetRaftSupportSurfaceSmoothingStrength(), 1.0f, 0.001f));
            Test->TestTrue(
                TEXT("Colorado Hance support uses the visible standing-wave scale"),
                FMath::IsNearlyEqual(
                    Water->GetRaftSupportStandingWaveScale(), 0.55f, 0.001f) &&
                FMath::IsNearlyEqual(
                    Water->GetRaftSupportHydraulicReliefScale(), 0.55f, 0.001f));
        }
    }

    const bool bUsesSolverOwnedVisibleRiver =
        bZambeziReferenceRun || bPacuareReferenceRun || bColoradoHanceReferenceRun ||
        bChilkoLavaCanyonReferenceRun || bFutaleufuTerminatorReferenceRun;
    const bool bUsesLegacyStraightRiverCoordinates =
        World->GetMapName().Contains(TEXT("L_Troublemaker"));
    int32 LiveSurfaceActorCount = 0;
    for (TActorIterator<ARaftSimWaterSurfaceActor> It(World); It; ++It)
    {
        ++LiveSurfaceActorCount;
        Test->TestTrue(
            TEXT("runnable river uses the refined authored-river presentation grid"),
            It->IsRiverPresentationGridRefined());
        Test->TestTrue(
            TEXT("runnable river presentation vertices use 0.5 m spacing"),
            FMath::IsNearlyEqual(
                It->GetPresentationVertexSpacingMeters(), 0.5f, 0.001f));
        Test->TestEqual(
            TEXT("runnable river presentation window has the refined vertex count"),
            It->GetSurfaceVertexCount(),
            bUsesLegacyStraightRiverCoordinates ? 160801 : 92833);
        Test->TestEqual(
            TEXT("runnable river presentation window has the refined triangle count"),
            It->GetSurfaceTriangleCount(),
            bUsesLegacyStraightRiverCoordinates ? 320000 : 184320);
        Test->TestEqual(
            TEXT("live surface carrier follows the saved river ownership contract"),
            It->IsLiveSurfaceCarrierEnabled(),
            bUsesSolverOwnedVisibleRiver);
        TArray<ARaftSimWaterSurfaceActor::FBreakingSite> PresentationBreakingSites;
        It->GetBreakingSites(PresentationBreakingSites);
        if (!PresentationBreakingSites.IsEmpty())
        {
            if (It->IsSingleLiveWaterSurfaceEnabled())
            {
                Test->TestFalse(
                    TEXT("single-surface rivers suppress the duplicate roller curtain"),
                    It->IsBreakingRollerVolumeVisible());
                Test->TestEqual(
                    TEXT("single-surface rivers keep roller geometry out of the render path"),
                    It->GetBreakingRollerVolumeTriangleCount(),
                    0);
            }
            else
            {
                const int32 ExpectedConnectedCurtainTriangles =
                    FMath::Min(PresentationBreakingSites.Num(), 3) * 1044;
                const int32 ExpectedConnectedCurtainVertices =
                    FMath::Min(PresentationBreakingSites.Num(), 3) * 570;
                Test->TestTrue(
                    TEXT("solver breaking sites retain a connected production water curtain"),
                    It->IsBreakingRollerVolumeVisible());
                Test->TestEqual(
                    TEXT("connected curtain uses one bounded two-skin crest envelope at the three strongest sites"),
                    It->GetBreakingRollerVolumeTriangleCount(),
                    ExpectedConnectedCurtainTriangles);
                Test->TestEqual(
                    TEXT("connected crest envelope retains two coherent skins per selected site"),
                    It->GetBreakingRollerVolumeVertexCount(),
                    ExpectedConnectedCurtainVertices);
                Test->TestTrue(
                    TEXT("connected crest envelope has visible but bounded full thickness"),
                    It->GetBreakingRollerVolumeMaximumThicknessCm() > 10.0f &&
                        It->GetBreakingRollerVolumeMaximumThicknessCm() <= 40.01f);
            }
        }
        if (bUsesSolverOwnedVisibleRiver)
        {
            if (bZambeziReferenceRun || bPacuareReferenceRun ||
                bColoradoHanceReferenceRun ||
                bChilkoLavaCanyonReferenceRun ||
                bFutaleufuTerminatorReferenceRun)
            {
                Test->TestTrue(
                    TEXT("accepted transmitting-water river enables the wet-cell-clipped optical core"),
                    It->IsLiveVolumeCoreEnabled());
                Test->TestTrue(
                    TEXT("accepted transmitting-water optical core has visible wet-cell triangles"),
                    It->IsLiveVolumeCoreVisible() &&
                        It->GetLiveVolumeCoreTriangleCount() > 0);
                Test->TestTrue(
                    TEXT("accepted transmitting-water detail skin stays below opaque-sheet coverage"),
                    It->GetCalmLiveSurfaceCoverage() < 0.10f);
            }
            else
            {
                Test->TestTrue(
                    TEXT("solver-owned river has visible calm-water coverage"),
                    It->GetCalmLiveSurfaceCoverage() >= 0.80f);
                Test->TestFalse(
                    TEXT("non-pilot rivers retain their reviewed water carrier"),
                    It->IsLiveVolumeCoreEnabled());
            }
            Test->TestTrue(
                TEXT("solver-owned river has visible active-water coverage"),
                It->GetActiveLiveSurfaceCoverage() >=
                    It->GetCalmLiveSurfaceCoverage());
            if (bColoradoHanceReferenceRun)
            {
                Test->TestTrue(
                    TEXT("Colorado Hance live mesh and raft support share surface smoothing"),
                    It->IsLivePresentationSurfaceSmoothingEnabled());
                Test->TestTrue(
                    TEXT("Colorado Hance live smoothing matches the unified carrier"),
                    FMath::IsNearlyEqual(
                        It->GetLivePresentationSurfaceSmoothingStrength(),
                        1.0f,
                        0.001f));
            }
        }
        else
        {
            Test->TestTrue(
                TEXT("authored water has no duplicate calm skin and lets breaking crests reach full coverage"),
                FMath::IsNearlyEqual(
                    It->GetCalmLiveSurfaceCoverage(), 0.0f, 0.001f) &&
                    FMath::IsNearlyEqual(
                        It->GetActiveLiveSurfaceCoverage(), 1.0f, 0.001f));
        }

        UProceduralMeshComponent* LiveSurfaceMesh = nullptr;
        TArray<UProceduralMeshComponent*> WaterMeshes;
        It->GetComponents<UProceduralMeshComponent>(WaterMeshes);
        for (UProceduralMeshComponent* Candidate : WaterMeshes)
        {
            if (Candidate && Candidate->GetFName() == TEXT("SurfaceMesh"))
            {
                LiveSurfaceMesh = Candidate;
                break;
            }
        }
        Test->TestNotNull(TEXT("live water exposes its velocity-carrying mesh"), LiveSurfaceMesh);
        const FProcMeshSection* LiveSurfaceSection = LiveSurfaceMesh
            ? LiveSurfaceMesh->GetProcMeshSection(0)
            : nullptr;
        int32 NonzeroSolverVelocityVertexCount = 0;
        bool bAllSolverVelocityUvsFinite = true;
        if (LiveSurfaceSection)
        {
            for (const FProcMeshVertex& Vertex : LiveSurfaceSection->ProcVertexBuffer)
            {
                bAllSolverVelocityUvsFinite &=
                    FMath::IsFinite(Vertex.UV1.X) && FMath::IsFinite(Vertex.UV1.Y);
                NonzeroSolverVelocityVertexCount +=
                    Vertex.UV1.SizeSquared() > 0.0025f ? 1 : 0;
            }
        }
        Test->TestTrue(TEXT("solver velocity UV1 remains finite"),
            bAllSolverVelocityUvsFinite);
        Test->TestTrue(TEXT("live water mesh receives nonzero solver velocity in UV1"),
            NonzeroSolverVelocityVertexCount > 0);
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
        int32 NearBankEcologyActorCount = 0;
        int32 NearBankEcologyInstanceCount = 0;
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
            Test->TestTrue(
                TEXT("temperate vegetation uses deterministic bank ecology V4"),
                (*It)->Tags.Contains(
                    TEXT("RaftSimTemperateBankEcologyV4")));
            Test->TestTrue(
                TEXT("temperate vegetation records a morphology variant family"),
                (*It)->Tags.Contains(
                    TEXT("RaftSimTemperateMorphologyVariantFamily")));
            OrganicGroundCoverActorCount +=
                (*It)->Tags.Contains(TEXT("RaftSimOrganicBankGroundCover")) ? 1 : 0;
            if ((*It)->Tags.Contains(TEXT("RaftSimTemperateNearBankEcologyV4")))
            {
                ++NearBankEcologyActorCount;
                if (const UHierarchicalInstancedStaticMeshComponent* Instances =
                        (*It)->FindComponentByClass<
                            UHierarchicalInstancedStaticMeshComponent>())
                {
                    NearBankEcologyInstanceCount += Instances->GetInstanceCount();
                    Test->TestEqual(
                        TEXT("near-bank ecology remains non-colliding"),
                        Instances->GetCollisionEnabled(),
                        ECollisionEnabled::NoCollision);
                }
                Test->TestTrue(
                    TEXT("near-bank ecology is source Landscape grounded"),
                    (*It)->Tags.Contains(TEXT("RaftSimSourceLandscapeGrounded")));
                Test->TestTrue(
                    TEXT("near-bank ecology stays outside the solver strip"),
                    (*It)->Tags.Contains(TEXT("RaftSimOutsideProtectedSolverStrip")));
            }
            ++OpaqueVegetationActorCount;
        }
        Test->TestEqual(
            TEXT("temperate river has eight opaque volumetric vegetation morphologies"),
            OpaqueVegetationActorCount,
            8);
        Test->TestEqual(
            TEXT("temperate river has two organic ground-cover morphologies"),
            OrganicGroundCoverActorCount,
            2);
        Test->TestEqual(
            TEXT("temperate river has four near-bank grass/forb/shrub morphology actors"),
            NearBankEcologyActorCount,
            4);
        Test->TestTrue(
            TEXT("temperate near-bank ecology retains at least 1600 placed instances"),
            NearBankEcologyInstanceCount >= 1600);

        if (bFutaleufuTerminatorReferenceRun)
        {
            int32 ScannedUnderstoryActorCount = 0;
            int32 ScannedUnderstoryInstanceCount = 0;
            for (TActorIterator<AActor> It(World); It; ++It)
            {
                AActor* Actor = *It;
                if (!Actor ||
                    !Actor->Tags.Contains(
                        TEXT("RaftSimFutaleufuScannedNearBankUnderstoryV1")) ||
                    !Actor->Tags.Contains(RiverRunTag))
                {
                    continue;
                }
                ++ScannedUnderstoryActorCount;
                const UHierarchicalInstancedStaticMeshComponent* Instances =
                    Actor->FindComponentByClass<
                        UHierarchicalInstancedStaticMeshComponent>();
                Test->TestNotNull(
                    TEXT("Futaleufu scanned understory owns an HISM component"),
                    Instances);
                if (Instances)
                {
                    ScannedUnderstoryInstanceCount += Instances->GetInstanceCount();
                    Test->TestEqual(
                        TEXT("Futaleufu scanned understory remains non-colliding"),
                        Instances->GetCollisionEnabled(),
                        ECollisionEnabled::NoCollision);
                }
                Test->TestTrue(
                    TEXT("Futaleufu scanned understory is source Landscape grounded"),
                    Actor->Tags.Contains(TEXT("RaftSimSourceLandscapeGrounded")));
                Test->TestTrue(
                    TEXT("Futaleufu scanned understory stays outside the solver strip"),
                    Actor->Tags.Contains(
                        TEXT("RaftSimOutsideProtectedSolverStrip")));
                Test->TestTrue(
                    TEXT("Futaleufu scanned understory records CC0 analog authority"),
                    Actor->Tags.Contains(
                        TEXT("RaftSimRightsReviewedCC0UnderstoryAnalog")));
                Test->TestTrue(
                    TEXT("Futaleufu scanned understory disclaims species authority"),
                    Actor->Tags.Contains(
                        TEXT("RaftSimNoSpeciesOrEcologyAuthority")));
                Test->TestFalse(
                    TEXT("Futaleufu scanned understory is not promoted as canopy"),
                    Actor->Tags.Contains(TEXT("RaftSimOpaqueVolumetricVegetation")));
            }
            Test->TestEqual(
                TEXT("Futaleufu has seven scanned small-fir and fern actors"),
                ScannedUnderstoryActorCount,
                7);
            Test->TestTrue(
                TEXT("Futaleufu retains at least 1200 scanned near-bank instances"),
                ScannedUnderstoryInstanceCount >= 1200);
        }

        int32 WaterlineStructureActorCount = 0;
        int32 WaterlineStructureInstanceCount = 0;
        for (TActorIterator<AActor> It(World); It; ++It)
        {
            AActor* Actor = *It;
            if (!Actor ||
                !Actor->Tags.Contains(
                    TEXT("RaftSimTemperateWaterlineStructureV1")) ||
                !Actor->Tags.Contains(RiverRunTag))
            {
                continue;
            }
            const UHierarchicalInstancedStaticMeshComponent* Instances =
                Actor->FindComponentByClass<
                    UHierarchicalInstancedStaticMeshComponent>();
            Test->TestNotNull(
                TEXT("temperate waterline structure actor has one HISM"),
                Instances);
            if (!Instances)
            {
                continue;
            }
            Test->TestEqual(
                TEXT("temperate waterline structure remains non-colliding"),
                Instances->GetCollisionEnabled(),
                ECollisionEnabled::NoCollision);
            Test->TestTrue(
                TEXT("temperate waterline structure remains outside the solver strip"),
                Actor->Tags.Contains(
                    TEXT("RaftSimOutsideProtectedSolverStrip")) &&
                    Instances->ComponentTags.Contains(
                        TEXT("RaftSimOutsideProtectedSolverStrip")));
            Test->TestTrue(
                TEXT("temperate waterline structure disclaims measured geology and hydraulics"),
                Actor->Tags.Contains(
                    TEXT("RaftSimGenericRockAnalogNoLithologyAuthority")) &&
                    Actor->Tags.Contains(
                        TEXT("RaftSimPresentationOnlyNoHydraulicAuthority")) &&
                    Actor->Tags.Contains(
                        TEXT("RaftSimProceduralSourceGapFill")));
            Test->TestTrue(
                TEXT("temperate waterline structure is source-Landscape grounded"),
                Actor->Tags.Contains(
                    TEXT("RaftSimSourceLandscapeGrounded")));
            WaterlineStructureInstanceCount += Instances->GetInstanceCount();
            ++WaterlineStructureActorCount;
        }
        Test->TestEqual(
            TEXT("temperate river has six waterline rock morphology variants"),
            WaterlineStructureActorCount,
            6);
        Test->TestTrue(
            TEXT("temperate river has dense organic waterline structure"),
            WaterlineStructureInstanceCount >= 1250);

        if (bChilkoLavaCanyonReferenceRun)
        {
            int32 OrganicShorelineActorCount = 0;
            int32 OrganicShorelineGravelActorCount = 0;
            int32 OrganicShorelineGravelInstanceCount = 0;
            int32 OrganicShorelineGroundCoverActorCount = 0;
            int32 OrganicShorelineGroundCoverInstanceCount = 0;
            for (TActorIterator<AActor> It(World); It; ++It)
            {
                AActor* Actor = *It;
                if (!Actor ||
                    !Actor->Tags.Contains(
                        TEXT("RaftSimChilkoOrganicShorelineV2")) ||
                    !Actor->Tags.Contains(
                        TEXT("RaftSimChilkoLavaCanyonRun")))
                {
                    continue;
                }
                const UHierarchicalInstancedStaticMeshComponent* Instances =
                    Actor->FindComponentByClass<
                        UHierarchicalInstancedStaticMeshComponent>();
                Test->TestNotNull(
                    TEXT("Chilko organic shoreline actor has one HISM"),
                    Instances);
                if (!Instances)
                {
                    continue;
                }
                Test->TestEqual(
                    TEXT("Chilko organic shoreline remains non-colliding"),
                    Instances->GetCollisionEnabled(),
                    ECollisionEnabled::NoCollision);
                Test->TestTrue(
                    TEXT("Chilko organic shoreline stays outside the solver strip"),
                    Actor->Tags.Contains(
                        TEXT("RaftSimOutsideProtectedSolverStrip")) &&
                        Instances->ComponentTags.Contains(
                            TEXT("RaftSimOutsideProtectedSolverStrip")));
                Test->TestTrue(
                    TEXT("Chilko organic shoreline is source-Landscape grounded"),
                    Actor->Tags.Contains(
                        TEXT("RaftSimSourceLandscapeGrounded")));
                Test->TestTrue(
                    TEXT("Chilko organic shoreline disclaims hydraulic authority"),
                    Actor->Tags.Contains(
                        TEXT("RaftSimPresentationOnlyNoHydraulicAuthority")) &&
                        Actor->Tags.Contains(
                            TEXT("RaftSimProceduralSourceGapFill")));
                Test->TestTrue(
                    TEXT("Chilko organic shoreline retains the V3 naturalism contract"),
                    Actor->Tags.Contains(
                        TEXT("RaftSimChilkoShorelineNaturalismV3")) &&
                        Instances->ComponentTags.Contains(
                            TEXT("RaftSimChilkoShorelineNaturalismV3")));
                if (Actor->Tags.Contains(
                        TEXT("RaftSimChilkoShorelineGravel")))
                {
                    Test->TestTrue(
                        TEXT("Chilko shoreline gravel disclaims lithology authority"),
                        Actor->Tags.Contains(
                            TEXT("RaftSimGenericRockAnalogNoLithologyAuthority")));
                    Test->TestTrue(
                        TEXT("Chilko shoreline gravel uses the V3 sorted scale range"),
                        Actor->Tags.Contains(
                            TEXT("RaftSimChilkoSortedGravelScaleV3")));
                    OrganicShorelineGravelInstanceCount +=
                        Instances->GetInstanceCount();
                    ++OrganicShorelineGravelActorCount;
                }
                if (Actor->Tags.Contains(
                        TEXT("RaftSimChilkoShorelineGroundCover")))
                {
                    Test->TestTrue(
                        TEXT("Chilko shoreline ground cover disclaims ecology authority"),
                        Actor->Tags.Contains(
                            TEXT("RaftSimNoSpeciesOrEcologyAuthority")));
                    Test->TestFalse(
                        TEXT("Chilko shoreline ground cover suppresses self-shadowing"),
                        Instances->CastShadow);
                    Test->TestTrue(
                        TEXT("Chilko shoreline ground cover keeps its muted V3 tag"),
                        Actor->Tags.Contains(
                            TEXT("RaftSimChilkoMutedGroundCoverV3")) &&
                            Instances->ComponentTags.Contains(
                                TEXT("RaftSimChilkoMutedGroundCoverV3")));
                    const UMaterialInterface* GroundCoverMaterial =
                        Instances->GetMaterial(0);
                    Test->TestTrue(
                        TEXT("Chilko shoreline ground cover uses its river-local material"),
                        GroundCoverMaterial &&
                            GroundCoverMaterial->GetPathName().Contains(
                                TEXT("MI_RaftSim_Chilko_MutedGroundCoverV3")));
                    OrganicShorelineGroundCoverInstanceCount +=
                        Instances->GetInstanceCount();
                    ++OrganicShorelineGroundCoverActorCount;
                }
                ++OrganicShorelineActorCount;
            }
            Test->TestEqual(
                TEXT("Chilko organic shoreline has eight dedicated morphology actors"),
                OrganicShorelineActorCount,
                8);
            Test->TestEqual(
                TEXT("Chilko shoreline has six gravel morphology actors"),
                OrganicShorelineGravelActorCount,
                6);
            Test->TestTrue(
                TEXT("Chilko shoreline retains at least 6800 gravel instances"),
                OrganicShorelineGravelInstanceCount >= 6800);
            Test->TestEqual(
                TEXT("Chilko shoreline has two short ground-cover morphologies"),
                OrganicShorelineGroundCoverActorCount,
                2);
            Test->TestTrue(
                TEXT("Chilko shoreline retains at least 7900 ground-cover instances"),
                OrganicShorelineGroundCoverInstanceCount >= 7900);
        }
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
            if ((*It)->GetActorLabelView() == TEXT("RaftSim_Zambezi_RuntimeWaterConfig"))
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
                Test->TestTrue(
                    TEXT("Zambezi solver owns the visible gameplay river"),
                    (*It)->bLiveSolverOwnsRuntimeRendering);
                Test->TestTrue(
                    TEXT("Zambezi enables the wet-cell-clipped transmitting core"),
                    (*It)->bEnableLiveSolverVolumeCore);
                Test->TestTrue(
                    TEXT("Zambezi config binds river-local transmitting water"),
                    (*It)->LiveVolumeCoreMaterialOverride &&
                        (*It)->LiveVolumeCoreMaterialOverride->GetPathName().Contains(
                            TEXT("MI_RaftSim_ZambeziBatoka_LiveVolumeWaterV2")));
                Test->TestTrue(
                    TEXT("Zambezi config binds its first-party flow normal"),
                    (*It)->LiveWaterFlowNormalTexture &&
                        (*It)->LiveWaterFlowNormalTexture->GetPathName().Contains(
                            TEXT("T_RaftSim_ZambeziBatokaWaterV1_FlowNormal")));
                Test->TestTrue(
                    TEXT("Zambezi config binds solver-masked foam lace"),
                    (*It)->LiveWaterFoamLaceTexture &&
                        (*It)->LiveWaterFoamLaceTexture->GetPathName().Contains(
                            TEXT("T_RaftSim_ZambeziBatokaWaterV1_FoamLace")));
                Test->TestTrue(
                    TEXT("Zambezi live detail skin cannot become an opaque sheet"),
                    FMath::IsNearlyZero(
                        (*It)->LiveSurfaceCalmCoverage, 0.001f) &&
                        FMath::IsNearlyEqual(
                            (*It)->LiveSurfaceActiveCoverage,
                            0.06f,
                            0.001f));
                Test->TestTrue(
                    TEXT("Zambezi V18 keeps a rough localized reflection response"),
                    FMath::IsNearlyEqual(
                        (*It)->LiveSurfaceRoughness, 0.66f, 0.001f) &&
                        FMath::IsNearlyEqual(
                            (*It)->LiveSurfaceSpecular, 0.15f, 0.001f) &&
                        FMath::IsNearlyEqual(
                            (*It)->LiveSkyReflectionStrength, 0.055f, 0.001f) &&
                        FMath::IsNearlyEqual(
                            (*It)->LiveRippleStrength, 0.48f, 0.001f));
                Test->TestTrue(
                    TEXT("Zambezi uses shared render/support surface smoothing"),
                    (*It)->bEnableLivePresentationSurfaceSmoothing &&
                        FMath::IsNearlyEqual(
                            (*It)->LivePresentationSurfaceSmoothingStrength,
                            0.62f,
                            0.001f));
                Test->TestTrue(
                    TEXT("Zambezi feathers the optical body across three bank cells"),
                    FMath::IsNearlyEqual(
                        (*It)->LiveSurfaceBankBlendMeters,
                        7.5f,
                        0.001f));
                Test->TestTrue(
                    TEXT("Zambezi live-water tags disclaim solver mutation"),
                    (*It)->Tags.Contains(TEXT("RaftSimZambeziTransmittingWaterV2")) &&
                        (*It)->Tags.Contains(
                            TEXT("RaftSimOpacityFeatheredVolumeEdgeV2")) &&
                        (*It)->Tags.Contains(TEXT("RaftSimRestrainedSolarGlareV2")) &&
                        (*It)->Tags.Contains(
                            TEXT("RaftSimZambeziLocalizedReflectionWaterV18")) &&
                        (*It)->Tags.Contains(TEXT("RaftSimSolverMaskedFoamLace")) &&
                        (*It)->Tags.Contains(TEXT("RaftSimNoSolverStateMutation")));
                ++RuntimeWaterConfigCount;
            }
        }
        Test->TestEqual(
            TEXT("Zambezi reference run has one procedural runtime water config"),
            RuntimeWaterConfigCount,
            1);
        int32 CaptureOnlyStaticWaterCount = 0;
        for (TActorIterator<AActor> It(World); It; ++It)
        {
            if (!(*It)->Tags.Contains(TEXT("RaftSimCaptureOnlyStaticWater")))
            {
                continue;
            }
            Test->TestTrue(
                TEXT("Zambezi authored capture water is hidden during play"),
                (*It)->IsHidden());
            Test->TestTrue(
                TEXT("Zambezi static water records live-solver ownership"),
                (*It)->Tags.Contains(
                    TEXT("RaftSimLiveSolverWaterOwnsRuntimeRendering")));
            ++CaptureOnlyStaticWaterCount;
        }
        Test->TestTrue(
            TEXT("Zambezi retains capture-only static water for editor review"),
            CaptureOnlyStaticWaterCount >= 1);
        int32 BreakingSiteCount = 0;
        if (TActorIterator<ARaftSimWaterSurfaceActor> It(World); It)
        {
            TArray<ARaftSimWaterSurfaceActor::FBreakingSite> BreakingSites;
            It->GetBreakingSites(BreakingSites);
            BreakingSiteCount = BreakingSites.Num();
            Test->TestTrue(
                FString::Printf(
                    TEXT("Zambezi retains advected foam data for the single carrier (%d vertices)"),
                    It->GetVisibleRapidFoamVertexCount()),
                It->GetVisibleRapidFoamVertexCount() > 0);
            Test->TestFalse(
                TEXT("Zambezi does not show a separate rapid-foam surface"),
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
            Test->TestEqual(
                TEXT("Zambezi emits a bounded multi-site rapid roller field"),
                It->GetActiveRapidRollerNiagaraCount(),
                6);
            Test->TestEqual(
                TEXT("Zambezi emits a bounded multi-site rapid aerosol field"),
                It->GetActiveRapidAerosolNiagaraCount(),
                6);
            Test->TestEqual(
                TEXT("Zambezi emits fine ballistic spray from the same solver-owned crests"),
                It->GetActiveRapidCrestSprayNiagaraCount(),
                6);
            Test->TestEqual(
                TEXT("Zambezi three-scale rapid particle pools cover the same sites"),
                It->GetActiveRapidCrestSprayNiagaraCount(),
                It->GetActiveRapidRollerNiagaraCount());
            Test->TestEqual(
                TEXT("Zambezi aerosol and crest-spray pools cover the same sites"),
                It->GetActiveRapidAerosolNiagaraCount(),
                It->GetActiveRapidCrestSprayNiagaraCount());
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
            Test->TestTrue(
                TEXT("conditioned Batoka tile records the V18 exposure-safe scarp pass"),
                Actor->Tags.Contains(
                    TEXT("RaftSimBatokaExposureSafeScarpV18")));
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
        int32 AdaptiveNearFieldVertexCount = 0;
        int32 AdaptiveWetBankVertexCount = 0;
        int32 RunnableLaunchTalusActorCount = 0;
        int32 RunnableLaunchTalusInstanceCount = 0;
        int32 RunnableLaunchTalusWaterlineCount = 0;
        int32 ZambeziAtmosphereActorCount = 0;
        int32 AtmosphereSunCount = 0;
        int32 CapturedSkyFillCount = 0;
        int32 DrySeasonSkyCount = 0;
        int32 GorgeHazeCount = 0;
        for (TActorIterator<AActor> It(World); It; ++It)
        {
            AActor* Actor = *It;
            if (Actor->Tags.Contains(TEXT("RaftSimZambeziAdaptiveNearFieldTerrainV2")))
            {
                UProceduralMeshComponent* Mesh =
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
                    if (const FProcMeshSection* Section = Mesh->GetProcMeshSection(0))
                    {
                        AdaptiveNearFieldVertexCount +=
                            Section->ProcVertexBuffer.Num();
                        for (const FProcMeshVertex& Vertex :
                             Section->ProcVertexBuffer)
                        {
                            AdaptiveWetBankVertexCount +=
                                Vertex.Color.R > 5 ? 1 : 0;
                        }
                    }
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
                Test->TestTrue(
                    TEXT("adaptive Zambezi bank records its irregular topology contract"),
                    Actor->Tags.Contains(TEXT("RaftSimIrregularPlanarTopologyV2")));
                Test->TestTrue(
                    TEXT("adaptive Zambezi bank records its geomorphic relief contract"),
                    Actor->Tags.Contains(TEXT("RaftSimDomainWarpedGeomorphicReliefV2")));
                Test->TestTrue(
                    TEXT("adaptive Zambezi bank binds the conditioned wet-bank treatment"),
                    Actor->Tags.Contains(TEXT("RaftSimConditionedWaterlineWetBankV1")) &&
                        Actor->Tags.Contains(TEXT("RaftSimVertexRedWetBankMask")));
                Test->TestTrue(
                    TEXT("adaptive Zambezi wet bank disclaims measured authority"),
                    Actor->Tags.Contains(
                        TEXT("RaftSimProceduralWetBankNoMeasuredAuthority")));
                ++AdaptiveNearFieldTerrainCount;
            }

            if (Actor->Tags.Contains(TEXT("RaftSimRunnableLaunchTalusV1")))
            {
                const UHierarchicalInstancedStaticMeshComponent* Talus =
                    Actor->FindComponentByClass<
                        UHierarchicalInstancedStaticMeshComponent>();
                Test->TestNotNull(
                    TEXT("Zambezi launch talus actor has one HISM"),
                    Talus);
                if (Talus)
                {
                    Test->TestEqual(
                        TEXT("Zambezi launch talus is presentation-only"),
                        Talus->GetCollisionEnabled(),
                        ECollisionEnabled::NoCollision);
                    Test->TestTrue(
                        TEXT("Zambezi launch talus retains grounded rock shadows"),
                        Talus->CastShadow);
                    Test->TestTrue(
                        TEXT("Zambezi launch talus uses a reviewed rock mesh"),
                        Talus->GetStaticMesh() &&
                            Talus->GetStaticMesh()->GetPathName().Contains(
                                TEXT("RockMossSet01")));
                    Test->TestTrue(
                        TEXT("Zambezi launch talus uses its specific basalt-analog material"),
                        Talus->GetMaterial(0) &&
                            Talus->GetMaterial(0)->GetPathName().Contains(
                                TEXT("MI_RaftSim_Zambezi_BasaltTalusV1")));
                    Test->TestEqual(
                        TEXT("Zambezi launch talus reserves one waterline data channel"),
                        Talus->NumCustomDataFloats,
                        1);
                    Test->TestEqual(
                        TEXT("Every Zambezi launch talus instance has one waterline value"),
                        Talus->PerInstanceSMCustomData.Num(),
                        Talus->GetInstanceCount());
                    for (const float WaterlineZ : Talus->PerInstanceSMCustomData)
                    {
                        if (FMath::IsFinite(WaterlineZ) && WaterlineZ > -1.0e6f)
                        {
                            ++RunnableLaunchTalusWaterlineCount;
                        }
                    }
                    RunnableLaunchTalusInstanceCount += Talus->GetInstanceCount();
                }
                Test->TestTrue(
                    TEXT("Zambezi launch talus declares its basalt-analog retone"),
                    Actor->Tags.Contains(
                        TEXT("RaftSimZambeziBasaltAnalogMaterialV1")) &&
                        Actor->Tags.Contains(
                            TEXT("RaftSimProjectOwnedMineralRetone")));
                Test->TestTrue(
                    TEXT("Zambezi launch talus declares a generic visual analog"),
                    Actor->Tags.Contains(
                        TEXT("RaftSimGenericRockAnalogNoLithologyAuthority")));
                Test->TestTrue(
                    TEXT("Zambezi launch talus cannot replace Landscape collision"),
                    Actor->Tags.Contains(TEXT("RaftSimNonCollisionRenderSurface")));
                Test->TestTrue(
                    TEXT("Zambezi launch talus has no hydraulic authority"),
                    Actor->Tags.Contains(
                        TEXT("RaftSimPresentationOnlyNoHydraulicAuthority")));
                Test->TestTrue(
                    TEXT("Zambezi launch talus binds a per-instance conditioned waterline"),
                    Actor->Tags.Contains(TEXT("RaftSimConditionedWaterlineWetBankV1")) &&
                        Actor->Tags.Contains(
                            TEXT("RaftSimPerInstanceConditionedWaterline")));
                Test->TestTrue(
                    TEXT("Zambezi talus wetness disclaims measured authority"),
                    Actor->Tags.Contains(
                        TEXT("RaftSimProceduralWetBankNoMeasuredAuthority")));
                ++RunnableLaunchTalusActorCount;
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
        Test->TestTrue(
            TEXT("Zambezi adaptive terrain carries a visible but bounded wet-bank mask"),
            AdaptiveWetBankVertexCount > 0 &&
                AdaptiveWetBankVertexCount < AdaptiveNearFieldVertexCount);
        Test->TestEqual(
            TEXT("Zambezi reference run has six launch-talus HISM actors"),
            RunnableLaunchTalusActorCount,
            6);
        Test->TestEqual(
            TEXT("Zambezi reference run has 360 launch-talus rock analogs"),
            RunnableLaunchTalusInstanceCount,
            360);
        Test->TestEqual(
            TEXT("Every Zambezi launch-talus rock has a finite conditioned waterline"),
            RunnableLaunchTalusWaterlineCount,
            360);
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

        int32 HumidAtmosphereActorCount = 0;
        int32 HumidityDirectionalLightCount = 0;
        int32 HumiditySkyFillCount = 0;
        int32 HumidAerialPerspectiveCount = 0;
        int32 LayeredHumidityCount = 0;
        for (TActorIterator<AActor> It(World); It; ++It)
        {
            AActor* Actor = *It;
            if (!Actor ||
                !Actor->Tags.Contains(
                    TEXT("RaftSimPacuareHumidAtmosphereV1")))
            {
                continue;
            }
            ++HumidAtmosphereActorCount;
            HumidityDirectionalLightCount += Actor->Tags.Contains(
                TEXT("RaftSimHumidityDirectionalLight")) ? 1 : 0;
            HumiditySkyFillCount += Actor->Tags.Contains(
                TEXT("RaftSimHumiditySkyFill")) ? 1 : 0;
            HumidAerialPerspectiveCount += Actor->Tags.Contains(
                TEXT("RaftSimHumidAerialPerspective")) ? 1 : 0;
            if (Actor->Tags.Contains(
                    TEXT("RaftSimLayeredRainforestHumidity")))
            {
                const UExponentialHeightFogComponent* FogComponent =
                    Actor->FindComponentByClass<
                        UExponentialHeightFogComponent>();
                Test->TestNotNull(
                    TEXT("Pacuare humidity actor has a height-fog component"),
                    FogComponent);
                if (FogComponent)
                {
                    Test->AddInfo(FString::Printf(
                        TEXT("Pacuare humidity runtime values: density=%.7f volumetric=%d max_opacity=%.4f start_cm=%.2f second_density=%.7f second_offset_cm=%.2f second_falloff=%.4f"),
                        FogComponent->FogDensity,
                        FogComponent->bEnableVolumetricFog ? 1 : 0,
                        FogComponent->FogMaxOpacity,
                        FogComponent->StartDistance,
                        FogComponent->SecondFogData.FogDensity,
                        FogComponent->SecondFogData.FogHeightOffset,
                        FogComponent->SecondFogData.FogHeightFalloff));
                    Test->TestTrue(
                        TEXT("Pacuare humidity uses the reviewed fog density"),
                        FMath::IsNearlyEqual(
                            FogComponent->FogDensity, 0.0075f, 0.0001f));
                    Test->TestTrue(
                        TEXT("Pacuare humidity avoids rejected volumetric occlusion"),
                        !FogComponent->bEnableVolumetricFog);
                    Test->TestTrue(
                        TEXT("Pacuare humidity keeps a bounded opacity"),
                        FMath::IsNearlyEqual(
                            FogComponent->FogMaxOpacity, 0.62f, 0.001f));
                    Test->TestTrue(
                        TEXT("Pacuare humidity begins beyond the guide camera"),
                        FMath::IsNearlyEqual(
                            FogComponent->StartDistance,
                            450.0f,
                            0.1f));
                    Test->TestTrue(
                        TEXT("Pacuare humidity uses a restrained water-level layer"),
                        FMath::IsNearlyEqual(
                            FogComponent->SecondFogData.FogDensity,
                            0.0012f,
                            0.0001f) &&
                            FMath::IsNearlyEqual(
                                FogComponent->SecondFogData.FogHeightOffset,
                                -160.0f,
                                0.1f) &&
                            FMath::IsNearlyEqual(
                                FogComponent->SecondFogData.FogHeightFalloff,
                                0.06f,
                                0.001f));
                }
                Test->TestTrue(
                    TEXT("Pacuare humidity disclaims hydraulic authority"),
                    Actor->Tags.Contains(
                        TEXT("RaftSimPresentationOnlyNoHydraulicAuthority")));
                ++LayeredHumidityCount;
            }
        }
        Test->TestEqual(
            TEXT("Pacuare has a four-actor humid-atmosphere contract"),
            HumidAtmosphereActorCount,
            4);
        Test->TestEqual(
            TEXT("Pacuare links one humidity-aware directional light"),
            HumidityDirectionalLightCount,
            1);
        Test->TestEqual(
            TEXT("Pacuare links one humidity-aware sky fill"),
            HumiditySkyFillCount,
            1);
        Test->TestEqual(
            TEXT("Pacuare links one humid aerial-perspective sky"),
            HumidAerialPerspectiveCount,
            1);
        Test->TestEqual(
            TEXT("Pacuare links one layered humidity actor"),
            LayeredHumidityCount,
            1);

        int32 RuntimeWaterConfigCount = 0;
        for (TActorIterator<ARaftSimRiverWaterConfig> It(World); It; ++It)
        {
            if ((*It)->GetActorLabelView() !=
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
            Test->TestTrue(
                TEXT("Pacuare reasserts the reviewed fog contract after PIE duplication"),
                (*It)->bEnforceTaggedHeightFogPresentation &&
                    (*It)->RuntimeHeightFogActorTag ==
                        FName(TEXT("RaftSimLayeredRainforestHumidity")) &&
                    FMath::IsNearlyEqual(
                        (*It)->RuntimeHeightFogDensity,
                        0.0075f,
                        0.0001f) &&
                    !(*It)->bRuntimeVolumetricFogEnabled);
            Test->TestTrue(
                TEXT("Pacuare solver owns the visible gameplay river"),
                (*It)->bLiveSolverOwnsRuntimeRendering);
            Test->TestTrue(
                TEXT("Pacuare enables the transmitting wet-cell volume core"),
                (*It)->bEnableLiveSolverVolumeCore);
            Test->TestTrue(
                TEXT("Pacuare stores restrained calm detail coverage"),
                FMath::IsNearlyEqual(
                    (*It)->LiveSurfaceCalmCoverage, 0.035f, 0.001f));
            Test->TestTrue(
                TEXT("Pacuare stores active-water detail response"),
                FMath::IsNearlyEqual(
                    (*It)->LiveSurfaceActiveCoverage, 0.14f, 0.001f));
            Test->TestTrue(
                TEXT("Pacuare binds river-local volume water"),
                (*It)->LiveVolumeCoreMaterialOverride &&
                    (*It)->LiveVolumeCoreMaterialOverride->GetPathName().Contains(
                        TEXT("MI_RaftSim_PacuareUpperHuacas_LiveVolumeWaterV1")));
            Test->TestTrue(
                TEXT("Pacuare binds a river-local flow normal"),
                (*It)->LiveWaterFlowNormalTexture &&
                    (*It)->LiveWaterFlowNormalTexture->GetPathName().Contains(
                        TEXT("T_RaftSim_PacuareUpperHuacasWaterV1_FlowNormal")));
            Test->TestTrue(
                TEXT("Pacuare binds solver-masked foam lace"),
                (*It)->LiveWaterFoamLaceTexture &&
                    (*It)->LiveWaterFoamLaceTexture->GetPathName().Contains(
                        TEXT("T_RaftSim_PacuareUpperHuacasWaterV1_FoamLace")));
            Test->TestTrue(
                TEXT("Pacuare enables shared render/support subcell smoothing"),
                (*It)->bEnableLivePresentationSurfaceSmoothing);
            Test->TestTrue(
                TEXT("Pacuare smoothing strength is bounded"),
                FMath::IsNearlyEqual(
                    (*It)->LivePresentationSurfaceSmoothingStrength,
                    0.62f,
                    0.001f));
            Test->TestTrue(
                TEXT("Pacuare shallow transmission remains open enough for bed cues"),
                FMath::IsNearlyEqual(
                    (*It)->LiveShallowWaterOpacity, 0.46f, 0.001f));
            Test->TestTrue(
                TEXT("Pacuare config marks the transmitting visual-only upgrade"),
                (*It)->Tags.Contains(TEXT("RaftSimPacuareTransmittingWaterV1")) &&
                    (*It)->Tags.Contains(TEXT("RaftSimNoSolverStateMutation")));
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

        int32 OrganicShorelineActorCount = 0;
        int32 OrganicShorelineRockActorCount = 0;
        int32 OrganicShorelineRockInstanceCount = 0;
        int32 OrganicShorelineGroundCoverActorCount = 0;
        int32 OrganicShorelineGroundCoverInstanceCount = 0;
        int32 ScannedFernActorCount = 0;
        int32 ScannedFernInstanceCount = 0;
        int32 OrganicShorelineShrubActorCount = 0;
        int32 OrganicShorelineShrubInstanceCount = 0;
        int32 ForestFloorActorCount = 0;
        int32 ForestFloorLeafActorCount = 0;
        int32 ForestFloorLeafInstanceCount = 0;
        int32 ForestFloorRootActorCount = 0;
        int32 ForestFloorRootInstanceCount = 0;
        int32 ForestFloorDeadwoodActorCount = 0;
        int32 ForestFloorDeadwoodInstanceCount = 0;
        for (TActorIterator<AActor> It(World); It; ++It)
        {
            AActor* Actor = *It;
            if (!Actor ||
                !Actor->Tags.Contains(
                    TEXT("RaftSimPacuareOrganicShorelineV1")))
            {
                continue;
            }
            const UHierarchicalInstancedStaticMeshComponent* Instances =
                Actor->FindComponentByClass<
                    UHierarchicalInstancedStaticMeshComponent>();
            Test->TestNotNull(
                TEXT("Pacuare organic shoreline actor has one HISM"),
                Instances);
            if (!Instances)
            {
                continue;
            }
            Test->TestEqual(
                TEXT("Pacuare organic shoreline remains non-colliding"),
                Instances->GetCollisionEnabled(),
                ECollisionEnabled::NoCollision);
            Test->TestTrue(
                TEXT("Pacuare organic shoreline is source-Landscape grounded"),
                Actor->Tags.Contains(TEXT("RaftSimSourceLandscapeGrounded")));
            Test->TestTrue(
                TEXT("Pacuare organic shoreline stays outside the solver strip"),
                Actor->Tags.Contains(
                    TEXT("RaftSimOutsideProtectedSolverStrip")) &&
                    Instances->ComponentTags.Contains(
                        TEXT("RaftSimOutsideProtectedSolverStrip")));
            Test->TestTrue(
                TEXT("Pacuare organic shoreline disclaims hydraulic authority"),
                Actor->Tags.Contains(
                    TEXT("RaftSimPresentationOnlyNoHydraulicAuthority")) &&
                    Actor->Tags.Contains(
                        TEXT("RaftSimProceduralSourceGapFill")));
            if (Actor->Tags.Contains(
                    TEXT("RaftSimPacuareShorelineMossRock")))
            {
                Test->TestTrue(
                    TEXT("Pacuare shoreline rocks disclaim lithology authority"),
                    Actor->Tags.Contains(
                        TEXT("RaftSimGenericRockAnalogNoLithologyAuthority")));
                OrganicShorelineRockInstanceCount +=
                    Instances->GetInstanceCount();
                ++OrganicShorelineRockActorCount;
            }
            if (Actor->Tags.Contains(
                    TEXT("RaftSimPacuareShorelineGroundCover")))
            {
                Test->TestTrue(
                    TEXT("Pacuare shoreline ground cover disclaims ecology authority"),
                    Actor->Tags.Contains(
                        TEXT("RaftSimNoSpeciesOrEcologyAuthority")));
                Test->TestFalse(
                    TEXT("Pacuare short ground cover suppresses self-shadowing"),
                    Instances->CastShadow);
                OrganicShorelineGroundCoverInstanceCount +=
                    Instances->GetInstanceCount();
                ++OrganicShorelineGroundCoverActorCount;
                if (Actor->Tags.Contains(
                        TEXT("RaftSimPacuareScannedFernUnderstoryV1")))
                {
                    Test->TestTrue(
                        TEXT("Pacuare scanned ferns retain CC0 review provenance"),
                        Actor->Tags.Contains(
                            TEXT("RaftSimRightsReviewedCC0UnderstoryAnalog")));
                    const UStaticMesh* Mesh = Instances->GetStaticMesh();
                    Test->TestTrue(
                        TEXT("Pacuare scanned fern actor binds a reviewed fern mesh"),
                        Mesh && Mesh->GetName().StartsWith(
                            TEXT("SM_Fern02_fern_02_")) &&
                            Mesh->GetPathName().Contains(
                                TEXT("/FutaleufuTemperateForestSet_1K/")));
                    ScannedFernInstanceCount += Instances->GetInstanceCount();
                    ++ScannedFernActorCount;
                }
            }
            if (Actor->Tags.Contains(
                    TEXT("RaftSimPacuareShorelineShrub")))
            {
                Test->TestTrue(
                    TEXT("Pacuare shoreline shrubs disclaim ecology authority"),
                    Actor->Tags.Contains(
                        TEXT("RaftSimNoSpeciesOrEcologyAuthority")));
                OrganicShorelineShrubInstanceCount +=
                    Instances->GetInstanceCount();
                ++OrganicShorelineShrubActorCount;
            }
            if (Actor->Tags.Contains(TEXT("RaftSimPacuareForestFloorV1")))
            {
                Test->TestTrue(
                    TEXT("Pacuare forest floor retains procedural-infill authority"),
                    Actor->Tags.Contains(TEXT("RaftSimProceduralInfill")) &&
                        Actor->Tags.Contains(
                            TEXT("RaftSimNoSpeciesOrEcologyAuthority")) &&
                        Actor->Tags.Contains(
                            TEXT("RaftSimNoTerrainCollisionOrWaterAuthority")));
                const UStaticMesh* Mesh = Instances->GetStaticMesh();
                Test->TestTrue(
                    TEXT("Pacuare forest floor binds a project-owned V1 mesh"),
                    Mesh && Mesh->GetPathName().Contains(
                        TEXT("/PacuareRun/Vegetation/Meshes/")) &&
                        Mesh->GetName().EndsWith(TEXT("ForestFloorV1")));
                if (Actor->Tags.Contains(
                        TEXT("RaftSimPacuareFoldedLeafLitter")))
                {
                    Test->TestFalse(
                        TEXT("Pacuare low leaf litter suppresses self-shadowing"),
                        Instances->CastShadow);
                    ForestFloorLeafInstanceCount += Instances->GetInstanceCount();
                    ++ForestFloorLeafActorCount;
                }
                if (Actor->Tags.Contains(
                        TEXT("RaftSimPacuareButtressRoot")))
                {
                    ForestFloorRootInstanceCount += Instances->GetInstanceCount();
                    ++ForestFloorRootActorCount;
                }
                if (Actor->Tags.Contains(TEXT("RaftSimPacuareDeadwood")))
                {
                    ForestFloorDeadwoodInstanceCount += Instances->GetInstanceCount();
                    ++ForestFloorDeadwoodActorCount;
                }
                ++ForestFloorActorCount;
            }
            ++OrganicShorelineActorCount;
        }
        Test->TestEqual(
            TEXT("Pacuare organic shoreline has sixteen dedicated morphology actors"),
            OrganicShorelineActorCount,
            16);
        Test->TestEqual(
            TEXT("Pacuare organic shoreline has six moss-rock variants"),
            OrganicShorelineRockActorCount,
            6);
        Test->TestTrue(
            TEXT("Pacuare organic shoreline retains dense moss-rock structure"),
            OrganicShorelineRockInstanceCount >= 2350);
        Test->TestEqual(
            TEXT("Pacuare organic shoreline has one procedural plus four scanned ground-cover actors"),
            OrganicShorelineGroundCoverActorCount,
            5);
        Test->TestTrue(
            TEXT("Pacuare organic shoreline retains dense rainforest-floor cover"),
            OrganicShorelineGroundCoverInstanceCount >= 4700);
        Test->TestEqual(
            TEXT("Pacuare uses all four reviewed scanned fern variants"),
            ScannedFernActorCount,
            4);
        Test->TestTrue(
            TEXT("Pacuare replaces most near-bank ground cover with scanned fern morphology"),
            ScannedFernInstanceCount >= 3300);
        Test->TestEqual(
            TEXT("Pacuare organic shoreline has one shrub actor"),
            OrganicShorelineShrubActorCount,
            1);
        Test->TestTrue(
            TEXT("Pacuare organic shoreline retains a layered shrub transition"),
            OrganicShorelineShrubInstanceCount >= 1050);
        Test->TestEqual(
            TEXT("Pacuare forest floor has four dedicated solid morphology actors"),
            ForestFloorActorCount,
            4);
        Test->TestEqual(
            TEXT("Pacuare forest floor has two folded-leaf litter variants"),
            ForestFloorLeafActorCount,
            2);
        Test->TestEqual(
            TEXT("Pacuare forest floor places the complete leaf-litter population"),
            ForestFloorLeafInstanceCount,
            2600);
        Test->TestEqual(
            TEXT("Pacuare forest floor has one buttress-root actor"),
            ForestFloorRootActorCount,
            1);
        Test->TestEqual(
            TEXT("Pacuare forest floor places half its woody targets as roots"),
            ForestFloorRootInstanceCount,
            350);
        Test->TestEqual(
            TEXT("Pacuare forest floor has one deadwood actor"),
            ForestFloorDeadwoodActorCount,
            1);
        Test->TestEqual(
            TEXT("Pacuare forest floor places half its woody targets as deadwood"),
            ForestFloorDeadwoodInstanceCount,
            350);
        return true;
    }

    if (bColoradoHanceReferenceRun)
    {
        Test->TestTrue(
            TEXT("Colorado Hance player raft is marked reference-runnable"),
            PlayerRaft->Tags.Contains(TEXT("RaftSimReferenceRunnable")));
        Test->TestTrue(
            TEXT("Colorado Hance launches on the reviewed rapid approach"),
            PlayerRaft->Tags.Contains(
                TEXT("RaftSimColoradoHanceRapidApproachLaunchV1")));
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
            if ((*It)->GetActorLabelView() !=
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
            Test->TestTrue(
                TEXT("Colorado Hance solver owns the visible gameplay river"),
                (*It)->bLiveSolverOwnsRuntimeRendering);
            Test->TestTrue(
                TEXT("Colorado Hance enables or safely migrates the transmitting volume core"),
                (*It)->bEnableLiveSolverVolumeCore ||
                    (*It)->CookedFieldsDir.Contains(
                        TEXT("colorado_river_grand_canyon_rowing"),
                        ESearchCase::CaseSensitive));
            if ((*It)->bEnableLiveSolverVolumeCore)
            {
                Test->TestTrue(
                    TEXT("regenerated Colorado Hance config stores restrained calm detail coverage"),
                    FMath::IsNearlyEqual(
                        (*It)->LiveSurfaceCalmCoverage, 0.035f, 0.001f));
                Test->TestTrue(
                    TEXT("regenerated Colorado Hance config stores active-water detail response"),
                    FMath::IsNearlyEqual(
                        (*It)->LiveSurfaceActiveCoverage, 0.14f, 0.001f));
                Test->TestTrue(
                    TEXT("regenerated Colorado Hance config binds river-local volume water"),
                    (*It)->LiveVolumeCoreMaterialOverride &&
                        (*It)->LiveVolumeCoreMaterialOverride->GetPathName().Contains(
                            TEXT("MI_RaftSim_ColoradoHance_LiveVolumeWaterV2")));
                Test->TestTrue(
                    TEXT("regenerated Colorado Hance config binds river-local flow normal"),
                    (*It)->LiveWaterFlowNormalTexture &&
                        (*It)->LiveWaterFlowNormalTexture->GetPathName().Contains(
                            TEXT("T_RaftSim_ColoradoHanceWaterV1_FlowNormal")));
                Test->TestTrue(
                    TEXT("regenerated Colorado Hance config binds solver-masked foam lace"),
                    (*It)->LiveWaterFoamLaceTexture &&
                        (*It)->LiveWaterFoamLaceTexture->GetPathName().Contains(
                            TEXT("T_RaftSim_ColoradoHanceWaterV1_FoamLace")));
            }
            else
            {
                Test->TestNotNull(
                    TEXT("versioned Colorado Hance map can migrate to V2 live-volume water"),
                    LoadObject<UMaterialInterface>(
                        nullptr,
                        TEXT("/Game/RaftSim/Environment/ColoradoRun/Water/Materials/"
                             "MI_RaftSim_ColoradoHance_LiveVolumeWaterV2."
                             "MI_RaftSim_ColoradoHance_LiveVolumeWaterV2")));
                Test->TestNotNull(
                    TEXT("versioned Colorado Hance map can migrate to river-local flow normal"),
                    LoadObject<UTexture2D>(
                        nullptr,
                        TEXT("/Game/RaftSim/Environment/ColoradoRun/Water/Textures/"
                             "T_RaftSim_ColoradoHanceWaterV1_FlowNormal."
                             "T_RaftSim_ColoradoHanceWaterV1_FlowNormal")));
                Test->TestNotNull(
                    TEXT("versioned Colorado Hance map can migrate to solver-masked foam lace"),
                    LoadObject<UTexture2D>(
                        nullptr,
                        TEXT("/Game/RaftSim/Environment/ColoradoRun/Water/Textures/"
                             "T_RaftSim_ColoradoHanceWaterV1_FoamLace."
                             "T_RaftSim_ColoradoHanceWaterV1_FoamLace")));
            }
            Test->TestTrue(
                TEXT("Colorado Hance enables shared render/support subcell smoothing"),
                (*It)->bEnableLivePresentationSurfaceSmoothing);
            Test->TestTrue(
                TEXT("Colorado Hance smoothing strength is reviewed"),
                FMath::IsNearlyEqual(
                    (*It)->LivePresentationSurfaceSmoothingStrength,
                    0.72f,
                    0.001f));
            Test->TestTrue(
                TEXT("Colorado Hance reduces synthetic standing-wave amplitude"),
                FMath::IsNearlyEqual(
                    (*It)->LivePresentationStandingWaveScale, 0.55f, 0.001f));
            Test->TestTrue(
                TEXT("Colorado Hance reduces amplified hydraulic relief"),
                FMath::IsNearlyEqual(
                    (*It)->LivePresentationHydraulicReliefScale, 0.55f, 0.001f));
            Test->TestTrue(
                TEXT("Colorado Hance focuses rapid foam above low-energy haze"),
                FMath::IsNearlyEqual(
                    (*It)->LiveRapidFoamFocusStart, 0.30f, 0.001f) &&
                    FMath::IsNearlyEqual(
                        (*It)->LiveRapidFoamFocusEnd, 0.82f, 0.001f) &&
                    FMath::IsNearlyEqual(
                        (*It)->LiveRapidFoamCoverageGain, 0.82f, 0.001f));
            Test->TestTrue(
                TEXT("Colorado Hance config preserves solver-state authority tags"),
                (*It)->Tags.Contains(
                    TEXT("RaftSimColoradoHanceSubcellSmoothedWaterV1")) &&
                    (*It)->Tags.Contains(TEXT("RaftSimRenderOnlyHydraulicSmoothing")) &&
                    (*It)->Tags.Contains(TEXT("RaftSimNoSolverStateMutation")) &&
                    (*It)->Tags.Contains(TEXT("RaftSimColoradoHanceLaceFoamV1")));
            Test->TestTrue(
                TEXT("Colorado Hance config records rapid-approach framing"),
                (*It)->Tags.Contains(
                    TEXT("RaftSimColoradoHanceRapidApproachLaunchV1")));
            ++RuntimeWaterConfigCount;
        }
        Test->TestEqual(
            TEXT("Colorado Hance reference run has one runtime water config"),
            RuntimeWaterConfigCount,
            1);

        bool bHasSolverRapidCamera = false;
        for (TActorIterator<AActor> It(World); It; ++It)
        {
            if ((*It)->GetActorLabelView() ==
                TEXT("RaftSim_SolverRapid_RiverEyeCaptureCamera"))
            {
                bHasSolverRapidCamera = true;
                break;
            }
        }
        Test->TestTrue(
            TEXT("Colorado Hance map retains a distinct solver-rapid camera"),
            bHasSolverRapidCamera);

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
            if (!(*It)->Tags.Contains(TEXT("RaftSimSolverFieldFoam")))
            {
                Test->TestTrue(
                    TEXT("Colorado Hance capture ribbon uses isolated Default Lit water"),
                    (*It)->Tags.Contains(TEXT("RaftSimColoradoHanceDefaultLitWater")));
                Test->TestTrue(
                    TEXT("Colorado Hance capture ribbon records CPU cooked-field color authority"),
                    (*It)->Tags.Contains(TEXT("RaftSimCpuAuthoredCookedFieldColor")));
                Test->TestTrue(
                    TEXT("Colorado Hance capture ribbon declares subcell smoothing"),
                    (*It)->Tags.Contains(
                        TEXT("RaftSimColoradoHanceSubcellSmoothedWaterV1")) &&
                        (*It)->Tags.Contains(
                            TEXT("RaftSimRenderOnlyHydraulicSmoothing")) &&
                        (*It)->Tags.Contains(TEXT("RaftSimNoSolverStateMutation")));
            }
            if ((*It)->Tags.Contains(TEXT("RaftSimSolverFieldFoam")))
            {
                Test->TestTrue(
                    TEXT("Colorado Hance foam is identified as solver-field visualization"),
                    (*It)->Tags.Contains(
                        TEXT("RaftSimColoradoHanceSolverVisualization")));
                Test->TestTrue(
                    TEXT("Colorado Hance foam declares the lace breakup contract"),
                    (*It)->Tags.Contains(TEXT("RaftSimColoradoHanceLaceFoamV1")) &&
                        (*It)->Tags.Contains(TEXT("RaftSimNoSolverStateMutation")));
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

        int32 DrylandComponentCount = 0;
        int32 DrylandGroundCoverInstanceCount = 0;
        int32 DrylandShrubInstanceCount = 0;
        TSet<FString> DrylandMeshPaths;
        for (TActorIterator<AActor> It(World); It; ++It)
        {
            AActor* Actor = *It;
            if (!Actor ||
                !Actor->Tags.Contains(
                    TEXT("RaftSimHanceOpaqueDrylandVegetationV2")))
            {
                continue;
            }
            const UHierarchicalInstancedStaticMeshComponent* Instances =
                Actor->FindComponentByClass<
                    UHierarchicalInstancedStaticMeshComponent>();
            Test->TestNotNull(
                TEXT("Colorado Hance dryland dressing actor has one HISM"),
                Instances);
            if (!Instances)
            {
                continue;
            }
            Test->TestEqual(
                TEXT("Colorado Hance dryland dressing remains non-colliding"),
                Instances->GetCollisionEnabled(),
                ECollisionEnabled::NoCollision);
            Test->TestTrue(
                TEXT("Colorado Hance dryland dressing remains outside the solver strip"),
                Actor->Tags.Contains(
                    TEXT("RaftSimOutsideProtectedSolverStrip")) &&
                    Instances->ComponentTags.Contains(
                        TEXT("RaftSimOutsideProtectedSolverStrip")));
            Test->TestTrue(
                TEXT("Colorado Hance dryland dressing is reference-constrained non-authoritative gap fill"),
                Actor->Tags.Contains(TEXT("RaftSimNoEcologyAuthority")) &&
                    Actor->Tags.Contains(TEXT("RaftSimNoGeographyAuthority")) &&
                    Actor->Tags.Contains(TEXT("RaftSimNoHydraulicAuthority")) &&
                    Actor->Tags.Contains(
                        TEXT("RaftSimOfficialReferenceConstrainedProceduralGapFill")) &&
                    Actor->Tags.Contains(
                        TEXT("RaftSimProceduralVegetationFallback")));
            Test->TestTrue(
                TEXT("Colorado Hance dryland dressing uses the isolated material"),
                Instances->GetMaterial(0) &&
                    Instances->GetMaterial(0)->GetPathName().Contains(
                        TEXT("M_RaftSim_Hance_OpaqueDrylandVegetationV2")));
            if (const UStaticMesh* Mesh = Instances->GetStaticMesh())
            {
                DrylandMeshPaths.Add(Mesh->GetPathName());
            }

            const FString ComponentName = Instances->GetName();
            if (ComponentName.Contains(TEXT("HanceDrylandGroundCover")))
            {
                Test->TestFalse(
                    TEXT("Colorado Hance ground cover suppresses coarse self-shadowing"),
                    Instances->CastShadow);
                Test->TestTrue(
                    TEXT("Colorado Hance ground cover records self-shadow suppression"),
                    Instances->ComponentTags.Contains(
                        TEXT("RaftSimGroundCoverSelfShadowSuppressed")));
                DrylandGroundCoverInstanceCount += Instances->GetInstanceCount();
            }
            else if (ComponentName.Contains(TEXT("HanceDrylandShrub")))
            {
                Test->TestTrue(
                    TEXT("Colorado Hance shrubs retain grounded shadows"),
                    Instances->CastShadow);
                DrylandShrubInstanceCount += Instances->GetInstanceCount();
            }
            ++DrylandComponentCount;
        }
        Test->TestEqual(
            TEXT("Colorado Hance has two ground-cover and two shrub HISM components"),
            DrylandComponentCount,
            4);
        Test->TestTrue(
            TEXT("Colorado Hance has dense dryland ground cover"),
            DrylandGroundCoverInstanceCount >= 2700);
        Test->TestTrue(
            TEXT("Colorado Hance has distributed dryland shrubs"),
            DrylandShrubInstanceCount >= 420);
        for (const TCHAR* MeshToken : {
                 TEXT("SM_RaftSim_Hance_DesertShrub_A_OpaqueV2"),
                 TEXT("SM_RaftSim_Hance_DesertShrub_B_OpaqueV2"),
                 TEXT("SM_RaftSim_Hance_DryGroundCover_A_OpaqueV2"),
                 TEXT("SM_RaftSim_Hance_DryGroundCover_B_OpaqueV2")})
        {
            const FString ExpectedMeshPath = FString::Printf(
                TEXT("/Game/RaftSim/Environment/ColoradoRun/Vegetation/Meshes/%s.%s"),
                MeshToken,
                MeshToken);
            Test->TestTrue(
                FString::Printf(
                    TEXT("Colorado Hance includes vegetation morphology %s"),
                    MeshToken),
                DrylandMeshPaths.Contains(ExpectedMeshPath));
        }
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
            if ((*It)->GetActorLabelView() !=
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
                TEXT("Futaleufu enables or safely migrates the bank-clipped Single Layer Water core"),
                (*It)->bEnableLiveSolverVolumeCore ||
                    (*It)->CookedFieldsDir.Contains(
                        TEXT("futaleufu_river_chile"),
                        ESearchCase::CaseSensitive));
            if ((*It)->bEnableLiveSolverVolumeCore)
            {
                Test->TestTrue(
                    TEXT("regenerated Futaleufu config stores restrained calm detail coverage"),
                    FMath::IsNearlyEqual(
                        (*It)->LiveSurfaceCalmCoverage, 0.035f, 0.001f));
                Test->TestTrue(
                    TEXT("regenerated Futaleufu config stores active-water detail response"),
                    FMath::IsNearlyEqual(
                        (*It)->LiveSurfaceActiveCoverage, 0.14f, 0.001f));
                Test->TestTrue(
                    TEXT("regenerated Futaleufu config binds its river-local live-volume material"),
                    (*It)->LiveVolumeCoreMaterialOverride &&
                        (*It)->LiveVolumeCoreMaterialOverride->GetPathName().Contains(
                            TEXT("MI_RaftSim_FutaleufuTerminator_LiveVolumeWaterV3")));
                Test->TestTrue(
                    TEXT("regenerated Futaleufu config binds its river-local flow normal"),
                    (*It)->LiveWaterFlowNormalTexture &&
                        (*It)->LiveWaterFlowNormalTexture->GetPathName().Contains(
                            TEXT("T_RaftSim_FutaleufuTerminatorWaterV1_FlowNormal")));
                Test->TestTrue(
                    TEXT("regenerated Futaleufu config binds its solver-masked foam lace"),
                    (*It)->LiveWaterFoamLaceTexture &&
                        (*It)->LiveWaterFoamLaceTexture->GetPathName().Contains(
                            TEXT("T_RaftSim_FutaleufuTerminatorWaterV1_FoamLace")));
                Test->TestTrue(
                    TEXT("regenerated Futaleufu live sky reflection stays restrained"),
                    FMath::IsNearlyEqual(
                        (*It)->LiveSkyReflectionStrength, 0.05f, 0.001f));
                Test->TestTrue(
                    TEXT("regenerated Futaleufu config uses its turbulent ripple bracket"),
                    FMath::IsNearlyEqual(
                        (*It)->LiveRippleStrength, 0.72f, 0.001f));
                Test->TestTrue(
                    TEXT("regenerated Futaleufu config uses its turbulent roughness bracket"),
                    FMath::IsNearlyEqual(
                        (*It)->LiveSurfaceRoughness, 0.42f, 0.001f));
                Test->TestTrue(
                    TEXT("regenerated Futaleufu retains bounded dielectric energy"),
                    FMath::IsNearlyEqual(
                        (*It)->LiveSurfaceSpecular, 0.18f, 0.001f));
                Test->TestTrue(
                    TEXT("Futaleufu records the shared cold-water highlight contract"),
                    (*It)->Tags.Contains(
                        TEXT("RaftSimColdWaterHighlightNaturalismV1")));
                Test->TestTrue(
                    TEXT("Futaleufu enforces the restrained runtime sun"),
                    (*It)->bEnforceTaggedDirectionalLightPresentation &&
                        (*It)->RuntimeDirectionalLightActorTag ==
                            TEXT("RaftSimColdWaterHighlightNaturalismV1") &&
                        FMath::IsNearlyEqual(
                            (*It)->RuntimeDirectionalLightIntensity,
                            2.40f,
                            0.001f) &&
                        (*It)->RuntimeDirectionalLightRotation.Equals(
                            FRotator(-50.0f, 30.0f, 0.0f),
                            0.001f));
                Test->TestTrue(
                    TEXT("Futaleufu records the cold-water depth attenuation contract"),
                    (*It)->Tags.Contains(
                        TEXT("RaftSimColdWaterDepthAttenuationV2")));
                Test->TestTrue(
                    TEXT("Futaleufu shallow water transmits dark bed detail"),
                    FMath::IsNearlyEqual(
                        (*It)->LiveShallowWaterOpacity, 0.36f, 0.001f));
                Test->TestTrue(
                    TEXT("Futaleufu deep water retains absorbing optical depth"),
                    FMath::IsNearlyEqual(
                        (*It)->LiveDeepWaterOpacity, 0.86f, 0.001f));
                Test->TestTrue(
                    TEXT("Futaleufu foam stays optically legible"),
                    FMath::IsNearlyEqual(
                        (*It)->LiveFoamWaterOpacity, 0.88f, 0.001f));
                Test->TestTrue(
                    TEXT("regenerated Futaleufu solver foam remains optically legible"),
                    FMath::IsNearlyEqual(
                        (*It)->LiveFoamIntensity, 0.58f, 0.001f));
            }
            else
            {
                Test->TestNotNull(
                    TEXT("versioned Futaleufu map can migrate to the V3 live-volume material"),
                    LoadObject<UMaterialInterface>(
                        nullptr,
                        TEXT("/Game/RaftSim/Environment/FutaleufuRun/Water/Materials/"
                             "MI_RaftSim_FutaleufuTerminator_LiveVolumeWaterV3."
                             "MI_RaftSim_FutaleufuTerminator_LiveVolumeWaterV3")));
                Test->TestNotNull(
                    TEXT("versioned Futaleufu map can migrate to the river-local flow normal"),
                    LoadObject<UTexture2D>(
                        nullptr,
                        TEXT("/Game/RaftSim/Environment/FutaleufuRun/Water/Textures/"
                             "T_RaftSim_FutaleufuTerminatorWaterV1_FlowNormal."
                             "T_RaftSim_FutaleufuTerminatorWaterV1_FlowNormal")));
                Test->TestNotNull(
                    TEXT("versioned Futaleufu map can migrate to solver-masked foam lace"),
                    LoadObject<UTexture2D>(
                        nullptr,
                        TEXT("/Game/RaftSim/Environment/FutaleufuRun/Water/Textures/"
                             "T_RaftSim_FutaleufuTerminatorWaterV1_FoamLace."
                             "T_RaftSim_FutaleufuTerminatorWaterV1_FoamLace")));
            }
            Test->TestTrue(
                TEXT("Futaleufu rapid lace begins at low solver foam activity"),
                FMath::IsNearlyEqual(
                    (*It)->LiveRapidFoamFocusStart, 0.08f, 0.001f));
            Test->TestTrue(
                TEXT("Futaleufu rapid lace reaches full focus before calm water"),
                FMath::IsNearlyEqual(
                    (*It)->LiveRapidFoamFocusEnd, 0.58f, 0.001f));
            Test->TestTrue(
                TEXT("Futaleufu rapid lace retains full solver coverage"),
                FMath::IsNearlyEqual(
                    (*It)->LiveRapidFoamCoverageGain, 1.0f, 0.001f));
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
            TEXT("Chilko launches on the reviewed rapid-approach framing"),
            PlayerRaft->Tags.Contains(TEXT("RaftSimChilkoRapidApproachLaunchV1")));
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
            if ((*It)->GetActorLabelView() !=
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
                TEXT("Chilko enables or safely migrates the bank-clipped Single Layer Water core"),
                (*It)->bEnableLiveSolverVolumeCore ||
                    (*It)->CookedFieldsDir.Contains(
                        TEXT("chilko_river_lava_canyon"),
                        ESearchCase::CaseSensitive));
            if ((*It)->bEnableLiveSolverVolumeCore)
            {
                Test->TestTrue(
                    TEXT("regenerated Chilko config stores restrained calm detail coverage"),
                    FMath::IsNearlyEqual(
                        (*It)->LiveSurfaceCalmCoverage, 0.035f, 0.001f));
                Test->TestTrue(
                    TEXT("regenerated Chilko config stores active-water detail response"),
                    FMath::IsNearlyEqual(
                        (*It)->LiveSurfaceActiveCoverage, 0.14f, 0.001f));
                Test->TestTrue(
                    TEXT("regenerated Chilko config stores river-local volume water"),
                    (*It)->LiveVolumeCoreMaterialOverride &&
                        (*It)->LiveVolumeCoreMaterialOverride->GetPathName().Contains(
                            TEXT("MI_RaftSim_ChilkoLavaCanyon_LiveVolumeWaterV2")));
                Test->TestTrue(
                    TEXT("regenerated Chilko config stores its river-local flow normal"),
                    (*It)->LiveWaterFlowNormalTexture &&
                        (*It)->LiveWaterFlowNormalTexture->GetPathName().Contains(
                            TEXT("T_RaftSim_ChilkoLavaCanyonWaterV1_FlowNormal")));
                Test->TestTrue(
                    TEXT("regenerated Chilko config stores solver-masked foam lace"),
                    (*It)->LiveWaterFoamLaceTexture &&
                        (*It)->LiveWaterFoamLaceTexture->GetPathName().Contains(
                            TEXT("T_RaftSim_ChilkoLavaCanyonWaterV1_FoamLace")));
            }
            Test->TestTrue(
                TEXT("Chilko live sky reflection stays restrained"),
                FMath::IsNearlyEqual(
                    (*It)->LiveSkyReflectionStrength, 0.05f, 0.001f));
            Test->TestTrue(
                TEXT("versioned Chilko config retains its serialized ripple baseline"),
                FMath::IsNearlyEqual(
                    (*It)->LiveRippleStrength, 0.55f, 0.001f));
            Test->TestTrue(
                TEXT("versioned Chilko config retains its serialized roughness baseline"),
                FMath::IsNearlyEqual(
                    (*It)->LiveSurfaceRoughness, 0.68f, 0.001f));
            Test->TestTrue(
                TEXT("Chilko live carrier retains a physical dielectric response"),
                FMath::IsNearlyEqual(
                    (*It)->LiveSurfaceSpecular, 0.18f, 0.001f));
            Test->TestTrue(
                TEXT("Chilko live carrier records the localized reflection contract"),
                (*It)->Tags.Contains(
                    TEXT("RaftSimChilkoLocalizedReflectionWaterV3")));
            Test->TestTrue(
                TEXT("Chilko records the shared cold-water highlight contract"),
                (*It)->Tags.Contains(
                    TEXT("RaftSimColdWaterHighlightNaturalismV1")));
            Test->TestTrue(
                TEXT("Chilko enforces the restrained runtime sun"),
                (*It)->bEnforceTaggedDirectionalLightPresentation &&
                    (*It)->RuntimeDirectionalLightActorTag ==
                        TEXT("RaftSimColdWaterHighlightNaturalismV1") &&
                    FMath::IsNearlyEqual(
                        (*It)->RuntimeDirectionalLightIntensity,
                        2.90f,
                        0.001f) &&
                    (*It)->RuntimeDirectionalLightRotation.Equals(
                        FRotator(-50.0f, 55.0f, 0.0f),
                        0.001f));
            Test->TestTrue(
                TEXT("Chilko solver foam remains optically legible"),
                FMath::IsNearlyEqual(
                    (*It)->LiveFoamIntensity, 0.56f, 0.001f));
            Test->TestTrue(
                TEXT("Chilko retains conservative rapid-lace onset while edge-only jumps are rejected"),
                FMath::IsNearlyEqual(
                    (*It)->LiveRapidFoamFocusStart, 0.12f, 0.001f));
            Test->TestTrue(
                TEXT("Chilko retains conservative rapid-lace full-focus threshold"),
                FMath::IsNearlyEqual(
                    (*It)->LiveRapidFoamFocusEnd, 0.72f, 0.001f));
            Test->TestTrue(
                TEXT("Chilko rapid lace keeps restrained solver coverage"),
                FMath::IsNearlyEqual(
                    (*It)->LiveRapidFoamCoverageGain, 0.90f, 0.001f));
            Test->TestTrue(
                TEXT("Chilko applies shared render/support subcell smoothing"),
                (*It)->bEnableLivePresentationSurfaceSmoothing &&
                    FMath::IsNearlyEqual(
                        (*It)->LivePresentationSurfaceSmoothingStrength,
                        0.58f,
                        0.001f));
            Test->TestTrue(
                TEXT("Chilko shallow water remains transmitting"),
                FMath::IsNearlyEqual(
                    (*It)->LiveShallowWaterOpacity, 0.36f, 0.001f));
            Test->TestTrue(
                TEXT("Chilko deep water retains absorbing optical depth"),
                FMath::IsNearlyEqual(
                    (*It)->LiveDeepWaterOpacity, 0.84f, 0.001f));
            Test->TestTrue(
                TEXT("Chilko records the cold-water depth attenuation contract"),
                (*It)->Tags.Contains(
                    TEXT("RaftSimColdWaterDepthAttenuationV2")));
            Test->TestTrue(
                TEXT("Chilko records the visual-only transmitting-water contract"),
                (*It)->Tags.Contains(TEXT("RaftSimChilkoTransmittingWaterV2")) &&
                    (*It)->Tags.Contains(TEXT("RaftSimNoSolverStateMutation")));
            ++RuntimeWaterConfigCount;
        }
        Test->TestEqual(
            TEXT("Chilko Lava Canyon reference run has one runtime water config"),
            RuntimeWaterConfigCount,
            1);

        int32 BreakingSiteCount = 0;
        if (TActorIterator<ARaftSimWaterSurfaceActor> It(World); It)
        {
            TArray<ARaftSimWaterSurfaceActor::FBreakingSite> BreakingSites;
            It->GetBreakingSites(BreakingSites);
            BreakingSiteCount = BreakingSites.Num();
            if (!BreakingSites.IsEmpty())
            {
                const ARaftSimWaterSurfaceActor::FBreakingSite& StrongestSite =
                    BreakingSites[0];
                Test->TestTrue(
                    TEXT("Chilko strongest launch-window jump is in the interpreted Lava Canyon crux"),
                    StrongestSite.RiverCoordinatesMeters.X >= 285.0f &&
                        StrongestSite.RiverCoordinatesMeters.X <= 365.0f);
                Test->TestTrue(
                    TEXT("Chilko strongest launch-window jump has complete presentation coverage"),
                    StrongestSite.PresentationCoverage >= 0.999f);
                Test->TestTrue(
                    TEXT("Chilko strongest launch-window jump retains 15 m bank/edge clearance"),
                    StrongestSite.PresentationEdgeClearanceMeters >= 15.0f);
            }
            Test->TestTrue(
                TEXT("Chilko single carrier retains solver-derived foam data"),
                It->GetVisibleRapidFoamVertexCount() > 0);
            Test->TestFalse(
                TEXT("Chilko single carrier keeps the duplicate rapid-foam sheet hidden"),
                It->IsRapidFoamMeshVisible());
        }
        Test->TestTrue(
            TEXT("Chilko launch window activates an interior solver-owned breaking site"),
            BreakingSiteCount > 0);

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

DEFINE_LATENT_AUTOMATION_COMMAND_TWO_PARAMETER(
    FRaftSimAssertSouthForkSupportParityCommand,
    FAutomationTestBase*, Test,
    TSharedPtr<float>, StartTimeSeconds);
bool FRaftSimAssertSouthForkSupportParityCommand::Update()
{
    UWorld* World = GetRiverTestWorld();
    if (World == nullptr)
    {
        Test->AddError(TEXT("No world for South Fork support-parity test"));
        return true;
    }

    ARaftSimWaterSurfaceActor* Surface = nullptr;
    if (TActorIterator<ARaftSimWaterSurfaceActor> It(World); It)
    {
        Surface = *It;
    }

    ARaftSimRaftActor* Raft = nullptr;
    if (TActorIterator<ARaftSimRaftActor> It(World); It)
    {
        Raft = *It;
    }

    const UGameInstance* GI = World->GetGameInstance();
    URaftSimPhysicsBridgeSubsystem* Bridge =
        GI ? GI->GetSubsystem<URaftSimPhysicsBridgeSubsystem>() : nullptr;
    URaftSimWaterRuntimeAdapter* Water =
        Bridge ? Bridge->GetWaterRuntime() : nullptr;

    // Suite order leaks world state into this test twice over: the water
    // adapter is a game-instance subsystem that outlives AutomationOpenMap,
    // and AutomationOpenMap itself is a no-op when the requested map is
    // already loaded — so a preceding approach ride can leave this "fresh"
    // test with the SAME world, its raft kilometres downriver mid-run and
    // the moving window chasing it. Pin the raft to a known wet put-in
    // station on the first tick, then hold the assert pass until the
    // support surface answers wet there, bounded so genuinely missing
    // infrastructure still reports.
    if (StartTimeSeconds.IsValid() && *StartTimeSeconds < 0.0f)
    {
        *StartTimeSeconds = World->GetTimeSeconds();
        if (Raft && Water)
        {
            // Settle the raft onto the nearest wet centreline station the
            // live window can answer for, wherever the leftover world put
            // it (mid-air over a rapid included): the assertions only need
            // A raft on supported water, not a particular reach.
            FVector2D RaftRiver;
            FVector RiverTangent;
            FVector RiverLeftNormal;
            if (Water->WorldToRiverCoordinates(
                    Raft->GetActorLocation(), RaftRiver, RiverTangent,
                    RiverLeftNormal))
            {
                for (float OffsetM = 0.0f; OffsetM <= 120.0f; OffsetM += 10.0f)
                {
                    FRaftSimWaterSample PinSample;
                    bool bPinned = false;
                    for (const float SignedM : {OffsetM, -OffsetM})
                    {
                        if (Water->SampleWaterAtRiverCoordinates(
                                FVector2D(RaftRiver.X + SignedM, 0.0f),
                                PinSample) &&
                            PinSample.bWet)
                        {
                            Raft->TeleportForTesting(
                                PinSample.WorldPosition +
                                    FVector(0.0f, 0.0f, 12.0f),
                                Raft->GetActorRotation().Yaw,
                                false);
                            bPinned = true;
                            break;
                        }
                    }
                    if (bPinned)
                    {
                        break;
                    }
                }
            }
        }
    }
    if (Raft && Water && StartTimeSeconds.IsValid() &&
        World->GetTimeSeconds() - *StartTimeSeconds < 12.0f)
    {
        FRaftSimWaterSample ReadinessSample;
        const bool bSupportReady =
            Water->SampleRaftSupportSurfaceAtWorldPosition(
                Raft->GetActorLocation(), ReadinessSample) &&
            ReadinessSample.bWet;
        if (!bSupportReady)
        {
            return false;
        }
    }

    Test->TestNotNull(TEXT("South Fork full reach has a live water surface"), Surface);
    Test->TestNotNull(TEXT("South Fork full reach has a playable raft"), Raft);
    Test->TestNotNull(TEXT("South Fork full reach has a water runtime"), Water);
    if (Surface && Water)
    {
        Test->TestTrue(
            TEXT("South Fork live solver owns the runtime waterline"),
            Surface->IsLiveSurfaceCarrierEnabled());
        Test->TestTrue(
            TEXT("South Fork uses one solver-conforming base water surface"),
            Surface->IsSingleLiveWaterSurfaceEnabled());
        Test->TestTrue(
            TEXT("South Fork single surface uses the visible Single Layer Water core"),
            Surface->IsLiveVolumeCoreVisible());
        Test->TestFalse(
            TEXT("South Fork does not render a translucent second base sheet"),
            Surface->IsTranslucentBaseSheetVisible());
        Test->TestFalse(
            TEXT("South Fork integrates foam into its single water surface"),
            Surface->IsRapidFoamMeshVisible());
        Test->TestFalse(
            TEXT("South Fork single surface has no flashing breaking-lip texture"),
            Surface->IsBreakingLipVisible());
        Test->TestFalse(
            TEXT("South Fork single surface has no flashing roller texture"),
            Surface->IsBreakingRollerVolumeVisible());
        int32 TaggedAuthoredWaterCount = 0;
        bool bAllTaggedAuthoredWaterHidden = true;
        for (TActorIterator<AActor> It(World); It; ++It)
        {
            for (const FName& Tag : It->Tags)
            {
                if (Tag.ToString().StartsWith(TEXT("RaftSimFlowBand_")))
                {
                    ++TaggedAuthoredWaterCount;
                    bAllTaggedAuthoredWaterHidden &= It->IsHidden();
                    break;
                }
            }
        }
        Test->TestTrue(
            FString::Printf(
                TEXT("South Fork hides every authored base-water actor during play (%d present)"),
                TaggedAuthoredWaterCount),
            bAllTaggedAuthoredWaterHidden);
        Test->TestTrue(
            TEXT("South Fork visible rapid relief is coupled into raft support"),
            Water->IsRaftSupportSurfaceEnabled());
        Test->TestTrue(
            TEXT("South Fork boulder pillows and Y wakes are configured for raft support"),
            Water->GetRaftSupportBoulderFootprintCount() > 0);
        const float MeatGrinderPillowSupportM =
            Water->ComputeConfiguredBoulderSupportDisplacementMeters(
                FVector2D(904.84f - 2.54f * 1.10f, -3.02f),
                1.8f,
                0.0f);
        Test->TestTrue(
            TEXT("Meat Grinder upstream pillow raises the ridden surface"),
            MeatGrinderPillowSupportM > 0.10f);
        Test->TestTrue(
            TEXT("South Fork support uses the rendered standing-wave scale"),
            FMath::IsNearlyEqual(
                Water->GetRaftSupportStandingWaveScale(),
                Surface->GetLivePresentationStandingWaveScale(),
                0.001f));
        Test->TestTrue(
            TEXT("South Fork support uses the rendered hydraulic-relief scale"),
            FMath::IsNearlyEqual(
                Water->GetRaftSupportHydraulicReliefScale(),
                Surface->GetLivePresentationHydraulicReliefScale(),
                0.001f));

        if (Raft)
        {
            FRaftSimWaterSample SupportSample;
            const bool bHasSupport =
                Water->SampleRaftSupportSurfaceAtWorldPosition(
                    Raft->GetActorLocation(), SupportSample) &&
                SupportSample.bWet;
            Test->TestTrue(
                TEXT("South Fork raft center has a wet support sample"),
                bHasSupport);
            float FloorCenterZCm = 0.0f;
            const bool bHasFloor =
                Raft->GetRenderedFloorCenterWorldZCm(FloorCenterZCm);
            Test->TestTrue(
                TEXT("South Fork rendered self-bailing floor is measurable"),
                bHasFloor);
            if (bHasSupport && bHasFloor)
            {
                const float RenderSurfaceZCm =
                    SupportSample.SurfaceHeightMeters * 100.0f +
                    Surface->GetResolvedLiveSurfaceRenderLiftCm();
                const float RenderFreeboardCm =
                    FloorCenterZCm - RenderSurfaceZCm;
                Test->AddInfo(FString::Printf(
                    TEXT("South Fork support waterline: raft_center=%.1f cm "
                         "floor=%.1f cm render_surface=%.1f cm "
                         "render_freeboard=%.1f cm"),
                    Raft->GetActorLocation().Z,
                    FloorCenterZCm,
                    RenderSurfaceZCm,
                    RenderFreeboardCm));
                Test->TestTrue(
                    FString::Printf(
                        TEXT("South Fork floor remains visibly above the "
                             "coupled rapid surface (%.1f cm >= 5.0 cm)"),
                        RenderFreeboardCm),
                    RenderFreeboardCm >= 5.0f);
            }
        }
    }
    return true;
}

DEFINE_LATENT_AUTOMATION_COMMAND_TWO_PARAMETER(
    FRaftSimMoveSouthForkToBoulderWakeCommand,
    FAutomationTestBase*, Test,
    float, TargetStationM);
bool FRaftSimMoveSouthForkToBoulderWakeCommand::Update()
{
    UWorld* World = GetRiverTestWorld();
    const UGameInstance* GI = World ? World->GetGameInstance() : nullptr;
    URaftSimPhysicsBridgeSubsystem* Bridge =
        GI ? GI->GetSubsystem<URaftSimPhysicsBridgeSubsystem>() : nullptr;
    URaftSimWaterRuntimeAdapter* Water =
        Bridge ? Bridge->GetWaterRuntime() : nullptr;
    ARaftSimRaftActor* Raft = nullptr;
    if (World)
    {
        if (TActorIterator<ARaftSimRaftActor> It(World); It)
        {
            Raft = *It;
        }
    }
    if (!World || !Water || !Raft)
    {
        Test->AddError(TEXT("Could not move South Fork to the first Meat Grinder boulder"));
        return true;
    }

    constexpr float BoulderStationM = 904.84f;
    const float TargetLateralM = FMath::IsNearlyEqual(
        TargetStationM, BoulderStationM, 0.1f)
        ? -3.02f
        : 0.0f;
    FVector BoulderWorldCm = FVector::ZeroVector;
    FVector DownstreamWorldCm = FVector::ZeroVector;
    if (!Water->RiverToWorldPosition(
            FVector2D(TargetStationM, TargetLateralM),
            Water->GetRiverVerticalDatumM(), BoulderWorldCm) ||
        !Water->RiverToWorldPosition(
            FVector2D(TargetStationM + 1.0f, TargetLateralM),
            Water->GetRiverVerticalDatumM(), DownstreamWorldCm))
    {
        Test->AddError(TEXT("Could not resolve the first Meat Grinder boulder in world space"));
        return true;
    }
    BoulderWorldCm.Z = Raft->GetActorLocation().Z;
    const float FacingYawDegrees =
        (DownstreamWorldCm - BoulderWorldCm).Rotation().Yaw;
    Raft->TeleportForTesting(
        BoulderWorldCm, FacingYawDegrees, /*bApplyFacing=*/true);
    if (FMath::IsNearlyEqual(TargetStationM, BoulderStationM, 0.1f))
    {
        Test->AddInfo(TEXT("Moved the live water window to the first Meat Grinder boulder"));
    }
    return true;
}

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(
    FRaftSimAssertSouthForkBoulderWakeCommand, FAutomationTestBase*, Test);
bool FRaftSimAssertSouthForkBoulderWakeCommand::Update()
{
    UWorld* World = GetRiverTestWorld();
    ARaftSimWaterSurfaceActor* Surface = nullptr;
    if (World)
    {
        if (TActorIterator<ARaftSimWaterSurfaceActor> It(World); It)
        {
            Surface = *It;
        }
    }
    Test->TestNotNull(TEXT("South Fork boulder check has a live water surface"), Surface);
    if (Surface)
    {
        Test->TestTrue(
            TEXT("Meat Grinder live window loads a cooked boulder footprint"),
            Surface->GetCurrentBoulderFootprintCount() > 0);
        Test->TestTrue(
            TEXT("Meat Grinder boulder produces displaced rolling wake geometry"),
            Surface->GetMaximumAbsoluteBoulderWakeMeters() > 0.01f);
        Test->TestTrue(
            TEXT("Meat Grinder boulder produces breaking wake foam"),
            Surface->GetBoulderWakeFoamVertexCount() > 0);
        Test->TestFalse(
            TEXT("Meat Grinder wake foam stays in the unified water surface"),
            Surface->IsRapidFoamMeshVisible());
        Test->TestFalse(
            TEXT("Meat Grinder crest remains in the unified water surface"),
            Surface->IsBreakingLipVisible() ||
                Surface->IsBreakingRollerVolumeVisible());
        Test->TestTrue(
            TEXT("South Fork single surface has no duplicate calm live skin"),
            FMath::IsNearlyZero(Surface->GetCalmLiveSurfaceCoverage(), 0.001f));
        Test->TestTrue(
            TEXT("South Fork single surface has no duplicate active live skin"),
            FMath::IsNearlyZero(
                Surface->GetActiveLiveSurfaceCoverage(), 0.001f));
    }
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

bool FRaftSimSouthForkFullReachSupportParityTest::RunTest(const FString&)
{
    const FString MapPath =
        TEXT("/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach");
    if (!MapExists(MapPath))
    {
        AddError(TEXT("South Fork full-reach map is missing"));
        return false;
    }
    AutomationOpenMap(MapPath);
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(4.0f));
    ADD_LATENT_AUTOMATION_COMMAND(FRaftSimAssertSouthForkSupportParityCommand(
        this, MakeShared<float>(-1.0f)));
    // Advance through overlapping 80 m windows, matching the streamer's
    // runtime contract. A direct 120 -> 905 m teleport is correctly rejected
    // because it cannot transfer solver state across the intervening reach.
    const float TraverseStationsM[] = {
        200.0f, 280.0f, 360.0f, 440.0f, 520.0f,
        600.0f, 680.0f, 760.0f, 840.0f, 904.84f};
    for (const float StationM : TraverseStationsM)
    {
        ADD_LATENT_AUTOMATION_COMMAND(
            FRaftSimMoveSouthForkToBoulderWakeCommand(this, StationM));
        ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(0.6f));
    }
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(3.0f));
    ADD_LATENT_AUTOMATION_COMMAND(FRaftSimAssertSouthForkBoulderWakeCommand(this));
    return true;
}

#endif // WITH_AUTOMATION_TESTS
