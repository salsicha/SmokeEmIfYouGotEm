#include "RaftSimStoredBankContour.h"
#include "Misc/AutomationTest.h"
#include "Misc/FileHelper.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "HAL/PlatformTime.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimStoredBankContourTest,"RaftSim.M4.ThreeWetStoredCoordinates",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimStoredBankContourTest::RunTest(const FString&)
{
    using namespace RaftSimThreeWetBankContour;
    const double Bed[]={8.711944580078125,8.45587158203125,8.5344696044921875,8.3977813720703125};
    const double H[]={0.,double(.061720576137304306f),double(.17600621283054352f),double(.16925844550132751f)};
    FCurve C;if(!TestTrue(TEXT("original v22 donors"),C.Init(Bed,H)))return false;
    struct FMap{FVector2D O,Step,RenderOrigin;};
    const FMap Maps[]={
        {FVector2D(-542600.,-360200.),FVector2D(-100.,-100.),FVector2D(-542600.,-360200.)},
        {FVector2D(0.,0.),FVector2D(100.,100.),FVector2D(0.,0.)},
        {FVector2D(-542600.,-360200.),FVector2D(100.,-100.),FVector2D(-542600.,-360200.)},
        {FVector2D(361100.,-543000.),FVector2D(-100.,100.),FVector2D(361100.,-543000.)},
        // Original source_id26184 = row116,col84 in the225-wide captured
        // grid. ONE grid origin (not one origin per bank) preserves edges.
        {FVector2D(-542600.,-360200.),FVector2D(-100.,-100.),FVector2D(-551000.,-348600.)}
    };
    TArray<TSharedPtr<FJsonValue>> Cases;
    const auto Pair=[](const FVector2D& P)
    {
        TArray<TSharedPtr<FJsonValue>> A;
        for(double V:{P.X,P.Y})A.Add(MakeShared<FJsonValueString>(FString::Printf(TEXT("%.17g"),V)));
        return A;
    };
    for(int32 K=0;K<UE_ARRAY_COUNT(Maps);++K)
    {
        const auto& M=Maps[K];RaftSimStoredBankContour::FStorage Storage;
        if(!TestTrue(TEXT("Cartesian GPU storage map valid"),Storage.Init(C,M.O,
            M.O+FVector2D(M.Step.X,0.),M.O+FVector2D(0.,M.Step.Y),.1,M.RenderOrigin)))return false;
        FResult R;const uint32 Control=VectorGetControlRegister();const double Begin=FPlatformTime::Seconds();
        const bool Good=RaftSimStoredBankContour::Build(C,Storage,R);
        const double Ms=1000.*(FPlatformTime::Seconds()-Begin);
        AddInfo(FString::Printf(TEXT("StoredBank case=%d built=%d boundary=%d triangles=%d coefficient_tests=%d construction_ms=%.6f"),
            K,int32(Good),R.Boundary.Num(),R.Triangles.Num(),R.Stats.CoefficientTests,Ms));
        if(!Good)AddInfo(FString::Printf(TEXT("StoredBank failure_stage=%d A=(%.17g,%.17g) B=(%.17g,%.17g)"),
            R.Stats.FailedStage,R.Stats.FailedA.X,R.Stats.FailedA.Y,R.Stats.FailedB.X,R.Stats.FailedB.Y));
        TestEqual(TEXT("storage proof restores floating point state"),VectorGetControlRegister(),Control);
        if(!TestTrue(TEXT("whole stored contour certified"),Good))return false;
        TestEqual(TEXT("complete wet polygon triangulation"),R.Triangles.Num(),R.Polygon.Num()-2);
        for(const auto& P:R.Polygon)
        {
            const auto World=Storage.BufferPosition(P);
            const auto Reload=Storage.Local(World);
            TestTrue(TEXT("actual float buffer storage is idempotent"),Storage.BufferPosition(Reload)==World);
            TestTrue(TEXT("certificate bounds bind the submitted coordinate"),SamePoint(P,Reload));
        }
        TestTrue(TEXT("canonical shared crossings retained exactly"),
            Storage.BufferPosition(R.Boundary[0])==Storage.Crossings[0] && Storage.BufferPosition(R.Boundary.Last())==Storage.Crossings[1]);
        auto Item=MakeShared<FJsonObject>();Item->SetNumberField(TEXT("case"),K);
        Item->SetNumberField(TEXT("construction_ms"),Ms);Item->SetNumberField(TEXT("coefficient_tests"),R.Stats.CoefficientTests);
        Item->SetArrayField(TEXT("origin_cm"),Pair(M.O));Item->SetArrayField(TEXT("end_cm"),Pair(M.O+M.Step));
        Item->SetArrayField(TEXT("render_origin_cm"),Pair(Storage.RenderOrigin));
        Item->SetStringField(TEXT("width_cm"),TEXT("0.10000000000000001"));
        TArray<TSharedPtr<FJsonValue>> BValues,HValues,Boundary,Inner,Polygon,Triangles;
        for(int32 I=0;I<4;++I)
        {
            BValues.Add(MakeShared<FJsonValueString>(FString::Printf(TEXT("%.17g"),Bed[I])));
            HValues.Add(MakeShared<FJsonValueString>(FString::Printf(TEXT("%.17g"),H[I])));
        }
        for(const auto& P:R.Boundary)Boundary.Add(MakeShared<FJsonValueArray>(Pair(Storage.BufferPosition(P))));
        // Inner dry proof is mathematical geometry, not another submitted surface.
        for(const auto& P:R.InnerBoundary)Inner.Add(MakeShared<FJsonValueArray>(Pair(P.XY)));
        for(const auto& P:R.Polygon)Polygon.Add(MakeShared<FJsonValueArray>(Pair(Storage.BufferPosition(P))));
        for(const auto& T:R.Triangles)
        {
            TArray<TSharedPtr<FJsonValue>> Ids;
            for(int32 I:{T.X,T.Y,T.Z})Ids.Add(MakeShared<FJsonValueNumber>(I));
            Triangles.Add(MakeShared<FJsonValueArray>(Ids));
        }
        Item->SetArrayField(TEXT("bed"),BValues);Item->SetArrayField(TEXT("depth"),HValues);
        Item->SetArrayField(TEXT("boundary_buffer_cm"),Boundary);Item->SetArrayField(TEXT("inner_local"),Inner);
        Item->SetArrayField(TEXT("polygon_buffer_cm"),Polygon);Item->SetArrayField(TEXT("triangles"),Triangles);
        Cases.Add(MakeShared<FJsonValueObject>(Item));
    }
    RaftSimStoredBankContour::FStorage Bad;FResult R;
    RaftSimStoredBankContour::FStorage Unrebased;
    TestTrue(TEXT("unrebased captured map initializes"),Unrebased.Init(C,Maps[0].O,
        Maps[0].O+FVector2D(-100.,0.),Maps[0].O+FVector2D(0.,-100.),.1));
    TestFalse(TEXT("unrebased captured failure retained, NOT declared safe"),RaftSimStoredBankContour::Build(C,Unrebased,R));
    double Difference=0.;
    TestFalse(TEXT("inexact origin subtraction rejected"),RaftSimStoredBankContour::FStorage::ExactDifference(1.,1.e-100,Difference));
    TestFalse(TEXT("uninitialized storage cannot certify"),RaftSimStoredBankContour::Build(C,Bad,R));
    TestFalse(TEXT("sheared map rejected rather than assumed Cartesian"),Bad.Init(C,{0.,0.},{100.,1.},{0.,100.},.1));
    TestFalse(TEXT("coarse GPU coordinates reject the one millimetre budget"),Bad.Init(C,{10000000.,10000000.},
        {10000100.,10000000.},{10000000.,10000100.},.1));
    TestFalse(TEXT("invalid reinitialization cannot reuse old map"),RaftSimStoredBankContour::Build(C,Bad,R));
    FString Path;
    if(FParse::Value(FCommandLine::Get(),TEXT("RaftSimStoredBankExport="),Path))
    {
        auto Root=MakeShared<FJsonObject>();Root->SetArrayField(TEXT("cases"),Cases);
        Root->SetBoolField(TEXT("normal_renderer_integrated"),false);Root->SetBoolField(TEXT("gameplay_accepted"),false);
        FString Text;auto Writer=TJsonWriterFactory<>::Create(&Text);
        TestTrue(TEXT("stored contour export serializes"),FJsonSerializer::Serialize(Root,Writer));
        TestTrue(TEXT("stored contour export saved"),FFileHelper::SaveStringToFile(Text,*Path));
    }
    return !HasAnyErrors();
}
#endif
