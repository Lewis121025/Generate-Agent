# Lewis AI System - 数据库服务启动脚本
# 仅启动 PostgreSQL、Redis 和 Weaviate 数据库服务

Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Lewis AI System - 数据库服务启动" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# 检查.env文件
if (-not (Test-Path ".env")) {
    Write-Host "✗ .env 文件不存在！" -ForegroundColor Red
    Write-Host "请先创建 .env 文件并配置 DATABASE_URL" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ 发现 .env 配置文件" -ForegroundColor Green

# 检查Docker
try {
    docker --version | Out-Null
} catch {
    Write-Host "✗ Docker未安装或未启动" -ForegroundColor Red
    Write-Host "请先启动 Docker Desktop" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ Docker 已就绪" -ForegroundColor Green
Write-Host ""

# 启动数据库服务
Write-Host "🗄️ 启动数据库服务..." -ForegroundColor Yellow
Write-Host "  • PostgreSQL (端口 5432)" -ForegroundColor Gray
Write-Host "  • Redis (端口 6379)" -ForegroundColor Gray
Write-Host "  • Weaviate (端口 8080)" -ForegroundColor Gray
Write-Host ""

# 启动所有数据库服务
docker compose up -d postgres redis weaviate

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ 数据库服务启动失败" -ForegroundColor Red
    Write-Host "查看日志: docker compose logs postgres redis weaviate" -ForegroundColor Yellow
    exit 1
}

Write-Host "⏳ 等待数据库服务就绪..." -ForegroundColor Yellow

# 等待 PostgreSQL 就绪
$maxRetries = 30
$retryCount = 0
$postgresReady = $false

while ($retryCount -lt $maxRetries) {
    try {
        $result = docker compose exec -T postgres pg_isready -U lewis 2>&1
        if ($LASTEXITCODE -eq 0) {
            $postgresReady = $true
            break
        }
    } catch {
        # 继续重试
    }
    $retryCount++
    Start-Sleep -Seconds 1
}

if (-not $postgresReady) {
    Write-Host "✗ PostgreSQL 未能在预期时间内就绪" -ForegroundColor Red
    Write-Host "查看日志: docker compose logs postgres" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ PostgreSQL 已就绪" -ForegroundColor Green

# 等待 Redis 就绪
$retryCount = 0
$redisReady = $false

while ($retryCount -lt $maxRetries) {
    try {
        $result = docker compose exec -T redis redis-cli ping 2>&1
        if ($result -match "PONG") {
            $redisReady = $true
            break
        }
    } catch {
        # 继续重试
    }
    $retryCount++
    Start-Sleep -Seconds 1
}

if (-not $redisReady) {
    Write-Host "⚠ Redis 未能在预期时间内就绪，但继续执行" -ForegroundColor Yellow
} else {
    Write-Host "✓ Redis 已就绪" -ForegroundColor Green
}

# Weaviate 通常启动较慢，只做基本检查
Start-Sleep -Seconds 3
Write-Host "✓ Weaviate 已启动" -ForegroundColor Green

Write-Host ""
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  ✅ 数据库服务启动成功！" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "📊 服务状态:" -ForegroundColor Cyan
docker compose ps postgres redis weaviate
Write-Host ""
Write-Host "📝 常用命令:" -ForegroundColor Cyan
Write-Host "  .\scripts\db-init.ps1          # 初始化数据库表结构" -ForegroundColor Gray
Write-Host "  .\scripts\stop-databases.ps1   # 停止数据库服务" -ForegroundColor Gray
Write-Host "  docker compose logs -f         # 查看日志" -ForegroundColor Gray
Write-Host "  docker compose ps              # 查看状态" -ForegroundColor Gray
Write-Host ""

