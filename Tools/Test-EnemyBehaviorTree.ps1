param([int]$TimeoutSeconds=60)
$ErrorActionPreference='Stop'
. "$PSScriptRoot/UnrealMcpHelpers.ps1"
$btv2Performance=@{refPath='/Script/UnrealEd.Default__EditorPerformanceSettings'}
$btv2Toolset='editor_toolset.toolsets.object.ObjectTools'
$btv2Original=(Invoke-UnrealTool 'get_properties' @{instance=$btv2Performance;properties=@('bThrottleCPUWhenNotForeground')} $btv2Toolset)|ConvertFrom-Json
$btv2Report='E:/UE5.8Project/ProjectUnreal/Saved/BTv2-RuntimeVerification.json'
$btv2Started=$false
try {
 Invoke-UnrealTool 'set_properties' @{instance=$btv2Performance;values='{"bThrottleCPUWhenNotForeground":false}'} $btv2Toolset|Out-Null
 Invoke-UnrealTool 'StartPIE' @{options=@{bSimulate=$false;playMode='PlayMode_InViewPort';warmupSeconds=0}} 'EditorToolset.EditorAppToolset'|Out-Null
 $btv2Started=$true
 $btv2Begin=Get-Date
 & "$PSScriptRoot/Invoke-ScopedUnrealPython.ps1" -Script 'Saved/bt_v2_runtime.py'
 $btv2Deadline=(Get-Date).AddSeconds($TimeoutSeconds)
 $btv2Fresh=$false
 while((Get-Date) -lt $btv2Deadline) {
  if((Test-Path -LiteralPath $btv2Report) -and (Get-Item -LiteralPath $btv2Report).LastWriteTime -ge $btv2Begin){$btv2Fresh=$true;break}
  Start-Sleep -Milliseconds 300
 }
 if(-not $btv2Fresh){throw 'Runtime verification timed out without a fresh report'}
 $btv2Result=Get-Content -LiteralPath $btv2Report -Raw|ConvertFrom-Json
 $btv2Result|Select-Object passed,reason,exception|ConvertTo-Json
 $btv2Result.tests|ConvertTo-Json -Depth 5
} finally {
 if($btv2Started){try{Invoke-UnrealTool 'StopPIE' @{} 'EditorToolset.EditorAppToolset'|Out-Null}catch{Write-Warning $_}}
 $btv2Restore=@{bThrottleCPUWhenNotForeground=[bool]$btv2Original.bThrottleCPUWhenNotForeground}|ConvertTo-Json -Compress
 Invoke-UnrealTool 'set_properties' @{instance=$btv2Performance;values=$btv2Restore} $btv2Toolset|Out-Null
 Write-Output 'PIE stopped and original CPU throttling restored.'
}
