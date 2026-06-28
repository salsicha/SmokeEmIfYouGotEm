#pragma once

#include "Modules/ModuleManager.h"

class FRaftSimRaftModule final : public IModuleInterface
{
public:
    virtual void StartupModule() override;
    virtual void ShutdownModule() override;
};
