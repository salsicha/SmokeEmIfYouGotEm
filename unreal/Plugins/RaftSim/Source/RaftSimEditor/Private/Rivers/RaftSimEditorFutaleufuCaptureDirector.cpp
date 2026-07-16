#include "Environment/RaftSimEditorEnvironmentInternal.h"

using namespace RaftSimEditorEnvironment;

bool FRaftSimEditorModule::CaptureFutaleufuNativeCanopyCorridorComparison(
    FString& OutSummary)
{
    const FRaftSimLandscapeImportCandidateSpec* FutaleufuCandidate = nullptr;
    const TArray<FRaftSimLandscapeImportCandidateSpec> Candidates = GetLandscapeImportCandidateSpecs();
    for (const FRaftSimLandscapeImportCandidateSpec& Candidate : Candidates)
    {
        if (Candidate.PreviewSpec.RiverId == TEXT("futaleufu_terminator"))
        {
            FutaleufuCandidate = &Candidate;
            break;
        }
    }
    if (!FutaleufuCandidate)
    {
        OutSummary += TEXT("The Futaleufu physical-corridor candidate is not registered.\n");
        return false;
    }

    const FString CaptureRelativeRoot =
        TEXT("docs/environment-captures/photoreal_river_previews/landscape_candidates");
    const FString CaptureRoot = FPaths::Combine(GetRepoRoot(), CaptureRelativeRoot);
    IFileManager::Get().MakeDirectory(*CaptureRoot, true);
    FString BaselineGuidePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("futaleufu_v14_pre_instanced_material_review_guide_seat_downstream.png"));
    FString BaselineRiverEyePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("futaleufu_v14_pre_instanced_material_review_river_eye_downstream.png"));
    FString ComparisonGuidePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("futaleufu_v14_instanced_material_review_guide_seat_downstream.png"));
    FString ComparisonRiverEyePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("futaleufu_v14_instanced_material_review_river_eye_downstream.png"));

    const bool bBaselineGuideCaptured = CapturePreviewImageForSpec(
        FutaleufuCandidate->PreviewSpec,
        CaptureRoot,
        BaselineGuidePath,
        TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"),
        TEXT("pre_native_coigue_corridor_review_guide_seat_downstream"),
        TEXT("Futaleufu baseline guide-seat native-canopy corridor comparison"),
        true,
        OutSummary);
    const bool bBaselineRiverEyeCaptured = CapturePreviewImageForSpec(
        FutaleufuCandidate->PreviewSpec,
        CaptureRoot,
        BaselineRiverEyePath,
        TEXT("RaftSim_RiverEye_DownstreamCaptureCamera"),
        TEXT("pre_native_coigue_corridor_review_river_eye_downstream"),
        TEXT("Futaleufu baseline river-eye native-canopy corridor comparison"),
        true,
        OutSummary);

    FFutaleufuCanopyCorridorComparisonStats GuideStats;
    FFutaleufuCanopyCorridorComparisonStats RiverEyeStats;
    auto MakeWorldSetup = [FutaleufuCandidate](
                              FFutaleufuCanopyCorridorComparisonStats& Stats)
    {
        return [FutaleufuCandidate, &Stats](
                   UWorld* World,
                   ACameraActor* Camera,
                   FString& Summary)
        {
            return AddFutaleufuCanopyCorridorComparisonInstances(
                World,
                Camera,
                *FutaleufuCandidate,
                EFutaleufuCanopyCorridorRenderMode::Native,
                Stats,
                Summary);
        };
    };
    const bool bComparisonGuideCaptured = CapturePreviewImageForSpec(
        FutaleufuCandidate->PreviewSpec,
        CaptureRoot,
        ComparisonGuidePath,
        TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"),
        TEXT("native_coigue_corridor_review_guide_seat_downstream"),
        TEXT("Futaleufu guide-seat source-masked native-coigue corridor comparison"),
        true,
        OutSummary,
        MakeWorldSetup(GuideStats));
    const bool bComparisonRiverEyeCaptured = CapturePreviewImageForSpec(
        FutaleufuCandidate->PreviewSpec,
        CaptureRoot,
        ComparisonRiverEyePath,
        TEXT("RaftSim_RiverEye_DownstreamCaptureCamera"),
        TEXT("native_coigue_corridor_review_river_eye_downstream"),
        TEXT("Futaleufu river-eye source-masked native-coigue corridor comparison"),
        true,
        OutSummary,
        MakeWorldSetup(RiverEyeStats));
    const bool bAllCaptured =
        bBaselineGuideCaptured && bBaselineRiverEyeCaptured &&
        bComparisonGuideCaptured && bComparisonRiverEyeCaptured;

    auto MakeStatsObject = [](const FFutaleufuCanopyCorridorComparisonStats& Stats)
    {
        TSharedRef<FJsonObject> Object = MakeShared<FJsonObject>();
        Object->SetNumberField(TEXT("candidate_count"), Stats.CandidateCount);
        Object->SetNumberField(TEXT("accepted_tree_count"), Stats.AcceptedTreeCount);
        Object->SetNumberField(TEXT("near_full_tree_count"), Stats.NearTreeCount);
        Object->SetNumberField(TEXT("mid_tree_count"), Stats.MidTreeCount);
        Object->SetNumberField(TEXT("runtime_far_tree_count"), Stats.FarTreeCount);
        Object->SetNumberField(TEXT("hidden_fallback_pve_actor_count"), Stats.HiddenFallbackActorCount);
        Object->SetNumberField(TEXT("rejected_natural_gap_count"), Stats.RejectedNaturalGapCount);
        Object->SetNumberField(
            TEXT("rejected_vegetation_mask_count"),
            Stats.RejectedVegetationMaskCount);
        Object->SetNumberField(TEXT("rejected_water_mask_count"), Stats.RejectedWaterMaskCount);
        Object->SetNumberField(TEXT("rejected_elevation_count"), Stats.RejectedElevationCount);
        Object->SetNumberField(TEXT("rejected_slope_count"), Stats.RejectedSlopeCount);
        Object->SetNumberField(TEXT("rejected_dry_aspect_count"), Stats.RejectedDryAspectCount);
        Object->SetNumberField(TEXT("rejected_spacing_count"), Stats.RejectedSpacingCount);
        Object->SetNumberField(
            TEXT("minimum_accepted_slope_degrees"),
            Stats.MinimumAcceptedSlopeDegrees);
        Object->SetNumberField(
            TEXT("maximum_accepted_slope_degrees"),
            Stats.MaximumAcceptedSlopeDegrees);
        Object->SetNumberField(
            TEXT("minimum_accepted_elevation_m"),
            Stats.MinimumAcceptedElevationCm * 0.01f);
        Object->SetNumberField(
            TEXT("maximum_accepted_elevation_m"),
            Stats.MaximumAcceptedElevationCm * 0.01f);
        Object->SetNumberField(
            TEXT("mean_accepted_vegetation_mask"),
            Stats.AcceptedTreeCount > 0
                ? Stats.AcceptedVegetationMaskSum / Stats.AcceptedTreeCount
                : 0.0);
        Object->SetNumberField(
            TEXT("mean_accepted_water_mask"),
            Stats.AcceptedTreeCount > 0
                ? Stats.AcceptedWaterMaskSum / Stats.AcceptedTreeCount
                : 0.0);
        return Object;
    };

    TSharedRef<FJsonObject> Report = MakeShared<FJsonObject>();
    Report->SetStringField(
        TEXT("schema"),
        TEXT("raftsim.unreal.futaleufu_native_canopy_corridor_comparison.v2"));
    Report->SetStringField(TEXT("river_id"), TEXT("futaleufu_terminator"));
    Report->SetStringField(
        TEXT("status"),
        bAllCaptured
            ? TEXT("paired_source_masked_transient_corridor_comparison_captured_pending_human_review")
            : TEXT("one_or_more_corridor_comparison_captures_failed"));
    Report->SetBoolField(TEXT("production_promoted"), false);
    Report->SetBoolField(TEXT("source_map_modified"), false);
    Report->SetBoolField(TEXT("collision_or_gameplay_authority_modified"), false);
    Report->SetStringField(TEXT("source_map"), FutaleufuCandidate->PreviewSpec.MapPackagePath);
    Report->SetStringField(
        TEXT("source_manifest"),
        FutaleufuCandidate->PreviewSpec.SourceManifest);
    Report->SetStringField(
        TEXT("vegetation_mask"),
        FutaleufuCandidate->PreviewSpec.VegetationMaskImage);
    Report->SetStringField(TEXT("water_mask"), FutaleufuCandidate->PreviewSpec.WaterMaskImage);
    Report->SetStringField(
        TEXT("placement_boundary"),
        TEXT("Transient review-only HISM components replace only visible temporary PVE foliage for each capture; source Landscape, dense visual terrain, physical river ribbon, water, rocks, collision, solver, and saved map remain unchanged."));
    TSharedRef<FJsonObject> MaterialContract = MakeShared<FJsonObject>();
    MaterialContract->SetBoolField(TEXT("bark_instanced_static_meshes_usage_persisted"), true);
    MaterialContract->SetBoolField(TEXT("leaf_instanced_static_meshes_usage_persisted"), true);
    MaterialContract->SetStringField(
        TEXT("compile_order"),
        TEXT("material expression refresh, InstancedStaticMeshes usage enablement, shader completion, package save, then HISM creation"));
    MaterialContract->SetStringField(
        TEXT("experiment"),
        TEXT("V14 isolates whether the V13 corridor silhouette failure was caused by late automatic HISM shader-permutation creation"));
    Report->SetObjectField(TEXT("material_contract"), MaterialContract);

    TSharedRef<FJsonObject> Placement = MakeShared<FJsonObject>();
    Placement->SetStringField(
        TEXT("mask_mapping"),
        TEXT("north-up source image UV mapped over the physical Landscape bounds; Unreal +Y follows source rows south from the northwest corner"));
    Placement->SetStringField(
        TEXT("distribution"),
        TEXT("Halton low-discrepancy candidates with 15 m minimum-spacing rejection and three macro plus deterministic micro canopy gaps"));
    Placement->SetNumberField(TEXT("target_tree_count_per_view"), 1200);
    Placement->SetNumberField(TEXT("centerline_progress_min"), 0.55);
    Placement->SetNumberField(TEXT("centerline_progress_max"), 0.91);
    Placement->SetNumberField(TEXT("river_setback_m"), 65.0);
    Placement->SetNumberField(TEXT("maximum_lateral_offset_m"), 300.0);
    Placement->SetNumberField(TEXT("minimum_spacing_m"), 15.0);
    Placement->SetNumberField(TEXT("minimum_vegetation_mask"), 0.34);
    Placement->SetNumberField(TEXT("maximum_water_mask"), 0.28);
    Placement->SetNumberField(TEXT("minimum_elevation_m"), 100.0);
    Placement->SetNumberField(TEXT("maximum_elevation_m"), 900.0);
    Placement->SetNumberField(TEXT("maximum_slope_degrees"), 39.0);
    Placement->SetStringField(
        TEXT("aspect_treatment"),
        TEXT("Moist southwest-facing and flat sites retained; dry-aspect candidates below 0.28 suitability are deterministically thinned by 52 percent."));
    Placement->SetNumberField(TEXT("near_full_representation_max_distance_m"), 300.0);
    Placement->SetNumberField(TEXT("mid_representation_max_distance_m"), 500.0);
    Placement->SetStringField(
        TEXT("far_representation"),
        TEXT("v12 runtime far crown beyond 500 m; 94-percent family resource reduction measured in the isolated benchmark"));
    Report->SetObjectField(TEXT("placement_contract"), Placement);

    TSharedRef<FJsonObject> Captures = MakeShared<FJsonObject>();
    Captures->SetStringField(TEXT("baseline_guide_seat"), BaselineGuidePath);
    Captures->SetStringField(TEXT("baseline_river_eye"), BaselineRiverEyePath);
    Captures->SetStringField(TEXT("comparison_guide_seat"), ComparisonGuidePath);
    Captures->SetStringField(TEXT("comparison_river_eye"), ComparisonRiverEyePath);
    Captures->SetBoolField(TEXT("all_captured"), bAllCaptured);
    Report->SetObjectField(TEXT("captures"), Captures);
    Report->SetObjectField(TEXT("guide_seat_stats"), MakeStatsObject(GuideStats));
    Report->SetObjectField(TEXT("river_eye_stats"), MakeStatsObject(RiverEyeStats));

    TArray<TSharedPtr<FJsonValue>> OpenGates;
    for (const TCHAR* Gate : {
             TEXT("paired_human_visual_review"),
             TEXT("moving_camera_transition_and_temporal_wind_review"),
             TEXT("second_native_canopy_species_and_understory_strata"),
             TEXT("guide_ecology_and_hazard_readability_review"),
             TEXT("masked_overdraw_streaming_and_culling_measurement"),
             TEXT("packaged_desktop_and_on_device_VR_performance")})
    {
        OpenGates.Add(MakeShared<FJsonValueString>(Gate));
    }
    Report->SetArrayField(TEXT("open_promotion_gates"), OpenGates);

    FString SerializedReport;
    const TSharedRef<TJsonWriter<TCHAR, TPrettyJsonPrintPolicy<TCHAR>>> Writer =
        TJsonWriterFactory<TCHAR, TPrettyJsonPrintPolicy<TCHAR>>::Create(&SerializedReport);
    const bool bSerialized = FJsonSerializer::Serialize(Report, Writer);
    SerializedReport += TEXT("\n");
    const FString ReportRelativePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("futaleufu_native_canopy_coigue_v14_instanced_material_comparison_report.json"));
    const FString ReportPath = FPaths::Combine(GetRepoRoot(), ReportRelativePath);
    const bool bReportSaved =
        bSerialized && FFileHelper::SaveStringToFile(SerializedReport, *ReportPath);
    OutSummary += FString::Printf(
        TEXT("%s Futaleufu native-canopy corridor comparison report -> %s\n"),
        bReportSaved ? TEXT("Saved") : TEXT("Failed to save"),
        *ReportPath);
    return bAllCaptured && bReportSaved;
}

