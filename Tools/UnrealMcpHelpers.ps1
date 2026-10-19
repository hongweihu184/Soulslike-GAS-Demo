function Invoke-UnrealTool {
    param([string]$Tool, [hashtable]$Arguments = @{}, [string]$Toolset = 'editor_toolset.toolsets.blueprint.BlueprintTools')
    $request = @{name='call_tool';arguments=@{toolset_name=$Toolset;tool_name=$Tool;arguments=$Arguments}} | ConvertTo-Json -Depth 40 -Compress
    $response = (& "$PSScriptRoot/Invoke-UnrealMcp.ps1" -Method 'tools/call' -ParamsJson $request) | ConvertFrom-Json
    if ($response.error) { throw ($response.error | ConvertTo-Json -Compress) }
    if ($response.result.isError) { throw ($response.result.content.text -join "`n") }
    $body = ($response.result.content | Where-Object type -eq 'text' | ForEach-Object text) -join "`n"
    if ($body) {
        $parsed = $body | ConvertFrom-Json
        return $parsed.returnValue
    }
}

function Get-UnrealGraphNodes {
    param([string]$Graph)
    $nodes = @(Invoke-UnrealTool 'find_nodes' @{graph=@{refPath=$Graph};title=''})
    if ($nodes.Count) { Invoke-UnrealTool 'get_node_infos' @{nodes=$nodes} }
}
