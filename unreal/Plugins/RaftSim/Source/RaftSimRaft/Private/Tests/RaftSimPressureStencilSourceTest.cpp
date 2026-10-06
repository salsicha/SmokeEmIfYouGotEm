#include "Misc/AutomationTest.h"
#include "RaftSimTotalDepthSource.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimPressureStencilSourceTest,
    "RaftSim.M4.PressureStencilSource",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimPressureStencilSourceTest::RunTest(const FString&)
{
    TArray<FVector4f> Wide,Geometry,Old,OldGeometry;
    TArray<float> Faces;Faces.Init(.25f,512);
    for(int32 Y=0;Y<69;++Y)for(int32 X=0;X<69;++X)
    {
        const float H=(Y%7==0)?1e-30f:1.f+.125f*X+.25f*Y;
        Wide.Emplace(H,(X%3)-1.f,(Y%5)*.25f,0);
        Geometry.Emplace(1000000.f+X+Y,1000000.f+X+Y,H,0);
        if(X>=1 && X<=67 && Y>=1 && Y<=67){Old.Add(Wide.Last());OldGeometry.Add(Geometry.Last());}
    }
    FString Error;int64 Compared=0;
    for(float PY:{0.f,.5f})for(float PX:{0.f,.5f})
    {
        const FVector2f Origin(-5450.f+PX,3566.f+PY);
        auto A=FRaftSimTotalDepthSource::Build(Old,OldGeometry,Faces,Origin,7.25,1,Error);
        auto B=FRaftSimTotalDepthSource::Build(Wide,Geometry,Faces,Origin,7.25,1,Error);
        if(!A || !B){AddError(Error);return false;}
        TestTrue(TEXT("all existing source fields remain exact under expanded sampling"),
            A->State==B->State && A->Bed==B->Bed && A->Reference==B->Reference &&
            A->ExteriorState==B->ExteriorState && A->ExteriorBed==B->ExteriorBed && A->FaceNormalVelocity==B->FaceNormalVelocity);
        TestTrue(TEXT("ordinary source has no diagnostic halo allocation"),A->PressureStencilState.IsEmpty() && A->PressureStencilBed.IsEmpty());
        TSet<FIntPoint> Seen;
        for(int32 I=0;I<B->PressureStencilCount;++I)
        {
            const auto P=B->PressureStencilCell(I);Seen.Add(P);
            TestTrue(TEXT("three rings exclude all interior cells"),P.X<0 || P.Y<0 || P.X>=128 || P.Y>=128);
            // Independent four coarse-corner lookup, exact half-cell weights.
            const float X=P.X*.5f+PX+2,Y=P.Y*.5f+PY+2;
            const int32 CX=FMath::FloorToInt(X),CY=FMath::FloorToInt(Y);
            FVector4f Expected=FVector4f::Zero();float ExpectedBed=0;
            for(int32 DY=0;DY<2;++DY)for(int32 DX=0;DX<2;++DX)
            {
                const float Weight=(DX?X-CX:1-(X-CX))*(DY?Y-CY:1-(Y-CY));
                const int32 J=(CY+DY)*69+CX+DX;const auto F=Wide[J];
                Expected+=Weight*FVector4f(F.X,F.X*F.Y,F.X*F.Z,0);
                ExpectedBed+=Weight*Geometry[J].X;
            }
            TestTrue(TEXT("actual outer sample matches independent interpolation"),
                B->PressureStencilState[I].Equals(Expected,1e-6f) && B->PressureStencilBed[I]==ExpectedBed);
        }
        TestEqual(TEXT("every outer cell including corners appears once"),Seen.Num(),B->PressureStencilCount);
        auto Bad=*B;Bad.PressureStencilBed.Pop();TestFalse(TEXT("partial halo rejected"),Bad.Validate(Error));
        Compared+=B->State.Num()+B->ExteriorState.Num()+B->PressureStencilState.Num();
    }
    AddInfo(FString::Printf(TEXT("Pressure stencil compared %lld source/ghost cells across all four half-cell phases; existing fields exact"),Compared));
    return !HasAnyErrors();
}
#endif
