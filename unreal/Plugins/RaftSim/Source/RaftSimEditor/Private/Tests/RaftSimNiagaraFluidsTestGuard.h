#pragma once

#include "CoreMinimal.h"
#include "Interfaces/IPluginManager.h"
#include "Misc/AutomationTest.h"

// Editor-only FLIP fixtures run against NiagaraFluids, which is mounted only by
// the process-local -EnablePlugins=NiagaraFluids flag and never in the project
// descriptor. Skip, rather than fail on missing scripts, when it is absent.
inline bool RaftSimSkipWithoutNiagaraFluids(FAutomationTestBase& Test)
{
    if (IPluginManager::Get().FindEnabledPlugin(TEXT("NiagaraFluids"))) return false;
    Test.AddInfo(TEXT("Skipped NiagaraFluids fixture: pass -EnablePlugins=NiagaraFluids to run it."));
    return true;
}
