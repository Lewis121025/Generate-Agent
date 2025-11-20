# ✅ 生产部署检查清单

使用本检查清单确保系统成功部署到生产环境。

---

## 📋 部署前检查

### 1. 环境准备
- [ ] Python 3.11+ 已安装（推荐 3.13）
- [ ] Node.js 18+ 已安装
- [ ] Docker 和 Docker Compose 已安装（推荐）
- [ ] PostgreSQL 数据库可用（本地或云端）
- [ ] Redis 服务可用（可选，推荐）

### 2. API密钥获取
- [ ] OpenRouter API Key（必需，用于LLM）
- [ ] Runway API Key（可选，用于视频生成）
- [ ] Pika API Key（可选，用于视频生成）
- [ ] Runware API Key（可选，用于视频生成）
- [ ] ElevenLabs API Key（可选，用于语音合成）
- [ ] Tavily API Key（可选，用于网页搜索）

### 3. 配置文件
- [ ] 复制 `.env.example` 为 `.env`
- [ ] 填写所有必需的API密钥
- [ ] 配置 `DATABASE_URL`（生产环境使用真实数据库）
- [ ] 配置 `REDIS_URL`（推荐）
- [ ] 设置 `SECRET_KEY`（32字符随机字符串）
- [ ] 配置 `CORS_ORIGINS`（前端域名）
- [ ] 设置 `APP_ENV=production`

### 4. 存储配置
- [ ] 配置S3存储（或兼容服务）
  - `S3_BUCKET_NAME`
  - `S3_REGION`
  - `S3_ACCESS_KEY`
  - `S3_SECRET_KEY`
- [ ] 或使用本地文件存储（测试用）

---

## 🔍 部署验证

### 自动验证
```bash
python verify_deployment.py
```

**预期结果**：
```
[必需项检查]
✅ Python 版本 (>= 3.11)
✅ Python 依赖
✅ 后端模块导入
✅ 环境配置
✅ 端口可用性

必需项通过: 5/5
[OK] 系统已就绪，可以部署!
```

### 手动验证步骤

#### 步骤1: 测试后端
```bash
# 运行所有测试
pytest

# 预期: 58 passed
```

#### 步骤2: 测试后端启动
```bash
uvicorn lewis_ai_system.main:app --host 0.0.0.0 --port 8000
```

- [ ] 访问 http://localhost:8000/health 返回 `{"status":"healthy"}`
- [ ] 访问 http://localhost:8000/docs 显示API文档
- [ ] 日志无严重错误

#### 步骤3: 测试前端构建
```bash
cd frontend
npm install
npm run build
```

- [ ] 构建成功，无错误
- [ ] 输出显示所有路由已优化

#### 步骤4: 测试前端启动
```bash
npm run dev  # 开发模式
# 或
npm run start  # 生产模式（需先build）
```

- [ ] 访问 http://localhost:3000 显示主页
- [ ] 侧边栏可折叠
- [ ] 设置页面正常显示
- [ ] 无控制台错误

#### 步骤5: 功能测试

**创作模式测试**:
- [ ] 选择创作模式
- [ ] 输入测试提示词
- [ ] 工作流启动成功
- [ ] 状态更新正常
- [ ] 可以查看项目详情

**通用模式测试**:
- [ ] 选择通用模式
- [ ] 输入测试任务
- [ ] ReAct循环执行
- [ ] 显示思考过程
- [ ] 返回最终结果

**设置页面测试**:
- [ ] 打开设置页面
- [ ] 可以查看/编辑API密钥
- [ ] 主题切换正常
- [ ] 系统信息显示正确

---

## 🚀 部署方法选择

### 方法1: Docker Compose（推荐生产环境）

**优点**: 
- ✅ 一键部署
- ✅ 环境隔离
- ✅ 易于扩展

**步骤**:
```bash
# 1. 构建镜像
docker-compose build

# 2. 启动服务
docker-compose up -d

# 3. 查看状态
docker-compose ps

# 4. 查看日志
docker-compose logs -f
```

**验证**:
- [ ] 所有容器状态为 `Up`
- [ ] 访问前端 http://localhost:3000
- [ ] 访问后端 http://localhost:8000/docs
- [ ] 数据库连接正常

### 方法2: 一键启动脚本

**适用**: 快速测试和开发

```powershell
# Windows
.\start.ps1

# Linux/macOS
./start.sh
```

**验证**:
- [ ] 脚本执行无错误
- [ ] 所有服务启动成功
- [ ] 端口正常监听

### 方法3: 手动部署

**适用**: 自定义配置需求

**后端部署**:
```bash
# 1. 安装依赖
pip install -e .

# 2. 初始化数据库
python -m lewis_ai_system.cli init-db

# 3. 启动（使用进程管理器）
gunicorn lewis_ai_system.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

**前端部署**:
```bash
cd frontend

