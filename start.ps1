# Lewis AI System - 快速启动脚本
# 使用现有的 .env 配置直接启动服务

Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Lewis AI System - 快速启动" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# 检查.env文件
if (-not (Test-Path ".env")) {
    Write-Host "✗ .env 文件不存在！" -ForegroundColor Red
    exit 1
}

Write-Host "✓ 发现 .env 配置文件" -ForegroundColor Green

# 检查必需配置
$envContent = Get-Content .env -Raw

# 自动生成缺失的密钥
$modified = $false

if ($envContent -match 'your_secret_key_here') {
    Write-Host "🔐 生成 SECRET_KEY..." -ForegroundColor Yellow
    $bytes = New-Object byte[] 32
    [System.Security.Cryptography.RNGCryptoServiceProvider]::Create().GetBytes($bytes)
    $SECRET_KEY = ($bytes | ForEach-Object { $_.ToString("x2") }) -join ''
    $envContent = $envContent -replace 'your_secret_key_here', $SECRET_KEY
    $modified = $true
    Write-Host "✓ SECRET_KEY 已生成" -ForegroundColor Green
}

if ($envContent -match 'your_api_key_salt_here') {
    Write-Host "🔐 生成 API_KEY_SALT..." -ForegroundColor Yellow
    $bytes = New-Object byte[] 16
    [System.Security.Cryptography.RNGCryptoServiceProvider]::Create().GetBytes($bytes)
    $API_KEY_SALT = ($bytes | ForEach-Object { $_.ToString("x2") }) -join ''
    $envContent = $envContent -replace 'your_api_key_salt_here', $API_KEY_SALT
    $modified = $true
    Write-Host "✓ API_KEY_SALT 已生成" -ForegroundColor Green
}

if ($modified) {
    Set-Content .env $envContent
    Write-Host "✓ 配置文件已更新" -ForegroundColor Green
}

# 验证API密钥
if ($envContent -notmatch 'sk-or-v1-') {
    Write-Host ""
    Write-Host "⚠ 警告: 未检测到 OPENROUTER_API_KEY" -ForegroundColor Yellow
    Write-Host "系统将使用Mock模式运行" -ForegroundColor Yellow
    Write-Host ""
}

if ($envContent -notmatch '(?m)^DATABASE_URL\s*=\s*\S+') {
    Write-Host "✗ DATABASE_URL 未在 .env 中配置，无法连接数据库" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "📦 启动服务..." -ForegroundColor Cyan

# 检查Docker
try {
    docker --version | Out-Null
} catch {
    Write-Host "✗ Docker未安装或未启动" -ForegroundColor Red
    Write-Host "请先启动 Docker Desktop" -ForegroundColor Yellow
    exit 1
}

# 停止旧容器
Write-Host "🛑 停止旧容器..." -ForegroundColor Gray
docker compose down 2>$null

# 构建镜像
Write-Host "🏗️ 构建镜像..." -ForegroundColor Yellow
docker compose build
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ 构建失败" -ForegroundColor Red
    exit 1
}

# 启动数据库
Write-Host "🗄️ 启动数据库容器..." -ForegroundColor Gray
docker compose up -d postgres
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Postgres 启动失败" -ForegroundColor Red
    exit 1
}

# 执行数据库初始化
Write-Host "🧱 执行数据库迁移..." -ForegroundColor Yellow
docker compose run --rm -e SKIP_ENTRYPOINT_DB_INIT=1 lewis-api python -m lewis_ai_system.cli init-db
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ 数据库迁移失败，检查 postgres/lewis-api 日志" -ForegroundColor Red
    exit 1
}

# 启动服务
Write-Host "🚀 启动新容器..." -ForegroundColor Yellow
docker compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "✗ 启动失败" -ForegroundColor Red
    Write-Host "查看日志: docker compose logs" -ForegroundColor Yellow
    exit 1
}

# 等待启动
Write-Host ""
Write-Host "⏳ 等待服务就绪..." -ForegroundColor Yellow
Start-Sleep -Seconds 8

# 健康检查
$maxRetries = 20
$retryCount = 0
$healthOk = $false

while ($retryCount -lt $maxRetries) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/healthz" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $healthOk = $true
            break
        }
    } catch {
        # 继续重试
    }
    $retryCount++
    Start-Sleep -Seconds 1
}

Write-Host ""

if ($healthOk) {
    Write-Host "═══════════════════════════════════════════════" -ForegroundColor Green
    Write-Host "  ✅ 服务启动成功！" -ForegroundColor Green
    Write-Host "═══════════════════════════════════════════════" -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 服务地址:" -ForegroundColor Cyan
    Write-Host "  • API: http://localhost:8000" -ForegroundColor White
    Write-Host "  • 文档: http://localhost:8000/docs" -ForegroundColor White
    Write-Host "  • 健康检查: http://localhost:8000/healthz" -ForegroundColor White
    Write-Host ""
    Write-Host "📝 常用命令:" -ForegroundColor Cyan
    Write-Host "  docker compose logs -f     # 查看日志" -ForegroundColor Gray
    Write-Host "  docker compose ps          # 查看状态" -ForegroundColor Gray
    Write-Host "  docker compose down        # 停止服务" -ForegroundColor Gray
    Write-Host "  docker compose restart     # 重启服务" -ForegroundColor Gray
    Write-Host ""
    
    # 打开浏览器
    $openBrowser = Read-Host "是否在浏览器中打开API文档? (Y/n)"
    if ($openBrowser -ne 'n' -and $openBrowser -ne 'N') {
        Start-Process "http://localhost:8000/docs"
    }
    
} else {
    Write-Host "═══════════════════════════════════════════════" -ForegroundColor Red
    Write-Host "  ⚠ 服务启动异常" -ForegroundColor Red
    Write-Host "═══════════════════════════════════════════════" -ForegroundColor Red
    Write-Host ""
    Write-Host "容器已启动但健康检查失败" -ForegroundColor Yellow
    Write-Host "请查看日志排查问题: docker compose logs -f lewis-api" -ForegroundColor Yellow
    Write-Host ""
    
    # 显示最后几行日志
    Write-Host "最近日志:" -ForegroundColor Cyan
    docker compose logs --tail=20 lewis-api
}
