# Lewis AI System - 生产环境部署指南

本指南详细说明如何将 Lewis AI System 从原型部署到生产环境。

## 前置准备

### 1. 基础设施要求

- **计算资源**: 4 vCPU, 8GB RAM (推荐 8 vCPU, 16GB RAM)
- **存储**: 50GB SSD (数据库 + Redis + 应用)
- **网络**: 公网 IP + 域名 (支持 HTTPS)
- **操作系统**: Ubuntu 22.04 LTS / Debian 11+

### 2. 外部服务账号

必须注册以下服务并获取 API Keys:

- **AI Provider**: OpenRouter (https://openrouter.ai) - 用于 LLM 调用
- **代码沙箱**: E2B (https://e2b.dev) - 安全执行用户代码
- **视频生成**: Runway (https://runwayml.com) 或 Pika (https://pika.art)
- **认证服务**: Clerk (https://clerk.com) 或 Auth0 (https://auth0.com)
- **对象存储**: AWS S3 / Cloudflare R2 / MinIO (自托管)

### 3. 开发工具

```bash
# 安装 Docker & Docker Compose
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 安装 Node.js 20+
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# 安装 Python 3.11+
sudo apt install -y python3.11 python3.11-venv python3-pip
```

---

## 第一步: 配置环境变量

创建 `.env` 文件 (生产环境):

```bash
# ==================== 应用配置 ====================
APP_ENV=production
LOG_LEVEL=INFO
SECRET_KEY=<使用 openssl rand -hex 32 生成>
API_KEY_SALT=<使用 openssl rand -hex 16 生成>

# ==================== 数据库 ====================
DATABASE_URL=postgresql://lewis_user:STRONG_PASSWORD@postgres:5432/lewis_production
REDIS_URL=redis://redis:6379/0
REDIS_ENABLED=true

# ==================== 向量数据库 ====================
VECTOR_DB_TYPE=weaviate
VECTOR_DB_URL=http://weaviate:8080

# ==================== 对象存储 (S3) ====================
S3_ENDPOINT_URL=https://s3.amazonaws.com  # 或 Cloudflare R2 URL
S3_ACCESS_KEY=<你的 Access Key>
S3_SECRET_KEY=<你的 Secret Key>
S3_BUCKET_NAME=lewis-production-assets
S3_REGION=us-east-1

# ==================== AI Providers (必须配置!) ====================
# LLM Provider
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
LLM_PROVIDER_MODE=openrouter  # 生产环境禁止使用 mock

# 代码沙箱 (安全执行代码)
E2B_API_KEY=e2b_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 视频生成
RUNWAY_API_KEY=rw_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
VIDEO_PROVIDER=runway

# 图片生成 (可选)
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  # 用于 DALL-E 3
REPLICATE_API_KEY=r8_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 搜索引擎 (可选)
TAVILY_API_KEY=tvly-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ==================== 认证服务 ====================
AUTH_PROVIDER=clerk  # 或 auth0

# Clerk 配置
CLERK_JWKS_URL=https://clerk.your-app.com/.well-known/jwks.json

# Auth0 配置 (如果使用 Auth0)
# AUTH0_DOMAIN=your-tenant.auth0.com
# AUTH0_AUDIENCE=https://api.your-app.com

# ==================== 前端配置 ====================
NEXT_PUBLIC_API_URL=https://api.your-domain.com
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ==================== 监控与追踪 (可选) ====================
SENTRY_DSN=https://xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx@sentry.io/xxxxxxx
OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4318

# ==================== CORS 配置 ====================
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com
TRUSTED_HOSTS=*.your-domain.com,your-domain.com

# ==================== 速率限制 ====================
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
```

---

## 第二步: 初始化数据库

### 2.1 启动数据库服务

```bash
# 仅启动数据库容器
docker compose up -d postgres redis weaviate
```

### 2.2 运行数据库迁移

```bash
# 安装 Alembic
pip install alembic

# 运行迁移
cd src
alembic upgrade head
```

### 2.3 创建管理员账号

```bash
python -c "
from lewis_ai_system.database import db_manager, User
import asyncio

async def create_admin():
    await db_manager.init_database()
    async with db_manager.get_session() as db:
        admin = User(
            external_id='admin_001',
            email='admin@your-domain.com',
            credits_usd=1000.0,
            is_admin=True
        )
        db.add(admin)
        await db.commit()
        print('✅ Admin user created')

asyncio.run(create_admin())
"
```

---

## 第三步: 构建与部署后端

### 3.1 构建 Docker 镜像

```bash
# 构建生产镜像
docker build -t lewis-backend:latest -f Dockerfile .
```

### 3.2 启动后端服务

```bash
# 启动 API 服务
docker compose up -d backend

# 启动 Worker (处理异步任务)
docker compose up -d worker
```

### 3.3 验证后端健康

```bash
curl https://api.your-domain.com/health
# 预期输出: {"status": "healthy", "version": "0.2.0"}
```

---

## 第四步: 构建与部署前端

### 4.1 配置前端环境变量

在 `frontend/.env.production` 中:

```bash
NEXT_PUBLIC_API_URL=https://api.your-domain.com
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 4.2 构建前端

```bash
cd frontend
npm install
npm run build
```

### 4.3 部署到 Vercel (推荐)

```bash
# 安装 Vercel CLI
npm install -g vercel

# 部署
vercel --prod
```

**或者使用 Docker 部署:**

```bash
docker build -t lewis-frontend:latest -f frontend/Dockerfile frontend/
docker compose up -d frontend
```

---

## 第五步: 配置 Nginx 反向代理

创建 `/etc/nginx/sites-available/lewis-ai`:

```nginx
# API 服务
server {
    listen 443 ssl http2;
    server_name api.your-domain.com;

    ssl_certificate /etc/letsencrypt/live/api.your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.your-domain.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        
        # WebSocket 支持
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 标准代理头
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时配置 (视频生成需要长时间)
        proxy_read_timeout 3600s;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
    }
}

# 前端服务
server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

启用配置:

```bash
sudo ln -s /etc/nginx/sites-available/lewis-ai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 第六步: 配置 SSL 证书

使用 Let's Encrypt:

```bash
sudo apt install certbot python3-certbot-nginx

# 为 API 申请证书
sudo certbot --nginx -d api.your-domain.com

# 为前端申请证书
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# 设置自动续期
sudo certbot renew --dry-run
```

---

## 第七步: 配置监控与日志

### 7.1 配置 Sentry (错误追踪)

在 `.env` 中已配置 `SENTRY_DSN`。

### 7.2 配置日志收集

```bash
# 使用 Docker 日志驱动
docker compose logs -f backend worker
```

### 7.3 配置 Prometheus + Grafana (可选)

```yaml
# docker-compose.monitoring.yml
services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

---

## 第八步: 安全加固

### 8.1 防火墙配置

```bash
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

### 8.2 限制数据库访问

在 `docker-compose.yml` 中:

```yaml
services:
  postgres:
    ports:
      - "127.0.0.1:5432:5432"  # 仅本地访问
```

### 8.3 配置定期备份

```bash
# 创建备份脚本
cat > /opt/lewis-backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR=/opt/backups
mkdir -p $BACKUP_DIR
DATE=$(date +%Y%m%d_%H%M%S)

# 备份数据库
docker exec lewis-postgres pg_dump -U lewis_user lewis_production | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# 删除 30 天前的备份
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +30 -delete
EOF

chmod +x /opt/lewis-backup.sh

# 添加到 crontab (每天凌晨 2 点)
echo "0 2 * * * /opt/lewis-backup.sh" | sudo crontab -
```

---

## 第九步: 性能优化

### 9.1 配置 Redis 持久化

在 `docker-compose.yml` 中:

```yaml
services:
  redis:
    command: redis-server --appendonly yes --maxmemory 2gb --maxmemory-policy allkeys-lru
```

### 9.2 配置数据库连接池

在 `config.py` 中已配置 SQLAlchemy 连接池。

### 9.3 启用 CDN (可选)

将静态资源 (前端 build) 上传到 CDN (Cloudflare / AWS CloudFront)。

---

## 第十步: 启动完整系统

```bash
# 启动所有服务
docker compose up -d

# 检查服务状态
docker compose ps

# 查看日志
docker compose logs -f backend worker frontend
```

---

## 验证清单

- [ ] 所有环境变量已正确配置
- [ ] 数据库迁移已完成
- [ ] 后端 API 返回 200 状态码
- [ ] 前端可以正常访问
- [ ] 用户可以注册/登录 (Clerk/Auth0)
- [ ] 创作模式可以生成脚本
- [ ] 任务队列正常工作 (Redis + ARQ Worker)
- [ ] SSL 证书有效
- [ ] 日志正常输出
- [ ] 备份脚本运行正常

---

## 故障排查

### 问题 1: 后端启动失败

```bash
# 查看日志
docker compose logs backend

# 常见原因:
# - DATABASE_URL 配置错误
# - API Keys 未配置或无效
# - 端口被占用
```

### 问题 2: 视频生成超时

```bash
# 检查 Worker 是否运行
docker compose ps worker

# 查看 Worker 日志
docker compose logs worker

# 检查 Redis 连接
docker exec lewis-redis redis-cli PING
```

### 问题 3: 前端无法连接后端

```bash
# 检查 CORS 配置
# 确保 CORS_ORIGINS 包含前端域名

# 检查 Nginx 反向代理
sudo nginx -t
sudo tail -f /var/log/nginx/error.log
```

---

## 扩展阅读

- [Alembic 数据库迁移文档](https://alembic.sqlalchemy.org/)
- [ARQ 异步任务队列文档](https://arq-docs.helpmanual.io/)
- [Clerk 认证集成指南](https://clerk.com/docs)
- [Docker Compose 生产部署最佳实践](https://docs.docker.com/compose/production/)
