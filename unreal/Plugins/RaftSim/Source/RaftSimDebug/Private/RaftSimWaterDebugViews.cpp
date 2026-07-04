#include "RaftSimWaterDebugViews.h"

void URaftSimWaterDebugViewModel::Configure(URaftSimWaterDebugViewSet* InViewSet)
{
    ViewSet = InViewSet;
    EnabledViews.Reset();

    if (!ViewSet)
    {
        return;
    }

    for (const FRaftSimWaterDebugViewDefinition& Definition : ViewSet->Views)
    {
        EnabledViews.Add(Definition.View, Definition.bDefaultEnabled);
    }
}

void URaftSimWaterDebugViewModel::SetViewEnabled(ERaftSimWaterDebugView View, bool bEnabled)
{
    EnabledViews.Add(View, bEnabled);
}

bool URaftSimWaterDebugViewModel::IsViewEnabled(ERaftSimWaterDebugView View) const
{
    if (const bool* bEnabled = EnabledViews.Find(View))
    {
        return *bEnabled;
    }
    return false;
}
