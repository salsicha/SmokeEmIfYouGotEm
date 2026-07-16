#include "Environment/RaftSimEditorEnvironmentInternal.h"

DEFINE_LOG_CATEGORY(LogRaftSimEditorEnvironment);

namespace RaftSimEditorEnvironment
{
float GetPreviewRiverCenterY(const FRaftSimEnvironmentPreviewSpec& Spec, float X);

                                                 
 
                                      
                                      
                                     
                                     
                                              
                                     
                                
                                      
                                     
                                    
                                                                              
                                                                             
  

                                           
 
                                    
                                 
                                 
                                
                                    
                                  
  

                                              
 
                                 
                                     
                            
                           
                          
                                  
                                 
                         
                                   
                                   
                                      
                                          
                                          
                                   
                                          
                                         
                                             
                                             
                                        
                                         
                                           
                                                                          
                                                                                  
                                                                              
                                                                          
                                                                                        
                                                                                        
                                                                                 
  

FRaftSimLandscapeCandidateWaterSettings GetLandscapeCandidateWaterSettings(const FString& RiverId)
{
    FRaftSimLandscapeCandidateWaterSettings Settings;
    if (RiverId == TEXT("colorado_river"))
    {
        Settings.BaseColorScale = 1.20f;
        Settings.EmissiveFillScale = 0.100f;
        Settings.Roughness = 0.40f;
        Settings.Specular = 0.30f;
        Settings.Opacity = 0.55f;
        Settings.NormalIntensity = 0.40f;
        Settings.PhaseG = 0.05f;
        Settings.VertexTintWeight = 0.55f;
        Settings.RenderWidthScale = 1.17f;
        Settings.RenderNormalUpBlend = 0.60f;
        Settings.RenderDisplacementScale = 0.55f;
        Settings.ReflectionFillIntensity = 0.10f;
        Settings.SolverFieldEnable = 0.0f;
        Settings.SolverMacroNormalWeight = 0.0f;
        Settings.SolverDepthColorWeight = 0.0f;
        Settings.SolverFieldRoughnessWeight = 0.0f;
        Settings.SolverFroudeAerationWeight = 0.0f;
        Settings.SolverSpeedVisualGain = 0.0f;
        Settings.SolverFroudeVisualGain = 0.0f;
        Settings.SolverSurfaceReliefScale = 0.0f;
        Settings.SurfaceTint = FLinearColor(0.220f, 0.240f, 0.150f, 0.0f);
        Settings.ReflectionTint = FLinearColor(0.38f, 0.44f, 0.46f, 0.0f);
        Settings.ScatteringCoefficients = FLinearColor(0.0042f, 0.0023f, 0.0007f, 0.0f);
        Settings.AbsorptionCoefficients = FLinearColor(0.0014f, 0.0022f, 0.0040f, 0.0f);
        Settings.ColorScaleBehindWater = FLinearColor(0.84f, 0.76f, 0.62f, 0.0f);
    }
    else if (RiverId == TEXT("pacuare"))
    {
        Settings.BaseColorScale = 1.00f;
        Settings.EmissiveFillScale = 0.075f;
        Settings.Roughness = 0.32f;
        Settings.Specular = 0.42f;
        Settings.Opacity = 0.40f;
        Settings.NormalIntensity = 0.68f;
        Settings.PhaseG = 0.25f;
        Settings.VertexTintWeight = 0.62f;
        Settings.RenderWidthScale = 1.45f;
        Settings.RenderNormalUpBlend = 0.48f;
        Settings.RenderDisplacementScale = 0.78f;
        Settings.ReflectionFillIntensity = 0.15f;
        Settings.SolverFieldEnable = 0.0f;
        Settings.SolverMacroNormalWeight = 0.0f;
        Settings.SolverDepthColorWeight = 0.0f;
        Settings.SolverFieldRoughnessWeight = 0.0f;
        Settings.SolverFroudeAerationWeight = 0.0f;
        Settings.SolverSpeedVisualGain = 0.0f;
        Settings.SolverFroudeVisualGain = 0.0f;
        Settings.SolverSurfaceReliefScale = 0.0f;
        Settings.SurfaceTint = FLinearColor(0.018f, 0.095f, 0.065f, 0.0f);
        Settings.ReflectionTint = FLinearColor(0.32f, 0.48f, 0.54f, 0.0f);
        Settings.ScatteringCoefficients = FLinearColor(0.0008f, 0.0030f, 0.0018f, 0.0f);
        Settings.AbsorptionCoefficients = FLinearColor(0.0050f, 0.0012f, 0.0022f, 0.0f);
        Settings.ColorScaleBehindWater = FLinearColor(0.82f, 0.94f, 0.84f, 0.0f);
    }
    else if (RiverId == TEXT("zambezi_batoka_gorge"))
    {
        Settings.BaseColorScale = 1.10f;
        Settings.EmissiveFillScale = 0.085f;
        Settings.Roughness = 0.38f;
        Settings.Specular = 0.34f;
        Settings.Opacity = 0.52f;
        Settings.NormalIntensity = 0.58f;
        Settings.VertexTintWeight = 0.58f;
        Settings.RenderWidthScale = 1.24f;
        Settings.SolverFieldEnable = 0.0f;
        Settings.SolverMacroNormalWeight = 0.0f;
        Settings.SolverDepthColorWeight = 0.0f;
        Settings.SolverFieldRoughnessWeight = 0.0f;
        Settings.SolverFroudeAerationWeight = 0.0f;
        Settings.SolverSpeedVisualGain = 0.0f;
        Settings.SolverFroudeVisualGain = 0.0f;
        Settings.SolverSurfaceReliefScale = 0.0f;
        Settings.SurfaceTint = FLinearColor(0.13f, 0.16f, 0.065f, 0.0f);
        Settings.ReflectionTint = FLinearColor(0.40f, 0.46f, 0.39f, 0.0f);
    }
    else if (RiverId == TEXT("futaleufu_terminator"))
    {
        Settings.BaseColorScale = 1.08f;
        Settings.EmissiveFillScale = 0.090f;
        Settings.Roughness = 0.27f;
        Settings.Specular = 0.50f;
        Settings.Opacity = 0.34f;
        Settings.NormalIntensity = 0.74f;
        Settings.VertexTintWeight = 0.66f;
        Settings.RenderWidthScale = 1.30f;
        Settings.SolverFieldEnable = 0.0f;
        Settings.SolverMacroNormalWeight = 0.0f;
        Settings.SolverDepthColorWeight = 0.0f;
        Settings.SolverFieldRoughnessWeight = 0.0f;
        Settings.SolverFroudeAerationWeight = 0.0f;
        Settings.SolverSpeedVisualGain = 0.0f;
        Settings.SolverFroudeVisualGain = 0.0f;
        Settings.SolverSurfaceReliefScale = 0.0f;
        Settings.SurfaceTint = FLinearColor(0.012f, 0.20f, 0.24f, 0.0f);
        Settings.ReflectionTint = FLinearColor(0.40f, 0.60f, 0.68f, 0.0f);
    }
    else if (RiverId == TEXT("chilko_river_lava_canyon"))
    {
        Settings.BaseColorScale = 1.06f;
        Settings.EmissiveFillScale = 0.085f;
        Settings.Roughness = 0.29f;
        Settings.Specular = 0.48f;
        Settings.Opacity = 0.36f;
        Settings.NormalIntensity = 0.70f;
        Settings.VertexTintWeight = 0.64f;
        Settings.RenderWidthScale = 1.28f;
        Settings.SolverFieldEnable = 0.0f;
        Settings.SolverMacroNormalWeight = 0.0f;
        Settings.SolverDepthColorWeight = 0.0f;
        Settings.SolverFieldRoughnessWeight = 0.0f;
        Settings.SolverFroudeAerationWeight = 0.0f;
        Settings.SolverSpeedVisualGain = 0.0f;
        Settings.SolverFroudeVisualGain = 0.0f;
        Settings.SolverSurfaceReliefScale = 0.0f;
        Settings.SurfaceTint = FLinearColor(0.018f, 0.24f, 0.27f, 0.0f);
        Settings.ReflectionTint = FLinearColor(0.42f, 0.60f, 0.66f, 0.0f);
    }
    return Settings;
}

                                          
 
                               
                                    
                               
                                
                             
                           
                          
                           
                                    
                                                               
                                                              
  

FRaftSimPhotographicCaptureSettings GetPhotographicCaptureSettings(const FString& RiverId)
{
    FRaftSimPhotographicCaptureSettings Settings;
    if (RiverId == TEXT("colorado_river"))
    {
        Settings.SunIntensity = 5.40f;
        Settings.SkyLightIntensity = 2.10f;
        Settings.FogDensity = 0.0016f;
        Settings.ExposureBias = -0.12f;
        Settings.Saturation = 1.04f;
        Settings.Contrast = 1.03f;
        Settings.Sharpen = 0.26f;
        Settings.SunColor = FLinearColor(1.0f, 0.95f, 0.86f);
        Settings.FogColor = FLinearColor(0.64f, 0.57f, 0.47f);
    }
    else if (RiverId == TEXT("pacuare"))
    {
        Settings.SunIntensity = 4.60f;
        Settings.SkyLightIntensity = 1.45f;
        Settings.FogDensity = 0.0075f;
        Settings.ExposureBias = -0.18f;
        Settings.Saturation = 1.04f;
        Settings.Contrast = 1.03f;
        Settings.Sharpen = 0.22f;
        Settings.Vignette = 0.05f;
        Settings.SunColor = FLinearColor(0.90f, 0.97f, 0.91f);
        Settings.FogColor = FLinearColor(0.43f, 0.57f, 0.46f);
    }
    else if (RiverId == TEXT("zambezi_batoka_gorge"))
    {
        Settings.SunIntensity = 5.30f;
        Settings.SkyLightIntensity = 1.65f;
        Settings.FogDensity = 0.0038f;
        Settings.ExposureBias = -0.18f;
        Settings.Saturation = 1.04f;
        Settings.SunColor = FLinearColor(1.0f, 0.91f, 0.78f);
        Settings.FogColor = FLinearColor(0.58f, 0.50f, 0.39f);
    }
    else if (RiverId == TEXT("futaleufu_terminator"))
    {
        Settings.SunIntensity = 4.75f;
        Settings.SkyLightIntensity = 1.55f;
        Settings.FogDensity = 0.0055f;
        Settings.ExposureBias = -0.16f;
        Settings.Saturation = 1.05f;
        Settings.SunColor = FLinearColor(0.91f, 0.96f, 1.0f);
        Settings.FogColor = FLinearColor(0.46f, 0.58f, 0.60f);
    }
    else if (RiverId == TEXT("chilko_river_lava_canyon"))
    {
        Settings.SunIntensity = 5.05f;
        Settings.SkyLightIntensity = 1.60f;
        Settings.FogDensity = 0.0030f;
        Settings.ExposureBias = -0.16f;
        Settings.Saturation = 1.04f;
        Settings.Contrast = 1.03f;
        Settings.Sharpen = 0.24f;
        Settings.SunColor = FLinearColor(0.96f, 0.97f, 1.0f);
        Settings.FogColor = FLinearColor(0.50f, 0.58f, 0.60f);
    }
    return Settings;
}

                                                
 
                                                                        
                                                                       
                                                                               
                                                                      
                                                                     
                                                                             
                                    
                                 
  

FRaftSimLandscapeCandidateFoliageSettings GetLandscapeCandidateFoliageSettings(
    const FString& RiverId)
{
    FRaftSimLandscapeCandidateFoliageSettings Settings;
    if (RiverId == TEXT("colorado_river"))
    {
        Settings.BroadleafFrontTint = FLinearColor(0.96f, 1.04f, 0.58f);
        Settings.BroadleafBackTint = FLinearColor(0.74f, 0.82f, 0.40f);
        Settings.BroadleafTransmissionTint = FLinearColor(0.62f, 0.72f, 0.34f);
        Settings.ConiferFrontTint = FLinearColor(0.82f, 0.90f, 0.48f);
        Settings.ConiferBackTint = FLinearColor(0.64f, 0.72f, 0.34f);
        Settings.ConiferTransmissionTint = FLinearColor(0.54f, 0.62f, 0.30f);
        Settings.RoughnessStrength = 0.82f;
        Settings.NormalStrength = 0.52f;
    }
    else if (RiverId == TEXT("pacuare"))
    {
        Settings.BroadleafFrontTint = FLinearColor(0.70f, 1.15f, 0.62f);
        Settings.BroadleafBackTint = FLinearColor(0.46f, 0.86f, 0.42f);
        Settings.BroadleafTransmissionTint = FLinearColor(0.34f, 0.72f, 0.30f);
        Settings.ConiferFrontTint = FLinearColor(0.60f, 1.00f, 0.50f);
        Settings.ConiferBackTint = FLinearColor(0.40f, 0.76f, 0.34f);
        Settings.ConiferTransmissionTint = FLinearColor(0.30f, 0.64f, 0.26f);
        Settings.RoughnessStrength = 0.74f;
        Settings.NormalStrength = 0.58f;
    }
    else if (RiverId == TEXT("zambezi_batoka_gorge"))
    {
        Settings.BroadleafFrontTint = FLinearColor(0.92f, 1.02f, 0.48f);
        Settings.BroadleafBackTint = FLinearColor(0.66f, 0.76f, 0.30f);
        Settings.BroadleafTransmissionTint = FLinearColor(0.56f, 0.68f, 0.24f);
        Settings.RoughnessStrength = 0.82f;
        Settings.NormalStrength = 0.50f;
    }
    else if (RiverId == TEXT("futaleufu_terminator"))
    {
        Settings.BroadleafFrontTint = FLinearColor(0.66f, 1.10f, 0.56f);
        Settings.BroadleafBackTint = FLinearColor(0.42f, 0.78f, 0.38f);
        Settings.BroadleafTransmissionTint = FLinearColor(0.32f, 0.66f, 0.30f);
        Settings.ConiferFrontTint = FLinearColor(0.54f, 0.92f, 0.48f);
        Settings.ConiferBackTint = FLinearColor(0.34f, 0.68f, 0.30f);
        Settings.RoughnessStrength = 0.76f;
        Settings.NormalStrength = 0.60f;
    }
    else if (RiverId == TEXT("chilko_river_lava_canyon"))
    {
        Settings.BroadleafFrontTint = FLinearColor(0.78f, 1.08f, 0.58f);
        Settings.BroadleafBackTint = FLinearColor(0.52f, 0.80f, 0.38f);
        Settings.BroadleafTransmissionTint = FLinearColor(0.42f, 0.70f, 0.30f);
        Settings.ConiferFrontTint = FLinearColor(0.62f, 0.92f, 0.46f);
        Settings.ConiferBackTint = FLinearColor(0.40f, 0.68f, 0.30f);
        Settings.ConiferTransmissionTint = FLinearColor(0.32f, 0.58f, 0.24f);
        Settings.RoughnessStrength = 0.78f;
        Settings.NormalStrength = 0.56f;
    }
    return Settings;
}

FRaftSimPreviewWaterMaterialResponse GetPreviewWaterMaterialResponse(const FString& RiverId)
{
    FRaftSimPreviewWaterMaterialResponse Response;
    if (RiverId == TEXT("colorado_river"))
    {
        Response.EmissiveFillScale = 0.28f;
        Response.RoughnessScale = 0.22f;
        Response.RoughnessFloor = 0.34f;
        Response.SpecularLevel = 0.18f;
        Response.MeshNormalUpBlend = 0.18f;
        Response.NormalIntensity = 0.22f;
    }
    else if (RiverId == TEXT("pacuare"))
    {
        Response.EmissiveFillScale = 0.26f;
        Response.RoughnessScale = 0.18f;
        Response.RoughnessFloor = 0.30f;
        Response.SpecularLevel = 0.22f;
        Response.MeshNormalUpBlend = 0.12f;
        Response.NormalIntensity = 0.36f;
    }
    else if (RiverId == TEXT("zambezi_batoka_gorge"))
    {
        Response.EmissiveFillScale = 0.28f;
        Response.RoughnessScale = 0.22f;
        Response.RoughnessFloor = 0.34f;
        Response.SpecularLevel = 0.20f;
        Response.NormalIntensity = 0.30f;
    }
    else if (RiverId == TEXT("futaleufu_terminator"))
    {
        Response.EmissiveFillScale = 0.25f;
        Response.RoughnessScale = 0.16f;
        Response.RoughnessFloor = 0.26f;
        Response.SpecularLevel = 0.27f;
        Response.NormalIntensity = 0.42f;
    }
    return Response;
}

                           
 
                    
                     
                                

                        
     
                                                                         
     

                                               
     
                       
         
                                       
         

                                                                                                         
                                                                                                                    
                                                     
                                                                                     
                                                                                          
                                                                                          
                                                                                          
                         
                       
     

                                                  
     
                       
         
                                       
         

                                                                                                         
                                                                                                                    
                                                     
                         
                       
     

                                                          
     
                       
         
                                       
         

                                                                                         
                                                                                                   
                                                                               
                                                                                
                                                       
                                                        
                                                            
                                                            
                                                                                                      
                                                                                                         
                                               
     

                                            
     
                       
         
                        
         

                                                                                                         
                                                                                                                    
                                                           
                                                                                                   
     

                                                    
     
                       
         
                        
         

                                                                                         
                                                                                                   
                                                                               
                                                                                
                                                       
                                                        
                                                            
                                                            
                                                    
         
                                                              
                                                                                                 
          
                                                                             
                                                                                
                                               
     
  

FString GetRepoRoot()
{
    return FPaths::ConvertRelativePathToFull(FPaths::Combine(FPaths::ProjectDir(), TEXT("..")));
}

FString GetCaptureRoot()
{
    return FPaths::ConvertRelativePathToFull(FPaths::Combine(GetRepoRoot(), TEXT("docs/tool-captures/milestone25a")));
}

FString GetEnvironmentCaptureRoot()
{
    return FPaths::ConvertRelativePathToFull(
        FPaths::Combine(GetRepoRoot(), TEXT("docs/environment-captures/photoreal_river_previews")));
}

FString GetPhotorealRiverSourcePlanRelativePath()
{
    return TEXT("unreal/Content/RaftSim/Rendering/photoreal_river_environment_sources.json");
}

FString GetPhotorealFlowVariantCapturePlanRelativePath()
{
    return TEXT("docs/environment-captures/photoreal_river_previews/photoreal_flow_variant_capture_plan.json");
}

FString GetFirstPartyProceduralEnvironmentAssetPlanRelativePath()
{
    return TEXT("unreal/Content/RaftSim/Rendering/first_party_procedural_environment_assets.json");
}

FString GetFirstPartyProceduralMaterialRecipePlanRelativePath()
{
    return TEXT("unreal/Content/RaftSim/Rendering/first_party_procedural_material_recipes.json");
}

FString GetFirstPartyMaterialTextureAtlasManifestRelativePath()
{
    return TEXT("unreal/Content/RaftSim/Rendering/ProceduralTextureAtlases/first_party_material_texture_atlas_manifest.json");
}

FString GetSourceConditionedMaterialMapManifestRelativePath()
{
    return TEXT("unreal/Content/RaftSim/Rendering/SourceConditionedMaterialMaps/first_party_source_conditioned_material_map_manifest.json");
}

FString GetProductionDetailTextureManifestRelativePath()
{
    return TEXT("unreal/Content/RaftSim/Rendering/ProductionDetailTextures/first_party_production_detail_texture_manifest.json");
}

FString GetFirstPartyMaterialInstanceCandidateManifestRelativePath()
{
    return TEXT("unreal/Content/RaftSim/Rendering/first_party_material_instance_candidates.json");
}

FString GetFirstPartyMaterialInstanceReviewAssetRootRelativePath()
{
    return TEXT("unreal/Content/RaftSim/Materials/MaterialInstances");
}

FString GetFirstPartyMaterialInstanceReviewAssetStatus()
{
    return TEXT("created_unreal_material_instance_constant_review_assets_with_texture_bindings_sampler_parent_and_scene_assignment_not_lifelike");
}

FString GetFirstPartyMaterialInstanceSceneAssignmentStatus()
{
    return TEXT("assigned_review_material_instances_to_preview_map_surface_proxies_not_lifelike");
}

FString GetFirstPartyMaterialTextureAssetRootRelativePath()
{
    return TEXT("unreal/Content/RaftSim/Rendering/ProceduralTextureAtlases/Textures");
}

FString GetFirstPartyMaterialTextureAssetStatus()
{
    return TEXT("created_unreal_texture2d_review_assets_bound_to_material_instance_candidates_not_lifelike");
}

FString GetSourceConditionedMaterialTextureAssetRootRelativePath()
{
    return TEXT("unreal/Content/RaftSim/Rendering/SourceConditionedMaterialMaps/Textures");
}

FString GetSourceConditionedMaterialTextureAssetStatus()
{
    return TEXT("created_unreal_texture2d_review_assets_bound_to_source_conditioned_material_instances_not_lifelike");
}

FString GetProductionDetailTextureAssetRootRelativePath()
{
    return TEXT("unreal/Content/RaftSim/Rendering/ProductionDetailTextures/Textures");
}

FString GetProductionDetailTextureAssetStatus()
{
    return TEXT("created_unreal_first_party_terrain_detail_texture_candidates_bound_to_review_material_not_lifelike");
}

FString GetSolverVisualizationFieldManifestRelativePath()
{
    return TEXT("unreal/Content/RaftSim/Rendering/SolverVisualizationFields/cpp_solver_visualization_field_manifest.json");
}

FString GetSolverVisualizationFieldTextureAssetRootRelativePath()
{
    return TEXT("unreal/Content/RaftSim/Rendering/SolverVisualizationFields/Textures");
}

FString GetFirstPartyAtlasSampleReviewMaterialRelativePath()
{
    return TEXT("unreal/Content/RaftSim/Materials/M_RaftSim_AtlasSampleReview.uasset");
}

FString GetFirstPartyAtlasSampleReviewMaterialStatus()
{
    return TEXT("created_unreal_atlas_sampler_review_parent_material_not_lifelike");
}

FString GetFirstPartyMaterialTextureAtlasAlbedoRelativePath(const FString& RiverId)
{
    return FString::Printf(
        TEXT("unreal/Content/RaftSim/Rendering/ProceduralTextureAtlases/%s_first_party_material_texture_atlas_albedo.png"),
        *RiverId);
}

FString GetFirstPartyMaterialTextureAtlasNormalRelativePath(const FString& RiverId)
{
    return FString::Printf(
        TEXT("unreal/Content/RaftSim/Rendering/ProceduralTextureAtlases/%s_first_party_material_texture_atlas_normal.png"),
        *RiverId);
}

FString GetFirstPartyMaterialTextureAtlasPackedRelativePath(const FString& RiverId)
{
    return FString::Printf(
        TEXT("unreal/Content/RaftSim/Rendering/ProceduralTextureAtlases/%s_first_party_material_texture_atlas_ao_roughness_height.png"),
        *RiverId);
}

FString GetSourceConditionedMaterialMapRelativePath(const FString& RiverId, const FString& MapKey)
{
    FString MapSuffix = TEXT("macro_albedo");
    if (MapKey == TEXT("SourceConditionedMaterialZones"))
    {
        MapSuffix = TEXT("material_zones");
    }
    else if (MapKey == TEXT("SourceConditionedAORoughnessHeight"))
    {
        MapSuffix = TEXT("ao_roughness_height");
    }
    else if (MapKey == TEXT("SourceConditionedNormalDetail"))
    {
        MapSuffix = TEXT("normal_detail");
    }

    return FString::Printf(
        TEXT("unreal/Content/RaftSim/Rendering/SourceConditionedMaterialMaps/%s_source_conditioned_%s.png"),
        *RiverId,
        *MapSuffix);
}

FString GetProductionDetailTextureRelativePath(const FString& RiverId, const FString& MapKey)
{
    FString MapSuffix = TEXT("albedo");
    if (MapKey == TEXT("TerrainDetailNormal"))
    {
        MapSuffix = TEXT("normal");
    }
    else if (MapKey == TEXT("TerrainDetailAORoughnessHeight"))
    {
        MapSuffix = TEXT("ao_roughness_height");
    }

    return FString::Printf(
        TEXT("unreal/Content/RaftSim/Rendering/ProductionDetailTextures/%s_terrain_bank_detail_v1_%s.png"),
        *RiverId,
        *MapSuffix);
}

FString GetProductionGeospatialAttachmentLedgerRelativePath()
{
    return TEXT("physics/data/real_world/production_geospatial_attachment_ledger.json");
}

                                                     
 
       
                                                     
     
                              
                                                                                                    
                                 
         
                                                             
                               
             
                                                                 
                                
                       
                                     
                            
                                                                                                                         
             
         
     

                                                      
     
                                             
         
                                                                      
         
     

        
                                                     
                                
                          
  

FString EscapeRaftSimJsonString(const FString& Value)
{
    FString Escaped = Value.Replace(TEXT("\\"), TEXT("\\\\"));
    Escaped = Escaped.Replace(TEXT("\""), TEXT("\\\""));
    Escaped = Escaped.Replace(TEXT("\r"), TEXT("\\r"));
    Escaped = Escaped.Replace(TEXT("\n"), TEXT("\\n"));
    return Escaped;
}

                                                
 
                               
                                              
                                                    
                                              
  

bool LoadLandscapeCandidateLocalCenterline(
    const FRaftSimLandscapeImportCandidateSpec& Candidate,
    TArray<FRaftSimLandscapeCandidateCenterlinePoint>& OutPoints,
    FString& OutSummary)
{
    OutPoints.Reset();
    if (Candidate.LocalCenterlineRelativePath.IsEmpty())
    {
        return true;
    }

    const FString AbsolutePath = FPaths::ConvertRelativePathToFull(
        FPaths::Combine(GetRepoRoot(), Candidate.LocalCenterlineRelativePath));
    FString JsonText;
    if (!FFileHelper::LoadFileToString(JsonText, *AbsolutePath))
    {
        OutSummary += FString::Printf(TEXT("Could not read physical corridor centerline %s.\n"), *AbsolutePath);
        return false;
    }
    TSharedPtr<FJsonObject> Root;
    const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(JsonText);
    if (!FJsonSerializer::Deserialize(Reader, Root) || !Root.IsValid())
    {
        OutSummary += FString::Printf(TEXT("Could not parse physical corridor centerline %s.\n"), *AbsolutePath);
        return false;
    }

    const TArray<TSharedPtr<FJsonValue>>* PointValues = nullptr;
    if (!Root->TryGetArrayField(TEXT("points"), PointValues) || !PointValues)
    {
        OutSummary += TEXT("Physical corridor centerline has no points array.\n");
        return false;
    }
    for (const TSharedPtr<FJsonValue>& PointValue : *PointValues)
    {
        const TSharedPtr<FJsonObject> PointObject = PointValue ? PointValue->AsObject() : nullptr;
        const TArray<TSharedPtr<FJsonValue>>* LocalValues = nullptr;
        if (!PointObject.IsValid() ||
            !PointObject->TryGetArrayField(TEXT("unreal_local_cm"), LocalValues) ||
            !LocalValues || LocalValues->Num() != 2)
        {
            continue;
        }
        FRaftSimLandscapeCandidateCenterlinePoint Point;
        Point.StationMeters = static_cast<float>(PointObject->GetNumberField(TEXT("station_m")));
        Point.LocalCm = FVector2D(
            static_cast<float>((*LocalValues)[0]->AsNumber()),
            static_cast<float>((*LocalValues)[1]->AsNumber()));
        double ConditionedVisualSurfaceNormalized = 0.0;
        if (PointObject->TryGetNumberField(
                TEXT("conditioned_visual_surface_normalized"),
                ConditionedVisualSurfaceNormalized))
        {
            Point.ConditionedVisualSurfaceNormalized = static_cast<float>(
                ConditionedVisualSurfaceNormalized);
            Point.bHasConditionedVisualSurface = true;
        }
        OutPoints.Add(Point);
    }
    if (OutPoints.Num() < 2)
    {
        OutSummary += TEXT("Physical corridor centerline has fewer than two usable points.\n");
        return false;
    }
    OutSummary += FString::Printf(
        TEXT("Loaded %d source-aligned physical corridor centerline points from %s.\n"),
        OutPoints.Num(),
        *Candidate.LocalCenterlineRelativePath);
    return true;
}

FVector2D SampleLandscapeCandidateCenterlineWorld(
    const FRaftSimLandscapeImportCandidateSpec& Candidate,
    const TArray<FRaftSimLandscapeCandidateCenterlinePoint>& Points,
    float Progress,
    FVector2D* OutTangent)
{
    constexpr float LandscapeMinX = -5800.0f;
    if (Points.Num() < 2)
    {
        const float X = FMath::Lerp(
            LandscapeMinX,
            LandscapeMinX + Candidate.HorizontalSpanXCm,
            FMath::Clamp(Progress, 0.0f, 1.0f));
        if (OutTangent)
        {
            *OutTangent = FVector2D(1.0f, 0.0f);
        }
        return FVector2D(X, GetPreviewRiverCenterY(Candidate.PreviewSpec, X));
    }

    const float TargetStation = FMath::Lerp(
        Points[0].StationMeters,
        Points.Last().StationMeters,
        FMath::Clamp(Progress, 0.0f, 1.0f));
    int32 SegmentIndex = 0;
    while (SegmentIndex + 1 < Points.Num() - 1 &&
           Points[SegmentIndex + 1].StationMeters < TargetStation)
    {
        ++SegmentIndex;
    }
    const FRaftSimLandscapeCandidateCenterlinePoint& A = Points[SegmentIndex];
    const FRaftSimLandscapeCandidateCenterlinePoint& B = Points[SegmentIndex + 1];
    const float SegmentLength = FMath::Max(0.001f, B.StationMeters - A.StationMeters);
    const float T = FMath::Clamp((TargetStation - A.StationMeters) / SegmentLength, 0.0f, 1.0f);
    const FVector2D Local = FMath::Lerp(A.LocalCm, B.LocalCm, T);
    const FVector2D Tangent = (B.LocalCm - A.LocalCm).GetSafeNormal();
    if (OutTangent)
    {
        *OutTangent = Tangent;
    }
    return FVector2D(
        LandscapeMinX + Local.X,
        -Candidate.HorizontalSpanYCm * 0.5f + Local.Y);
}

bool SampleLandscapeCandidateConditionedVisualSurfaceWorldZ(
    const FRaftSimLandscapeImportCandidateSpec& Candidate,
    const TArray<FRaftSimLandscapeCandidateCenterlinePoint>& Points,
    float Progress,
    float& OutWorldZ)
{
    if (Points.Num() < 2)
    {
        return false;
    }
    const float TargetStation = FMath::Lerp(
        Points[0].StationMeters,
        Points.Last().StationMeters,
        FMath::Clamp(Progress, 0.0f, 1.0f));
    int32 SegmentIndex = 0;
    while (SegmentIndex + 1 < Points.Num() - 1 &&
           Points[SegmentIndex + 1].StationMeters < TargetStation)
    {
        ++SegmentIndex;
    }
    const FRaftSimLandscapeCandidateCenterlinePoint& A = Points[SegmentIndex];
    const FRaftSimLandscapeCandidateCenterlinePoint& B = Points[SegmentIndex + 1];
    if (!A.bHasConditionedVisualSurface || !B.bHasConditionedVisualSurface)
    {
        return false;
    }
    const float SegmentLength = FMath::Max(0.001f, B.StationMeters - A.StationMeters);
    const float T = FMath::Clamp((TargetStation - A.StationMeters) / SegmentLength, 0.0f, 1.0f);
    OutWorldZ = FMath::Lerp(
        A.ConditionedVisualSurfaceNormalized,
        B.ConditionedVisualSurfaceNormalized,
        T) * Candidate.TargetReliefCm;
    return true;
}

TArray<FRaftSimEnvironmentPreviewSpec> GetEnvironmentPreviewSpecs()
{
    TArray<FRaftSimEnvironmentPreviewSpec> Specs;

    FRaftSimEnvironmentPreviewSpec SouthFork;
    SouthFork.RiverId = TEXT("american_south_fork");
    SouthFork.DisplayName = TEXT("South Fork American River");
    SouthFork.MapPackagePath = TEXT("/Game/RaftSim/Maps/EnvironmentPreviews/L_SouthForkAmerican_PhotorealPreview");
    SouthFork.SourceManifest = TEXT("physics/data/real_world/south_fork_american_chili_bar/source_manifest.json");
    SouthFork.AerialDrapeImage =
        TEXT("physics/data/real_world/south_fork_american_chili_bar/imagery/production_import_pilot/source_drape_4096.png");
    SouthFork.TerrainReliefImage =
        TEXT("physics/data/real_world/south_fork_american_chili_bar/terrain/production_import_pilot/dem_relief_2048.png");
    SouthFork.HeightfieldPreviewImage =
        TEXT("physics/data/real_world/south_fork_american_chili_bar/terrain/production_import_pilot/heightfield_candidate_2017.png");
    SouthFork.WaterMaskImage =
        TEXT("physics/data/real_world/south_fork_american_chili_bar/imagery/production_import_pilot/water_mask_2048.png");
    SouthFork.VegetationMaskImage =
        TEXT("physics/data/real_world/south_fork_american_chili_bar/imagery/production_import_pilot/vegetation_mask_2048.png");
    SouthFork.ElevationSample =
        TEXT("physics/data/real_world/south_fork_american_chili_bar/terrain/production_import_pilot/3dep_tiles");
    SouthFork.SourceDrapeDescription =
        TEXT("stitched South Fork production-import pilot source drape generated from four official USDA/APFO NAIP 2048px tiles, plus stitched USGS 3DEP pilot DEM relief and a review-gated 2017px heightfield candidate sampled into bank and valley preview geometry; pilot source water/vegetation masks are sampled into terrain color, source-aware terrain photo mottle/microrelief, source-conditioned far-bank albedo/microrelief calibration, first-party photographic color-grade palette compression, broad-slope terrain exposure fill and relief, source-aware macro terrain ridge/facet relief, source-aware terrain slope facet texture, first-party source-aware terrain surface granularity, source-aware riparian canopy mass texture, minimized source overlay plate artifacts, graphic waterline ribbon demotion, remaining water overlay slab demotion, long dark water streak demotion, current streak and waterline rail artifact demotion, central water scaffold plate demotion, base-water center guide-stripe breakup, base-water cross-channel breakup, base-water residual center-seam erase, dark micro-ripple artifact demotion, source-aware bank breakup patches, first-party source-masked bank/bar microgeometry, first-party near-field riverbed pebble/debris dressing, first-party irregular shoreline edge breakup, first-party source-masked shoreline lip/overhang edge breakup, first-party terrain material layer facets, first-party Landscape/Nanite material scaffold microfacets/strata/slope occlusion, first-party terrain erosion-rill/bank-gully strips, source-aware boulder wetness/abrasion/moss facets, biome-specific deadfall/log/grass/root ecology props, first-party biome foliage silhouette cards, dense layered riparian canopy/understory proxy clusters, first-party instanced procedural foliage-equivalent canopy/trunk/understory scaffold, first-party procedural-only foliage review path with stylized PCG sample tree meshes disabled, first-party procedural canopy height and massing profile, first-party procedural canopy tone compression and shadow profile, first-party foliage card/canopy artifact demotion, square foliage/source-card artifact demotion, remaining square card cull, first-party organic branch/frond lattice foliage, first-party fine twig canopy lace foliage, first-party foliage crown depth and leaflet breakup, lit water variation, first-party lit water normal-response scaffold, base-water flow-thread texture, flow-cued water foam/slick mottle, flow-dependent hydraulic aeration/spray mats and beads, flow-band depth texture ribbons, flow-aware surface chop/turbidity patches, turbidity-depth patch artifact demotion, first-party water shader depth/reflection/refraction scaffold, source-aware shallow-water clarity/aeration layers, deterministic wet-rock, talus, foliage, understory, mask-aware ground-cover cards, disabled guide-seat raft/oar foreground proxy hooks, river-specific atmospheric backdrop cards, and source-aware sky-gradient/depth layers; all pilot derivatives remain review-gated until metadata review, mosaic/clip, hydrologic conditioning, channel burning, masks, and guide/geospatial approval pass; rocks, foliage, water, foam, raft, and lighting still include first-party procedural proxy layers");
    SouthFork.FlowBandId = TEXT("median_runnable");
    SouthFork.FlowBandDisplayName = TEXT("Median Runnable / Summer Commercial");
    SouthFork.FlowBandSource = TEXT("physics/data/real_world/south_fork_american_chili_bar/flow_presets.json");
    SouthFork.FlowVisualDescription =
        TEXT("Default South Fork summer-commercial validation band from USGS-11445500 planning presets; keeps moderate tongues, wet rocks, and foam lines visible while low/high seasonal variants remain future capture targets.");
    SouthFork.FlowReferenceDischargeCfs = 1600.0f;
    SouthFork.WaterColor = FLinearColor(0.070f, 0.205f, 0.115f);
    SouthFork.TerrainColor = FLinearColor(0.35f, 0.30f, 0.21f);
    SouthFork.RockColor = FLinearColor(0.38f, 0.36f, 0.31f);
    SouthFork.FoliageColor = FLinearColor(0.16f, 0.29f, 0.105f);
    SouthFork.CanyonHeightCm = 850.0f;
    SouthFork.RiverHalfWidthCm = 335.0f;
    SouthFork.BankWidthCm = 720.0f;
    SouthFork.BendAmplitudeCm = 290.0f;
    SouthFork.TerrainReliefAmplitudeCm = 180.0f;
    SouthFork.HeightfieldPreviewAmplitudeCm = 620.0f;
    SouthFork.HeightfieldLocalReliefAmplitudeCm = 620.0f;
    SouthFork.HeightfieldSeamFeatherUv = 0.030f;
    SouthFork.TerrainNormalSofteningBlend = 0.52f;
    SouthFork.BoulderCount = 24;
    SouthFork.FoliageCount = 36;
    SouthFork.FoamTrainCount = 14;
    Specs.Add(SouthFork);

    FRaftSimEnvironmentPreviewSpec Colorado;
    Colorado.RiverId = TEXT("colorado_river");
    Colorado.DisplayName = TEXT("Colorado River Grand Canyon");
    Colorado.MapPackagePath = TEXT("/Game/RaftSim/Maps/EnvironmentPreviews/L_ColoradoGrandCanyon_PhotorealPreview");
    Colorado.SourceManifest = TEXT("physics/data/real_world/colorado_river_grand_canyon_rowing/source_manifest.json");
    Colorado.AerialDrapeImage =
        TEXT("physics/data/real_world/colorado_river_grand_canyon_rowing/imagery/production_import_pilot/source_drape_4096.png");
    Colorado.TerrainReliefImage =
        TEXT("physics/data/real_world/colorado_river_grand_canyon_rowing/terrain/production_import_pilot/dem_relief_2048.png");
    Colorado.HeightfieldPreviewImage =
        TEXT("physics/data/real_world/colorado_river_grand_canyon_rowing/terrain/production_import_pilot/heightfield_candidate_2017.png");
    Colorado.WaterMaskImage =
        TEXT("physics/data/real_world/colorado_river_grand_canyon_rowing/imagery/production_import_pilot/water_mask_2048.png");
    Colorado.VegetationMaskImage =
        TEXT("physics/data/real_world/colorado_river_grand_canyon_rowing/imagery/production_import_pilot/vegetation_mask_2048.png");
    Colorado.ElevationSample =
        TEXT("physics/data/real_world/colorado_river_grand_canyon_rowing/terrain/production_import_pilot/3dep_tiles");
    Colorado.SourceDrapeDescription =
        TEXT("stitched Colorado/Lees Ferry production-import pilot source drape generated from four official USDA/APFO NAIP 2048px tiles, plus stitched USGS 3DEP pilot DEM relief and a review-gated 2017px heightfield candidate sampled into canyon bank preview geometry; pilot source water/vegetation masks are sampled into terrain color, source-aware terrain photo mottle/microrelief, source-conditioned far-bank albedo/microrelief calibration, first-party photographic color-grade palette compression, broad-slope terrain exposure fill and relief, source-aware macro terrain ridge/facet relief, source-aware terrain slope facet texture, first-party source-aware terrain surface granularity, source-aware riparian canopy mass texture, minimized source overlay plate artifacts, graphic waterline ribbon demotion, remaining water overlay slab demotion, long dark water streak demotion, current streak and waterline rail artifact demotion, central water scaffold plate demotion, base-water center guide-stripe breakup, base-water cross-channel breakup, base-water residual center-seam erase, dark micro-ripple artifact demotion, source-aware bank breakup patches, first-party source-masked bank/bar microgeometry, first-party near-field riverbed pebble/debris dressing, first-party irregular shoreline edge breakup, first-party source-masked shoreline lip/overhang edge breakup, first-party terrain material layer facets, first-party Landscape/Nanite material scaffold microfacets/strata/slope occlusion, first-party terrain erosion-rill/bank-gully strips, source-aware boulder wetness/abrasion/sediment facets, biome-specific sparse deadfall/grass/root ecology props, first-party sparse desert scrub silhouettes, sparse desert riparian thicket proxy clusters, first-party instanced procedural desert-thicket/trunk scaffold, first-party procedural-only foliage review path with stylized PCG sample tree meshes disabled, first-party procedural canopy height and massing profile, first-party procedural canopy tone compression and shadow profile, first-party foliage card/canopy artifact demotion, square foliage/source-card artifact demotion, remaining square card cull, first-party foliage crown depth and leaflet breakup, lit water variation, first-party lit water normal-response scaffold, base-water flow-thread texture, flow-cued water foam/slick mottle, flow-dependent hydraulic aeration/spray mats and beads, flow-band depth texture ribbons, flow-aware surface chop/turbidity patches, turbidity-depth patch artifact demotion, first-party water shader depth/reflection/refraction scaffold, source-aware shallow-water clarity/aeration layers, deterministic wet-rock, talus, sparse scrub, boulder placement, mask-aware canyon ground-cover cards, disabled guide-seat raft/oar foreground proxy hooks, river-specific atmospheric backdrop cards, and source-aware sky-gradient/depth layers; all pilot derivatives remain review-gated until metadata review, mosaic/clip, river-mile stationing, hydrologic conditioning, release-aware masks, and guide/oarsman approval pass; rocks, foliage, water, foam, raft, and lighting still include first-party procedural proxy layers");
    Colorado.FlowBandId = TEXT("moderate_release_planning");
    Colorado.FlowBandDisplayName = TEXT("Moderate Release Planning");
    Colorado.FlowBandSource = TEXT("physics/data/real_world/colorado_river_grand_canyon_rowing/flow_presets.json");
    Colorado.FlowVisualDescription =
        TEXT("Default Grand Canyon rowing preview band from release-planning presets; slightly widens the big-water ribbon and strengthens long wave/current cues while release history and guide review remain required.");
    Colorado.FlowReferenceDischargeCfs = 12000.0f;
    Colorado.FlowWidthScale = 1.08f;
    Colorado.FlowFoamScale = 1.15f;
    Colorado.FlowWetBankScale = 1.10f;
    Colorado.FlowCurrentCueScale = 1.15f;
    Colorado.FlowWaterLevelOffsetCm = 8.0f;
    Colorado.WaterColor = FLinearColor(0.320f, 0.255f, 0.175f);
    Colorado.TerrainColor = FLinearColor(0.48f, 0.30f, 0.18f);
    Colorado.RockColor = FLinearColor(0.55f, 0.32f, 0.20f);
    Colorado.FoliageColor = FLinearColor(0.30f, 0.32f, 0.18f);
    Colorado.CanyonHeightCm = 2600.0f;
    Colorado.RiverHalfWidthCm = 520.0f;
    Colorado.BankWidthCm = 1500.0f;
    Colorado.BendAmplitudeCm = 360.0f;
    Colorado.TerrainReliefAmplitudeCm = 650.0f;
    Colorado.HeightfieldPreviewAmplitudeCm = 2200.0f;
    Colorado.HeightfieldLocalReliefAmplitudeCm = 1500.0f;
    Colorado.HeightfieldSeamFeatherUv = 0.035f;
    Colorado.TerrainNormalSofteningBlend = 0.38f;
    Colorado.BoulderCount = 20;
    Colorado.FoliageCount = 16;
    Colorado.FoamTrainCount = 9;
    Colorado.bDesertCanyon = true;
    Specs.Add(Colorado);

    FRaftSimEnvironmentPreviewSpec Pacuare;
    Pacuare.RiverId = TEXT("pacuare");
    Pacuare.DisplayName = TEXT("Pacuare River Rainforest");
    Pacuare.MapPackagePath = TEXT("/Game/RaftSim/Maps/EnvironmentPreviews/L_PacuareRainforest_PhotorealPreview");
    Pacuare.SourceManifest = TEXT("physics/data/real_world/pacuare_river_costa_rica/source_manifest.json");
    Pacuare.AerialDrapeImage =
        TEXT("physics/data/real_world/pacuare_river_costa_rica/imagery/production_import_pilot/sentinel_augmented_source_drape_preview_4096.png");
    Pacuare.TerrainReliefImage =
        TEXT("physics/data/real_world/pacuare_river_costa_rica/terrain/production_import_pilot/dem_relief_2048.png");
    Pacuare.HeightfieldPreviewImage =
        TEXT("physics/data/real_world/pacuare_river_costa_rica/terrain/production_import_pilot/heightfield_candidate_2017.png");
    Pacuare.WaterMaskImage =
        TEXT("physics/data/real_world/pacuare_river_costa_rica/imagery/production_import_pilot/water_mask_2048.png");
    Pacuare.VegetationMaskImage =
        TEXT("physics/data/real_world/pacuare_river_costa_rica/imagery/production_import_pilot/vegetation_mask_2048.png");
    Pacuare.ElevationSample =
        TEXT("physics/data/real_world/pacuare_river_costa_rica/terrain/copernicus_dem_glo30_N09_W084.tif; physics/data/real_world/pacuare_river_costa_rica/terrain/copernicus_dem_glo30_N10_W084.tif");
    Pacuare.SourceDrapeDescription =
        TEXT("review-gated Pacuare Sentinel-augmented preview calibration drape generated from the coarse NASA GIBS/Copernicus 4096px placeholder plus low-opacity March 20 2025 Sentinel bbox clip color/detail; this is an Unreal preview input only, not a production source-drape replacement, route imagery claim, mask source, photoreal material source, or lifelike evidence; DEM relief, heightfield, and masks remain the production-import derivative placeholders until higher-resolution cloud-screened imagery, local hydrology/hydrography, protected-area review, and guide/outfitter validation are attached; first-party procedural rainforest leaf-litter, wet-rock, talus, mist, source-aware terrain photo mottle/microrelief, source-conditioned far-bank albedo/microrelief calibration, first-party photographic color-grade palette compression, broad-slope terrain exposure fill and relief, source-aware macro terrain ridge/facet relief, source-aware terrain slope facet texture, first-party source-aware terrain surface granularity, source-aware riparian canopy mass texture, minimized source overlay plate artifacts, graphic waterline ribbon demotion, remaining water overlay slab demotion, long dark water streak demotion, current streak and waterline rail artifact demotion, central water scaffold plate demotion, base-water center guide-stripe breakup, base-water cross-channel breakup, base-water residual center-seam erase, dark micro-ripple artifact demotion, source-aware bank breakup patches, first-party source-masked bank/bar microgeometry, first-party near-field riverbed pebble/debris dressing, first-party irregular shoreline edge breakup, first-party source-masked shoreline lip/overhang edge breakup, first-party terrain material layer facets, first-party Landscape/Nanite material scaffold microfacets/strata/slope occlusion, first-party terrain erosion-rill/bank-gully strips, source-aware boulder wetness/abrasion/moss facets, biome-specific deadfall/log/grass/root ecology props, rainforest canopy/vine silhouette cards, dense layered rainforest canopy/understory proxy clusters, first-party instanced procedural rainforest canopy/trunk/understory scaffold, first-party procedural-only foliage review path with stylized PCG sample tree meshes disabled, first-party procedural canopy height and massing profile, first-party procedural canopy tone compression and shadow profile, first-party foliage card/canopy artifact demotion, square foliage/source-card artifact demotion, remaining square card cull, first-party organic branch/frond lattice foliage, first-party fine twig canopy lace foliage, first-party foliage crown depth and leaflet breakup, waterfall curtain/plunge-mist proxy layers, lit water variation, first-party lit water normal-response scaffold, base-water flow-thread texture, flow-cued water foam/slick mottle, flow-dependent hydraulic aeration/spray mats and beads, flow-band depth texture ribbons, flow-aware surface chop/turbidity patches, turbidity-depth patch artifact demotion, first-party water shader depth/reflection/refraction scaffold, source-aware shallow-water clarity/aeration layers, dense mask-aware ground-cover/canopy cards, disabled guide-seat raft/oar foreground proxy hooks, humid atmospheric backdrop cards, and source-aware sky-gradient/depth layers remain rights-safe proxy dressing; rocks, foliage, water, foam, raft, and lighting still include first-party procedural proxy layers");
    Pacuare.FlowBandId = TEXT("rainfed_runnable_planning");
    Pacuare.FlowBandDisplayName = TEXT("Rain-Fed Runnable Planning");
    Pacuare.FlowBandSource = TEXT("physics/data/real_world/pacuare_river_costa_rica/flow_presets.json");
    Pacuare.FlowVisualDescription =
        TEXT("Default Pacuare planning band uses relative rainfed-runnable context only; numeric discharge stays unset until Costa Rica gauge, rainfall, flash-response, and guide review clear it.");
    Pacuare.FlowWidthScale = 1.05f;
    Pacuare.FlowFoamScale = 1.20f;
    Pacuare.FlowWetBankScale = 1.20f;
    Pacuare.FlowCurrentCueScale = 1.18f;
    Pacuare.FlowWaterLevelOffsetCm = 7.0f;
    Pacuare.WaterColor = FLinearColor(0.050f, 0.190f, 0.095f);
    Pacuare.TerrainColor = FLinearColor(0.17f, 0.22f, 0.13f);
    Pacuare.RockColor = FLinearColor(0.20f, 0.24f, 0.20f);
    Pacuare.FoliageColor = FLinearColor(0.035f, 0.20f, 0.055f);
    Pacuare.CanyonHeightCm = 1450.0f;
    Pacuare.RiverHalfWidthCm = 305.0f;
    Pacuare.BankWidthCm = 680.0f;
    Pacuare.BendAmplitudeCm = 340.0f;
    Pacuare.TerrainReliefAmplitudeCm = 420.0f;
    Pacuare.HeightfieldPreviewAmplitudeCm = 1500.0f;
    Pacuare.HeightfieldLocalReliefAmplitudeCm = 1050.0f;
    Pacuare.HeightfieldSeamFeatherUv = 0.035f;
    Pacuare.TerrainNormalSofteningBlend = 0.42f;
    Pacuare.BoulderCount = 22;
    Pacuare.FoliageCount = 62;
    Pacuare.FoamTrainCount = 16;
    Pacuare.bHasWaterfalls = true;
    Specs.Add(Pacuare);

    FRaftSimEnvironmentPreviewSpec Zambezi;
    Zambezi.RiverId = TEXT("zambezi_batoka_gorge");
    Zambezi.DisplayName = TEXT("Zambezi River Batoka Gorge");
    Zambezi.MapPackagePath = TEXT("/Game/RaftSim/Maps/EnvironmentPreviews/L_ZambeziBatokaGorge_PhotorealPreview");
    Zambezi.SourceManifest =
        TEXT("physics/data/real_world/zambezi_batoka_gorge/production_corridor/boiling_pot_to_mukuni_beach/manifest.json");
    Zambezi.AerialDrapeImage =
        TEXT("physics/data/real_world/zambezi_batoka_gorge/production_corridor/boiling_pot_to_mukuni_beach/derived/source_albedo_2048.png");
    Zambezi.TerrainReliefImage =
        TEXT("physics/data/real_world/zambezi_batoka_gorge/production_corridor/boiling_pot_to_mukuni_beach/derived/dem_relief_2048.png");
    Zambezi.HeightfieldPreviewImage =
        TEXT("physics/data/real_world/zambezi_batoka_gorge/production_corridor/boiling_pot_to_mukuni_beach/derived/heightfield_2017.png");
    Zambezi.WaterMaskImage =
        TEXT("physics/data/real_world/zambezi_batoka_gorge/production_corridor/boiling_pot_to_mukuni_beach/derived/water_mask_2048.png");
    Zambezi.VegetationMaskImage =
        TEXT("physics/data/real_world/zambezi_batoka_gorge/production_corridor/boiling_pot_to_mukuni_beach/derived/vegetation_mask_2048.png");
    Zambezi.ElevationSample =
        TEXT("physics/data/real_world/zambezi_batoka_gorge/terrain/source/copernicus_dem_glo30_S18_E025.tif");
    Zambezi.SourceDrapeDescription =
        TEXT("Route-clipped 10 m Copernicus Sentinel-2 visual mosaic and 30 m Copernicus DEM GLO-30 terrain for the published 30 km Boiling Pot-to-Mukuni Beach Batoka Gorge corridor; source geometry and exact bank access remain guide/geospatial review-gated, while first-party basalt, gorge woodland, foam, spray, mist, and water materials remain technical candidates until lifelike approval.");
    Zambezi.FlowBandId = TEXT("normal_big_water");
    Zambezi.FlowBandDisplayName = TEXT("Normal Big Water Planning");
    Zambezi.FlowBandSource =
        TEXT("physics/data/real_world/zambezi_batoka_gorge/production_corridor/boiling_pot_to_mukuni_beach/hydrology/seasonal_flow_context.json");
    Zambezi.FlowVisualDescription =
        TEXT("Victoria Falls Nana's Farm planning context drives a bounded normal-big-water visual candidate; rapid-specific hole washout, closure seasons, and station lag require local guide review.");
    Zambezi.FlowWidthScale = 1.20f;
    Zambezi.FlowFoamScale = 1.35f;
    Zambezi.FlowWetBankScale = 1.18f;
    Zambezi.FlowCurrentCueScale = 1.35f;
    Zambezi.FlowWaterLevelOffsetCm = 12.0f;
    Zambezi.WaterColor = FLinearColor(0.20f, 0.23f, 0.105f);
    Zambezi.TerrainColor = FLinearColor(0.30f, 0.22f, 0.15f);
    Zambezi.RockColor = FLinearColor(0.18f, 0.17f, 0.15f);
    Zambezi.FoliageColor = FLinearColor(0.19f, 0.25f, 0.10f);
    Zambezi.CanyonHeightCm = 3000.0f;
    Zambezi.RiverHalfWidthCm = 6000.0f;
    Zambezi.BankWidthCm = 22000.0f;
    Zambezi.BendAmplitudeCm = 600.0f;
    Zambezi.TerrainReliefAmplitudeCm = 1600.0f;
    Zambezi.HeightfieldPreviewAmplitudeCm = 37353.0f;
    Zambezi.HeightfieldLocalReliefAmplitudeCm = 16000.0f;
    Zambezi.HeightfieldSeamFeatherUv = 0.025f;
    Zambezi.TerrainNormalSofteningBlend = 0.32f;
    Zambezi.BoulderCount = 120;
    Zambezi.FoliageCount = 220;
    Zambezi.FoamTrainCount = 36;
    Zambezi.bDesertCanyon = true;
    Specs.Add(Zambezi);

    FRaftSimEnvironmentPreviewSpec Futaleufu;
    Futaleufu.RiverId = TEXT("futaleufu_terminator");
    Futaleufu.DisplayName = TEXT("Futaleufu Terminator Section");
    Futaleufu.MapPackagePath = TEXT("/Game/RaftSim/Maps/EnvironmentPreviews/L_FutaleufuTerminator_PhotorealPreview");
    Futaleufu.SourceManifest =
        TEXT("physics/data/real_world/futaleufu_river_chile/production_corridor/rio_azul_swinging_bridge_to_pasarela/manifest.json");
    Futaleufu.AerialDrapeImage =
        TEXT("physics/data/real_world/futaleufu_river_chile/production_corridor/rio_azul_swinging_bridge_to_pasarela/derived/source_albedo_2048.png");
    Futaleufu.TerrainReliefImage =
        TEXT("physics/data/real_world/futaleufu_river_chile/production_corridor/rio_azul_swinging_bridge_to_pasarela/derived/dem_relief_2048.png");
    Futaleufu.HeightfieldPreviewImage =
        TEXT("physics/data/real_world/futaleufu_river_chile/production_corridor/rio_azul_swinging_bridge_to_pasarela/derived/heightfield_2017.png");
    Futaleufu.WaterMaskImage =
        TEXT("physics/data/real_world/futaleufu_river_chile/production_corridor/rio_azul_swinging_bridge_to_pasarela/derived/water_mask_2048.png");
    Futaleufu.VegetationMaskImage =
        TEXT("physics/data/real_world/futaleufu_river_chile/production_corridor/rio_azul_swinging_bridge_to_pasarela/derived/vegetation_mask_2048.png");
    Futaleufu.ElevationSample =
        TEXT("physics/data/real_world/futaleufu_river_chile/terrain/source/copernicus_dem_glo30_S44_W073.tif");
    Futaleufu.SourceDrapeDescription =
        TEXT("Route-clipped near-cloud-free 10 m Copernicus Sentinel-2 visual mosaic and 30 m Copernicus DEM GLO-30 terrain from the Rio Azul track bridge through the confluence to the downstream Pasarela bridge; exact access and line stations remain guide/geospatial review-gated, while first-party granite, temperate rainforest, turquoise water, foam, and spray materials remain technical candidates until lifelike approval.");
    Futaleufu.FlowBandId = TEXT("normal_runnable");
    Futaleufu.FlowBandDisplayName = TEXT("Normal Runnable Planning");
    Futaleufu.FlowBandSource =
        TEXT("physics/data/real_world/futaleufu_river_chile/production_corridor/rio_azul_swinging_bridge_to_pasarela/hydrology/seasonal_flow_context.json");
    Futaleufu.FlowVisualDescription =
        TEXT("DGA monthly flow context drives a bounded normal-runnable visual candidate; time-series acquisition, upstream translation, snowmelt/rain interpretation, and guide validation remain required.");
    Futaleufu.FlowWidthScale = 1.12f;
    Futaleufu.FlowFoamScale = 1.32f;
    Futaleufu.FlowWetBankScale = 1.22f;
    Futaleufu.FlowCurrentCueScale = 1.38f;
    Futaleufu.FlowWaterLevelOffsetCm = 10.0f;
    Futaleufu.WaterColor = FLinearColor(0.025f, 0.31f, 0.34f);
    Futaleufu.TerrainColor = FLinearColor(0.16f, 0.23f, 0.16f);
    Futaleufu.RockColor = FLinearColor(0.37f, 0.39f, 0.38f);
    Futaleufu.FoliageColor = FLinearColor(0.055f, 0.25f, 0.105f);
    Futaleufu.CanyonHeightCm = 4200.0f;
    Futaleufu.RiverHalfWidthCm = 4800.0f;
    Futaleufu.BankWidthCm = 18000.0f;
    Futaleufu.BendAmplitudeCm = 650.0f;
    Futaleufu.TerrainReliefAmplitudeCm = 2200.0f;
    Futaleufu.HeightfieldPreviewAmplitudeCm = 167895.0f;
    Futaleufu.HeightfieldLocalReliefAmplitudeCm = 24000.0f;
    Futaleufu.HeightfieldSeamFeatherUv = 0.025f;
    Futaleufu.TerrainNormalSofteningBlend = 0.28f;
    Futaleufu.BoulderCount = 160;
    Futaleufu.FoliageCount = 520;
    Futaleufu.FoamTrainCount = 32;
    Specs.Add(Futaleufu);

    FRaftSimEnvironmentPreviewSpec Chilko;
    Chilko.RiverId = TEXT("chilko_river_lava_canyon");
    Chilko.DisplayName = TEXT("Chilko River Lodge to Chilko-Taseko Junction");
    Chilko.MapPackagePath = TEXT("/Game/RaftSim/Maps/EnvironmentPreviews/L_ChilkoRiver_PhotorealPreview");
    Chilko.SourceManifest =
        TEXT("physics/data/real_world/chilko_river_bc/production_corridor/chilko_river_lodge_to_taseko_junction/manifest.json");
    Chilko.AerialDrapeImage =
        TEXT("physics/data/real_world/chilko_river_bc/production_corridor/chilko_river_lodge_to_taseko_junction/derived/source_albedo_2048.png");
    Chilko.TerrainReliefImage =
        TEXT("physics/data/real_world/chilko_river_bc/production_corridor/chilko_river_lodge_to_taseko_junction/derived/dem_relief_2048.png");
    Chilko.HeightfieldPreviewImage =
        TEXT("physics/data/real_world/chilko_river_bc/production_corridor/chilko_river_lodge_to_taseko_junction/derived/heightfield_2017.png");
    Chilko.WaterMaskImage =
        TEXT("physics/data/real_world/chilko_river_bc/production_corridor/chilko_river_lodge_to_taseko_junction/derived/water_mask_2048.png");
    Chilko.VegetationMaskImage =
        TEXT("physics/data/real_world/chilko_river_bc/production_corridor/chilko_river_lodge_to_taseko_junction/derived/vegetation_mask_2048.png");
    Chilko.ElevationSample =
        TEXT("physics/data/real_world/chilko_river_bc/source/terrain/nrcan_mrdem30_chilko_corridor_dtm.tif");
    Chilko.SourceDrapeDescription =
        TEXT("Deterministically stitched official BC Freshwater Atlas route with a bounded 30 m NRCan MRDEM DTM/source clip and cloud-free 10 m Copernicus Sentinel-2 true-color corridor window; exact access, rapid-scale terrain and bathymetry, named rapid stations, numeric gameplay flow bands, guide approval, and land/publication review remain explicit blockers.");
    Chilko.FlowBandId = TEXT("summer_seasonal_context_review");
    Chilko.FlowBandDisplayName = TEXT("Summer Seasonal Context Review");
    Chilko.FlowBandSource =
        TEXT("physics/data/real_world/chilko_river_bc/hydrology/seasonal_flow_context.json");
    Chilko.FlowVisualDescription =
        TEXT("Official ECCC monthly history supports seasonal context only; no gameplay discharge threshold or rapid-specific stickiness, washout, or hazard response is approved.");
    Chilko.FlowWidthScale = 1.10f;
    Chilko.FlowFoamScale = 1.24f;
    Chilko.FlowWetBankScale = 1.16f;
    Chilko.FlowCurrentCueScale = 1.28f;
    Chilko.FlowWaterLevelOffsetCm = 8.0f;
    Chilko.WaterColor = FLinearColor(0.025f, 0.27f, 0.30f);
    Chilko.TerrainColor = FLinearColor(0.24f, 0.27f, 0.19f);
    Chilko.RockColor = FLinearColor(0.34f, 0.35f, 0.32f);
    Chilko.FoliageColor = FLinearColor(0.10f, 0.24f, 0.09f);
    Chilko.CanyonHeightCm = 3200.0f;
    Chilko.RiverHalfWidthCm = 4500.0f;
    Chilko.BankWidthCm = 16000.0f;
    Chilko.BendAmplitudeCm = 620.0f;
    Chilko.TerrainReliefAmplitudeCm = 1800.0f;
    Chilko.HeightfieldPreviewAmplitudeCm = 70353.516f;
    Chilko.HeightfieldLocalReliefAmplitudeCm = 22000.0f;
    Chilko.HeightfieldSeamFeatherUv = 0.025f;
    Chilko.TerrainNormalSofteningBlend = 0.30f;
    Chilko.BoulderCount = 140;
    Chilko.FoliageCount = 360;
    Chilko.FoamTrainCount = 28;
    Specs.Add(Chilko);

    return Specs;
}

TArray<FRaftSimLandscapeImportCandidateSpec> GetLandscapeImportCandidateSpecs()
{
    TArray<FRaftSimLandscapeImportCandidateSpec> Candidates;
    for (const FRaftSimEnvironmentPreviewSpec& PreviewSpec : GetEnvironmentPreviewSpecs())
    {
        FRaftSimLandscapeImportCandidateSpec Candidate;
        Candidate.PreviewSpec = PreviewSpec;
        Candidate.HorizontalSpanYCm = PreviewSpec.bDesertCanyon ? 8600.0f : 5500.0f;
        Candidate.TargetReliefCm = PreviewSpec.HeightfieldPreviewAmplitudeCm;

        if (PreviewSpec.RiverId == TEXT("american_south_fork"))
        {
            Candidate.HeightfieldRelativePath =
                TEXT("physics/data/real_world/south_fork_american_chili_bar/production_corridor/chili_bar_reach_0_2500m/derived/south_fork_chili_bar_reach_heightfield_2017.png");
            Candidate.HeightfieldManifestRelativePath =
                TEXT("physics/data/real_world/south_fork_american_chili_bar/production_corridor/chili_bar_reach_0_2500m/manifest.json");
            Candidate.ImportContractRelativePath =
                TEXT("physics/data/real_world/south_fork_american_chili_bar/production_corridor/chili_bar_reach_0_2500m/manifest.json");
            Candidate.LocalCenterlineRelativePath =
                TEXT("physics/data/real_world/south_fork_american_chili_bar/production_corridor/chili_bar_reach_0_2500m/centerline_local.json");
            Candidate.MapPackagePath =
                TEXT("/Game/RaftSim/Maps/EnvironmentPreviews/LandscapeCandidates/L_SouthForkAmerican_PhysicalCorridorCandidate");
            Candidate.LandscapeSize = 2017;
            Candidate.HorizontalSpanXCm = 240429.501f;
            Candidate.HorizontalSpanYCm = 169741.536f;
            Candidate.TargetReliefCm = 38118.896f;
            Candidate.bApplyPreviewAnalyticChannelBurn = false;
            Candidate.bUseSolverVisualizationFields = false;
            Candidate.bPhysicalScaleSourceCorridor = true;
            Candidate.bEnableLandscapeNanite = false;
            Candidate.PreviewSpec.RiverHalfWidthCm = 1100.0f;
            Candidate.PreviewSpec.BankWidthCm = 5200.0f;
        }
        else if (PreviewSpec.RiverId == TEXT("colorado_river"))
        {
            Candidate.HeightfieldRelativePath =
                TEXT("physics/data/real_world/colorado_river_grand_canyon_rowing/production_corridor/lees_ferry_reach_2200_4700m/derived/colorado_lees_ferry_reach_heightfield_2017.png");
            Candidate.HeightfieldManifestRelativePath =
                TEXT("physics/data/real_world/colorado_river_grand_canyon_rowing/production_corridor/lees_ferry_reach_2200_4700m/manifest.json");
            Candidate.ImportContractRelativePath =
                TEXT("physics/data/real_world/colorado_river_grand_canyon_rowing/production_corridor/lees_ferry_reach_2200_4700m/manifest.json");
            Candidate.LocalCenterlineRelativePath =
                TEXT("physics/data/real_world/colorado_river_grand_canyon_rowing/production_corridor/lees_ferry_reach_2200_4700m/centerline_local.json");
            Candidate.MapPackagePath =
                TEXT("/Game/RaftSim/Maps/EnvironmentPreviews/LandscapeCandidates/L_ColoradoGrandCanyon_PhysicalCorridorCandidate");
            Candidate.LandscapeSize = 2017;
            Candidate.HorizontalSpanXCm = 296889.772f;
            Candidate.HorizontalSpanYCm = 203765.214f;
            Candidate.TargetReliefCm = 49316.565f;
            Candidate.bApplyPreviewAnalyticChannelBurn = false;
            Candidate.bUseSolverVisualizationFields = false;
            Candidate.bPhysicalScaleSourceCorridor = true;
            Candidate.bEnableLandscapeNanite = false;
            Candidate.PreviewSpec.RiverHalfWidthCm = 6000.0f;
            Candidate.PreviewSpec.BankWidthCm = 24000.0f;
        }
        else if (PreviewSpec.RiverId == TEXT("pacuare"))
        {
            Candidate.HeightfieldRelativePath =
                TEXT("physics/data/real_world/pacuare_river_costa_rica/terrain/pacuare_copernicus_dem_corridor_heightfield_1009.png");
            Candidate.HeightfieldManifestRelativePath =
                TEXT("physics/data/real_world/pacuare_river_costa_rica/terrain/pacuare_copernicus_dem_corridor_heightfield_manifest.json");
            Candidate.ImportContractRelativePath =
                TEXT("unreal/Content/RaftSim/River/pacuare_heightfield_import_test.json");
            Candidate.MapPackagePath =
                TEXT("/Game/RaftSim/Maps/EnvironmentPreviews/LandscapeCandidates/L_Pacuare_SourceLandscapeCandidate");
        }
        else if (PreviewSpec.RiverId == TEXT("zambezi_batoka_gorge"))
        {
            Candidate.HeightfieldRelativePath =
                TEXT("physics/data/real_world/zambezi_batoka_gorge/production_corridor/boiling_pot_to_mukuni_beach/derived/heightfield_2017.png");
            Candidate.HeightfieldManifestRelativePath = PreviewSpec.SourceManifest;
            Candidate.ImportContractRelativePath = PreviewSpec.SourceManifest;
            Candidate.LocalCenterlineRelativePath =
                TEXT("physics/data/real_world/zambezi_batoka_gorge/production_corridor/boiling_pot_to_mukuni_beach/hydrography/centerline_local.json");
            Candidate.MapPackagePath =
                TEXT("/Game/RaftSim/Maps/EnvironmentPreviews/LandscapeCandidates/L_ZambeziBatokaGorge_PhysicalCorridorCandidate");
            Candidate.LandscapeSize = 2017;
            Candidate.HorizontalSpanXCm = 2025477.591f;
            Candidate.HorizontalSpanYCm = 1252708.111f;
            Candidate.TargetReliefCm = 37353.015f;
            Candidate.bApplyPreviewAnalyticChannelBurn = false;
            Candidate.bUseSolverVisualizationFields = false;
            Candidate.bPhysicalScaleSourceCorridor = true;
            Candidate.bEnableLandscapeNanite = false;
        }
        else if (PreviewSpec.RiverId == TEXT("futaleufu_terminator"))
        {
            Candidate.HeightfieldRelativePath =
                TEXT("physics/data/real_world/futaleufu_river_chile/production_corridor/rio_azul_swinging_bridge_to_pasarela/derived/heightfield_2017.png");
            Candidate.HeightfieldManifestRelativePath = PreviewSpec.SourceManifest;
            Candidate.ImportContractRelativePath = PreviewSpec.SourceManifest;
            Candidate.LocalCenterlineRelativePath =
                TEXT("physics/data/real_world/futaleufu_river_chile/production_corridor/rio_azul_swinging_bridge_to_pasarela/hydrography/centerline_local.json");
            Candidate.MapPackagePath =
                TEXT("/Game/RaftSim/Maps/EnvironmentPreviews/LandscapeCandidates/L_FutaleufuTerminator_PhysicalCorridorCandidate");
            Candidate.LandscapeSize = 2017;
            Candidate.HorizontalSpanXCm = 1006390.921f;
            Candidate.HorizontalSpanYCm = 836476.459f;
            Candidate.TargetReliefCm = 167894.690f;
            Candidate.bApplyPreviewAnalyticChannelBurn = false;
            Candidate.bUseSolverVisualizationFields = false;
            Candidate.bPhysicalScaleSourceCorridor = true;
            Candidate.bEnableLandscapeNanite = false;
        }
        else if (PreviewSpec.RiverId == TEXT("chilko_river_lava_canyon"))
        {
            Candidate.HeightfieldRelativePath =
                TEXT("physics/data/real_world/chilko_river_bc/production_corridor/chilko_river_lodge_to_taseko_junction/derived/heightfield_1009.png");
            Candidate.HeightfieldManifestRelativePath = PreviewSpec.SourceManifest;
            Candidate.ImportContractRelativePath =
                TEXT("unreal/Content/RaftSim/River/chilko_heightfield_import_test.json");
            Candidate.LocalCenterlineRelativePath =
                TEXT("physics/data/real_world/chilko_river_bc/production_corridor/chilko_river_lodge_to_taseko_junction/hydrography/centerline_local.json");
            Candidate.MapPackagePath =
                TEXT("/Game/RaftSim/Maps/EnvironmentPreviews/LandscapeCandidates/L_ChilkoRiver_PhysicalCorridorCandidate");
            Candidate.LandscapeSize = 1009;
            Candidate.HorizontalSpanXCm = 3390375.792f;
            Candidate.HorizontalSpanYCm = 3878909.999f;
            Candidate.TargetReliefCm = 70353.516f;
            Candidate.bApplyPreviewAnalyticChannelBurn = false;
            Candidate.bUseSolverVisualizationFields = false;
            Candidate.bPhysicalScaleSourceCorridor = true;
            Candidate.bEnableLandscapeNanite = true;
        }
        else
        {
            continue;
        }

        Candidate.PreviewSpec.MapPackagePath = Candidate.MapPackagePath;
        Candidates.Add(MoveTemp(Candidate));
    }
    return Candidates;
}

FRaftSimLandscapeMaterialCandidateSettings GetLandscapeMaterialCandidateSettings(const FString& RiverId)
{
    FRaftSimLandscapeMaterialCandidateSettings Settings;
    if (RiverId == TEXT("american_south_fork"))
    {
        Settings.DetailMappingScale = 128.0f;
    }
    else if (RiverId == TEXT("colorado_river"))
    {
        Settings.DetailMappingScale = 144.0f;
        Settings.DetailAlbedoWeight = 0.16f;
        Settings.DetailNormalWeight = 0.28f;
        Settings.EmissiveFillScale = 0.035f;
        Settings.SpecularLevel = 0.14f;
        Settings.RiverbedBlendWeight = 0.78f;
        Settings.WetBankBlendWeight = 0.58f;
        Settings.RiverbedRoughness = 0.84f;
        Settings.RiverbedColorScale = FLinearColor(0.36f, 0.28f, 0.20f, 0.0f);
        Settings.WetBankColorScale = FLinearColor(0.58f, 0.44f, 0.34f, 0.0f);
    }
    else if (RiverId == TEXT("pacuare"))
    {
        Settings.DetailMappingScale = 112.0f;
        Settings.DetailAlbedoWeight = 0.20f;
        Settings.DetailNormalWeight = 0.36f;
        Settings.DetailSurfaceResponseWeight = 0.32f;
        Settings.EmissiveFillScale = 0.055f;
        Settings.RiverbedBlendWeight = 0.84f;
        Settings.WetBankBlendWeight = 0.72f;
        Settings.RiverbedRoughness = 0.72f;
        Settings.RiverbedColorScale = FLinearColor(0.22f, 0.30f, 0.24f, 0.0f);
        Settings.WetBankColorScale = FLinearColor(0.42f, 0.50f, 0.40f, 0.0f);
    }
    else if (RiverId == TEXT("zambezi_batoka_gorge"))
    {
        Settings.DetailMappingScale = 152.0f;
        Settings.DetailAlbedoWeight = 0.14f;
        Settings.DetailNormalWeight = 0.30f;
        Settings.EmissiveFillScale = 0.040f;
        Settings.SpecularLevel = 0.13f;
        Settings.RiverbedBlendWeight = 0.74f;
        Settings.WetBankBlendWeight = 0.62f;
        Settings.RiverbedRoughness = 0.86f;
        Settings.RiverbedColorScale = FLinearColor(0.20f, 0.20f, 0.16f, 0.0f);
        Settings.WetBankColorScale = FLinearColor(0.36f, 0.38f, 0.30f, 0.0f);
    }
    else if (RiverId == TEXT("futaleufu_terminator"))
    {
        Settings.DetailMappingScale = 116.0f;
        Settings.DetailAlbedoWeight = 0.18f;
        Settings.DetailNormalWeight = 0.38f;
        Settings.DetailSurfaceResponseWeight = 0.34f;
        Settings.EmissiveFillScale = 0.050f;
        Settings.RiverbedBlendWeight = 0.86f;
        Settings.WetBankBlendWeight = 0.74f;
        Settings.RiverbedRoughness = 0.74f;
        Settings.RiverbedColorScale = FLinearColor(0.28f, 0.34f, 0.32f, 0.0f);
        Settings.WetBankColorScale = FLinearColor(0.44f, 0.52f, 0.48f, 0.0f);
    }
    else if (RiverId == TEXT("chilko_river_lava_canyon"))
    {
        Settings.DetailMappingScale = 124.0f;
        Settings.DetailAlbedoWeight = 0.17f;
        Settings.DetailNormalWeight = 0.34f;
        Settings.DetailSurfaceResponseWeight = 0.30f;
        Settings.EmissiveFillScale = 0.045f;
        Settings.RiverbedBlendWeight = 0.82f;
        Settings.WetBankBlendWeight = 0.70f;
        Settings.RiverbedRoughness = 0.76f;
        Settings.RiverbedColorScale = FLinearColor(0.30f, 0.35f, 0.32f, 0.0f);
        Settings.WetBankColorScale = FLinearColor(0.42f, 0.49f, 0.42f, 0.0f);
    }
    return Settings;
}

FString MakeFlowVariantPreviewMapPackagePath(const FRaftSimEnvironmentPreviewSpec& BaseSpec)
{
    const FString BaseDirectory = FPaths::GetPath(BaseSpec.MapPackagePath);
    const FString BaseName = FPackageName::GetShortName(BaseSpec.MapPackagePath);
    return FPaths::Combine(
        BaseDirectory,
        TEXT("FlowVariants"),
        FString::Printf(TEXT("%s_%s"), *BaseName, *BaseSpec.FlowBandId));
}

FRaftSimEnvironmentPreviewSpec MakeFlowVariantPreviewSpec(
    const FRaftSimEnvironmentPreviewSpec& BaseSpec,
    const FString& FlowBandId,
    const FString& FlowBandDisplayName,
    const FString& FlowVisualDescription,
    float FlowReferenceDischargeCfs,
    float FlowWidthScale,
    float FlowFoamScale,
    float FlowWetBankScale,
    float FlowCurrentCueScale,
    float FlowWaterLevelOffsetCm)
{
    FRaftSimEnvironmentPreviewSpec Variant = BaseSpec;
    Variant.FlowBandId = FlowBandId;
    Variant.FlowBandDisplayName = FlowBandDisplayName;
    Variant.FlowVisualDescription = FlowVisualDescription;
    Variant.FlowReferenceDischargeCfs = FlowReferenceDischargeCfs;
    Variant.FlowWidthScale = FlowWidthScale;
    Variant.FlowFoamScale = FlowFoamScale;
    Variant.FlowWetBankScale = FlowWetBankScale;
    Variant.FlowCurrentCueScale = FlowCurrentCueScale;
    Variant.FlowWaterLevelOffsetCm = FlowWaterLevelOffsetCm;
    Variant.MapPackagePath = MakeFlowVariantPreviewMapPackagePath(Variant);
    return Variant;
}

TArray<FRaftSimEnvironmentPreviewSpec> GetEnvironmentPreviewFlowVariantSpecs()
{
    TArray<FRaftSimEnvironmentPreviewSpec> Variants;
    const TArray<FRaftSimEnvironmentPreviewSpec> BaseSpecs = GetEnvironmentPreviewSpecs();
    for (const FRaftSimEnvironmentPreviewSpec& BaseSpec : BaseSpecs)
    {
        if (BaseSpec.RiverId == TEXT("american_south_fork"))
        {
            Variants.Add(MakeFlowVariantPreviewSpec(
                BaseSpec,
                TEXT("low_runnable"),
                TEXT("Low Runnable"),
                TEXT("South Fork low-runnable review band: expose more rocks and shallows, tighten tongues, reduce foam, and preserve rescue/hazard readability before guide approval."),
                900.0f,
                0.92f,
                0.75f,
                0.85f,
                0.82f,
                -8.0f));
            Variants.Add(MakeFlowVariantPreviewSpec(
                BaseSpec,
                TEXT("median_runnable"),
                TEXT("Median Runnable / Summer Commercial"),
                TEXT("South Fork median summer-commercial review band with readable tongues, wet rocks, eddy lines, and moderate wave trains."),
                1600.0f,
                1.0f,
                1.0f,
                1.0f,
                1.0f,
                0.0f));
            Variants.Add(MakeFlowVariantPreviewSpec(
                BaseSpec,
                TEXT("high_runnable"),
                TEXT("High Runnable"),
                TEXT("South Fork high-water review band: raise wet banks, strengthen laterals and wave trains, and keep boulder hazards visible instead of visually washing them away."),
                3000.0f,
                1.12f,
                1.25f,
                1.25f,
                1.25f,
                12.0f));
        }
        else if (BaseSpec.RiverId == TEXT("colorado_river"))
        {
            Variants.Add(MakeFlowVariantPreviewSpec(
                BaseSpec,
                TEXT("low_release_planning"),
                TEXT("Low Release Planning"),
                TEXT("Colorado low-release planning band with more exposed bars and sharper ferry setup while preserving big-water scale and swimmer visibility."),
                8000.0f,
                0.96f,
                0.85f,
                0.88f,
                0.90f,
                -6.0f));
            Variants.Add(MakeFlowVariantPreviewSpec(
                BaseSpec,
                TEXT("moderate_release_planning"),
                TEXT("Moderate Release Planning"),
                TEXT("Colorado moderate-release planning band with longer tongues, lateral waves, broad current streaks, and default oar-rig sightline readability."),
                12000.0f,
                1.08f,
                1.15f,
                1.10f,
                1.15f,
                8.0f));
            Variants.Add(MakeFlowVariantPreviewSpec(
                BaseSpec,
                TEXT("high_release_planning"),
                TEXT("High Release Planning"),
                TEXT("Colorado high-release review band with faster big-water read, stronger wave trains, eddy fences, and inspectable shore/rescue cues."),
                18000.0f,
                1.18f,
                1.35f,
                1.30f,
                1.35f,
                18.0f));
        }
        else if (BaseSpec.RiverId == TEXT("pacuare"))
        {
            Variants.Add(MakeFlowVariantPreviewSpec(
                BaseSpec,
                TEXT("clear_season_low_planning"),
                TEXT("Clear-Season Low Planning"),
                TEXT("Pacuare clear-season low planning band with exposed rocks, tighter tongues, clearer shallow-water cues, and reduced bank-pressure visuals."),
                -1.0f,
                0.90f,
                0.80f,
                0.88f,
                0.82f,
                -9.0f));
            Variants.Add(MakeFlowVariantPreviewSpec(
                BaseSpec,
                TEXT("rainfed_runnable_planning"),
                TEXT("Rain-Fed Runnable Planning"),
                TEXT("Pacuare rainfed runnable planning band with pushy tongues, active wave trains, wet banks, and vegetation pressure after rain."),
                -1.0f,
                1.05f,
                1.20f,
                1.20f,
                1.18f,
                7.0f));
            Variants.Add(MakeFlowVariantPreviewSpec(
                BaseSpec,
                TEXT("rainy_season_high_planning"),
                TEXT("Rainy-Season High Planning"),
                TEXT("Pacuare rainy-season high planning band with faster reaction windows, larger laterals, fewer visible eddies, and stronger swimmer drift cues."),
                -1.0f,
                1.18f,
                1.40f,
                1.35f,
                1.35f,
                20.0f));
            Variants.Add(MakeFlowVariantPreviewSpec(
                BaseSpec,
                TEXT("flash_response_review_only"),
                TEXT("Flash Response Review Only"),
                TEXT("Pacuare flash-response review-only band blocked from playable use until hydrology and guide review define safe visual and gameplay boundaries."),
                -1.0f,
                1.30f,
                1.55f,
                1.50f,
                1.55f,
                34.0f));
        }
    }

    return Variants;
}
} // namespace RaftSimEditorEnvironment
