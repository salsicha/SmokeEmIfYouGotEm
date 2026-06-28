#pragma once

#include "Modules/ModuleManager.h"

class FRaftSimPhysicsModule final : public IModuleInterface
{
public:
    virtual void StartupModule() override;
    virtual void ShutdownModule() override;
};
