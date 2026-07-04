#pragma once

#include "Modules/ModuleManager.h"

class FRaftSimCrewModule final : public IModuleInterface
{
public:
    virtual void StartupModule() override;
    virtual void ShutdownModule() override;
};
