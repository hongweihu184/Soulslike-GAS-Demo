param(
    [string]$Method = 'tools/list',
    [string]$ParamsJson = '{}'
)
$ErrorActionPreference = 'Stop'
$endpoint = 'http://127.0.0.1:8000/mcp'
$headers = @{ Accept = 'application/json, text/event-stream' }
$init = @{ jsonrpc='2.0'; id=1; method='initialize'; params=@{
    protocolVersion='2025-11-25'; capabilities=@{};
    clientInfo=@{name='ProjectUnreal'; version='1.0'}
}} | ConvertTo-Json -Depth 10 -Compress
$response = Invoke-WebRequest -Uri $endpoint -Method Post -ContentType 'application/json' -Headers $headers -Body $init -TimeoutSec 30
$session = $response.Headers['Mcp-Session-Id']
if ($session) { $headers['Mcp-Session-Id'] = [string]($session | Select-Object -First 1) }
$headers['MCP-Protocol-Version'] = '2025-11-25'
$notification = @{jsonrpc='2.0';method='notifications/initialized'} | ConvertTo-Json -Compress
$null = Invoke-WebRequest -Uri $endpoint -Method Post -ContentType 'application/json' -Headers $headers -Body $notification -TimeoutSec 30
$request = @{jsonrpc='2.0';id=2;method=$Method;params=($ParamsJson | ConvertFrom-Json)} | ConvertTo-Json -Depth 30 -Compress
$result = Invoke-WebRequest -Uri $endpoint -Method Post -ContentType 'application/json' -Headers $headers -Body ([Text.Encoding]::UTF8.GetBytes($request)) -TimeoutSec 60
$result.Content
