#include "Landscape/RaftSimEditorLandscapeFoliageInternal.h"

namespace RaftSimEditorEnvironment::LandscapeFoliage
{
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
    const TCHAR* SourceDescription)
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
    UStaticMesh* const Meshes[2] = {Context.BroadleafTreeMesh, Context.ConiferTreeMesh};
    UHierarchicalInstancedStaticMeshComponent* const Sources[2] = {
        Context.BroadleafTreeInstances, Context.ConiferTreeInstances};
    UHierarchicalInstancedStaticMeshComponent* Components[2] = {nullptr, nullptr};
    FVector MeshSizes[2];
    for (int32 Form = 0; Form < 2; ++Form)
    {
        Components[Form] = AddLandscapeCandidateInstancedMeshComponent(
            Context.World, Meshes[Form],
            FString::Printf(TEXT("%sCanopy%s_%s"), ComponentPrefix, Form == 0 ? TEXT("A") : TEXT("B"), *RiverId),
            true);
        if (Components[Form])
        {
            Components[Form]->GetOwner()->Tags.Append(
                {FName(ActorTag), TEXT("RaftSimImageryCanopyPositions"), TEXT("InferredVegetationNotSurveyedTrees")});
            for (int32 Slot = 0; Slot < Sources[Form]->GetNumMaterials(); ++Slot)
            {
                Components[Form]->SetMaterial(Slot, Sources[Form]->GetMaterial(Slot));
            }
        }
        MeshSizes[Form] = GetLandscapeCandidateEffectiveMeshBounds(Meshes[Form]).GetSize();
    }
    if (Components[0] && Components[1])
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
            const int32 Form = FMath::Clamp(static_cast<int32>((*Row)[5]->AsNumber()), 0, 1);
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
    if (UnderstoryComponent && Root->TryGetArrayField(TEXT("understory"), UnderstoryRows))
    {
        UnderstoryComponent->GetOwner()->Tags.Append({FName(ActorTag), TEXT("InferredVegetationNotSurveyedTrees")});
        for (int32 Slot = 0; Slot < Context.ShrubInstances->GetNumMaterials(); ++Slot)
        {
            UnderstoryComponent->SetMaterial(Slot, Context.ShrubInstances->GetMaterial(Slot));
        }
        const FVector Size = GetLandscapeCandidateEffectiveMeshBounds(Context.ShrubMesh).GetSize();
        Counts.Expected += UnderstoryRows->Num();
        for (const TSharedPtr<FJsonValue>& Value : *UnderstoryRows)
        {
            const TArray<TSharedPtr<FJsonValue>>* Row = nullptr;
            if (!Value.IsValid() || !Value->TryGetArray(Row) || Row->Num() < 5)
            {
                continue;
            }
            // x_cm, y_cm, height_m, width_m, yaw_deg
            const float X = static_cast<float>((*Row)[0]->AsNumber());
            const float Y = static_cast<float>((*Row)[1]->AsNumber());
            const float WidthScale = 100.0f * static_cast<float>((*Row)[3]->AsNumber()) /
                FMath::Max(1.0f, static_cast<float>(FMath::Max(Size.X, Size.Y)));
            const float HeightScale = 100.0f * static_cast<float>((*Row)[2]->AsNumber()) /
                FMath::Max(1.0f, static_cast<float>(Size.Z));
            Queries.AddGroundedInstance(
                UnderstoryComponent, Context.ShrubMesh, FVector2D(X, Y), Queries.GetLandscapeHeight(X, Y) - 20.0f,
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
}
