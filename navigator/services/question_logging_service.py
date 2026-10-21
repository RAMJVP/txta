from datetime import datetime, timezone, timedelta
class QuestionLoggingService:
    def __init__(self,repo,retention_days=30): self.repo=repo; self.days=retention_days
    async def log(self,doc):
        try:
            now=datetime.now(timezone.utc); doc={**doc,'createdAt':now,'expiresAt':now+timedelta(days=self.days)}; await self.repo.log(doc)
        except Exception: pass
