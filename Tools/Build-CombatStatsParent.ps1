# Rebuild the existing initialization graph in the new shared parent.
# The source graph audit must be captured before running this one-time migration.
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/UnrealMcpHelpers.ps1"
$projectRoot = Split-Path $PSScriptRoot -Parent
$source = @(Get-Content (Join-Path $projectRoot 'Saved/StatsNodesAudit.json') -Raw | ConvertFrom-Json)
$graphPath = '/Game/Gameplay/Characters/BP_CombatCharacter.BP_CombatCharacter:InitializeStatsFromTable'
$graph = @{refPath=$graphPath}
$existing = @(Get-UnrealGraphNodes $graphPath)
if ($existing.Count -ne 1) { throw 'Expected a new graph containing only its entry.' }
$mapping = @{}
foreach ($node in $source) {
    $id = $node.type_id
    if ($id -eq '|InitializeStatsFromTable') { $created = $existing[0].node }
    else {
        switch ($id) {
            '|GetCharacterStatsRowName' { $id='变量|默认|获取CharacterStatsRowName' }
            '|GetAbilitySystemComponent' { $id='变量|GAS|获取AbilitySystemComponent' }
            '工具|GetDataTableRowDT_CharacterStats' { $id='工具|获得数据表行' }
        }
        $created = Invoke-UnrealTool 'create_node' @{graph=$graph;type_id=$id;pos=@{x=[int]$node.position.x;y=[int]$node.position.y}}
    }
    $mapping[$node.node.refPath] = $created
    foreach ($pin in $node.input_pins) {
        if ($pin.connected_pins.Count -or -not $pin.value -or $pin.type_id -eq '执行') { continue }
        $current = @(Invoke-UnrealTool 'get_node_infos' @{nodes=@($created)})[0]
        $destination = @($current.input_pins | Where-Object name -eq $pin.name)
        if ($destination.Count -ne 1) { throw "Missing input $($pin.name) on $id" }
        Invoke-UnrealTool 'set_pin_value' @{pin=$destination[0].pin_id;value=[string]$pin.value} | Out-Null
    }
}
foreach ($node in $source) {
    foreach ($pin in $node.output_pins) {
        foreach ($connection in $pin.connected_pins) {
            if (-not $mapping.ContainsKey($connection.node.refPath)) { throw 'External graph connection detected' }
            $oldTarget = @($source | Where-Object {$_.node.refPath -eq $connection.node.refPath})[0]
            $oldInput = @($oldTarget.input_pins | Where-Object {$_.pin_id.index_id -eq $connection.index_id})[0]
            $newSource = @(Invoke-UnrealTool 'get_node_infos' @{nodes=@($mapping[$node.node.refPath])})[0]
            $newTarget = @(Invoke-UnrealTool 'get_node_infos' @{nodes=@($mapping[$connection.node.refPath])})[0]
            $outPin = @($newSource.output_pins | Where-Object name -eq $pin.name)
            $inPin = @($newTarget.input_pins | Where-Object name -eq $oldInput.name)
            if ($outPin.Count -ne 1 -or $inPin.Count -ne 1) { throw "Could not map $($pin.name) -> $($oldInput.name)" }
            Invoke-UnrealTool 'connect_pins' @{output_pin=$outPin[0].pin_id;input_pin=$inPin[0].pin_id} | Out-Null
        }
    }
}
Invoke-UnrealTool 'compile_blueprint' @{blueprint=@{refPath='/Game/Gameplay/Characters/BP_CombatCharacter.BP_CombatCharacter'};warnings_as_errors=$true}
'Shared initialization graph compiled.'
