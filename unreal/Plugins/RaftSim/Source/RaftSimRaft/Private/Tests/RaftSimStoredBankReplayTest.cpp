#include "RaftSimStoredBankContour.h"
#include "RaftSimStoredBankSearchReference.h"
#include "RaftSimWaterShoreline.h"
#include "RaftSimWaterRenderFrame.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimStoredBankReplayTest,"RaftSim.M4.StoredBankCapturedReplay",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimStoredBankReplayTest::RunTest(const FString&)
{
    using namespace RaftSimThreeWetBankContour;
    // ALL62 original shared-reserve-live-v1 rejections, not interpolated donors.
    // Original log SHA256:9b8e68b71b25ef793b4cda668593dc82d73731475e09962c893dc5ee7188d1f3.
    // Sources23259 and19466 are the same cell before/after a render-origin shift.
    const double Bed[]={8.0471343994140625,8.0450592041015625,7.95037841796875,8.0014495849609375};
    struct FCapture{int32 Frame,Source;double Depth[4];FVector2D RenderOrigin;};
    const FCapture Captures[]={
        {342,23259,{0,0.0018043745076283813,0.0071192341856658459,0.016551967710256577},{-554200,-348600}},
        {352,23259,{0,0.0018406575545668602,0.0071882200427353382,0.016593733802437782},{-554200,-348600}},
        {353,23259,{0,0.0018443003064021468,0.0071950829587876797,0.016597894951701164},{-554200,-348600}},
        {355,23259,{0,0.0018515939591452479,0.0072087906301021576,0.016606209799647331},{-554200,-348600}},
        {357,23259,{0,0.0018588985549286008,0.0072224736213684082,0.016614511609077454},{-554200,-348600}},
        {358,23259,{0,0.0018625549273565412,0.0072293062694370747,0.016618659719824791},{-554200,-348600}},
        {359,23259,{0,0.001866214326582849,0.0072361328639090061,0.01662280410528183},{-554200,-348600}},
        {360,23259,{0,0.0018698765197768807,0.0072429538704454899,0.01662694476544857},{-554200,-348600}},
        {362,23259,{0,0.001877209753729403,0.0072565781883895397,0.016635218635201454},{-554200,-348600}},
        {363,23259,{0,0.0018808809109032154,0.0072633819654583931,0.016639351844787598},{-554200,-348600}},
        {364,23259,{0,0.0018845552112907171,0.0072701801545917988,0.016643483191728592},{-554200,-348600}},
        {365,23259,{0,0.0018882325384765863,0.0072769727557897568,0.016647610813379288},{-554200,-348600}},
        {366,23259,{0,0.0018919131252914667,0.0072837602347135544,0.016651734709739685},{-554200,-348600}},
        {367,23259,{0,0.0018955968553200364,0.007290541660040617,0.016655856743454933},{-554200,-348600}},
        {367,19466,{0,0.0018992838449776173,0.0072973184287548065,0.016659976914525032},{-557400,-350300}},
        {368,19466,{0,0.0018992838449776173,0.0072973184287548065,0.016659976914525032},{-557400,-350300}},
        {369,19466,{0,0.0019029743270948529,0.0073040896095335484,0.016664093360304832},{-557400,-350300}},
        {370,19466,{0,0.0019066680688410997,0.0073108552023768425,0.016668206080794334},{-557400,-350300}},
        {371,19466,{0,0.0019103653030470014,0.0073176161386072636,0.016672316938638687},{-557400,-350300}},
        {372,19466,{0,0.001914065913297236,0.0073243719525635242,0.016676424071192741},{-557400,-350300}},
        {373,19466,{0,0.0019177701324224472,0.0073311226442456245,0.016680529341101646},{-557400,-350300}},
        {374,19466,{0,0.0019214779604226351,0.0073378682136535645,0.016684630885720253},{-557400,-350300}},
        {375,19466,{0,0.0019251892808824778,0.0073446091264486313,0.01668873056769371},{-557400,-350300}},
        {376,19466,{0,0.0019289043266326189,0.0073513449169695377,0.016692826524376869},{-557400,-350300}},
        {377,19466,{0,0.0019326230976730585,0.0073580760508775711,0.01669691875576973},{-557400,-350300}},
        {378,19466,{0,0.0019363454775884748,0.0073648025281727314,0.016701009124517441},{-557400,-350300}},
        {379,19466,{0,0.0019400715827941895,0.0073715243488550186,0.016705095767974854},{-557400,-350300}},
        {380,19466,{0,0.0019438014132902026,0.0073782415129244328,0.016709178686141968},{-557400,-350300}},
        {381,19466,{0,0.0019475350854918361,0.007384955883026123,0.016713250428438187},{-557400,-350300}},
        {382,19466,{0,0.0019512723665684462,0.0073916693218052387,0.016717299818992615},{-557400,-350300}},
        {383,19466,{0,0.0019550134893506765,0.0073983813636004925,0.016721324995160103},{-557400,-350300}},
        {384,19466,{0,0.0019587583374232054,0.007405091542750597,0.016725329682230949},{-557400,-350300}},
        {385,19466,{0,0.0019625071436166763,0.0074118007905781269,0.016729308292269707},{-557400,-350300}},
        {386,19466,{0,0.0019662594422698021,0.0074185105040669441,0.01673324778676033},{-557400,-350300}},
        {387,19466,{0,0.00197001569904387,0.0074252202175557613,0.01673714816570282},{-557400,-350300}},
        {388,19466,{0,0.0019737754482775927,0.0074319285340607166,0.016741013154387474},{-557400,-350300}},
        {389,19466,{0,0.0019775389228016138,0.0074386345222592354,0.016744846478104591},{-557400,-350300}},
        {390,19466,{0,0.0019813061226159334,0.007445337250828743,0.016748646274209023},{-557400,-350300}},
        {391,19466,{0,0.0019850768148899078,0.0074520357884466648,0.016752416267991066},{-557400,-350300}},
        {392,19466,{0,0.0019888509996235371,0.0074587292037904263,0.01675616018474102},{-557400,-350300}},
        {393,19466,{0,0.0019926286768168211,0.00746541703119874,0.016759874299168587},{-557400,-350300}},
        {394,19466,{0,0.0019964100793004036,0.0074720983393490314,0.016763564199209213},{-557400,-350300}},
        {395,19466,{0,0.0020001945085823536,0.0074787731282413006,0.0167672298848629},{-557400,-350300}},
        {396,19466,{0,0.0020039826631546021,0.0074854400008916855,0.016770871356129646},{-557400,-350300}},
        {397,19466,{0,0.002007773844525218,0.0074920989573001862,0.016774490475654602},{-557400,-350300}},
        {398,19466,{0,0.0020115682855248451,0.0074987495318055153,0.016778089106082916},{-557400,-350300}},
        {399,19466,{0,0.0020153657533228397,0.0075053912587463856,0.01678166538476944},{-557400,-350300}},
        {400,19466,{0,0.0020191662479192019,0.0075120232068002224,0.016785221174359322},{-557400,-350300}},
        {401,19466,{0,0.0020229697693139315,0.0075186458416283131,0.016788758337497711},{-557400,-350300}},
        {402,19466,{0,0.0020267760846763849,0.007525258231908083,0.016792276874184608},{-557400,-350300}},
        {403,19466,{0,0.0020305851940065622,0.0075318599119782448,0.016795776784420013},{-557400,-350300}},
        {404,19466,{0,0.0020343970973044634,0.0075384504161775112,0.016799259930849075},{-557400,-350300}},
        {405,19466,{0,0.0020382115617394447,0.0075450302101671696,0.016802724450826645},{-557400,-350300}},
        {406,19466,{0,0.0020420283544808626,0.0075515978969633579,0.016806174069643021},{-557400,-350300}},
        {407,19466,{0,0.002045847475528717,0.0075581534765660763,0.016809606924653053},{-557400,-350300}},
        {408,19466,{0,0.002049668924883008,0.0075646974146366119,0.016813024878501892},{-557400,-350300}},
        {409,19466,{0,0.0020534927025437355,0.007571228314191103,0.016816427931189537},{-557400,-350300}},
        {410,19466,{0,0.0020573183428496122,0.0075777461752295494,0.016819817945361137},{-557400,-350300}},
        {411,19466,{0,0.0020611460786312819,0.0075842509977519512,0.016823193058371544},{-557400,-350300}},
        {412,19466,{0,0.002064975444227457,0.0075907418504357338,0.016826556995511055},{-557400,-350300}},
        {413,19466,{0,0.0020688066724687815,0.0075972196646034718,0.016829906031489372},{-557400,-350300}},
        {414,19466,{0,0.0020726395305246115,0.0076036825776100159,0.016833245754241943},{-557400,-350300}},
    };
    TestEqual(TEXT("complete original capture set"),int32(UE_ARRAY_COUNT(Captures)),62);
    RaftSimWaterShoreline::FTopologyCache Cache;
    TArray<FProcMeshVertex> Mesh;TArray<uint32> Indices;TArray<int32> Offsets;
    int32 Certified=0;
    for(const FCapture& Capture:Captures)
    {
        FCurve C;RaftSimStoredBankContour::FStorage Storage;FResult Proof,Full;
        if(!C.Init(Bed,Capture.Depth) || !Storage.Init(C,{-545800.,-358900.},
            {-545700.,-358900.},{-545800.,-359000.},.1,Capture.RenderOrigin))
        {AddError(TEXT("Original captured donor/storage initialization failed"));continue;}
        // Evaluate independently: an unexecuted full search must not look
        // like a successful stage0 result after the bounded builder fails.
        const bool BoundedGood=RaftSimStoredBankContour::Build(C,Storage,Proof);
        const bool FullGood=BuildStored(C,Storage.Width,Full,Storage,Storage.RootWidth,true,false);
        if(!TestTrue(TEXT("captured neighbor reuse preserves exact geometry and proof counters"),
            RaftSimStoredBankSearchReference::Equivalent(C,Storage,Proof,Full)))continue;
        if(!BoundedGood || !FullGood)
        {
            AddError(FString::Printf(TEXT("CapturedBank frame=%d source=%d short_stage=%d full_stage=%d A=(%.17g,%.17g) B=(%.17g,%.17g)"),
                Capture.Frame,Capture.Source,Proof.Stats.FailedStage,Full.Stats.FailedStage,
                Proof.Stats.FailedA.X,Proof.Stats.FailedA.Y,Proof.Stats.FailedB.X,Proof.Stats.FailedB.Y));
            if(Proof.Stats.FailedStage==1 || Proof.Stats.FailedStage==4)
            {
                const auto StoredPoint=[&](const FVector2D& XY){return Storage.Local(Storage.BufferPosition(FPoint(XY)));};
                const FPoint P=StoredPoint(Proof.Stats.FailedA),Q=StoredPoint(Proof.Stats.FailedB);
                const FPoint A=Storage.InnerPoint(P,Storage.Width),B=Storage.InnerPoint(Q,Storage.Width);
                const FPoint O(FVector2D::ZeroVector,true);FStats Diagnostic;
                AddInfo(FString::Printf(TEXT("CapturedBank predicates frame=%d bounded=%d full=%d wet=%d dry=%d order=%.17g bandA=%.17g bandB=%.17g fan=%.17g capX=%d capY=%d"),
                    Capture.Frame,int32(BoundedGood),int32(FullGood),
                    int32(Certificate(C,P,Q,Q,true,Diagnostic)),int32(Certificate(C,O,A,B,false,Diagnostic)),
                    Cross(O,P,Q).Lo,Cross(P,Q,B).Lo,Cross(P,B,A).Lo,Cross(O,A,B).Lo,
                    int32(Storage.Endcaps[0].Active),int32(Storage.Endcaps[1].Active)));
            }
            continue;
        }
        TArray<FProcMeshVertex> Source;
        TArray<float> Depth,Beds;TArray<uint8> Wet,Available;
        for(int32 I=0;I<4;++I)
        {
            FProcMeshVertex V;V.Position=FVector(-545800.+100.*(I%2),-358900.-100.*(I/2),100.*(Bed[I]+Capture.Depth[I]));
            V.Normal=FVector::UpVector;V.UV0=FVector2D(I%2,I/2);
            Source.Add(V);Depth.Add(float(Capture.Depth[I]));Beds.Add(float(Bed[I]));Wet.Add(I!=0);Available.Add(1);
        }
        bool Good=true;
        for(int32 Pass=0;Pass<2 && Good;++Pass)
        {
            auto Input=Source;bool Rebuilt=false;
            Good=Cache.Update(2,2,MoveTemp(Input),Wet,Available,Depth,Beds,Mesh,Indices,Offsets,
                Rebuilt,true,true,true,true,&Capture.RenderOrigin);
            if(!Good || (Pass==1 && Rebuilt) || Indices.Num()!=3*Proof.Triangles.Num()){Good=false;break;}
            TArray<int32> ToProof;ToProof.Init(INDEX_NONE,Mesh.Num());
            const FRaftSimWaterRenderFrame Frame{FVector(Capture.RenderOrigin.X,Capture.RenderOrigin.Y,0.)};
            for(uint32 I:Indices)
            {
                const FVector3f Stored=Frame.Store(Mesh[I].Position);const FVector2D Buffer(double(Stored.X),double(Stored.Y));
                for(int32 J=0;J<Proof.Polygon.Num();++J)if(Buffer==Storage.BufferPosition(Proof.Polygon[J])){ToProof[I]=J;break;}
                if(ToProof[I]==INDEX_NONE){Good=false;break;}
            }
            for(int32 I=0;I<Proof.Triangles.Num() && Good;++I)
            {
                const FIntVector Actual(ToProof[Indices[3*I]],ToProof[Indices[3*I+1]],ToProof[Indices[3*I+2]]);
                const auto& E=Proof.Triangles[I];Good=Actual==E || Actual==FIntVector(E.X,E.Z,E.Y);
                // Matching ear membership alone permits reversed GPU faces.
                // Use submitted binary32 XY, promoted before subtraction, and
                // require the renderer's clockwise winding without tolerance.
                const FVector3f StoredA=Frame.Store(Mesh[Indices[3*I]].Position);
                const FVector3f StoredB=Frame.Store(Mesh[Indices[3*I+1]].Position);
                const FVector3f StoredC=Frame.Store(Mesh[Indices[3*I+2]].Position);
                const double Winding=(double(StoredB.X)-double(StoredA.X))*(double(StoredC.Y)-double(StoredA.Y))-
                    (double(StoredB.Y)-double(StoredA.Y))*(double(StoredC.X)-double(StoredA.X));
                Good=Good && Winding<0.;
            }
        }
        if(!Good){AddError(FString::Printf(TEXT("CapturedBank frame=%d source=%d actual cache/buffer/ear mismatch"),Capture.Frame,Capture.Source));continue;}
        ++Certified;
    }
    AddInfo(FString::Printf(TEXT("StoredBank original_shared_reserve_rejections=62 fully_certified=%d; captured fixture/cache coverage only"),Certified));
    TestEqual(TEXT("all62 original rejected updates certify and publish exact geometry"),Certified,62);
    return !HasAnyErrors();
}
#endif
