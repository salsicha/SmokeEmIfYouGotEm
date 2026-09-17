$ErrorActionPreference = 'Stop'
$source = Join-Path $PSScriptRoot 'run_south_fork_joint_preview.ps1'
$tokens=$null; $errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile($source,[ref]$tokens,[ref]$errors)
if ($errors.Count) { throw 'Preview launcher parse failure' }
$function=@($ast.FindAll({param($node)
    $node -is [Management.Automation.Language.FunctionDefinitionAst] -and
    $node.Name -eq 'Test-RaftSimJointPreviewDescriptor'
},$true))
if ($function.Count -ne 1) { throw 'Expected one production descriptor validator' }
. ([scriptblock]::Create($function[0].Extent.Text))
foreach ($version in @('v1','v2')) {
    $descriptor=('{"schema":"raftsim.south_fork_joint_preview.'+$version+'","candidate":true,"production_promoted":false}') | ConvertFrom-Json
    if (-not (Test-RaftSimJointPreviewDescriptor $descriptor)) { throw "Rejected supported $version descriptor" }
}
foreach ($json in @(
    'null', '{}',
    '{"schema":"raftsim.south_fork_joint_preview.v3","candidate":true,"production_promoted":false}',
    '{"schema":"RAFTSIM.SOUTH_FORK_JOINT_PREVIEW.V2","candidate":true,"production_promoted":false}',
    '{"schema":["raftsim.south_fork_joint_preview.v2"],"candidate":true,"production_promoted":false}',
    '{"schema":"raftsim.south_fork_joint_preview.v2","candidate":false,"production_promoted":false}',
    '{"schema":"raftsim.south_fork_joint_preview.v2","candidate":true,"production_promoted":true}',
    '{"schema":"raftsim.south_fork_joint_preview.v2","candidate":"true","production_promoted":false}',
    '{"schema":"raftsim.south_fork_joint_preview.v2","candidate":true,"production_promoted":"false"}',
    '{"schema":"raftsim.south_fork_joint_preview.v2","candidate":1,"production_promoted":0}',
    '{"schema":"raftsim.south_fork_joint_preview.v2","candidate":true}'
)) {
    if (Test-RaftSimJointPreviewDescriptor ($json | ConvertFrom-Json)) { throw "Accepted invalid descriptor: $json" }
}
'PASS: joint-preview launcher admits both native schemas and rejects missing, promoted and coerced flags'
