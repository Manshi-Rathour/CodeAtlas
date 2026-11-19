from datetime import datetime

from pydantic import BaseModel, Field


class ApiEndpointResponse(BaseModel):
    method: str
    path: str
    framework: str
    file: str
    line: int


class ApiEndpointListResponse(BaseModel):
    total: int
    frameworks: list[str] = Field(default_factory=list)
    endpoints: list[ApiEndpointResponse] = Field(default_factory=list)
    scanned_files: int = 0


class LanguageMetric(BaseModel):
    language: str
    files: int
    bytes: int


class SymbolMetrics(BaseModel):
    total: int
    functions: int
    methods: int
    classes: int
    other: int
    files_with_symbols: int


class ChunkMetrics(BaseModel):
    total: int
    files_with_chunks: int


class DependencyMetrics(BaseModel):
    total: int
    resolved: int
    external: int


class DocumentationMetrics(BaseModel):
    exists: bool
    updated_at: datetime | None = None


class ProjectMetricsResponse(BaseModel):
    project_id: int
    project_name: str
    status: str

    total_files: int
    total_bytes: int
    languages: list[LanguageMetric] = Field(default_factory=list)

    symbols: SymbolMetrics
    chunks: ChunkMetrics
    dependencies: DependencyMetrics

    api_endpoints: int
    api_frameworks: list[str] = Field(default_factory=list)

    conversations: int
    documentation: DocumentationMetrics
