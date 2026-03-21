"""File services."""

import os
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import aiofiles
from fastapi import UploadFile

from src import settings
from src.dao.orm.manager.file import FileManager
from src.data_schemas.api_schemas.base import SceneID
from src.data_schemas.api_schemas.file import FileUploadData
from src.services.base import DomainSupportService


class FileService(DomainSupportService):
    async def upload(self, *, file: UploadFile, scene_id: SceneID | None) -> FileUploadData:
        user = await self.get_default_user()
        filename = file.filename or "upload.bin"
        ext = Path(filename).suffix.lower()
        date_part = datetime.now().strftime("%Y%m%d")
        oss_key = f"user/{user.id}/{date_part}/{uuid4().hex}{ext}"

        base_dir = Path(settings.file_storage_dir)
        full_path = (base_dir / oss_key).resolve()
        full_path.parent.mkdir(parents=True, exist_ok=True)

        content = await file.read()
        async with aiofiles.open(full_path, "wb") as f:
            await f.write(content)

        file_id = await FileManager().add(
            {
                "user_id": user.id,
                "scene_id": scene_id,
                "oss_key": oss_key,
                "original_filename": filename,
                "content_type": file.content_type or "",
                "size_bytes": len(content),
                "storage_backend": "local",
            }
        )

        return FileUploadData(
            file_id=file_id,
            oss_key=oss_key,
            filename=filename,
            content_type=file.content_type or "",
            size_bytes=len(content),
            scene_id=scene_id,
        )

