"""
Log upload endpoints.

Any authenticated, active analyst (Admin, Tier 1, or Tier 2) can upload and
browse logs — log collection is a routine SOC activity, not a privileged
one. Parsing/normalization is intentionally out of scope for this module.
"""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_client_ip, get_current_active_user
from app.db.session import get_db
from app.models.log import LogSourceType
from app.models.user import User
from app.repositories.log_repository import LogRepository
from app.schemas.log import LogListResponse, LogOut, ParseRequest
from app.services.log_parsing_service import (
    AlreadyParsedError,
    LogNotFoundError,
    LogParsingService,
    UnsupportedForParsingError,
)
from app.services.log_upload_service import (
    FileTooLargeError,
    InvalidFileContentError,
    LogUploadService,
    MissingFilenameError,
    UnsupportedFileTypeError,
)

router = APIRouter(prefix="/logs", tags=["Log Upload"])


@router.post("/upload", response_model=LogOut, status_code=status.HTTP_201_CREATED)
async def upload_log(
    request: Request,
    file: UploadFile = File(..., description="The raw log file to upload"),
    source_type: LogSourceType = Form(..., description="Declared source type of the file"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> LogOut:
    service = LogUploadService(db)
    try:
        log = await service.upload(
            upload_file=file,
            source_type=source_type,
            uploaded_by_id=current_user.id,
            ip_address=get_client_ip(request),
        )
    except MissingFilenameError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except UnsupportedFileTypeError as exc:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(exc))
    except InvalidFileContentError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except FileTooLargeError as exc:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(exc))

    return LogOut.model_validate(log)


@router.get("", response_model=LogListResponse)
async def list_logs(
    source_type: Optional[LogSourceType] = Query(default=None),
    mine_only: bool = Query(default=False, description="If true, only return logs uploaded by the caller"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> LogListResponse:
    repo = LogRepository(db)
    uploaded_by_id = current_user.id if mine_only else None
    logs, total = await repo.list(
        source_type=source_type, uploaded_by_id=uploaded_by_id, limit=limit, offset=offset
    )
    return LogListResponse(
        items=[LogOut.model_validate(log) for log in logs],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{log_id}", response_model=LogOut)
async def get_log(
    log_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> LogOut:
    repo = LogRepository(db)
    log = await repo.get_by_id(log_id)
    if log is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log not found")
    return LogOut.model_validate(log)


@router.post("/{log_id}/parse", response_model=LogOut)
async def parse_log(
    log_id: uuid.UUID,
    request: Request,
    payload: ParseRequest = ParseRequest(),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> LogOut:
    """
    Parses a previously uploaded log file into `normalized_log_entries`.
    Returns the updated Log record, including `parse_status` and
    `parse_stats` (total/parsed/skipped/failed record counts).

    Malformed or corrupted files are handled gracefully: per-record issues
    are counted in `parse_stats` and the log ends up `partial`; a whole-file
    failure (e.g. the file can't be opened at all) ends up `failed` with an
    error message in `parse_stats` — neither case raises a 5xx.
    """
    service = LogParsingService(db)
    try:
        log = await service.parse_log(
            log_id=log_id,
            triggered_by_id=current_user.id,
            ip_address=get_client_ip(request),
            force=payload.force,
        )
    except LogNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except AlreadyParsedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except UnsupportedForParsingError as exc:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(exc))

    return LogOut.model_validate(log)
