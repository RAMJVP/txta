class KbChunkRepository:
    def __init__(self,db): self.c=db.kb_chunks if db is not None else None
    async def replace_for_page(self,page_id,chunks):
        await self.c.delete_many({'pageId':page_id})
        if chunks: await self.c.insert_many(chunks)
