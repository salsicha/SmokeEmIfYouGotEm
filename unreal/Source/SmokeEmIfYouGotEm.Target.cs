using UnrealBuildTool;
using System.Collections.Generic;

public class SmokeEmIfYouGotEmTarget : TargetRules
{
    public SmokeEmIfYouGotEmTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Game;
        DefaultBuildSettings = BuildSettingsVersion.V5;
        IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
        ExtraModuleNames.Add("SmokeEmIfYouGotEm");
    }
}
