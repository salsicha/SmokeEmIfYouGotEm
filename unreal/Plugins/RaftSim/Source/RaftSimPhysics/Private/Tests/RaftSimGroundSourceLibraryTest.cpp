#include "RaftSimGroundSourceLibrary.h"
#include "Dom/JsonObject.h"
#include "Engine/StaticMesh.h"
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimGroundSourceIdentityTest,"RaftSim.Physics.GroundSourceCPUIdentity",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimGroundSourceIdentityTest::RunTest(const FString&)
{
    auto* Mesh=LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cube.Cube"));if(!Mesh)return false;
    const bool Original=Mesh->bAllowCPUAccess;ON_SCOPE_EXIT{Mesh->bAllowCPUAccess=Original;};
    const auto Read=[](UStaticMesh* Input){TSharedPtr<FJsonObject> R;
        FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(URaftSimGroundSourceLibrary::AuditCollisionSource(Input)),R);return R;};
    Mesh->bAllowCPUAccess=false;const auto Before=Read(Mesh);
    Mesh->bAllowCPUAccess=true;const auto After=Read(Mesh);
    if(!Before || !After){AddError(TEXT("native source audit JSON missing"));return false;}
    TestTrue(TEXT("editor can inspect source without pretending cooked availability"),Before->GetBoolField(TEXT("available")) &&
        Before->GetBoolField(TEXT("editor_only_data")) && !Before->GetBoolField(TEXT("allow_cpu_access")));
    TestTrue(TEXT("retention flag is reported independently"),After->GetBoolField(TEXT("available")) && After->GetBoolField(TEXT("allow_cpu_access")));
    const auto Hash=Before->GetStringField(TEXT("collision_source_sha256"));
    TestTrue(TEXT("native SHA256 covers every source face"),Hash.Len()==64 && Before->GetIntegerField(TEXT("triangle_count"))==48);
    TestEqual(TEXT("CPU metadata change leaves exact source identity unchanged"),After->GetStringField(TEXT("collision_source_sha256")),Hash);
    const auto Missing=Read(nullptr);TestTrue(TEXT("missing source is explicit failure"),Missing && !Missing->GetBoolField(TEXT("available")));
    return !HasAnyErrors();
}
#endif
