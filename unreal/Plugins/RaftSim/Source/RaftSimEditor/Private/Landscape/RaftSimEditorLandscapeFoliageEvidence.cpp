#include "Landscape/RaftSimEditorLandscapeFoliageInternal.h"

namespace RaftSimEditorEnvironment::LandscapeFoliage
{
UMaterialInterface* LoadReachRockMaterial(const FString& RiverId, FString& OutSummary)
{
    const TCHAR* Path = RiverId.Contains(TEXT("futaleufu"))
        ? TEXT("/Game/RaftSim/Environment/FutaleufuRun/Rocks/MI_RaftSim_Futaleufu_GraniteRockV1."
               "MI_RaftSim_Futaleufu_GraniteRockV1")
        : RiverId.Contains(TEXT("chilko"))
        ? TEXT("/Game/RaftSim/Environment/ChilkoRun/Rocks/MI_RaftSim_Chilko_BasaltRockV1."
               "MI_RaftSim_Chilko_BasaltRockV1")
        : RiverId == TEXT("zambezi_batoka_gorge")
        ? TEXT("/Game/RaftSim/Environment/ZambeziRun/Rocks/MI_RaftSim_Zambezi_BasaltWallRockV1."
               "MI_RaftSim_Zambezi_BasaltWallRockV1")
        : nullptr;
    if (!Path)
    {
        return nullptr;
    }
    UMaterialInterface* Material = LoadObject<UMaterialInterface>(nullptr, Path);
    if (!Material)
    {
        OutSummary += FString::Printf(
            TEXT("Reach rock material missing (%s); run unreal/Scripts/create_tinted_rock_materials.py. "
                 "The scan's mossy material stays.\n"), Path);
    }
    return Material;
}

TSharedPtr<FJsonObject> LoadEvidencePlacement(
    const FString& TerrainFolder, const TCHAR* FileName, const TCHAR* Schema, FString& OutSummary)
{
    const FString Path = FPaths::ConvertRelativePathToFull(FPaths::Combine(GetRepoRoot(), TerrainFolder, FileName));
    FString Text;
    TSharedPtr<FJsonObject> Root;
    if (FFileHelper::LoadFileToString(Text, *Path))
    {
        const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Text);
        FJsonSerializer::Deserialize(Reader, Root);
    }
    const TArray<TSharedPtr<FJsonValue>>* Rows = nullptr;
    if (!Root.IsValid() || Root->GetStringField(TEXT("schema")) != Schema ||
        !Root->TryGetArrayField(TEXT("instances"), Rows) || Rows->Num() == 0)
    {
        OutSummary += FString::Printf(TEXT("Evidence placement missing or invalid: %s\n"), *Path);
        return nullptr;
    }
    return Root;
}

