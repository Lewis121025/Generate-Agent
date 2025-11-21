"""FastAPI router for General Mode sessions."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ..general.models import GeneralSessionCreateRequest, GeneralSessionResponse, GeneralSessionListResponse
from ..general.repository import general_repository
from ..general.session import general_orchestrator
from ..storage import default_storage


MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB per file


from pydantic import BaseModel


class RunIterationRequest(BaseModel):
    prompt: str | None = None

router = APIRouter(prefix="/general", tags=["general"])


@router.post("/sessions", response_model=GeneralSessionResponse, status_code=201)
async def create_session(payload: GeneralSessionCreateRequest) -> GeneralSessionResponse:
    try:
        session = await general_orchestrator.create_session(payload)
    except Exception as exc:
        from ..instrumentation import get_logger
        logger = get_logger()
        logger.error(f"Error creating session: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(exc)}") from exc
    return GeneralSessionResponse(session=session)


@router.post("/sessions/{session_id}/iterate", response_model=GeneralSessionResponse)
async def run_iteration(session_id: str, payload: RunIterationRequest | None = None) -> GeneralSessionResponse:
    try:
        session = await general_orchestrator.run_iteration(session_id, prompt_text=payload.prompt if payload else None)
    except KeyError as exc:  # pragma: no cover
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        from ..instrumentation import get_logger
        logger = get_logger()
        logger.error(f"Error running iteration for session {session_id}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to run iteration: {str(exc)}") from exc
    return GeneralSessionResponse(session=session)


@router.get("/sessions/{session_id}", response_model=GeneralSessionResponse)
async def get_session(session_id: str) -> GeneralSessionResponse:
    try:
        session_obj = general_repository.get(session_id)
        # Support both async and sync repository implementations
        if hasattr(session_obj, "__await__"):
            session = await session_obj
        else:
            session = session_obj
    except KeyError as exc:  # pragma: no cover
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        from ..instrumentation import get_logger
        logger = get_logger()
        logger.error(f"Error getting session {session_id}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {str(exc)}") from exc
    return GeneralSessionResponse(session=session)


@router.get("/sessions", response_model=GeneralSessionListResponse)
async def list_sessions(tenant_id: str = "demo", limit: int = 50) -> GeneralSessionListResponse:
    try:
        sessions_obj = general_repository.list_for_tenant(tenant_id, limit)
        if hasattr(sessions_obj, "__await__"):
            sessions = await sessions_obj  # type: ignore[func-returns-value]
        else:
            sessions = sessions_obj  # type: ignore[assignment]
    except Exception as exc:
        from ..instrumentation import get_logger
        logger = get_logger()
        logger.error(f"Error listing sessions for tenant {tenant_id}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(exc)}") from exc

    return GeneralSessionListResponse(sessions=list(sessions))


@router.post("/sessions/{session_id}/message", response_model=GeneralSessionResponse)
async def send_message_with_files(
    session_id: str,
    prompt: str | None = Form(default=None),
    files: list[UploadFile] | None = None,
) -> GeneralSessionResponse:
    """Accept user prompt + optional attachments, append to session, then run one iteration."""
    try:
        session_obj = general_repository.get(session_id)
        session = await session_obj if hasattr(session_obj, "__await__") else session_obj
    except KeyError as exc:  # pragma: no cover
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to get session: {exc}") from exc

    saved_paths: list[str] = []
    if files:
        for f in files:
            data = await f.read()
            if len(data) > MAX_UPLOAD_BYTES:
                raise HTTPException(status_code=400, detail=f"File {f.filename} exceeds 10MB limit")
            safe_name = f.filename or "upload.bin"
            relative_path = str(Path("general") / session_id / safe_name)
            path = default_storage.save_bytes(relative_path, data)
            session.uploads.append(
                {
                    "name": safe_name,
                    "content_type": f.content_type,
                    "size_bytes": len(data),
                    "local_path": path,
                }
            )
            saved_paths.append(path)

        if saved_paths:
            session.messages.append(f"User uploaded files: {', '.join(saved_paths)}")

    if prompt:
        session.goal = prompt
        session.messages.append(f"User: {prompt}")

    try:
        session = await general_repository.upsert(session)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to persist session updates: {exc}") from exc

    try:
        session = await general_orchestrator.run_iteration(session_id, prompt_text=None)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to run iteration: {exc}") from exc

    return GeneralSessionResponse(session=session)
