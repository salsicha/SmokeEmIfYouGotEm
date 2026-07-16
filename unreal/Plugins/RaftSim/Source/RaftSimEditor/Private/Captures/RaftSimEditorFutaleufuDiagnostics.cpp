#include "Environment/RaftSimEditorEnvironmentInternal.h"

using namespace RaftSimEditorEnvironment;

bool FRaftSimEditorModule::CaptureFutaleufuNativeCanopyLightingDiagnostics(
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
                TEXT("Futaleufu V17 lighting diagnostic could not load texture %s.\n"),
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
    if (!LeafMaterial)
    {
        OutSummary += TEXT("Futaleufu V17 lighting diagnostic could not rebuild the parameterized native leaf material.\n");
        return false;
    }

    const FString CaptureRelativeRoot =
        TEXT("docs/environment-captures/photoreal_river_previews/landscape_candidates");
    const FString CaptureRoot = FPaths::Combine(GetRepoRoot(), CaptureRelativeRoot);
    IFileManager::Get().MakeDirectory(*CaptureRoot, true);

    struct FFutaleufuLightingDiagnostic
    {
        EFutaleufuCanopyCorridorRenderMode RenderMode =
            EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleFourAoOffNoShadow;
        FString Token;
        FString Description;
        FString GuidePath;
        FString RiverEyePath;
        FFutaleufuCanopyCorridorComparisonStats GuideStats;
        FFutaleufuCanopyCorridorComparisonStats RiverEyeStats;
        bool bGuideCaptured = false;
        bool bRiverEyeCaptured = false;
    };
    TArray<FFutaleufuLightingDiagnostic> Diagnostics;
    auto AddDiagnostic = [&Diagnostics, &CaptureRelativeRoot](
                             EFutaleufuCanopyCorridorRenderMode RenderMode,
                             const TCHAR* Token,
                             const TCHAR* Description)
    {
        FFutaleufuLightingDiagnostic& Diagnostic = Diagnostics.AddDefaulted_GetRef();
        Diagnostic.RenderMode = RenderMode;
        Diagnostic.Token = Token;
        Diagnostic.Description = Description;
        Diagnostic.GuidePath = FPaths::Combine(
            CaptureRelativeRoot,
            FString::Printf(TEXT("futaleufu_v17_%s_guide_seat_downstream.png"), Token));
        Diagnostic.RiverEyePath = FPaths::Combine(
            CaptureRelativeRoot,
            FString::Printf(TEXT("futaleufu_v17_%s_river_eye_downstream.png"), Token));
    };
    AddDiagnostic(
        EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleFourAoOffNoShadow,
        TEXT("alpha4_ao_off_no_shadows"),
        TEXT("native TwoSidedFoliage with 4x alpha, AO influence zero, and leaf shadows disabled"));
    AddDiagnostic(
        EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleFourFlatNormalNoShadow,
        TEXT("alpha4_flat_normal_no_shadows"),
        TEXT("native TwoSidedFoliage with 4x alpha, flat two-sided normals, and leaf shadows disabled"));
    AddDiagnostic(
        EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleFourEmissiveNoShadow,
        TEXT("alpha4_emissive_035_no_shadows"),
        TEXT("native TwoSidedFoliage with 4x alpha, diagnostic emissive 0.35, and leaf shadows disabled"));

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
    bool bAllCaptured = true;
    for (FFutaleufuLightingDiagnostic& Diagnostic : Diagnostics)
    {
        Diagnostic.bGuideCaptured = CapturePreviewImageForSpec(
            FutaleufuCandidate->PreviewSpec,
            CaptureRoot,
            Diagnostic.GuidePath,
            TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"),
            FString::Printf(TEXT("futaleufu_v17_%s_guide_seat_downstream"), *Diagnostic.Token),
            FString::Printf(TEXT("Futaleufu guide-seat %s"), *Diagnostic.Description),
            true,
            OutSummary,
            MakeWorldSetup(Diagnostic.RenderMode, Diagnostic.GuideStats));
        Diagnostic.bRiverEyeCaptured = CapturePreviewImageForSpec(
            FutaleufuCandidate->PreviewSpec,
            CaptureRoot,
            Diagnostic.RiverEyePath,
            TEXT("RaftSim_RiverEye_DownstreamCaptureCamera"),
            FString::Printf(TEXT("futaleufu_v17_%s_river_eye_downstream"), *Diagnostic.Token),
            FString::Printf(TEXT("Futaleufu river-eye %s"), *Diagnostic.Description),
            true,
            OutSummary,
            MakeWorldSetup(Diagnostic.RenderMode, Diagnostic.RiverEyeStats));
        bAllCaptured &= Diagnostic.bGuideCaptured && Diagnostic.bRiverEyeCaptured;
    }

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
    bool bPlacementCountsIdentical = Diagnostics.Num() == 3;
    for (int32 Index = 1; Index < Diagnostics.Num(); ++Index)
    {
        bPlacementCountsIdentical &=
            PlacementCountsMatch(Diagnostics[0].GuideStats, Diagnostics[Index].GuideStats) &&
            PlacementCountsMatch(Diagnostics[0].RiverEyeStats, Diagnostics[Index].RiverEyeStats);
    }

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

    TSharedRef<FJsonObject> Report = MakeShared<FJsonObject>();
    Report->SetStringField(
        TEXT("schema"),
        TEXT("raftsim.unreal.futaleufu_native_canopy_lighting_diagnostic.v17"));
    Report->SetStringField(TEXT("river_id"), TEXT("futaleufu_terminator"));
    Report->SetStringField(
        TEXT("status"),
        bAllCaptured && bPlacementCountsIdentical
            ? TEXT("controlled_ao_normal_and_diagnostic_emissive_splits_captured_pending_human_review")
            : TEXT("one_or_more_lighting_diagnostics_failed_or_changed_placement"));
    Report->SetBoolField(TEXT("production_promoted"), false);
    Report->SetBoolField(TEXT("source_map_modified"), false);
    Report->SetBoolField(TEXT("collision_or_gameplay_authority_modified"), false);
    Report->SetBoolField(TEXT("placement_counts_identical_between_render_modes"), bPlacementCountsIdentical);
    Report->SetStringField(TEXT("source_map"), FutaleufuCandidate->PreviewSpec.MapPackagePath);
    Report->SetStringField(
        TEXT("alpha4_reference_guide_seat"),
        FPaths::Combine(
            CaptureRelativeRoot,
            TEXT("futaleufu_v16_native_alpha_scale_4_no_shadows_guide_seat_downstream.png")));
    Report->SetStringField(
        TEXT("alpha4_reference_river_eye"),
        FPaths::Combine(
            CaptureRelativeRoot,
            TEXT("futaleufu_v16_native_alpha_scale_4_no_shadows_river_eye_downstream.png")));
    Report->SetStringField(
        TEXT("control_boundary"),
        TEXT("The 4x restored-alpha silhouette, native masked TwoSidedFoliage graph, textures, source masks, transforms, meshes, cameras, exposure, terrain, water, rocks, and physics authority remain fixed. AO influence, normal strength, or diagnostic emissive changes independently; leaf shadows remain disabled."));

    TSharedRef<FJsonObject> MaterialDefaults = MakeShared<FJsonObject>();
    MaterialDefaults->SetNumberField(TEXT("LeafOpacityScale"), 1.0);
    MaterialDefaults->SetNumberField(TEXT("LeafOpacityOverride"), 0.0);
    MaterialDefaults->SetNumberField(TEXT("LeafAOInfluence"), 0.55);
    MaterialDefaults->SetNumberField(TEXT("LeafNormalStrength"), 1.0);
    MaterialDefaults->SetNumberField(TEXT("LeafDiagnosticEmissive"), 0.0);
    Report->SetObjectField(TEXT("retained_neutral_material_defaults"), MaterialDefaults);

    TSharedRef<FJsonObject> Captures = MakeShared<FJsonObject>();
    TSharedRef<FJsonObject> Stats = MakeShared<FJsonObject>();
    TSharedRef<FJsonObject> Modes = MakeShared<FJsonObject>();
    for (const FFutaleufuLightingDiagnostic& Diagnostic : Diagnostics)
    {
        Captures->SetStringField(Diagnostic.Token + TEXT("_guide_seat"), Diagnostic.GuidePath);
        Captures->SetStringField(Diagnostic.Token + TEXT("_river_eye"), Diagnostic.RiverEyePath);
        Stats->SetObjectField(Diagnostic.Token + TEXT("_guide_seat"), MakeStatsObject(Diagnostic.GuideStats));
        Stats->SetObjectField(Diagnostic.Token + TEXT("_river_eye"), MakeStatsObject(Diagnostic.RiverEyeStats));
        TSharedRef<FJsonObject> Mode = MakeShared<FJsonObject>();
        Mode->SetNumberField(TEXT("LeafOpacityScale"), 4.0);
        Mode->SetBoolField(TEXT("leaf_cast_shadow"), false);
        Mode->SetNumberField(
            TEXT("LeafAOInfluence"),
            Diagnostic.RenderMode == EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleFourAoOffNoShadow
                ? 0.0
                : 0.55);
        Mode->SetNumberField(
            TEXT("LeafNormalStrength"),
            Diagnostic.RenderMode == EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleFourFlatNormalNoShadow
                ? 0.0
                : 1.0);
        Mode->SetNumberField(
            TEXT("LeafDiagnosticEmissive"),
            Diagnostic.RenderMode == EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleFourEmissiveNoShadow
                ? 0.35
                : 0.0);
        Mode->SetBoolField(
            TEXT("promotion_eligible"),
            Diagnostic.RenderMode != EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleFourEmissiveNoShadow);
        Modes->SetObjectField(Diagnostic.Token, Mode);
    }
    Captures->SetBoolField(TEXT("all_captured"), bAllCaptured);
    Report->SetObjectField(TEXT("captures"), Captures);
    Report->SetObjectField(TEXT("placement_stats"), Stats);
    Report->SetObjectField(TEXT("render_modes"), Modes);

    FString SerializedReport;
    const TSharedRef<TJsonWriter<TCHAR, TPrettyJsonPrintPolicy<TCHAR>>> Writer =
        TJsonWriterFactory<TCHAR, TPrettyJsonPrintPolicy<TCHAR>>::Create(&SerializedReport);
    const bool bSerialized = FJsonSerializer::Serialize(Report, Writer);
    SerializedReport += TEXT("\n");
    const FString ReportRelativePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("futaleufu_native_canopy_coigue_v17_lighting_diagnostic_report.json"));
    const FString ReportPath = FPaths::Combine(GetRepoRoot(), ReportRelativePath);
    const bool bReportSaved =
        bSerialized && FFileHelper::SaveStringToFile(SerializedReport, *ReportPath);
    OutSummary += FString::Printf(
        TEXT("%s Futaleufu native-canopy V17 lighting diagnostic report -> %s\n"),
        bReportSaved ? TEXT("Saved") : TEXT("Failed to save"),
        *ReportPath);
    return bAllCaptured && bPlacementCountsIdentical && bReportSaved;
}

