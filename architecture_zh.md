# Lewis AI System 架构蓝图

_更新日期：2025-11-19_

## 1. 系统使命与范围
Lewis AI System 通过单一的 FastAPI 后端 (`src/lewis_ai_system/main.py`) 支撑新版蓝图中的双引擎体验：

- **Insight Lab (通用模式)**：企业级研究助手，通过链式调用 Web 搜索、沙箱 Python、知识库召回、结构化 API 和可视化工具，在几分钟内输出可供讨论的深度洞察报告。
- **Creative Sprint (创意模式)**：分阶段的创意生产流水线，将灵感或剧本转化为分镜、渲染图和交付资产，并集成了审批、质检 (QC) 和分发流程。

双引擎共享同一套基础设施 (`docker-compose.yml` 统一拉起 `lewis-api` 容器以及 Postgres、Redis 和 Weaviate)。业务状态持久化在 Postgres，热数据和限流在 Redis，向量嵌入在 Weaviate，大型制品流式传输至 S3 兼容存储。这种设计保持了 API 的无状态性、可移植性和水平扩展能力。

## 2. 体验入口
架构与三大核心价值场景一一对应：

1.  **Insight Lab**：`/general/sessions` 端点负责创建和迭代 ReAct 会话，设有预算围栏，并透出工具调用轨迹，方便策略团队审计每一步操作。
2.  **Creative Sprint**：`/creative/projects` 端点管理多阶段创意生命周期 (Brief → Script → Storyboard → Render → Distribution)，维护版本树和可分享的产出。
3.  **Unified Governance Console (统一治理控制台)**：通过 REST API 和内部仪表盘暴露的分析、成本和审计数据，允许运营团队检查运行历史、执行配额管理并导出证据。

模板、快速启动流和引导式规划器在客户端层实现，但所有交互最终都解析为上述路由，确保产品流程与架构紧密耦合。

## 3. 运行拓扑与部署
```
客户端 (Portal / REST / SDK)
        |
 FastAPI 应用 (lewis-api 容器)
        |
  ┌───────────────┬────────────────┬────────────────┐
  │               │                │                │
创意路由       通用路由        治理 API       服务端点
  │               │                │
创意工作流      ReAct 编排器      用量/成本遥测
  │               │                │
  │         ┌─────┴─────┐          │
  │         │ Agent Pool│          │
  │         └─────┬─────┘          │
  │               │                │
  └───── 共享服务：工具运行时、沙箱、Provider、成本监控、
           instrumentation、存储适配器、向量库、Redis 缓存
```

支撑容器和脚本：

-   **Postgres** (`database.py`)：项目、会话、工具执行、预算和审批的关系型数据源。
-   **Redis** (`redis_cache.py`)：异步缓存、会话记忆和限流。
-   **Weaviate** (`vector_db.py`)：语义记忆，测试时可回退到内存实现。
-   **Docker 入口** (`docker/entrypoint.sh`)：等待依赖就绪，可选执行 `python -m lewis_ai_system.cli init-db`，然后启动 `uvicorn`。
-   **启动脚本** (`start.sh`, `start.ps1`)：环境引导、密钥生成、Compose 编排、健康检查。

## 4. 能力堆栈映射
| 层级 | 模块 | 蓝图对齐 |
|-------|---------|---------------------|
| **基础层** | `config.py`, `auth.py`, `database.py`, `redis_cache.py`, `vector_db.py`, `s3_storage.py` | 多租户配置、认证、存储和两种模式的数据保障 |
| **服务网格** | `agents.py`, `tooling.py`, `sandbox.py`, `providers.py`, `costs.py`, `cost_monitor.py`, `instrumentation.py` | 智能体原语、工具编排、安全执行、Provider 抽象、主动成本遥测 |
| **业务逻辑** | `routers/general.py`, `routers/creative.py`, `general/session.py`, `creative/workflow.py`, repositories | 实现 Insight Lab 迭代和 Creative Sprint 阶段，包含预算+审批逻辑 |
| **体验层** | 模板/目录 API, 分享端点, 分析源 (向 Portal/UI 透出数据) | 支撑快速启动、引导式规划器、分享链接、运行历史和治理仪表盘 |

## 5. 工作流生命周期
### Insight Lab (通用模式)
1.  **创建会话**：`POST /general/sessions` 持久化目标、预算、工具白名单和治理标签。
2.  **成本预检**：预算信封 (来自 `costs.py`) 校验本次运行是否在用户/团队配额内。
3.  **迭代执行**：`POST /general/sessions/{id}/iterate` 调用 **LLM 驱动的 ReAct 循环** (`_decide_next_step`)，通过 `ToolRuntime` + `sandbox.py` 执行工具 (如 Web 搜索、Python 计算)，记录输出、轨迹、Token 消耗和成本。
    *   *优化点*：支持思维链 (Chain of Thought) 推理和结构化 JSON 决策。
