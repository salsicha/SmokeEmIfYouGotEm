#include "RaftSimRapidChallengeProfiles.h"
#include "RaftSimPhysicalBreakingSample.h"
#include "Misc/AutomationTest.h"
#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimRapidChallengeProfilesTest,
    "RaftSim.Water.RapidChallengeProfiles",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimRapidChallengeProfilesTest::RunTest(const FString&)
{
    using namespace RaftSimRapidChallengeProfiles;
    const FFeature Coverage{100.,0.,0.,1.f,5.f,.5f};
    TestFalse(TEXT("a downstream feature is not required in an unrelated earlier rapid"),OverlapsReach(Coverage,0,80));
    TestTrue(TEXT("crest and tail coverage intersects the section"),OverlapsReach(Coverage,120,140));
    TestTrue(TEXT("centre passes within the real compact footprint"),InsideReliefFootprint(Coverage,FVector2D(105,0)));
    TestFalse(TEXT("a legitimate lateral bypass is not a feature encounter"),InsideReliefFootprint(Coverage,FVector2D(105,20)));
    TestFalse(TEXT("downstream pool is outside the feature footprint"),InsideReliefFootprint(Coverage,FVector2D(136,0)));
    const FFeature Diagonal{100.,0.,90.,1.f,5.f,.5f};
    TestTrue(TEXT("rotated width projects onto reach"),OverlapsReach(Diagonal,111,112));
    TestFalse(TEXT("rotated footprint does not use unrotated tail"),OverlapsReach(Diagonal,120,140));
    TestEqual(TEXT("training unchanged"),Features(TEXT("L_RaftSimTestTank")).Num(),0);
    TestEqual(TEXT("Badger has a right entry hydraulic and five three-lane train waves"),Features(TEXT("L_Colorado_BadgerCreek")).Num(),17);
    TestEqual(TEXT("Badger PIE uses the same registered reach"),Features(TEXT("UEDPIE_0_L_Colorado_BadgerCreek")).Num(),17);
    TestFalse(TEXT("Badger lookalike is not playable"),HasProfile(TEXT("Other_L_Colorado_BadgerCreek")));
    TestEqual(TEXT("House Rock has leftward lateral, two left hydraulics and exit train"),Features(TEXT("L_Colorado_HouseRock")).Num(),11);
    TestFalse(TEXT("House Rock lookalike is not playable"),HasProfile(TEXT("Other_L_Colorado_HouseRock")));
    TestEqual(TEXT("Soap Creek uses centre/left hydraulics and a lower train"),Features(TEXT("L_Colorado_SoapCreek")).Num(),18);
    TestEqual(TEXT("Soap Creek PIE uses the same profile"),Features(TEXT("UEDPIE_0_L_Colorado_SoapCreek")).Num(),18);
    TestFalse(TEXT("Soap Creek lookalike is not playable"),HasProfile(TEXT("Other_L_Colorado_SoapCreek")));
    TestEqual(TEXT("Georgie has distinct right hole, wave, lateral and tail"),Features(TEXT("L_Colorado_Georgie")).Num(),8);
    TestEqual(TEXT("Georgie PIE uses the same profile"),Features(TEXT("UEDPIE_0_L_Colorado_Georgie")).Num(),8);
    TestFalse(TEXT("Georgie lookalike is not playable"),HasProfile(TEXT("Other_L_Colorado_Georgie")));
    TestFalse(TEXT("Georgie is not the separate 24 and a half mile rapid"),HasProfile(TEXT("L_Colorado_24HalfMile")));
    TestEqual(TEXT("Unkar has left hydraulics, a diagonal and four centre train waves"),Features(TEXT("L_Colorado_Unkar")).Num(),15);
    TestEqual(TEXT("Unkar PIE uses the same profile"),Features(TEXT("UEDPIE_0_L_Colorado_Unkar")).Num(),15);
    TestFalse(TEXT("Unkar lookalike is not playable"),HasProfile(TEXT("Other_L_Colorado_Unkar")));
    TestTrue(TEXT("Pacuare uses catalogued hydraulic profiles"),HasProfile(TEXT("L_UpperHuacas")));
    TestFalse(TEXT("Cartesian evidence requires registered coordinates, not station as eastings"),HasProfile(TEXT("L_ZambeziUpperGorge")));
    TestFalse(TEXT("profile lookalikes are not playable maps"),HasProfile(TEXT("Other_L_Hance")));
    TestTrue(TEXT("PIE keeps its named profile"),HasProfile(TEXT("UEDPIE_0_L_Hance")));
    TestEqual(TEXT("no suffix matching impostors"),Features(TEXT("Other_L_Hance")).Num(),0);
    TestEqual(TEXT("PIE uses same Hance features"),Features(TEXT("UEDPIE_0_L_Hance")).Num(),40);
    TArray<URaftSimWaterRuntimeAdapter::FSupportBreakingSite> Sites;
    const FBox2D Bounds(FVector2D(5900,-50),FVector2D(6580,50));
    auto Wet=[](const FVector2D&,FRaftSimWaterSample& W){W.bWet=true;W.DepthMeters=2;W.VelocityMetersPerSecond=FVector(3,0,0);return true;};
    TestTrue(TEXT("linked sequence also includes the catalogued Green Highway"),Append(TEXT("L_Zambezi"),Bounds,Wet,Sites)>34);
    for(const auto& S:Sites)
    {
        TestTrue(TEXT("bounded existing crest amplitude"),S.PhysicalCrestHeightMeters>0 && S.PhysicalCrestHeightMeters<=1.2f);
        TestTrue(TEXT("local envelope, not a global relief cap"),S.bLocalEnvelopeCap);
    }
    auto* Water=NewObject<URaftSimWaterRuntimeAdapter>();
    Water->ConfigureFeatureKinematics(true);
    Water->ConfigureRaftSupportBreakingSites(Sites,0.f,2.f);
    const auto& Director=Sites[0];
    const FVector2D ReturnLane=Director.RiverCoordinatesMeters+4.4*Director.FlowDirection;
    const auto Surface=Water->ComputeFeatureVelocityAtRiverCoordinates(ReturnLane,FVector2D(3,0),2.f,1.f);
    const auto Immersed=Water->ComputeFeatureVelocityAtRiverCoordinates(ReturnLane,FVector2D(3,0),2.f,.85f);
    TestTrue(TEXT("Director surface transport pushes left toward the Crease"),Surface.Y>.5);
    TestTrue(TEXT("shallow immersed hull receives the same leftward shove"),Immersed.Y>.5);
    float Foam=0;
    for(double Lateral:{-12.,-9.,-6.,-3.,0.,3.,6.,9.,12.})
    {
        TestTrue(TEXT("Giants crest spans the formerly bypassed side lanes"),
            RaftSimPhysicalBreakingSample::Evaluate<true>(FVector2D(6360,Lateral),Sites,0.f,&Foam)>.25f);
        const auto Current=Water->ComputeFeatureVelocityAtRiverCoordinates(FVector2D(6364.4,Lateral),FVector2D(3,0),2.f,1.f);
        TestTrue(TEXT("wide train affects the same surface-current path, not just pixels"),Current.X<2.5);
    }
    TestEqual(TEXT("downstream pool has no authored height"),RaftSimPhysicalBreakingSample::Evaluate<true>(FVector2D(6560,0),Sites,0.f,&Foam),0.f);
    TestEqual(TEXT("downstream pool has no authored froth"),Foam,0.f);
    Sites.Reset();
    auto Pool=[](const FVector2D&,FRaftSimWaterSample& W){W.bWet=true;W.DepthMeters=2;W.VelocityMetersPerSecond=FVector(.1,0,0);return true;};
    TestEqual(TEXT("quiet pools cannot activate a named roller"),Append(TEXT("L_Zambezi"),Bounds,Pool,Sites),0);
    auto Dry=[](const FVector2D&,FRaftSimWaterSample& W){W.bWet=false;W.DepthMeters=0;W.VelocityMetersPerSecond=FVector(3,0,0);return true;};
    TestEqual(TEXT("dry/blocked cells remain authoritative"),Append(TEXT("L_Zambezi"),Bounds,Dry,Sites),0);
    for(const TCHAR* Map:{TEXT("L_Hance"),TEXT("L_UpperHuacas"),TEXT("L_Terminator"),TEXT("L_LavaCanyon"),TEXT("L_Zambezi"),TEXT("L_Colorado_Georgie")})
    {
        TestTrue(TEXT("same immutable profile storage on repeated queries"),&Features(Map)==&Features(Map));
        for(const auto& F:Features(Map))
        {
            TestTrue(TEXT("finite bounded authored profile"),FMath::IsFinite(F.Station) && FMath::IsFinite(F.Lateral) &&
                F.Height>0.f && F.Height<=1.2f && F.Length>=2.f && F.Length<=7.f && F.Spill>=0.f && F.Spill<=1.f);
        }
        Sites.Reset();
        TestEqual(TEXT("no effects outside the actual visible region"),Append(Map,FBox2D(FVector2D(-1000,-10),FVector2D(-900,10)),Wet,Sites),0);
    }
    Sites.Reset();
    Append(TEXT("L_LavaCanyon"),FBox2D(FVector2D(755,-12),FVector2D(765,0)),Wet,Sites);
    Water->ConfigureRaftSupportBreakingSites(Sites,0.f,2.f);
    const auto Bidwell=Water->ComputeFeatureVelocityAtRiverCoordinates(FVector2D(763.604,-8.524),FVector2D(3,0),2.f,.85f);
    TestTrue(TEXT("Bidwell's documented right-bank lateral pushes immersed hull river-left"),Bidwell.Y>.4);
    Sites.Reset();
    Append(TEXT("L_Colorado_BadgerCreek"),FBox2D(FVector2D(700,-80),FVector2D(1100,80)),Wet,Sites);
    TestTrue(TEXT("Badger entry hole uses actual shared relief"),
        RaftSimPhysicalBreakingSample::Evaluate<true>(FVector2D(790,-24),Sites,0.f,&Foam)>.25f);
    TestEqual(TEXT("Badger's left tongue is not blocked by the right hydraulic"),
        RaftSimPhysicalBreakingSample::Evaluate<true>(FVector2D(790,10),Sites,0.f,&Foam),0.f);
    TestEqual(TEXT("Badger froth stops in the downstream pool"),
        RaftSimPhysicalBreakingSample::Evaluate<true>(FVector2D(1050,0),Sites,0.f,&Foam),0.f);
    TestEqual(TEXT("Badger pool has no profile foam"),Foam,0.f);
    Sites.Reset();
    Append(TEXT("L_Colorado_HouseRock"),FBox2D(FVector2D(700,-80),FVector2D(1100,80)),Wet,Sites);
    Water->ConfigureRaftSupportBreakingSites(Sites,0.f,2.f);
    const auto& HouseLateral=Sites[0];
    const FVector2D HouseReturn=HouseLateral.RiverCoordinatesMeters+4.4*HouseLateral.FlowDirection;
    const auto HouseHullCurrent=Water->ComputeFeatureVelocityAtRiverCoordinates(HouseReturn,FVector2D(3,0),2.f,.85f);
    TestTrue(TEXT("House Rock immersed hull current moves left with the visible diagonal"),HouseHullCurrent.Y>.4);
    TestTrue(TEXT("House Rock lower left hole is actual relief"),
        RaftSimPhysicalBreakingSample::Evaluate<true>(FVector2D(882,10),Sites,0.f,&Foam)>.25f);
    TestEqual(TEXT("House Rock right route is not blocked by a river-wide authored hole"),
        RaftSimPhysicalBreakingSample::Evaluate<true>(FVector2D(882,-8),Sites,0.f,&Foam),0.f);
    TestEqual(TEXT("House Rock pool has no authored height"),
        RaftSimPhysicalBreakingSample::Evaluate<true>(FVector2D(1050,0),Sites,0.f,&Foam),0.f);
    TestEqual(TEXT("House Rock pool has no profile foam"),Foam,0.f);
    Sites.Reset();
    Append(TEXT("L_Colorado_SoapCreek"),FBox2D(FVector2D(700,-80),FVector2D(1200,80)),Wet,Sites);
    Water->ConfigureRaftSupportBreakingSites(Sites,0.f,2.f);
    TestTrue(TEXT("Soap centre entry hydraulic has actual shared relief"),
        RaftSimPhysicalBreakingSample::Evaluate<true>(FVector2D(790,0),Sites,0.f,&Foam)>.25f);
    TestEqual(TEXT("Soap right entry tongue is outside the stronger centre holes"),
        RaftSimPhysicalBreakingSample::Evaluate<true>(FVector2D(790,-16),Sites,0.f,&Foam),0.f);
    const auto SoapHull=Water->ComputeFeatureVelocityAtRiverCoordinates(FVector2D(794.4,0),FVector2D(3,0),2.f,.85f);
    TestTrue(TEXT("Soap immersed hull encounters the same roller as visible surface"),SoapHull.X<2.5);
    TestTrue(TEXT("Soap right route still meets the lower wave train"),
        RaftSimPhysicalBreakingSample::Evaluate<true>(FVector2D(1020,-12),Sites,0.f,&Foam)>.25f);
    TestEqual(TEXT("Soap downstream pool has no authored height"),
        RaftSimPhysicalBreakingSample::Evaluate<true>(FVector2D(1170,0),Sites,0.f,&Foam),0.f);
    TestEqual(TEXT("Soap downstream pool has no authored froth"),Foam,0.f);
    Sites.Reset();
    TestEqual(TEXT("Soap quiet pool cannot activate rollers"),Append(TEXT("L_Colorado_SoapCreek"),FBox2D(FVector2D(700,-80),FVector2D(1200,80)),Pool,Sites),0);
    TestEqual(TEXT("Soap dry cell cannot activate rollers"),Append(TEXT("L_Colorado_SoapCreek"),FBox2D(FVector2D(700,-80),FVector2D(1200,80)),Dry,Sites),0);
    Sites.Reset();
    const FBox2D GeorgieBounds(FVector2D(750,-60),FVector2D(1000,60));
    TestEqual(TEXT("Georgie appends all wet production sites"),Append(TEXT("L_Colorado_Georgie"),GeorgieBounds,Wet,Sites),8);
    Water->ConfigureRaftSupportBreakingSites(Sites,0.f,2.f);
    const float GeorgieWave=RaftSimPhysicalBreakingSample::Evaluate<true>(FVector2D(822,0),Sites,0.f,&Foam);
    TestTrue(TEXT("Georgie standing wave has actual shared relief"),GeorgieWave>.25f);
    TestTrue(TEXT("Georgie standing wave generates local froth"),Foam>0.f);
    TestTrue(TEXT("Georgie right hole is a separate physical feature"),
        RaftSimPhysicalBreakingSample::Evaluate<true>(FVector2D(826,-18),Sites,0.f,&Foam)>.25f);
    TestTrue(TEXT("Georgie right-of-centre seam is lower than the main crest"),
        FMath::Abs(RaftSimPhysicalBreakingSample::Evaluate<true>(FVector2D(822,-9),Sites,0.f,&Foam))<GeorgieWave*.5f);
    const auto GeorgieSurface=Water->ComputeFeatureVelocityAtRiverCoordinates(FVector2D(830.4,-18),FVector2D(3,0),2.f,1.f);
    const auto GeorgieHull=Water->ComputeFeatureVelocityAtRiverCoordinates(FVector2D(830.4,-18),FVector2D(3,0),2.f,.85f);
    TestTrue(TEXT("Georgie surface and immersed hull share the right-hole return"),GeorgieSurface.X<2.5 && GeorgieHull.X<2.5);
    TestEqual(TEXT("Georgie does not add relief in the downstream pool"),
        RaftSimPhysicalBreakingSample::Evaluate<true>(FVector2D(960,0),Sites,0.f,&Foam),0.f);
    TestEqual(TEXT("Georgie froth ends before the downstream pool"),Foam,0.f);
    TestTrue(TEXT("Georgie return current also ends before the pool"),
        Water->ComputeFeatureVelocityAtRiverCoordinates(FVector2D(960,0),FVector2D(3,0),2.f,.85f).Equals(FVector(3,0,0),1.e-6));
    Sites.Reset();
    TestEqual(TEXT("Georgie quiet pools cannot activate named rollers"),Append(TEXT("L_Colorado_Georgie"),GeorgieBounds,Pool,Sites),0);
    TestEqual(TEXT("Georgie dry cells cannot activate named rollers"),Append(TEXT("L_Colorado_Georgie"),GeorgieBounds,Dry,Sites),0);
    Sites.Reset();
    const FBox2D UnkarBounds(FVector2D(700,-60),FVector2D(1040,60));
    TestEqual(TEXT("Unkar appends all wet production sites"),Append(TEXT("L_Colorado_Unkar"),UnkarBounds,Wet,Sites),15);
    Water->ConfigureRaftSupportBreakingSites(Sites,0.f,2.f);
    TestTrue(TEXT("Unkar left hole uses shared physical relief"),
        RaftSimPhysicalBreakingSample::Evaluate<true>(FVector2D(776,24),Sites,0.f,&Foam)>.25f);
    TestTrue(TEXT("Unkar left hole produces local froth"),Foam>0.f);
    TestEqual(TEXT("Unkar preserves the centre entry tongue"),
        RaftSimPhysicalBreakingSample::Evaluate<true>(FVector2D(776,0),Sites,0.f,&Foam),0.f);
    const auto UnkarSurface=Water->ComputeFeatureVelocityAtRiverCoordinates(FVector2D(780.4,24),FVector2D(3,0),2.f,1.f);
    const auto UnkarHull=Water->ComputeFeatureVelocityAtRiverCoordinates(FVector2D(780.4,24),FVector2D(3,0),2.f,.85f);
    TestTrue(TEXT("Unkar visible transport and immersed hull share hole return"),UnkarSurface.X<2.5 && UnkarHull.X<2.5);
    const FVector2D UnkarDiagonal=FVector2D(828,12)+4.4*FVector2D(FMath::Cos(FMath::DegreesToRadians(-25.)),FMath::Sin(FMath::DegreesToRadians(-25.)));
    TestTrue(TEXT("Unkar diagonal pushes surface toward left wall"),
        Water->ComputeFeatureVelocityAtRiverCoordinates(UnkarDiagonal,FVector2D(3,0),2.f,1.f).Y>.2);
    TestTrue(TEXT("Unkar diagonal pushes immersed hull through the same kernel"),
        Water->ComputeFeatureVelocityAtRiverCoordinates(UnkarDiagonal,FVector2D(3,0),2.f,.85f).Y>.2);
    TestEqual(TEXT("Unkar froth does not bridge the quiet reach into the next drop"),
        RaftSimPhysicalBreakingSample::Evaluate<true>(FVector2D(1040,6),Sites,0.f,&Foam),0.f);
    TestEqual(TEXT("Unkar pool has no profile froth"),Foam,0.f);
    TestTrue(TEXT("Unkar authored return also stops in the pool"),
        Water->ComputeFeatureVelocityAtRiverCoordinates(FVector2D(1040,6),FVector2D(3,0),2.f,.85f).Equals(FVector(3,0,0),1.e-6));
    Sites.Reset();
    TestEqual(TEXT("Unkar quiet pools cannot activate named rollers"),Append(TEXT("L_Colorado_Unkar"),UnkarBounds,Pool,Sites),0);
    TestEqual(TEXT("Unkar dry cells cannot activate named rollers"),Append(TEXT("L_Colorado_Unkar"),UnkarBounds,Dry,Sites),0);
    return true;
}
#endif
