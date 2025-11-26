# 在 Airflow 容器中安装量化分析依赖的脚本

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Airflow 量化DAG依赖安装脚本" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 检查容器状态
Write-Host "[1/4] 检查容器状态..." -ForegroundColor Yellow
$containerStatus = docker ps --filter "name=airflow_new-airflow-standalone" --format "{{.Status}}"
if ($containerStatus -like "*Up*") {
    Write-Host "✅ 容器运行正常" -ForegroundColor Green
} else {
    Write-Host "❌ 容器未运行，请先启动容器！" -ForegroundColor Red
    Write-Host "运行命令: docker compose -f docker-compose-standalone.yml up -d" -ForegroundColor Yellow
    exit 1
}

# 检查 requirements.txt
Write-Host "`n[2/4] 检查依赖文件..." -ForegroundColor Yellow
if (Test-Path "requirements.txt") {
    Write-Host "✅ 找到 requirements.txt" -ForegroundColor Green
    Get-Content "requirements.txt" | ForEach-Object { Write-Host "  - $_" -ForegroundColor Gray }
} else {
    Write-Host "❌ 未找到 requirements.txt！" -ForegroundColor Red
    exit 1
}

# 安装依赖
Write-Host "`n[3/4] 安装 Python 依赖包..." -ForegroundColor Yellow
Write-Host "这可能需要几分钟时间，请耐心等待..." -ForegroundColor Gray

$installCmd = "pip install --no-cache-dir -r /opt/airflow/requirements.txt"
docker exec airflow_new-airflow-standalone-1 bash -c $installCmd

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 依赖安装成功" -ForegroundColor Green
} else {
    Write-Host "❌ 依赖安装失败！请检查错误信息" -ForegroundColor Red
    exit 1
}

# 验证安装
Write-Host "`n[4/4] 验证依赖安装..." -ForegroundColor Yellow
$packages = @("backtrader", "pandas", "numpy", "loguru")
$allInstalled = $true

foreach ($pkg in $packages) {
    $checkCmd = "python -c 'import $pkg; print($pkg.__version__)' 2>&1"
    $result = docker exec airflow_new-airflow-standalone-1 bash -c $checkCmd
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ $pkg 已安装: $result" -ForegroundColor Green
    } else {
        Write-Host "❌ $pkg 安装失败" -ForegroundColor Red
        $allInstalled = $false
    }
}

# 总结
Write-Host "`n========================================" -ForegroundColor Cyan
if ($allInstalled) {
    Write-Host "✅ 所有依赖安装成功！" -ForegroundColor Green
    Write-Host "`n下一步操作:" -ForegroundColor White
    Write-Host "1. 刷新 Airflow Web UI (http://localhost:8080)" -ForegroundColor Gray
    Write-Host "2. 检查 DAG 导入错误是否已消除" -ForegroundColor Gray
    Write-Host "3. 手动触发 DAG 进行测试:" -ForegroundColor Gray
    Write-Host "   - jq_backtrader_precision (回测策略)" -ForegroundColor Gray
    Write-Host "   - starquant_factor_pipeline (因子分析)" -ForegroundColor Gray
} else {
    Write-Host "⚠️  部分依赖安装失败，请检查错误信息" -ForegroundColor Yellow
}
Write-Host "========================================`n" -ForegroundColor Cyan
