from datetime import datetime, timezone, timedelta
class SessionRepository:
    def __init__(self,db,ttl_minutes=30,max_turns=5): self.c=db.navigator_sessions if db is not None else None; self.ttl=ttl_minutes; self.max=max_turns
    async def get(self,h): return None if self.c is None else await self.c.find_one({'sessionIdHash':h})
    async def append(self,h,turn):
        if self.c is None: return
        exp=datetime.now(timezone.utc)+timedelta(minutes=self.ttl)
        await self.c.update_one({'sessionIdHash':h},{'$push':{'turns':{'$each':[turn],'$slice':-self.max}},'$set':{'expiresAt':exp,'updatedAt':datetime.now(timezone.utc)}},upsert=True)
    async def delete(self,h):
        if self.c is not None: await self.c.delete_one({'sessionIdHash':h})
