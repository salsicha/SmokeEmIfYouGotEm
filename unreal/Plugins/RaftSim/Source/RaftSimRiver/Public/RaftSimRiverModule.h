#pragma once

#include "Modules/ModuleManager.h"

class FRaftSimRiverModule final : public IModuleInterface
{
public:
    virtual void StartupModule() override;
    virtual void ShutdownModule() override;
};