4.  **完成**：当目标达成、迭代耗尽或 `cost_monitor.py` 触发硬限制时停止；流式返回总结并附带用于仪表盘的遥测数据。

### Creative Sprint (创意模式)
1.  **蓝图录入**：`POST /creative/projects` 存储 Brief、品牌套件、里程碑计划和基准预算。
2.  **阶段编排**：`creative/workflow.py` 推进任务 (Brief → Script → Storyboard → Render → Distribution)，持久化制品 (`storage.py`/`s3_storage.py`) 并关联审批。
    *   *优化点*：**智能剧本生成** (结构化场景/对白)、**智能场景拆分** (基于 LLM 的 JSON 解析)、**并行分镜生成** (AsyncIO 加速)。
3.  **版本图谱 + 分享**：每次生成都会写入 Postgres + S3 并更新版本树，使用户可以对比差异、回滚或升级为模板/分享链接。
4.  **分发**：最终资产推送到外部渠道 (S3, YouTube, TikTok, Meta, 广告平台)，附带元数据载荷和用于审计的治理事件。

## 6. 数据与存储织物
1.  **Postgres 模式** (`database.py`)：
    -   创意：`CreativeProject`, `Script`, `Storyboard`, `GeneratedShot`, `ProjectAsset`, 审批, 渲染队列条目。
    -   通用：`Conversation`, `ConversationTurn`, 工具轨迹。
    -   共享：`ToolExecution`, `CostBreakdown`, `User`, `VectorEmbedding`, `UserTopic`, `ToolSchemaRegistry`, `CostAnomalyAlert`, `VectorIndexMaintenance`。
2.  **Redis**：工具响应的 TTL 缓存、预算记忆和限流；测试期间切换到内存后端。
3.  **向量库**：由 `vector_db.py` 编排的 Weaviate 集合；`InMemoryVectorDB` 保持单元测试的封闭性。
4.  **制品存储**：`storage.py` 处理本地磁盘，`s3_storage.py` 抽象 AWS S3/MinIO；创意渲染图和可下载的研究包存储于此。

## 7. 成本治理与可观测性
-   **预算建模**：`costs.py` 分配项目/团队/API 信封；`governance/service.py` 解析层级 (项目 vs 会话)。
-   **实时监控**：`cost_monitor.py` 将支出增量流式传输到 `instrumentation.py`，供给用量分析并触发软/硬阈值。
-   **治理服务**：`governance/service.py` 聚合成本快照、审计事件和用量概览，供控制台使用。
-   **遥测**：结构化事件标记每一次工具调用、阶段流转、渲染作业和分发推送，用于治理控制台。
-   **健康端点**：`/healthz` 用于存活检查，`/readyz` 用于依赖就绪检查 (Postgres/S3/Redis/Weaviate)。

## 8. 安全与配置
-   **认证**：`auth.py` 集中处理 API Key 哈希、Bearer Token 和可选的 JWT 验证；Scope 映射到模板/运行权限。
-   **密钥与配置**：`.env` (及 `.env.docker.example`) 定义 `SECRET_KEY`, `API_KEY_SALT`, Provider 凭证和受信任主机；启动脚本在本地运行时回填缺失的密钥。
-   **网络态势**：`TrustedHostMiddleware` + CORS 配置实施边界规则；未来的反向代理可以在不更改代码的情况下叠加 mTLS 或 WAF 策略。
-   **Provider 治理**：`config.py` 注入 OpenRouter, Runway, Pika, Runware, ElevenLabs, Tavily, Firecrawl, Zapier, S3 等凭证，确保每个环境具有最小权限令牌。

## 9. 测试与扩展性
-   **测试体系**：`pytest` 套件覆盖认证、Provider、创意工作流、通用会话、新特性 (ReAct, 并行分镜) 和成本监控；内存替身确保 CI 与云服务隔离。
-   **扩展工具/Provider**：在 `tooling.py` 中实现新的 `Tool` 子类或 Helper 并注册到 `default_tool_runtime`；Provider 适配器插入 `providers.py` 并共享凭证加载。
-   **向量/存储切换**：`VectorDBManager` 可在 Weaviate 和新驱动之间切换，而 `s3_storage.py` 可以包装任何 S3 兼容端点。
-   **界面演进**：由于路由器暴露了清晰的契约，产品团队可以持续迭代模板、规划器、嵌入式 SDK 或治理仪表盘，而无需触碰核心编排器。

这份更新后的架构蓝图保留了代码库的全部技术保真度，同时将术语、流程和治理控制与最新的产品蓝图及近期实施的优化（如智能 ReAct 循环和并行创意流水线）保持一致。
