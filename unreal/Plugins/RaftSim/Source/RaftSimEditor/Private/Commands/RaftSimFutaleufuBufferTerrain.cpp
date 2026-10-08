// Targeted update of the reviewed hydraulic buffer chunks in the existing
// continuous scene. No new geometry policy, actor replacement or relaxed
// collision gate. The Python owner backs up packages and saves only our list.
#include "Environment/RaftSimEditorEnvironmentInternal.h"
#include "Materials/RaftSimLiquidDataset.h"
#include "LandscapeDataAccess.h"
#include "LandscapeEdit.h"
#include "LandscapeEditLayer.h"
#include "LandscapeInfo.h"
#include "LandscapeStreamingProxy.h"

namespace RaftSimFutaleufuBufferTerrain
{
static const FString Map=TEXT("/Game/RaftSim/Maps/Continuous/L_Futaleufu_ContinuousContextV1");
struct FChunk
{
    ALandscape* Land=nullptr;
    TArray<uint16> Before,After;
};

static bool Verify(const FChunk& C,const TArray<uint16>& Heights,int64& Vertices,int64& Probes,double& Maximum,FString& Error)
{
    int32 Count=0;
    for(const auto& Weak:C.Land->GetLandscapeInfo()->GetSortedStreamingProxies())
    {
        auto* Proxy=Weak.Get();if(!Proxy || Proxy->IsNaniteEnabled())return false;
        for(ULandscapeComponent* Component:Proxy->LandscapeComponents)
        {
            FLandscapeComponentDataInterface Data(Component,0,false);
            if(!Data.GetRawHeightData())return false;
            const FIntPoint Base=Component->GetSectionBase();
            for(int32 Y=0;Y<=Component->ComponentSizeQuads;++Y)
                for(int32 X=0;X<=Component->ComponentSizeQuads;++X)
                {
                    const int32 Col=Base.X+X,Row=Base.Y+Y;
                    if(Col<0 || Row<0 || Col>=127 || Row>=127 ||
                        FMath::Abs(int32(Data.GetHeight(X,Y))-int32(Heights[Row*127+Col]))>1)
                    {Error=TEXT("Rendered height differs from pinned source: ")+C.Land->GetActorLabel();return false;}
                    ++Count;
                }
        }
    }
    if(Count!=127*127)return false;
    Vertices+=Count;
    // All cells, both triangle interiors: sparse probes can miss a localized
    // hydraulic buffer edit. Read native complex collision, not source PNGs.
    const FVector Origin=C.Land->GetActorLocation();
    for(int32 Row=0;Row<126;++Row)for(int32 Col=0;Col<126;++Col)
        for(const FVector2D F:{FVector2D(.25,.75),FVector2D(.75,.25)})
        {
            const double A=Heights[Row*127+Col],B=Heights[Row*127+Col+1];
            const double D=Heights[(Row+1)*127+Col],E=Heights[(Row+1)*127+Col+1];
            const double H=F.X<F.Y ? (1-F.Y)*A+F.X*E+(F.Y-F.X)*D : (1-F.X)*A+(F.X-F.Y)*B+F.Y*E;
            const double Expected=(H*2400./65535.-150.)*100.;
            const auto Actual=C.Land->GetHeightAtLocation(Origin+FVector((Col+F.X)*200.,(Row+F.Y)*200.,0),EHeightfieldSource::Complex);
            if(!Actual.IsSet() || !FMath::IsFinite(Actual.GetValue()))return false;
            Maximum=FMath::Max(Maximum,FMath::Abs(double(Actual.GetValue())-Expected));++Probes;
        }
    if(Maximum>10.){Error=TEXT("Native complex collision exceeds unchanged 10 cm tolerance");return false;}
    return true;
}

static bool Run(const FString& Request,bool Apply,TSharedPtr<FJsonObject>& Result,FString& Error)
{
    const auto J=FRaftSimLiquidDataset::Read(Request);
    UWorld* World=GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
    if(!J || J->GetStringField(TEXT("schema"))!=TEXT("raftsim.futaleufu_buffer_native_update.v1") ||
        !World || World->GetPackage()->GetName()!=Map || FParse::Param(FCommandLine::Get(),TEXT("NullRHI")))
    {Error=TEXT("Reviewed contract, correct loaded scene and rendering RHI required");return false;}
    const FString Root=FPaths::ConvertRelativePathToFull(FPaths::ProjectDir()/TEXT(".."));
    auto Load=[&](const TSharedPtr<FJsonObject>& Row,const TCHAR* Key,TArray<uint16>& Values)->bool
    {
        const FString Relative=Row->GetStringField(Key);
        if(!FPaths::IsRelative(Relative) || Relative.Contains(TEXT("..")))return false;
        const FString Path=Root/Relative;
        if(FRaftSimLiquidDataset::Hash(Path)!=Row->GetStringField(FString(Key)+TEXT("_sha256")))return false;
        auto& Module=FModuleManager::LoadModuleChecked<ILandscapeEditorModule>(TEXT("LandscapeEditor"));
        const auto* Format=Module.GetHeightmapFormatByExtension(TEXT(".png"));if(!Format)return false;
        auto Imported=Format->Import(*Path,FLandscapeFileResolution(127,127));
        if(Imported.ResultCode==ELandscapeImportResult::Error || Imported.Data.Num()!=127*127)return false;
        Values=MoveTemp(Imported.Data);return true;
    };
    const TSet<FString> Allowed={TEXT("ContinuousTerrain_-8_-2"),TEXT("ContinuousTerrain_-7_-2"),TEXT("ContinuousTerrain_-7_-1"),
        TEXT("ContinuousTerrain_7_19"),TEXT("ContinuousTerrain_8_18"),TEXT("ContinuousTerrain_8_19"),
        TEXT("ContinuousTerrain_22_16"),TEXT("ContinuousTerrain_22_17"),TEXT("ContinuousTerrain_22_18")};
    TMap<FString,ALandscape*> Actors;
    for(TActorIterator<ALandscape> It(World);It;++It)
        if(Allowed.Contains(It->GetActorLabel()))
        {if(Actors.Contains(It->GetActorLabel()))return false;Actors.Add(It->GetActorLabel(),*It);}
    const auto& Rows=J->GetArrayField(TEXT("chunks"));
    if(Actors.Num()!=9 || Rows.Num()!=9)return false;
    TSet<FString> Seen;TArray<FChunk> Chunks;TSet<UPackage*> Packages;
    int64 Vertices=0,Probes=0;double Maximum=0.;
    for(const auto& Value:Rows)
    {
        const auto Row=Value->AsObject();if(!Row)return false;
        const FString Label=Row->GetStringField(TEXT("label"));
        if(!Actors.Contains(Label) || Seen.Contains(Label))return false;
        Seen.Add(Label);FChunk C;C.Land=Actors[Label];
        const auto& XYZ=Row->GetArrayField(TEXT("location_cm"));
        const FVector ExpectedScale(200.,200.,2400.*100./512.*65536./65535.);
        if(XYZ.Num()!=3 || !C.Land->GetActorLocation().Equals(FVector(XYZ[0]->AsNumber(),XYZ[1]->AsNumber(),XYZ[2]->AsNumber()),.0001) ||
            !C.Land->GetActorScale3D().Equals(ExpectedScale,.0001) || !C.Land->GetActorRotation().IsNearlyZero() ||
            C.Land->GetEditLayers().Num()!=1 || !C.Land->GetLandscapeInfo() ||
            !Load(Row,TEXT("before"),C.Before) || !Load(Row,TEXT("after"),C.After))return false;
        if(!Verify(C,Apply ? C.Before : C.After,Vertices,Probes,Maximum,Error))return false;
        Packages.Add(C.Land->GetPackage());
        for(const auto& Weak:C.Land->GetLandscapeInfo()->GetSortedStreamingProxies())Packages.Add(Weak->GetPackage());
        Chunks.Add(MoveTemp(C));
    }
    // Every chunk is checked before the first mutation. Any failed mutation
    // leaves only unsaved changes; the owner never saves without our receipt.
    if(Apply)
    {
        for(auto& C:Chunks)
        {
            C.Land->Modify();
            FLandscapeEditDataInterface Edit(C.Land->GetLandscapeInfo(),C.Land->GetEditLayers()[0]->GetGuid());
            Edit.SetHeightData(0,0,126,126,C.After.GetData(),127,true);
            Edit.Flush();C.Land->ForceLayersFullUpdate();
        }
        FAssetCompilingManager::Get().FinishAllCompilation();
        Vertices=0;Probes=0;Maximum=0.;
        for(const auto& C:Chunks)if(!Verify(C,C.After,Vertices,Probes,Maximum,Error))return false;
    }
    TArray<TSharedPtr<FJsonValue>> Names;
    for(auto* Package:Packages)
    {
        if(!Package || !Package->GetName().StartsWith(TEXT("/Game/__ExternalActors__/RaftSim/Maps/Continuous/L_Futaleufu_ContinuousContextV1/")))
        {Error=TEXT("Unexpected package ownership; no save allowed");return false;}
        Names.Add(MakeShared<FJsonValueString>(Package->GetName()));
    }
    Result=MakeShared<FJsonObject>();Result->SetStringField(TEXT("schema"),TEXT("raftsim.futaleufu_buffer_native_receipt.v1"));
    Result->SetStringField(TEXT("request_sha256"),FRaftSimLiquidDataset::Hash(Request));
    Result->SetBoolField(TEXT("applied_in_memory"),Apply);Result->SetBoolField(TEXT("saved"),false);
    Result->SetNumberField(TEXT("chunks"),Chunks.Num());Result->SetNumberField(TEXT("render_vertices"),Vertices);
    Result->SetNumberField(TEXT("complex_collision_probes"),Probes);Result->SetNumberField(TEXT("maximum_collision_error_cm"),Maximum);
    Result->SetArrayField(TEXT("target_packages"),Names);return true;
}

static void Command(const TArray<FString>& Args)
{
    if(Args.Num()!=3 || (Args[1]!=TEXT("apply") && Args[1]!=TEXT("verify")))return;
    const FString Root=FPaths::ConvertRelativePathToFull(FPaths::ProjectDir()/TEXT(".."));
    for(const int32 I:{0,2})if(!Args[I].StartsWith(TEXT("tmp/")) || Args[I].Contains(TEXT("..")))return;
    if(FPaths::FileExists(Root/Args[2]))return;
    FString Error=TEXT("Native buffer terrain precondition failed");TSharedPtr<FJsonObject> Result;
    if(!Run(Root/Args[0],Args[1]==TEXT("apply"),Result,Error))
    {UE_LOG(LogTemp,Error,TEXT("Futaleufu buffer terrain: %s"),*Error);return;}
    FString Text;FJsonSerializer::Serialize(Result.ToSharedRef(),TJsonWriterFactory<>::Create(&Text));
    FFileHelper::SaveStringToFile(Text,*(Root/Args[2]));
    UE_LOG(LogTemp,Display,TEXT("Futaleufu buffer terrain verified: %s"),*Text);
}
static FAutoConsoleCommand Registration(TEXT("RaftSim.UpdateFutaleufuBufferTerrain"),
    TEXT("<request> <apply|verify> <fresh-receipt>; caller owns backup and targeted save"),FConsoleCommandWithArgsDelegate::CreateStatic(&Command));
}