bool FRaftSimEditorModule::CaptureFutaleufuNativeCanopyCorridorLightRigDiagnostics(
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
                TEXT("Futaleufu V18 light-rig diagnostic could not load texture %s.\n"),
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
    if (!LeafMaterial)
    {
        OutSummary += TEXT("Futaleufu V18 light-rig diagnostic could not rebuild the neutral native leaf material.\n");
        return false;
    }

    const FString CaptureRelativeRoot =
        TEXT("docs/environment-captures/photoreal_river_previews/landscape_candidates");
    const FString CaptureRoot = FPaths::Combine(GetRepoRoot(), CaptureRelativeRoot);
    IFileManager::Get().MakeDirectory(*CaptureRoot, true);

    struct FFutaleufuLightRigDiagnostic
    {
        EFutaleufuCanopyCorridorLightingTreatment Treatment =
            EFutaleufuCanopyCorridorLightingTreatment::Baseline;
        FString Token;
        FString Description;
        FString GuidePath;
        FString RiverEyePath;
        FFutaleufuCanopyCorridorComparisonStats GuideStats;
        FFutaleufuCanopyCorridorComparisonStats RiverEyeStats;
        bool bGuideCaptured = false;
        bool bRiverEyeCaptured = false;
    };
    TArray<FFutaleufuLightRigDiagnostic> Diagnostics;
    auto AddDiagnostic = [&Diagnostics, &CaptureRelativeRoot](
                             EFutaleufuCanopyCorridorLightingTreatment Treatment,
                             const TCHAR* Token,
                             const TCHAR* Description)
    {
        FFutaleufuLightRigDiagnostic& Diagnostic = Diagnostics.AddDefaulted_GetRef();
        Diagnostic.Treatment = Treatment;
        Diagnostic.Token = Token;
        Diagnostic.Description = Description;
        Diagnostic.GuidePath = FPaths::Combine(
            CaptureRelativeRoot,
            FString::Printf(TEXT("futaleufu_v18_%s_guide_seat_downstream.png"), Token));
        Diagnostic.RiverEyePath = FPaths::Combine(
            CaptureRelativeRoot,
            FString::Printf(TEXT("futaleufu_v18_%s_river_eye_downstream.png"), Token));
    };
    AddDiagnostic(
        EFutaleufuCanopyCorridorLightingTreatment::Baseline,
        TEXT("alpha4_baseline_no_shadows"),
        TEXT("saved corridor light rig with neutral material, 4x alpha, and leaf shadows disabled"));
    AddDiagnostic(
        EFutaleufuCanopyCorridorLightingTreatment::IsolatedReviewFill,
        TEXT("alpha4_isolated_fill_no_shadows"),
        TEXT("transient isolated-review 0.75 front fill, 0.38 back fill, and 1.65 skylight"));
    AddDiagnostic(
        EFutaleufuCanopyCorridorLightingTreatment::SkyLightDouble,
        TEXT("alpha4_skylight_310_no_shadows"),
        TEXT("transient recaptured 3.10 skylight with no added fill lights"));

    auto MakeWorldSetup = [FutaleufuCandidate](
                              EFutaleufuCanopyCorridorLightingTreatment Treatment,
                              FFutaleufuCanopyCorridorComparisonStats& Stats)
    {
        return [FutaleufuCandidate, Treatment, &Stats](
                   UWorld* World,
                   ACameraActor* Camera,
                   FString& Summary)
        {
            if (!AddFutaleufuCanopyCorridorComparisonInstances(
                    World,
                    Camera,
                    *FutaleufuCandidate,
                    EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleFourNoShadow,
                    Stats,
                    Summary))
            {
                return false;
            }
            return ApplyFutaleufuCanopyCorridorLightingTreatment(World, Treatment, Summary);
        };
    };

    bool bAllCaptured = true;
    for (FFutaleufuLightRigDiagnostic& Diagnostic : Diagnostics)
    {
        Diagnostic.bGuideCaptured = CapturePreviewImageForSpec(
            FutaleufuCandidate->PreviewSpec,
            CaptureRoot,
            Diagnostic.GuidePath,
            TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"),
            FString::Printf(TEXT("futaleufu_v18_%s_guide_seat_downstream"), *Diagnostic.Token),
            FString::Printf(TEXT("Futaleufu guide-seat %s"), *Diagnostic.Description),
            true,
            OutSummary,
            MakeWorldSetup(Diagnostic.Treatment, Diagnostic.GuideStats));
        Diagnostic.bRiverEyeCaptured = CapturePreviewImageForSpec(
            FutaleufuCandidate->PreviewSpec,
            CaptureRoot,
            Diagnostic.RiverEyePath,
            TEXT("RaftSim_RiverEye_DownstreamCaptureCamera"),
            FString::Printf(TEXT("futaleufu_v18_%s_river_eye_downstream"), *Diagnostic.Token),
            FString::Printf(TEXT("Futaleufu river-eye %s"), *Diagnostic.Description),
            true,
            OutSummary,
            MakeWorldSetup(Diagnostic.Treatment, Diagnostic.RiverEyeStats));
        bAllCaptured &= Diagnostic.bGuideCaptured && Diagnostic.bRiverEyeCaptured;
    }

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
    bool bPlacementCountsIdentical = Diagnostics.Num() == 3;
    for (int32 Index = 1; Index < Diagnostics.Num(); ++Index)
    {
        bPlacementCountsIdentical &=
            PlacementCountsMatch(Diagnostics[0].GuideStats, Diagnostics[Index].GuideStats) &&
            PlacementCountsMatch(Diagnostics[0].RiverEyeStats, Diagnostics[Index].RiverEyeStats);
    }

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

    TSharedRef<FJsonObject> Report = MakeShared<FJsonObject>();
    Report->SetStringField(
        TEXT("schema"),
        TEXT("raftsim.unreal.futaleufu_native_canopy_corridor_light_rig_diagnostic.v18"));
    Report->SetStringField(TEXT("river_id"), TEXT("futaleufu_terminator"));
    Report->SetStringField(
        TEXT("status"),
        bAllCaptured && bPlacementCountsIdentical
            ? TEXT("controlled_baseline_fill_and_skylight_splits_captured_pending_human_review")
            : TEXT("one_or_more_light_rig_diagnostics_failed_or_changed_placement"));
    Report->SetBoolField(TEXT("production_promoted"), false);
    Report->SetBoolField(TEXT("source_map_modified"), false);
    Report->SetBoolField(TEXT("collision_or_gameplay_authority_modified"), false);
    Report->SetBoolField(TEXT("placement_counts_identical_between_render_modes"), bPlacementCountsIdentical);
    Report->SetStringField(TEXT("source_map"), FutaleufuCandidate->PreviewSpec.MapPackagePath);
    Report->SetStringField(
        TEXT("control_boundary"),
        TEXT("The neutral masked TwoSidedFoliage graph, 4x opacity diagnostic, disabled leaf shadows, source masks, transforms, meshes, cameras, exposure, terrain, water, rocks, and physics authority remain fixed. Only transient unsaved direct-fill or skylight intensity changes."));

    TSharedRef<FJsonObject> SavedLighting = MakeShared<FJsonObject>();
    SavedLighting->SetNumberField(TEXT("sun_intensity"), 4.75);
    SavedLighting->SetNumberField(TEXT("skylight_intensity"), 1.55);
    SavedLighting->SetNumberField(TEXT("exposure_compensation"), -0.16);
    SavedLighting->SetNumberField(TEXT("fog_density"), 0.0055);
    Report->SetObjectField(TEXT("saved_corridor_photometry"), SavedLighting);

    TSharedRef<FJsonObject> Captures = MakeShared<FJsonObject>();
    TSharedRef<FJsonObject> Stats = MakeShared<FJsonObject>();
    TSharedRef<FJsonObject> Treatments = MakeShared<FJsonObject>();
    for (const FFutaleufuLightRigDiagnostic& Diagnostic : Diagnostics)
    {
        Captures->SetStringField(Diagnostic.Token + TEXT("_guide_seat"), Diagnostic.GuidePath);
        Captures->SetStringField(Diagnostic.Token + TEXT("_river_eye"), Diagnostic.RiverEyePath);
        Stats->SetObjectField(Diagnostic.Token + TEXT("_guide_seat"), MakeStatsObject(Diagnostic.GuideStats));
        Stats->SetObjectField(Diagnostic.Token + TEXT("_river_eye"), MakeStatsObject(Diagnostic.RiverEyeStats));
        TSharedRef<FJsonObject> Treatment = MakeShared<FJsonObject>();
        Treatment->SetNumberField(TEXT("LeafOpacityScale"), 4.0);
        Treatment->SetBoolField(TEXT("leaf_cast_shadow"), false);
        Treatment->SetNumberField(TEXT("LeafAOInfluence"), 0.55);
        Treatment->SetNumberField(TEXT("LeafNormalStrength"), 1.0);
        Treatment->SetNumberField(TEXT("LeafDiagnosticEmissive"), 0.0);
        Treatment->SetNumberField(
            TEXT("skylight_intensity"),
            Diagnostic.Treatment == EFutaleufuCanopyCorridorLightingTreatment::Baseline
                ? 1.55
                : (Diagnostic.Treatment == EFutaleufuCanopyCorridorLightingTreatment::IsolatedReviewFill
                       ? 1.65
                       : 3.10));
        Treatment->SetNumberField(
            TEXT("front_fill_intensity"),
            Diagnostic.Treatment == EFutaleufuCanopyCorridorLightingTreatment::IsolatedReviewFill
                ? 0.75
                : 0.0);
        Treatment->SetNumberField(
            TEXT("back_fill_intensity"),
            Diagnostic.Treatment == EFutaleufuCanopyCorridorLightingTreatment::IsolatedReviewFill
                ? 0.38
                : 0.0);
        Treatment->SetBoolField(TEXT("saved_to_source_map"), false);
        Treatment->SetBoolField(TEXT("promotion_eligible"), false);
        Treatments->SetObjectField(Diagnostic.Token, Treatment);
    }
    Captures->SetBoolField(TEXT("all_captured"), bAllCaptured);
    Report->SetObjectField(TEXT("captures"), Captures);
    Report->SetObjectField(TEXT("placement_stats"), Stats);
    Report->SetObjectField(TEXT("lighting_treatments"), Treatments);

    FString SerializedReport;
    const TSharedRef<TJsonWriter<TCHAR, TPrettyJsonPrintPolicy<TCHAR>>> Writer =
        TJsonWriterFactory<TCHAR, TPrettyJsonPrintPolicy<TCHAR>>::Create(&SerializedReport);
    const bool bSerialized = FJsonSerializer::Serialize(Report, Writer);
    SerializedReport += TEXT("\n");
    const FString ReportRelativePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("futaleufu_native_canopy_coigue_v18_corridor_light_rig_diagnostic_report.json"));
    const FString ReportPath = FPaths::Combine(GetRepoRoot(), ReportRelativePath);
    const bool bReportSaved =
        bSerialized && FFileHelper::SaveStringToFile(SerializedReport, *ReportPath);
    OutSummary += FString::Printf(
        TEXT("%s Futaleufu native-canopy V18 corridor light-rig report -> %s\n"),
        bReportSaved ? TEXT("Saved") : TEXT("Failed to save"),
        *ReportPath);
    return bAllCaptured && bPlacementCountsIdentical && bReportSaved;
}

