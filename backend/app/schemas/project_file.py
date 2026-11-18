
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProjectFileResponse(BaseModel):
    id: int
    project_id: int
    filename: str
    relative_path: str
    extension: str
    language: str
    size_bytes: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectFileListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    files: list[ProjectFileResponse]


class ProjectFileTreeResponse(BaseModel):
    total: int
    shown: int
    truncated: bool
    files: list[ProjectFileResponse]
