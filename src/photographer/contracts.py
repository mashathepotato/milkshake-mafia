from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, model_validator


class Viewport(BaseModel):
    width: int = 1440
    height: int = 900


class CaptureRequest(BaseModel):
    request_id: str
    url: str
    viewport: Viewport = Viewport()
    full_page: bool = True
    wait_until: str = "networkidle"  # load | domcontentloaded | networkidle
    wait_ms: int = 500
    user_agent: Optional[str] = None
    headers: dict[str, str] = {}


class ErrorInfo(BaseModel):
    type: Optional[str] = None
    message: Optional[str] = None


class ScreenshotArtifact(BaseModel):
    request_id: str
    url: str
    captured_at: str
    viewport: Viewport
    full_page: bool
    png_base64: Optional[str] = None
    png_path: Optional[str] = None
    http_status: Optional[int] = None
    final_url: str
    warnings: list[str] = []
    error: Optional[ErrorInfo] = None


class EmbeddingInput(BaseModel):
    source: str  # "png_base64" | "png_path" | "none"
    image_width: int
    image_height: int


class EmbeddingArtifact(BaseModel):
    request_id: str
    url: str
    model_id: str
    embedding_dim: int
    embedding: list[float]
    normalized: bool = True
    computed_at: str
    input: EmbeddingInput
    warnings: list[str] = []
    error: Optional[ErrorInfo] = None

    @model_validator(mode="after")
    def check_embedding_dim(self) -> "EmbeddingArtifact":
        if len(self.embedding) != self.embedding_dim:
            raise ValueError(
                f"embedding_dim={self.embedding_dim} but len(embedding)={len(self.embedding)}"
            )
        return self
