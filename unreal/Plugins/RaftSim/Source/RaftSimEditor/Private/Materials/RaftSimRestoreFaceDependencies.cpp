#include "AssetToolsModule.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "HAL/FileManager.h"
#include "HAL/IConsoleManager.h"
#include "IAssetTools.h"
#include "Misc/FileHelper.h"
#include "Misc/PackageName.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

// Explicit maintenance action, never called by normal scene loading. The audit
// supplies a complete source closure; existing project assets are never replaced.
static void RestoreMissingFaceDependencies(const TArray<FString>& Args)
{
    if (Args.Num() != 1)
    {
        UE_LOG(LogTemp, Error, TEXT("FaceDependencyRestore requires one audited JSON path"));
        return;
    }
    FString Json;
    TSharedPtr<FJsonObject> Audit;
    if (!FFileHelper::LoadFileToString(Json, *Args[0]) ||
        !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Json), Audit) || !Audit.IsValid())
    {
        UE_LOG(LogTemp, Error, TEXT("FaceDependencyRestore: invalid audit"));
        return;
    }
    FString Schema;
    const TArray<TSharedPtr<FJsonValue>>* Entries = nullptr;
    const TArray<TSharedPtr<FJsonValue>>* Additional = nullptr;
    const TArray<TSharedPtr<FJsonValue>>* Missing = nullptr;
    if (!Audit->TryGetStringField(TEXT("schema"), Schema) ||
        Schema != TEXT("raftsim.face_material_source_audit.v1") ||
        !Audit->TryGetArrayField(TEXT("entries"), Entries) ||
        !Audit->TryGetArrayField(TEXT("mapped_additional_destinations"), Additional) ||
        !Audit->TryGetArrayField(TEXT("unregistered_source_dependencies"), Missing) || Missing->Num() != 0)
    {
        UE_LOG(LogTemp, Error, TEXT("FaceDependencyRestore: incomplete source closure"));
        return;
    }
    const FString SourceRoot(TEXT("/MetaHumanCharacter/Lookdev_UHM/"));
    const FString DestinationRoot(TEXT("/Game/RaftSim/Characters/Production/MetaHumans/Common/Lookdev_UHM/"));
    TMap<FString, FString> Copy;
    TArray<TSharedPtr<FJsonValue>> All = *Entries;
    All.Append(*Additional);
    for (const TSharedPtr<FJsonValue>& Value : All)
    {
        const TSharedPtr<FJsonObject>* Row = nullptr;
        FString Source, Destination, Filename;
        if (!Value->TryGetObject(Row) || !Row ||
            !(*Row)->TryGetStringField(TEXT("source"), Source) ||
            !(*Row)->TryGetStringField(TEXT("destination"), Destination) ||
            !Source.StartsWith(SourceRoot) ||
            !FPackageName::IsValidLongPackageName(Source) ||
            Destination != DestinationRoot + Source.RightChop(SourceRoot.Len()) ||
            !FPackageName::IsValidLongPackageName(Destination) ||
            !FPackageName::DoesPackageExist(Source) || Copy.Contains(Source) ||
            !FPackageName::TryConvertLongPackageNameToFilename(Destination, Filename, FPackageName::GetAssetPackageExtension()) ||
            IFileManager::Get().FileExists(*Filename) ||
            FindPackage(nullptr, *Destination))
        {
            UE_LOG(LogTemp, Error, TEXT("FaceDependencyRestore: invalid/missing source or destination collision: %s -> %s"), *Source, *Destination);
            return;
        }
        Copy.Add(Source, Destination);
    }
    if (Copy.IsEmpty())
    {
        UE_LOG(LogTemp, Error, TEXT("FaceDependencyRestore: empty closure"));
        return;
    }
    IAssetRegistry& Registry = FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get();
    Registry.SearchAllAssets(true);
    for (const TPair<FString, FString>& Pair : Copy)
    {
        TArray<FName> Dependencies;
        Registry.GetDependencies(FName(*Pair.Key), Dependencies);
        for (FName Dependency : Dependencies)
        {
            const FString Name = Dependency.ToString();
            if (Name.StartsWith(TEXT("/MetaHumanCharacter/")) && !Copy.Contains(Name))
            {
                UE_LOG(LogTemp, Error, TEXT("FaceDependencyRestore: unmapped plugin dependency %s of %s"), *Name, *Pair.Key);
                return;
            }
        }
    }
    IAssetTools& Tools = FModuleManager::LoadModuleChecked<FAssetToolsModule>(TEXT("AssetTools")).Get();
    // Advanced copy remaps cross-references among the entire set before saving;
    // individual duplicates would retain references to editor-plugin packages.
    const bool bCopied = Tools.AdvancedCopyPackages(Copy, true, false);
    int32 Saved = 0;
    for (const TPair<FString, FString>& Pair : Copy)
    {
        Saved += FPackageName::DoesPackageExist(Pair.Value) ? 1 : 0;
    }
    if (!bCopied || Saved != Copy.Num())
    {
        UE_LOG(LogTemp, Error, TEXT("FaceDependencyRestore incomplete: %d/%d saved; preserve partial output for inspection"), Saved, Copy.Num());
        return;
    }
    UE_LOG(LogTemp, Display, TEXT("FaceDependencyRestore copied %d missing packages; fresh closure/compile/render validation still required"), Saved);
}

static FAutoConsoleCommand RestoreFaceDependenciesCommand(
    TEXT("RaftSim.RestoreMissingFaceDependencies"),
    TEXT("Restore absent cropped-face dependencies from a verified installed-source audit; refuses destination collisions."),
    FConsoleCommandWithArgsDelegate::CreateStatic(&RestoreMissingFaceDependencies));
