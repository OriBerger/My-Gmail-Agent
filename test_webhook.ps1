# PowerShell script to test the webhook
# Test webhook functionality

$webhookUrl = "https://my-gmail-agent.onrender.com/webhook/gmail"

$body = @{
    message = @{
        data = "eyJ0ZXN0IjoidGVzdCJ9"
        messageId = "test123"
    }
} | ConvertTo-Json -Depth 3

Write-Host "Testing webhook at: $webhookUrl"
Write-Host "Sending test data..."

try {
    $response = Invoke-RestMethod -Uri $webhookUrl `
        -Method POST `
        -ContentType "application/json" `
        -Body $body
    
    Write-Host "SUCCESS: Webhook responded!" -ForegroundColor Green
    Write-Host "Response: $($response | ConvertTo-Json)" -ForegroundColor Green
}
catch {
    Write-Host "ERROR: Webhook test failed!" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}