from datetime import datetime
from pydantic import BaseModel, Field
class NavigatorSession(BaseModel):
    sessionIdHash: str
    turns: list[dict] = Field(default_factory=list, max_length=5)
    updatedAt: datetime
    expiresAt: datetime
