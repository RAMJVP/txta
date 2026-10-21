class VectorSearch:
    def __init__(self, repository, embedder, limit=10): self.repository=repository; self.embedder=embedder; self.limit=limit
    async def search(self, query):
        vector=await self.embedder.embed_query(query)
        return await self.repository.vector_search(vector,self.limit)
