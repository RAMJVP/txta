class RetrievalService:
    def __init__(self, hybrid): self.hybrid=hybrid
    async def retrieve(self, query): return await self.hybrid.search(query)
