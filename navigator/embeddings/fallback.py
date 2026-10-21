class FallbackEmbeddingProvider:
    def __init__(self,primary,fallback): self.primary=primary; self.fallback=fallback
    async def embed_query(self,text):
        try: return await self.primary.embed_query(text)
        except Exception: return await self.fallback.embed_query(text)
    async def embed_documents(self,texts):
        try: return await self.primary.embed_documents(texts)
        except Exception: return await self.fallback.embed_documents(texts)
    async def warmup(self):
        try: await self.primary.warmup()
        except Exception: await self.fallback.warmup()
