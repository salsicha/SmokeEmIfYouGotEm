#include "Misc/AutomationTest.h"
#include "NiagaraEmitterHandle.h"
#include "NiagaraSystem.h"
#include "NiagaraSpriteRendererProperties.h"
#include "Stateless/Modules/NiagaraStatelessModule_InitializeParticle.h"
#include "Stateless/Modules/NiagaraStatelessModule_AddVelocity.h"
#include "Stateless/Modules/NiagaraStatelessModule_GravityForce.h"
#include "Stateless/NiagaraStatelessEmitter.h"
#include "Stateless/Modules/NiagaraStatelessModule_ShapeLocation.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimRapidSourceBindingTest,
    "RaftSim.M5.RapidSourceBinding", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimRapidSourceBindingTest::RunTest(const FString&)
{
    const FNiagaraVariable Rotation(FNiagaraTypeDefinition::GetQuatDef(), TEXT("User.SourcePlaneRotation"));
    for (const TCHAR* Name : {TEXT("NS_RaftSim_RapidAerosol"), TEXT("NS_RaftSim_RapidRoller"), TEXT("NS_RaftSim_RapidCrestSpray")})
    {
        const FString Path = FString::Printf(TEXT("/Game/RaftSim/VFX/Water/%s.%s"), Name, Name);
        UNiagaraSystem* System = LoadObject<UNiagaraSystem>(nullptr, *Path);
        if (!TestNotNull(Name, System)) continue;
        if (!TestFalse(TEXT("system has an emitter"), System->GetEmitterHandles().IsEmpty())) continue;
        System->WaitForCompilationComplete(false, false);
        TestTrue(TEXT("compiled system ready"), System->IsReadyToRun());
        TestTrue(TEXT("quaternion parameter exported"), System->GetExposedParameters().IndexOf(Rotation) != INDEX_NONE);
        auto* Emitter = System->GetEmitterHandles()[0].GetStatelessEmitter();
        auto* Shape = Emitter ? Cast<UNiagaraStatelessModule_ShapeLocation>(
            Emitter->GetModule(UNiagaraStatelessModule_ShapeLocation::StaticClass())) : nullptr;
        if (!TestNotNull(TEXT("source shape module"), Shape)) continue;
        TestTrue(TEXT("source rotation is bound independently"), Shape->ShapeRotation.IsBinding());
        TestTrue(TEXT("correct quaternion binding"), Shape->ShapeRotation.ParameterBinding == Rotation);
        TestTrue(TEXT("source remains emitter local with correction supplied at runtime"),
            Shape->CoordinateSpace == ENiagaraCoordinateSpace::Local);
    }
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimChilkoBallisticSprayTest,
    "RaftSim.M5.ChilkoBallisticSpray", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimChilkoBallisticSprayTest::RunTest(const FString&)
{
    for (bool bRoller : {true, false})
    {
        const FString Suffix = bRoller ? TEXT("Roller") : TEXT("CrestSpray");
        const FString Name = TEXT("NS_RaftSim_ChilkoRapid") + Suffix;
        auto* System = LoadObject<UNiagaraSystem>(nullptr,
            *FString::Printf(TEXT("/Game/RaftSim/VFX/Water/Chilko/%s.%s"), *Name, *Name));
        const FString SourceName = TEXT("NS_RaftSim_Rapid") + Suffix;
        auto* Source = LoadObject<UNiagaraSystem>(nullptr,
            *FString::Printf(TEXT("/Game/RaftSim/VFX/Water/%s.%s"), *SourceName, *SourceName));
        if (!TestNotNull(*Name, System) || !TestNotNull(TEXT("legacy source"), Source)) continue;
        if (System->GetEmitterHandles().IsEmpty() || Source->GetEmitterHandles().IsEmpty())
        { AddError(TEXT("Missing emitter")); continue; }
        System->WaitForCompilationComplete(false, false);
        TestTrue(TEXT("saved variant ready"), System->IsReadyToRun());
        auto* Emitter = System->GetEmitterHandles()[0].GetStatelessEmitter();
        auto* Original = Source->GetEmitterHandles()[0].GetStatelessEmitter();
        if (!TestNotNull(TEXT("variant emitter"), Emitter) || !TestNotNull(TEXT("source emitter"), Original)) continue;
        TestTrue(TEXT("isolated emitter copy"), Emitter != Original);
        auto* Init = Cast<UNiagaraStatelessModule_InitializeParticle>(Emitter->GetModule(UNiagaraStatelessModule_InitializeParticle::StaticClass()));
        auto* Gravity = Cast<UNiagaraStatelessModule_GravityForce>(Emitter->GetModule(UNiagaraStatelessModule_GravityForce::StaticClass()));
        auto* Velocity = Cast<UNiagaraStatelessModule_AddVelocity>(Emitter->GetModule(UNiagaraStatelessModule_AddVelocity::StaticClass()));
        auto* OldGravity = Cast<UNiagaraStatelessModule_GravityForce>(Original->GetModule(UNiagaraStatelessModule_GravityForce::StaticClass()));
        if (!Init || !Gravity || !Velocity || !OldGravity) { AddError(TEXT("Missing particle modules")); continue; }
        TestEqual(TEXT("gravity in cm/s squared"), Gravity->GravityDistribution.Min.Z, -980.665f);
        TestEqual(TEXT("source gravity preserved"), OldGravity->GravityDistribution.Min.Z, bRoller ? -260.0f : -980.0f);
        TestTrue(TEXT("shortest life outlasts even vertical ballistic return"),
            Init->LifetimeDistribution.Min > 2.0f * Velocity->ConeVelocityDistribution.Max / 980.665f);
        TestEqual(TEXT("compact maximum sprite height"), Init->SpriteSizeDistribution.Max.Y, bRoller ? 18.0f : 10.0f);
        TestEqual(TEXT("spawn schedule count retained"), Emitter->GetNumSpawnInfos(), Original->GetNumSpawnInfos());
        const FNiagaraVariable Rotation(FNiagaraTypeDefinition::GetQuatDef(), TEXT("User.SourcePlaneRotation"));
        TestTrue(TEXT("source plane correction retained"), System->GetExposedParameters().IndexOf(Rotation) != INDEX_NONE);
        int32 SpriteCount = 0;
        for (auto* Renderer : Emitter->GetRenderers())
            if (auto* Sprite = Cast<UNiagaraSpriteRendererProperties>(Renderer))
            { ++SpriteCount; TestTrue(TEXT("no velocity-aligned elongation"), Sprite->Alignment == ENiagaraSpriteAlignment::Unaligned); }
        TestTrue(TEXT("sprite renderer present"), SpriteCount > 0);
    }
    return true;
}
#endif
