#include "Misc/AutomationTest.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"
#include "../Materials/RaftSimLiquidBoundaryProfile.h"
#include "../Materials/RaftSimLiquidBoundaryLayout.h"

namespace
{
TSharedPtr<FJsonObject> BoundaryFixture(bool Vector,int32 NX=64)
{
    auto Json=MakeShared<FJsonObject>();
    Json->SetStringField(TEXT("schema"),TEXT("raftsim.liquid_grid_boundary.v3"));
    TArray<FVector3f> Rows={{.8f,.6f,0},{-.6f,.8f,0},{-930,367,350},
        {float(NX*50),2400,800},{50,75,800.f/24},{float(NX),32,24},{float(NX+4),36,24},{float((NX+4)*50),2700,800}};
    TArray<TSharedPtr<FJsonValue>> Offsets,Counts;
    for (int32 Face=0;Face<4;++Face)
    {
        Offsets.Add(MakeShared<FJsonValueNumber>(Rows.Num()));
        Counts.Add(MakeShared<FJsonValueNumber>(Face<2?32:NX));
        for (int32 I=0;I<(Face<2?32:NX);++I) Rows.Add(FVector3f(400,600,Face%2?-25:25));
    }
    Json->SetArrayField(TEXT("face_rows_offsets"),Offsets);Json->SetArrayField(TEXT("face_row_counts"),Counts);
    if (Vector)
    {
        Json->SetNumberField(TEXT("vector_rows_offset"),Rows.Num());
        for (int32 Face=0;Face<4;++Face)
            for (int32 I=0;I<(Face<2?32:NX);++I) Rows.Add(Face<2?FVector3f(25,7,0):FVector3f(7,25,0));
    }
    TArray<TSharedPtr<FJsonValue>> Values;
    for (const auto& P:Rows) Values.Add(MakeShared<FJsonValueArray>(TArray<TSharedPtr<FJsonValue>>{
        MakeShared<FJsonValueNumber>(P.X),MakeShared<FJsonValueNumber>(P.Y),MakeShared<FJsonValueNumber>(P.Z)}));
    Json->SetArrayField(TEXT("packed_vectors"),Values);
    return Json;
}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLiquidBoundaryProfileTest,
    "RaftSim.Editor.LiquidBoundaryProfile",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLiquidBoundaryProfileTest::RunTest(const FString&)
{
    using namespace RaftSimLiquidBoundaryProfile;
    FDecoded Decoded;
    auto Scalar=BoundaryFixture(false),Vector=BoundaryFixture(true);
    if (!TestTrue(TEXT("Unequal rectangular scalar profile"),Decode(Scalar,false,Decoded))) return false;
    TestEqual(TEXT("Explicit anisotropic cell metric"),Decoded.CellSize,FVector3f(50,75,800.f/24));
    TestEqual(TEXT("Independent XYZ dimensions"),Decoded.ComputationalCells,FIntVector(68,36,24));
    TestEqual(TEXT("Per-table rectangular ABI marker"),Decoded.Packed[3].Z,-800.f);
    TestEqual(TEXT("Source datum origin preserved"),Decoded.Packed[2],FVector3f(-930,367,350));
    TestEqual(TEXT("Unequal side lengths respected"),Decoded.Packed.Num(),200);
    TestEqual(TEXT("Disk header not mutated"),Scalar->GetArrayField(TEXT("packed_vectors"))[3]->AsArray()[2]->AsNumber(),800.);
    TestTrue(TEXT("Rectangular vector extension"),Decode(Vector,true,Decoded));
    TestEqual(TEXT("Vector extension length"),Decoded.Packed.Num(),392);
    Vector->SetNumberField(TEXT("vector_rows_offset"),260);
    TestFalse(TEXT("Legacy offset cannot address rectangular rows"),Decode(Vector,true,Decoded));
    TestTrue(TEXT("Failed decode clears stale result"),Decoded.Packed.IsEmpty());
    TestFalse(TEXT("Vector rows cannot silently enter scalar decoder"),Decode(BoundaryFixture(true),false,Decoded));
    TestTrue(TEXT("Final two-cell pressure group accepted"),Decode(BoundaryFixture(true,62),true,Decoded));
    TestEqual(TEXT("Tail extent remains exact"),Decoded.ComputationalCells,FIntVector(66,36,24));
    TestFalse(TEXT("Odd X cannot use native half-X dispatch"),Decode(BoundaryFixture(false,63),false,Decoded));
    Scalar->SetStringField(TEXT("schema"),TEXT("unknown"));
    TestFalse(TEXT("Unknown schema rejected"),Decode(Scalar,false,Decoded));
    auto Offsets=BoundaryFixture(false)->GetArrayField(TEXT("face_rows_offsets"));
    Offsets[2]=MakeShared<FJsonValueNumber>(136);
    Scalar=BoundaryFixture(false);Scalar->SetArrayField(TEXT("face_rows_offsets"),Offsets);
    TestFalse(TEXT("Equal-side addressing is rejected"),Decode(Scalar,false,Decoded));

    FString Text;TSharedPtr<FJsonObject> Saved;
    const FString Directory=FPaths::ProjectDir()/TEXT("SourceArt/RaftSim/SouthForkLiquidWindow20260908");
    for (bool WithVectors:{false,true})
    {
        const FString Path=Directory/(WithVectors?TEXT("grid_vector_boundary_profile.json"):TEXT("grid_boundary_profile.json"));
        if (!TestTrue(TEXT("Saved legacy table readable"),FFileHelper::LoadFileToString(Text,*Path)) ||
            !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Saved)) return false;
        TestTrue(TEXT("Actual legacy profile supported"),Decode(Saved,WithVectors,Decoded));
        TestEqual(TEXT("Legacy allocation unchanged"),Decoded.ComputationalCells,FIntVector(68,68,24));
        TestEqual(TEXT("Legacy ABI marker unchanged"),Decoded.Packed[3].Z,24.f);
    }
    const FString Whole=FPaths::ProjectDir()/TEXT("../tmp/south-fork-whole-rapid-liquid-float-seeds-20260910/grid_boundary_profile.json");
    if (!TestTrue(TEXT("Prepared whole-rapid profile readable"),FFileHelper::LoadFileToString(Text,*Whole)) ||
        !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Saved)) return false;
    TestFalse(TEXT("Whole rapid cannot bypass bounded GPU allocation limits"),Decode(Saved,false,Decoded));
    const FString Face=RaftSimLiquidBoundaryFaceHlsl(TEXT("position"),TEXT("test"));
    TestTrue(TEXT("Separate X/Y extent selection"),Face.Contains(TEXT("testHalf.x")) && Face.Contains(TEXT("testHalf.y")));
    TestTrue(TEXT("Unequal side row addressing"),Face.Contains(TEXT("2*(int)testCells.y+(testFace-2)*(int)testCells.x")));
    const FString Grid=RaftSimLiquidBoundaryGridPositionHlsl(TEXT("p"),TEXT("Profile"));
    TestFalse(TEXT("No fixture-centred offset"),Grid.Contains(TEXT("1115.625")));
    TestTrue(TEXT("Uses actual regional floor"),Grid.Contains(TEXT("gridStageOrigin.z")));
    TestTrue(TEXT("Uses per-axis cell size"),Grid.Contains(TEXT("gridStageStep.xy")));
    return true;
}
