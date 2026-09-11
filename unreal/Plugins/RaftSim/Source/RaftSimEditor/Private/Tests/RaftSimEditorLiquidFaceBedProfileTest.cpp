#include "Misc/AutomationTest.h"
#include "Misc/Paths.h"
#include "Misc/FileHelper.h"
#include "Serialization/JsonSerializer.h"
#include "../Materials/RaftSimLiquidFaceBedProfile.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLiquidFaceBedProfileTest,"RaftSim.Editor.LiquidFaceBedProfile",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FLiquidFaceBedProfileTest::RunTest(const FString&)
{
    const FString Base=FPaths::ProjectDir()/TEXT("../tmp");
    auto Read=[](const FString& Path)
    {
        FString Text;TSharedPtr<FJsonObject> Json;
        if(FFileHelper::LoadFileToString(Text,*Path)) FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Json);
        return Json;
    };
    const FString Mesh=Base/TEXT("south-fork-rock-return-xy-candidate-v2-20260907/registered_mesh_source.npz");
    const FString Boundary=Base/TEXT("south-fork-whole-rapid-liquid-float-seeds-20260910/grid_vector_boundary_profile.json");
    const FString BedPath=Base/TEXT("south-fork-liquid-face-bed-20260910/physical_face_bed.json");
    const auto Geometry=Read(Base/TEXT("south-fork-liquid-regional-geometry-v4-20260910/manifest.json"));
    FString Error,Hash;RaftSimLiquidRegionalState::FParent Parent;
    if(!Geometry || !Geometry->TryGetStringField(TEXT("original_mesh_sha256"),Hash) ||
        !RaftSimLiquidRegionalState::DecodeParent(Read(Base/TEXT("south-fork-liquid-regional-state-20260910/manifest.json")),
            Read(Base/TEXT("south-fork-whole-rapid-liquid-float-seeds-20260910/grid_boundary_profile.json")),Parent,Error))
    { AddError(TEXT("Current prepared parent/contact sources required"));return false; }
    FRaftSimLiquidFaceBed Bed;
    if(!RaftSimLiquidFaceBedProfile::Decode(Read(BedPath),Parent,Mesh,Boundary,Hash,Bed,Error))
    { AddError(Error);return false; }
    TestTrue(TEXT("Four complete source-hashed terrain face profiles"),Bed.Knots.Num()>8);
    for(int32 Case=0;Case<6;++Case)
    {
        auto Json=Read(BedPath);if(!Json) return false;
        if(Case==0) Json->SetStringField(TEXT("source_boundary_sha256"),FString::ChrN(64,TCHAR('0')));
        if(Case==1) Json->SetStringField(TEXT("source_mesh_sha256"),FString::ChrN(64,TCHAR('0')));
        if(Case==2)
        {
            auto Axes=Json->GetArrayField(TEXT("canonical_axes"));auto Row=Axes[0]->AsArray();
            Row[0]=MakeShared<FJsonValueNumber>(0);Axes[0]=MakeShared<FJsonValueArray>(Row);
            Json->SetArrayField(TEXT("canonical_axes"),Axes);
        }
        if(Case==3)
        {
            auto Face=Json->GetArrayField(TEXT("faces"))[0]->AsObject();auto Knots=Face->GetArrayField(TEXT("knots_cm"));
            Knots[1]=Knots[0];Face->SetArrayField(TEXT("knots_cm"),Knots);
        }
        if(Case==4)
        { auto Faces=Json->GetArrayField(TEXT("faces"));Faces.Pop();Json->SetArrayField(TEXT("faces"),Faces); }
        if(Case==5)
        {
            auto Extent=Json->GetArrayField(TEXT("extent_cm"));
            Extent[2]=MakeShared<FJsonValueNumber>(Extent[2]->AsNumber()+1e-6);
            Json->SetArrayField(TEXT("extent_cm"),Extent);
        }
        TestFalse(FString::Printf(TEXT("Reject changed source/frame/coverage case%d"),Case),
            RaftSimLiquidFaceBedProfile::Decode(Json,Parent,Mesh,Boundary,Hash,Bed,Error));
        TestTrue(TEXT("Invalid bed clears candidate; no fallback to partial profile"),Bed.Knots.IsEmpty());
    }
    return !HasAnyErrors();
}