bool FRaftSimEditorModule::CaptureFutaleufuNativeCanopyReflectanceDiagnostics(
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
                TEXT("Futaleufu V19 reflectance diagnostic could not load texture %s.\n"),
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
    if (!LeafMaterial)
    {
        OutSummary += TEXT("Futaleufu V19 reflectance diagnostic could not rebuild the neutral native leaf material.\n");
        return false;
    }

    const FString CaptureRelativeRoot =
        TEXT("docs/environment-captures/photoreal_river_previews/landscape_candidates");
    const FString CaptureRoot = FPaths::Combine(GetRepoRoot(), CaptureRelativeRoot);
    IFileManager::Get().MakeDirectory(*CaptureRoot, true);

    struct FFutaleufuReflectanceDiagnostic
    {
        EFutaleufuCanopyCorridorRenderMode RenderMode =
            EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleFourBaseColorDoubleNoShadow;
        FString Token;
        FString Description;
        FString GuidePath;
        FString RiverEyePath;
        FFutaleufuCanopyCorridorComparisonStats GuideStats;
        FFutaleufuCanopyCorridorComparisonStats RiverEyeStats;
        bool bGuideCaptured = false;
        bool bRiverEyeCaptured = false;
    };
    TArray<FFutaleufuReflectanceDiagnostic> Diagnostics;
    auto AddDiagnostic = [&Diagnostics, &CaptureRelativeRoot](
                             EFutaleufuCanopyCorridorRenderMode RenderMode,
                             const TCHAR* Token,
                             const TCHAR* Description)
    {
        FFutaleufuReflectanceDiagnostic& Diagnostic = Diagnostics.AddDefaulted_GetRef();
        Diagnostic.RenderMode = RenderMode;
        Diagnostic.Token = Token;
        Diagnostic.Description = Description;
        Diagnostic.GuidePath = FPaths::Combine(
            CaptureRelativeRoot,
            FString::Printf(TEXT("futaleufu_v19_%s_guide_seat_downstream.png"), Token));
        Diagnostic.RiverEyePath = FPaths::Combine(
            CaptureRelativeRoot,
            FString::Printf(TEXT("futaleufu_v19_%s_river_eye_downstream.png"), Token));
    };
    AddDiagnostic(
        EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleFourBaseColorDoubleNoShadow,
        TEXT("alpha4_basecolor_236_no_shadows"),
        TEXT("native foliage with LeafBaseColorScale 2.36 and neutral transmission"));
    AddDiagnostic(
        EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleFourTransmissionWhiteNoShadow,
        TEXT("alpha4_white_transmission_no_shadows"),
        TEXT("native foliage with LeafBaseColorScale 1.18 and neutral-white transmission"));
    AddDiagnostic(
        EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleFourBaseColorDoubleTransmissionWhiteNoShadow,
        TEXT("alpha4_basecolor_236_white_transmission_no_shadows"),
        TEXT("native foliage with LeafBaseColorScale 2.36 and neutral-white transmission"));

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

    bool bAllCaptured = true;
    for (FFutaleufuReflectanceDiagnostic& Diagnostic : Diagnostics)
    {
        Diagnostic.bGuideCaptured = CapturePreviewImageForSpec(
            FutaleufuCandidate->PreviewSpec,
            CaptureRoot,
            Diagnostic.GuidePath,
            TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"),
            FString::Printf(TEXT("futaleufu_v19_%s_guide_seat_downstream"), *Diagnostic.Token),
            FString::Printf(TEXT("Futaleufu guide-seat %s"), *Diagnostic.Description),
            true,
            OutSummary,
            MakeWorldSetup(Diagnostic.RenderMode, Diagnostic.GuideStats));
        Diagnostic.bRiverEyeCaptured = CapturePreviewImageForSpec(
            FutaleufuCandidate->PreviewSpec,
            CaptureRoot,
            Diagnostic.RiverEyePath,
            TEXT("RaftSim_RiverEye_DownstreamCaptureCamera"),
            FString::Printf(TEXT("futaleufu_v19_%s_river_eye_downstream"), *Diagnostic.Token),
            FString::Printf(TEXT("Futaleufu river-eye %s"), *Diagnostic.Description),
            true,
            OutSummary,
            MakeWorldSetup(Diagnostic.RenderMode, Diagnostic.RiverEyeStats));
        bAllCaptured &= Diagnostic.bGuideCaptured && Diagnostic.bRiverEyeCaptured;
    }

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
    bool bPlacementCountsIdentical = Diagnostics.Num() == 3;
    for (int32 Index = 1; Index < Diagnostics.Num(); ++Index)
    {
        bPlacementCountsIdentical &=
            PlacementCountsMatch(Diagnostics[0].GuideStats, Diagnostics[Index].GuideStats) &&
            PlacementCountsMatch(Diagnostics[0].RiverEyeStats, Diagnostics[Index].RiverEyeStats);
    }

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

    TSharedRef<FJsonObject> Report = MakeShared<FJsonObject>();
    Report->SetStringField(
        TEXT("schema"),
        TEXT("raftsim.unreal.futaleufu_native_canopy_reflectance_diagnostic.v19"));
    Report->SetStringField(TEXT("river_id"), TEXT("futaleufu_terminator"));
    Report->SetStringField(
        TEXT("status"),
        bAllCaptured && bPlacementCountsIdentical
            ? TEXT("controlled_basecolor_transmission_and_interaction_splits_captured_pending_human_review")
            : TEXT("one_or_more_reflectance_diagnostics_failed_or_changed_placement"));
    Report->SetBoolField(TEXT("production_promoted"), false);
    Report->SetBoolField(TEXT("source_map_modified"), false);
    Report->SetBoolField(TEXT("collision_or_gameplay_authority_modified"), false);
    Report->SetBoolField(TEXT("placement_counts_identical_between_render_modes"), bPlacementCountsIdentical);
    Report->SetStringField(TEXT("source_map"), FutaleufuCandidate->PreviewSpec.MapPackagePath);
    Report->SetStringField(
        TEXT("alpha4_reference_guide_seat"),
        FPaths::Combine(CaptureRelativeRoot, TEXT("futaleufu_v18_alpha4_baseline_no_shadows_guide_seat_downstream.png")));
    Report->SetStringField(
        TEXT("alpha4_reference_river_eye"),
        FPaths::Combine(CaptureRelativeRoot, TEXT("futaleufu_v18_alpha4_baseline_no_shadows_river_eye_downstream.png")));
    Report->SetStringField(
        TEXT("control_boundary"),
        TEXT("Saved corridor lighting, exposure, native textures and graph, 4x opacity diagnostic, disabled leaf shadows, AO, normals, emissive, masks, placement, geometry, cameras, terrain, water, rocks, and physics authority remain fixed. Base-color scale and transmission tint change independently, followed by an interaction control."));

    TSharedRef<FJsonObject> MaterialDefaults = MakeShared<FJsonObject>();
    MaterialDefaults->SetNumberField(TEXT("LeafBaseColorScale"), 1.18);
    MaterialDefaults->SetStringField(TEXT("LeafTransmissionTint"), TEXT("0.55,0.78,0.36"));
    MaterialDefaults->SetNumberField(TEXT("LeafOpacityScale"), 1.0);
    MaterialDefaults->SetNumberField(TEXT("LeafAOInfluence"), 0.55);
    MaterialDefaults->SetNumberField(TEXT("LeafNormalStrength"), 1.0);
    MaterialDefaults->SetNumberField(TEXT("LeafDiagnosticEmissive"), 0.0);
    Report->SetObjectField(TEXT("retained_neutral_material_defaults"), MaterialDefaults);

    TSharedRef<FJsonObject> Captures = MakeShared<FJsonObject>();
    TSharedRef<FJsonObject> Stats = MakeShared<FJsonObject>();
    TSharedRef<FJsonObject> Modes = MakeShared<FJsonObject>();
    for (const FFutaleufuReflectanceDiagnostic& Diagnostic : Diagnostics)
    {
        Captures->SetStringField(Diagnostic.Token + TEXT("_guide_seat"), Diagnostic.GuidePath);
        Captures->SetStringField(Diagnostic.Token + TEXT("_river_eye"), Diagnostic.RiverEyePath);
        Stats->SetObjectField(Diagnostic.Token + TEXT("_guide_seat"), MakeStatsObject(Diagnostic.GuideStats));
        Stats->SetObjectField(Diagnostic.Token + TEXT("_river_eye"), MakeStatsObject(Diagnostic.RiverEyeStats));
        const bool bDoubleBaseColor =
            Diagnostic.RenderMode == EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleFourBaseColorDoubleNoShadow ||
            Diagnostic.RenderMode == EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleFourBaseColorDoubleTransmissionWhiteNoShadow;
        const bool bWhiteTransmission =
            Diagnostic.RenderMode == EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleFourTransmissionWhiteNoShadow ||
            Diagnostic.RenderMode == EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleFourBaseColorDoubleTransmissionWhiteNoShadow;
        TSharedRef<FJsonObject> Mode = MakeShared<FJsonObject>();
        Mode->SetNumberField(TEXT("LeafOpacityScale"), 4.0);
        Mode->SetBoolField(TEXT("leaf_cast_shadow"), false);
        Mode->SetNumberField(TEXT("LeafBaseColorScale"), bDoubleBaseColor ? 2.36 : 1.18);
        Mode->SetStringField(
            TEXT("LeafTransmissionTint"),
            bWhiteTransmission ? TEXT("1,1,1") : TEXT("0.55,0.78,0.36"));
        Mode->SetNumberField(TEXT("LeafAOInfluence"), 0.55);
        Mode->SetNumberField(TEXT("LeafNormalStrength"), 1.0);
        Mode->SetNumberField(TEXT("LeafDiagnosticEmissive"), 0.0);
        Mode->SetBoolField(TEXT("promotion_eligible"), false);
        Modes->SetObjectField(Diagnostic.Token, Mode);
    }
    Captures->SetBoolField(TEXT("all_captured"), bAllCaptured);
    Report->SetObjectField(TEXT("captures"), Captures);
    Report->SetObjectField(TEXT("placement_stats"), Stats);
    Report->SetObjectField(TEXT("render_modes"), Modes);

    FString SerializedReport;
    const TSharedRef<TJsonWriter<TCHAR, TPrettyJsonPrintPolicy<TCHAR>>> Writer =
        TJsonWriterFactory<TCHAR, TPrettyJsonPrintPolicy<TCHAR>>::Create(&SerializedReport);
    const bool bSerialized = FJsonSerializer::Serialize(Report, Writer);
    SerializedReport += TEXT("\n");
    const FString ReportRelativePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("futaleufu_native_canopy_coigue_v19_reflectance_diagnostic_report.json"));
    const FString ReportPath = FPaths::Combine(GetRepoRoot(), ReportRelativePath);
    const bool bReportSaved =
        bSerialized && FFileHelper::SaveStringToFile(SerializedReport, *ReportPath);
    OutSummary += FString::Printf(
        TEXT("%s Futaleufu native-canopy V19 reflectance report -> %s\n"),
        bReportSaved ? TEXT("Saved") : TEXT("Failed to save"),
        *ReportPath);
    return bAllCaptured && bPlacementCountsIdentical && bReportSaved;
}

