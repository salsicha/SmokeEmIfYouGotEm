#include "RaftSimGroundSourceLibrary.h"
#include "Algo/Sort.h"
#include "Dom/JsonObject.h"
#include "Engine/StaticMesh.h"
#include "HAL/IConsoleManager.h"
#include "HAL/PlatformMisc.h"
#include "Interface_CollisionDataProviderCore.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "PhysicsEngine/BodySetup.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
THIRD_PARTY_INCLUDES_START
#include <openssl/sha.h>
THIRD_PARTY_INCLUDES_END

namespace
{
FString Encode(const TSharedRef<FJsonObject>& Object)
{
    FString Text;FJsonSerializer::Serialize(Object,TJsonWriterFactory<>::Create(&Text));return Text;
}
// Raw little-endian float coordinates, cyclically canonicalized (never reverse
// winding), then material-slot index. Sorting permits provider vertex/face
// renumbering, but cannot conceal a changed coordinate, face or material slot.
struct FSourceTriangle {uint32 Words[10];};
static_assert(sizeof(FSourceTriangle)==40);
}

FString URaftSimGroundSourceLibrary::AuditCollisionSource(UStaticMesh* Mesh)
{
    const auto Result=MakeShared<FJsonObject>();Result->SetBoolField(TEXT("available"),false);
    Result->SetStringField(TEXT("format"),TEXT("le_f32_cyclic_directed_triangles_material_u32_sorted_v1"));
    Result->SetBoolField(TEXT("editor_only_data"),WITH_EDITORONLY_DATA!=0);
    const auto Fail=[&](const TCHAR* Reason){Result->SetStringField(TEXT("error"),Reason);return Encode(Result);};
    if(!Mesh || !Mesh->HasValidRenderData() || !Mesh->GetBodySetup())return Fail(TEXT("missing mesh render/body data"));
    Result->SetStringField(TEXT("asset"),Mesh->GetPathName().LeftChop(Mesh->GetName().Len()+1));
    Result->SetBoolField(TEXT("allow_cpu_access"),Mesh->bAllowCPUAccess);
    Result->SetNumberField(TEXT("collision_lod"),Mesh->LODForCollision);
    Result->SetNumberField(TEXT("collision_trace_flag"),int32(Mesh->GetBodySetup()->GetCollisionTraceFlag()));
#if WITH_EDITORONLY_DATA
    if(Mesh->ComplexCollisionMesh && Mesh->ComplexCollisionMesh!=Mesh)return Fail(TEXT("alternate editor-only complex source requires separate cooked qualification"));
#endif
    FTriMeshCollisionData Data;
    if(!Mesh->GetPhysicsTriMeshData(&Data,false))return Fail(TEXT("collision-provider CPU triangles unavailable"));
    if(Data.Indices.Num()==0 || Data.MaterialIndices.Num()!=Data.Indices.Num())return Fail(TEXT("incomplete source faces/material slots"));
    TArray<FSourceTriangle> Records;Records.SetNumUninitialized(Data.Indices.Num());
    for(int32 I=0;I<Data.Indices.Num();++I)
    {
        const auto& F=Data.Indices[I];const int32 Indices[3]={F.v0,F.v1,F.v2};uint32 Points[3][3];
        for(int32 V=0;V<3;++V)
        {
            if(!Data.Vertices.IsValidIndex(Indices[V]))return Fail(TEXT("invalid collision-provider index"));
            const FVector3f P=Data.Vertices[Indices[V]];
            if(P.ContainsNaN())return Fail(TEXT("nonfinite collision-provider vertex"));
            const float XYZ[3]={P.X,P.Y,P.Z};FMemory::Memcpy(Points[V],XYZ,sizeof(XYZ));
        }
        int32 First=0;
        for(int32 V=1;V<3;++V)for(int32 Corner=0;Corner<3;++Corner)
        {
            const int32 Compare=FMemory::Memcmp(Points[(V+Corner)%3],Points[(First+Corner)%3],12);
            if(Compare<0)First=V;if(Compare!=0)break;
        }
        for(int32 V=0;V<3;++V)FMemory::Memcpy(Records[I].Words+V*3,Points[(First+V)%3],12);
        Records[I].Words[9]=uint32(Data.MaterialIndices[I]);
    }
    Algo::Sort(Records,[](const FSourceTriangle& A,const FSourceTriangle& B){return FMemory::Memcmp(&A,&B,sizeof(A))<0;});
    if(uint64(Records.Num())*sizeof(FSourceTriangle)>MAX_uint32)return Fail(TEXT("source exceeds hash API byte limit"));
    uint8 Signature[SHA256_DIGEST_LENGTH];
    if(!SHA256(reinterpret_cast<const unsigned char*>(Records.GetData()),Records.Num()*sizeof(FSourceTriangle),Signature))return Fail(TEXT("SHA256 unavailable"));
    Result->SetStringField(TEXT("collision_source_sha256"),BytesToHex(Signature,UE_ARRAY_COUNT(Signature)).ToLower());
    Result->SetNumberField(TEXT("triangle_count"),Data.Indices.Num());
    Result->SetNumberField(TEXT("provider_vertex_count"),Data.Vertices.Num());
    Result->SetBoolField(TEXT("flip_normals"),Data.bFlipNormals);
    Result->SetBoolField(TEXT("available"),true);return Encode(Result);
}

