"""Creative project repository implementations."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from threading import Lock
from typing import Iterable

from sqlalchemy import select

from ..database import CreativeProject as CreativeProjectRecord
from ..database import db_manager
from ..instrumentation import get_logger
from ..config import settings
from .models import CreativeProject, CreativeProjectCreateRequest

logger = get_logger()


class BaseCreativeProjectRepository(ABC):
    """Abstract repository contract for creative projects."""

    @abstractmethod
    async def create(self, payload: CreativeProjectCreateRequest) -> CreativeProject:  # pragma: no cover - interface
        raise NotImplementedError

    @abstractmethod
    async def get(self, project_id: str) -> CreativeProject:  # pragma: no cover - interface
        raise NotImplementedError

    @abstractmethod
    async def upsert(self, project: CreativeProject) -> CreativeProject:  # pragma: no cover - interface
        raise NotImplementedError

    @abstractmethod
    async def list_for_tenant(self, tenant_id: str) -> Iterable[CreativeProject]:  # pragma: no cover - interface
        raise NotImplementedError


class InMemoryCreativeProjectRepository(BaseCreativeProjectRepository):
    """Thread-safe in-memory repository used for tests and local development."""

    def __init__(self) -> None:
        self._items: dict[str, CreativeProject] = {}
        self._lock = Lock()

    async def create(self, payload: CreativeProjectCreateRequest) -> CreativeProject:
        project = CreativeProject(
            id=str(uuid.uuid4()),
            tenant_id=payload.tenant_id,
            title=payload.title,
            brief=payload.brief,
            duration_seconds=payload.duration_seconds,
            style=payload.style,
            budget_limit_usd=payload.budget_limit_usd,
            auto_pause_enabled=payload.auto_pause_enabled,
        )
        return await self.upsert(project)

    async def get(self, project_id: str) -> CreativeProject:
        project = self._items.get(project_id)
        if not project:
            raise KeyError(f"Project {project_id} not found")
        return project

    async def upsert(self, project: CreativeProject) -> CreativeProject:
        with self._lock:
            self._items[project.id] = project
        return project

    async def list_for_tenant(self, tenant_id: str) -> Iterable[CreativeProject]:
        return [p for p in self._items.values() if p.tenant_id == tenant_id]


class DatabaseCreativeProjectRepository(BaseCreativeProjectRepository):
    """SQL-backed repository that stores serialized project state in JSON."""

    def __init__(self) -> None:
        if not settings.database_url:
            raise RuntimeError("DATABASE_URL must be configured for DatabaseCreativeProjectRepository")
        
        # Check if database is actually initialized
        from ..database import db_manager
        if not db_manager.engine:
            raise RuntimeError("Database not initialized. Call init_database() first.")

    async def create(self, payload: CreativeProjectCreateRequest) -> CreativeProject:
        project = CreativeProject(
            id=str(uuid.uuid4()),
            tenant_id=payload.tenant_id,
            title=payload.title,
            brief=payload.brief,
            duration_seconds=payload.duration_seconds,
            style=payload.style,
            budget_limit_usd=payload.budget_limit_usd,
            auto_pause_enabled=payload.auto_pause_enabled,
        )
        await self.upsert(project)
        return project

    async def get(self, project_id: str) -> CreativeProject:
        record = await self._fetch_record(project_id)
        if not record or not record.config_json:
            raise KeyError(f"Project {project_id} not found")
        return CreativeProject.model_validate(record.config_json)

    async def upsert(self, project: CreativeProject) -> CreativeProject:
        await self._persist(project)
        return project

    async def list_for_tenant(self, tenant_id: str) -> Iterable[CreativeProject]:
        async with db_manager.get_session() as db:
            stmt = select(CreativeProjectRecord).where(CreativeProjectRecord.user_id == tenant_id)
            results = (await db.scalars(stmt)).all()
            return [CreativeProject.model_validate(rec.config_json) for rec in results if rec.config_json]

    async def _persist(self, project: CreativeProject) -> None:
        async with db_manager.get_session() as db:
            stmt = select(CreativeProjectRecord).where(CreativeProjectRecord.external_id == project.id)
            record = await db.scalar(stmt)
            payload = project.model_dump(mode="json")
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            if record:
                record.config_json = payload
                record.status = project.state.value
                record.cost_usd = project.cost_usd
                record.budget_usd = project.budget_limit_usd
                record.last_active_at = now
            else:
                record = CreativeProjectRecord(
                    external_id=project.id,
                    user_id=project.tenant_id,
                    config_json=payload,
                    status=project.state.value,
                    cost_usd=project.cost_usd,
                    budget_usd=project.budget_limit_usd,
                    created_at=now,
                    last_active_at=now,
                )
                db.add(record)

    async def _fetch_record(self, project_id: str) -> CreativeProjectRecord | None:
        async with db_manager.get_session() as db:
            stmt = select(CreativeProjectRecord).where(CreativeProjectRecord.external_id == project_id)
            return await db.scalar(stmt)


def _build_default_repository() -> BaseCreativeProjectRepository:
    """Build the default repository, with proper fallback logic."""
    if settings.database_url:
        try:
            # Check if database is actually available
            from ..database import db_manager
            if db_manager.engine:
                return DatabaseCreativeProjectRepository()
            else:
                logger.warning("DATABASE_URL configured but database not initialized, using in-memory repository")
        except (RuntimeError, ImportError, AttributeError) as exc:
            logger.warning("Falling back to in-memory creative repository: %s", exc)
    return InMemoryCreativeProjectRepository()


creative_repository: BaseCreativeProjectRepository = _build_default_repository()
