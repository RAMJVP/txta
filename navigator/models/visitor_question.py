from datetime import datetime
from pydantic import BaseModel, Field
class VisitorQuestion(BaseModel):
    sessionIdHash: str
    question: str
    normalizedQuestion: str
    safetyDecision: str
    resultPageIds: list[str] = Field(default_factory=list)
    outcome: str
    latencyMs: int
    createdAt: datetime
    expiresAt: datetime