FEvidenceCanopyCounts AddEvidenceCanopy(
    const FPlacementContext& Context,
    const FPlacementQueries& Queries,
    const FString& TerrainFolder,
    const TCHAR* FileName,
    const TCHAR* Schema,
    const TCHAR* ComponentPrefix,
    const TCHAR* ActorTag,
    const TCHAR* SourceDescription,
    TConstArrayView<UStaticMesh*> ExtraTreeForms,
    UStaticMesh* AltUnderstoryMesh)
{
    // Evidence canopy over the whole Landscape window (placement JSON from the
    // reach's evidence dressing builder): imagery-placed trees with inferred
    // crown size, height and species, plus an inferred understory shrub
    // beside each. Own components keep its count and cost separable; the
    // component settings and materials mirror the reach's canopy layers.
    FEvidenceCanopyCounts Counts;
    if (!Context.BroadleafTreeMesh || !Context.ConiferTreeMesh ||
        !Context.BroadleafTreeInstances || !Context.ConiferTreeInstances)
    {
        return Counts;
    }
    const TSharedPtr<FJsonObject> Root = LoadEvidencePlacement(TerrainFolder, FileName, Schema, Context.OutSummary);
    const TArray<TSharedPtr<FJsonValue>>* Rows = nullptr;
    if (!Root.IsValid() || !Root->TryGetArrayField(TEXT("instances"), Rows))
    {
        Counts.Expected = 1;
        return Counts;
    }
    const FString RiverId = Context.Candidate.PreviewSpec.RiverId;
    Counts.Expected = Rows->Num();
    // Forms 0/1 mirror the reach's canopy components (and their materials);
    // extra forms keep their own mesh materials.
    TArray<UStaticMesh*> Meshes = {Context.BroadleafTreeMesh, Context.ConiferTreeMesh};
    Meshes.Append(ExtraTreeForms.GetData(), ExtraTreeForms.Num());
    UHierarchicalInstancedStaticMeshComponent* const Sources[2] = {
        Context.BroadleafTreeInstances, Context.ConiferTreeInstances};
    TArray<UHierarchicalInstancedStaticMeshComponent*> Components;
    TArray<FVector> MeshSizes;
    bool bAllComponents = true;
    for (int32 Form = 0; Form < Meshes.Num(); ++Form)
    {
        const FString Suffix = Form < 2 ? FString(Form == 0 ? TEXT("A") : TEXT("B")) : FString::Printf(TEXT("Form%d"), Form);
        UHierarchicalInstancedStaticMeshComponent* Component = Meshes[Form]
            ? AddLandscapeCandidateInstancedMeshComponent(
                  Context.World, Meshes[Form], FString::Printf(TEXT("%sCanopy%s_%s"), ComponentPrefix, *Suffix, *RiverId), true)
            : nullptr;
        if (Component)
        {
            Component->GetOwner()->Tags.Append(
                {FName(ActorTag), TEXT("RaftSimImageryCanopyPositions"), TEXT("InferredVegetationNotSurveyedTrees")});
            for (int32 Slot = 0; Form < 2 && Slot < Sources[Form]->GetNumMaterials(); ++Slot)
            {
                Component->SetMaterial(Slot, Sources[Form]->GetMaterial(Slot));
            }
        }
        bAllComponents &= Component != nullptr;
        Components.Add(Component);
        MeshSizes.Add(Meshes[Form] ? GetLandscapeCandidateEffectiveMeshBounds(Meshes[Form]).GetSize() : FVector::OneVector);
    }
    if (bAllComponents)
    {
        for (const TSharedPtr<FJsonValue>& Value : *Rows)
        {
            const TArray<TSharedPtr<FJsonValue>>* Row = nullptr;
            if (!Value.IsValid() || !Value->TryGetArray(Row) || Row->Num() < 8)
            {
                continue;
            }
            // x_cm, y_cm, terrain_z_cm, crown_radius_m, height_m, form, kind, yaw_deg
            const float X = static_cast<float>((*Row)[0]->AsNumber());
            const float Y = static_cast<float>((*Row)[1]->AsNumber());
            const float RadiusM = static_cast<float>((*Row)[3]->AsNumber());
            const float HeightM = static_cast<float>((*Row)[4]->AsNumber());
            const int32 Form = FMath::Clamp(static_cast<int32>((*Row)[5]->AsNumber()), 0, Meshes.Num() - 1);
            const float YawDegrees = static_cast<float>((*Row)[7]->AsNumber());
            const FVector& Size = MeshSizes[Form];
            const float CrownScale = 200.0f * RadiusM / FMath::Max(1.0f, static_cast<float>(FMath::Max(Size.X, Size.Y)));
            const float HeightScale = FMath::Clamp(
                100.0f * HeightM / FMath::Max(1.0f, static_cast<float>(Size.Z)), 0.8f * CrownScale, 1.8f * CrownScale);
            // Sink roots 30 cm so trunks meet the sloping Landscape.
            Queries.AddGroundedInstance(
                Components[Form], Meshes[Form], FVector2D(X, Y), Queries.GetLandscapeHeight(X, Y) - 30.0f,
                FRotator(0.0f, YawDegrees, 0.0f), FVector(CrownScale, CrownScale, HeightScale));
            ++Counts.Placed;
        }
    }
    Counts.Trees = Counts.Placed;
    const TArray<TSharedPtr<FJsonValue>>* UnderstoryRows = nullptr;
    UHierarchicalInstancedStaticMeshComponent* UnderstoryComponent =
        Context.ShrubMesh && Context.ShrubInstances
            ? AddLandscapeCandidateInstancedMeshComponent(
                  Context.World, Context.ShrubMesh, FString::Printf(TEXT("%sUnderstory_%s"), ComponentPrefix, *RiverId), true)
            : nullptr;
    UHierarchicalInstancedStaticMeshComponent* AltUnderstoryComponent =
        UnderstoryComponent && AltUnderstoryMesh
            ? AddLandscapeCandidateInstancedMeshComponent(
                  Context.World, AltUnderstoryMesh, FString::Printf(TEXT("%sUnderstoryB_%s"), ComponentPrefix, *RiverId), true)
            : nullptr;
    if (UnderstoryComponent && Root->TryGetArrayField(TEXT("understory"), UnderstoryRows))
    {
        UnderstoryComponent->GetOwner()->Tags.Append({FName(ActorTag), TEXT("InferredVegetationNotSurveyedTrees")});
        if (AltUnderstoryComponent)
        {
            AltUnderstoryComponent->GetOwner()->Tags.Append({FName(ActorTag), TEXT("InferredVegetationNotSurveyedTrees")});
        }
        for (int32 Slot = 0; Slot < Context.ShrubInstances->GetNumMaterials(); ++Slot)
        {
            UnderstoryComponent->SetMaterial(Slot, Context.ShrubInstances->GetMaterial(Slot));
        }
        const FVector Size = GetLandscapeCandidateEffectiveMeshBounds(Context.ShrubMesh).GetSize();
        const FVector AltSize = AltUnderstoryMesh ? GetLandscapeCandidateEffectiveMeshBounds(AltUnderstoryMesh).GetSize() : Size;
        Counts.Expected += UnderstoryRows->Num();
        for (const TSharedPtr<FJsonValue>& Value : *UnderstoryRows)
        {
            const TArray<TSharedPtr<FJsonValue>>* Row = nullptr;
            if (!Value.IsValid() || !Value->TryGetArray(Row) || Row->Num() < 5)
            {
                continue;
            }
            // x_cm, y_cm, height_m, width_m, yaw_deg[, kind]; kind 1 uses the alternate understory.
            const bool bAlt = AltUnderstoryComponent && Row->Num() >= 6 && static_cast<int32>((*Row)[5]->AsNumber()) == 1;
            const FVector& RowSize = bAlt ? AltSize : Size;
            const float X = static_cast<float>((*Row)[0]->AsNumber());
            const float Y = static_cast<float>((*Row)[1]->AsNumber());
            const float WidthScale = 100.0f * static_cast<float>((*Row)[3]->AsNumber()) /
                FMath::Max(1.0f, static_cast<float>(FMath::Max(RowSize.X, RowSize.Y)));
            const float HeightScale = 100.0f * static_cast<float>((*Row)[2]->AsNumber()) /
                FMath::Max(1.0f, static_cast<float>(RowSize.Z));
            Queries.AddGroundedInstance(
                bAlt ? AltUnderstoryComponent : UnderstoryComponent, bAlt ? AltUnderstoryMesh : Context.ShrubMesh,
                FVector2D(X, Y), Queries.GetLandscapeHeight(X, Y) - 20.0f,
                FRotator(0.0f, static_cast<float>((*Row)[4]->AsNumber()), 0.0f),
                FVector(WidthScale, WidthScale, HeightScale));
            ++Counts.Placed;
        }
    }
    else
    {
        Counts.Expected += 1;
    }
    Context.OutResult.DressingFoliageInstanceCount += Counts.Placed;
    Context.OutResult.DressingCanopyTreeInstanceCount += Counts.Trees;
    Context.OutResult.DressingUnderstoryInstanceCount += Counts.Placed - Counts.Trees;
    Context.OutSummary += FString::Printf(
        TEXT("%s evidence canopy: %d trees and %d understory shrubs, %d/%d rows (%s; crown size, heights, species ")
        TEXT("and understory inferred), Landscape-grounded, non-colliding.\n"),
        *RiverId, Counts.Trees, Counts.Placed - Counts.Trees, Counts.Placed, Counts.Expected, SourceDescription);
    return Counts;
}

