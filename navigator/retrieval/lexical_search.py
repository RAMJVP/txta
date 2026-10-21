class LexicalSearch:
    def __init__(self, repository, limit=10): self.repository=repository; self.limit=limit
    async def search(self, query): return await self.repository.lexical_search(query,self.limit)
