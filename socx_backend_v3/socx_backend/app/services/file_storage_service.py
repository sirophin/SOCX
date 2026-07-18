"""
File storage service — streams uploaded files to the uploads/ directory
on disk, enforcing a max size limit and performing content sniffing on
the first chunk before committing to the write.

Storage layout: uploads/<source_type>/<yyyy>/<mm>/<uuid>_<sanitized_name>
This keeps any single directory from accumulating unbounded file counts
and makes it trivial to shard/move to object storage later (see
architecture doc Section 18, Scalability).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings
from app.core.file_validation import sanitize_filename, sniff_content
from app.models.log import LogSourceType

_CHUNK_SIZE = 1024 * 1024  # 1 MB


class FileTooLargeError(Exception):
    pass


class FileStorageService:
    def __init__(self, base_dir: str | Path | None = None):
        self.base_dir = Path(base_dir or settings.UPLOAD_DIR).resolve()

    def _build_destination(self, source_type: LogSourceType, original_filename: str) -> Path:
        safe_name = sanitize_filename(original_filename)
        now = datetime.now(timezone.utc)
        subdir = self.base_dir / source_type.value / f"{now:%Y}" / f"{now:%m}"
        subdir.mkdir(parents=True, exist_ok=True)
        unique_name = f"{uuid.uuid4().hex}_{safe_name}"
        return subdir / unique_name

    async def save(self, upload_file: UploadFile, source_type: LogSourceType) -> tuple[str, int]:
        """
        Streams `upload_file` to disk in chunks, enforcing MAX_UPLOAD_SIZE_MB
        and sniffing the first chunk's content against the claimed source
        type. Returns (relative_path_from_upload_dir, size_bytes).

        Raises FileTooLargeError or InvalidFileContentError (from
        app.core.file_validation) and cleans up any partial file on failure.
        """
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        dest_path = self._build_destination(source_type, upload_file.filename or "upload")

        total_bytes = 0
        first_chunk_checked = False

        try:
            with open(dest_path, "wb") as out_file:
                while True:
                    chunk = await upload_file.read(_CHUNK_SIZE)
                    if not chunk:
                        break

                    if not first_chunk_checked:
                        sniff_content(chunk, source_type)  # raises InvalidFileContentError
                        first_chunk_checked = True

                    total_bytes += len(chunk)
                    if total_bytes > max_bytes:
                        raise FileTooLargeError(
                            f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB} MB"
                        )

                    out_file.write(chunk)

            if not first_chunk_checked:
                # Zero-byte file: read() returned empty immediately.
                sniff_content(b"", source_type)  # raises InvalidFileContentError("empty")

        except Exception:
            dest_path.unlink(missing_ok=True)
            raise
        finally:
            await upload_file.close()

        relative_path = dest_path.relative_to(self.base_dir).as_posix()
        return relative_path, total_bytes

    def resolve_absolute_path(self, relative_path: str) -> Path:
        return self.base_dir / relative_path

    def delete(self, relative_path: str) -> None:
        self.resolve_absolute_path(relative_path).unlink(missing_ok=True)
