# Lewis AI System - 部署清单

## ✅ 生产就绪检查清单

### 核心功能 ✅
- [x] 后端 API 服务
- [x] 前端 Web 应用
- [x] 创作模式工作流
- [x] 通用模式 ReAct
- [x] 治理与成本监控
- [x] 视频预览功能

### 测试覆盖 ✅
- [x] 58 个单元测试全部通过
- [x] E2E 场景测试
- [x] Provider 集成测试
- [x] 工作流状态机测试

### 前端构建 ✅
- [x] 生产构建成功
- [x] 类型检查通过
- [x] Linting 通过
- [x] 10 个页面路由
- [x] 响应式设计

### 配置文件 ✅
- [x] docker-compose.yml
- [x] Dockerfile (后端)
- [x] Dockerfile (前端)
- [x] .env.example
- [x] pyproject.toml
- [x] package.json

---

## 🚀 部署方式

### 方式 1: Docker Compose（推荐）

**优点**: 一键启动所有服务，包括数据库、缓存、向量数据库

```bash
# 1. 复制环境变量配置
cp .env.example .env

# 2. 编辑 .env 文件，填写必需的 API 密钥
# 至少需要配置: OPENROUTER_API_KEY

# 3. 启动所有服务
docker-compose up -d

# 4. 查看日志
docker-compose logs -f

# 5. 访问服务
# 前端: http://localhost:3000
# 后端: http://localhost:8000
# API文档: http://localhost:8000/docs
```

### 方式 2: 本地开发

**优点**: 快速迭代开发，无需 Docker

```bash
# 后端
cd c:\Learn\Lewis_AI_System
python -m pip install -e .
uvicorn lewis_ai_system.main:app --reload --host 0.0.0.0 --port 8000

# 前端（新终端）
cd frontend
npm install
npm run dev
```

### 方式 3: 快速启动脚本

```bash
# Windows PowerShell
.\start.ps1

# Linux/Mac
./start.sh
```

---

## 📋 最低配置要求

### 必需配置
- ✅ `OPENROUTER_API_KEY` - LLM 调用（必需）
- ✅ `SECRET_KEY` - JWT 令牌签名（生产环境必需）
- ✅ `API_KEY_SALT` - API 密钥哈希（生产环境必需）

### 可选配置（功能增强）
- `DATABASE_URL` - PostgreSQL 持久化（否则使用内存存储）
- `REDIS_URL` - 缓存加速
- `VECTOR_DB_URL` - Weaviate 向量数据库
- `RUNWAY_API_KEY` / `PIKA_API_KEY` - 视频生成
- `ELEVENLABS_API_KEY` - 语音合成
- `S3_*` - 对象存储（否则使用本地文件）

---

## 🌐 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| 前端 | 3000 | Next.js Web 应用 |
| 后端 API | 8000 | FastAPI 服务 |
| PostgreSQL | 5432 | 数据库（可选）|
| Redis | 6379 | 缓存（可选）|
| Weaviate | 8080 | 向量数据库（可选）|

---

## 📊 系统架构

```
┌─────────────────┐
│   Browser       │
│  (localhost:3000)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Next.js Frontend│
│  - React UI     │
│  - Tailwind CSS │
└────────┬────────┘
         │ HTTP/REST
         ▼
┌─────────────────┐
│  FastAPI Backend│
│  (localhost:8000)│
│  - Creative Mode│
│  - General Mode │
│  - Governance   │
└────────┬────────┘
         │
    ┌────┴────┬────────┬──────────┐
    ▼         ▼        ▼          ▼
┌────────┐ ┌──────┐ ┌──────┐  ┌─────────┐
│Postgres│ │Redis │ │Vector│  │ Storage │
│  (DB)  │ │(Cache)│ │ (DB) │  │ (S3/FS) │
└────────┘ └──────┘ └──────┘  └─────────┘
```

---

## 🔐 安全配置

