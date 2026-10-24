param([Parameter(Mandatory=$true)][string]$Script)
$ErrorActionPreference='Stop'
. "$PSScriptRoot/UnrealMcpHelpers.ps1"
$spacingSettings=@{refPath='/Script/PythonScriptPlugin.Default__PythonScriptPluginSettings'}
$spacingToolset='editor_toolset.toolsets.object.ObjectTools'
$spacingOriginal=(Invoke-UnrealTool 'get_properties' @{instance=$spacingSettings;properties=@('bRemoteExecution','RemoteExecutionMulticastBindAddress','RemoteExecutionMulticastTtl')} $spacingToolset)|ConvertFrom-Json
if ($spacingOriginal.RemoteExecutionMulticastBindAddress -ne '127.0.0.1' -or $spacingOriginal.RemoteExecutionMulticastTtl -ne 0) {throw 'Refusing non-loopback Python bridge'}
try {
    Invoke-UnrealTool 'set_properties' @{instance=$spacingSettings;values='{"bRemoteExecution":true}'} $spacingToolset | Out-Null
    & 'E:/UE_5.8/Engine/Binaries/ThirdParty/Python3/Win64/python.exe' "$PSScriptRoot/Invoke-UnrealPython.py" $Script
    if ($LASTEXITCODE -ne 0) {throw "Editor script failed: $Script"}
} finally {
    $spacingRestore=@{bRemoteExecution=[bool]$spacingOriginal.bRemoteExecution}|ConvertTo-Json -Compress
    Invoke-UnrealTool 'set_properties' @{instance=$spacingSettings;values=$spacingRestore} $spacingToolset | Out-Null
    Write-Output 'Original Python bridge setting restored.'
}
