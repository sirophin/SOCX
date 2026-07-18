"""
Log upload service — orchestrates validation, on-disk storage, and metadata
persistence for uploaded log files.

Scope boundary: this module stops at storing the raw file and its metadata
row in `logs`. It does NOT parse file contents into `normalized_log_entries`
— that's a separate LogParsingService/pipeline stage (see architecture doc
Section 9), built on top of this module's output.
"""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.file_validation import (
    InvalidFileContentError,
    UnsupportedFileTypeError,
    validate_extension,
    validate_source_type_supported,
)
from app.models.log import Log, LogSourceType
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.log_repository import LogRepository
from app.services.file_storage_service import FileStorageService, FileTooLargeError

# Re-exported so the API layer only needs to import from this module.
__all__ = [
    "LogUploadService",
    "UnsupportedFileTypeError",
    "InvalidFileContentError",
    "FileTooLargeError",
    "MissingFilenameError",
]


class MissingFilenameError(Exception):
    pass


class LogUploadService:
    def __init__(self, db: AsyncSession, storage: Optional[FileStorageService] = None):
        self.db = db
        self.storage = storage or FileStorageService()
        self.logs = LogRepository(db)
        self.audit = AuditLogRepository(db)

    async def upload(
        self,
        upload_file: UploadFile,
        source_type: LogSourceType,
        uploaded_by_id: Optional[uuid.UUID],
        ip_address: Optional[str] = None,
    ) -> Log:
        if not upload_file.filename:
            raise MissingFilenameError("Uploaded file has no filename")

        # 1. Validate source type is supported by this module and the
        #    extension matches what's allowed for that source type.
        validate_source_type_supported(source_type)
        validate_extension(upload_file.filename, source_type)

        # 2. Stream to disk, enforcing size limit and sniffing content.
        #    Raises FileTooLargeError / InvalidFileContentError on failure;
        #    any partially-written file is cleaned up by the storage service.
        relative_path, size_bytes = await self.storage.save(upload_file, source_type)

        # 3. Persist metadata.
        log = await self.logs.create(
            source_type=source_type,
            original_filename=upload_file.filename,
            file_reference=relative_path,
            file_size_bytes=size_bytes,
            uploaded_by_id=uploaded_by_id,
        )

        # 4. Audit trail.
        await self.audit.write(
            action="log.upload",
            target_entity="Log",
            user_id=uploaded_by_id,
            target_id=log.id,
            ip_address=ip_address,
        )

        await self.db.commit()
        await self.db.refresh(log, attribute_names=["uploaded_by"])
        return log
