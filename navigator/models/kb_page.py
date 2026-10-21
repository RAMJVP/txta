from datetime import datetime
from pydantic import BaseModel, Field
class KbPage(BaseModel):
    canonicalUrl: str
    url: str
    title: str
    description: str = ''
    keywords: list[str] = Field(default_factory=list)
    headings: list[str] = Field(default_factory=list)
    category: str = ''
    content: str
    contentHash: str
    locale: str = 'en-IN'
    status: str = 'published'
    embedding: list[float]
    embeddingModel: str
    embeddingDimension: int = 384
    indexedAt: datetime
