class MetadataRepository:
    def __init__(self,db): self.c=db.kb_metadata if db is not None else None
    async def set(self,key,value): await self.c.update_one({'key':key},{'$set':{'value':value}},upsert=True)