FObservedRockCounts AddObservedRockShells(
    const FPlacementContext& Context,
    const FPlacementQueries& Queries,
    const FString& TerrainFolder,
    const TCHAR* FileName,
    const TCHAR* ComponentPrefix,
    const TCHAR* ActorTag)
{
    FObservedRockCounts Counts;
    if (Context.ReviewedRockMeshes.Num() != 6)
    {
        Counts.Expected = 1;
        return Counts;
    }
    const TSharedPtr<FJsonObject> Root = LoadEvidencePlacement(
        TerrainFolder, FileName, TEXT("raftsim.observed_rock_placement.v1"), Context.OutSummary);
    const TArray<TSharedPtr<FJsonValue>>* Rows = nullptr;
    if (!Root.IsValid() || !Root->TryGetArrayField(TEXT("instances"), Rows))
    {
        Counts.Expected = 1;
        return Counts;
    }
    Counts.Expected = Rows->Num();
    const FString RiverId = Context.Candidate.PreviewSpec.RiverId;
    // The reach's observed rock colour (grey granite, dark basalt) instead of
    // the scan's mossy tan; the scan's shape, normal and roughness are kept.
    UMaterialInterface* ReachRockMaterial = LoadReachRockMaterial(RiverId, Context.OutSummary);
    UHierarchicalInstancedStaticMeshComponent* Components[6] = {};
    FVector MeshSizes[6];
    for (int32 Variant = 0; Variant < 6; ++Variant)
    {
        UStaticMesh* Mesh = Context.ReviewedRockMeshes[Variant];
        Components[Variant] = AddLandscapeCandidateInstancedMeshComponent(
            Context.World, Mesh, FString::Printf(TEXT("%s%d_%s"), ComponentPrefix, Variant, *RiverId), true,
            ReachRockMaterial);
        if (!Components[Variant])
        {
            return Counts;
        }
        Components[Variant]->GetOwner()->Tags.Append(
            {FName(ActorTag), TEXT("RaftSimObservedRockPositions"), TEXT("RaftSimNoTerrainCollisionOrWaterAuthority")});
        MeshSizes[Variant] = GetLandscapeCandidateEffectiveMeshBounds(Mesh).GetSize();
    }
    for (const TSharedPtr<FJsonValue>& Value : *Rows)
    {
        const TArray<TSharedPtr<FJsonValue>>* Row = nullptr;
        if (!Value.IsValid() || !Value->TryGetArray(Row) || Row->Num() < 10)
        {
            continue;
        }
        // x_cm, y_cm, sink_cm, length_m, width_m, height_m, yaw_deg, variant, pitch_deg, roll_deg
        const float X = static_cast<float>((*Row)[0]->AsNumber());
        const float Y = static_cast<float>((*Row)[1]->AsNumber());
        const int32 Variant = FMath::Clamp(static_cast<int32>((*Row)[7]->AsNumber()), 0, 5);
        const FVector& Size = MeshSizes[Variant];
        const FVector Scale(
            100.0f * static_cast<float>((*Row)[3]->AsNumber()) / FMath::Max(1.0f, static_cast<float>(Size.X)),
            100.0f * static_cast<float>((*Row)[4]->AsNumber()) / FMath::Max(1.0f, static_cast<float>(Size.Y)),
            100.0f * static_cast<float>((*Row)[5]->AsNumber()) / FMath::Max(1.0f, static_cast<float>(Size.Z)));
        Queries.AddGroundedInstance(
            Components[Variant], Context.ReviewedRockMeshes[Variant], FVector2D(X, Y),
            Queries.GetLandscapeHeight(X, Y) - static_cast<float>((*Row)[2]->AsNumber()),
            FRotator(static_cast<float>((*Row)[8]->AsNumber()), static_cast<float>((*Row)[6]->AsNumber()),
                static_cast<float>((*Row)[9]->AsNumber())),
            Scale);
        ++Counts.Placed;
    }
    Context.OutSummary += FString::Printf(
        TEXT("%s observed rock: %d/%d reviewed rock meshes at described outcrops, cliffs and waterline talus ")
        TEXT("(positions and sizes approximate), Landscape-grounded, non-colliding.\n"),
        *RiverId, Counts.Placed, Counts.Expected);
    return Counts;
}
}
