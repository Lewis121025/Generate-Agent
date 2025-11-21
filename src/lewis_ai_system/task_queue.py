"""
异步任务队列系统 - 使用 ARQ (Async Redis Queue)
解决视频生成等长时间任务的超时问题
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from arq import create_pool
from arq.connections import RedisSettings, ArqRedis

from .config import settings
from .instrumentation import get_logger

logger = get_logger()


# ==================== 任务队列配置 ====================
class WorkerSettings:
    """ARQ Worker 配置"""
    
    redis_settings = RedisSettings(
        host=settings.redis_url.split("://")[-1].split(":")[0] if settings.redis_url else "localhost",
        port=int(settings.redis_url.split(":")[-1].split("/")[0]) if settings.redis_url and ":" in settings.redis_url else 6379,
    )
    
    # 任务函数注册
    functions = []
    
    # Worker 配置
    max_jobs = 10  # 最大并发任务数
    job_timeout = 3600  # 任务超时时间 (1小时)
    keep_result = 3600  # 结果保留时间


# ==================== 任务状态枚举 ====================
class TaskStatus:
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ==================== 任务队列客户端 ====================
class TaskQueue:
    """任务队列客户端 (用于 API 层提交任务)"""
    
    def __init__(self):
        self.pool: ArqRedis | None = None
    
    async def connect(self):
        """连接到 Redis"""
        if not self.pool:
            self.pool = await create_pool(WorkerSettings.redis_settings)
            logger.info("Task queue connected to Redis")
    
    async def disconnect(self):
        """断开连接"""
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("Task queue disconnected")
    
    async def enqueue_video_generation(
        self,
        project_id: str,
        script: str,
        storyboard: list[dict[str, Any]],
        **kwargs
    ) -> str:
        """
        提交视频生成任务到队列
        
        Returns:
            task_id (str): 任务 ID,用于查询状态
        """
        if not self.pool:
            await self.connect()
        
        # 提交任务到 ARQ
        job = await self.pool.enqueue_job(
            "generate_video_task",  # 任务函数名
            project_id,
            script,
            storyboard,
            **kwargs
        )
        
        logger.info(f"Enqueued video generation task: {job.job_id} for project {project_id}")
        
        return job.job_id
    
    async def get_task_status(self, task_id: str) -> dict[str, Any]:
        """
        查询任务状态
        
        Returns:
            {
                "status": "pending" | "running" | "completed" | "failed",
                "progress": 0.0 - 1.0,
                "result": Any,  # 仅 completed 时有值
                "error": str,   # 仅 failed 时有值
            }
        """
        if not self.pool:
            await self.connect()
        
        job = await self.pool.get_job(task_id)
        
        if not job:
            return {
                "status": TaskStatus.CANCELLED,
                "progress": 0.0,
                "error": "Task not found"
            }
        
        # 获取任务状态
        job_result = await job.result()
        job_info = await job.info()
        
        status = TaskStatus.PENDING
        if job_info.job_try and job_info.job_try > 0:
            status = TaskStatus.RUNNING
        if job_result is not None:
            status = TaskStatus.COMPLETED
        if job_info.job_try and job_info.job_try >= 3:  # 重试3次后失败
            status = TaskStatus.FAILED
        
        return {
            "status": status,
            "progress": job_info.job_try / 3 if job_info.job_try else 0.0,
            "result": job_result,
            "error": None,
        }


# ==================== Worker 任务函数 ====================
async def generate_video_task(
    ctx: dict[str, Any],
    project_id: str,
    script: str,
    storyboard: list[dict[str, Any]],
    **kwargs
) -> dict[str, Any]:
    """
    视频生成任务 (在 Worker 进程中执行)
    
    这个函数运行在独立的 Worker 进程中,不会阻塞 API 请求。
    
    Args:
        ctx: ARQ 上下文 (包含 Redis 连接等)
        project_id: 项目 ID
        script: 视频脚本
        storyboard: 分镜列表
    
    Returns:
        {"video_url": str, "cost_usd": float}
    """
    logger.info(f"Starting video generation for project {project_id}")
    
    try:
        # 1. 导入必要的模块
        from .creative.models import VideoGenerationRequest
        from .providers import get_video_provider
        from .database import db_manager
        from .creative.repository import creative_repository
        
        # 2. 获取项目信息
        project = await creative_repository.get(project_id)
        
        # 3. 调用视频生成 Provider
        video_provider = get_video_provider(settings.video_provider_default)
        
        # 构造请求
        request = VideoGenerationRequest(
            script=script,
            duration=project.duration_seconds,
            style=project.style,
        )
        
        # 调用 Provider (这里会等待 3-5 分钟)
        result = await video_provider.generate(request)
        
        # 4. 更新项目状态
        project.video_url = result.video_url
        project.cost_usd += result.cost_usd
        project.state = "rendering_complete"
        
        await creative_repository.upsert(project)
        
        logger.info(f"Video generation completed for project {project_id}: {result.video_url}")
        
        return {
            "video_url": result.video_url,
            "cost_usd": result.cost_usd,
            "duration": result.duration,
        }
    
    except Exception as e:
        logger.error(f"Video generation failed for project {project_id}: {e}", exc_info=True)
        
        # 更新项目状态为失败
        try:
            project = await creative_repository.get(project_id)
            project.error_message = str(e)
            await creative_repository.upsert(project)
        except Exception:
            pass
        
        raise  # 重新抛出异常,让 ARQ 记录失败


# 注册任务函数
WorkerSettings.functions = [generate_video_task]


# ==================== 全局队列实例 ====================
task_queue = TaskQueue()


# ==================== FastAPI 生命周期集成 ====================
async def init_task_queue():
    """FastAPI 启动时初始化任务队列"""
    if settings.redis_enabled and settings.redis_url:
        await task_queue.connect()
        logger.info("Task queue initialized")
    else:
        logger.warning("Task queue disabled (REDIS_ENABLED=false or REDIS_URL not set)")


async def shutdown_task_queue():
    """FastAPI 关闭时清理任务队列"""
    await task_queue.disconnect()
    logger.info("Task queue shut down")
