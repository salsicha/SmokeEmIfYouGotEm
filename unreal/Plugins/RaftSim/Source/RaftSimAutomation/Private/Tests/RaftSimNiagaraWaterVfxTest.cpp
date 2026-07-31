#include "Engine/Texture2D.h"
#include "Materials/Material.h"
#include "Misc/AutomationTest.h"
#include "NiagaraEmitterHandle.h"
#include "NiagaraSystem.h"
#include "TextureCompiler.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimM5ProductionNiagaraWaterVfxTest,
    "RaftSim.M5.ProductionNiagaraWaterVfx",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimM5ProductionNiagaraWaterVfxTest::RunTest(const FString&)
{
    UMaterial* ParticleMaterial = LoadObject<UMaterial>(
        nullptr,
        TEXT("/Game/RaftSim/Materials/M_RaftSim_NiagaraWaterParticle."
             "M_RaftSim_NiagaraWaterParticle"));
    TestNotNull(
        TEXT("project-owned spray material loads for Niagara"), ParticleMaterial);
    if (ParticleMaterial)
    {
        TestTrue(
            TEXT("project-owned spray material has Niagara sprite usage"),
            ParticleMaterial->GetUsageByFlag(MATUSAGE_NiagaraSprites));
    }
    UTexture2D* ParticleAtlas = LoadObject<UTexture2D>(
        nullptr,
        TEXT("/Game/RaftSim/VFX/Water/Textures/"
             "T_RaftSim_WaterParticle_SubUV."
             "T_RaftSim_WaterParticle_SubUV"));
    TestNotNull(
        TEXT("project-owned water-particle SubUV atlas loads"), ParticleAtlas);
    if (ParticleAtlas)
    {
#if WITH_EDITOR
        TArray<UTexture*> Textures{ParticleAtlas};
        FTextureCompilingManager::Get().FinishCompilation(Textures);
        ParticleAtlas->BlockOnAnyAsyncBuild();
#endif
        TestEqual(
            TEXT("particle atlas imported-source width"),
            ParticleAtlas->GetSizeX(),
            2048);
        TestEqual(
            TEXT("particle atlas imported-source height"),
            ParticleAtlas->GetSizeY(),
            2048);
    }

    static const TCHAR* SystemNames[] = {
        TEXT("NS_RaftSim_SolverSpray"),
        TEXT("NS_RaftSim_ContactDroplets"),
        TEXT("NS_RaftSim_AeratedMist"),
        TEXT("NS_RaftSim_RapidAerosol"),
        TEXT("NS_RaftSim_RapidRoller"),
    };
    const FNiagaraVariable SpawnRateVariable(
        FNiagaraTypeDefinition::GetFloatDef(), TEXT("User.SpawnRate"));
    for (const TCHAR* SystemName : SystemNames)
    {
        const FString ObjectPath = FString::Printf(
            TEXT("/Game/RaftSim/VFX/Water/%s.%s"), SystemName, SystemName);
        UNiagaraSystem* System = LoadObject<UNiagaraSystem>(nullptr, *ObjectPath);
        TestNotNull(
            FString::Printf(TEXT("project-owned Niagara system loads: %s"), SystemName),
            System);
        if (!System)
        {
            continue;
        }
#if WITH_EDITOR
        System->WaitForCompilationComplete(false, false);
#endif
        TestTrue(
            FString::Printf(TEXT("Niagara system is ready: %s"), SystemName),
            System->IsReadyToRun());
        TestEqual(
            FString::Printf(TEXT("Niagara system has one bounded emitter: %s"), SystemName),
            System->GetEmitterHandles().Num(),
            1);
        if (!System->GetEmitterHandles().IsEmpty())
        {
            TestEqual(
                FString::Printf(TEXT("Niagara emitter is stateless: %s"), SystemName),
                static_cast<int32>(System->GetEmitterHandles()[0].GetEmitterMode()),
                static_cast<int32>(ENiagaraEmitterMode::Stateless));
        }
        TestTrue(
            FString::Printf(TEXT("Niagara spawn rate is solver-bindable: %s"), SystemName),
            System->GetExposedParameters().IndexOf(SpawnRateVariable) != INDEX_NONE);
    }
    return true;
}

#endif
