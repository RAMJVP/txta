from pydantic import BaseModel, Field
class KbChunk(BaseModel):
    pageId: str
    canonicalUrl: str
    chunkNumber: int
    content: str
    headingPath: list[str] = Field(default_factory=list)
    contentHash: str
    embedding: list[float]
    embeddingModel: str
    embeddingDimension: int = 384
    status: str = 'published'