bool FRaftSimEditorModule::CaptureFutaleufuNativeCanopyShadingModelDiagnostics(
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
                TEXT("Futaleufu V20 shading-model diagnostic could not load texture %s.\n"),
                *ObjectPath);
            return false;
        }
        NativeTextures.Add(Spec.MapKey, Texture);
    }
    UMaterial* NativeLeafMaterial = CreateOrUpdateFutaleufuNativeCanopyMaterial(
        TEXT("M_RaftSim_FutaleufuCoigue_Leaves"),
        true,
        NativeTextures,
        OutSummary);
    UMaterial* DefaultLitLeafMaterial = CreateOrUpdateFutaleufuNativeCanopyMaterial(
        TEXT("M_RaftSim_FutaleufuCoigue_Leaves_DefaultLitDiagnostic"),
        true,
        NativeTextures,
        OutSummary,
        true);
    if (!NativeLeafMaterial || !DefaultLitLeafMaterial)
    {
        OutSummary += TEXT("Futaleufu V20 shading-model diagnostic could not build both leaf materials.\n");
        return false;
    }

    const FString CaptureRelativeRoot =
        TEXT("docs/environment-captures/photoreal_river_previews/landscape_candidates");
    const FString CaptureRoot = FPaths::Combine(GetRepoRoot(), CaptureRelativeRoot);
    IFileManager::Get().MakeDirectory(*CaptureRoot, true);

    struct FFutaleufuShadingModelDiagnostic
    {
        EFutaleufuCanopyCorridorRenderMode RenderMode =
            EFutaleufuCanopyCorridorRenderMode::DefaultLitAlphaScaleFourNoShadow;
        FString Token;
        double BaseColorScale = 1.18;
        FString GuidePath;
        FString RiverEyePath;
        FFutaleufuCanopyCorridorComparisonStats GuideStats;
        FFutaleufuCanopyCorridorComparisonStats RiverEyeStats;
        bool bGuideCaptured = false;
        bool bRiverEyeCaptured = false;
    };
    TArray<FFutaleufuShadingModelDiagnostic> Diagnostics;
    auto AddDiagnostic = [&Diagnostics, &CaptureRelativeRoot](
                             EFutaleufuCanopyCorridorRenderMode RenderMode,
                             const TCHAR* Token,
                             double BaseColorScale)
    {
        FFutaleufuShadingModelDiagnostic& Diagnostic = Diagnostics.AddDefaulted_GetRef();
        Diagnostic.RenderMode = RenderMode;
        Diagnostic.Token = Token;
        Diagnostic.BaseColorScale = BaseColorScale;
        Diagnostic.GuidePath = FPaths::Combine(
            CaptureRelativeRoot,
            FString::Printf(TEXT("futaleufu_v20_%s_guide_seat_downstream.png"), Token));
        Diagnostic.RiverEyePath = FPaths::Combine(
            CaptureRelativeRoot,
            FString::Printf(TEXT("futaleufu_v20_%s_river_eye_downstream.png"), Token));
    };
    AddDiagnostic(
        EFutaleufuCanopyCorridorRenderMode::DefaultLitAlphaScaleFourNoShadow,
        TEXT("defaultlit_alpha4_basecolor_118_no_shadows"),
        1.18);
    AddDiagnostic(
        EFutaleufuCanopyCorridorRenderMode::DefaultLitAlphaScaleFourBaseColorDoubleNoShadow,
        TEXT("defaultlit_alpha4_basecolor_236_no_shadows"),
        2.36);

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

    bool bAllCaptured = true;
    for (FFutaleufuShadingModelDiagnostic& Diagnostic : Diagnostics)
    {
        const FString Description = FString::Printf(
            TEXT("masked DefaultLit same-texture foliage with LeafBaseColorScale %.2f"),
            Diagnostic.BaseColorScale);
        Diagnostic.bGuideCaptured = CapturePreviewImageForSpec(
            FutaleufuCandidate->PreviewSpec,
            CaptureRoot,
            Diagnostic.GuidePath,
            TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"),
            FString::Printf(TEXT("futaleufu_v20_%s_guide_seat_downstream"), *Diagnostic.Token),
            FString::Printf(TEXT("Futaleufu guide-seat %s"), *Description),
            true,
            OutSummary,
            MakeWorldSetup(Diagnostic.RenderMode, Diagnostic.GuideStats));
        Diagnostic.bRiverEyeCaptured = CapturePreviewImageForSpec(
            FutaleufuCandidate->PreviewSpec,
            CaptureRoot,
            Diagnostic.RiverEyePath,
            TEXT("RaftSim_RiverEye_DownstreamCaptureCamera"),
            FString::Printf(TEXT("futaleufu_v20_%s_river_eye_downstream"), *Diagnostic.Token),
            FString::Printf(TEXT("Futaleufu river-eye %s"), *Description),
            true,
            OutSummary,
            MakeWorldSetup(Diagnostic.RenderMode, Diagnostic.RiverEyeStats));
        bAllCaptured &= Diagnostic.bGuideCaptured && Diagnostic.bRiverEyeCaptured;
    }

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
    const bool bPlacementCountsIdentical = Diagnostics.Num() == 2 &&
        PlacementCountsMatch(Diagnostics[0].GuideStats, Diagnostics[1].GuideStats) &&
        PlacementCountsMatch(Diagnostics[0].RiverEyeStats, Diagnostics[1].RiverEyeStats);

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

    TSharedRef<FJsonObject> Report = MakeShared<FJsonObject>();
    Report->SetStringField(
        TEXT("schema"),
        TEXT("raftsim.unreal.futaleufu_native_canopy_shading_model_diagnostic.v20"));
    Report->SetStringField(TEXT("river_id"), TEXT("futaleufu_terminator"));
    Report->SetStringField(
        TEXT("status"),
        bAllCaptured && bPlacementCountsIdentical
            ? TEXT("same_texture_defaultlit_pairs_captured_pending_human_review")
            : TEXT("one_or_more_shading_model_diagnostics_failed_or_changed_placement"));
    Report->SetBoolField(TEXT("production_promoted"), false);
    Report->SetBoolField(TEXT("source_map_modified"), false);
    Report->SetBoolField(TEXT("collision_or_gameplay_authority_modified"), false);
    Report->SetBoolField(TEXT("placement_counts_identical_between_render_modes"), bPlacementCountsIdentical);
    Report->SetStringField(TEXT("source_map"), FutaleufuCandidate->PreviewSpec.MapPackagePath);
    Report->SetStringField(
        TEXT("defaultlit_material"),
        TEXT("/Game/RaftSim/Environment/ProceduralVegetation/FutaleufuNativeCanopy/Materials/M_RaftSim_FutaleufuCoigue_Leaves_DefaultLitDiagnostic"));
    Report->SetStringField(
        TEXT("control_boundary"),
        TEXT("The source leaf textures, masked opacity graph, 4x opacity diagnostic, two-sided geometry, normal graph, base-color scales, saved corridor lighting, shadows, masks, placement, meshes, cameras, terrain, water, rocks, and physics authority remain fixed. DefaultLit omits only the TwoSidedFoliage-specific subsurface input."));

    TSharedRef<FJsonObject> References = MakeShared<FJsonObject>();
    References->SetStringField(
        TEXT("twosidedfoliage_basecolor_118_guide_seat"),
        FPaths::Combine(CaptureRelativeRoot, TEXT("futaleufu_v18_alpha4_baseline_no_shadows_guide_seat_downstream.png")));
    References->SetStringField(
        TEXT("twosidedfoliage_basecolor_118_river_eye"),
        FPaths::Combine(CaptureRelativeRoot, TEXT("futaleufu_v18_alpha4_baseline_no_shadows_river_eye_downstream.png")));
    References->SetStringField(
        TEXT("twosidedfoliage_basecolor_236_guide_seat"),
        FPaths::Combine(CaptureRelativeRoot, TEXT("futaleufu_v19_alpha4_basecolor_236_no_shadows_guide_seat_downstream.png")));
    References->SetStringField(
        TEXT("twosidedfoliage_basecolor_236_river_eye"),
        FPaths::Combine(CaptureRelativeRoot, TEXT("futaleufu_v19_alpha4_basecolor_236_no_shadows_river_eye_downstream.png")));
    Report->SetObjectField(TEXT("twosidedfoliage_references"), References);

    TSharedRef<FJsonObject> Captures = MakeShared<FJsonObject>();
    TSharedRef<FJsonObject> Stats = MakeShared<FJsonObject>();
    TSharedRef<FJsonObject> Modes = MakeShared<FJsonObject>();
    for (const FFutaleufuShadingModelDiagnostic& Diagnostic : Diagnostics)
    {
        Captures->SetStringField(Diagnostic.Token + TEXT("_guide_seat"), Diagnostic.GuidePath);
        Captures->SetStringField(Diagnostic.Token + TEXT("_river_eye"), Diagnostic.RiverEyePath);
        Stats->SetObjectField(Diagnostic.Token + TEXT("_guide_seat"), MakeStatsObject(Diagnostic.GuideStats));
        Stats->SetObjectField(Diagnostic.Token + TEXT("_river_eye"), MakeStatsObject(Diagnostic.RiverEyeStats));
        TSharedRef<FJsonObject> Mode = MakeShared<FJsonObject>();
        Mode->SetStringField(TEXT("shading_model"), TEXT("DefaultLit"));
        Mode->SetBoolField(TEXT("masked"), true);
        Mode->SetBoolField(TEXT("two_sided_geometry"), true);
        Mode->SetNumberField(TEXT("LeafOpacityScale"), 4.0);
        Mode->SetNumberField(TEXT("LeafBaseColorScale"), Diagnostic.BaseColorScale);
        Mode->SetBoolField(TEXT("leaf_cast_shadow"), false);
        Mode->SetBoolField(TEXT("promotion_eligible"), false);
        Modes->SetObjectField(Diagnostic.Token, Mode);
    }
    Captures->SetBoolField(TEXT("all_captured"), bAllCaptured);
    Report->SetObjectField(TEXT("captures"), Captures);
    Report->SetObjectField(TEXT("placement_stats"), Stats);
    Report->SetObjectField(TEXT("render_modes"), Modes);

    FString SerializedReport;
    const TSharedRef<TJsonWriter<TCHAR, TPrettyJsonPrintPolicy<TCHAR>>> Writer =
        TJsonWriterFactory<TCHAR, TPrettyJsonPrintPolicy<TCHAR>>::Create(&SerializedReport);
    const bool bSerialized = FJsonSerializer::Serialize(Report, Writer);
    SerializedReport += TEXT("\n");
    const FString ReportRelativePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("futaleufu_native_canopy_coigue_v20_shading_model_diagnostic_report.json"));
    const FString ReportPath = FPaths::Combine(GetRepoRoot(), ReportRelativePath);
    const bool bReportSaved =
        bSerialized && FFileHelper::SaveStringToFile(SerializedReport, *ReportPath);
    OutSummary += FString::Printf(
        TEXT("%s Futaleufu native-canopy V20 shading-model report -> %s\n"),
        bReportSaved ? TEXT("Saved") : TEXT("Failed to save"),
        *ReportPath);
    return bAllCaptured && bPlacementCountsIdentical && bReportSaved;
}