### 生产环境必须更改
```bash
# 生成随机密钥
python -c "import secrets; print(secrets.token_hex(32))"

# 更新 .env
SECRET_KEY=<生成的密钥>
API_KEY_SALT=<生成的密钥>
```

### CORS 配置
```bash
# 开发环境
CORS_ORIGINS=*

# 生产环境
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

---

## 📈 性能优化

### 推荐配置
- ✅ 启用 Redis 缓存
- ✅ 使用 PostgreSQL 持久化
- ✅ 配置 S3 存储（大文件）
- ✅ 启用 Weaviate 向量搜索

### 资源需求
- **最小**: 2 CPU, 4GB RAM（仅 API + 前端）
- **推荐**: 4 CPU, 8GB RAM（完整堆栈）
- **高负载**: 8 CPU, 16GB RAM + Redis + Postgres

---

## 🔍 健康检查

```bash
# 后端健康检查
curl http://localhost:8000/healthz

# 前端健康检查
curl http://localhost:3000

# API 文档
open http://localhost:8000/docs
```

---

## 📝 API 密钥获取

| Provider | 注册地址 | 说明 |
|----------|---------|------|
| OpenRouter | https://openrouter.ai/ | LLM 调用（必需）|
| Runway | https://runwayml.com/ | 视频生成 |
| Pika | https://pika.art/ | 视频生成 |
| ElevenLabs | https://elevenlabs.io/ | 语音合成 |

---

## 🐛 故障排查

### 问题: 后端无法启动
```bash
# 检查依赖
pip install -e .

# 检查配置
cat .env | grep OPENROUTER_API_KEY

# 查看详细日志
LOG_LEVEL=DEBUG uvicorn lewis_ai_system.main:app
```

### 问题: 前端构建失败
```bash
cd frontend
rm -rf node_modules .next
npm install
npm run build
```

### 问题: 数据库连接失败
```bash
# 方式1: 不使用数据库（内存模式）
# 在 .env 中注释掉 DATABASE_URL

# 方式2: 启动 PostgreSQL
docker-compose up -d postgres
```

---

## 📦 数据备份

### 备份 artifacts 目录
```bash
tar -czf artifacts-backup-$(date +%Y%m%d).tar.gz artifacts/
```

### 备份数据库
```bash
docker-compose exec postgres pg_dump -U lewis lewis_db > backup.sql
```

---

## 🔄 升级流程

```bash
# 1. 备份数据
./backup.sh

# 2. 拉取最新代码
git pull

# 3. 重新构建
docker-compose down
docker-compose build
docker-compose up -d

# 4. 检查健康状态
docker-compose ps
curl http://localhost:8000/healthz
```

---

## 📞 支持与文档

- 📖 API 文档: http://localhost:8000/docs
- 🎬 视频预览指南: `VIDEO_PREVIEW_GUIDE.md`
- 🎨 前端重构总结: `FRONTEND_REFACTOR_SUMMARY.md`
- 🐛 问题修复记录: `FIXES_SUMMARY.md`
- 📊 项目完成报告: `PROJECT_COMPLETION_REPORT.md`

---

## ✅ 生产就绪确认

- ✅ **代码质量**: 58 个测试全部通过
- ✅ **前端构建**: 生产优化完成
- ✅ **Docker 支持**: 完整的容器化配置
- ✅ **环境配置**: 灵活的 .env 配置
- ✅ **文档完整**: 全面的使用和部署文档
- ✅ **安全性**: JWT 认证、密钥管理
- ✅ **可观测性**: 日志、健康检查、成本监控
- ✅ **扩展性**: 模块化架构、Provider 可插拔

**系统状态**: 🟢 生产就绪

**部署难度**: ⭐⭐ (简单)

**维护难度**: ⭐⭐ (简单)

---

**更新时间**: 2025-11-20  
**版本**: v0.2.0  
**状态**: ✅ Production Ready
