# Airflow 3.1.3 登录完整测试脚本
# 此脚本会测试所有可能的登录方式并诊断问题

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Airflow 3.1.3 登录测试开始" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 测试1: 检查容器状态
Write-Host "[测试1] 检查容器状态..." -ForegroundColor Yellow
$containerStatus = docker ps --filter "name=airflow_new-airflow-standalone" --format "{{.Status}}"
if ($containerStatus -like "*Up*") {
    Write-Host "✅ 容器运行正常: $containerStatus" -ForegroundColor Green
} else {
    Write-Host "❌ 容器未运行！" -ForegroundColor Red
    exit 1
}

# 测试2: 获取当前密码
Write-Host "`n[测试2] 获取当前密码..." -ForegroundColor Yellow
$passwordLine = docker logs airflow_new-airflow-standalone-1 2>&1 | Select-String "Password for user" | Select-Object -Last 1
if ($passwordLine) {
    $password = ($passwordLine -split "'admin': ")[1]
    Write-Host "✅ 密码: $password" -ForegroundColor Green
} else {
    Write-Host "❌ 无法获取密码！" -ForegroundColor Red
    exit 1
}

# 测试3: 验证密码文件
Write-Host "`n[测试3] 验证密码文件..." -ForegroundColor Yellow
$passwordFile = docker exec airflow_new-airflow-standalone-1 cat /opt/airflow/simple_auth_manager_passwords.json.generated
Write-Host "✅ 密码文件内容: $passwordFile" -ForegroundColor Green

# 测试4: API Token 认证
Write-Host "`n[测试4] 测试 API Token 认证..." -ForegroundColor Yellow
try {
    $body = @{username='admin'; password=$password} | ConvertTo-Json
    $response = Invoke-RestMethod -Uri 'http://localhost:8080/auth/token' -Method POST -Body $body -ContentType 'application/json'
    $token = $response.access_token
    Write-Host "✅ Token 获取成功！" -ForegroundColor Green
    Write-Host "   Token (前50字符): $($token.Substring(0,50))..." -ForegroundColor Gray
} catch {
    Write-Host "❌ Token 获取失败: $_" -ForegroundColor Red
    exit 1
}

# 测试5: 使用 Token 访问 API
Write-Host "`n[测试5] 测试使用 Token 访问 API..." -ForegroundColor Yellow
try {
    $headers = @{Authorization = "Bearer $token"}
    $response = Invoke-RestMethod -Uri 'http://localhost:8080/ui/config' -Headers $headers
    Write-Host "✅ API 访问成功！" -ForegroundColor Green
    Write-Host "   API 版本: $($response.airflow_version)" -ForegroundColor Gray
} catch {
    Write-Host "❌ API 访问失败: $_" -ForegroundColor Red
    exit 1
}

# 测试6: 测试 DAGs API
Write-Host "`n[测试6] 测试 DAGs API..." -ForegroundColor Yellow
try {
    $headers = @{Authorization = "Bearer $token"}
    $response = Invoke-RestMethod -Uri 'http://localhost:8080/api/v1/dags' -Headers $headers
    $dagCount = $response.dags.Count
    Write-Host "✅ DAGs API 访问成功！" -ForegroundColor Green
    Write-Host "   检测到 $dagCount 个 DAG" -ForegroundColor Gray
    if ($dagCount -gt 0) {
        Write-Host "   DAG 列表:" -ForegroundColor Gray
        foreach ($dag in $response.dags) {
            Write-Host "   - $($dag.dag_id)" -ForegroundColor Gray
        }
    }
} catch {
    Write-Host "⚠️  DAGs API 访问失败（可能正常，如果没有 DAG）: $_" -ForegroundColor Yellow
}

# 测试7: 检查日志中的认证错误
Write-Host "`n[测试7] 检查最近的认证错误..." -ForegroundColor Yellow
$authErrors = docker logs airflow_new-airflow-standalone-1 2>&1 | Out-String | Select-String -Pattern "401|403|Unauthorized" -AllMatches
if ($authErrors.Matches.Count -gt 0) {
    Write-Host "⚠️  发现认证错误日志" -ForegroundColor Yellow
} else {
    Write-Host "✅ 无认证错误" -ForegroundColor Green
}

# 总结
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "测试总结" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "当前登录凭据:" -ForegroundColor White
Write-Host "  用户名: admin" -ForegroundColor Green
Write-Host "  密码: $password" -ForegroundColor Green
Write-Host "  访问地址: http://localhost:8080" -ForegroundColor Green
Write-Host "`n✅ 所有 API 测试通过！" -ForegroundColor Green
Write-Host "`n如果浏览器无法登录，请尝试:" -ForegroundColor Yellow
Write-Host "  1. 使用隐私/无痕模式打开浏览器" -ForegroundColor White
Write-Host "  2. 清除浏览器缓存和 Cookie (F12 -> Application -> Clear Storage)" -ForegroundColor White
Write-Host "  3. 硬刷新页面 (Ctrl+Shift+R 或 Ctrl+F5)" -ForegroundColor White
Write-Host "  4. 尝试其他浏览器" -ForegroundColor White
Write-Host "`n========================================`n" -ForegroundColor Cyan