bool FRaftSimEditorModule::CaptureFutaleufuNativeCanopyMipPaddingDiagnostics(
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
    if (!CreateFutaleufuNativeCanopyTextureAssets(NativeTextures, OutSummary))
    {
        OutSummary += TEXT("Futaleufu V21 mip-padding diagnostic could not import the corrected native textures.\n");
        return false;
    }
    UMaterial* LeafMaterial = CreateOrUpdateFutaleufuNativeCanopyMaterial(
        TEXT("M_RaftSim_FutaleufuCoigue_Leaves"),
        true,
        NativeTextures,
        OutSummary);
    if (!LeafMaterial)
    {
        OutSummary += TEXT("Futaleufu V21 mip-padding diagnostic could not rebuild native TwoSidedFoliage.\n");
        return false;
    }

    const FString CaptureRelativeRoot =
        TEXT("docs/environment-captures/photoreal_river_previews/landscape_candidates");
    const FString CaptureRoot = FPaths::Combine(GetRepoRoot(), CaptureRelativeRoot);
    IFileManager::Get().MakeDirectory(*CaptureRoot, true);
    FString GuidePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("futaleufu_v21_alpha_preserved_rgb_padded_alpha4_no_shadows_guide_seat_downstream.png"));
    FString RiverEyePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("futaleufu_v21_alpha_preserved_rgb_padded_alpha4_no_shadows_river_eye_downstream.png"));
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
                EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleFourNoShadow,
                Stats,
                Summary);
        };
    };
    const bool bGuideCaptured = CapturePreviewImageForSpec(
        FutaleufuCandidate->PreviewSpec,
        CaptureRoot,
        GuidePath,
        TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"),
        TEXT("futaleufu_v21_alpha_preserved_rgb_padded_alpha4_no_shadows_guide_seat_downstream"),
        TEXT("Futaleufu guide-seat alpha-preserved per-tile RGB-padded native foliage"),
        true,
        OutSummary,
        MakeWorldSetup(GuideStats));
    const bool bRiverEyeCaptured = CapturePreviewImageForSpec(
        FutaleufuCandidate->PreviewSpec,
        CaptureRoot,
        RiverEyePath,
        TEXT("RaftSim_RiverEye_DownstreamCaptureCamera"),
        TEXT("futaleufu_v21_alpha_preserved_rgb_padded_alpha4_no_shadows_river_eye_downstream"),
        TEXT("Futaleufu river-eye alpha-preserved per-tile RGB-padded native foliage"),
        true,
        OutSummary,
        MakeWorldSetup(RiverEyeStats));
    const bool bAllCaptured = bGuideCaptured && bRiverEyeCaptured;

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

    TSharedRef<FJsonObject> Report = MakeShared<FJsonObject>();
    Report->SetStringField(
        TEXT("schema"),
        TEXT("raftsim.unreal.futaleufu_native_canopy_mip_padding_diagnostic.v21"));
    Report->SetStringField(TEXT("river_id"), TEXT("futaleufu_terminator"));
    Report->SetStringField(
        TEXT("status"),
        bAllCaptured
            ? TEXT("alpha_preserved_rgb_padded_native_pair_captured_pending_human_review")
            : TEXT("one_or_more_mip_padding_captures_failed"));
    Report->SetBoolField(TEXT("production_promoted"), false);
    Report->SetBoolField(TEXT("source_map_modified"), false);
    Report->SetBoolField(TEXT("collision_or_gameplay_authority_modified"), false);
    Report->SetStringField(TEXT("source_map"), FutaleufuCandidate->PreviewSpec.MapPackagePath);
    Report->SetStringField(
        TEXT("source_manifest"),
        TEXT("unreal/Content/RaftSim/Environment/ProceduralVegetation/FutaleufuNativeCanopy/futaleufu_native_canopy_texture_manifest.json"));
    Report->SetStringField(
        TEXT("reference_guide_seat"),
        FPaths::Combine(CaptureRelativeRoot, TEXT("futaleufu_v18_alpha4_baseline_no_shadows_guide_seat_downstream.png")));
    Report->SetStringField(
        TEXT("reference_river_eye"),
        FPaths::Combine(CaptureRelativeRoot, TEXT("futaleufu_v18_alpha4_baseline_no_shadows_river_eye_downstream.png")));
    Report->SetStringField(
        TEXT("control_boundary"),
        TEXT("The alpha channel, nontransparent source RGB, normal and packed texture sources, native TwoSidedFoliage graph and defaults, 4x opacity diagnostic, disabled leaf shadows, saved lighting, masks, placement, meshes, cameras, terrain, water, rocks, and physics authority remain fixed. Only RGB at alpha <=2 is padded up to 24 pixels within each atlas tile before Unreal mip generation."));

    TSharedRef<FJsonObject> PaddingContract = MakeShared<FJsonObject>();
    PaddingContract->SetNumberField(TEXT("padding_pixels"), 24);
    PaddingContract->SetNumberField(TEXT("alpha_threshold_255"), 2);
    PaddingContract->SetNumberField(TEXT("atlas_columns"), 4);
    PaddingContract->SetNumberField(TEXT("atlas_rows"), 4);
    PaddingContract->SetBoolField(TEXT("tile_boundary_crossing_allowed"), false);
    PaddingContract->SetBoolField(TEXT("alpha_preserved_byte_for_byte"), true);
    PaddingContract->SetBoolField(TEXT("nontransparent_rgb_preserved_byte_for_byte"), true);
    PaddingContract->SetStringField(
        TEXT("alpha_sha256"),
        TEXT("c8b8ce2baab7a740417696a9e3cfdbcd5ad42458ed30828358922d473e1c18c6"));
    PaddingContract->SetStringField(
        TEXT("nontransparent_rgb_sha256"),
        TEXT("0a4101494bd6a579e8fc0390da9cc13bd2f51f0d9735d5e44e7a1095b552ae16"));
    PaddingContract->SetNumberField(TEXT("padded_transparent_pixel_count"), 517669);
    Report->SetObjectField(TEXT("padding_contract"), PaddingContract);

    TSharedRef<FJsonObject> Captures = MakeShared<FJsonObject>();
    Captures->SetStringField(TEXT("guide_seat"), GuidePath);
    Captures->SetStringField(TEXT("river_eye"), RiverEyePath);
    Captures->SetBoolField(TEXT("all_captured"), bAllCaptured);
    Report->SetObjectField(TEXT("captures"), Captures);
    TSharedRef<FJsonObject> PlacementStats = MakeShared<FJsonObject>();
    PlacementStats->SetObjectField(TEXT("guide_seat"), MakeStatsObject(GuideStats));
    PlacementStats->SetObjectField(TEXT("river_eye"), MakeStatsObject(RiverEyeStats));
    Report->SetObjectField(TEXT("placement_stats"), PlacementStats);

    FString SerializedReport;
    const TSharedRef<TJsonWriter<TCHAR, TPrettyJsonPrintPolicy<TCHAR>>> Writer =
        TJsonWriterFactory<TCHAR, TPrettyJsonPrintPolicy<TCHAR>>::Create(&SerializedReport);
    const bool bSerialized = FJsonSerializer::Serialize(Report, Writer);
    SerializedReport += TEXT("\n");
    const FString ReportRelativePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("futaleufu_native_canopy_coigue_v21_mip_padding_diagnostic_report.json"));
    const FString ReportPath = FPaths::Combine(GetRepoRoot(), ReportRelativePath);
    const bool bReportSaved =
        bSerialized && FFileHelper::SaveStringToFile(SerializedReport, *ReportPath);
    OutSummary += FString::Printf(
        TEXT("%s Futaleufu native-canopy V21 mip-padding report -> %s\n"),
        bReportSaved ? TEXT("Saved") : TEXT("Failed to save"),
        *ReportPath);
    return bAllCaptured && bReportSaved;
}

