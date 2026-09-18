#include "RaftSimAtlasStencil.h"
#include "RaftSimLiveWaterWindow.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "Misc/AutomationTest.h"
#include "Async/ParallelFor.h"
#include <limits>

#if WITH_AUTOMATION_TESTS && RAFTSIM_HAS_LIVE_SOLVER
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimAtlasStencilTest,"RaftSim.M3.AtlasStencil",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimAtlasStencilTest::RunTest(const FString&)
{
    // Non-square tiles, negative global cells, holes, seams and large keys.
    for(FIntPoint Shape:{FIntPoint(2,3),FIntPoint(80,64),FIntPoint(4096,4096)})
    {
        TMap<FIntPoint,int32> Tiles;
        Tiles.Add(FIntPoint(-2,-1),2);Tiles.Add(FIntPoint(-1,-1),0);
        Tiles.Add(FIntPoint(-1,0),1);Tiles.Add(FIntPoint(99999998,-99999998),3);
        int32 Calls=0;
        const auto Lookup=[&](int64 X,int64 Y)
        {
            ++Calls;
            const FIntPoint K(int32(FMath::FloorToDouble(double(X)/Shape.X)),int32(FMath::FloorToDouble(double(Y)/Shape.Y)));
            const int32* Tile=Tiles.Find(K);
            return Tile ? int32((*Tile*Shape.Y+Y-int64(K.Y)*Shape.Y)*Shape.X+X-int64(K.X)*Shape.X) : INDEX_NONE;
        };
        for(const auto& Entry:Tiles)for(int32 LY:{0,1,Shape.Y-1})for(int32 LX:{0,1,Shape.X-1})
        {
            const int64 X=int64(Entry.Key.X)*Shape.X+LX,Y=int64(Entry.Key.Y)*Shape.Y+LY;
            FRaftSimAtlasStencil Cached(X,Y,Shape.X,Shape.Y,Lookup);
            for(int32 DY=-1;DY<=1;++DY)for(int32 DX=-1;DX<=1;++DX)
                if(!TestEqual(TEXT("query-local index equals original lookup"),Cached.At(X+DX,Y+DY,Lookup),Lookup(X+DX,Y+DY)))return false;
        }
        FRaftSimAtlasStencil Missing(Shape.X*5,Shape.Y*5,Shape.X,Shape.Y,Lookup);
        TestEqual(TEXT("missing center stays missing"),Missing.At(Shape.X*5,Shape.Y*5,Lookup),INDEX_NONE);
        if(Shape.X>2)
        {
            const int64 X=-int64(Shape.X)+2,Y=-int64(Shape.Y)+2;
            Calls=0;FRaftSimAtlasStencil Interior(X,Y,Shape.X,Shape.Y,Lookup);
            for(int32 DY=-1;DY<=1;++DY)for(int32 DX=-1;DX<=1;++DX)Interior.At(X+DX,Y+DY,Lookup);
            TestEqual(TEXT("whole interior stencil uses one original lookup"),Calls,1);
        }
    }
    const FString Root=URaftSimWaterRuntimeAdapter::ResolveRuntimeDataPath(TEXT("tmp/cartesian-atlas-fixture-v1"));
    const FVector2D Origin(-5432.,3600.);
    const auto Equal=[](const FRaftSimLiveWaterSampleResult& A,const FRaftSimLiveWaterSampleResult& B)
    {return A.bValid==B.bValid && A.bWet==B.bWet && A.DepthM==B.DepthM && A.BedHeightM==B.BedHeightM &&
        A.SurfaceHeightM==B.SurfaceHeightM && A.VelocityMps==B.VelocityMps && A.SurfaceNormal==B.SurfaceNormal;};
    for(const TCHAR* Name:{TEXT("valid"),TEXT("dry_island"),TEXT("missing_northeast")})
    {
        FString Error;
        auto Window=FRaftSimLiveWaterWindow::CreateFromCookedFields(Root/Name,TEXT("analytic"),
            Origin+FVector2D(5.5,5.5),FVector2D(7.,7.),.035f,Error,false);
        if(!TestTrue(*Error,Window.IsValid()))return false;
        constexpr int32 N=109;
        TArray<uint8> Exact;Exact.SetNum(N*N);
        ParallelFor(N*N,[&](int32 I)
        {
            const FVector2D P=Origin+FVector2D((I%N)*.25-2.,(I/N)*.25-2.);
            Exact[I]=Equal(Window->SamplePresentationSource(P,false),Window->SamplePresentationSource(P,true));
        });
        for(uint8 Same:Exact)if(!TestTrue(TEXT("all full sampler fields exactly match across wet/dry/hole/seam/exterior"),Same!=0))return false;
        for(FVector2D P:{Origin+FVector2D(23.,23.),FVector2D(1.e20,-1.e20),FVector2D(std::numeric_limits<double>::quiet_NaN(),0.)})
            TestTrue(TEXT("endpoint and nonfinite/range guards unchanged"),Equal(Window->SamplePresentationSource(P,false),Window->SamplePresentationSource(P,true)));
    }
    return !HasAnyErrors();
}
#endif
