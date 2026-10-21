class HostedEmbeddingProvider:
    """Optional extension point. The default build does not depend on a hosted provider."""
    async def embed_query(self,text): raise RuntimeError('hosted embeddings are disabled by default')
    async def embed_documents(self,texts): raise RuntimeError('hosted embeddings are disabled by default')
