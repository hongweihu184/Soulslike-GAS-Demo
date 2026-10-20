. "$PSScriptRoot/UnrealMcpHelpers.ps1"

function Get-BlueprintNodeInfo {
    param($Node)
    return @(Invoke-UnrealTool 'get_node_infos' @{nodes=@($Node)})[0]
}

function Get-BlueprintPin {
    param($Node, [string]$Name, [ValidateSet('input','output')][string]$Direction)
    $info = Get-BlueprintNodeInfo $Node
    $pins = if ($Direction -eq 'input') { $info.input_pins } else { $info.output_pins }
    $matches = @($pins | Where-Object name -eq $Name)
    if ($matches.Count -ne 1) { throw "Expected one $Direction pin '$Name' on $($Node.refPath)." }
    return $matches[0].pin_id
}

function Connect-BlueprintPins {
    param($From, [string]$OutputPinName, $To, [string]$InputPinName)
    Invoke-UnrealTool 'connect_pins' @{
        output_pin=(Get-BlueprintPin $From $OutputPinName 'output')
        input_pin=(Get-BlueprintPin $To $InputPinName 'input')
    } | Out-Null
}

function Set-BlueprintPin {
    param($Node, [string]$Name, [string]$Value)
    Invoke-UnrealTool 'set_pin_value' @{pin=(Get-BlueprintPin $Node $Name 'input');value=$Value} | Out-Null
}
