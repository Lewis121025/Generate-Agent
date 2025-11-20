# Lewis AI System - 数据库服务停止脚本
# 停止 PostgreSQL、Redis 和 Weaviate 数据库服务

Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Lewis AI System - 数据库服务停止" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# 检查Docker
try {
    docker --version | Out-Null
} catch {
    Write-Host "✗ Docker未安装或未启动" -ForegroundColor Red
    exit 1
}

# 检查是否有运行中的数据库服务
$runningServices = docker compose ps postgres redis weaviate --format json | ConvertFrom-Json | Where-Object { $_.State -eq "running" }

if (-not $runningServices) {
    Write-Host "ℹ 没有运行中的数据库服务" -ForegroundColor Yellow
    exit 0
}

Write-Host "📊 当前运行的服务:" -ForegroundColor Yellow
docker compose ps postgres redis weaviate
Write-Host ""

# 询问是否清理数据卷
$cleanVolumes = $false
$response = Read-Host "是否删除数据卷？这将清除所有数据库数据 (y/N)"
if ($response -eq 'y' -or $response -eq 'Y') {
    $cleanVolumes = $true
    Write-Host "⚠ 警告: 将删除所有数据库数据！" -ForegroundColor Red
    $confirm = Read-Host "确认删除？输入 'yes' 继续"
    if ($confirm -ne 'yes') {
        Write-Host "已取消操作" -ForegroundColor Yellow
        exit 0
    }
}

Write-Host ""
Write-Host "🛑 停止数据库服务..." -ForegroundColor Yellow

if ($cleanVolumes) {
    Write-Host "🗑️ 停止服务并删除数据卷..." -ForegroundColor Yellow
    docker compose down -v postgres redis weaviate
} else {
    Write-Host "⏸️ 停止服务（保留数据卷）..." -ForegroundColor Yellow
    docker compose stop postgres redis weaviate
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ 停止服务时出错" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  ✅ 数据库服务已停止" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""

if ($cleanVolumes) {
    Write-Host "📝 数据卷已删除，所有数据已清除" -ForegroundColor Cyan
} else {
    Write-Host "📝 数据卷已保留，数据未丢失" -ForegroundColor Cyan
    Write-Host "   重新启动: .\scripts\start-databases.ps1" -ForegroundColor Gray
}

Write-Host ""

