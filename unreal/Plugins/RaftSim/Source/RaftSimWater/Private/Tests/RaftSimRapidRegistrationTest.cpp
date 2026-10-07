#include "RaftSimRapidChallengeProfiles.h"
#include "RaftSimRiverWaterConfig.h"
#include "Engine/World.h"
#include "Misc/AutomationTest.h"
#include "Misc/CommandLine.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/ScopeExit.h"
#include "HAL/FileManager.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include <limits>

#if WITH_AUTOMATION_TESTS
namespace
{
FString RegistrationChart(double Angle, double Start, double X0, double Y0)
{
    FString Text=TEXT("{\"schema\":\"raftsim.curved_river_coordinate_map.v1\",\"world_y_sign\":-1,\"vertical_datum_m\":10,\"points\":[");
    for(int32 I=0;I<=200;++I)
    {
        if(I)Text+=TEXT(",");
        const double D=I*2.;
        Text+=FString::Printf(TEXT("[%.15g,%.15g,%.15g,%.15g,%.15g]"),
            Start+D,X0+D*FMath::Cos(Angle),Y0+D*FMath::Sin(Angle),
            -FMath::Sin(Angle),FMath::Cos(Angle));
    }
    return Text+TEXT("]}");
}
FVector RegistrationHeading(const FVector& T,const FVector& L,double Degrees)
{
    const double A=FMath::DegreesToRadians(Degrees);
    return T*FMath::Cos(A)+L*FMath::Sin(A);
}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimRapidRegistrationTest,
    "RaftSim.Continuous.RapidRegistration",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimRapidRegistrationTest::RunTest(const FString&)
{
    const FString Base=FPaths::Combine(FPaths::ProjectSavedDir(),TEXT("Automation"),
        TEXT("rapid-registration-")+FGuid::NewGuid().ToString());
    const FString A=Base+TEXT("-source.json"),B=Base+TEXT("-target.json");
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Base),true);
    ON_SCOPE_EXIT {IFileManager::Get().Delete(*A);IFileManager::Get().Delete(*B);};
    const double Angle=.1;
    if(!FFileHelper::SaveStringToFile(RegistrationChart(0.,0.,0.,0.),*A) ||
       !FFileHelper::SaveStringToFile(RegistrationChart(Angle,1000.,-100.*FMath::Cos(Angle),-100.*FMath::Sin(Angle)),*B))return false;
    auto* Source=NewObject<URaftSimWaterRuntimeAdapter>();
    auto* Target=NewObject<URaftSimWaterRuntimeAdapter>();
    auto* Empty=NewObject<URaftSimWaterRuntimeAdapter>();
    using namespace RaftSimRapidChallengeProfiles;
    TArray<FFeature> Input{{40.,5.,35.,.8f,4.f,.6f},{100.,-8.,-30.,1.1f,3.f,.9f}},Output;
    FString Error;
    TestFalse(TEXT("unloaded maps refuse"),Register(*Source,*Target,Input,Output,Error));
    if(!Source->ConfigureRiverCoordinateMap(A)||!Target->ConfigureRiverCoordinateMap(B))return false;
    if(!TestTrue(TEXT("native coordinate registration"),Register(*Source,*Target,Input,Output,Error)))
    {AddError(Error);return false;}
    TestEqual(TEXT("all sites retained"),Output.Num(),Input.Num());
    for(int32 I=0;I<Input.Num();++I)
    {
        FVector P,Q,ST,SL,TT,TL;FVector2D R;
        Source->RiverToWorldPosition({Input[I].Station,Input[I].Lateral},10.f,P);
        Target->RiverToWorldPosition({Output[I].Station,Output[I].Lateral},10.f,Q);
        Source->WorldToRiverCoordinates(P,R,ST,SL);Target->WorldToRiverCoordinates(Q,R,TT,TL);
        TestTrue(TEXT("physical centre preserved within one cm"),FVector::Distance(P,Q)<1.);
        TestTrue(TEXT("physical normal direction preserved"),RegistrationHeading(ST,SL,Input[I].AngleDegrees).Equals(
            RegistrationHeading(TT,TL,Output[I].AngleDegrees),1.e-8));
        TestTrue(TEXT("shared kernel parameters unchanged"),Input[I].Height==Output[I].Height &&
            Input[I].Length==Output[I].Length && Input[I].Spill==Output[I].Spill);
    }
    TestTrue(TEXT("rotation is not approximated by a station offset"),
        FMath::Abs((Output[0].Station-Input[0].Station)-(Output[1].Station-Input[1].Station))>.1);
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    if(!World)return false;
    ON_SCOPE_EXIT {World->DestroyWorld(false);};
    auto* Config=World->SpawnActor<ARaftSimRiverWaterConfig>();
    if(!Config)return false;
    TArray<FFeature> Resolved;
    TestTrue(TEXT("existing map profiles remain available"),Config->ResolveRapidFeatures(TEXT("L_Hance"),*Target,Resolved,Error));
    TestEqual(TEXT("legacy profile count unchanged"),Resolved.Num(),Features(TEXT("L_Hance")).Num());
    Config->RegisteredRapidFeatures=Output;
    TestFalse(TEXT("serialized sites require chart identity"),Config->ResolveRapidFeatures(TEXT("L_Hance"),*Target,Resolved,Error));
    Config->RegisteredRapidChartFingerprint=Target->GetRiverCoordinateMapFingerprint();
    TestTrue(TEXT("continuous map resolves its own registered sites"),Config->ResolveRapidFeatures(TEXT("L_Colorado_Continuous"),*Target,Resolved,Error));
    TestEqual(TEXT("registered profile count"),Resolved.Num(),Input.Num());
    TestFalse(TEXT("wrong chart refuses"),Config->ResolveRapidFeatures(TEXT("L_Hance"),*Source,Resolved,Error));
    TestTrue(TEXT("failed resolve cannot leak legacy or registered sites"),Resolved.IsEmpty());
    TestFalse(TEXT("unavailable chart refuses"),Config->ResolveRapidFeatures(TEXT("L_Hance"),*Empty,Resolved,Error));
    Input.Add({std::numeric_limits<double>::quiet_NaN(),0.,0.,.8f,4.f,.5f});
    TestFalse(TEXT("nonfinite site refuses entire transfer"),Register(*Source,*Target,Input,Output,Error));
    TestTrue(TEXT("atomic transfer leaves no partial set"),Output.IsEmpty());
    Input.Last().Station=900.;
    TestFalse(TEXT("outside source refuses"),Register(*Source,*Target,Input,Output,Error));
    if(!FFileHelper::SaveStringToFile(TEXT("{}"),*B))return false;
    AddExpectedError(TEXT("coordinate map schema is unsupported"),EAutomationExpectedErrorFlags::Contains,1);
    TestFalse(TEXT("bad reload refuses"),Target->ConfigureRiverCoordinateMap(B));
    TestTrue(TEXT("bad reload clears old identity"),Target->GetRiverCoordinateMapFingerprint().IsEmpty());
    TestFalse(TEXT("bad reload invalidates registered sites"),Config->ResolveRapidFeatures(TEXT("L_Colorado_Continuous"),*Target,Resolved,Error));
    return !HasAnyErrors();
}

