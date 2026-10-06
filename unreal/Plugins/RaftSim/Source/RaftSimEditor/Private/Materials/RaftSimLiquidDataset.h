#pragma once
#include "CoreMinimal.h"
#include "Dom/JsonObject.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"
THIRD_PARTY_INCLUDES_START
#include <openssl/sha.h>
THIRD_PARTY_INCLUDES_END

// Versioned diagnostic datasets. Selection never changes saved assets/defaults.
// Hash every referenced state/contact page before creating native components;
// capture the manifest identities so offline audits cannot silently use another
// parent after a dataset switch. This is provenance, not physical acceptance.
struct FRaftSimLiquidDataset
{
    FString Key,Parent,Regions,Geometry,FaceBed,Mesh;
    TSharedPtr<FJsonObject> Evidence;

    static TSharedPtr<FJsonObject> Read(const FString& Path)
    {
        FString Text;TSharedPtr<FJsonObject> J;
        if(FFileHelper::LoadFileToString(Text,*Path))
            FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),J);
        return J;
    }
    static FString Hash(const FString& Path)
    {
        TArray<uint8> Bytes;uint8 Digest[SHA256_DIGEST_LENGTH];
        if(!FFileHelper::LoadFileToArray(Bytes,*Path) || !SHA256(Bytes.GetData(),Bytes.Num(),Digest)) return {};
        return BytesToHex(Digest,SHA256_DIGEST_LENGTH).ToLower();
    }
    static bool VerifyFiles(const FString& Directory,const TSharedPtr<FJsonObject>& Map)
    {
        if(!Map || Map->Values.IsEmpty() || Map->Values.Num()>256) return false;
        for(const auto& Pair:Map->Values)
        {
            FString Expected;const FString Name(*Pair.Key);
            if(FPaths::GetCleanFilename(Name)!=Name || Name.Contains(TEXT("..")) ||
                !Pair.Value->TryGetString(Expected) || Expected.Len()!=64 || Hash(Directory/Name)!=Expected) return false;
        }
        return true;
    }
    static bool Load(const FString& Base,const FString& Key,FRaftSimLiquidDataset& Out,FString& Error)
    {
        Out={};Error=TEXT("Unknown or changed regional liquid dataset; no native components created");
        FRaftSimLiquidDataset D;D.Key=Key;
        if(Key==TEXT("core-v1"))
        {
            D.Parent=Base/TEXT("south-fork-whole-rapid-liquid-float-seeds-20260910");
            D.Regions=Base/TEXT("south-fork-liquid-regional-state-20260910");
            D.Geometry=Base/TEXT("south-fork-liquid-regional-geometry-v4-20260910");
            D.FaceBed=Base/TEXT("south-fork-liquid-face-bed-20260910/physical_face_bed.json");
        }
        else if(Key==TEXT("reservoir-v1"))
        {
            D.Parent=Base/TEXT("south-fork-liquid-reservoir-window-20260910");
            D.Regions=Base/TEXT("south-fork-liquid-reservoir-regions-20260910");
            D.Geometry=Base/TEXT("south-fork-liquid-reservoir-geometry-20260910");
            D.FaceBed=Base/TEXT("south-fork-liquid-reservoir-face-bed-20260910/physical_face_bed.json");
        }
        else return false;
        D.Mesh=Base/TEXT("south-fork-rock-return-xy-candidate-v2-20260907/registered_mesh_source.npz");
        const auto State=Read(D.Regions/TEXT("manifest.json")),Geo=Read(D.Geometry/TEXT("manifest.json"));
        const TSharedPtr<FJsonObject> *Files=nullptr;
        const TArray<TSharedPtr<FJsonValue>> *Pages=nullptr;
        FString Expected;
        if(!State || !Geo || !State->TryGetObjectField(TEXT("parent_files_sha256"),Files) || !VerifyFiles(D.Parent,*Files) ||
            !Geo->TryGetObjectField(TEXT("parent_files_sha256"),Files) || !VerifyFiles(D.Parent,*Files) ||
            !Geo->TryGetStringField(TEXT("ownership_manifest_sha256"),Expected) || Hash(D.Regions/TEXT("manifest.json"))!=Expected ||
            !Geo->TryGetStringField(TEXT("original_mesh_sha256"),Expected) || Hash(D.Mesh)!=Expected ||
            !Geo->TryGetStringField(TEXT("extended_parent_contact_sha256"),Expected) ||
            Hash(D.Geometry/TEXT("extended_parent_contact.json"))!=Expected ||
            !State->TryGetArrayField(TEXT("region_files"),Pages) || Pages->Num()!=12) return false;
        TSet<FString> Names;
        for(const auto& Page:*Pages)
        {
            const TSharedPtr<FJsonObject>* P;FString Name;
            if(!Page->TryGetObject(P) || !(*P)->TryGetStringField(TEXT("file"),Name) ||
                !(*P)->TryGetStringField(TEXT("sha256"),Expected) || FPaths::GetCleanFilename(Name)!=Name ||
                Names.Contains(Name) || Hash(D.Regions/Name)!=Expected) return false;
            Names.Add(Name);
        }
        if(!Geo->TryGetArrayField(TEXT("regions"),Pages) || Pages->Num()!=12) return false;
        for(const auto& Page:*Pages)
        {
            const TSharedPtr<FJsonObject>* P;
            if(!Page->TryGetObject(P) || !(*P)->TryGetObjectField(TEXT("files"),Files) || !VerifyFiles(D.Geometry,*Files)) return false;
        }
        D.Evidence=MakeShared<FJsonObject>();D.Evidence->SetStringField(TEXT("key"),Key);
        D.Evidence->SetStringField(TEXT("parent_manifest_sha256"),Hash(D.Parent/TEXT("manifest.json")));
        D.Evidence->SetStringField(TEXT("ownership_manifest_sha256"),Hash(D.Regions/TEXT("manifest.json")));
        D.Evidence->SetStringField(TEXT("geometry_manifest_sha256"),Hash(D.Geometry/TEXT("manifest.json")));
        const FString BedHash=Hash(D.FaceBed);if(BedHash.Len()!=64) return false;
        D.Evidence->SetStringField(TEXT("face_bed_sha256"),BedHash);
        D.Evidence->SetBoolField(TEXT("physical_acceptance"),false);
        Out=MoveTemp(D);Error.Reset();return true;
    }
};