#if !UE_BUILD_SHIPPING
namespace
{
void AuditCookedSources(const TArray<FString>& Args)
{
    if(Args.Num()!=2 || FPaths::FileExists(Args[1]))
    {UE_LOG(LogTemp,Error,TEXT("Ground source audit requires <expected.json> <fresh-report.json>"));return;}
    FString Text;TSharedPtr<FJsonObject> Expected;
    if(!FFileHelper::LoadFileToString(Text,*Args[0]) || !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Expected) || !Expected.IsValid())
    {UE_LOG(LogTemp,Error,TEXT("Invalid ground source audit manifest"));return;}
    const TArray<TSharedPtr<FJsonValue>>* Assets=nullptr;
    if(!Expected->TryGetArrayField(TEXT("assets"),Assets) || Assets->IsEmpty())return;
    bool Passed=true;TArray<TSharedPtr<FJsonValue>> Results;
    for(const auto& Value:*Assets)
    {
        const auto Record=Value->AsObject();FString Asset,Hash;double Triangles=0.;
        if(!Record || !Record->TryGetStringField(TEXT("asset"),Asset) || !Asset.StartsWith(TEXT("/Game/")) ||
            !Record->TryGetStringField(TEXT("collision_source_sha256"),Hash) || !Record->TryGetNumberField(TEXT("triangle_count"),Triangles))
        {Passed=false;break;}
        auto* Mesh=LoadObject<UStaticMesh>(nullptr,*Asset);
        TSharedPtr<FJsonObject> Actual;
        FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(URaftSimGroundSourceLibrary::AuditCollisionSource(Mesh)),Actual);
        bool Available=false,CPU=false;FString ActualHash;double ActualTriangles=0.;
        bool Match=Actual.IsValid() && Actual->TryGetBoolField(TEXT("available"),Available) && Available &&
            Actual->TryGetBoolField(TEXT("allow_cpu_access"),CPU) && CPU &&
            Actual->TryGetStringField(TEXT("collision_source_sha256"),ActualHash) && ActualHash==Hash &&
            Actual->TryGetNumberField(TEXT("triangle_count"),ActualTriangles) && ActualTriangles==Triangles;
        if(Match)
        {
            for(const TCHAR* Key:{TEXT("collision_lod"),TEXT("collision_trace_flag"),TEXT("provider_vertex_count")})
            {double A=0.,B=0.;Match&=Record->TryGetNumberField(Key,A) && Actual->TryGetNumberField(Key,B) && A==B;}
            bool A=false,B=false;FString ExpectedFormat,ActualFormat;
            Match&=Record->TryGetBoolField(TEXT("flip_normals"),A) && Actual->TryGetBoolField(TEXT("flip_normals"),B) && A==B;
            Match&=Record->TryGetStringField(TEXT("format"),ExpectedFormat) && Actual->TryGetStringField(TEXT("format"),ActualFormat) && ExpectedFormat==ActualFormat;
        }
        if(!Actual)Actual=MakeShared<FJsonObject>();Actual->SetBoolField(TEXT("source_matches"),Match);
        Passed&=Match;Results.Add(MakeShared<FJsonValueObject>(Actual));
    }
    const auto Report=MakeShared<FJsonObject>();Report->SetArrayField(TEXT("assets"),Results);
    Report->SetBoolField(TEXT("passed"),Passed && Results.Num()==Assets->Num());
    Report->SetBoolField(TEXT("editor_only_data"),WITH_EDITORONLY_DATA!=0);
    const bool Saved=FFileHelper::SaveStringToFile(Encode(Report),*Args[1],FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM);
    UE_LOG(LogTemp,Display,TEXT("Ground source audit: assets=%d matched=%d report_saved=%d editor_only_data=%d"),Results.Num(),int32(Passed),int32(Saved),int32(WITH_EDITORONLY_DATA));
    FPlatformMisc::RequestExitWithStatus(false,Passed && Saved?0:1);
}
FAutoConsoleCommand AuditCommand(TEXT("RaftSim.AuditGroundSources"),TEXT("Compare actual CPU collision triangles with an editor-exported source manifest; writes fresh report and exits."),
    FConsoleCommandWithArgsDelegate::CreateStatic(&AuditCookedSources));
}
#endif
