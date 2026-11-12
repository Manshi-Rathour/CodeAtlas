
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, ConfigDict


# Schema used when creating a project
class ProjectCreate(BaseModel):

    name: str = Field(
        min_length=2,
        max_length=150
    )

    description: str | None = Field(
        default=None,
        max_length=2000
    )

    source_type: Literal["github", "zip", "manual"] = "manual"

    repository_url: str | None = Field(
        default=None,
        max_length=500
    )


# Schema used when updating a project
class ProjectUpdate(BaseModel):

    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150
    )

    description: str | None = Field(
        default=None,
        max_length=2000
    )


# Schema used when returning project information
class ProjectResponse(BaseModel):

    id: int
    owner_id: int
    name: str
    description: str | None
    source_type: str
    repository_url: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )
