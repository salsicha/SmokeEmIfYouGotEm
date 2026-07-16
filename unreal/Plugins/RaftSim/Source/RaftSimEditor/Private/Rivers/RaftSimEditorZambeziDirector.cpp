#include "Environment/RaftSimEditorEnvironmentInternal.h"

using namespace RaftSimEditorEnvironment;

bool FRaftSimEditorModule::CreateZambeziBatokaBasaltFamily(FString& OutSummary)
{
    OutSummary.Reset();
    if (!GEditor)
    {
        OutSummary += TEXT("No editor is available for the Batoka basalt family review.\n");
        return false;
    }

    UMaterialInterface* BasaltMaterial = LoadOrCreateZambeziBatokaBasaltReviewMaterial(OutSummary);
    if (!BasaltMaterial)
    {
        return false;
    }

    struct FModuleRuntime
    {
        FZambeziBatokaBasaltModuleDefinition Definition;
        FVector WorldOffset = FVector::ZeroVector;
        FZambeziBatokaBasaltModuleMetrics Metrics;
        FString MeshPackagePath;
        UStaticMesh* Mesh = nullptr;
    };

    TArray<FModuleRuntime> Modules;
    Modules.SetNum(4);
    Modules[0].Definition = {
        TEXT("lower_massive_scarp"),
        TEXT("lower massive scarp"),
        TEXT("LowerMassiveScarp"),
        1301,
        3200.0f,
        1500.0f,
        2600.0f,
        9,
        3,
        -1.0f,
        0.0f,
        0.0f,
        1.15f,
        0.18f};
    Modules[1].Definition = {
        TEXT("jointed_mid_scarp"),
        TEXT("jointed middle scarp"),
        TEXT("JointedMidScarp"),
        2903,
        2800.0f,
        1400.0f,
        3000.0f,
        11,
        4,
        0.58f,
        0.12f,
        290.0f,
        0.92f,
        0.22f};
    Modules[2].Definition = {
        TEXT("irregular_brecciated_upper"),
        TEXT("irregular brecciated upper scarp"),
        TEXT("IrregularBrecciatedUpper"),
        4703,
        3600.0f,
        1700.0f,
        2200.0f,
        10,
        3,
        0.34f,
        0.16f,
        410.0f,
        1.28f,
        0.72f};
    Modules[3].Definition = {
        TEXT("talus_ledged_spur"),
        TEXT("talus-ledged rock spur"),
        TEXT("TalusLedgedSpur"),
        6701,
        3000.0f,
        1900.0f,
        2400.0f,
        8,
        3,
        0.72f,
        0.10f,
        -260.0f,
        1.55f,
        0.42f};
    for (int32 ModuleIndex = 0; ModuleIndex < Modules.Num(); ++ModuleIndex)
    {
        Modules[ModuleIndex].WorldOffset = FVector(ModuleIndex * 500000.0f, 0.0f, 0.0f);
    }

    UWorld* World = UEditorLoadingAndSavingUtils::NewBlankMap(false);
    if (!World)
    {
        OutSummary += TEXT("Could not create the isolated Batoka basalt review map.\n");
        return false;
    }

    static const FString MeshRoot =
        TEXT("/Game/RaftSim/Environment/ProceduralGeology/ZambeziBatokaBasalt/Meshes/");
    bool bSceneComplete = true;
    for (FModuleRuntime& Module : Modules)
    {
        TArray<FVector> Vertices;
        TArray<int32> Triangles;
        TArray<FVector> Normals;
        TArray<FVector2D> UVs;
        TArray<FLinearColor> VertexColors;
        BuildZambeziBatokaBasaltModuleGeometry(
            Module.Definition,
            Vertices,
            Triangles,
            Normals,
            UVs,
            VertexColors,
            Module.Metrics);
        const bool bGeometryValid =
            Module.Metrics.Bounds.IsValid &&
            Module.Metrics.WallCellCount ==
                Module.Definition.ColumnCount * 3 *
                    Module.Definition.MinimumLayerCount * 6 &&
            Module.Metrics.TalusBlockCount >= 24 &&
            Module.Metrics.VertexCount == Vertices.Num() &&
            Module.Metrics.TriangleCount == Triangles.Num() / 3 &&
            Normals.Num() == Vertices.Num() &&
            UVs.Num() == Vertices.Num() &&
            VertexColors.Num() == Vertices.Num();
        if (!bGeometryValid)
        {
            OutSummary += FString::Printf(
                TEXT("Batoka module %s failed its deterministic geometry contract.\n"),
                *Module.Definition.Id);
            return false;
        }

        AActor* ProceduralActor = AddPreviewProceduralMeshActor(
            World,
            FString::Printf(TEXT("RaftSim_ZambeziBatokaBasalt_%s_Procedural"), *Module.Definition.AssetToken),
            Vertices,
            Triangles,
            Normals,
            UVs,
            FLinearColor::White,
            BasaltMaterial,
            &VertexColors,
            false);
        if (!ProceduralActor)
        {
            OutSummary += FString::Printf(
                TEXT("Could not construct Batoka module %s.\n"),
                *Module.Definition.Id);
            return false;
        }

        Module.MeshPackagePath = MeshRoot + FString::Printf(
            TEXT("SM_RaftSim_ZambeziBatokaBasalt_%s_V10"),
            *Module.Definition.AssetToken);
        Module.Mesh = ConvertNativeCanopyProceduralActorToStaticMesh(
            ProceduralActor,
            Module.MeshPackagePath,
            BasaltMaterial,
            true,
            ENaniteShapePreservation::None,
            OutSummary);
        ProceduralActor->Destroy();
        if (!Module.Mesh || !Module.Mesh->IsNaniteEnabled())
        {
            OutSummary += FString::Printf(
                TEXT("Batoka module %s did not produce a Nanite static mesh.\n"),
                *Module.Definition.Id);
            return false;
        }

        AStaticMeshActor* ModuleActor = World->SpawnActor<AStaticMeshActor>(
            AStaticMeshActor::StaticClass(),
            FTransform(FRotator::ZeroRotator, Module.WorldOffset));
        bSceneComplete &= ModuleActor && ModuleActor->GetStaticMeshComponent();
        if (ModuleActor && ModuleActor->GetStaticMeshComponent())
        {
            ModuleActor->SetActorLabel(FString::Printf(
                TEXT("RaftSim_ZambeziBatokaBasalt_%s_V10_IsolatedReview"),
                *Module.Definition.AssetToken));
            ModuleActor->Tags.Add(TEXT("RaftSim_VisualReviewOnly"));
            UStaticMeshComponent* MeshComponent = ModuleActor->GetStaticMeshComponent();
            MeshComponent->SetStaticMesh(Module.Mesh);
            MeshComponent->SetMaterial(0, BasaltMaterial);
            MeshComponent->SetMobility(EComponentMobility::Static);
            MeshComponent->SetCollisionEnabled(ECollisionEnabled::NoCollision);
            MeshComponent->SetGenerateOverlapEvents(false);
            MeshComponent->SetCastShadow(true);
        }
        OutSummary += FString::Printf(
            TEXT("Batoka V10 %s: wall_cells=%d talus_rocks=%d vertices=%d triangles=%d "
                 "bounds_cm=(%.1f, %.1f, %.1f) Nanite=true collision=false.\n"),
            *Module.Definition.Id,
            Module.Metrics.WallCellCount,
            Module.Metrics.TalusBlockCount,
            Module.Metrics.VertexCount,
            Module.Metrics.TriangleCount,
            Module.Metrics.Bounds.GetSize().X,
            Module.Metrics.Bounds.GetSize().Y,
            Module.Metrics.Bounds.GetSize().Z);
    }

    UStaticMesh* PlaneMesh = LoadPreviewMesh(TEXT("/Engine/BasicShapes/Plane.Plane"));
    bSceneComplete &= PlaneMesh != nullptr;
    for (const FModuleRuntime& Module : Modules)
    {
        AStaticMeshActor* GroundActor = World->SpawnActor<AStaticMeshActor>(
            AStaticMeshActor::StaticClass(),
            FTransform(
                FRotator::ZeroRotator,
                Module.WorldOffset + FVector(0.0f, 0.0f, -8.0f),
                FVector(90.0f, 90.0f, 1.0f)));
        bSceneComplete &= GroundActor && GroundActor->GetStaticMeshComponent();
        if (GroundActor && GroundActor->GetStaticMeshComponent())
        {
            GroundActor->SetActorLabel(FString::Printf(
                TEXT("RaftSim_ZambeziBatokaBasalt_%s_NeutralGround"),
                *Module.Definition.AssetToken));
            GroundActor->GetStaticMeshComponent()->SetStaticMesh(PlaneMesh);
            GroundActor->GetStaticMeshComponent()->SetMaterial(0, LoadPreviewBaseMaterial());
            GroundActor->GetStaticMeshComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
            GroundActor->GetStaticMeshComponent()->SetCastShadow(false);
        }
    }

    FRaftSimEnvironmentPreviewSpec ReviewSpec;
    ReviewSpec.RiverId = TEXT("zambezi_batoka_gorge");
    ReviewSpec.DisplayName = TEXT("Zambezi Batoka V10 shared morphology and two-scale isolated surface family");
    ReviewSpec.MapPackagePath =
        TEXT("/Game/RaftSim/Environment/GeneratedLocalReview/ZambeziBatokaBasalt/"
             "L_ZambeziBatokaBasalt_V10_IsolatedFamilyReview");
    ReviewSpec.RockColor = FLinearColor(0.18f, 0.19f, 0.19f, 1.0f);
    ReviewSpec.TerrainColor = FLinearColor(0.24f, 0.21f, 0.17f, 1.0f);
    ReviewSpec.FoliageColor = FLinearColor(0.22f, 0.29f, 0.12f, 1.0f);
    AddPreviewLightRig(World, ReviewSpec);
    for (TActorIterator<ASkyLight> It(World); It; ++It)
    {
        if (It->GetLightComponent())
        {
            It->GetLightComponent()->SetIntensity(1.90f);
            It->GetLightComponent()->RecaptureSky();
        }
    }
    ADirectionalLight* FrontFill = World->SpawnActor<ADirectionalLight>(
        ADirectionalLight::StaticClass(),
        FTransform(FRotator(-27.0f, 22.0f, 0.0f)));
    bSceneComplete &= FrontFill && FrontFill->GetLightComponent();
    if (FrontFill && FrontFill->GetLightComponent())
    {
        FrontFill->SetActorLabel(TEXT("RaftSim_ZambeziBatokaBasalt_NeutralFrontFill"));
        FrontFill->GetLightComponent()->SetIntensity(1.35f);
        FrontFill->GetLightComponent()->SetLightColor(FLinearColor(1.0f, 0.93f, 0.84f));
        FrontFill->GetLightComponent()->SetCastShadows(false);
    }
    ADirectionalLight* SideFill = World->SpawnActor<ADirectionalLight>(
        ADirectionalLight::StaticClass(),
        FTransform(FRotator(-31.0f, -118.0f, 0.0f)));
    bSceneComplete &= SideFill && SideFill->GetLightComponent();
    if (SideFill && SideFill->GetLightComponent())
    {
        SideFill->SetActorLabel(TEXT("RaftSim_ZambeziBatokaBasalt_NeutralSideFill"));
        SideFill->GetLightComponent()->SetIntensity(0.65f);
        SideFill->GetLightComponent()->SetLightColor(FLinearColor(0.84f, 0.91f, 1.0f));
        SideFill->GetLightComponent()->SetCastShadows(false);
    }

    const FRaftSimPhotographicCaptureSettings CaptureSettings =
        GetPhotographicCaptureSettings(ReviewSpec.RiverId);
    auto AddReviewCamera = [World, CaptureSettings](
                               const FString& Label,
                               const FVector& Location,
                               const FVector& Target,
                               float FieldOfView)
    {
        ACameraActor* Camera = World->SpawnActor<ACameraActor>(
            ACameraActor::StaticClass(),
            FTransform((Target - Location).Rotation(), Location));
        if (!Camera || !Camera->GetCameraComponent())
        {
            return false;
        }
        Camera->SetActorLabel(Label);
        UCameraComponent* CameraComponent = Camera->GetCameraComponent();
        CameraComponent->FieldOfView = FieldOfView;
        FPostProcessSettings& Settings = CameraComponent->PostProcessSettings;
        Settings.bOverride_AutoExposureMethod = true;
        Settings.AutoExposureMethod = AEM_Manual;
        Settings.bOverride_AutoExposureBias = true;
        Settings.AutoExposureBias = 0.0f;
        Settings.bOverride_AutoExposureApplyPhysicalCameraExposure = true;
        Settings.AutoExposureApplyPhysicalCameraExposure = 0;
        Settings.bOverride_ColorSaturation = true;
        Settings.ColorSaturation = FVector4(
            CaptureSettings.Saturation,
            CaptureSettings.Saturation,
            CaptureSettings.Saturation,
            1.0f);
        Settings.bOverride_ColorContrast = true;
        Settings.ColorContrast = FVector4(
            CaptureSettings.Contrast,
            CaptureSettings.Contrast,
            CaptureSettings.Contrast,
            1.0f);
        Settings.bOverride_Sharpen = true;
        Settings.Sharpen = CaptureSettings.Sharpen;
        Settings.bOverride_FilmGrainIntensity = true;
        Settings.FilmGrainIntensity = 0.0f;
        return true;
    };

    struct FBasaltCaptureRequest
    {
        FString RelativePath;
        FString CameraLabel;
        FString CaptureId;
        FString Description;
        bool bCaptured = false;
    };
    TArray<FBasaltCaptureRequest> CaptureRequests;
    for (const FModuleRuntime& Module : Modules)
    {
        const FVector BoundsCenter = Module.Metrics.Bounds.GetCenter();
        const FVector BoundsSize = Module.Metrics.Bounds.GetSize();
        const FVector MainTarget = Module.WorldOffset + FVector(
            BoundsCenter.X,
            Module.Metrics.Bounds.Min.Y + BoundsSize.Y * 0.34f,
            Module.Metrics.Bounds.Min.Z + BoundsSize.Z * 0.54f);
        const float TurntableDistance = FMath::Max(
            BoundsSize.Z * 2.15f,
            BoundsSize.X * 1.75f);
        const FVector CloseupTarget = Module.WorldOffset + FVector(
            BoundsCenter.X + BoundsSize.X * 0.12f,
            Module.Metrics.Bounds.Min.Y + BoundsSize.Y * 0.42f,
            Module.Metrics.Bounds.Min.Z + BoundsSize.Z * 0.48f);
        struct FViewDefinition
        {
            const TCHAR* Suffix;
            const TCHAR* Description;
            FVector Location;
            FVector Target;
            float FieldOfView;
        };
        const FViewDefinition Views[] = {
            {TEXT("turntable_azimuth_035"), TEXT("turntable azimuth 35"),
             MainTarget + FVector(
                 -TurntableDistance * FMath::Cos(FMath::DegreesToRadians(35.0f)),
                 -TurntableDistance * FMath::Sin(FMath::DegreesToRadians(35.0f)),
                 BoundsSize.Z * 0.10f), MainTarget, 44.0f},
            {TEXT("turntable_azimuth_145"), TEXT("turntable azimuth 145"),
             MainTarget + FVector(
                 -TurntableDistance * FMath::Cos(FMath::DegreesToRadians(145.0f)),
                 -TurntableDistance * FMath::Sin(FMath::DegreesToRadians(145.0f)),
                 BoundsSize.Z * 0.10f), MainTarget, 44.0f},
            {TEXT("joint_flow_break_closeup"), TEXT("joint and flow-break closeup"),
             CloseupTarget + FVector(-900.0f, -1500.0f, 170.0f), CloseupTarget, 35.0f},
            {TEXT("river_distance_60m"), TEXT("60 m river-distance proxy"),
             MainTarget + FVector(-450.0f, -6000.0f, 220.0f), MainTarget, 30.0f}};
        for (const FViewDefinition& View : Views)
        {
            FBasaltCaptureRequest Request;
            Request.CameraLabel = FString::Printf(
                TEXT("RaftSim_ZambeziBatokaBasalt_%s_%s"),
                *Module.Definition.Id,
                View.Suffix);
            Request.CaptureId = Module.Definition.Id + TEXT("_") + View.Suffix;
            Request.RelativePath = FString::Printf(
                TEXT("docs/environment-captures/photoreal_river_previews/landscape_candidates/"
                     "zambezi_batoka_basalt_v10_%s_%s.png"),
                *Module.Definition.Id,
                View.Suffix);
            Request.Description = FString::Printf(
                TEXT("Batoka V10 shared morphology and two-scale CC0 surface study %s %s"),
                *Module.Definition.Id,
                View.Description);
            bSceneComplete &= AddReviewCamera(
                Request.CameraLabel,
                View.Location,
                View.Target,
                View.FieldOfView);
            CaptureRequests.Add(MoveTemp(Request));
        }
    }
    bSceneComplete &= CaptureRequests.Num() == 16;

    FString MapSummary;
    const bool bMapSaved = bSceneComplete &&
        SavePreviewWorld(World, ReviewSpec.MapPackagePath, MapSummary);
    OutSummary += MapSummary;
    bool bCaptured = bMapSaved;
    if (bMapSaved)
    {
        for (FBasaltCaptureRequest& Request : CaptureRequests)
        {
            Request.bCaptured = CapturePreviewImageForSpec(
                ReviewSpec,
                GetRepoRoot(),
                Request.RelativePath,
                Request.CameraLabel,
                Request.CaptureId,
                Request.Description,
                false,
                OutSummary,
                [ExpectedCameraLabel = Request.CameraLabel](
                    UWorld*, ACameraActor* Camera, FString& SetupSummary)
                {
                    const FString ActualLabel = Camera ? Camera->GetActorLabel() : TEXT("");
                    const bool bExactCamera = ActualLabel == ExpectedCameraLabel;
                    if (!bExactCamera)
                    {
                        SetupSummary += FString::Printf(
                            TEXT("Batoka V10 expected camera '%s' but capture selected '%s'.\n"),
                            *ExpectedCameraLabel,
                            *ActualLabel);
                    }
                    return bExactCamera;
                });
            bCaptured &= Request.bCaptured;
        }
    }

    TSharedRef<FJsonObject> ReportObject = MakeShared<FJsonObject>();
    ReportObject->SetStringField(
        TEXT("schema"),
        TEXT("raftsim.unreal.zambezi_batoka_basalt_isolated_family.v10"));
    ReportObject->SetStringField(
        TEXT("status"),
        bCaptured
            ? TEXT("v10_shared_surface_two_scale_cc0_family_captured_pending_human_review")
            : TEXT("v10_shared_surface_two_scale_cc0_family_capture_incomplete"));
    ReportObject->SetBoolField(TEXT("production_promoted"), false);
    ReportObject->SetBoolField(TEXT("corridor_substitution_performed"), false);
    ReportObject->SetBoolField(TEXT("source_map_modified"), false);
    ReportObject->SetBoolField(TEXT("collision_enabled"), false);
    ReportObject->SetBoolField(TEXT("project_owned_geometry"), true);
    ReportObject->SetBoolField(TEXT("external_pixels_copied"), true);
    ReportObject->SetBoolField(TEXT("external_geometry_copied"), false);
    ReportObject->SetNumberField(TEXT("isolated_review_diagnostic_ambient_scale"), 0.028f);
    ReportObject->SetNumberField(TEXT("isolated_review_manual_exposure_bias"), 0.0f);
    ReportObject->SetNumberField(TEXT("isolated_review_skylight_intensity"), 1.90f);
    ReportObject->SetNumberField(TEXT("isolated_review_front_fill_intensity"), 1.35f);
    ReportObject->SetNumberField(TEXT("isolated_review_side_fill_intensity"), 0.65f);
    ReportObject->SetBoolField(TEXT("isolated_review_two_sided_culling_diagnostic"), false);
    ReportObject->SetBoolField(TEXT("front_winding_correction_applied"), true);
    ReportObject->SetBoolField(TEXT("hard_macro_fracture_panel_normals_applied"), false);
    ReportObject->SetBoolField(TEXT("shared_vertex_surface_normals_applied"), true);
    ReportObject->SetBoolField(TEXT("smooth_joint_profiles_applied"), true);
    ReportObject->SetBoolField(TEXT("detached_flow_break_geometry_present"), false);
    ReportObject->SetBoolField(TEXT("rights_reviewed_external_surface_textures"), true);
    ReportObject->SetStringField(
        TEXT("surface_texture_manifest"),
        TEXT("unreal/Content/RaftSim/Environment/ExternalReview/PolyHaven/AerialRocks02_4K/"
             "polyhaven_aerial_rocks_02_source_manifest.json"));
    ReportObject->SetStringField(
        TEXT("surface_texture_import_report"),
        TEXT("docs/environment-captures/photoreal_river_previews/"
             "polyhaven_aerial_rocks_02_batoka_macro_import_report.json"));
    ReportObject->SetStringField(
        TEXT("surface_texture_asset_id"),
        TEXT("polyhaven_aerial_rocks_02_4k"));
    ReportObject->SetStringField(
        TEXT("detail_texture_manifest"),
        TEXT("unreal/Content/RaftSim/Environment/ExternalReview/AmbientCG/Rock037_2K/"
             "ambientcg_rock037_source_manifest.json"));
    ReportObject->SetStringField(
        TEXT("detail_texture_import_report"),
        TEXT("docs/environment-captures/photoreal_river_previews/"
             "ambientcg_rock037_batoka_surface_import_report.json"));
    ReportObject->SetStringField(
        TEXT("detail_texture_asset_id"),
        TEXT("ambientcg_rock037_2k"));
    ReportObject->SetStringField(
        TEXT("batoka_basalt_match"),
        TEXT("not_established_generic_large_scale_natural_rock_analog_only"));
    ReportObject->SetNumberField(TEXT("surface_texture_tile_cm"), 5000.0f);
    ReportObject->SetNumberField(TEXT("detail_texture_tile_cm"), 240.0f);
    TArray<TSharedPtr<FJsonValue>> SurfaceColorBalance;
    SurfaceColorBalance.Add(MakeShared<FJsonValueNumber>(0.78f));
    SurfaceColorBalance.Add(MakeShared<FJsonValueNumber>(0.58f));
    SurfaceColorBalance.Add(MakeShared<FJsonValueNumber>(0.72f));
    ReportObject->SetArrayField(TEXT("surface_color_balance_rgb"), SurfaceColorBalance);
    ReportObject->SetNumberField(TEXT("vertex_tint_weight"), 0.10f);
    ReportObject->SetNumberField(TEXT("detail_color_scale"), 1.18f);
    ReportObject->SetNumberField(TEXT("detail_color_weight"), 0.16f);
    ReportObject->SetNumberField(TEXT("detail_normal_weight"), 0.42f);
    ReportObject->SetNumberField(TEXT("detail_roughness_weight"), 0.28f);
    ReportObject->SetNumberField(TEXT("surface_ao_weight"), 0.32f);
    ReportObject->SetNumberField(TEXT("surface_roughness_texture_weight"), 0.64f);
    ReportObject->SetNumberField(TEXT("surface_roughness_floor"), 0.72f);
    ReportObject->SetNumberField(TEXT("surface_displacement_weathering_tint_weight"), 0.04f);
    ReportObject->SetStringField(TEXT("surface_normal_convention"), TEXT("DirectX"));
    ReportObject->SetStringField(TEXT("map_asset"), ReviewSpec.MapPackagePath);
    ReportObject->SetBoolField(TEXT("map_saved"), bMapSaved);
    ReportObject->SetStringField(
        TEXT("source_manifest"),
        TEXT("unreal/Content/RaftSim/Environment/ProceduralGeology/ZambeziBatokaBasalt/"
             "zambezi_batoka_basalt_authoring_manifest.json"));
    ReportObject->SetStringField(
        TEXT("zra_source"),
        TEXT("https://www.zambezira.org/sites/default/files/BGHES_Project%20Overview%20Document.pdf"));
    ReportObject->SetStringField(
        TEXT("erm_source"),
        TEXT("https://www.erm.com/contentassets/6bdbb76b347f4e9fb9b9c14054806210/annexes/"
             "annex-m---zam-cultural-heritage-report.pdf"));
    ReportObject->SetStringField(
        TEXT("authority_boundary"),
        TEXT("visual morphology review only; no source terrain, centerline, bank, bed, collision, custom C++ water, GeoClaw, feature-forcing, raft-contact, or gameplay authority"));

    TArray<TSharedPtr<FJsonValue>> ModuleValues;
    for (const FModuleRuntime& Module : Modules)
    {
        TSharedRef<FJsonObject> ModuleObject = MakeShared<FJsonObject>();
        ModuleObject->SetStringField(TEXT("id"), Module.Definition.Id);
        ModuleObject->SetStringField(TEXT("display_name"), Module.Definition.DisplayName);
        ModuleObject->SetStringField(TEXT("mesh_asset"), Module.MeshPackagePath);
        ModuleObject->SetNumberField(TEXT("seed"), Module.Definition.Seed);
        ModuleObject->SetNumberField(TEXT("wall_cell_count"), Module.Metrics.WallCellCount);
        ModuleObject->SetNumberField(TEXT("talus_rock_count"), Module.Metrics.TalusBlockCount);
        ModuleObject->SetNumberField(TEXT("source_vertices"), Module.Metrics.VertexCount);
        ModuleObject->SetNumberField(TEXT("source_triangles"), Module.Metrics.TriangleCount);
        ModuleObject->SetNumberField(TEXT("render_vertices"), Module.Mesh->GetNumVertices(0));
        ModuleObject->SetNumberField(TEXT("render_triangles"), Module.Mesh->GetNumTriangles(0));
        ModuleObject->SetBoolField(TEXT("nanite_enabled"), Module.Mesh->IsNaniteEnabled());
        ModuleObject->SetBoolField(TEXT("collision_enabled"), false);
        const FVector BoundsSize = Module.Metrics.Bounds.GetSize();
        TArray<TSharedPtr<FJsonValue>> BoundsValues;
        BoundsValues.Add(MakeShared<FJsonValueNumber>(BoundsSize.X));
        BoundsValues.Add(MakeShared<FJsonValueNumber>(BoundsSize.Y));
        BoundsValues.Add(MakeShared<FJsonValueNumber>(BoundsSize.Z));
        ModuleObject->SetArrayField(TEXT("bounds_size_cm"), BoundsValues);
        ModuleValues.Add(MakeShared<FJsonValueObject>(ModuleObject));
    }
    ReportObject->SetArrayField(TEXT("modules"), ModuleValues);
    ReportObject->SetNumberField(TEXT("module_count"), Modules.Num());

    TArray<TSharedPtr<FJsonValue>> CaptureValues;
    for (const FBasaltCaptureRequest& Request : CaptureRequests)
    {
        TSharedRef<FJsonObject> CaptureObject = MakeShared<FJsonObject>();
        CaptureObject->SetStringField(TEXT("path"), Request.RelativePath);
        CaptureObject->SetStringField(TEXT("camera"), Request.CameraLabel);
        CaptureObject->SetStringField(TEXT("capture_id"), Request.CaptureId);
        CaptureObject->SetStringField(TEXT("description"), Request.Description);
        CaptureObject->SetBoolField(TEXT("captured"), Request.bCaptured);
        CaptureValues.Add(MakeShared<FJsonValueObject>(CaptureObject));
    }
    ReportObject->SetArrayField(TEXT("captures"), CaptureValues);
    ReportObject->SetNumberField(TEXT("capture_count"), CaptureRequests.Num());
    ReportObject->SetStringField(
        TEXT("promotion_boundary"),
        TEXT("human isolated visual acceptance is required before a transient non-colliding corridor comparison; geologist, guide, geospatial, rights, performance, and surveyed gameplay-collision review remain separate later gates"));

    FString SerializedReport;
    const TSharedRef<TJsonWriter<TCHAR, TPrettyJsonPrintPolicy<TCHAR>>> Writer =
        TJsonWriterFactory<TCHAR, TPrettyJsonPrintPolicy<TCHAR>>::Create(&SerializedReport);
    const bool bSerialized = FJsonSerializer::Serialize(ReportObject, Writer);
    SerializedReport += TEXT("\n");
    const FString ReportPath = FPaths::Combine(
        GetRepoRoot(),
        TEXT("docs/environment-captures/photoreal_river_previews/landscape_candidates/"
             "zambezi_batoka_basalt_v10_isolated_family_report.json"));
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(ReportPath), true);
    const bool bReportSaved = bSerialized &&
        FFileHelper::SaveStringToFile(SerializedReport, *ReportPath);
    OutSummary += FString::Printf(
        TEXT("%s Batoka basalt V10 isolated family report -> %s\n"),
        bReportSaved ? TEXT("Saved") : TEXT("Failed to save"),
        *ReportPath);
    return bCaptured && bReportSaved;
}

bool FRaftSimEditorModule::CaptureZambeziCliffComparison(FString& OutSummary)
{
    const FRaftSimLandscapeImportCandidateSpec* ZambeziCandidate = nullptr;
    const TArray<FRaftSimLandscapeImportCandidateSpec> Candidates = GetLandscapeImportCandidateSpecs();
    for (const FRaftSimLandscapeImportCandidateSpec& Candidate : Candidates)
    {
        if (Candidate.PreviewSpec.RiverId == TEXT("zambezi_batoka_gorge"))
        {
            ZambeziCandidate = &Candidate;
            break;
        }
    }
    if (!ZambeziCandidate)
    {
        OutSummary += TEXT("The Zambezi physical-corridor candidate is not registered.\n");
        return false;
    }

    const FString CliffAssetPath =
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/NamaqualandCliff02_2K/"
             "SM_NamaqualandCliff02.SM_NamaqualandCliff02");
    UStaticMesh* CliffMesh = LoadObject<UStaticMesh>(nullptr, *CliffAssetPath);
    if (!CliffMesh)
    {
        OutSummary += FString::Printf(TEXT("Missing reviewed Zambezi cliff mesh %s.\n"), *CliffAssetPath);
        return false;
    }
    const FVector CliffDimensionsCm =
        GetZambeziCliffComparisonEffectiveBounds(CliffMesh).GetSize();
    UMaterialInterface* CliffMaterial = CliffMesh->GetMaterial(0);
    const bool bAssetValidated =
        CliffMesh->IsNaniteEnabled() &&
        CliffDimensionsCm.X >= 1900.0f && CliffDimensionsCm.X <= 2150.0f &&
        CliffDimensionsCm.Y >= 550.0f && CliffDimensionsCm.Y <= 760.0f &&
        CliffDimensionsCm.Z >= 600.0f && CliffDimensionsCm.Z <= 820.0f &&
        CliffMaterial &&
        CliffMaterial->GetPathName().Contains(TEXT("M_NamaqualandCliff02_ReviewLit"));
    if (!bAssetValidated)
    {
        OutSummary += FString::Printf(
            TEXT("Reviewed cliff validation failed: Nanite=%d dimensions=(%.2f, %.2f, %.2f) material=%s.\n"),
            CliffMesh->IsNaniteEnabled(),
            CliffDimensionsCm.X,
            CliffDimensionsCm.Y,
            CliffDimensionsCm.Z,
            CliffMaterial ? *CliffMaterial->GetPathName() : TEXT("<null>"));
        return false;
    }

    const FString CaptureRelativeRoot =
        TEXT("docs/environment-captures/photoreal_river_previews/landscape_candidates");
    const FString CaptureRoot = FPaths::Combine(GetRepoRoot(), CaptureRelativeRoot);
    IFileManager::Get().MakeDirectory(*CaptureRoot, true);
    FString BaselineGuidePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("zambezi_batoka_gorge_pre_namaqualand_cliff_review_guide_seat_downstream.png"));
    FString BaselineRiverEyePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("zambezi_batoka_gorge_pre_namaqualand_cliff_review_river_eye_downstream.png"));
    FString ComparisonGuidePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("zambezi_batoka_gorge_namaqualand_cliff_review_guide_seat_downstream.png"));
    FString ComparisonRiverEyePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("zambezi_batoka_gorge_namaqualand_cliff_review_river_eye_downstream.png"));

    const bool bBaselineGuideCaptured = CapturePreviewImageForSpec(
        ZambeziCandidate->PreviewSpec,
        CaptureRoot,
        BaselineGuidePath,
        TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"),
        TEXT("pre_namaqualand_cliff_review_guide_seat_downstream"),
        TEXT("Zambezi baseline guide-seat cliff comparison"),
        true,
        OutSummary);
    const bool bBaselineRiverEyeCaptured = CapturePreviewImageForSpec(
        ZambeziCandidate->PreviewSpec,
        CaptureRoot,
        BaselineRiverEyePath,
        TEXT("RaftSim_RiverEye_DownstreamCaptureCamera"),
        TEXT("pre_namaqualand_cliff_review_river_eye_downstream"),
        TEXT("Zambezi baseline river-eye cliff comparison"),
        true,
        OutSummary);

    TArray<FZambeziCliffComparisonPlacement> GuidePlacements;
    TArray<FZambeziCliffComparisonPlacement> RiverEyePlacements;
    auto MakeWorldSetup = [CliffMesh](TArray<FZambeziCliffComparisonPlacement>& Placements)
    {
        return [CliffMesh, &Placements](UWorld* World, ACameraActor* Camera, FString& Summary)
        {
            return AddZambeziCliffComparisonInstances(
                World,
                Camera,
                CliffMesh,
                Placements,
                Summary);
        };
    };
    const bool bComparisonGuideCaptured = CapturePreviewImageForSpec(
        ZambeziCandidate->PreviewSpec,
        CaptureRoot,
        ComparisonGuidePath,
        TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"),
        TEXT("namaqualand_cliff_review_guide_seat_downstream"),
        TEXT("Zambezi guide-seat Namaqualand cliff analog comparison"),
        true,
        OutSummary,
        MakeWorldSetup(GuidePlacements));
    const bool bComparisonRiverEyeCaptured = CapturePreviewImageForSpec(
        ZambeziCandidate->PreviewSpec,
        CaptureRoot,
        ComparisonRiverEyePath,
        TEXT("RaftSim_RiverEye_DownstreamCaptureCamera"),
        TEXT("namaqualand_cliff_review_river_eye_downstream"),
        TEXT("Zambezi river-eye Namaqualand cliff analog comparison"),
        true,
        OutSummary,
        MakeWorldSetup(RiverEyePlacements));
    const bool bAllCaptured =
        bBaselineGuideCaptured && bBaselineRiverEyeCaptured &&
        bComparisonGuideCaptured && bComparisonRiverEyeCaptured;

    auto MakeVectorArray = [](const FVector& Value)
    {
        TArray<TSharedPtr<FJsonValue>> Values;
        Values.Add(MakeShared<FJsonValueNumber>(Value.X));
        Values.Add(MakeShared<FJsonValueNumber>(Value.Y));
        Values.Add(MakeShared<FJsonValueNumber>(Value.Z));
        return Values;
    };
    auto MakePlacementArray = [&MakeVectorArray](
                                  const TArray<FZambeziCliffComparisonPlacement>& Placements)
    {
        TArray<TSharedPtr<FJsonValue>> Values;
        for (int32 Index = 0; Index < Placements.Num(); ++Index)
        {
            const FZambeziCliffComparisonPlacement& Placement = Placements[Index];
            TSharedRef<FJsonObject> PlacementObject = MakeShared<FJsonObject>();
            PlacementObject->SetNumberField(TEXT("instance_index"), Index);
            PlacementObject->SetArrayField(TEXT("location_cm"), MakeVectorArray(Placement.Location));
            PlacementObject->SetArrayField(
                TEXT("rotation_degrees"),
                MakeVectorArray(FVector(
                    Placement.Rotation.Roll,
                    Placement.Rotation.Pitch,
                    Placement.Rotation.Yaw)));
            PlacementObject->SetArrayField(TEXT("scale"), MakeVectorArray(Placement.Scale));
            Values.Add(MakeShared<FJsonValueObject>(PlacementObject));
        }
        return Values;
    };

    TSharedRef<FJsonObject> Report = MakeShared<FJsonObject>();
    Report->SetStringField(
        TEXT("schema"), TEXT("raftsim.unreal.zambezi_cliff_corridor_comparison.v1"));
    Report->SetStringField(TEXT("river_id"), TEXT("zambezi_batoka_gorge"));
    Report->SetStringField(
        TEXT("status"),
        bAllCaptured
            ? TEXT("paired_transient_corridor_comparison_captured_pending_human_review")
            : TEXT("one_or_more_comparison_captures_failed"));
    Report->SetBoolField(TEXT("production_promoted"), false);
    Report->SetBoolField(TEXT("corridor_substitution_performed"), false);
    Report->SetStringField(TEXT("source_map"), ZambeziCandidate->PreviewSpec.MapPackagePath);
    Report->SetStringField(TEXT("asset"), CliffAssetPath);
    Report->SetStringField(
        TEXT("source_manifest"),
        TEXT("unreal/Content/RaftSim/Environment/ExternalReview/PolyHaven/"
             "NamaqualandCliff02_2K/polyhaven_namaqualand_cliff_02_source_manifest.json"));
    Report->SetStringField(
        TEXT("geology_boundary"),
        TEXT("South African weathered-cliff structure analog only; not Batoka basalt, surveyed gorge, collision, or gameplay authority"));
    Report->SetArrayField(TEXT("mesh_dimensions_cm"), MakeVectorArray(CliffDimensionsCm));
    Report->SetBoolField(TEXT("nanite_enabled"), CliffMesh->IsNaniteEnabled());
    Report->SetStringField(TEXT("material"), CliffMaterial->GetPathName());
    Report->SetNumberField(TEXT("instances_per_capture"), GuidePlacements.Num());
    Report->SetArrayField(TEXT("guide_seat_placements"), MakePlacementArray(GuidePlacements));
    Report->SetArrayField(TEXT("river_eye_placements"), MakePlacementArray(RiverEyePlacements));

    TSharedRef<FJsonObject> Captures = MakeShared<FJsonObject>();
    Captures->SetStringField(TEXT("baseline_guide_seat"), BaselineGuidePath);
    Captures->SetStringField(TEXT("baseline_river_eye"), BaselineRiverEyePath);
    Captures->SetStringField(TEXT("comparison_guide_seat"), ComparisonGuidePath);
    Captures->SetStringField(TEXT("comparison_river_eye"), ComparisonRiverEyePath);
    Captures->SetBoolField(TEXT("all_captured"), bAllCaptured);
    Report->SetObjectField(TEXT("captures"), Captures);

    TArray<TSharedPtr<FJsonValue>> PromotionGates;
    for (const TCHAR* Gate : {
             TEXT("paired_human_visual_review"),
             TEXT("Batoka_geology_review"),
             TEXT("guide_and_hazard_readability_review"),
             TEXT("repetition_and_silhouette_review"),
             TEXT("desktop_and_VR_corridor_performance"),
             TEXT("rights_and_attribution_audit")})
    {
        PromotionGates.Add(MakeShared<FJsonValueString>(Gate));
    }
    Report->SetArrayField(TEXT("open_promotion_gates"), PromotionGates);

    FString SerializedReport;
    const TSharedRef<TJsonWriter<TCHAR, TPrettyJsonPrintPolicy<TCHAR>>> Writer =
        TJsonWriterFactory<TCHAR, TPrettyJsonPrintPolicy<TCHAR>>::Create(&SerializedReport);
    const bool bSerialized = FJsonSerializer::Serialize(Report, Writer);
    SerializedReport += TEXT("\n");
    const FString ReportRelativePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("polyhaven_namaqualand_cliff_02_corridor_comparison_report.json"));
    const FString ReportPath = FPaths::Combine(GetRepoRoot(), ReportRelativePath);
    const bool bReportSaved =
        bSerialized && FFileHelper::SaveStringToFile(SerializedReport, *ReportPath);
    OutSummary += FString::Printf(
        TEXT("%s Zambezi cliff corridor comparison report -> %s\n"),
        bReportSaved ? TEXT("Saved") : TEXT("Failed to save"),
        *ReportPath);
    return bAllCaptured && bReportSaved;
}

bool FRaftSimEditorModule::CaptureZambeziBatokaBasaltCorridorComparison(
    FString& OutSummary)
{
    const FRaftSimLandscapeImportCandidateSpec* ZambeziCandidate = nullptr;
    const TArray<FRaftSimLandscapeImportCandidateSpec> Candidates =
        GetLandscapeImportCandidateSpecs();
    for (const FRaftSimLandscapeImportCandidateSpec& Candidate : Candidates)
    {
        if (Candidate.PreviewSpec.RiverId == TEXT("zambezi_batoka_gorge"))
        {
            ZambeziCandidate = &Candidate;
            break;
        }
    }
    if (!ZambeziCandidate)
    {
        OutSummary += TEXT("The Zambezi physical-corridor candidate is not registered.\n");
        return false;
    }

    static const FString MeshRoot =
        TEXT("/Game/RaftSim/Environment/ProceduralGeology/ZambeziBatokaBasalt/Meshes/");
    const TCHAR* AssetTokens[] = {
        TEXT("LowerMassiveScarp"),
        TEXT("JointedMidScarp"),
        TEXT("IrregularBrecciatedUpper"),
        TEXT("TalusLedgedSpur")};
    TArray<UStaticMesh*> ModuleMeshes;
    TArray<TSharedPtr<FJsonValue>> ModuleAssets;
    for (const TCHAR* AssetToken : AssetTokens)
    {
        const FString PackagePath = MeshRoot + FString::Printf(
            TEXT("SM_RaftSim_ZambeziBatokaBasalt_%s_V10"),
            AssetToken);
        const FString ObjectPath = FString::Printf(
            TEXT("%s.SM_RaftSim_ZambeziBatokaBasalt_%s_V10"),
            *PackagePath,
            AssetToken);
        UStaticMesh* ModuleMesh = LoadObject<UStaticMesh>(nullptr, *ObjectPath);
        UMaterialInterface* Material = ModuleMesh ? ModuleMesh->GetMaterial(0) : nullptr;
        const bool bValid =
            ModuleMesh &&
            ModuleMesh->IsNaniteEnabled() &&
            Material &&
            Material->GetPathName().Contains(TEXT("V10_TwoScaleReview"));
        if (!bValid)
        {
            OutSummary += FString::Printf(
                TEXT("Batoka V10 corridor comparison could not validate module %s.\n"),
                *ObjectPath);
            return false;
        }
        ModuleMeshes.Add(ModuleMesh);
        ModuleAssets.Add(MakeShared<FJsonValueString>(ObjectPath));
    }

    const FString CaptureRelativeRoot =
        TEXT("docs/environment-captures/photoreal_river_previews/landscape_candidates");
    const FString CaptureRoot = FPaths::Combine(GetRepoRoot(), CaptureRelativeRoot);
    IFileManager::Get().MakeDirectory(*CaptureRoot, true);
    FString BaselineGuidePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("zambezi_batoka_v10_c2_pre_comparison_guide_seat_downstream.png"));
    FString BaselineRiverEyePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("zambezi_batoka_v10_c2_pre_comparison_river_eye_downstream.png"));
    FString ComparisonGuidePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("zambezi_batoka_v10_c2_transient_comparison_guide_seat_downstream.png"));
    FString ComparisonRiverEyePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("zambezi_batoka_v10_c2_transient_comparison_river_eye_downstream.png"));

    const bool bBaselineGuideCaptured = CapturePreviewImageForSpec(
        ZambeziCandidate->PreviewSpec,
        CaptureRoot,
        BaselineGuidePath,
        TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"),
        TEXT("pre_batoka_v10_comparison_guide_seat_downstream"),
        TEXT("Zambezi untouched baseline guide-seat Batoka V10 comparison"),
        true,
        OutSummary);
    const bool bBaselineRiverEyeCaptured = CapturePreviewImageForSpec(
        ZambeziCandidate->PreviewSpec,
        CaptureRoot,
        BaselineRiverEyePath,
        TEXT("RaftSim_RiverEye_DownstreamCaptureCamera"),
        TEXT("pre_batoka_v10_comparison_river_eye_downstream"),
        TEXT("Zambezi untouched baseline river-eye Batoka V10 comparison"),
        true,
        OutSummary);

    TArray<FZambeziBatokaCorridorPlacement> GuidePlacements;
    TArray<FZambeziBatokaCorridorPlacement> RiverEyePlacements;
    auto MakeWorldSetup = [&ModuleMeshes](
                              TArray<FZambeziBatokaCorridorPlacement>& Placements)
    {
        return [&ModuleMeshes, &Placements](
                   UWorld* World,
                   ACameraActor* Camera,
                   FString& Summary)
        {
            return AddZambeziBatokaBasaltCorridorComparisonInstances(
                World,
                Camera,
                ModuleMeshes,
                Placements,
                Summary);
        };
    };
    const bool bComparisonGuideCaptured = CapturePreviewImageForSpec(
        ZambeziCandidate->PreviewSpec,
        CaptureRoot,
        ComparisonGuidePath,
        TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"),
        TEXT("batoka_v10_transient_comparison_guide_seat_downstream"),
        TEXT("Zambezi guide-seat transient non-colliding Batoka V10 comparison"),
        true,
        OutSummary,
        MakeWorldSetup(GuidePlacements));
    const bool bComparisonRiverEyeCaptured = CapturePreviewImageForSpec(
        ZambeziCandidate->PreviewSpec,
        CaptureRoot,
        ComparisonRiverEyePath,
        TEXT("RaftSim_RiverEye_DownstreamCaptureCamera"),
        TEXT("batoka_v10_transient_comparison_river_eye_downstream"),
        TEXT("Zambezi river-eye transient non-colliding Batoka V10 comparison"),
        true,
        OutSummary,
        MakeWorldSetup(RiverEyePlacements));
    const bool bAllCaptured =
        bBaselineGuideCaptured && bBaselineRiverEyeCaptured &&
        bComparisonGuideCaptured && bComparisonRiverEyeCaptured;

    auto MakeVectorArray = [](const FVector& Value)
    {
        TArray<TSharedPtr<FJsonValue>> Values;
        Values.Add(MakeShared<FJsonValueNumber>(Value.X));
        Values.Add(MakeShared<FJsonValueNumber>(Value.Y));
        Values.Add(MakeShared<FJsonValueNumber>(Value.Z));
        return Values;
    };
    auto MakePlacementArray = [&MakeVectorArray](
                                  const TArray<FZambeziBatokaCorridorPlacement>& Placements)
    {
        TArray<TSharedPtr<FJsonValue>> Values;
        for (int32 Index = 0; Index < Placements.Num(); ++Index)
        {
            const FZambeziBatokaCorridorPlacement& Placement = Placements[Index];
            TSharedRef<FJsonObject> PlacementObject = MakeShared<FJsonObject>();
            PlacementObject->SetNumberField(TEXT("instance_index"), Index);
            PlacementObject->SetStringField(TEXT("module_asset"), Placement.ModuleAsset);
            PlacementObject->SetArrayField(TEXT("location_cm"), MakeVectorArray(Placement.Location));
            PlacementObject->SetArrayField(
                TEXT("rotation_degrees"),
                MakeVectorArray(FVector(
                    Placement.Rotation.Roll,
                    Placement.Rotation.Pitch,
                    Placement.Rotation.Yaw)));
            PlacementObject->SetArrayField(TEXT("scale"), MakeVectorArray(Placement.Scale));
            Values.Add(MakeShared<FJsonValueObject>(PlacementObject));
        }
        return Values;
    };

    TSharedRef<FJsonObject> Report = MakeShared<FJsonObject>();
    Report->SetStringField(
        TEXT("schema"),
        TEXT("raftsim.unreal.zambezi_batoka_basalt_corridor_comparison.v2"));
    Report->SetStringField(TEXT("river_id"), TEXT("zambezi_batoka_gorge"));
    Report->SetStringField(
        TEXT("status"),
        bAllCaptured
            ? TEXT("paired_gorge_scale_slope_aligned_v10_corridor_comparison_captured_pending_human_review")
            : TEXT("one_or_more_v10_corridor_comparison_captures_failed"));
    Report->SetBoolField(TEXT("production_promoted"), false);
    Report->SetBoolField(TEXT("corridor_substitution_performed"), false);
    Report->SetBoolField(TEXT("source_map_modified"), false);
    Report->SetBoolField(TEXT("collision_or_gameplay_authority_modified"), false);
    Report->SetBoolField(TEXT("external_pixels_copied"), true);
    Report->SetBoolField(TEXT("external_geometry_copied"), false);
    Report->SetStringField(TEXT("source_map"), ZambeziCandidate->PreviewSpec.MapPackagePath);
    Report->SetArrayField(TEXT("module_assets"), ModuleAssets);
    Report->SetStringField(
        TEXT("isolated_family_report"),
        TEXT("docs/environment-captures/photoreal_river_previews/landscape_candidates/"
             "zambezi_batoka_basalt_v10_isolated_family_report.json"));
    Report->SetStringField(
        TEXT("isolated_visual_review"),
        TEXT("docs/environment-captures/photoreal_river_previews/landscape_candidates/"
             "zambezi_batoka_basalt_v10_visual_review.json"));
    Report->SetStringField(
        TEXT("rejected_namaqualand_control_report"),
        TEXT("docs/environment-captures/photoreal_river_previews/landscape_candidates/"
             "polyhaven_namaqualand_cliff_02_corridor_comparison_report.json"));
    Report->SetStringField(
        TEXT("authority_boundary"),
        TEXT("transient visual comparison only; source map, Landscape, centerline, bank, bed, collision, custom C++ water, GeoClaw, feature forcing, raft contact, hazards, and gameplay authority remain unchanged"));
    Report->SetNumberField(TEXT("instances_per_capture"), GuidePlacements.Num());
    Report->SetStringField(
        TEXT("placement_revision"),
        TEXT("C2 scales 30 m isolated modules to 84-132 m gorge scarps, aligns each front plane to the sampled Landscape slope, and buries the base by 10 m; all actors remain transient and non-colliding"));
    Report->SetStringField(
        TEXT("rejected_c1_report"),
        TEXT("docs/environment-captures/photoreal_river_previews/landscape_candidates/"
             "zambezi_batoka_basalt_v10_corridor_comparison_report.json"));
    Report->SetArrayField(TEXT("guide_seat_placements"), MakePlacementArray(GuidePlacements));
    Report->SetArrayField(TEXT("river_eye_placements"), MakePlacementArray(RiverEyePlacements));

    TSharedRef<FJsonObject> Captures = MakeShared<FJsonObject>();
    Captures->SetStringField(TEXT("baseline_guide_seat"), BaselineGuidePath);
    Captures->SetStringField(TEXT("baseline_river_eye"), BaselineRiverEyePath);
    Captures->SetStringField(TEXT("comparison_guide_seat"), ComparisonGuidePath);
    Captures->SetStringField(TEXT("comparison_river_eye"), ComparisonRiverEyePath);
    Captures->SetBoolField(TEXT("all_captured"), bAllCaptured);
    Report->SetObjectField(TEXT("captures"), Captures);

    TArray<TSharedPtr<FJsonValue>> OpenGates;
    for (const TCHAR* Gate : {
             TEXT("paired_human_visual_review"),
             TEXT("module_perimeter_and_pasted_fragment_review"),
             TEXT("Batoka_geology_and_reach_specific_lithology_review"),
             TEXT("guide_and_hazard_readability_review"),
             TEXT("geospatial_and_source_terrain_review"),
             TEXT("rights_and_art_review"),
             TEXT("repetition_and_talus_review"),
             TEXT("desktop_console_handheld_and_VR_performance"),
             TEXT("separate_surveyed_collision_and_hydrodynamic_review")})
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
        TEXT("zambezi_batoka_basalt_v10_c2_corridor_comparison_report.json"));
    const FString ReportPath = FPaths::Combine(GetRepoRoot(), ReportRelativePath);
    const bool bReportSaved =
        bSerialized && FFileHelper::SaveStringToFile(SerializedReport, *ReportPath);
    OutSummary += FString::Printf(
        TEXT("%s Batoka V10 C2 transient corridor comparison report -> %s\n"),
        bReportSaved ? TEXT("Saved") : TEXT("Failed to save"),
        *ReportPath);
    return bAllCaptured && bReportSaved;
}

struct FZambeziBatokaVisualMorphologyStats
{
    int32 VisualTileCount = 0;
    int64 TotalVertexCount = 0;
    int64 ModifiedVertexCount = 0;
    int64 ProtectedRiverCorridorVertexCount = 0;
    int64 RejectedLowSlopeVertexCount = 0;
    double AbsoluteOffsetSumCm = 0.0;
    float MinimumOffsetCm = TNumericLimits<float>::Max();
    float MaximumOffsetCm = TNumericLimits<float>::Lowest();
};

bool ApplyZambeziBatokaVisualTerrainTreatment(
    UWorld* World,
    UMaterialInterface* TerrainReviewMaterial,
    const FRaftSimLandscapeImportCandidateSpec& Candidate,
    bool bApplyVisualMorphology,
    FZambeziBatokaVisualMorphologyStats* OutStats,
    FString& OutSummary)
{
    if (!World || !TerrainReviewMaterial)
    {
        return false;
    }

    FZambeziBatokaVisualMorphologyStats LocalStats;
    TArray<FVector2D> CenterlineWorldPoints;
    if (bApplyVisualMorphology)
    {
        TArray<FRaftSimLandscapeCandidateCenterlinePoint> Centerline;
        if (!LoadLandscapeCandidateLocalCenterline(Candidate, Centerline, OutSummary))
        {
            return false;
        }
        for (int32 Index = 0; Index < Centerline.Num(); Index += 2)
        {
            const float Progress = Centerline.Num() > 1
                ? static_cast<float>(Index) / static_cast<float>(Centerline.Num() - 1)
                : 0.0f;
            CenterlineWorldPoints.Add(
                SampleLandscapeCandidateCenterlineWorld(Candidate, Centerline, Progress));
        }
        if (CenterlineWorldPoints.IsEmpty() ||
            !CenterlineWorldPoints.Last().Equals(
                SampleLandscapeCandidateCenterlineWorld(Candidate, Centerline, 1.0f),
                1.0f))
        {
            CenterlineWorldPoints.Add(
                SampleLandscapeCandidateCenterlineWorld(Candidate, Centerline, 1.0f));
        }
    }

    static const FString DenseTerrainActorPrefix =
        TEXT("RaftSim_PhysicalCorridorDenseSourceTerrainTile_");
    for (TActorIterator<AActor> It(World); It; ++It)
    {
        AActor* Actor = *It;
        if (!Actor || !Actor->GetActorLabel().StartsWith(DenseTerrainActorPrefix))
        {
            continue;
        }
        UProceduralMeshComponent* MeshComponent =
            Actor->FindComponentByClass<UProceduralMeshComponent>();
        if (!MeshComponent)
        {
            continue;
        }
        MeshComponent->SetMaterial(0, TerrainReviewMaterial);
        ++LocalStats.VisualTileCount;
        if (!bApplyVisualMorphology)
        {
            continue;
        }

        FProcMeshSection* Section = MeshComponent->GetProcMeshSection(0);
        if (!Section || Section->ProcVertexBuffer.IsEmpty() ||
            Section->ProcIndexBuffer.IsEmpty() || Section->bEnableCollision)
        {
            OutSummary += FString::Printf(
                TEXT("Batoka V13 refused to condition invalid or collision-enabled visual tile %s.\n"),
                *Actor->GetActorLabel());
            return false;
        }

        TArray<FVector> Vertices;
        TArray<int32> Triangles;
        Vertices.Reserve(Section->ProcVertexBuffer.Num());
        Triangles.Reserve(Section->ProcIndexBuffer.Num());
        for (const FProcMeshVertex& Vertex : Section->ProcVertexBuffer)
        {
            Vertices.Add(FVector(Vertex.Position));
        }
        for (const uint32 Index : Section->ProcIndexBuffer)
        {
            Triangles.Add(static_cast<int32>(Index));
        }
        const TArray<FVector> SourceNormals = ComputePreviewMeshNormals(Vertices, Triangles);
        const FTransform ActorTransform = Actor->GetActorTransform();
        for (int32 VertexIndex = 0; VertexIndex < Vertices.Num(); ++VertexIndex)
        {
            ++LocalStats.TotalVertexCount;
            const FVector WorldPosition = ActorTransform.TransformPosition(Vertices[VertexIndex]);
            float MinimumCenterlineDistanceSquared = TNumericLimits<float>::Max();
            for (const FVector2D& CenterlinePoint : CenterlineWorldPoints)
            {
                MinimumCenterlineDistanceSquared = FMath::Min(
                    MinimumCenterlineDistanceSquared,
                    FVector2D::DistSquared(
                        FVector2D(WorldPosition.X, WorldPosition.Y),
                        CenterlinePoint));
            }
            const float CenterlineDistanceCm = FMath::Sqrt(MinimumCenterlineDistanceSquared);
            const float RiverProtectionFade = SmoothPreviewStep(
                22000.0f,
                65000.0f,
                CenterlineDistanceCm);
            if (RiverProtectionFade <= KINDA_SMALL_NUMBER)
            {
                ++LocalStats.ProtectedRiverCorridorVertexCount;
                continue;
            }

            const float Steepness = 1.0f - FMath::Clamp(
                SourceNormals[VertexIndex].Z,
                0.0f,
                1.0f);
            const float ScarpMask = SmoothPreviewStep(0.12f, 0.62f, Steepness);
            const float TalusMask =
                SmoothPreviewStep(0.08f, 0.30f, Steepness) *
                (1.0f - SmoothPreviewStep(0.55f, 0.78f, Steepness));
            if (ScarpMask <= KINDA_SMALL_NUMBER && TalusMask <= KINDA_SMALL_NUMBER)
            {
                ++LocalStats.RejectedLowSlopeVertexCount;
                continue;
            }

            const FVector2D BroadCoordinates(
                WorldPosition.X * 0.000018f,
                WorldPosition.Y * 0.000018f);
            const float BroadVariation = FMath::PerlinNoise2D(BroadCoordinates);
            const float LayerHeightCm = 1100.0f + BroadVariation * 260.0f;
            const float LayerPhaseCm = FMath::PerlinNoise2D(
                FVector2D(
                    WorldPosition.X * 0.000043f + 19.0f,
                    WorldPosition.Y * 0.000043f - 7.0f)) *
                360.0f;
            const float LayerCoordinate =
                (WorldPosition.Z + LayerPhaseCm) / LayerHeightCm;
            const float LayerFloor = FMath::FloorToFloat(LayerCoordinate);
            const float LayerFraction = LayerCoordinate - LayerFloor;
            const float ConditionedLayerFraction = SmoothPreviewStep(
                0.28f,
                0.72f,
                LayerFraction);
            const float TerracedWorldZ =
                (LayerFloor + ConditionedLayerFraction) * LayerHeightCm - LayerPhaseCm;
            const float TerraceOffsetCm =
                (TerracedWorldZ - WorldPosition.Z) * 0.82f;

            const float JointNoise = FMath::PerlinNoise2D(
                FVector2D(
                    WorldPosition.X * 0.000031f - 5.0f,
                    WorldPosition.Y * 0.000031f + 13.0f));
            const float PrimaryJointCoordinate =
                (WorldPosition.X * 0.78f + WorldPosition.Y * 0.62f) / 9200.0f +
                JointNoise * 0.62f;
            const float PrimaryJointFraction =
                PrimaryJointCoordinate - FMath::FloorToFloat(PrimaryJointCoordinate);
            const float PrimaryJointDistance = FMath::Min(
                PrimaryJointFraction,
                1.0f - PrimaryJointFraction);
            const float PrimaryJointMask =
                1.0f - SmoothPreviewStep(0.015f, 0.085f, PrimaryJointDistance);
            const float SecondaryJointCoordinate =
                (WorldPosition.X * -0.44f + WorldPosition.Y * 0.90f) / 14800.0f -
                JointNoise * 0.38f;
            const float SecondaryJointFraction =
                SecondaryJointCoordinate - FMath::FloorToFloat(SecondaryJointCoordinate);
            const float SecondaryJointDistance = FMath::Min(
                SecondaryJointFraction,
                1.0f - SecondaryJointFraction);
            const float SecondaryJointMask =
                1.0f - SmoothPreviewStep(0.01f, 0.055f, SecondaryJointDistance);
            const float JointRecessCm =
                -(PrimaryJointMask * 120.0f + SecondaryJointMask * 65.0f);

            const float TalusBroad = FMath::PerlinNoise2D(
                FVector2D(
                    WorldPosition.X * 0.00012f + 31.0f,
                    WorldPosition.Y * 0.00012f - 23.0f));
            const float TalusFine = FMath::PerlinNoise2D(
                FVector2D(
                    WorldPosition.X * 0.00038f - 17.0f,
                    WorldPosition.Y * 0.00038f + 29.0f));
            const float TalusOffsetCm =
                (TalusBroad * 92.0f + TalusFine * 46.0f) * TalusMask;
            const float OffsetCm = FMath::Clamp(
                RiverProtectionFade *
                    (ScarpMask * (TerraceOffsetCm + JointRecessCm) + TalusOffsetCm),
                -450.0f,
                450.0f);
            if (FMath::Abs(OffsetCm) <= 0.5f)
            {
                continue;
            }

            const FVector LocalOffset = ActorTransform.InverseTransformVectorNoScale(
                FVector(0.0f, 0.0f, OffsetCm));
            Vertices[VertexIndex] += LocalOffset;
            ++LocalStats.ModifiedVertexCount;
            LocalStats.AbsoluteOffsetSumCm += FMath::Abs(OffsetCm);
            LocalStats.MinimumOffsetCm = FMath::Min(LocalStats.MinimumOffsetCm, OffsetCm);
            LocalStats.MaximumOffsetCm = FMath::Max(LocalStats.MaximumOffsetCm, OffsetCm);
        }

        const TArray<FVector> ConditionedNormals = ComputePreviewMeshNormals(
            Vertices,
            Triangles);
        MeshComponent->UpdateMeshSection(
            0,
            Vertices,
            ConditionedNormals,
            TArray<FVector2D>(),
            TArray<FColor>(),
            TArray<FProcMeshTangent>());
    }

    if (OutStats)
    {
        *OutStats = LocalStats;
    }
    OutSummary += FString::Printf(
        TEXT("Applied the transient Batoka %s treatment to %d dense visual-terrain tiles; collision and source Landscape were not changed.\n"),
        bApplyVisualMorphology ? TEXT("V13 morphology plus V12 world-aligned material")
                               : TEXT("V12 world-aligned material"),
        LocalStats.VisualTileCount);
    return LocalStats.VisualTileCount == 4;
}

bool CaptureZambeziBatokaTerrainComparisonInternal(
    bool bWorldAligned,
    FString& OutSummary)
{
    const FRaftSimLandscapeImportCandidateSpec* ZambeziCandidate = nullptr;
    const TArray<FRaftSimLandscapeImportCandidateSpec> Candidates =
        GetLandscapeImportCandidateSpecs();
    for (const FRaftSimLandscapeImportCandidateSpec& Candidate : Candidates)
    {
        if (Candidate.PreviewSpec.RiverId == TEXT("zambezi_batoka_gorge"))
        {
            ZambeziCandidate = &Candidate;
            break;
        }
    }
    if (!ZambeziCandidate)
    {
        OutSummary += TEXT("The Zambezi physical-corridor candidate is not registered.\n");
        return false;
    }

    UMaterialInterface* TerrainReviewMaterial =
        LoadOrCreatePhysicalSourceTerrainRenderMaterial(
            *ZambeziCandidate,
            true,
            bWorldAligned);
    if (!TerrainReviewMaterial)
    {
        OutSummary += FString::Printf(
            TEXT("Could not create the Batoka %s terrain-integrated review material.\n"),
            bWorldAligned ? TEXT("V12 world-aligned") : TEXT("V11 top-down"));
        return false;
    }

    const FString CaptureRelativeRoot =
        TEXT("docs/environment-captures/photoreal_river_previews/landscape_candidates");
    const FString CaptureRoot = FPaths::Combine(GetRepoRoot(), CaptureRelativeRoot);
    IFileManager::Get().MakeDirectory(*CaptureRoot, true);
    FString BaselineGuidePath = FPaths::Combine(
        CaptureRelativeRoot,
        bWorldAligned
            ? TEXT("zambezi_batoka_v12_pre_world_aligned_guide_seat_downstream.png")
            : TEXT("zambezi_batoka_v11_pre_terrain_integrated_guide_seat_downstream.png"));
    FString BaselineRiverEyePath = FPaths::Combine(
        CaptureRelativeRoot,
        bWorldAligned
            ? TEXT("zambezi_batoka_v12_pre_world_aligned_river_eye_downstream.png")
            : TEXT("zambezi_batoka_v11_pre_terrain_integrated_river_eye_downstream.png"));
    FString ComparisonGuidePath = FPaths::Combine(
        CaptureRelativeRoot,
        bWorldAligned
            ? TEXT("zambezi_batoka_v12_world_aligned_guide_seat_downstream.png")
            : TEXT("zambezi_batoka_v11_terrain_integrated_guide_seat_downstream.png"));
    FString ComparisonRiverEyePath = FPaths::Combine(
        CaptureRelativeRoot,
        bWorldAligned
            ? TEXT("zambezi_batoka_v12_world_aligned_river_eye_downstream.png")
            : TEXT("zambezi_batoka_v11_terrain_integrated_river_eye_downstream.png"));

    const bool bBaselineGuideCaptured = CapturePreviewImageForSpec(
        ZambeziCandidate->PreviewSpec,
        CaptureRoot,
        BaselineGuidePath,
        TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"),
        bWorldAligned
            ? TEXT("pre_batoka_v12_world_aligned_guide_seat_downstream")
            : TEXT("pre_batoka_v11_terrain_integrated_guide_seat_downstream"),
        TEXT("Zambezi untouched baseline guide-seat terrain-integrated Batoka comparison"),
        true,
        OutSummary);
    const bool bBaselineRiverEyeCaptured = CapturePreviewImageForSpec(
        ZambeziCandidate->PreviewSpec,
        CaptureRoot,
        BaselineRiverEyePath,
        TEXT("RaftSim_RiverEye_DownstreamCaptureCamera"),
        bWorldAligned
            ? TEXT("pre_batoka_v12_world_aligned_river_eye_downstream")
            : TEXT("pre_batoka_v11_terrain_integrated_river_eye_downstream"),
        TEXT("Zambezi untouched baseline river-eye terrain-integrated Batoka comparison"),
        true,
        OutSummary);

    auto MakeWorldSetup = [TerrainReviewMaterial, bWorldAligned](int32& OutOverriddenTileCount)
    {
        return [TerrainReviewMaterial, bWorldAligned, &OutOverriddenTileCount](
                   UWorld* World,
                   ACameraActor*,
                   FString& Summary)
        {
            if (!World || !TerrainReviewMaterial)
            {
                return false;
            }

            OutOverriddenTileCount = 0;
            static const FString DenseTerrainActorPrefix =
                TEXT("RaftSim_PhysicalCorridorDenseSourceTerrainTile_");
            for (TActorIterator<AActor> It(World); It; ++It)
            {
                AActor* Actor = *It;
                if (!Actor || !Actor->GetActorLabel().StartsWith(DenseTerrainActorPrefix))
                {
                    continue;
                }
                UProceduralMeshComponent* MeshComponent =
                    Actor->FindComponentByClass<UProceduralMeshComponent>();
                if (!MeshComponent)
                {
                    continue;
                }
                MeshComponent->SetMaterial(0, TerrainReviewMaterial);
                ++OutOverriddenTileCount;
            }
            Summary += FString::Printf(
                TEXT("Applied the transient Batoka %s material to %d dense visual-terrain tiles; collision and source Landscape were not changed.\n"),
                bWorldAligned ? TEXT("V12 world-aligned") : TEXT("V11 top-down"),
                OutOverriddenTileCount);
            return OutOverriddenTileCount == 4;
        };
    };

    int32 GuideOverriddenTileCount = 0;
    int32 RiverEyeOverriddenTileCount = 0;
    const bool bComparisonGuideCaptured = CapturePreviewImageForSpec(
        ZambeziCandidate->PreviewSpec,
        CaptureRoot,
        ComparisonGuidePath,
        TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"),
        bWorldAligned
            ? TEXT("batoka_v12_world_aligned_guide_seat_downstream")
            : TEXT("batoka_v11_terrain_integrated_guide_seat_downstream"),
        bWorldAligned
            ? TEXT("Zambezi guide-seat transient world-aligned Batoka V12 comparison")
            : TEXT("Zambezi guide-seat transient terrain-integrated Batoka V11 comparison"),
        true,
        OutSummary,
        MakeWorldSetup(GuideOverriddenTileCount));
    const bool bComparisonRiverEyeCaptured = CapturePreviewImageForSpec(
        ZambeziCandidate->PreviewSpec,
        CaptureRoot,
        ComparisonRiverEyePath,
        TEXT("RaftSim_RiverEye_DownstreamCaptureCamera"),
        bWorldAligned
            ? TEXT("batoka_v12_world_aligned_river_eye_downstream")
            : TEXT("batoka_v11_terrain_integrated_river_eye_downstream"),
        bWorldAligned
            ? TEXT("Zambezi river-eye transient world-aligned Batoka V12 comparison")
            : TEXT("Zambezi river-eye transient terrain-integrated Batoka V11 comparison"),
        true,
        OutSummary,
        MakeWorldSetup(RiverEyeOverriddenTileCount));
    const bool bAllCaptured =
        bBaselineGuideCaptured && bBaselineRiverEyeCaptured &&
        bComparisonGuideCaptured && bComparisonRiverEyeCaptured;

    TSharedRef<FJsonObject> Report = MakeShared<FJsonObject>();
    Report->SetStringField(
        TEXT("schema"),
        bWorldAligned
            ? TEXT("raftsim.unreal.zambezi_batoka_world_aligned_terrain_comparison.v1")
            : TEXT("raftsim.unreal.zambezi_batoka_terrain_integrated_comparison.v1"));
    Report->SetStringField(TEXT("river_id"), TEXT("zambezi_batoka_gorge"));
    Report->SetStringField(
        TEXT("status"),
        bAllCaptured
            ? (bWorldAligned
                   ? TEXT("paired_transient_world_aligned_v12_comparison_captured_pending_human_review")
                   : TEXT("paired_transient_terrain_integrated_v11_comparison_captured_pending_human_review"))
            : (bWorldAligned
                   ? TEXT("one_or_more_world_aligned_v12_comparison_captures_failed")
                   : TEXT("one_or_more_terrain_integrated_v11_comparison_captures_failed")));
    Report->SetBoolField(TEXT("production_promoted"), false);
    Report->SetBoolField(TEXT("corridor_substitution_performed"), false);
    Report->SetBoolField(TEXT("source_map_modified"), false);
    Report->SetBoolField(TEXT("landscape_height_or_collision_modified"), false);
    Report->SetBoolField(TEXT("hydrodynamic_or_gameplay_authority_modified"), false);
    Report->SetBoolField(TEXT("external_pixels_copied"), true);
    Report->SetBoolField(TEXT("external_geometry_copied"), false);
    Report->SetStringField(TEXT("source_map"), ZambeziCandidate->PreviewSpec.MapPackagePath);
    Report->SetStringField(TEXT("material_asset"), TerrainReviewMaterial->GetPathName());
    Report->SetStringField(
        TEXT("target_actor_prefix"),
        TEXT("RaftSim_PhysicalCorridorDenseSourceTerrainTile_"));
    Report->SetNumberField(TEXT("expected_visual_tile_count"), 4);
    Report->SetNumberField(TEXT("guide_overridden_visual_tile_count"), GuideOverriddenTileCount);
    Report->SetNumberField(TEXT("river_eye_overridden_visual_tile_count"), RiverEyeOverriddenTileCount);
    Report->SetStringField(
        TEXT("authority_boundary"),
        TEXT("transient render-material override on the continuous dense visual-terrain mesh only; saved map, source Landscape, height query, collision, centerline, bed, banks, custom C++ water, GeoClaw, feature forcing, raft contact, hazards, and gameplay authority remain unchanged"));

    TSharedRef<FJsonObject> MaterialParameters = MakeShared<FJsonObject>();
    MaterialParameters->SetNumberField(TEXT("macro_tile_cm"), 5000.0);
    MaterialParameters->SetNumberField(TEXT("detail_tile_cm"), 240.0);
    MaterialParameters->SetNumberField(TEXT("macro_albedo_weight"), 0.56);
    MaterialParameters->SetNumberField(TEXT("detail_albedo_weight"), 0.16);
    MaterialParameters->SetNumberField(TEXT("detail_color_scale"), 1.18);
    MaterialParameters->SetNumberField(TEXT("detail_normal_weight"), 0.42);
    MaterialParameters->SetNumberField(TEXT("detail_roughness_weight"), 0.28);
    MaterialParameters->SetNumberField(TEXT("macro_ao_weight"), 0.32);
    MaterialParameters->SetNumberField(TEXT("rock_slope_start"), 0.10);
    MaterialParameters->SetNumberField(TEXT("rock_slope_gain"), 3.3);
    MaterialParameters->SetStringField(
        TEXT("projection"),
        bWorldAligned ? TEXT("world_aligned_triplanar") : TEXT("top_down_corridor_uv"));
    MaterialParameters->SetBoolField(
        TEXT("world_space_normal_output"),
        bWorldAligned);
    MaterialParameters->SetStringField(
        TEXT("macro_asset_id"),
        TEXT("polyhaven_aerial_rocks_02_4k"));
    MaterialParameters->SetStringField(
        TEXT("detail_asset_id"),
        TEXT("ambientcg_rock037_2k"));
    Report->SetObjectField(TEXT("material_parameters"), MaterialParameters);

    TSharedRef<FJsonObject> Captures = MakeShared<FJsonObject>();
    Captures->SetStringField(TEXT("baseline_guide_seat"), BaselineGuidePath);
    Captures->SetStringField(TEXT("baseline_river_eye"), BaselineRiverEyePath);
    Captures->SetStringField(TEXT("comparison_guide_seat"), ComparisonGuidePath);
    Captures->SetStringField(TEXT("comparison_river_eye"), ComparisonRiverEyePath);
    Captures->SetBoolField(TEXT("all_captured"), bAllCaptured);
    Report->SetObjectField(TEXT("captures"), Captures);

    TArray<TSharedPtr<FJsonValue>> OpenGates;
    for (const TCHAR* Gate : {
             TEXT("paired_human_visual_review"),
             TEXT("continuous_surface_seam_and_repetition_review"),
             TEXT("Batoka_geology_and_reach_specific_lithology_review"),
             TEXT("higher_resolution_terrain_and_gorge_silhouette_review"),
             TEXT("guide_and_hazard_readability_review"),
             TEXT("geospatial_and_source_terrain_review"),
             TEXT("rights_and_art_review"),
             TEXT("woodland_water_mist_and_lighting_review"),
             TEXT("desktop_console_handheld_and_VR_performance"),
             TEXT("separate_surveyed_collision_and_hydrodynamic_review")})
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
        bWorldAligned
            ? TEXT("zambezi_batoka_v12_world_aligned_comparison_report.json")
            : TEXT("zambezi_batoka_v11_terrain_integrated_comparison_report.json"));
    const FString ReportPath = FPaths::Combine(GetRepoRoot(), ReportRelativePath);
    const bool bReportSaved =
        bSerialized && FFileHelper::SaveStringToFile(SerializedReport, *ReportPath);
    OutSummary += FString::Printf(
        TEXT("%s Batoka %s transient terrain-integrated comparison report -> %s\n"),
        bReportSaved ? TEXT("Saved") : TEXT("Failed to save"),
        bWorldAligned ? TEXT("V12 world-aligned") : TEXT("V11 top-down"),
        *ReportPath);
    return bAllCaptured && bReportSaved;
}

bool FRaftSimEditorModule::CaptureZambeziBatokaTerrainIntegratedComparison(
    FString& OutSummary)
{
    return CaptureZambeziBatokaTerrainComparisonInternal(false, OutSummary);
}

bool FRaftSimEditorModule::CaptureZambeziBatokaWorldAlignedTerrainComparison(
    FString& OutSummary)
{
    return CaptureZambeziBatokaTerrainComparisonInternal(true, OutSummary);
}

bool FRaftSimEditorModule::CaptureZambeziBatokaVisualMorphologyComparison(
    FString& OutSummary)
{
    const FRaftSimLandscapeImportCandidateSpec* ZambeziCandidate = nullptr;
    const TArray<FRaftSimLandscapeImportCandidateSpec> Candidates =
        GetLandscapeImportCandidateSpecs();
    for (const FRaftSimLandscapeImportCandidateSpec& Candidate : Candidates)
    {
        if (Candidate.PreviewSpec.RiverId == TEXT("zambezi_batoka_gorge"))
        {
            ZambeziCandidate = &Candidate;
            break;
        }
    }
    if (!ZambeziCandidate)
    {
        OutSummary += TEXT("The Zambezi physical-corridor candidate is not registered.\n");
        return false;
    }

    UMaterialInterface* TerrainReviewMaterial =
        LoadOrCreatePhysicalSourceTerrainRenderMaterial(
            *ZambeziCandidate,
            true,
            true);
    if (!TerrainReviewMaterial)
    {
        OutSummary += TEXT("Could not load the retained Batoka V12 world-aligned material.\n");
        return false;
    }

    const FString CaptureRelativeRoot =
        TEXT("docs/environment-captures/photoreal_river_previews/landscape_candidates");
    const FString CaptureRoot = FPaths::Combine(GetRepoRoot(), CaptureRelativeRoot);
    IFileManager::Get().MakeDirectory(*CaptureRoot, true);
    FString BaselineGuidePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("zambezi_batoka_v13_pre_morphology_guide_seat_downstream.png"));
    FString BaselineRiverEyePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("zambezi_batoka_v13_pre_morphology_river_eye_downstream.png"));
    FString ComparisonGuidePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("zambezi_batoka_v13_visual_morphology_guide_seat_downstream.png"));
    FString ComparisonRiverEyePath = FPaths::Combine(
        CaptureRelativeRoot,
        TEXT("zambezi_batoka_v13_visual_morphology_river_eye_downstream.png"));

    FZambeziBatokaVisualMorphologyStats BaselineGuideStats;
    FZambeziBatokaVisualMorphologyStats BaselineRiverEyeStats;
    FZambeziBatokaVisualMorphologyStats ComparisonGuideStats;
    FZambeziBatokaVisualMorphologyStats ComparisonRiverEyeStats;
    auto MakeWorldSetup = [ZambeziCandidate, TerrainReviewMaterial](
                              bool bApplyMorphology,
                              FZambeziBatokaVisualMorphologyStats& Stats)
    {
        return [ZambeziCandidate, TerrainReviewMaterial, bApplyMorphology, &Stats](
                   UWorld* World,
                   ACameraActor*,
                   FString& Summary)
        {
            return ApplyZambeziBatokaVisualTerrainTreatment(
                World,
                TerrainReviewMaterial,
                *ZambeziCandidate,
                bApplyMorphology,
                &Stats,
                Summary);
        };
    };

    const bool bBaselineGuideCaptured = CapturePreviewImageForSpec(
        ZambeziCandidate->PreviewSpec,
        CaptureRoot,
        BaselineGuidePath,
        TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"),
        TEXT("batoka_v13_pre_morphology_guide_seat_downstream"),
        TEXT("Zambezi guide-seat retained V12 material before V13 morphology"),
        true,
        OutSummary,
        MakeWorldSetup(false, BaselineGuideStats));
    const bool bBaselineRiverEyeCaptured = CapturePreviewImageForSpec(
        ZambeziCandidate->PreviewSpec,
        CaptureRoot,
        BaselineRiverEyePath,
        TEXT("RaftSim_RiverEye_DownstreamCaptureCamera"),
        TEXT("batoka_v13_pre_morphology_river_eye_downstream"),
        TEXT("Zambezi river-eye retained V12 material before V13 morphology"),
        true,
        OutSummary,
        MakeWorldSetup(false, BaselineRiverEyeStats));
    const bool bComparisonGuideCaptured = CapturePreviewImageForSpec(
        ZambeziCandidate->PreviewSpec,
        CaptureRoot,
        ComparisonGuidePath,
        TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"),
        TEXT("batoka_v13_visual_morphology_guide_seat_downstream"),
        TEXT("Zambezi guide-seat bounded render-only Batoka V13 morphology"),
        true,
        OutSummary,
        MakeWorldSetup(true, ComparisonGuideStats));
    const bool bComparisonRiverEyeCaptured = CapturePreviewImageForSpec(
        ZambeziCandidate->PreviewSpec,
        CaptureRoot,
        ComparisonRiverEyePath,
        TEXT("RaftSim_RiverEye_DownstreamCaptureCamera"),
        TEXT("batoka_v13_visual_morphology_river_eye_downstream"),
        TEXT("Zambezi river-eye bounded render-only Batoka V13 morphology"),
        true,
        OutSummary,
        MakeWorldSetup(true, ComparisonRiverEyeStats));
    const bool bAllCaptured =
        bBaselineGuideCaptured && bBaselineRiverEyeCaptured &&
        bComparisonGuideCaptured && bComparisonRiverEyeCaptured;

    auto MakeStatsObject = [](const FZambeziBatokaVisualMorphologyStats& Stats)
    {
        TSharedRef<FJsonObject> Object = MakeShared<FJsonObject>();
        Object->SetNumberField(TEXT("visual_tile_count"), Stats.VisualTileCount);
        Object->SetNumberField(TEXT("total_vertex_count"), Stats.TotalVertexCount);
        Object->SetNumberField(TEXT("modified_vertex_count"), Stats.ModifiedVertexCount);
        Object->SetNumberField(
            TEXT("protected_river_corridor_vertex_count"),
            Stats.ProtectedRiverCorridorVertexCount);
        Object->SetNumberField(
            TEXT("rejected_low_slope_vertex_count"),
            Stats.RejectedLowSlopeVertexCount);
        Object->SetNumberField(
            TEXT("minimum_offset_cm"),
            Stats.ModifiedVertexCount > 0 ? Stats.MinimumOffsetCm : 0.0);
        Object->SetNumberField(
            TEXT("maximum_offset_cm"),
            Stats.ModifiedVertexCount > 0 ? Stats.MaximumOffsetCm : 0.0);
        Object->SetNumberField(
            TEXT("mean_absolute_offset_cm"),
            Stats.ModifiedVertexCount > 0
                ? Stats.AbsoluteOffsetSumCm / Stats.ModifiedVertexCount
                : 0.0);
        return Object;
    };

    TSharedRef<FJsonObject> Report = MakeShared<FJsonObject>();
    Report->SetStringField(
        TEXT("schema"),
        TEXT("raftsim.unreal.zambezi_batoka_visual_morphology_comparison.v1"));
    Report->SetStringField(TEXT("river_id"), TEXT("zambezi_batoka_gorge"));
    Report->SetStringField(
        TEXT("status"),
        bAllCaptured
            ? TEXT("paired_transient_v13_visual_morphology_comparison_captured_pending_human_review")
            : TEXT("one_or_more_v13_visual_morphology_comparison_captures_failed"));
    Report->SetBoolField(TEXT("production_promoted"), false);
    Report->SetBoolField(TEXT("survey_or_source_terrain_replacement_performed"), false);
    Report->SetBoolField(TEXT("corridor_substitution_performed"), false);
    Report->SetBoolField(TEXT("source_map_modified"), false);
    Report->SetBoolField(TEXT("landscape_height_or_collision_modified"), false);
    Report->SetBoolField(TEXT("hydrodynamic_or_gameplay_authority_modified"), false);
    Report->SetBoolField(TEXT("external_pixels_copied"), true);
    Report->SetBoolField(TEXT("external_geometry_copied"), false);
    Report->SetStringField(TEXT("source_map"), ZambeziCandidate->PreviewSpec.MapPackagePath);
    Report->SetStringField(TEXT("material_asset"), TerrainReviewMaterial->GetPathName());
    Report->SetStringField(
        TEXT("authority_boundary"),
        TEXT("transient authored visual hypothesis on the continuous dense render mesh only; saved map, 30 m source DSM, source Landscape, height query, collision, centerline, bed, banks, custom C++ water, GeoClaw, feature forcing, raft contact, hazards, and gameplay authority remain unchanged"));
    Report->SetStringField(
        TEXT("evidence_limit"),
        TEXT("regional Batoka morphology constraints guide bounded visual breakup but do not establish surveyed wall, ledge, joint, gully, talus, bank, or bed geometry for Boiling Pot to Mukuni Beach"));

    TSharedRef<FJsonObject> MorphologyParameters = MakeShared<FJsonObject>();
    MorphologyParameters->SetStringField(
        TEXT("projection_basis"),
        TEXT("V12 world-aligned material"));
    MorphologyParameters->SetNumberField(TEXT("source_dsm_resolution_m"), 30.0);
    MorphologyParameters->SetNumberField(TEXT("visual_mesh_target_spacing_m"), 12.5);
    MorphologyParameters->SetNumberField(TEXT("maximum_absolute_offset_m"), 4.5);
    MorphologyParameters->SetNumberField(TEXT("river_protection_full_width_m"), 220.0);
    MorphologyParameters->SetNumberField(TEXT("river_protection_fade_end_m"), 650.0);
    MorphologyParameters->SetNumberField(TEXT("minimum_lava_flow_height_m"), 8.4);
    MorphologyParameters->SetNumberField(TEXT("maximum_lava_flow_height_m"), 13.6);
    MorphologyParameters->SetNumberField(TEXT("primary_joint_spacing_m"), 92.0);
    MorphologyParameters->SetNumberField(TEXT("secondary_joint_spacing_m"), 148.0);
    MorphologyParameters->SetStringField(
        TEXT("treatments"),
        TEXT("bounded elevation-conditioned flow breaks, two irregular joint families, and moderate-slope talus-scale breakup"));
    Report->SetObjectField(TEXT("morphology_parameters"), MorphologyParameters);

    TSharedRef<FJsonObject> Stats = MakeShared<FJsonObject>();
    Stats->SetObjectField(TEXT("baseline_guide_seat"), MakeStatsObject(BaselineGuideStats));
    Stats->SetObjectField(TEXT("baseline_river_eye"), MakeStatsObject(BaselineRiverEyeStats));
    Stats->SetObjectField(TEXT("comparison_guide_seat"), MakeStatsObject(ComparisonGuideStats));
    Stats->SetObjectField(TEXT("comparison_river_eye"), MakeStatsObject(ComparisonRiverEyeStats));
    Report->SetObjectField(TEXT("treatment_statistics"), Stats);

    TSharedRef<FJsonObject> Captures = MakeShared<FJsonObject>();
    Captures->SetStringField(TEXT("baseline_guide_seat"), BaselineGuidePath);
    Captures->SetStringField(TEXT("baseline_river_eye"), BaselineRiverEyePath);
    Captures->SetStringField(TEXT("comparison_guide_seat"), ComparisonGuidePath);
    Captures->SetStringField(TEXT("comparison_river_eye"), ComparisonRiverEyePath);
    Captures->SetBoolField(TEXT("all_captured"), bAllCaptured);
    Report->SetObjectField(TEXT("captures"), Captures);

    TArray<TSharedPtr<FJsonValue>> OpenGates;
    for (const TCHAR* Gate : {
             TEXT("paired_human_visual_review"),
             TEXT("higher_resolution_survey_or_photogrammetry_acquisition"),
             TEXT("Batoka_geology_and_reach_specific_lithology_review"),
             TEXT("gorge_silhouette_and_procedural_artifact_review"),
             TEXT("guide_and_hazard_readability_review"),
             TEXT("geospatial_and_source_terrain_review"),
             TEXT("rights_and_art_review"),
             TEXT("woodland_water_mist_and_lighting_review"),
             TEXT("desktop_console_handheld_and_VR_performance"),
             TEXT("separate_surveyed_collision_and_hydrodynamic_review")})
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
        TEXT("zambezi_batoka_v13_visual_morphology_comparison_report.json"));
    const FString ReportPath = FPaths::Combine(GetRepoRoot(), ReportRelativePath);
    const bool bReportSaved =
        bSerialized && FFileHelper::SaveStringToFile(SerializedReport, *ReportPath);
    OutSummary += FString::Printf(
        TEXT("%s Batoka V13 transient visual-morphology comparison report -> %s\n"),
        bReportSaved ? TEXT("Saved") : TEXT("Failed to save"),
        *ReportPath);
    return bAllCaptured && bReportSaved;
}