bool FRaftSimEditorModule::CaptureFutaleufuDenseCanopyComparison(
    FString& OutSummary)
{
    const FRaftSimLandscapeImportCandidateSpec* FutaleufuCandidate = nullptr;
    const TArray<FRaftSimLandscapeImportCandidateSpec> Candidates =
        GetLandscapeImportCandidateSpecs();
    for (const FRaftSimLandscapeImportCandidateSpec& Candidate : Candidates)
    {
        if (Candidate.PreviewSpec.RiverId == TEXT("futaleufu_terminator"))
        {
            FutaleufuCandidate = &Candidate;
            break;
        }
    }
    if (!FutaleufuCandidate)
    {
        OutSummary += TEXT("The Futaleufu physical-corridor candidate is not registered.\n");
        return false;
    }

    const FString CaptureRelativeRoot =
        TEXT("docs/environment-captures/photoreal_river_previews/landscape_candidates");
    const FString CaptureRoot = FPaths::Combine(GetRepoRoot(), CaptureRelativeRoot);
    IFileManager::Get().MakeDirectory(*CaptureRoot, true);
    FString SparseGuidePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("futaleufu_v24_sparse_alpha2_guide_seat_downstream.png"));
    FString SparseRiverEyePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("futaleufu_v24_sparse_alpha2_river_eye_downstream.png"));
    FString DenseGuidePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("futaleufu_v24_dense_source_masked_alpha2_guide_seat_downstream.png"));
    FString DenseRiverEyePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("futaleufu_v24_dense_source_masked_alpha2_river_eye_downstream.png"));

    FFutaleufuCanopyCorridorComparisonStats SparseGuideStats;
    FFutaleufuCanopyCorridorComparisonStats SparseRiverEyeStats;
    FFutaleufuCanopyCorridorComparisonStats DenseGuideStats;
    FFutaleufuCanopyCorridorComparisonStats DenseRiverEyeStats;
    auto MakeWorldSetup = [FutaleufuCandidate](
                              bool bDenseLocalReview,
                              FFutaleufuCanopyCorridorComparisonStats& Stats)
    {
        return [FutaleufuCandidate, bDenseLocalReview, &Stats](
                   UWorld* World,
                   ACameraActor* Camera,
                   FString& Summary)
        {
            return AddFutaleufuCanopyCorridorComparisonInstances(
                World,
                Camera,
                *FutaleufuCandidate,
                EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleTwoNoShadow,
                Stats,
                Summary,
                bDenseLocalReview);
        };
    };

    const bool bSparseGuideCaptured = CapturePreviewImageForSpec(
        FutaleufuCandidate->PreviewSpec,
        CaptureRoot,
        SparseGuidePath,
        TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"),
        TEXT("futaleufu_v24_sparse_alpha2_guide_seat_downstream"),
        TEXT("Futaleufu guide-seat retained sparse alpha2 no-shadow canopy"),
        true,
        OutSummary,
        MakeWorldSetup(false, SparseGuideStats));
    const bool bSparseRiverEyeCaptured = CapturePreviewImageForSpec(
        FutaleufuCandidate->PreviewSpec,
        CaptureRoot,
        SparseRiverEyePath,
        TEXT("RaftSim_RiverEye_DownstreamCaptureCamera"),
        TEXT("futaleufu_v24_sparse_alpha2_river_eye_downstream"),
        TEXT("Futaleufu river-eye retained sparse alpha2 no-shadow canopy"),
        true,
        OutSummary,
        MakeWorldSetup(false, SparseRiverEyeStats));
    const bool bDenseGuideCaptured = CapturePreviewImageForSpec(
        FutaleufuCandidate->PreviewSpec,
        CaptureRoot,
        DenseGuidePath,
        TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"),
        TEXT("futaleufu_v24_dense_source_masked_alpha2_guide_seat_downstream"),
        TEXT("Futaleufu guide-seat dense camera-local source-masked alpha2 no-shadow canopy"),
        true,
        OutSummary,
        MakeWorldSetup(true, DenseGuideStats));
    const bool bDenseRiverEyeCaptured = CapturePreviewImageForSpec(
        FutaleufuCandidate->PreviewSpec,
        CaptureRoot,
        DenseRiverEyePath,
        TEXT("RaftSim_RiverEye_DownstreamCaptureCamera"),
        TEXT("futaleufu_v24_dense_source_masked_alpha2_river_eye_downstream"),
        TEXT("Futaleufu river-eye dense camera-local source-masked alpha2 no-shadow canopy"),
        true,
        OutSummary,
        MakeWorldSetup(true, DenseRiverEyeStats));
    const bool bAllCaptured =
        bSparseGuideCaptured && bSparseRiverEyeCaptured &&
        bDenseGuideCaptured && bDenseRiverEyeCaptured;

    auto MakeStatsObject = [](const FFutaleufuCanopyCorridorComparisonStats& Stats)
    {
        TSharedRef<FJsonObject> Object = MakeShared<FJsonObject>();
        Object->SetBoolField(TEXT("dense_local_review"), Stats.bDenseLocalReview);
        Object->SetNumberField(TEXT("candidate_count"), Stats.CandidateCount);
        Object->SetNumberField(TEXT("target_tree_count"), Stats.TargetTreeCount);
        Object->SetNumberField(TEXT("accepted_tree_count"), Stats.AcceptedTreeCount);
        Object->SetNumberField(TEXT("near_full_tree_count"), Stats.NearTreeCount);
        Object->SetNumberField(TEXT("mid_tree_count"), Stats.MidTreeCount);
        Object->SetNumberField(TEXT("runtime_far_tree_count"), Stats.FarTreeCount);
        Object->SetNumberField(
            TEXT("hidden_fallback_pve_actor_count"),
            Stats.HiddenFallbackActorCount);
        Object->SetNumberField(
            TEXT("rejected_vegetation_mask_count"),
            Stats.RejectedVegetationMaskCount);
        Object->SetNumberField(
            TEXT("rejected_water_mask_count"),
            Stats.RejectedWaterMaskCount);
        Object->SetNumberField(TEXT("rejected_slope_count"), Stats.RejectedSlopeCount);
        Object->SetNumberField(TEXT("rejected_spacing_count"), Stats.RejectedSpacingCount);
        Object->SetNumberField(TEXT("centerline_progress_min"), Stats.ProgressMinimum);
        Object->SetNumberField(TEXT("centerline_progress_max"), Stats.ProgressMaximum);
        Object->SetNumberField(TEXT("minimum_spacing_m"), Stats.MinimumSpacingCm * 0.01f);
        Object->SetNumberField(TEXT("river_setback_m"), Stats.RiverSetbackCm * 0.01f);
        Object->SetNumberField(
            TEXT("maximum_lateral_offset_m"),
            Stats.MaximumLateralOffsetCm * 0.01f);
        Object->SetNumberField(
            TEXT("mean_accepted_vegetation_mask"),
            Stats.AcceptedTreeCount > 0
                ? Stats.AcceptedVegetationMaskSum / Stats.AcceptedTreeCount
                : 0.0);
        Object->SetNumberField(
            TEXT("mean_accepted_water_mask"),
            Stats.AcceptedTreeCount > 0
                ? Stats.AcceptedWaterMaskSum / Stats.AcceptedTreeCount
                : 0.0);
        return Object;
    };

    TSharedRef<FJsonObject> Report = MakeShared<FJsonObject>();
    Report->SetStringField(
        TEXT("schema"),
        TEXT("raftsim.unreal.futaleufu_dense_canopy_comparison.v1"));
    Report->SetStringField(TEXT("river_id"), TEXT("futaleufu_terminator"));
    Report->SetStringField(
        TEXT("status"),
        bAllCaptured
            ? TEXT("paired_v24_sparse_dense_source_masked_canopy_captured_pending_human_review")
            : TEXT("one_or_more_v24_sparse_dense_canopy_captures_failed"));
    Report->SetBoolField(TEXT("production_promoted"), false);
    Report->SetBoolField(TEXT("corridor_substitution_performed"), false);
    Report->SetBoolField(TEXT("source_map_modified"), false);
    Report->SetBoolField(TEXT("landscape_or_collision_modified"), false);
    Report->SetBoolField(TEXT("hydrodynamic_or_gameplay_authority_modified"), false);
    Report->SetStringField(TEXT("source_map"), FutaleufuCandidate->PreviewSpec.MapPackagePath);
    Report->SetStringField(
        TEXT("source_manifest"),
        FutaleufuCandidate->PreviewSpec.SourceManifest);
    Report->SetStringField(
        TEXT("vegetation_mask"),
        FutaleufuCandidate->PreviewSpec.VegetationMaskImage);
    Report->SetStringField(
        TEXT("water_mask"),
        FutaleufuCandidate->PreviewSpec.WaterMaskImage);
    Report->SetStringField(
        TEXT("fixed_between_variants"),
        TEXT("project-owned eight-form coigue meshes, V12 runtime-far representation, V22 RGB-padded leaf atlas, alpha2 no-shadow material, source masks, deterministic Halton candidates, terrain, water, rocks, cameras, lighting, physics, and saved map"));
    Report->SetStringField(
        TEXT("changed_in_dense_variant"),
        TEXT("camera-local centerline window, 9000-tree target, 6.5 m minimum spacing, 24 m river setback, 750 m maximum lateral coverage, reduced deterministic micro-gap thinning, and 0.78-1.12 scale range"));
    Report->SetStringField(
        TEXT("authority_boundary"),
        TEXT("transient review-only non-colliding HISM placement; source Landscape, visual terrain, physical river ribbon, collision, custom C++ water, GeoClaw, feature forcing, raft contact, hazards, gameplay, and saved-map authority remain unchanged"));

    TSharedRef<FJsonObject> Stats = MakeShared<FJsonObject>();
    Stats->SetObjectField(TEXT("sparse_guide_seat"), MakeStatsObject(SparseGuideStats));
    Stats->SetObjectField(TEXT("sparse_river_eye"), MakeStatsObject(SparseRiverEyeStats));
    Stats->SetObjectField(TEXT("dense_guide_seat"), MakeStatsObject(DenseGuideStats));
    Stats->SetObjectField(TEXT("dense_river_eye"), MakeStatsObject(DenseRiverEyeStats));
    Report->SetObjectField(TEXT("placement_statistics"), Stats);

    TSharedRef<FJsonObject> Captures = MakeShared<FJsonObject>();
    Captures->SetStringField(TEXT("sparse_guide_seat"), SparseGuidePath);
    Captures->SetStringField(TEXT("sparse_river_eye"), SparseRiverEyePath);
    Captures->SetStringField(TEXT("dense_guide_seat"), DenseGuidePath);
    Captures->SetStringField(TEXT("dense_river_eye"), DenseRiverEyePath);
    Captures->SetBoolField(TEXT("all_captured"), bAllCaptured);
    Report->SetObjectField(TEXT("captures"), Captures);

    TArray<TSharedPtr<FJsonValue>> OpenGates;
    for (const TCHAR* Gate : {
             TEXT("paired_human_visual_review"),
             TEXT("source_mask_and_aerial_alignment_review"),
             TEXT("second_ecology_reviewed_native_canopy_species"),
             TEXT("riparian_shrub_understory_fern_bamboo_epiphyte_and_deadwood_strata"),
             TEXT("terrain_water_boulder_and_atmosphere_review"),
             TEXT("moving_camera_temporal_stability_and_wind"),
             TEXT("masked_overdraw_streaming_culling_and_multiplatform_performance"),
             TEXT("guide_ecology_geospatial_rights_and_art_approval")})
    {
        OpenGates.Add(MakeShared<FJsonValueString>(Gate));
    }
    Report->SetArrayField(TEXT("open_promotion_gates"), OpenGates);

    FString SerializedReport;
    const TSharedRef<TJsonWriter<TCHAR, TPrettyJsonPrintPolicy<TCHAR>>> Writer =
        TJsonWriterFactory<TCHAR, TPrettyJsonPrintPolicy<TCHAR>>::Create(&SerializedReport);
    const bool bSerialized = FJsonSerializer::Serialize(Report, Writer);
    SerializedReport += TEXT("\n");
    const FString ReportRelativePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("futaleufu_native_canopy_coigue_v24_dense_canopy_comparison_report.json"));
    const FString ReportPath = FPaths::Combine(GetRepoRoot(), ReportRelativePath);
    const bool bReportSaved =
        bSerialized && FFileHelper::SaveStringToFile(SerializedReport, *ReportPath);
    OutSummary += FString::Printf(
        TEXT("%s Futaleufu V24 sparse/dense canopy comparison report -> %s\n"),
        bReportSaved ? TEXT("Saved") : TEXT("Failed to save"),
        *ReportPath);
    return bAllCaptured && bReportSaved;
}

