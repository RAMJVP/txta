from datetime import datetime, timezone
class ClickEventRepository:
    def __init__(self,db): self.c=db.navigator_events if db is not None else None
    async def add(self,request_id,page_id):
        if self.c is not None: await self.c.insert_one({'requestId':request_id,'pageId':page_id,'createdAt':datetime.now(timezone.utc)})
