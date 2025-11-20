# 快速入门指南 🚀

本指南帮助你在5分钟内启动Lewis AI System并体验核心功能。

## 前置要求

- Python 3.11+ （推荐3.13）
- Node.js 18+ （前端开发需要）
- Docker Desktop（可选，推荐）
- 至少一个AI Provider API Key（OpenRouter/Runway/Pika等）

## 步骤1：获取代码

```bash
git clone https://github.com/yourusername/Lewis_AI_System.git
cd Lewis_AI_System
```

## 步骤2：配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env，至少填入以下密钥：
# OPENROUTER_API_KEY=your_key_here  # 用于LLM调用
# RUNWAY_API_KEY=your_key_here      # 用于视频生成（可选）
```

**最小配置示例**：
```env
APP_ENV=development
LOG_LEVEL=INFO
SECRET_KEY=your-secret-key-here
LLM_PROVIDER_MODE=openrouter
OPENROUTER_API_KEY=sk-or-xxx
VIDEO_PROVIDER=runway
RUNWAY_API_KEY=your-runway-key
```

## 步骤3：启动系统

### 选项A：一键启动（推荐）

**Windows**:
```powershell
.\start.ps1
```

**Linux/macOS**:
```bash
chmod +x start.sh
./start.sh
```

脚本会自动完成所有设置和启动步骤。

### 选项B：手动启动

```bash
# 1. 安装Python依赖
pip install -e .

# 2. 初始化数据库
python -m lewis_ai_system.cli init-db

# 3. 启动后端
uvicorn lewis_ai_system.main:app --host 0.0.0.0 --port 8000

# 4. 在新终端启动前端
cd frontend
npm install
npm run dev
```

### 选项C：Docker Compose

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

## 步骤4：访问系统

- **前端界面**: http://localhost:3000
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

## 步骤5：验证安装

运行验证脚本：
```bash
python verify_deployment.py
```

应该看到所有检查项都显示 ✅。

## 快速体验功能

### 体验1：创作模式（视频生成）

1. 打开 http://localhost:3000
2. 点击"创作模式"卡片
3. 在输入框输入：
   ```
   制作一个30秒的科技产品宣传视频，展示AI助手的核心功能
   ```
4. 按 Ctrl+Enter（或点击"生成"）
5. 等待工作流完成：
   - 文案扩展 → 脚本生成 → 分镜规划 → 视频生成 → 质量检查
6. 完成后点击项目查看视频预览和分镜

### 体验2：通用模式（任务执行）

1. 返回首页，点击"通用模式"
2. 输入任务：
   ```
   搜索"2024年AI发展趋势"并总结前3条结果
   ```
3. 观察ReAct循环的思考和执行过程
4. 查看最终整理的结果

### 体验3：设置页面

1. 点击左侧边栏的"设置"图标
2. 在"API Keys"标签下管理你的API密钥
3. 在"Appearance"标签切换主题（Light/Dark/System）
4. 在"Profile"标签查看系统信息

## 运行测试

验证系统完整性：
```bash
# 运行所有58个测试
pytest

# 快速验证核心功能
pytest tests/test_full_system.py tests/test_creative_workflow.py tests/test_general_session.py -v
```

## 常见问题

### Q1: 端口被占用
```bash
# 检查端口占用
# Windows
netstat -ano | findstr :3000
netstat -ano | findstr :8000

# Linux/macOS
lsof -i :3000
lsof -i :8000
```

解决：修改 `.env` 中的端口或停止占用进程。

### Q2: API密钥不生效
- 确保 `.env` 文件在项目根目录
- 检查密钥格式是否正确（无引号，无空格）
- 重启服务以加载新配置

### Q3: Docker启动失败
```bash
# 查看详细错误
docker-compose logs

# 重新构建
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Q4: 前端构建错误
```bash
cd frontend
rm -rf node_modules .next
npm install
npm run build
```

### Q5: 数据库连接失败
- 检查 `DATABASE_URL` 是否正确
- 确保PostgreSQL服务已启动
- 运行 `python -m lewis_ai_system.cli init-db` 初始化

## 下一步

- 📖 阅读 [DEPLOYMENT.md](DEPLOYMENT.md) 了解生产部署
- 🎨 查看 [FRONTEND_REFACTOR_SUMMARY.md](FRONTEND_REFACTOR_SUMMARY.md) 了解界面设计
- 🎬 阅读 [VIDEO_PREVIEW_GUIDE.md](VIDEO_PREVIEW_GUIDE.md) 了解视频预览功能
- 🏗️ 查看 [docs/architecture.md](docs/architecture.md) 理解系统架构

## 获取帮助

- 📋 查看 [GitHub Issues](https://github.com/yourusername/Lewis_AI_System/issues)
- 📧 联系开发团队
- 📖 阅读完整文档

---

**恭喜！** 你已经成功启动Lewis AI System。开始探索AI视频创作和智能任务执行的强大功能吧！🎉