bool FRaftSimEditorModule::CaptureFutaleufuAreaSampledCanopyComparison(
    FString& OutSummary)
{
    const FRaftSimLandscapeImportCandidateSpec* FutaleufuCandidate = nullptr;
    const TArray<FRaftSimLandscapeImportCandidateSpec> Candidates =
        GetLandscapeImportCandidateSpecs();
    for (const FRaftSimLandscapeImportCandidateSpec& Candidate : Candidates)
    {
        if (Candidate.PreviewSpec.RiverId == TEXT("futaleufu_terminator"))
        {
            FutaleufuCandidate = &Candidate;
            break;
        }
    }
    if (!FutaleufuCandidate)
    {
        OutSummary += TEXT("The Futaleufu physical-corridor candidate is not registered.\n");
        return false;
    }

    const FString CaptureRelativeRoot =
        TEXT("docs/environment-captures/photoreal_river_previews/landscape_candidates");
    const FString CaptureRoot = FPaths::Combine(GetRepoRoot(), CaptureRelativeRoot);
    IFileManager::Get().MakeDirectory(*CaptureRoot, true);
    FString CenterlineGuidePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("futaleufu_v25_centerline_dense_alpha2_guide_seat_downstream.png"));
    FString CenterlineRiverEyePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("futaleufu_v25_centerline_dense_alpha2_river_eye_downstream.png"));
    FString AreaGuidePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("futaleufu_v25_area_sampled_alpha2_guide_seat_downstream.png"));
    FString AreaRiverEyePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("futaleufu_v25_area_sampled_alpha2_river_eye_downstream.png"));

    FFutaleufuCanopyCorridorComparisonStats CenterlineGuideStats;
    FFutaleufuCanopyCorridorComparisonStats CenterlineRiverEyeStats;
    FFutaleufuCanopyCorridorComparisonStats AreaGuideStats;
    FFutaleufuCanopyCorridorComparisonStats AreaRiverEyeStats;
    auto MakeWorldSetup = [FutaleufuCandidate](
                              bool bAreaSampledReview,
                              FFutaleufuCanopyCorridorComparisonStats& Stats)
    {
        return [FutaleufuCandidate, bAreaSampledReview, &Stats](
                   UWorld* World,
                   ACameraActor* Camera,
                   FString& Summary)
        {
            return AddFutaleufuCanopyCorridorComparisonInstances(
                World,
                Camera,
                *FutaleufuCandidate,
                EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleTwoNoShadow,
                Stats,
                Summary,
                true,
                bAreaSampledReview);
        };
    };

    const bool bCenterlineGuideCaptured = CapturePreviewImageForSpec(
        FutaleufuCandidate->PreviewSpec,
        CaptureRoot,
        CenterlineGuidePath,
        TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"),
        TEXT("futaleufu_v25_centerline_dense_alpha2_guide_seat_downstream"),
        TEXT("Futaleufu guide-seat V24 centerline-dense alpha2 no-shadow baseline"),
        true,
        OutSummary,
        MakeWorldSetup(false, CenterlineGuideStats));
    const bool bCenterlineRiverEyeCaptured = CapturePreviewImageForSpec(
        FutaleufuCandidate->PreviewSpec,
        CaptureRoot,
        CenterlineRiverEyePath,
        TEXT("RaftSim_RiverEye_DownstreamCaptureCamera"),
        TEXT("futaleufu_v25_centerline_dense_alpha2_river_eye_downstream"),
        TEXT("Futaleufu river-eye V24 centerline-dense alpha2 no-shadow baseline"),
        true,
        OutSummary,
        MakeWorldSetup(false, CenterlineRiverEyeStats));
    const bool bAreaGuideCaptured = CapturePreviewImageForSpec(
        FutaleufuCandidate->PreviewSpec,
        CaptureRoot,
        AreaGuidePath,
        TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"),
        TEXT("futaleufu_v25_area_sampled_alpha2_guide_seat_downstream"),
        TEXT("Futaleufu guide-seat 2D area-sampled source-masked alpha2 no-shadow canopy"),
        true,
        OutSummary,
        MakeWorldSetup(true, AreaGuideStats));
    const bool bAreaRiverEyeCaptured = CapturePreviewImageForSpec(
        FutaleufuCandidate->PreviewSpec,
        CaptureRoot,
        AreaRiverEyePath,
        TEXT("RaftSim_RiverEye_DownstreamCaptureCamera"),
        TEXT("futaleufu_v25_area_sampled_alpha2_river_eye_downstream"),
        TEXT("Futaleufu river-eye 2D area-sampled source-masked alpha2 no-shadow canopy"),
        true,
        OutSummary,
        MakeWorldSetup(true, AreaRiverEyeStats));
    const bool bAllCaptured =
        bCenterlineGuideCaptured && bCenterlineRiverEyeCaptured &&
        bAreaGuideCaptured && bAreaRiverEyeCaptured;

    auto MakeStatsObject = [](const FFutaleufuCanopyCorridorComparisonStats& Stats)
    {
        TSharedRef<FJsonObject> Object = MakeShared<FJsonObject>();
        Object->SetBoolField(TEXT("dense_local_review"), Stats.bDenseLocalReview);
        Object->SetBoolField(TEXT("area_sampled_review"), Stats.bAreaSampledReview);
        Object->SetNumberField(TEXT("candidate_count"), Stats.CandidateCount);
        Object->SetNumberField(TEXT("target_tree_count"), Stats.TargetTreeCount);
        Object->SetNumberField(TEXT("accepted_tree_count"), Stats.AcceptedTreeCount);
        Object->SetNumberField(TEXT("near_full_tree_count"), Stats.NearTreeCount);
        Object->SetNumberField(TEXT("mid_tree_count"), Stats.MidTreeCount);
        Object->SetNumberField(TEXT("runtime_far_tree_count"), Stats.FarTreeCount);
        Object->SetNumberField(
            TEXT("hidden_fallback_pve_actor_count"),
            Stats.HiddenFallbackActorCount);
        Object->SetNumberField(
            TEXT("rejected_natural_gap_count"),
            Stats.RejectedNaturalGapCount);
        Object->SetNumberField(
            TEXT("rejected_vegetation_mask_count"),
            Stats.RejectedVegetationMaskCount);
        Object->SetNumberField(
            TEXT("rejected_water_mask_count"),
            Stats.RejectedWaterMaskCount);
        Object->SetNumberField(
            TEXT("rejected_river_setback_count"),
            Stats.RejectedRiverSetbackCount);
        Object->SetNumberField(
            TEXT("rejected_stand_density_count"),
            Stats.RejectedStandDensityCount);
        Object->SetNumberField(TEXT("rejected_slope_count"), Stats.RejectedSlopeCount);
        Object->SetNumberField(TEXT("rejected_spacing_count"), Stats.RejectedSpacingCount);
        Object->SetNumberField(TEXT("centerline_progress_min"), Stats.ProgressMinimum);
        Object->SetNumberField(TEXT("centerline_progress_max"), Stats.ProgressMaximum);
        Object->SetNumberField(TEXT("minimum_spacing_m"), Stats.MinimumSpacingCm * 0.01f);
        Object->SetNumberField(TEXT("river_setback_m"), Stats.RiverSetbackCm * 0.01f);
        Object->SetNumberField(
            TEXT("maximum_lateral_offset_m"),
            Stats.MaximumLateralOffsetCm * 0.01f);
        Object->SetNumberField(
            TEXT("sampling_half_extent_m"),
            Stats.SamplingHalfExtentCm * 0.01f);
        Object->SetNumberField(
            TEXT("minimum_accepted_river_distance_m"),
            Stats.AcceptedTreeCount > 0
                ? Stats.MinimumAcceptedRiverDistanceCm * 0.01f
                : 0.0f);
        Object->SetNumberField(
            TEXT("maximum_accepted_river_distance_m"),
            Stats.AcceptedTreeCount > 0
                ? Stats.MaximumAcceptedRiverDistanceCm * 0.01f
                : 0.0f);
        Object->SetNumberField(
            TEXT("mean_accepted_vegetation_mask"),
            Stats.AcceptedTreeCount > 0
                ? Stats.AcceptedVegetationMaskSum / Stats.AcceptedTreeCount
                : 0.0);
        Object->SetNumberField(
            TEXT("mean_accepted_water_mask"),
            Stats.AcceptedTreeCount > 0
                ? Stats.AcceptedWaterMaskSum / Stats.AcceptedTreeCount
                : 0.0);
        return Object;
    };

    TSharedRef<FJsonObject> Report = MakeShared<FJsonObject>();
    Report->SetStringField(
        TEXT("schema"),
        TEXT("raftsim.unreal.futaleufu_area_sampled_canopy_comparison.v1"));
    Report->SetStringField(TEXT("river_id"), TEXT("futaleufu_terminator"));
    Report->SetStringField(
        TEXT("status"),
        bAllCaptured
            ? TEXT("paired_v25_centerline_area_sampled_canopy_captured_pending_human_review")
            : TEXT("one_or_more_v25_area_sampled_canopy_captures_failed"));
    Report->SetBoolField(TEXT("production_promoted"), false);
    Report->SetBoolField(TEXT("corridor_substitution_performed"), false);
    Report->SetBoolField(TEXT("source_map_modified"), false);
    Report->SetBoolField(TEXT("landscape_or_collision_modified"), false);
    Report->SetBoolField(TEXT("hydrodynamic_or_gameplay_authority_modified"), false);
    Report->SetStringField(TEXT("source_map"), FutaleufuCandidate->PreviewSpec.MapPackagePath);
    Report->SetStringField(
        TEXT("source_manifest"),
        FutaleufuCandidate->PreviewSpec.SourceManifest);
    Report->SetStringField(
        TEXT("vegetation_mask"),
        FutaleufuCandidate->PreviewSpec.VegetationMaskImage);
    Report->SetStringField(
        TEXT("water_mask"),
        FutaleufuCandidate->PreviewSpec.WaterMaskImage);
    Report->SetStringField(
        TEXT("fixed_between_variants"),
        TEXT("9000-tree target, 6.5 m spacing, 24 m river setback, project-owned eight-form coigue meshes, V12 runtime-far representation, V22 RGB-padded leaf atlas, alpha2 no-shadow material, source masks, terrain, water, rocks, cameras, lighting, physics, and saved map"));
    Report->SetStringField(
        TEXT("changed_in_area_sampled_variant"),
        TEXT("deterministic direct 2D Halton sampling in a 2.2 km camera-local square, true nearest-centerline setback enforcement, probabilistic source-mask feathering, and broad plus mid-scale deterministic stand-density fields replace centerline progress/lateral placement and stripe-like progress gaps"));
    Report->SetStringField(
        TEXT("authority_boundary"),
        TEXT("transient review-only non-colliding HISM placement; source Landscape, visual terrain, physical river ribbon, collision, custom C++ water, GeoClaw, feature forcing, raft contact, hazards, gameplay, and saved-map authority remain unchanged"));

    TSharedRef<FJsonObject> Stats = MakeShared<FJsonObject>();
    Stats->SetObjectField(
        TEXT("centerline_guide_seat"),
        MakeStatsObject(CenterlineGuideStats));
    Stats->SetObjectField(
        TEXT("centerline_river_eye"),
        MakeStatsObject(CenterlineRiverEyeStats));
    Stats->SetObjectField(TEXT("area_sampled_guide_seat"), MakeStatsObject(AreaGuideStats));
    Stats->SetObjectField(TEXT("area_sampled_river_eye"), MakeStatsObject(AreaRiverEyeStats));
    Report->SetObjectField(TEXT("placement_statistics"), Stats);

    TSharedRef<FJsonObject> Captures = MakeShared<FJsonObject>();
    Captures->SetStringField(TEXT("centerline_guide_seat"), CenterlineGuidePath);
    Captures->SetStringField(TEXT("centerline_river_eye"), CenterlineRiverEyePath);
    Captures->SetStringField(TEXT("area_sampled_guide_seat"), AreaGuidePath);
    Captures->SetStringField(TEXT("area_sampled_river_eye"), AreaRiverEyePath);
    Captures->SetBoolField(TEXT("all_captured"), bAllCaptured);
    Report->SetObjectField(TEXT("captures"), Captures);

    TArray<TSharedPtr<FJsonValue>> OpenGates;
    for (const TCHAR* Gate : {
             TEXT("paired_human_visual_review"),
             TEXT("source_mask_and_aerial_alignment_review"),
             TEXT("second_ecology_reviewed_native_canopy_species"),
             TEXT("riparian_shrub_understory_fern_bamboo_epiphyte_and_deadwood_strata"),
             TEXT("terrain_water_boulder_and_atmosphere_review"),
             TEXT("moving_camera_temporal_stability_and_wind"),
             TEXT("masked_overdraw_streaming_culling_and_multiplatform_performance"),
             TEXT("guide_ecology_geospatial_rights_and_art_approval")})
    {
        OpenGates.Add(MakeShared<FJsonValueString>(Gate));
    }
    Report->SetArrayField(TEXT("open_promotion_gates"), OpenGates);

    FString SerializedReport;
    const TSharedRef<TJsonWriter<TCHAR, TPrettyJsonPrintPolicy<TCHAR>>> Writer =
        TJsonWriterFactory<TCHAR, TPrettyJsonPrintPolicy<TCHAR>>::Create(&SerializedReport);
    const bool bSerialized = FJsonSerializer::Serialize(Report, Writer);
    SerializedReport += TEXT("\n");
    const FString ReportRelativePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("futaleufu_native_canopy_coigue_v25_area_sampled_comparison_report.json"));
    const FString ReportPath = FPaths::Combine(GetRepoRoot(), ReportRelativePath);
    const bool bReportSaved =
        bSerialized && FFileHelper::SaveStringToFile(SerializedReport, *ReportPath);
    OutSummary += FString::Printf(
        TEXT("%s Futaleufu V25 centerline/area-sampled canopy comparison report -> %s\n"),
        bReportSaved ? TEXT("Saved") : TEXT("Failed to save"),
        *ReportPath);
    return bAllCaptured && bReportSaved;
}

