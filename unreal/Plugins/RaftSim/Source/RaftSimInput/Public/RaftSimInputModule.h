#pragma once

#include "Modules/ModuleManager.h"

class FRaftSimInputModule final : public IModuleInterface
{
public:
    virtual void StartupModule() override;
    virtual void ShutdownModule() override;
};
