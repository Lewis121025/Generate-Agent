"""FastAPI router for Creative Mode."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..creative.models import CreativeProjectCreateRequest, CreativeProjectResponse, CreativeProjectListResponse
from ..creative.repository import creative_repository
from ..creative.workflow import creative_orchestrator

router = APIRouter(prefix="/creative", tags=["creative"])


@router.post("/projects", response_model=CreativeProjectResponse, status_code=201)
async def create_project(payload: CreativeProjectCreateRequest) -> CreativeProjectResponse:
    try:
        project = await creative_orchestrator.create_project(payload)
    except Exception as exc:
        from ..instrumentation import get_logger
        logger = get_logger()
        logger.error(f"Error creating project: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(exc)}") from exc
    return CreativeProjectResponse(project=project)


@router.post("/projects/{project_id}/approve-script", response_model=CreativeProjectResponse)
async def approve_script(project_id: str) -> CreativeProjectResponse:
    try:
        project = await creative_orchestrator.approve_script(project_id)
        # Ensure project is not a coroutine
        if hasattr(project, '__await__'):
            project = await project
    except KeyError as exc:  # pragma: no cover - FastAPI handles
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        from ..instrumentation import get_logger
        logger = get_logger()
        logger.error(f"Error approving script for project {project_id}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to approve script: {str(exc)}") from exc
    return CreativeProjectResponse(project=project)


@router.post("/projects/{project_id}/advance", response_model=CreativeProjectResponse)
async def advance_project(project_id: str) -> CreativeProjectResponse:
    try:
        project = await creative_orchestrator.advance(project_id)
    except KeyError as exc:  # pragma: no cover - FastAPI handles
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        from ..instrumentation import get_logger
        logger = get_logger()
        logger.error(f"Error advancing project {project_id}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to advance project: {str(exc)}") from exc
    return CreativeProjectResponse(project=project)


@router.post("/projects/{project_id}/approve-preview", response_model=CreativeProjectResponse)
async def approve_preview(project_id: str) -> CreativeProjectResponse:
    try:
        project = await creative_orchestrator.approve_preview(project_id)
        # Ensure project is not a coroutine
        if hasattr(project, '__await__'):
            project = await project
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        from ..instrumentation import get_logger
        logger = get_logger()
        logger.error(f"Error approving preview for project {project_id}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to approve preview: {str(exc)}") from exc
    return CreativeProjectResponse(project=project)


@router.get("/projects", response_model=CreativeProjectListResponse)
async def list_projects(tenant_id: str = "demo") -> CreativeProjectListResponse:
    try:
        projects_obj = creative_repository.list_for_tenant(tenant_id)
        if hasattr(projects_obj, '__await__'):
            projects = await projects_obj  # type: ignore[func-returns-value]
        else:
            projects = projects_obj  # type: ignore[assignment]
    except Exception as exc:
        from ..instrumentation import get_logger
        logger = get_logger()
        logger.error(f"Error listing projects for tenant {tenant_id}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list projects: {str(exc)}") from exc

    return CreativeProjectListResponse(projects=list(projects))


@router.get("/projects/{project_id}", response_model=CreativeProjectResponse)
async def get_project(project_id: str) -> CreativeProjectResponse:
    from ..instrumentation import get_logger
    logger = get_logger()
    
    try:
        # Get project - ensure we await the coroutine
        project_coro = creative_repository.get(project_id)
        if hasattr(project_coro, '__await__'):
            project = await project_coro
        else:
            project = project_coro
        
        # Double-check: ensure project is not a coroutine (defensive programming)
        if hasattr(project, '__await__'):
            logger.warning(f"Project {project_id} is still a coroutine, awaiting again...")
            project = await project
        
        logger.debug(f"Retrieved project {project_id}, state: {project.state}, type: {type(project)}")
    except KeyError as exc:  # pragma: no cover
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.error(f"Error getting project {project_id}: {exc}", exc_info=True)
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(exc)}") from exc
    
    try:
        # Validate the project can be serialized
        response = CreativeProjectResponse(project=project)
        # Try to serialize to catch any serialization errors early
        _ = response.model_dump(mode="json")
        return response
    except Exception as exc:
        logger.error(f"Error serializing project {project_id}: {exc}", exc_info=True)
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Serialization error: {str(exc)}") from exc
