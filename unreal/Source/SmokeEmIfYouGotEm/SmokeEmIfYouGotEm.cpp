#include "SmokeEmIfYouGotEm.h"

#include "Modules/ModuleManager.h"
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