# 1. 安装依赖
npm install

# 2. 构建
npm run build

# 3. 启动
npm run start
```

---

## 🔒 安全检查

### 生产环境安全清单
- [ ] `SECRET_KEY` 使用强随机字符串（至少32字符）
- [ ] `API_KEY_SALT` 使用强随机字符串
- [ ] 所有API密钥已妥善保管
- [ ] `.env` 文件不在版本控制中
- [ ] `APP_ENV` 设置为 `production`
- [ ] CORS配置限制了允许的域名
- [ ] 数据库使用强密码
- [ ] Redis设置了密码（如果暴露）
- [ ] 启用HTTPS（生产环境）
- [ ] 配置防火墙规则

### 数据安全
- [ ] 数据库定期备份
- [ ] S3存储配置访问权限
- [ ] 日志不包含敏感信息
- [ ] API密钥加密存储

---

## 📊 监控设置

### 日志监控
- [ ] 配置日志级别（生产环境建议 `INFO` 或 `WARNING`）
- [ ] 设置日志轮转
- [ ] 配置日志聚合（如ELK、Loki）

### 性能监控
- [ ] 安装APM工具（如Prometheus）
- [ ] 配置指标收集
- [ ] 设置Grafana仪表板

### 告警配置
- [ ] 服务宕机告警
- [ ] 错误率告警
- [ ] 响应时间告警
- [ ] 成本异常告警

---

## 🔧 故障排除

### 常见问题

**问题1: 端口被占用**
```bash
# Windows查看端口
netstat -ano | findstr :8000
netstat -ano | findstr :3000

# Linux/macOS
lsof -i :8000
lsof -i :3000
```
解决: 停止占用进程或修改端口配置

**问题2: 数据库连接失败**
```bash
# 测试数据库连接
python -c "from lewis_ai_system.database import engine; print(engine.connect())"
```
解决: 检查 `DATABASE_URL` 配置和数据库服务状态

**问题3: API调用失败**
- 检查API密钥是否正确
- 验证网络连接和代理设置
- 查看后端日志获取详细错误

**问题4: Docker启动失败**
```bash
# 查看详细日志
docker-compose logs

# 重新构建
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

**问题5: 前端打包错误**
```bash
cd frontend
rm -rf node_modules .next
npm install
npm run build
```

---

## 📈 性能优化

### 后端优化
- [ ] 配置多个worker进程
- [ ] 启用Redis缓存
- [ ] 配置数据库连接池
- [ ] 启用gzip压缩

### 前端优化
- [ ] 启用静态页面生成
- [ ] 配置CDN
- [ ] 启用图片优化
- [ ] 配置浏览器缓存

---

## 🎯 生产就绪标准

### 核心功能
- [x] 创作模式完整工作流
- [x] 通用模式ReAct循环
- [x] 视频预览功能
- [x] API密钥管理
- [x] 设置页面
- [x] 侧边栏导航

### 质量保证
- [x] 58个测试全部通过
- [x] 无严重bug
- [x] 前端构建成功
- [x] 后端健康检查

### 文档完整性
- [x] README.md
- [x] QUICKSTART.md
- [x] DEPLOYMENT.md
- [x] VIDEO_PREVIEW_GUIDE.md
- [x] PRODUCTION_READY.md
- [x] .env.example

### 部署支持
- [x] Docker配置
- [x] 启动脚本
- [x] 验证脚本
- [x] 健康检查端点

---

## ✅ 部署完成验证

完成部署后，确认以下所有项目：

### 基础验证
- [ ] 前端页面可访问
- [ ] 后端API可访问
- [ ] API文档正常显示
- [ ] 健康检查通过

### 功能验证
- [ ] 创作模式可以创建项目
- [ ] 通用模式可以执行任务
- [ ] 视频预览功能正常
- [ ] 设置页面可以保存

### 性能验证
- [ ] 页面加载时间 < 2秒
- [ ] API响应时间 < 1秒
- [ ] 无内存泄漏
- [ ] CPU使用率正常

### 安全验证
- [ ] HTTPS配置正确（生产环境）
- [ ] API密钥未暴露
- [ ] CORS配置正确
- [ ] 无安全警告

---

## 🎉 部署成功！

如果所有检查项都已完成，恭喜你成功部署了Lewis AI System！

**下一步**:
1. 监控系统运行状态
2. 收集用户反馈
3. 定期更新和维护
4. 扩展新功能

**获取支持**:
- 📖 查看文档: [DEPLOYMENT.md](DEPLOYMENT.md)
- 🐛 报告问题: GitHub Issues
- 💬 联系团队

---

**部署日期**: _____________  
**部署人员**: _____________  
**环境**: □ 测试 □ 预发布 □ 生产  
**备注**: _____________
