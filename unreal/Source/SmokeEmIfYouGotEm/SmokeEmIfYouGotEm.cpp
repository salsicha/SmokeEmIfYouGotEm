#include "SmokeEmIfYouGotEm.h"

#include "Modules/ModuleManager.h"
#if WITH_EDITOR
#include "HAL/IConsoleManager.h"
#include "Misc/CoreMisc.h"
#include "RaftSimPythonStartupPolicy.h"
#endif
#if !UE_BUILD_SHIPPING
#include "Tests/RaftSimDetailStreamingPlayProbe.h"
#include "Tests/RaftSimCheckpointPlayProbe.h"
#endif

class FSmokeEmIfYouGotEmModule final : public FDefaultGameModuleImpl
{
public:
    void StartupModule() override
    {
        FDefaultGameModuleImpl::StartupModule();
#if WITH_EDITOR
        if (RaftSimPythonStartupPolicy::DisableDefault(true, IsRunningGame(), IsRunningCommandlet()))
        {
            // PythonScriptPlugin registers this in PreDefault and consumes it
            // at OnPostEngineInit, after this Default-phase game module. Only
            // change the default: explicit Enable/ForceEnablePython and editor
            // user preferences retain the engine's own precedence. No engine
            // plugin, user setting, startup script or error logging is changed.
            if (IConsoleVariable* PythonDefault = IConsoleManager::Get().FindConsoleVariable(TEXT("Engine.Python.IsEnabledByDefault")))
            {
                PythonDefault->Set(0, ECVF_SetByProjectSetting);
                UE_LOG(LogTemp, Display, TEXT("RaftSim editor-hosted game: editor Python default disabled; explicit engine Python overrides remain available"));
            }
            else
            {
                UE_LOG(LogTemp, Warning, TEXT("RaftSim editor-hosted game: Python default control unavailable; startup policy was not applied"));
            }
        }
#endif
#if !UE_BUILD_SHIPPING
        DetailProbe=RaftSimDetailStreamingPlayProbe::Register();
        CheckpointProbe=RaftSimCheckpointPlayProbe::Register();
#endif
    }
    void ShutdownModule() override
    {
#if !UE_BUILD_SHIPPING
        if(DetailProbe.IsValid())FWorldDelegates::OnWorldPostActorTick.Remove(DetailProbe);
        if(CheckpointProbe.IsValid())FWorldDelegates::OnWorldPostActorTick.Remove(CheckpointProbe);
#endif
        FDefaultGameModuleImpl::ShutdownModule();
    }
private:
#if !UE_BUILD_SHIPPING
    FDelegateHandle DetailProbe;
    FDelegateHandle CheckpointProbe;
#endif
};

IMPLEMENT_PRIMARY_GAME_MODULE(FSmokeEmIfYouGotEmModule, SmokeEmIfYouGotEm, "SmokeEmIfYouGotEm");