bool FRaftSimEditorModule::CaptureFutaleufuNativeCanopyOpacitySelectionDiagnostics(
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
    if (!CreateFutaleufuNativeCanopyTextureAssets(NativeTextures, OutSummary))
    {
        OutSummary += TEXT("Futaleufu V22 opacity-selection diagnostic could not import the corrected native textures.\n");
        return false;
    }
    UMaterial* LeafMaterial = CreateOrUpdateFutaleufuNativeCanopyMaterial(
        TEXT("M_RaftSim_FutaleufuCoigue_Leaves"),
        true,
        NativeTextures,
        OutSummary);
    if (!LeafMaterial)
    {
        OutSummary += TEXT("Futaleufu V22 opacity-selection diagnostic could not rebuild native TwoSidedFoliage.\n");
        return false;
    }

    const FString CaptureRelativeRoot =
        TEXT("docs/environment-captures/photoreal_river_previews/landscape_candidates");
    const FString CaptureRoot = FPaths::Combine(GetRepoRoot(), CaptureRelativeRoot);
    IFileManager::Get().MakeDirectory(*CaptureRoot, true);
    struct FFutaleufuOpacitySelectionDiagnostic
    {
        EFutaleufuCanopyCorridorRenderMode RenderMode =
            EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleTwoNoShadow;
        FString Token;
        double OpacityScale = 2.0;
        FString GuidePath;
        FString RiverEyePath;
        FFutaleufuCanopyCorridorComparisonStats GuideStats;
        FFutaleufuCanopyCorridorComparisonStats RiverEyeStats;
        bool bGuideCaptured = false;
        bool bRiverEyeCaptured = false;
    };
    TArray<FFutaleufuOpacitySelectionDiagnostic> Diagnostics;
    auto AddDiagnostic = [&Diagnostics, &CaptureRelativeRoot](
                             EFutaleufuCanopyCorridorRenderMode RenderMode,
                             const TCHAR* Token,
                             double OpacityScale)
    {
        FFutaleufuOpacitySelectionDiagnostic& Diagnostic = Diagnostics.AddDefaulted_GetRef();
        Diagnostic.RenderMode = RenderMode;
        Diagnostic.Token = Token;
        Diagnostic.OpacityScale = OpacityScale;
        Diagnostic.GuidePath = FPaths::Combine(
            CaptureRelativeRoot,
            FString::Printf(TEXT("futaleufu_v22_%s_guide_seat_downstream.png"), Token));
        Diagnostic.RiverEyePath = FPaths::Combine(
            CaptureRelativeRoot,
            FString::Printf(TEXT("futaleufu_v22_%s_river_eye_downstream.png"), Token));
    };
    AddDiagnostic(
        EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleTwoNoShadow,
        TEXT("rgb_padded_alpha2_no_shadows"),
        2.0);
    AddDiagnostic(
        EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleThreeNoShadow,
        TEXT("rgb_padded_alpha3_no_shadows"),
        3.0);

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
    bool bAllCaptured = true;
    for (FFutaleufuOpacitySelectionDiagnostic& Diagnostic : Diagnostics)
    {
        Diagnostic.bGuideCaptured = CapturePreviewImageForSpec(
            FutaleufuCandidate->PreviewSpec,
            CaptureRoot,
            Diagnostic.GuidePath,
            TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"),
            FString::Printf(TEXT("futaleufu_v22_%s_guide_seat_downstream"), *Diagnostic.Token),
            FString::Printf(TEXT("Futaleufu guide-seat RGB-padded alpha %.0f native foliage"), Diagnostic.OpacityScale),
            true,
            OutSummary,
            MakeWorldSetup(Diagnostic.RenderMode, Diagnostic.GuideStats));
        Diagnostic.bRiverEyeCaptured = CapturePreviewImageForSpec(
            FutaleufuCandidate->PreviewSpec,
            CaptureRoot,
            Diagnostic.RiverEyePath,
            TEXT("RaftSim_RiverEye_DownstreamCaptureCamera"),
            FString::Printf(TEXT("futaleufu_v22_%s_river_eye_downstream"), *Diagnostic.Token),
            FString::Printf(TEXT("Futaleufu river-eye RGB-padded alpha %.0f native foliage"), Diagnostic.OpacityScale),
            true,
            OutSummary,
            MakeWorldSetup(Diagnostic.RenderMode, Diagnostic.RiverEyeStats));
        bAllCaptured &= Diagnostic.bGuideCaptured && Diagnostic.bRiverEyeCaptured;
    }

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
    const bool bPlacementCountsIdentical = Diagnostics.Num() == 2 &&
        PlacementCountsMatch(Diagnostics[0].GuideStats, Diagnostics[1].GuideStats) &&
        PlacementCountsMatch(Diagnostics[0].RiverEyeStats, Diagnostics[1].RiverEyeStats);
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

    TSharedRef<FJsonObject> Report = MakeShared<FJsonObject>();
    Report->SetStringField(
        TEXT("schema"),
        TEXT("raftsim.unreal.futaleufu_native_canopy_opacity_selection_diagnostic.v22"));
    Report->SetStringField(TEXT("river_id"), TEXT("futaleufu_terminator"));
    Report->SetStringField(
        TEXT("status"),
        bAllCaptured && bPlacementCountsIdentical
            ? TEXT("rgb_padded_alpha2_and_alpha3_pairs_captured_pending_human_review")
            : TEXT("one_or_more_opacity_selection_captures_failed_or_changed_placement"));
    Report->SetBoolField(TEXT("production_promoted"), false);
    Report->SetBoolField(TEXT("source_map_modified"), false);
    Report->SetBoolField(TEXT("collision_or_gameplay_authority_modified"), false);
    Report->SetBoolField(TEXT("placement_counts_identical_between_render_modes"), bPlacementCountsIdentical);
    Report->SetStringField(TEXT("source_map"), FutaleufuCandidate->PreviewSpec.MapPackagePath);
    Report->SetStringField(
        TEXT("alpha4_reference_guide_seat"),
        FPaths::Combine(CaptureRelativeRoot, TEXT("futaleufu_v21_alpha_preserved_rgb_padded_alpha4_no_shadows_guide_seat_downstream.png")));
    Report->SetStringField(
        TEXT("alpha4_reference_river_eye"),
        FPaths::Combine(CaptureRelativeRoot, TEXT("futaleufu_v21_alpha_preserved_rgb_padded_alpha4_no_shadows_river_eye_downstream.png")));
    Report->SetStringField(
        TEXT("control_boundary"),
        TEXT("The corrected RGB-padded atlas and alpha, native TwoSidedFoliage graph and neutral reflectance/transmission/AO/normal/emissive defaults, disabled leaf shadows, saved lighting, masks, placement, meshes, cameras, terrain, water, rocks, and physics authority remain fixed. Only LeafOpacityScale changes from the retained alpha4 reference to 2 or 3."));

    TSharedRef<FJsonObject> Captures = MakeShared<FJsonObject>();
    TSharedRef<FJsonObject> Stats = MakeShared<FJsonObject>();
    TSharedRef<FJsonObject> Modes = MakeShared<FJsonObject>();
    for (const FFutaleufuOpacitySelectionDiagnostic& Diagnostic : Diagnostics)
    {
        Captures->SetStringField(Diagnostic.Token + TEXT("_guide_seat"), Diagnostic.GuidePath);
        Captures->SetStringField(Diagnostic.Token + TEXT("_river_eye"), Diagnostic.RiverEyePath);
        Stats->SetObjectField(Diagnostic.Token + TEXT("_guide_seat"), MakeStatsObject(Diagnostic.GuideStats));
        Stats->SetObjectField(Diagnostic.Token + TEXT("_river_eye"), MakeStatsObject(Diagnostic.RiverEyeStats));
        TSharedRef<FJsonObject> Mode = MakeShared<FJsonObject>();
        Mode->SetNumberField(TEXT("LeafOpacityScale"), Diagnostic.OpacityScale);
        Mode->SetNumberField(TEXT("LeafBaseColorScale"), 1.18);
        Mode->SetStringField(TEXT("LeafTransmissionTint"), TEXT("0.55,0.78,0.36"));
        Mode->SetBoolField(TEXT("leaf_cast_shadow"), false);
        Mode->SetBoolField(TEXT("promotion_eligible"), false);
        Modes->SetObjectField(Diagnostic.Token, Mode);
    }
    Captures->SetBoolField(TEXT("all_captured"), bAllCaptured);
    Report->SetObjectField(TEXT("captures"), Captures);
    Report->SetObjectField(TEXT("placement_stats"), Stats);
    Report->SetObjectField(TEXT("render_modes"), Modes);

    FString SerializedReport;
    const TSharedRef<TJsonWriter<TCHAR, TPrettyJsonPrintPolicy<TCHAR>>> Writer =
        TJsonWriterFactory<TCHAR, TPrettyJsonPrintPolicy<TCHAR>>::Create(&SerializedReport);
    const bool bSerialized = FJsonSerializer::Serialize(Report, Writer);
    SerializedReport += TEXT("\n");
    const FString ReportRelativePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("futaleufu_native_canopy_coigue_v22_opacity_selection_diagnostic_report.json"));
    const FString ReportPath = FPaths::Combine(GetRepoRoot(), ReportRelativePath);
    const bool bReportSaved =
        bSerialized && FFileHelper::SaveStringToFile(SerializedReport, *ReportPath);
    OutSummary += FString::Printf(
        TEXT("%s Futaleufu native-canopy V22 opacity-selection report -> %s\n"),
        bReportSaved ? TEXT("Saved") : TEXT("Failed to save"),
        *ReportPath);
    return bAllCaptured && bPlacementCountsIdentical && bReportSaved;
}

