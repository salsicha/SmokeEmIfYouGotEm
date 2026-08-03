#include "Environment/RaftSimEditorEnvironmentInternal.h"

namespace RaftSimEditorEnvironment
{
namespace
{
constexpr TCHAR FullReachMapPackagePath[] =
    TEXT("/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach");
constexpr TCHAR BuildManifestRelativePath[] =
    TEXT("unreal/Content/RaftSim/Environment/SouthForkFullReach/"
         "full_reach_environment_build_manifest.json");
} // namespace

bool WriteSouthForkFullReachBuildManifest(
    UWorld* World,
    const FSouthForkFullReachBuildMetrics& Metrics,
    bool bReuseExistingDetailedMeshes,
    bool bAllCapturesSaved,
    const TArray<FString>& CapturePaths,
    FString& OutSummary)
{
    TSharedRef<FJsonObject> BuildRoot = MakeShared<FJsonObject>();
    BuildRoot->SetStringField(
        TEXT("schema"), TEXT("raftsim.unreal.south_fork_full_reach_build.v1"));
    BuildRoot->SetStringField(TEXT("generated_on"), TEXT("2026-07-19"));
    BuildRoot->SetStringField(TEXT("map"), FullReachMapPackagePath);
    BuildRoot->SetBoolField(
        TEXT("world_partition"), World && World->GetWorldPartition() != nullptr);
    BuildRoot->SetBoolField(TEXT("nanite_terrain"), Metrics.TerrainTileCount == 13);
    BuildRoot->SetBoolField(TEXT("spatial_streaming_actors"), true);
    BuildRoot->SetBoolField(TEXT("deterministic_actor_guids"), true);
    BuildRoot->SetNumberField(
        TEXT("deterministic_actor_guid_count"), Metrics.StableActorIdentityCount);
    BuildRoot->SetBoolField(TEXT("deterministic_actor_object_names"), true);
    BuildRoot->SetNumberField(
        TEXT("deterministic_actor_object_name_count"),
        Metrics.StableActorIdentityCount);
    BuildRoot->SetBoolField(TEXT("moving_live_water_configured"), true);
    BuildRoot->SetBoolField(TEXT("source_conditioned_vertex_materials"), true);
    BuildRoot->SetBoolField(TEXT("wet_bank_material_response"), true);
    BuildRoot->SetBoolField(
        TEXT("three_flow_presentations"), Metrics.WaterTileCount == 39);
    BuildRoot->SetBoolField(
        TEXT("solver_and_guide_conditioned_whitewater_foam_overlays"),
        Metrics.WhitewaterFoamActorCount > 0 &&
            Metrics.WhitewaterFoamTriangleCount > 0);
    BuildRoot->SetBoolField(
        TEXT("whitewater_foam_overlays_affect_gameplay_collision"), false);
    BuildRoot->SetBoolField(
        TEXT("whitewater_foam_overlays_affect_hydraulics"), false);
    BuildRoot->SetStringField(
        TEXT("whitewater_foam_overlay_rule"),
        TEXT("one-metre refined non-colliding aerated presentation sheet emitted only over positive solver-derived or review-gated guide-feature-conditioned cells; calm-water opacity and displacement are exactly zero; maximum vertical displacement 0.56 m"));
    BuildRoot->SetStringField(
        TEXT("whitewater_guide_feature_geometry_authority"),
        TEXT("procedural_infill_interpreted_from_guide_inventory_pending_human_review"));
    BuildRoot->SetBoolField(
        TEXT("terminal_visual_water_continuation"),
        Metrics.TerminalVisualWaterActorCount == 1);
    BuildRoot->SetBoolField(
        TEXT("terminal_visual_water_affects_gameplay_collision"), false);
    BuildRoot->SetBoolField(
        TEXT("terminal_visual_water_affects_hydraulics"), false);
    BuildRoot->SetBoolField(
        TEXT("procedural_shoreline_completion_applied"),
        Metrics.ProceduralShorelineCompletionVertexCount > 0);
    BuildRoot->SetStringField(
        TEXT("procedural_shoreline_completion_rule"),
        TEXT("solver wet-mask alpha gaps filled only where decoded terrain is 0.03-0.25 m below decoded water; partial cells emitted only when every dry vertex is inside the 0.05 m terrain-clipped bank skirt; deep gaps omitted; visual only, no collision or hydraulics"));
    BuildRoot->SetBoolField(
        TEXT("far_field_geography_complete"), Metrics.FarFieldPatchCount == 8);
    BuildRoot->SetBoolField(
        TEXT("cc0_scanned_ground_cover_v1"),
        Metrics.Cc0ScannedGroundCoverInstanceCount > 0);
    BuildRoot->SetNumberField(TEXT("cc0_scanned_ground_cover_mesh_forms"), 8);
    BuildRoot->SetNumberField(
        TEXT("cc0_scanned_ground_cover_imported_family_forms"), 19);
    BuildRoot->SetNumberField(
        TEXT("cc0_scanned_ground_cover_import_build_scale"), 1000.0);
    BuildRoot->SetNumberField(
        TEXT("cc0_scanned_ground_cover_forms_per_source_cluster"), 2.0);
    BuildRoot->SetStringField(
        TEXT("cc0_scanned_ground_cover_normalized_patch_target"),
        TEXT("approximately 1.9 m footprint by 0.70 m height before source-conditioned organic scale"));
    BuildRoot->SetStringField(
        TEXT("cc0_scanned_ground_cover_dry_transition_band_m"),
        TEXT("14-30; interleaved four-metre lateral samples only below 34 m; solver/VFX wet-mask cells excluded before placement"));
    BuildRoot->SetBoolField(
        TEXT("cc0_scanned_ground_cover_nanite_enabled"), false);
    BuildRoot->SetStringField(
        TEXT("cc0_scanned_ground_cover_authority"),
        TEXT("Poly Haven Grass Bermuda 01 CC0 morphology used only as non-colliding visual ground cover at the retained source-conditioned clusters plus a bounded dry transition bench; the vegetation-density raster, solver/VFX wet exclusion, bank band, slope screen, and deterministic patch field retain placement authority; no exact South Fork species or ecology claim; no collision, terrain, water, hydraulic, or raft authority"));
    BuildRoot->SetObjectField(
        TEXT("procedural_far_field_microrelief"),
        BuildSouthForkInferredFarFieldReliefManifest());
    BuildRoot->SetBoolField(
        TEXT("detailed_mesh_reuse_requested"), bReuseExistingDetailedMeshes);
    BuildRoot->SetBoolField(TEXT("capture_set_complete"), bAllCapturesSaved);
    BuildRoot->SetBoolField(TEXT("hlod_generation_complete"), false);
    BuildRoot->SetStringField(
        TEXT("hlod_status"),
        TEXT("ready_for_WorldPartitionHLODsBuilder_commandlet"));
    BuildRoot->SetBoolField(TEXT("owner_art_and_readability_review_passed"), false);
    BuildRoot->SetStringField(
        TEXT("authority"),
        TEXT("authoritative sources where present; deterministic procedural infill explicitly labelled; not for navigation"));

    TSharedRef<FJsonObject> MetricRoot = MakeShared<FJsonObject>();
    MetricRoot->SetNumberField(TEXT("terrain_tiles"), Metrics.TerrainTileCount);
    MetricRoot->SetNumberField(TEXT("water_tiles"), Metrics.WaterTileCount);
    MetricRoot->SetNumberField(
        TEXT("whitewater_foam_actors"), Metrics.WhitewaterFoamActorCount);
    MetricRoot->SetNumberField(
        TEXT("terminal_visual_water_actors"), Metrics.TerminalVisualWaterActorCount);
    MetricRoot->SetNumberField(TEXT("far_field_patches"), Metrics.FarFieldPatchCount);
    MetricRoot->SetNumberField(
        TEXT("terrain_triangles"), Metrics.TerrainTriangleCount);
    MetricRoot->SetNumberField(TEXT("water_triangles"), Metrics.WaterTriangleCount);
    MetricRoot->SetNumberField(
        TEXT("whitewater_foam_triangles"),
        Metrics.WhitewaterFoamTriangleCount);
    MetricRoot->SetNumberField(
        TEXT("procedural_shoreline_completion_vertices"),
        Metrics.ProceduralShorelineCompletionVertexCount);
    MetricRoot->SetNumberField(
        TEXT("procedural_shoreline_transition_cells"),
        Metrics.ProceduralShorelineTransitionCellCount);
    MetricRoot->SetNumberField(
        TEXT("terminal_visual_water_triangles"),
        Metrics.TerminalVisualWaterTriangleCount);
    MetricRoot->SetNumberField(
        TEXT("far_field_triangles"), Metrics.FarFieldTriangleCount);
    MetricRoot->SetNumberField(
        TEXT("foliage_instances"), Metrics.FoliageInstanceCount);
    MetricRoot->SetNumberField(
        TEXT("far_field_foliage_instances"),
        Metrics.FarFieldFoliageInstanceCount);
    MetricRoot->SetNumberField(
        TEXT("far_field_detailed_pine_instances"),
        Metrics.FarFieldDetailedPineInstanceCount);
    MetricRoot->SetNumberField(
        TEXT("far_field_pine_card_instances"),
        Metrics.FarFieldPineCardInstanceCount);
    MetricRoot->SetNumberField(
        TEXT("boulder_instances"), Metrics.BoulderInstanceCount);
    MetricRoot->SetNumberField(
        TEXT("boulder_overlap_suppressed_instances"),
        Metrics.BoulderOverlapSuppressedInstanceCount);
    MetricRoot->SetNumberField(
        TEXT("scenic_noncolliding_bank_rock_instances"),
        Metrics.ScenicRockInstanceCount);
    MetricRoot->SetNumberField(
        TEXT("procedural_noncolliding_shore_cobble_instances"),
        Metrics.ShoreCobbleInstanceCount);
    MetricRoot->SetNumberField(
        TEXT("procedural_noncolliding_ground_cover_instances"),
        Metrics.GroundCoverInstanceCount);
    MetricRoot->SetNumberField(
        TEXT("cc0_noncolliding_scanned_ground_cover_instances"),
        Metrics.Cc0ScannedGroundCoverInstanceCount);
    MetricRoot->SetNumberField(
        TEXT("spray_mist_instances"), Metrics.SprayMistInstanceCount);
    MetricRoot->SetNumberField(
        TEXT("infrastructure_actors"), Metrics.InfrastructureActorCount);
    MetricRoot->SetNumberField(
        TEXT("local_reflection_probes"), Metrics.ReflectionProbeCount);
    BuildRoot->SetObjectField(TEXT("metrics"), MetricRoot);

    TArray<TSharedPtr<FJsonValue>> CaptureJson;
    for (const FString& Path : CapturePaths)
    {
        CaptureJson.Add(MakeShared<FJsonValueString>(Path));
    }
    BuildRoot->SetArrayField(TEXT("captures"), CaptureJson);
    FString BuildText;
    const TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&BuildText);
    FJsonSerializer::Serialize(BuildRoot, Writer);
    BuildText += TEXT("\n");
    const FString BuildManifestAbsolute = FPaths::ConvertRelativePathToFull(
        FPaths::Combine(GetRepoRoot(), BuildManifestRelativePath));
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(BuildManifestAbsolute), true);
    const bool bBuildManifestSaved = FFileHelper::SaveStringToFile(
        BuildText,
        *BuildManifestAbsolute,
        FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM);
    OutSummary += FString::Printf(
        TEXT("Full reach: %d terrain tiles, %d water tiles, %d solver-foam overlays, "
             "%lld procedurally completed "
             "shoreline vertices, %lld shoreline transition cells, %d foliage, "
             "%d project-owned ground-cover tufts, "
             "%d scanned ground-cover overlay instances, "
             "%d boulders, %d overlap-suppressed boulder presentation instances, "
             "%d spray/mist instances, %d infrastructure actors.\n"),
        Metrics.TerrainTileCount,
        Metrics.WaterTileCount,
        Metrics.WhitewaterFoamActorCount,
        Metrics.ProceduralShorelineCompletionVertexCount,
        Metrics.ProceduralShorelineTransitionCellCount,
        Metrics.FoliageInstanceCount,
        Metrics.GroundCoverInstanceCount,
        Metrics.Cc0ScannedGroundCoverInstanceCount,
        Metrics.BoulderInstanceCount,
        Metrics.BoulderOverlapSuppressedInstanceCount,
        Metrics.SprayMistInstanceCount,
        Metrics.InfrastructureActorCount);
    return bAllCapturesSaved && bBuildManifestSaved;
}
} // namespace RaftSimEditorEnvironment