bool FRaftSimEditorModule::CaptureFutaleufuWorldStableCanopyComparison(
    FString& OutSummary)
{
    const FRaftSimLandscapeImportCandidateSpec* FutaleufuCandidate = nullptr;
    const TArray<FRaftSimLandscapeImportCandidateSpec> Candidates =
        GetLandscapeImportCandidateSpecs();
    for (const FRaftSimLandscapeImportCandidateSpec& Candidate : Candidates)
    {
        if (Candidate.PreviewSpec.RiverId == TEXT("futaleufu_terminator"))
        {
            FutaleufuCandidate = &Candidate;
            break;
        }
    }
    if (!FutaleufuCandidate)
    {
        OutSummary += TEXT("The Futaleufu physical-corridor candidate is not registered.\n");
        return false;
    }

    const FString CaptureRelativeRoot =
        TEXT("docs/environment-captures/photoreal_river_previews/landscape_candidates");
    const FString CaptureRoot = FPaths::Combine(GetRepoRoot(), CaptureRelativeRoot);
    IFileManager::Get().MakeDirectory(*CaptureRoot, true);
    FString CameraLocalGuidePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("futaleufu_v26_camera_local_area_alpha2_guide_seat_downstream.png"));
    FString CameraLocalRiverEyePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("futaleufu_v26_camera_local_area_alpha2_river_eye_downstream.png"));
    FString WorldStableGuidePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("futaleufu_v26_world_stable_occupancy_alpha2_guide_seat_downstream.png"));
    FString WorldStableRiverEyePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("futaleufu_v26_world_stable_occupancy_alpha2_river_eye_downstream.png"));

    FFutaleufuCanopyCorridorComparisonStats CameraLocalGuideStats;
    FFutaleufuCanopyCorridorComparisonStats CameraLocalRiverEyeStats;
    FFutaleufuCanopyCorridorComparisonStats WorldStableGuideStats;
    FFutaleufuCanopyCorridorComparisonStats WorldStableRiverEyeStats;
    auto MakeWorldSetup = [FutaleufuCandidate](
                              bool bWorldStableReview,
                              FFutaleufuCanopyCorridorComparisonStats& Stats)
    {
        return [FutaleufuCandidate, bWorldStableReview, &Stats](
                   UWorld* World,
                   ACameraActor* Camera,
                   FString& Summary)
        {
            return AddFutaleufuCanopyCorridorComparisonInstances(
                World,
                Camera,
                *FutaleufuCandidate,
                EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleTwoNoShadow,
                Stats,
                Summary,
                !bWorldStableReview,
                !bWorldStableReview,
                bWorldStableReview);
        };
    };

    const bool bCameraLocalGuideCaptured = CapturePreviewImageForSpec(
        FutaleufuCandidate->PreviewSpec,
        CaptureRoot,
        CameraLocalGuidePath,
        TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"),
        TEXT("futaleufu_v26_camera_local_area_alpha2_guide_seat_downstream"),
        TEXT("Futaleufu guide-seat V25 camera-local area-sampled baseline"),
        true,
        OutSummary,
        MakeWorldSetup(false, CameraLocalGuideStats));
    const bool bCameraLocalRiverEyeCaptured = CapturePreviewImageForSpec(
        FutaleufuCandidate->PreviewSpec,
        CaptureRoot,
        CameraLocalRiverEyePath,
        TEXT("RaftSim_RiverEye_DownstreamCaptureCamera"),
        TEXT("futaleufu_v26_camera_local_area_alpha2_river_eye_downstream"),
        TEXT("Futaleufu river-eye V25 camera-local area-sampled baseline"),
        true,
        OutSummary,
        MakeWorldSetup(false, CameraLocalRiverEyeStats));
    const bool bWorldStableGuideCaptured = CapturePreviewImageForSpec(
        FutaleufuCandidate->PreviewSpec,
        CaptureRoot,
        WorldStableGuidePath,
        TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"),
        TEXT("futaleufu_v26_world_stable_occupancy_alpha2_guide_seat_downstream"),
        TEXT("Futaleufu guide-seat world-stable spatial-occupancy canopy"),
        true,
        OutSummary,
        MakeWorldSetup(true, WorldStableGuideStats));
    const bool bWorldStableRiverEyeCaptured = CapturePreviewImageForSpec(
        FutaleufuCandidate->PreviewSpec,
        CaptureRoot,
        WorldStableRiverEyePath,
        TEXT("RaftSim_RiverEye_DownstreamCaptureCamera"),
        TEXT("futaleufu_v26_world_stable_occupancy_alpha2_river_eye_downstream"),
        TEXT("Futaleufu river-eye world-stable spatial-occupancy canopy"),
        true,
        OutSummary,
        MakeWorldSetup(true, WorldStableRiverEyeStats));
    const bool bAllCaptured =
        bCameraLocalGuideCaptured && bCameraLocalRiverEyeCaptured &&
        bWorldStableGuideCaptured && bWorldStableRiverEyeCaptured;
    const bool bWorldStableFingerprintsMatch =
        WorldStableGuideStats.AcceptedTreeCount > 0 &&
        WorldStableGuideStats.PlacementFingerprint ==
            WorldStableRiverEyeStats.PlacementFingerprint;

    auto MakeStatsObject = [](const FFutaleufuCanopyCorridorComparisonStats& Stats)
    {
        TSharedRef<FJsonObject> Object = MakeShared<FJsonObject>();
        Object->SetBoolField(TEXT("dense_local_review"), Stats.bDenseLocalReview);
        Object->SetBoolField(TEXT("area_sampled_review"), Stats.bAreaSampledReview);
        Object->SetBoolField(TEXT("world_stable_review"), Stats.bWorldStableReview);
        Object->SetNumberField(TEXT("candidate_count"), Stats.CandidateCount);
        Object->SetNumberField(TEXT("target_tree_count"), Stats.TargetTreeCount);
        Object->SetNumberField(TEXT("accepted_tree_count"), Stats.AcceptedTreeCount);
        Object->SetNumberField(TEXT("near_full_tree_count"), Stats.NearTreeCount);
        Object->SetNumberField(TEXT("mid_tree_count"), Stats.MidTreeCount);
        Object->SetNumberField(TEXT("runtime_far_tree_count"), Stats.FarTreeCount);
        Object->SetNumberField(
            TEXT("hidden_fallback_pve_actor_count"),
            Stats.HiddenFallbackActorCount);
        Object->SetNumberField(
            TEXT("rejected_vegetation_mask_count"),
            Stats.RejectedVegetationMaskCount);
        Object->SetNumberField(
            TEXT("rejected_river_setback_count"),
            Stats.RejectedRiverSetbackCount);
        Object->SetNumberField(
            TEXT("rejected_stand_density_count"),
            Stats.RejectedStandDensityCount);
        Object->SetNumberField(TEXT("rejected_slope_count"), Stats.RejectedSlopeCount);
        Object->SetNumberField(TEXT("rejected_spacing_count"), Stats.RejectedSpacingCount);
        Object->SetNumberField(TEXT("minimum_spacing_m"), Stats.MinimumSpacingCm * 0.01f);
        Object->SetNumberField(TEXT("river_setback_m"), Stats.RiverSetbackCm * 0.01f);
        Object->SetNumberField(
            TEXT("sampling_half_extent_m"),
            Stats.SamplingHalfExtentCm * 0.01f);
        Object->SetNumberField(
            TEXT("sampling_along_half_extent_m"),
            Stats.SamplingAlongHalfExtentCm * 0.01f);
        Object->SetNumberField(
            TEXT("sampling_cross_half_extent_m"),
            Stats.SamplingCrossHalfExtentCm * 0.01f);
        Object->SetNumberField(
            TEXT("occupancy_field_resolution"),
            Stats.OccupancyFieldResolution);
        Object->SetNumberField(
            TEXT("occupancy_feather_distance_m"),
            Stats.OccupancyFeatherDistanceCm * 0.01f);
        Object->SetNumberField(
            TEXT("minimum_accepted_river_distance_m"),
            Stats.AcceptedTreeCount > 0
                ? Stats.MinimumAcceptedRiverDistanceCm * 0.01f
                : 0.0f);
        Object->SetStringField(
            TEXT("placement_fingerprint_fnv1a64"),
            FString::Printf(
                TEXT("%016llx"),
                static_cast<unsigned long long>(Stats.PlacementFingerprint)));
        return Object;
    };

    TSharedRef<FJsonObject> Report = MakeShared<FJsonObject>();
    Report->SetStringField(
        TEXT("schema"),
        TEXT("raftsim.unreal.futaleufu_world_stable_canopy_comparison.v1"));
    Report->SetStringField(TEXT("river_id"), TEXT("futaleufu_terminator"));
    Report->SetStringField(
        TEXT("status"),
        bAllCaptured && bWorldStableFingerprintsMatch
            ? TEXT("paired_v26_camera_local_world_stable_canopy_captured_identical_world_placement_pending_human_review")
            : TEXT("v26_capture_or_world_stability_gate_failed"));
    Report->SetBoolField(TEXT("production_promoted"), false);
    Report->SetBoolField(TEXT("corridor_substitution_performed"), false);
    Report->SetBoolField(TEXT("source_map_modified"), false);
    Report->SetBoolField(TEXT("landscape_or_collision_modified"), false);
    Report->SetBoolField(TEXT("hydrodynamic_or_gameplay_authority_modified"), false);
    Report->SetBoolField(
        TEXT("world_stable_placement_fingerprints_match"),
        bWorldStableFingerprintsMatch);
    Report->SetStringField(TEXT("source_map"), FutaleufuCandidate->PreviewSpec.MapPackagePath);
    Report->SetStringField(
        TEXT("source_manifest"),
        FutaleufuCandidate->PreviewSpec.SourceManifest);
    Report->SetStringField(
        TEXT("fixed_between_variants"),
        TEXT("6.5 m spacing, 24 m river setback, project-owned eight-form coigue meshes, V12 runtime-far representation, V22 RGB-padded leaf atlas, alpha2 no-shadow material, source masks, terrain, water, rocks, cameras, lighting, physics, and saved map"));
    Report->SetStringField(
        TEXT("changed_in_world_stable_variant"),
        TEXT("a corridor-anchored 6.0 km by 2.2 km curvilinear centerline domain and 24000-tree target replace each camera's 2.2 km square and 9000-tree target; a 512-cell chamfer signed-distance occupancy field with 180 m feather replaces scalar source-mask luma feathering"));
    Report->SetStringField(
        TEXT("authority_boundary"),
        TEXT("transient review-only non-colliding HISM placement; source Landscape, visual terrain, physical river ribbon, collision, custom C++ water, GeoClaw, feature forcing, raft contact, hazards, gameplay, and saved-map authority remain unchanged"));

    TSharedRef<FJsonObject> Stats = MakeShared<FJsonObject>();
    Stats->SetObjectField(
        TEXT("camera_local_guide_seat"),
        MakeStatsObject(CameraLocalGuideStats));
    Stats->SetObjectField(
        TEXT("camera_local_river_eye"),
        MakeStatsObject(CameraLocalRiverEyeStats));
    Stats->SetObjectField(
        TEXT("world_stable_guide_seat"),
        MakeStatsObject(WorldStableGuideStats));
    Stats->SetObjectField(
        TEXT("world_stable_river_eye"),
        MakeStatsObject(WorldStableRiverEyeStats));
    Report->SetObjectField(TEXT("placement_statistics"), Stats);

    TSharedRef<FJsonObject> Captures = MakeShared<FJsonObject>();
    Captures->SetStringField(TEXT("camera_local_guide_seat"), CameraLocalGuidePath);
    Captures->SetStringField(TEXT("camera_local_river_eye"), CameraLocalRiverEyePath);
    Captures->SetStringField(TEXT("world_stable_guide_seat"), WorldStableGuidePath);
    Captures->SetStringField(TEXT("world_stable_river_eye"), WorldStableRiverEyePath);
    Captures->SetBoolField(TEXT("all_captured"), bAllCaptured);
    Report->SetObjectField(TEXT("captures"), Captures);

    TArray<TSharedPtr<FJsonValue>> OpenGates;
    for (const TCHAR* Gate : {
             TEXT("paired_human_visual_review"),
             TEXT("camera_motion_temporal_stability"),
             TEXT("mixed_native_canopy_species_and_vertical_strata"),
             TEXT("terrain_water_boulder_and_atmosphere_review"),
             TEXT("masked_overdraw_streaming_culling_and_multiplatform_performance"),
             TEXT("guide_ecology_geospatial_rights_and_art_approval")})
    {
        OpenGates.Add(MakeShared<FJsonValueString>(Gate));
    }
    Report->SetArrayField(TEXT("open_promotion_gates"), OpenGates);

    FString SerializedReport;
    const TSharedRef<TJsonWriter<TCHAR, TPrettyJsonPrintPolicy<TCHAR>>> Writer =
        TJsonWriterFactory<TCHAR, TPrettyJsonPrintPolicy<TCHAR>>::Create(&SerializedReport);
    const bool bSerialized = FJsonSerializer::Serialize(Report, Writer);
    SerializedReport += TEXT("\n");
    const FString ReportRelativePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("futaleufu_native_canopy_coigue_v26_world_stable_comparison_report.json"));
    const FString ReportPath = FPaths::Combine(GetRepoRoot(), ReportRelativePath);
    const bool bReportSaved =
        bSerialized && FFileHelper::SaveStringToFile(SerializedReport, *ReportPath);
    OutSummary += FString::Printf(
        TEXT("%s Futaleufu V26 world-stable canopy comparison report -> %s\n"),
        bReportSaved ? TEXT("Saved") : TEXT("Failed to save"),
        *ReportPath);
    return bAllCaptured && bWorldStableFingerprintsMatch && bReportSaved;
}