bool FRaftSimEditorModule::CaptureFutaleufuNativeCanopyBoundedShadowDiagnostics(
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
    if (!CreateFutaleufuNativeCanopyTextureAssets(NativeTextures, OutSummary))
    {
        OutSummary += TEXT("Futaleufu V23 bounded-shadow diagnostic could not import the corrected native textures.\n");
        return false;
    }
    UMaterial* LeafMaterial = CreateOrUpdateFutaleufuNativeCanopyMaterial(
        TEXT("M_RaftSim_FutaleufuCoigue_Leaves"),
        true,
        NativeTextures,
        OutSummary);
    if (!LeafMaterial)
    {
        OutSummary += TEXT("Futaleufu V23 bounded-shadow diagnostic could not rebuild native TwoSidedFoliage.\n");
        return false;
    }

    const FString CaptureRelativeRoot =
        TEXT("docs/environment-captures/photoreal_river_previews/landscape_candidates");
    const FString CaptureRoot = FPaths::Combine(GetRepoRoot(), CaptureRelativeRoot);
    IFileManager::Get().MakeDirectory(*CaptureRoot, true);
    FString GuidePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("futaleufu_v23_rgb_padded_alpha2_bounded_near_shadows_guide_seat_downstream.png"));
    FString RiverEyePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("futaleufu_v23_rgb_padded_alpha2_bounded_near_shadows_river_eye_downstream.png"));
    const FString GuideReferencePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("futaleufu_v22_rgb_padded_alpha2_no_shadows_guide_seat_downstream.png"));
    const FString RiverEyeReferencePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("futaleufu_v22_rgb_padded_alpha2_no_shadows_river_eye_downstream.png"));
    const bool bReferencesExist =
        FPaths::FileExists(FPaths::Combine(GetRepoRoot(), GuideReferencePath)) &&
        FPaths::FileExists(FPaths::Combine(GetRepoRoot(), RiverEyeReferencePath));

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
                EFutaleufuCanopyCorridorRenderMode::NativeAlphaScaleTwoBoundedShadow,
                Stats,
                Summary);
        };
    };
    const bool bGuideCaptured = CapturePreviewImageForSpec(
        FutaleufuCandidate->PreviewSpec,
        CaptureRoot,
        GuidePath,
        TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"),
        TEXT("futaleufu_v23_rgb_padded_alpha2_bounded_near_shadows_guide_seat_downstream"),
        TEXT("Futaleufu guide-seat RGB-padded alpha2 bounded near dynamic shadows"),
        true,
        OutSummary,
        MakeWorldSetup(GuideStats));
    const bool bRiverEyeCaptured = CapturePreviewImageForSpec(
        FutaleufuCandidate->PreviewSpec,
        CaptureRoot,
        RiverEyePath,
        TEXT("RaftSim_RiverEye_DownstreamCaptureCamera"),
        TEXT("futaleufu_v23_rgb_padded_alpha2_bounded_near_shadows_river_eye_downstream"),
        TEXT("Futaleufu river-eye RGB-padded alpha2 bounded near dynamic shadows"),
        true,
        OutSummary,
        MakeWorldSetup(RiverEyeStats));
    const bool bAllCaptured = bGuideCaptured && bRiverEyeCaptured;

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

    TSharedRef<FJsonObject> Report = MakeShared<FJsonObject>();
    Report->SetStringField(
        TEXT("schema"),
        TEXT("raftsim.unreal.futaleufu_native_canopy_bounded_shadow_diagnostic.v23"));
    Report->SetStringField(TEXT("river_id"), TEXT("futaleufu_terminator"));
    Report->SetStringField(
        TEXT("status"),
        bAllCaptured && bReferencesExist
            ? TEXT("alpha2_bounded_near_shadow_pair_captured_pending_artifact_review")
            : TEXT("bounded_shadow_capture_or_reference_missing"));
    Report->SetBoolField(TEXT("production_promoted"), false);
    Report->SetBoolField(TEXT("source_map_modified"), false);
    Report->SetBoolField(TEXT("collision_or_gameplay_authority_modified"), false);
    Report->SetBoolField(TEXT("no_shadow_references_exist"), bReferencesExist);
    Report->SetStringField(TEXT("source_map"), FutaleufuCandidate->PreviewSpec.MapPackagePath);
    Report->SetStringField(
        TEXT("control_boundary"),
        TEXT("The corrected RGB-padded atlas, alpha2 dynamic material, native TwoSidedFoliage graph and neutral reflectance/transmission/AO/normal/emissive defaults, saved lighting, masks, placement, meshes, cameras, terrain, water, rocks, and physics authority remain fixed. Relative to V22 alpha2, only near-representation leaf dynamic shadows are enabled; mid and runtime-far leaf shadows, static shadows, contact shadows, distance-field lighting, and dynamic indirect lighting remain disabled."));

    TSharedRef<FJsonObject> Captures = MakeShared<FJsonObject>();
    Captures->SetStringField(TEXT("guide_seat_bounded_shadow"), GuidePath);
    Captures->SetStringField(TEXT("river_eye_bounded_shadow"), RiverEyePath);
    Captures->SetStringField(TEXT("guide_seat_no_shadow_reference"), GuideReferencePath);
    Captures->SetStringField(TEXT("river_eye_no_shadow_reference"), RiverEyeReferencePath);
    Captures->SetBoolField(TEXT("all_captured"), bAllCaptured);
    Report->SetObjectField(TEXT("captures"), Captures);

    TSharedRef<FJsonObject> PlacementStats = MakeShared<FJsonObject>();
    PlacementStats->SetObjectField(TEXT("guide_seat"), MakeStatsObject(GuideStats));
    PlacementStats->SetObjectField(TEXT("river_eye"), MakeStatsObject(RiverEyeStats));
    Report->SetObjectField(TEXT("placement_stats"), PlacementStats);

    TSharedRef<FJsonObject> ShadowPolicy = MakeShared<FJsonObject>();
    ShadowPolicy->SetNumberField(TEXT("LeafOpacityScale"), 2.0);
    ShadowPolicy->SetStringField(TEXT("shadowed_leaf_representation"), TEXT("near_only"));
    ShadowPolicy->SetNumberField(TEXT("near_leaf_cull_distance_cm"), 38000);
    ShadowPolicy->SetBoolField(TEXT("cast_shadow"), true);
    ShadowPolicy->SetBoolField(TEXT("cast_dynamic_shadow"), true);
    ShadowPolicy->SetBoolField(TEXT("cast_static_shadow"), false);
    ShadowPolicy->SetBoolField(TEXT("cast_contact_shadow"), false);
    ShadowPolicy->SetBoolField(TEXT("affect_distance_field_lighting"), false);
    ShadowPolicy->SetBoolField(TEXT("affect_dynamic_indirect_lighting"), false);
    ShadowPolicy->SetBoolField(TEXT("mid_leaf_cast_shadow"), false);
    ShadowPolicy->SetBoolField(TEXT("runtime_far_leaf_cast_shadow"), false);
    Report->SetObjectField(TEXT("bounded_shadow_policy"), ShadowPolicy);

    FString SerializedReport;
    const TSharedRef<TJsonWriter<TCHAR, TPrettyJsonPrintPolicy<TCHAR>>> Writer =
        TJsonWriterFactory<TCHAR, TPrettyJsonPrintPolicy<TCHAR>>::Create(&SerializedReport);
    const bool bSerialized = FJsonSerializer::Serialize(Report, Writer);
    SerializedReport += TEXT("\n");
    const FString ReportRelativePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("futaleufu_native_canopy_coigue_v23_bounded_shadow_diagnostic_report.json"));
    const FString ReportPath = FPaths::Combine(GetRepoRoot(), ReportRelativePath);
    const bool bReportSaved =
        bSerialized && FFileHelper::SaveStringToFile(SerializedReport, *ReportPath);
    OutSummary += FString::Printf(
        TEXT("%s Futaleufu native-canopy V23 bounded-shadow report -> %s\n"),
        bReportSaved ? TEXT("Saved") : TEXT("Failed to save"),
        *ReportPath);
    return bAllCaptured && bReferencesExist && bReportSaved;
}
