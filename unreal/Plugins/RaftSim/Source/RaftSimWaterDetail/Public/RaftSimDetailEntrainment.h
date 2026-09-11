#pragma once
#include "CoreMinimal.h"

// Empirical entrainment potential, not measured bubble production. Fast flow
// alone is not whitewater: require deceleration/convergence near a transition.
// Compute from the complete immutable depth/velocity input; output only W.
struct FRaftSimDetailEntrainment
{
    static void Build(FIntPoint Size,float CellMeters,TArray<FVector4f>& Flow)
    {
        check(Size.X>=2 && Size.Y>=2 && CellMeters>0 && Flow.Num()==Size.X*Size.Y);
        const auto Speed=[](const FVector4f& F) { return FMath::Sqrt(F.Y*F.Y+F.Z*F.Z); };
        const auto Froude=[&](const FVector4f& F) { return F.X>0.01f ? Speed(F)/FMath::Sqrt(9.81f*F.X) : 0.0f; };
        for (int32 Y=0;Y<Size.Y;++Y)for (int32 X=0;X<Size.X;++X)
        {
            FVector4f& C=Flow[Y*Size.X+X];
            if (C.X<=0.01f) { C.W=0;continue; }
            // A dry neighbour must not become an artificial zero-velocity
            // sample. Use one-sided wet derivatives or zero with no support.
            const auto Neighbor=[&](int32 NX,int32 NY)->const FVector4f*
            {
                if (NX<0 || NY<0 || NX>=Size.X || NY>=Size.Y)return nullptr;
                const auto& F=Flow[NY*Size.X+NX];return F.X>0.01f ? &F : nullptr;
            };
            const auto* L=Neighbor(X-1,Y);const auto* R=Neighbor(X+1,Y);
            const auto* B=Neighbor(X,Y-1);const auto* T=Neighbor(X,Y+1);
            const auto Derivative=[&](const FVector4f* Low,const FVector4f* High,int32 Component)
            {
                if (!Low && !High)return 0.0f;
                const auto Value=[&](const FVector4f& F) { return Component<0 ? Speed(F) : F[Component]; };
                return (Value(High ? *High : C)-Value(Low ? *Low : C))/(CellMeters*(Low && High ? 2 : 1));
            };
            const float SpeedMps=Speed(C);
            const float Compression=FMath::Max(0.0f,-Derivative(L,R,1)-Derivative(B,T,2));
            const float Deceleration=SpeedMps>0.1f ? FMath::Max(0.0f,
                -(C.Y*Derivative(L,R,-1)+C.Z*Derivative(B,T,-1))/SpeedMps) : 0.0f;
            float LocalFroude=Froude(C);
            for (const FVector4f* F:{L,R,B,T})if (F)LocalFroude=FMath::Max(LocalFroude,Froude(*F));
            // Rates in 1/s; intentionally stated heuristic thresholds. Density
            // is then transported/decayed by the GPU, not repainted each frame.
            C.W=FMath::SmoothStep(0.65f,1.1f,LocalFroude)*
                FMath::SmoothStep(0.05f,0.65f,FMath::Max(Compression,Deceleration));
        }
    }
};
