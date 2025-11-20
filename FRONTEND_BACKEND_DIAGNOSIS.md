# 前后端问题诊断与解决方案

## 诊断时间
2025年11月20日

## 问题总结

### 后端 ✓ 正常运行
- **状态**: 健康
- **地址**: http://localhost:8000
- **环境**: production
- **数据**: 已有3个创意项目

### 前端 ⚠ 存在问题

#### 1. 配置文件冲突 ✓ 已解决
**问题描述**:
- 同时存在 `next.config.mjs` 和 `next.config.ts` 两个配置文件
- Next.js优先使用 `.mjs` 文件
- `.mjs` 默认配置为 Docker 服务名 `lewis-api:8000`，导致本地开发无法连接后端

**解决方案**:
- 修改 `frontend/next.config.mjs`，将默认后端地址改为 `http://localhost:8000`
- 创建 `frontend/.env.local` 文件，明确配置本地开发环境变量:
  ```
  BACKEND_URL=http://localhost:8000
  NEXT_PUBLIC_API_BASE=/api
  ```

#### 2. API代理500错误 ✓ 已解决
**问题描述**:
- 前端通过 `/api/*` 代理访问后端时返回500错误
- 直接访问后端 API 正常

**根本原因**:
- Next.js代理配置使用了Docker服务名，本地开发时无法解析

**解决方案**:
- 见问题1的解决方案

#### 3. 前端服务器异常退出 ✓ 已解决
**问题描述**:
- `npm run dev` 启动后显示 "Ready"，但立即退出
- Exit code: 1

**根本原因**:
- PowerShell终端在后台运行模式下会在命令完成后关闭
- Next.js dev服务器需要持续运行，但终端环境退出导致进程终止

**解决方案**:
- 使用 `Start-Job` 在PowerShell后台任务中运行
- 命令示例：
  ```powershell
  $job = Start-Job -ScriptBlock { 
      Set-Location "c:\Learn\Lewis_AI_System\frontend"
      npm run dev 
  }
  ```
- 或在新的PowerShell窗口中运行（推荐）

## 测试结果

### 后端测试
```powershell
✓ http://localhost:8000/healthz - 200 OK
✓ http://localhost:8000/creative/projects - 200 OK，返回3个项目
✓ http://localhost:8000/docs - 200 OK
```

### 前端测试 (修复后)
```powershell
✓ http://localhost:3000 - 200 OK
✓ http://localhost:3000/api/creative/projects - 200 OK，通过代理获取到16个项目
✓ API代理功能正常
✓ 配置文件已更新
✓ 环境变量文件已创建
✓ 服务器运行正常
```

## 使用说明

### 启动后端
```powershell
# 已经在运行中，端口8000
# 如需重启:
cd c:\Learn\Lewis_AI_System
.\start.ps1
```

### 启动前端
```powershell
# 方法1: 使用后台任务（推荐）
cd c:\Learn\Lewis_AI_System
$job = Start-Job -ScriptBlock { Set-Location "c:\Learn\Lewis_AI_System\frontend"; npm run dev }

# 方法2: 在新窗口中启动
cd c:\Learn\Lewis_AI_System\frontend
Start-Process pwsh -ArgumentList "-NoExit", "-Command", "npm run dev"

# 检查任务状态
Get-Job
```

### 访问系统
- 前端: http://localhost:3000
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

## 建议

1. **删除重复配置**: 建议只保留 `next.config.ts` 或 `next.config.mjs` 其中之一
2. **环境配置管理**: 
   - 使用 `.env.local` 用于本地开发
   - 使用 `.env.production` 用于生产环境（Docker）
3. **启动脚本**: 使用提供的 PowerShell 脚本确保正确启动
4. **Docker部署**: 如果使用Docker Compose，环境变量会自动配置正确

## 已修复的文件

1. `frontend/next.config.mjs` - 修改默认后端地址
2. `frontend/.env.local` - 新建本地环境变量文件
3. `start-frontend.ps1` - 新建前端启动脚本

## 下一步

如果前端仍无法正常启动，建议:
1. 检查 Node.js 版本 (建议 >=18.17.0)
2. 清理并重新安装依赖:
   ```powershell
   cd frontend
   Remove-Item -Recurse -Force node_modules, .next
   npm install
   ```
3. 检查是否有防火墙或安全软件阻止
