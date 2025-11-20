# 前端快速启动脚本
# 用于本地开发环境

Write-Host "启动 Lewis AI System 前端..." -ForegroundColor Cyan

# 切换到前端目录
Set-Location "$PSScriptRoot\frontend"

# 检查node_modules
if (-not (Test-Path "node_modules")) {
    Write-Host "安装依赖..." -ForegroundColor Yellow
    npm install
}

# 检查环境变量文件
if (-not (Test-Path ".env.local")) {
    Write-Host "创建 .env.local 文件..." -ForegroundColor Yellow
    @"
# 本地开发环境变量
BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_API_BASE=/api
"@ | Out-File -FilePath ".env.local" -Encoding utf8
}

# 杀掉占用3000端口的进程
$connections = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
if ($connections) {
    Write-Host "释放3000端口..." -ForegroundColor Yellow
    $connections | ForEach-Object {
        $process = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue
        if ($process) {
            Write-Host "  停止进程: $($process.ProcessName) (PID: $($process.Id))"
            Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        }
    }
    Start-Sleep -Seconds 2
}

Write-Host "`n✓ 启动前端开发服务器..." -ForegroundColor Green
Write-Host "  URL: http://localhost:3000`n" -ForegroundColor Cyan

# 使用npm run dev启动
npm run dev
