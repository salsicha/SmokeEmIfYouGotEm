#pragma once

#include "Environment/RaftSimEditorEnvironmentInternal.h"
#include "Engine/PostProcessVolume.h"
#include "Engine/SphereReflectionCapture.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/ReflectionCaptureComponent.h"
#include "Components/SphereReflectionCaptureComponent.h"
#include "Components/VolumetricCloudComponent.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/WorldSettings.h"
#include "HAL/IConsoleManager.h"
#include "RaftSimRaftActor.h"
#include "RaftSimRockObstacleActor.h"
#include "RaftSimRiverWaterConfig.h"
#include "RaftSimWaterSurfaceActor.h"
#include "RenderingThread.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "StaticMeshResources.h"
#include "UObject/SavePackage.h"
#include "WorldPartition/HLOD/HLODLayer.h"
#include "WorldPartition/WorldPartition.h"
#include "WorldPartition/WorldPartitionMiniMap.h"
#include "WorldPartition/WorldPartitionRuntimeHash.h"

// Shared implementation details of the FullReach editor builder and exporter.
namespace RaftSimEditorEnvironment::SouthForkFullReach
{
constexpr TCHAR EnvironmentManifestRelativePath[] = TEXT(
    "physics/data/real_world/south_fork_american_chili_bar/production_corridor/"
         "photoreal_environment/manifest.json");
constexpr TCHAR FullReachMapPackagePath[] = TEXT("/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach");
constexpr TCHAR FullReachInstancedHlodLayerPackagePath[] =
    TEXT("/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach_HLODLayer_Instanced");
constexpr TCHAR CaptureDirectoryRelativePath[] =
    TEXT("docs/environment-captures/south_fork_full_reach");
constexpr float DetailedTerrainHalfWidthM = 112.0f;
constexpr float DetailedPineAnalogRiverDistanceM = 1100.0f;
struct FSouthForkCoordinatePoint
{
    double StationM = 0.0;
    FVector2D CenterM = FVector2D::ZeroVector;
    FVector2D LeftNormal = FVector2D::UnitY();
};
struct FSouthForkGray16Image
{
    int32 Width = 0;
    int32 Height = 0;
    TArray<uint16> Values;
};

FString AbsoluteRepoPath(const FString& RelativePath);
FGuid SouthForkActorGuid(UClass* ActorClass, const FString& Label);
FName SouthForkActorObjectName(UClass* ActorClass, const FString& Label);
bool ReplaceWorldPartitionMiniMapWithStableActor(UWorld* World, FString& OutSummary);
bool LoadJsonObject(const FString& RelativePath, TSharedPtr<FJsonObject>& OutRoot);
bool LoadGray16Png(const FString& RelativePath, FSouthForkGray16Image& OutImage);
bool ParseCoordinateMap(
    const TSharedPtr<FJsonObject>& EnvironmentRoot,
    TArray<FSouthForkCoordinatePoint>& OutPoints,
    float& OutVerticalDatumM,
    FString& OutCoordinateMapPath);
int32 ClosestCoordinateIndex(
    const TArray<FSouthForkCoordinatePoint>& Points, double StationM);
FVector2D CoordinateWorldM(
    const FSouthForkCoordinatePoint& Point, float LateralM);
FVector CoordinateTangent(const TArray<FSouthForkCoordinatePoint>& Points, int32 Index);
float ComputeSouthForkSignedCurvaturePerM(
    const TArray<FSouthForkCoordinatePoint>& Points, int32 Index);
void SetSpatiallyLoadedIfAllowed(AActor* Actor, bool bSpatiallyLoaded);
bool CreateTerminalVisualWater(
    UWorld* World, const TArray<FSouthForkCoordinatePoint>& Points, float WaterZCm,
    UMaterialInterface* Material, bool bReuseMesh,
    FSouthForkFullReachBuildMetrics& Metrics, FString& OutSummary);
UHierarchicalInstancedStaticMeshComponent* AddHism(
    AActor* Owner,
    USceneComponent* Root,
    const FName Name,
    UStaticMesh* Mesh,
    UMaterialInterface* OverrideMaterial,
    int32 CullStartCm,
    int32 CullEndCm,
    ECollisionEnabled::Type Collision,
    bool bEnableDensityScaling = false,
    bool bCastShadow = true);
AActor* CreateInstancingActor(UWorld* World, const FString& Label, FName Tag);
float StableUnitRandom(int32 A, int32 B, int32 C);
bool AddSouthForkBankMicroreliefPresentationPatches(
    UWorld* World,
    const FString& TileId,
    int32 GlobalRowStart,
    const FVector2D& TileOriginM,
    const TArray<FSouthForkCoordinatePoint>& CoordinatePoints,
    int32 Width,
    int32 Height,
    const TArray<FVector>& SourceVertices,
    const TArray<FVector2D>& SourceUvs,
    const TArray<FLinearColor>& SourceColors,
    const TArray<FVector>& SourceNormals,
    const FRaftSimPreviewImage& VfxImage,
    UMaterialInterface* TerrainMaterial,
    bool bReuseExistingMeshes,
    FSouthForkFullReachBuildMetrics& Metrics,
    FString& OutSummary);
void AddSouthForkLighting(UWorld* World);
bool SaveFullReachWorld(UWorld* World);
bool ValidateStableSouthForkActorIdentities(
    UWorld* World, FSouthForkFullReachBuildMetrics& Metrics, FString& OutSummary);
UHLODLayer* ConfigureSouthForkInstancedHlodLayer(FString& OutSummary);

template <typename T>
T* SpawnStableSouthForkActor(
    UWorld* World, const FTransform& Transform, const FString& Label)
{
    if (!World)
    {
        return nullptr;
    }
    FActorSpawnParameters SpawnParameters;
    SpawnParameters.InitialActorLabel = Label;
    SpawnParameters.OverrideActorGuid = SouthForkActorGuid(T::StaticClass(), Label);
    // External actor package paths are derived from the actor object path, not
    // from ActorGuid. Give every generated actor a cross-process-stable object
    // name as well as a stable GUID so repeated builds reuse the same packages.
    SpawnParameters.Name = SouthForkActorObjectName(T::StaticClass(), Label);
    return World->SpawnActor<T>(T::StaticClass(), Transform, SpawnParameters);
}
} // namespace RaftSimEditorEnvironment::SouthForkFullReach