// Explicit source paths keep local construction captures out of unit fixtures.
// Run with both arguments to obtain native proof for a real source assembly.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimRapidRegistrationSourcesTest,
    "RaftSim.Continuous.RapidSourceRegistration",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimRapidRegistrationSourcesTest::RunTest(const FString&)
{
    FString Assembly,Chart;
    const bool HasAssembly=FParse::Value(FCommandLine::Get(),TEXT("RaftSimRapidRegistrationAssembly="),Assembly);
    const bool HasChart=FParse::Value(FCommandLine::Get(),TEXT("RaftSimRapidRegistrationChart="),Chart);
    if(!HasAssembly&&!HasChart){AddWarning(TEXT("Real construction source registration NOT exercised: supply assembly and chart arguments"));return true;}
    if(!HasAssembly||!HasChart){AddError(TEXT("Both real source registration arguments are required"));return false;}
    FString Text;TSharedPtr<FJsonObject> Root;
    if(!FFileHelper::LoadFileToString(Text,*Assembly)||!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Root)||!Root.IsValid())return false;
    auto* Target=NewObject<URaftSimWaterRuntimeAdapter>();
    if(!Target->ConfigureRiverCoordinateMap(Chart))return false;
    int32 Count=0,ReachCount=0;
    for(const auto& Value:Root->GetArrayField(TEXT("source_reaches")))
    {
        const auto& Reach=Value->AsObject();const FString Name=Reach->GetStringField(TEXT("name"));
        FString Map;
        if(Name==TEXT("Badger Creek"))Map=TEXT("L_Colorado_BadgerCreek");
        else if(Name==TEXT("House Rock"))Map=TEXT("L_Colorado_HouseRock");
        else if(Name==TEXT("Hance"))Map=TEXT("L_Hance");else continue;
        auto* Source=NewObject<URaftSimWaterRuntimeAdapter>();
        const FString Path=FPaths::Combine(FPaths::GetPath(Assembly),Reach->GetStringField(TEXT("rebased_chart")));
        if(!Source->ConfigureRiverCoordinateMap(Path))return false;
        const auto& Input=RaftSimRapidChallengeProfiles::Features(Map);
        TArray<FRaftSimRapidFeature> Output;FString Error;
        if(!RaftSimRapidChallengeProfiles::Register(*Source,*Target,Input,Output,Error))
        {AddError(Name+TEXT(": ")+Error);return false;}
        double MaxError=0.;
        for(int32 I=0;I<Input.Num();++I)
        {
            FVector P,Q,ST,SL,TT,TL;FVector2D R;
            Source->RiverToWorldPosition({Input[I].Station,Input[I].Lateral},0.f,P);
            Target->RiverToWorldPosition({Output[I].Station,Output[I].Lateral},0.f,Q);
            MaxError=FMath::Max(MaxError,FVector::Dist2D(P,Q));
            Source->WorldToRiverCoordinates(P,R,ST,SL);Target->WorldToRiverCoordinates(Q,R,TT,TL);
            TestTrue(TEXT("real site direction preserved"),RegistrationHeading(ST,SL,Input[I].AngleDegrees).Equals(
                RegistrationHeading(TT,TL,Output[I].AngleDegrees),1.e-6));
        }
        TestTrue(TEXT("real site centres preserved within one cm"),MaxError<=1.);
        AddInfo(FString::Printf(TEXT("Registered %s: %d sites; maximum centre error %.9f cm"),*Name,Output.Num(),MaxError));
        Count+=Output.Num();++ReachCount;
    }
    TestEqual(TEXT("all three production source reaches exercised"),ReachCount,3);
    TestEqual(TEXT("all production source sites exercised"),Count,68);
    return !HasAnyErrors();
}
#endif
