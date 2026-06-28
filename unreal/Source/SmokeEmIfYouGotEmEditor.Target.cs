using UnrealBuildTool;
using System.Collections.Generic;

public class SmokeEmIfYouGotEmEditorTarget : TargetRules
{
    public SmokeEmIfYouGotEmEditorTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Editor;
        DefaultBuildSettings = BuildSettingsVersion.V5;
        IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
        ExtraModuleNames.Add("SmokeEmIfYouGotEm");
    }
}
