#pragma once
#include "CoreMinimal.h"

// Remove only provably inactive ROOTS from adaptive work, never from output.
// Retain a vertex-neighbour ring so every split edge has its conforming owner.
// All coordinates remain in their original index space and all root ordering
// is restored after refinement. No sampled height survives between builds.
struct FRaftSimCrestRootWorkset
{
    TArray<int32> Triangles, RootOwners;

    bool Prepare(const TArray<FVector2D>& Points,const TArray<int32>& Roots,
        TConstArrayView<FBox2D> Regions,const FBox2D* DetailWindow,float DetailSpanCm)
    {
        Triangles.Reset();RootOwners.Reset();
        if(Roots.Num()%3)return false;
        for(int32 I:Roots)if(!Points.IsValidIndex(I))return false;
        bool Full=Regions.IsEmpty(); // No regions means unrestricted, NOT zero.
        for(const auto& R:Regions)
            Full|=!R.bIsValid || R.Min.ContainsNaN() || R.Max.ContainsNaN();
        if(DetailWindow && DetailSpanCm>0)
            Full|=!DetailWindow->bIsValid || DetailWindow->Min.ContainsNaN() || DetailWindow->Max.ContainsNaN();
        for(const auto& P:Points)Full|=P.ContainsNaN();
        TArray<uint8> ActiveNodes;ActiveNodes.Init(0,Points.Num());
        if(!Full)for(int32 T=0;T<Roots.Num();T+=3)
        {
            FBox2D B(ForceInit);for(int32 K=0;K<3;++K)B+=Points[Roots[T+K]];
            // Enlarge eligibility only, to cover descendant coordinate rounding.
            const double Magnitude=FMath::Max(B.Min.GetAbsMax(),B.Max.GetAbsMax());
            B=B.ExpandBy(1.e-9*(1.+Magnitude));
            bool Active=DetailWindow && DetailSpanCm>0 && B.Intersect(*DetailWindow);
            for(const auto& R:Regions)if(B.Intersect(R)){Active=true;break;}
            if(Active)for(int32 K=0;K<3;++K)ActiveNodes[Roots[T+K]]=1;
        }
        Triangles.Reserve(Roots.Num());RootOwners.Reserve(Roots.Num()/3);
        for(int32 T=0;T<Roots.Num();T+=3)
            if(Full || ActiveNodes[Roots[T]] || ActiveNodes[Roots[T+1]] || ActiveNodes[Roots[T+2]])
            {RootOwners.Add(T/3);for(int32 K=0;K<3;++K)Triangles.Add(Roots[T+K]);}
        return true;
    }

    bool Merge(const TArray<int32>& Roots,TArray<int32>& Refined,TArray<int32>& Origins) const
    {
        if(Refined.Num()!=Origins.Num()*3)return false;
        int32 Previous=-1;
        for(int32 O:Origins)
        {if(!RootOwners.IsValidIndex(O) || O<Previous)return false;Previous=O;}
        TArray<int32> All,AllOrigins;
        All.Reserve(Refined.Num()+Roots.Num()-Triangles.Num());
        AllOrigins.Reserve(All.Max()/3);
        int32 WorkRoot=0,Fine=0;
        for(int32 Root=0;Root<Roots.Num()/3;++Root)
        {
            if(WorkRoot<RootOwners.Num() && RootOwners[WorkRoot]==Root)
            {
                while(Fine<Origins.Num() && Origins[Fine]==WorkRoot)
                {for(int32 K=0;K<3;++K)All.Add(Refined[3*Fine+K]);AllOrigins.Add(Root);++Fine;}
                ++WorkRoot;
            }
            else
            {for(int32 K=0;K<3;++K)All.Add(Roots[3*Root+K]);AllOrigins.Add(Root);}
        }
        if(Fine!=Origins.Num() || WorkRoot!=RootOwners.Num())return false;
        Refined=MoveTemp(All);Origins=MoveTemp(AllOrigins);return true;
    }
};
