#pragma once

#include "Modules/ModuleInterface.h"

class UToolMenu;
struct FRaftSimEditorToolDescriptor;

class FRaftSimEditorModule : public IModuleInterface
{
public:
    virtual void StartupModule() override;
    virtual void ShutdownModule() override;

private:
    void RegisterMenus();
    void PopulateRaftSimToolsMenu(UToolMenu* Menu);
    void LaunchTool(FName ToolId);
    const TArray<FRaftSimEditorToolDescriptor>& GetToolDescriptors();

    TArray<FRaftSimEditorToolDescriptor> ToolDescriptors;
};