bool FRaftSimEditorModule::CaptureFutaleufuNativeCanopyRenderDiagnostics(
    FString& OutSummary)
{
    const FRaftSimLandscapeImportCandidateSpec* FutaleufuCandidate = nullptr;
    const TArray<FRaftSimLandscapeImportCandidateSpec> Candidates = GetLandscapeImportCandidateSpecs();
    for (const FRaftSimLandscapeImportCandidateSpec& Candidate : Candidates)
    {
        if (Candidate.PreviewSpec.RiverId == TEXT("futaleufu_terminator"))
        {
            FutaleufuCandidate = &Candidate;
            break;
        }
    }
    if (!FutaleufuCandidate)
    {
        OutSummary += TEXT("The Futaleufu physical-corridor candidate is not registered.\n");
        return false;
    }

    const FString CaptureRelativeRoot =
        TEXT("docs/environment-captures/photoreal_river_previews/landscape_candidates");
    const FString CaptureRoot = FPaths::Combine(GetRepoRoot(), CaptureRelativeRoot);
    IFileManager::Get().MakeDirectory(*CaptureRoot, true);
    FString ShadowlessGuidePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("futaleufu_v15_native_leaf_shadows_disabled_guide_seat_downstream.png"));
    FString ShadowlessRiverEyePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("futaleufu_v15_native_leaf_shadows_disabled_river_eye_downstream.png"));
    FString OpaqueGuidePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("futaleufu_v15_opaque_leaf_no_shadows_guide_seat_downstream.png"));
    FString OpaqueRiverEyePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("futaleufu_v15_opaque_leaf_no_shadows_river_eye_downstream.png"));

    FFutaleufuCanopyCorridorComparisonStats ShadowlessGuideStats;
    FFutaleufuCanopyCorridorComparisonStats ShadowlessRiverEyeStats;
    FFutaleufuCanopyCorridorComparisonStats OpaqueGuideStats;
    FFutaleufuCanopyCorridorComparisonStats OpaqueRiverEyeStats;
    auto MakeWorldSetup = [FutaleufuCandidate](
                              EFutaleufuCanopyCorridorRenderMode RenderMode,
                              FFutaleufuCanopyCorridorComparisonStats& Stats)
    {
        return [FutaleufuCandidate, RenderMode, &Stats](
                   UWorld* World,
                   ACameraActor* Camera,
                   FString& Summary)
        {
            return AddFutaleufuCanopyCorridorComparisonInstances(
                World,
                Camera,
                *FutaleufuCandidate,
                RenderMode,
                Stats,
                Summary);
        };
    };

    const bool bShadowlessGuideCaptured = CapturePreviewImageForSpec(
        FutaleufuCandidate->PreviewSpec,
        CaptureRoot,
        ShadowlessGuidePath,
        TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"),
        TEXT("futaleufu_v15_native_leaf_shadows_disabled_guide_seat_downstream"),
        TEXT("Futaleufu guide-seat native leaf material with leaf shadows disabled"),
        true,
        OutSummary,
        MakeWorldSetup(
            EFutaleufuCanopyCorridorRenderMode::NativeLeavesNoShadow,
            ShadowlessGuideStats));
    const bool bShadowlessRiverEyeCaptured = CapturePreviewImageForSpec(
        FutaleufuCandidate->PreviewSpec,
        CaptureRoot,
        ShadowlessRiverEyePath,
        TEXT("RaftSim_RiverEye_DownstreamCaptureCamera"),
        TEXT("futaleufu_v15_native_leaf_shadows_disabled_river_eye_downstream"),
        TEXT("Futaleufu river-eye native leaf material with leaf shadows disabled"),
        true,
        OutSummary,
        MakeWorldSetup(
            EFutaleufuCanopyCorridorRenderMode::NativeLeavesNoShadow,
            ShadowlessRiverEyeStats));
    const bool bOpaqueGuideCaptured = CapturePreviewImageForSpec(
        FutaleufuCandidate->PreviewSpec,
        CaptureRoot,
        OpaqueGuidePath,
        TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"),
        TEXT("futaleufu_v15_opaque_leaf_no_shadows_guide_seat_downstream"),
        TEXT("Futaleufu guide-seat opaque diagnostic leaf cards with shadows disabled"),
        true,
        OutSummary,
        MakeWorldSetup(
            EFutaleufuCanopyCorridorRenderMode::OpaqueLeavesNoShadow,
            OpaqueGuideStats));
    const bool bOpaqueRiverEyeCaptured = CapturePreviewImageForSpec(
        FutaleufuCandidate->PreviewSpec,
        CaptureRoot,
        OpaqueRiverEyePath,
        TEXT("RaftSim_RiverEye_DownstreamCaptureCamera"),
        TEXT("futaleufu_v15_opaque_leaf_no_shadows_river_eye_downstream"),
        TEXT("Futaleufu river-eye opaque diagnostic leaf cards with shadows disabled"),
        true,
        OutSummary,
        MakeWorldSetup(
            EFutaleufuCanopyCorridorRenderMode::OpaqueLeavesNoShadow,
            OpaqueRiverEyeStats));
    const bool bAllCaptured =
        bShadowlessGuideCaptured && bShadowlessRiverEyeCaptured &&
        bOpaqueGuideCaptured && bOpaqueRiverEyeCaptured;

    auto MakeStatsObject = [](const FFutaleufuCanopyCorridorComparisonStats& Stats)
    {
        TSharedRef<FJsonObject> Object = MakeShared<FJsonObject>();
        Object->SetNumberField(TEXT("candidate_count"), Stats.CandidateCount);
        Object->SetNumberField(TEXT("accepted_tree_count"), Stats.AcceptedTreeCount);
        Object->SetNumberField(TEXT("near_full_tree_count"), Stats.NearTreeCount);
        Object->SetNumberField(TEXT("mid_tree_count"), Stats.MidTreeCount);
        Object->SetNumberField(TEXT("runtime_far_tree_count"), Stats.FarTreeCount);
        Object->SetNumberField(TEXT("hidden_fallback_pve_actor_count"), Stats.HiddenFallbackActorCount);
        Object->SetNumberField(TEXT("rejected_natural_gap_count"), Stats.RejectedNaturalGapCount);
        Object->SetNumberField(TEXT("rejected_vegetation_mask_count"), Stats.RejectedVegetationMaskCount);
        Object->SetNumberField(TEXT("rejected_water_mask_count"), Stats.RejectedWaterMaskCount);
        Object->SetNumberField(TEXT("rejected_elevation_count"), Stats.RejectedElevationCount);
        Object->SetNumberField(TEXT("rejected_slope_count"), Stats.RejectedSlopeCount);
        Object->SetNumberField(TEXT("rejected_dry_aspect_count"), Stats.RejectedDryAspectCount);
        Object->SetNumberField(TEXT("rejected_spacing_count"), Stats.RejectedSpacingCount);
        return Object;
    };
    auto PlacementCountsMatch = [](const FFutaleufuCanopyCorridorComparisonStats& A,
                                   const FFutaleufuCanopyCorridorComparisonStats& B)
    {
        return A.CandidateCount == B.CandidateCount &&
            A.AcceptedTreeCount == B.AcceptedTreeCount &&
            A.NearTreeCount == B.NearTreeCount &&
            A.MidTreeCount == B.MidTreeCount &&
            A.FarTreeCount == B.FarTreeCount &&
            A.HiddenFallbackActorCount == B.HiddenFallbackActorCount &&
            A.RejectedNaturalGapCount == B.RejectedNaturalGapCount &&
            A.RejectedVegetationMaskCount == B.RejectedVegetationMaskCount &&
            A.RejectedWaterMaskCount == B.RejectedWaterMaskCount &&
            A.RejectedElevationCount == B.RejectedElevationCount &&
            A.RejectedSlopeCount == B.RejectedSlopeCount &&
            A.RejectedDryAspectCount == B.RejectedDryAspectCount &&
            A.RejectedSpacingCount == B.RejectedSpacingCount;
    };
    const bool bPlacementCountsIdentical =
        PlacementCountsMatch(ShadowlessGuideStats, OpaqueGuideStats) &&
        PlacementCountsMatch(ShadowlessRiverEyeStats, OpaqueRiverEyeStats);

    TSharedRef<FJsonObject> Report = MakeShared<FJsonObject>();
    Report->SetStringField(
        TEXT("schema"),
        TEXT("raftsim.unreal.futaleufu_native_canopy_render_diagnostic.v15"));
    Report->SetStringField(TEXT("river_id"), TEXT("futaleufu_terminator"));
    Report->SetStringField(
        TEXT("status"),
        bAllCaptured && bPlacementCountsIdentical
            ? TEXT("controlled_leaf_shadow_and_opaque_card_diagnostics_captured_pending_human_review")
            : TEXT("one_or_more_render_diagnostics_failed_or_changed_placement"));
    Report->SetBoolField(TEXT("production_promoted"), false);
    Report->SetBoolField(TEXT("source_map_modified"), false);
    Report->SetBoolField(TEXT("collision_or_gameplay_authority_modified"), false);
    Report->SetBoolField(TEXT("placement_counts_identical_between_render_modes"), bPlacementCountsIdentical);
    Report->SetStringField(TEXT("source_map"), FutaleufuCandidate->PreviewSpec.MapPackagePath);
    Report->SetStringField(
        TEXT("native_reference_guide_seat"),
        FPaths::Combine(
            CaptureRelativeRoot,
            TEXT("futaleufu_v14_instanced_material_review_guide_seat_downstream.png")));
    Report->SetStringField(
        TEXT("native_reference_river_eye"),
        FPaths::Combine(
            CaptureRelativeRoot,
            TEXT("futaleufu_v14_instanced_material_review_river_eye_downstream.png")));
    Report->SetStringField(
        TEXT("control_boundary"),
        TEXT("Camera, exposure, source masks, tree transforms, near/mid/far meshes, terrain, water, rocks, collision, custom C++ solver, and GeoClaw reference remain fixed; only leaf shadow casting and the leaf material override vary."));

    TSharedRef<FJsonObject> RenderModes = MakeShared<FJsonObject>();
    TSharedRef<FJsonObject> ShadowlessMode = MakeShared<FJsonObject>();
    ShadowlessMode->SetStringField(TEXT("leaf_material"), TEXT("native masked TwoSidedFoliage"));
    ShadowlessMode->SetBoolField(TEXT("leaf_cast_shadow"), false);
    ShadowlessMode->SetBoolField(TEXT("trunk_and_branchlet_cast_shadow"), true);
    RenderModes->SetObjectField(TEXT("native_leaves_no_shadow"), ShadowlessMode);
    TSharedRef<FJsonObject> OpaqueMode = MakeShared<FJsonObject>();
    OpaqueMode->SetStringField(TEXT("leaf_material"), TEXT("opaque two-sided DefaultLit diagnostic green"));
    OpaqueMode->SetArrayField(
        TEXT("linear_color_rgba"),
        {
            MakeShared<FJsonValueNumber>(0.045),
            MakeShared<FJsonValueNumber>(0.31),
            MakeShared<FJsonValueNumber>(0.065),
            MakeShared<FJsonValueNumber>(1.0),
        });
    OpaqueMode->SetBoolField(TEXT("leaf_cast_shadow"), false);
    OpaqueMode->SetBoolField(TEXT("trunk_and_branchlet_cast_shadow"), true);
    RenderModes->SetObjectField(TEXT("opaque_leaves_no_shadow"), OpaqueMode);
    Report->SetObjectField(TEXT("render_modes"), RenderModes);

    TSharedRef<FJsonObject> Captures = MakeShared<FJsonObject>();
    Captures->SetStringField(TEXT("native_leaves_no_shadow_guide_seat"), ShadowlessGuidePath);
    Captures->SetStringField(TEXT("native_leaves_no_shadow_river_eye"), ShadowlessRiverEyePath);
    Captures->SetStringField(TEXT("opaque_leaves_no_shadow_guide_seat"), OpaqueGuidePath);
    Captures->SetStringField(TEXT("opaque_leaves_no_shadow_river_eye"), OpaqueRiverEyePath);
    Captures->SetBoolField(TEXT("all_captured"), bAllCaptured);
    Report->SetObjectField(TEXT("captures"), Captures);
    TSharedRef<FJsonObject> Stats = MakeShared<FJsonObject>();
    Stats->SetObjectField(TEXT("native_leaves_no_shadow_guide_seat"), MakeStatsObject(ShadowlessGuideStats));
    Stats->SetObjectField(TEXT("native_leaves_no_shadow_river_eye"), MakeStatsObject(ShadowlessRiverEyeStats));
    Stats->SetObjectField(TEXT("opaque_leaves_no_shadow_guide_seat"), MakeStatsObject(OpaqueGuideStats));
    Stats->SetObjectField(TEXT("opaque_leaves_no_shadow_river_eye"), MakeStatsObject(OpaqueRiverEyeStats));
    Report->SetObjectField(TEXT("placement_stats"), Stats);

    TArray<TSharedPtr<FJsonValue>> Questions;
    Questions.Add(MakeShared<FJsonValueString>(
        TEXT("Do the elongated black ground marks disappear when native leaf shadows are disabled?")));
    Questions.Add(MakeShared<FJsonValueString>(
        TEXT("Do opaque cards reveal retained crown geometry at near, mid, and runtime-far distances?")));
    Questions.Add(MakeShared<FJsonValueString>(
        TEXT("Does the remaining failure localize to opacity/mips, foliage lighting/transmission, shadows, or insufficient distance-crown geometry?")));
    Report->SetArrayField(TEXT("human_review_questions"), Questions);

    FString SerializedReport;
    const TSharedRef<TJsonWriter<TCHAR, TPrettyJsonPrintPolicy<TCHAR>>> Writer =
        TJsonWriterFactory<TCHAR, TPrettyJsonPrintPolicy<TCHAR>>::Create(&SerializedReport);
    const bool bSerialized = FJsonSerializer::Serialize(Report, Writer);
    SerializedReport += TEXT("\n");
    const FString ReportRelativePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("futaleufu_native_canopy_coigue_v15_leaf_shadow_opacity_diagnostic_report.json"));
    const FString ReportPath = FPaths::Combine(GetRepoRoot(), ReportRelativePath);
    const bool bReportSaved =
        bSerialized && FFileHelper::SaveStringToFile(SerializedReport, *ReportPath);
    OutSummary += FString::Printf(
        TEXT("%s Futaleufu native-canopy V15 render diagnostic report -> %s\n"),
        bReportSaved ? TEXT("Saved") : TEXT("Failed to save"),
        *ReportPath);
    return bAllCaptured && bPlacementCountsIdentical && bReportSaved;
}

