#include "RaftSimRapidChallengeProfiles.h"
#include "RaftSimPhysicalBreakingSample.h"
#include "RaftSimRiverWaterConfig.h"
#include "Engine/World.h"
#include "Misc/AutomationTest.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/ScopeExit.h"
#include "HAL/FileManager.h"
#include <limits>

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCartesianRapidRegistrationTest,
    "RaftSim.Continuous.CartesianRapidRegistration",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimCartesianRapidRegistrationTest::RunTest(const FString&)
{
    using namespace RaftSimRapidChallengeProfiles;
    const FString Base=FPaths::ProjectSavedDir()/TEXT("Automation")/(TEXT("cartesian-rapid-")+FGuid::NewGuid().ToString());
    const FString A=Base+TEXT("-source.json"),B=Base+TEXT("-target.json");
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Base),true);
    ON_SCOPE_EXIT {IFileManager::Get().Delete(*A);IFileManager::Get().Delete(*B);};
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    if(!World)return false;
    ON_SCOPE_EXIT {World->DestroyWorld(false);};
    auto* Config=World->SpawnActor<ARaftSimRiverWaterConfig>();
    if(!Config)return false;
    const FBox2D Bounds(FVector2D(-500,-500),FVector2D(500,500));
    for(double Sign:{-1.,1.})
    for(double Bearing:{0.,37.,90.,180.,270.})
    {
        const double Angle=FMath::DegreesToRadians(Bearing);
        FString Chart=FString::Printf(TEXT("{\"schema\":\"raftsim.curved_river_coordinate_map.v1\",\"world_y_sign\":%.0f,\"vertical_datum_m\":10,\"points\":["),Sign);
        for(int32 I=0;I<=200;++I)
        {
            if(I)Chart+=TEXT(",");
            Chart+=FString::Printf(TEXT("[%.15g,%.15g,%.15g,%.15g,%.15g]"),I*2.,
                I*2.*FMath::Cos(Angle),I*2.*FMath::Sin(Angle),-FMath::Sin(Angle),FMath::Cos(Angle));
        }
        Chart+=TEXT("]}");
        const FString Cartesian=FString::Printf(TEXT("{\"schema\":\"raftsim.cartesian_water_coordinate_map.v1\",\"world_y_sign\":%.0f,\"vertical_datum_m\":10,\"hydraulic_bounds_m\":[-500,-500,500,500]}"),Sign);
        if(!FFileHelper::SaveStringToFile(Chart,*A)||!FFileHelper::SaveStringToFile(Cartesian,*B))return false;
        auto* Source=NewObject<URaftSimWaterRuntimeAdapter>();
        auto* Target=NewObject<URaftSimWaterRuntimeAdapter>();
        if(!Source->ConfigureRiverCoordinateMap(A)||!Target->ConfigureRiverCoordinateMap(B))return false;
        const TArray<FFeature> Input{{100.,-8.,-30.,1.1f,3.f,.9f}};
        TArray<FFeature> Output,Resolved;FString Error;
        if(!TestTrue(TEXT("curved profile registers into Cartesian water"),Register(*Source,*Target,Input,Output,Error)))
        {AddError(Error);return false;}
        TestEqual(TEXT("all authored sites retained"),Output.Num(),1);
        FVector P,Q,ST,SL,TT,TL;FVector2D R;
        if(!Source->RiverToWorldPosition({Input[0].Station,Input[0].Lateral},10.f,P) ||
            !Target->RiverToWorldPosition({Output[0].Station,Output[0].Lateral},10.f,Q) ||
            !Source->WorldToRiverCoordinates(P,R,ST,SL) || !Target->WorldToRiverCoordinates(Q,R,TT,TL))return false;
        TestTrue(TEXT("registered world centre unchanged"),P.Equals(Q,1.e-5));
        Config->RegisteredRapidFeatures=Output;
        Config->RegisteredRapidChartFingerprint=Target->GetRiverCoordinateMapFingerprint();
        TestTrue(TEXT("Cartesian configuration resolves its fingerprint-bound sites"),
            Config->ResolveRapidFeatures(TEXT("L_Futaleufu_ContinuousContextV1"),*Target,Resolved,Error));
        TestEqual(TEXT("resolved site count"),Resolved.Num(),1);
        double Min=0.,Max=0.;
        TestFalse(TEXT("Cartesian X is still not a downstream progress station"),Target->GetExactRiverStationRangeM(Min,Max));
        for(double Along:{-3.,0.,.749,.751,3.})
        for(double Across:{-7.,0.,7.})
        {
            const FVector V=ST*Along+SL*Across;
            auto Sample=[&](const FVector2D&,FRaftSimWaterSample& W)
            {W.bWet=true;W.DepthMeters=3.f;W.VelocityMetersPerSecond={FVector::DotProduct(V,TT),FVector::DotProduct(V,TL),0.};return true;};
            TArray<URaftSimWaterRuntimeAdapter::FSupportBreakingSite> Sites;
            TestEqual(TEXT("activation follows original downstream, not east or diagonal normal"),
                Append(Output,Bounds,Sample,Sites),Along>=.75?1:0);
        }
        auto SourceSample=[](const FVector2D&,FRaftSimWaterSample& W)
        {W.bWet=true;W.DepthMeters=3.f;W.VelocityMetersPerSecond={3.,0.,0.};return true;};
        const FVector V=ST*3.;
        const FVector2D TargetBulk(FVector::DotProduct(V,TT),FVector::DotProduct(V,TL));
        auto TargetSample=[&](const FVector2D&,FRaftSimWaterSample& W)
        {W.bWet=true;W.DepthMeters=3.f;W.VelocityMetersPerSecond={TargetBulk.X,TargetBulk.Y,0.};return true;};
        TArray<URaftSimWaterRuntimeAdapter::FSupportBreakingSite> OldSites,NewSites;
        if(Append(Input,Bounds,SourceSample,OldSites)!=1 || Append(Output,Bounds,TargetSample,NewSites)!=1)return false;
        Source->ConfigureFeatureKinematics(true);Target->ConfigureFeatureKinematics(true);
        Source->ConfigureRaftSupportBreakingSites(OldSites,0.f,2.f);
        Target->ConfigureRaftSupportBreakingSites(NewSites,0.f,2.f);
        // Real shared production functions, not a test-only fluid substitute.
        for(const FVector2D Delta:{FVector2D(0,0),FVector2D(4.4,0),FVector2D(-3,3),FVector2D(60,0),FVector2D(0,20)})
        {
            const FVector2D Local=FVector2D(Input[0].Station,Input[0].Lateral)+Delta;
            FVector WorldPoint,UnusedT,UnusedL;FVector2D Grid;
            if(!Source->RiverToWorldPosition(Local,10.f,WorldPoint) || !Target->WorldToRiverCoordinates(WorldPoint,Grid,UnusedT,UnusedL))return false;
            float OldFoam=0.f,NewFoam=0.f;
            const float OldHeight=RaftSimPhysicalBreakingSample::Evaluate<true>(Local,OldSites,0.f,&OldFoam);
            const float NewHeight=RaftSimPhysicalBreakingSample::Evaluate<true>(Grid,NewSites,0.f,&NewFoam);
            TestTrue(TEXT("shared visible/support relief survives registration"),FMath::Abs(OldHeight-NewHeight)<1.e-5f);
            TestTrue(TEXT("shared froth footprint survives registration"),FMath::Abs(OldFoam-NewFoam)<1.e-5f);
            for(float Immersion:{.85f,1.f})
            {
                const auto OldVelocity=Source->ComputeFeatureVelocityAtRiverCoordinates(Local,{3.,0.},3.f,Immersion);
                const auto NewVelocity=Target->ComputeFeatureVelocityAtRiverCoordinates(Grid,TargetBulk,3.f,Immersion);
                const FVector OldWorld=ST*OldVelocity.X+SL*OldVelocity.Y+FVector::UpVector*OldVelocity.Z;
                const FVector NewWorld=TT*NewVelocity.X+TL*NewVelocity.Y+FVector::UpVector*NewVelocity.Z;
                TestTrue(TEXT("immersed hull and surface currents retain world direction and magnitude"),OldWorld.Equals(NewWorld,1.e-5));
            }
            if(Delta.X==60.)
            {
                TestEqual(TEXT("no registered relief in downstream pool"),NewHeight,0.f);
                TestEqual(TEXT("no registered froth in downstream pool"),NewFoam,0.f);
            }
        }
        Config->RegisteredRapidFeatures[0].Lateral=501.;
        TestFalse(TEXT("north/south bounds checked, not only east/west"),Config->ResolveRapidFeatures(TEXT(""),*Target,Resolved,Error));
        TestTrue(TEXT("failed resolve clears stale features"),Resolved.IsEmpty());
        Config->RegisteredRapidFeatures=Output;
        Config->RegisteredRapidFeatures[0].FlowAxisDegrees=std::numeric_limits<double>::quiet_NaN();
        TestFalse(TEXT("nonfinite downstream orientation refuses"),Config->ResolveRapidFeatures(TEXT(""),*Target,Resolved,Error));
        Config->RegisteredRapidFeatures=Output;
        Config->RegisteredRapidChartFingerprint=Source->GetRiverCoordinateMapFingerprint();
        TestFalse(TEXT("different chart identity refuses"),Config->ResolveRapidFeatures(TEXT(""),*Target,Resolved,Error));
        TArray<FFeature> Roundtrip;
        if(!TestTrue(TEXT("Cartesian profile can roundtrip to the source chart"),Register(*Target,*Source,Output,Roundtrip,Error)))return false;
        TestTrue(TEXT("roundtrip coordinates and both axes preserved"),
            FMath::Abs(Roundtrip[0].Station-Input[0].Station)<1.e-5 && FMath::Abs(Roundtrip[0].Lateral-Input[0].Lateral)<1.e-5 &&
            FMath::Abs(Roundtrip[0].AngleDegrees-Input[0].AngleDegrees)<1.e-5 && FMath::Abs(Roundtrip[0].FlowAxisDegrees)<1.e-5);
    }
    return !HasAnyErrors();
}
#endif
