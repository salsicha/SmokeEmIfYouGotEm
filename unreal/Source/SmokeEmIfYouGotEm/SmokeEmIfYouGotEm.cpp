#include "SmokeEmIfYouGotEm.h"

#include "Modules/ModuleManager.h"
#if !UE_BUILD_SHIPPING
#include "Tests/RaftSimDetailStreamingPlayProbe.h"
#endif

class FSmokeEmIfYouGotEmModule final : public FDefaultGameModuleImpl
{
public:
    void StartupModule() override
    {
        FDefaultGameModuleImpl::StartupModule();
#if !UE_BUILD_SHIPPING
        DetailProbe=RaftSimDetailStreamingPlayProbe::Register();
#endif
    }
    void ShutdownModule() override
    {
#if !UE_BUILD_SHIPPING
        if(DetailProbe.IsValid())FWorldDelegates::OnWorldPostActorTick.Remove(DetailProbe);
#endif
        FDefaultGameModuleImpl::ShutdownModule();
    }
private:
#if !UE_BUILD_SHIPPING
    FDelegateHandle DetailProbe;
#endif
};

IMPLEMENT_PRIMARY_GAME_MODULE(FSmokeEmIfYouGotEmModule, SmokeEmIfYouGotEm, "SmokeEmIfYouGotEm");