bool FRaftSimEditorModule::CaptureFutaleufuNativeCanopyOpacityDiagnostics(
    FString& OutSummary)
{
    const FRaftSimLandscapeImportCandidateSpec* FutaleufuCandidate = nullptr;
    const TArray<FRaftSimLandscapeImportCandidateSpec> Candidates = GetLandscapeImportCandidateSpecs();
    for (const FRaftSimLandscapeImportCandidateSpec& Candidate : Candidates)
    {
        if (Candidate.PreviewSpec.RiverId == TEXT("futaleufu_terminator"))
        {
            FutaleufuCandidate = &Candidate;
            break;
        }
    }
    if (!FutaleufuCandidate)
    {
        OutSummary += TEXT("The Futaleufu physical-corridor candidate is not registered.\n");
        return false;
    }

    TMap<FString, UTexture2D*> NativeTextures;
    for (const FRaftSimFirstPartyMaterialTextureAssetSpec& Spec :
         GetFutaleufuNativeCanopyTextureAssetSpecs())
    {
        const FString ObjectPath = FString::Printf(
            TEXT("%s.%s"),
            *Spec.GetTextureAssetPath(),
            *Spec.GetTextureAssetName());
        UTexture2D* Texture = LoadObject<UTexture2D>(nullptr, *ObjectPath);
        if (!Texture)
        {
            OutSummary += FString::Printf(
                TEXT("Futaleufu V16 opacity diagnostic could not load texture %s.\n"),
                *ObjectPath);
            return false;
        }
        NativeTextures.Add(Spec.MapKey, Texture);
    }
    UMaterial* LeafMaterial = CreateOrUpdateFutaleufuNativeCanopyMaterial(
        TEXT("M_RaftSim_FutaleufuCoigue_Leaves"),
        true,
        NativeTextures,
        OutSummary);
    UTexture2D* LeafAlbedo = NativeTextures.FindRef(TEXT("LeafAlbedoOpacity"));
    if (!LeafMaterial || !LeafAlbedo)
    {
        OutSummary += TEXT("Futaleufu V16 opacity diagnostic could not rebuild the parameterized native leaf material.\n");
        return false;
    }

    const FString CaptureRelativeRoot =
        TEXT("docs/environment-captures/photoreal_river_previews/landscape_candidates");
    const FString CaptureRoot = FPaths::Combine(GetRepoRoot(), CaptureRelativeRoot);
    IFileManager::Get().MakeDirectory(*CaptureRoot, true);
    FString AlphaScaleGuidePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("futaleufu_v16_native_alpha_scale_4_no_shadows_guide_seat_downstream.png"));
    FString AlphaScaleRiverEyePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("futaleufu_v16_native_alpha_scale_4_no_shadows_river_eye_downstream.png"));
    FString ConstantOpacityGuidePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("futaleufu_v16_native_constant_opacity_no_shadows_guide_seat_downstream.png"));
    FString ConstantOpacityRiverEyePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("futaleufu_v16_native_constant_opacity_no_shadows_river_eye_downstream.png"));

    FFutaleufuCanopyCorridorComparisonStats AlphaScaleGuideStats;
    FFutaleufuCanopyCorridorComparisonStats AlphaScaleRiverEyeStats;
    FFutaleufuCanopyCorridorComparisonStats ConstantOpacityGuideStats;
    FFutaleufuCanopyCorridorComparisonStats ConstantOpacityRiverEyeStats;
    auto MakeWorldSetup = [FutaleufuCandidate](
                              EFutaleufuCanopyCorridorRenderMode RenderMode,
                              FFutaleufuCanopyCorridorComparisonStats& Stats)
    {
        return [FutaleufuCandidate, RenderMode, &Stats](
                   UWorld* World,
                   ACameraActor* Camera,
                   FString& Summary)
        {
            return AddFutaleufuCanopyCorridorComparisonInstances(
                World,
                Camera,
                *FutaleufuCandidate,
                RenderMode,
                Stats,
                Summary);
        };
    };

    const bool bAlphaScaleGuideCaptured = CapturePreviewImageForSpec(
        FutaleufuCandidate->PreviewSpec,
        CaptureRoot,
        AlphaScaleGuidePath,
        TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"),
        TEXT("futaleufu_v16_native_alpha_scale_4_no_shadows_guide_seat_downstream"),
        TEXT("Futaleufu guide-seat native TwoSidedFoliage with 4x opacity scale and leaf shadows disabled"),
        true,
        OutSummary,
        MakeWorldSetup(
            EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleFourNoShadow,
            AlphaScaleGuideStats));
    const bool bAlphaScaleRiverEyeCaptured = CapturePreviewImageForSpec(
        FutaleufuCandidate->PreviewSpec,
        CaptureRoot,
        AlphaScaleRiverEyePath,
        TEXT("RaftSim_RiverEye_DownstreamCaptureCamera"),
        TEXT("futaleufu_v16_native_alpha_scale_4_no_shadows_river_eye_downstream"),
        TEXT("Futaleufu river-eye native TwoSidedFoliage with 4x opacity scale and leaf shadows disabled"),
        true,
        OutSummary,
        MakeWorldSetup(
            EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleFourNoShadow,
            AlphaScaleRiverEyeStats));
    const bool bConstantOpacityGuideCaptured = CapturePreviewImageForSpec(
        FutaleufuCandidate->PreviewSpec,
        CaptureRoot,
        ConstantOpacityGuidePath,
        TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"),
        TEXT("futaleufu_v16_native_constant_opacity_no_shadows_guide_seat_downstream"),
        TEXT("Futaleufu guide-seat native TwoSidedFoliage with constant opacity and leaf shadows disabled"),
        true,
        OutSummary,
        MakeWorldSetup(
            EFutaleufuCanopyCorridorRenderMode::NativeConstantOpacityNoShadow,
            ConstantOpacityGuideStats));
    const bool bConstantOpacityRiverEyeCaptured = CapturePreviewImageForSpec(
        FutaleufuCandidate->PreviewSpec,
        CaptureRoot,
        ConstantOpacityRiverEyePath,
        TEXT("RaftSim_RiverEye_DownstreamCaptureCamera"),
        TEXT("futaleufu_v16_native_constant_opacity_no_shadows_river_eye_downstream"),
        TEXT("Futaleufu river-eye native TwoSidedFoliage with constant opacity and leaf shadows disabled"),
        true,
        OutSummary,
        MakeWorldSetup(
            EFutaleufuCanopyCorridorRenderMode::NativeConstantOpacityNoShadow,
            ConstantOpacityRiverEyeStats));
    const bool bAllCaptured =
        bAlphaScaleGuideCaptured && bAlphaScaleRiverEyeCaptured &&
        bConstantOpacityGuideCaptured && bConstantOpacityRiverEyeCaptured;

    auto MakeStatsObject = [](const FFutaleufuCanopyCorridorComparisonStats& Stats)
    {
        TSharedRef<FJsonObject> Object = MakeShared<FJsonObject>();
        Object->SetNumberField(TEXT("candidate_count"), Stats.CandidateCount);
        Object->SetNumberField(TEXT("accepted_tree_count"), Stats.AcceptedTreeCount);
        Object->SetNumberField(TEXT("near_full_tree_count"), Stats.NearTreeCount);
        Object->SetNumberField(TEXT("mid_tree_count"), Stats.MidTreeCount);
        Object->SetNumberField(TEXT("runtime_far_tree_count"), Stats.FarTreeCount);
        Object->SetNumberField(TEXT("hidden_fallback_pve_actor_count"), Stats.HiddenFallbackActorCount);
        return Object;
    };
    auto PlacementCountsMatch = [](const FFutaleufuCanopyCorridorComparisonStats& A,
                                   const FFutaleufuCanopyCorridorComparisonStats& B)
    {
        return A.CandidateCount == B.CandidateCount &&
            A.AcceptedTreeCount == B.AcceptedTreeCount &&
            A.NearTreeCount == B.NearTreeCount &&
            A.MidTreeCount == B.MidTreeCount &&
            A.FarTreeCount == B.FarTreeCount &&
            A.HiddenFallbackActorCount == B.HiddenFallbackActorCount;
    };
    const bool bPlacementCountsIdentical =
        PlacementCountsMatch(AlphaScaleGuideStats, ConstantOpacityGuideStats) &&
        PlacementCountsMatch(AlphaScaleRiverEyeStats, ConstantOpacityRiverEyeStats);

    TSharedRef<FJsonObject> Report = MakeShared<FJsonObject>();
    Report->SetStringField(
        TEXT("schema"),
        TEXT("raftsim.unreal.futaleufu_native_canopy_same_shader_opacity_diagnostic.v16"));
    Report->SetStringField(TEXT("river_id"), TEXT("futaleufu_terminator"));
    Report->SetStringField(
        TEXT("status"),
        bAllCaptured && bPlacementCountsIdentical
            ? TEXT("same_shader_alpha_scale_and_constant_opacity_diagnostics_captured_pending_human_review")
            : TEXT("one_or_more_same_shader_opacity_diagnostics_failed_or_changed_placement"));
    Report->SetBoolField(TEXT("production_promoted"), false);
    Report->SetBoolField(TEXT("source_map_modified"), false);
    Report->SetBoolField(TEXT("collision_or_gameplay_authority_modified"), false);
    Report->SetBoolField(TEXT("placement_counts_identical_between_render_modes"), bPlacementCountsIdentical);
    Report->SetStringField(TEXT("source_map"), FutaleufuCandidate->PreviewSpec.MapPackagePath);
    Report->SetStringField(
        TEXT("shadowless_native_reference_guide_seat"),
        FPaths::Combine(
            CaptureRelativeRoot,
            TEXT("futaleufu_v15_native_leaf_shadows_disabled_guide_seat_downstream.png")));
    Report->SetStringField(
        TEXT("shadowless_native_reference_river_eye"),
        FPaths::Combine(
            CaptureRelativeRoot,
            TEXT("futaleufu_v15_native_leaf_shadows_disabled_river_eye_downstream.png")));
    Report->SetStringField(
        TEXT("control_boundary"),
        TEXT("The native masked TwoSidedFoliage shader, textures, cutoff, source masks, tree transforms, near/mid/far meshes, cameras, exposure, terrain, water, rocks, and physics authority remain fixed; only LeafOpacityScale or LeafOpacityOverride varies, and leaf shadows remain disabled."));

    TSharedRef<FJsonObject> TextureContract = MakeShared<FJsonObject>();
    TextureContract->SetBoolField(TEXT("has_alpha_channel"), LeafAlbedo->HasAlphaChannel());
    TextureContract->SetBoolField(TEXT("compression_no_alpha"), LeafAlbedo->CompressionNoAlpha);
    TextureContract->SetBoolField(
        TEXT("scale_mips_for_alpha_coverage"),
        LeafAlbedo->bDoScaleMipsForAlphaCoverage);
    TextureContract->SetArrayField(
        TEXT("alpha_coverage_thresholds_rgba"),
        {
            MakeShared<FJsonValueNumber>(LeafAlbedo->AlphaCoverageThresholds.X),
            MakeShared<FJsonValueNumber>(LeafAlbedo->AlphaCoverageThresholds.Y),
            MakeShared<FJsonValueNumber>(LeafAlbedo->AlphaCoverageThresholds.Z),
            MakeShared<FJsonValueNumber>(LeafAlbedo->AlphaCoverageThresholds.W),
        });
    TextureContract->SetBoolField(TEXT("sharpen5_mips"), LeafAlbedo->MipGenSettings == TMGS_Sharpen5);
    TextureContract->SetBoolField(TEXT("never_stream"), LeafAlbedo->NeverStream);
    TextureContract->SetBoolField(TEXT("virtual_texture_streaming"), LeafAlbedo->VirtualTextureStreaming);
    Report->SetObjectField(TEXT("leaf_texture_contract"), TextureContract);

    TSharedRef<FJsonObject> MaterialContract = MakeShared<FJsonObject>();
    MaterialContract->SetStringField(TEXT("blend_mode"), TEXT("masked"));
    MaterialContract->SetStringField(TEXT("shading_model"), TEXT("TwoSidedFoliage"));
    MaterialContract->SetNumberField(TEXT("opacity_mask_clip_value"), LeafMaterial->OpacityMaskClipValue);
    MaterialContract->SetBoolField(TEXT("two_sided"), LeafMaterial->TwoSided);
    MaterialContract->SetBoolField(TEXT("dithered_lod_transition"), LeafMaterial->DitheredLODTransition);
    MaterialContract->SetNumberField(TEXT("default_leaf_opacity_scale"), 1.0);
    MaterialContract->SetNumberField(TEXT("default_leaf_opacity_override"), 0.0);
    Report->SetObjectField(TEXT("leaf_material_contract"), MaterialContract);

    TSharedRef<FJsonObject> RenderModes = MakeShared<FJsonObject>();
    TSharedRef<FJsonObject> AlphaScaleMode = MakeShared<FJsonObject>();
    AlphaScaleMode->SetNumberField(TEXT("LeafOpacityScale"), 4.0);
    AlphaScaleMode->SetNumberField(TEXT("LeafOpacityOverride"), 0.0);
    AlphaScaleMode->SetBoolField(TEXT("leaf_cast_shadow"), false);
    RenderModes->SetObjectField(TEXT("native_alpha_scale_4_no_shadow"), AlphaScaleMode);
    TSharedRef<FJsonObject> ConstantOpacityMode = MakeShared<FJsonObject>();
    ConstantOpacityMode->SetNumberField(TEXT("LeafOpacityScale"), 1.0);
    ConstantOpacityMode->SetNumberField(TEXT("LeafOpacityOverride"), 1.0);
    ConstantOpacityMode->SetBoolField(TEXT("leaf_cast_shadow"), false);
    RenderModes->SetObjectField(TEXT("native_constant_opacity_no_shadow"), ConstantOpacityMode);
    Report->SetObjectField(TEXT("render_modes"), RenderModes);

    TSharedRef<FJsonObject> Captures = MakeShared<FJsonObject>();
    Captures->SetStringField(TEXT("native_alpha_scale_4_no_shadow_guide_seat"), AlphaScaleGuidePath);
    Captures->SetStringField(TEXT("native_alpha_scale_4_no_shadow_river_eye"), AlphaScaleRiverEyePath);
    Captures->SetStringField(TEXT("native_constant_opacity_no_shadow_guide_seat"), ConstantOpacityGuidePath);
    Captures->SetStringField(TEXT("native_constant_opacity_no_shadow_river_eye"), ConstantOpacityRiverEyePath);
    Captures->SetBoolField(TEXT("all_captured"), bAllCaptured);
    Report->SetObjectField(TEXT("captures"), Captures);
    TSharedRef<FJsonObject> Stats = MakeShared<FJsonObject>();
    Stats->SetObjectField(TEXT("native_alpha_scale_4_no_shadow_guide_seat"), MakeStatsObject(AlphaScaleGuideStats));
    Stats->SetObjectField(TEXT("native_alpha_scale_4_no_shadow_river_eye"), MakeStatsObject(AlphaScaleRiverEyeStats));
    Stats->SetObjectField(TEXT("native_constant_opacity_no_shadow_guide_seat"), MakeStatsObject(ConstantOpacityGuideStats));
    Stats->SetObjectField(TEXT("native_constant_opacity_no_shadow_river_eye"), MakeStatsObject(ConstantOpacityRiverEyeStats));
    Report->SetObjectField(TEXT("placement_stats"), Stats);

    FString SerializedReport;
    const TSharedRef<TJsonWriter<TCHAR, TPrettyJsonPrintPolicy<TCHAR>>> Writer =
        TJsonWriterFactory<TCHAR, TPrettyJsonPrintPolicy<TCHAR>>::Create(&SerializedReport);
    const bool bSerialized = FJsonSerializer::Serialize(Report, Writer);
    SerializedReport += TEXT("\n");
    const FString ReportRelativePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("futaleufu_native_canopy_coigue_v16_same_shader_opacity_diagnostic_report.json"));
    const FString ReportPath = FPaths::Combine(GetRepoRoot(), ReportRelativePath);
    const bool bReportSaved =
        bSerialized && FFileHelper::SaveStringToFile(SerializedReport, *ReportPath);
    OutSummary += FString::Printf(
        TEXT("%s Futaleufu native-canopy V16 same-shader opacity report -> %s\n"),
        bReportSaved ? TEXT("Saved") : TEXT("Failed to save"),
        *ReportPath);
    return bAllCaptured && bPlacementCountsIdentical && bReportSaved;
}
